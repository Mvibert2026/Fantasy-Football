"""
Backtest harness (Phase 1, Step 3).

Evaluates a candidate ranking configuration against a season's actual
outcomes, structurally barred from letting ranking-input construction see
that season's own data (CLAUDE.md #6.1). Compares against three baselines:

- bpa_prior_season_points: ranked by the immediately prior season's actual
  fantasy points (CLAUDE.md #6.5 baseline #2). This is the disclosed,
  buildable proxy for "draft best available off a good half-PPR list" --
  it doesn't require an external projections source, so it always works.
- consensus_adp: NOT AVAILABLE. No true ADP source has been ingested --
  FFC disallows /api/ in robots.txt, and Yahoo/ESPN/Sleeper/Underdog need
  per-site ToS review that hasn't been done (docs/deferred.md). Reported
  as unavailable rather than faked.
- fantasypros_preseason: FantasyPros Expert Consensus Rankings, the
  preseason (pre-Week-1) snapshot for the target season, from the
  `rankings` table (source=fantasypros_ecr; see src/ingest_rankings.py).

Replacement levels are scoring.ReplacementLevels as already defined
(QB10 / RB28 / WR41 / TE11 for this 10-team league) -- not redefined here.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scipy.stats import spearmanr

import db
from scoring import ReplacementLevels, compute_vbd, score_offensive_game

RankingConfig = Dict[str, int]  # player_id -> rank (1 = best)


@dataclass
class BaselineResult:
    name: str
    available: bool
    reason: Optional[str] = None
    vbd_sum: Optional[float] = None
    correlation_with_actual_finish: Optional[float] = None
    delta_vs_candidate: Optional[float] = None


@dataclass
class BacktestResult:
    season: int
    n_candidate_players: int
    n_matched_actuals: int
    candidate_vbd_sum: float
    correlation_with_actual_finish: float
    baselines: Dict[str, BaselineResult] = field(default_factory=dict)


def _season_actuals(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[float, Optional[str]]]:
    """{player_id: (total_actual_points, position)} for a season's REG games."""
    totals: Dict[str, float] = {}
    positions: Dict[str, Dict[str, int]] = {}
    for row in db.actual_season_outcomes(conn, season):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        pts = score_offensive_game(stats)
        pid = row["player_id"]
        totals[pid] = totals.get(pid, 0.0) + pts
        pos_counts = positions.setdefault(pid, {})
        pos_counts[row["position"]] = pos_counts.get(row["position"], 0) + 1

    result: Dict[str, Tuple[float, Optional[str]]] = {}
    for pid, total in totals.items():
        pos = max(positions[pid].items(), key=lambda kv: kv[1])[0]
        result[pid] = (total, pos)
    return result


def _rank_correlation(ranking: RankingConfig, actuals: Dict[str, Tuple[float, Optional[str]]]) -> Tuple[float, int]:
    """Spearman correlation between the ranking's implied order and actual
    points, in matching polarity (+1.0 = perfect: rank 1 scored the most).
    Players in `ranking` absent from `actuals` are scored 0 points -- a
    ranked player who never produced is a bust, not a missing data point.
    """
    player_ids = list(ranking.keys())
    if len(player_ids) < 2:
        return float("nan"), sum(1 for pid in player_ids if pid in actuals)
    candidate_goodness = [-ranking[pid] for pid in player_ids]  # rank 1 -> highest
    actual_points = [actuals.get(pid, (0.0, None))[0] for pid in player_ids]
    n_matched = sum(1 for pid in player_ids if pid in actuals)
    corr, _ = spearmanr(candidate_goodness, actual_points)
    return corr, n_matched


def _vbd_lookup(actuals: Dict[str, Tuple[float, Optional[str]]], levels: ReplacementLevels) -> Dict[str, float]:
    by_position: Dict[str, List[Tuple[str, float]]] = {}
    for pid, (points, pos) in actuals.items():
        if pos is None:
            continue
        by_position.setdefault(pos, []).append((pid, points))
    return compute_vbd(by_position, levels)


def _vbd_sum_for_ranking(
    ranking: RankingConfig,
    actuals: Dict[str, Tuple[float, Optional[str]]],
    vbd: Dict[str, float],
    levels: ReplacementLevels,
) -> float:
    """Sum of actual value-over-replacement for the top-N ranked players at
    each position, N = that position's replacement-level baseline. Tests
    whether the ranking put the players who'd actually beat replacement
    level at the top -- using one shared, empirically-grounded replacement
    baseline (`vbd`) so every ranking system is judged on the same scale.
    """
    baselines = levels.baselines()
    by_position: Dict[str, List[Tuple[int, str]]] = {}
    for pid, rank in ranking.items():
        pos = actuals.get(pid, (0.0, None))[1]
        if pos is None or pos not in baselines:
            continue
        by_position.setdefault(pos, []).append((rank, pid))

    total = 0.0
    for pos, entries in by_position.items():
        entries.sort()  # by rank ascending, best first
        top_n = entries[: baselines[pos]]
        total += sum(vbd.get(pid, 0.0) for _, pid in top_n)
    return total


def _bpa_baseline(store: "db.CutoffEnforcedStore", prior_season: int) -> RankingConfig:
    """Prior-season actual fantasy points, ranked (CLAUDE.md #6.5 baseline #2).
    Routed through the cutoff-enforced store even though prior_season is
    always < cutoff_season by construction -- baselines get the same
    structural guarantee as the candidate, not an exemption."""
    totals: Dict[str, float] = {}
    for row in store.player_week_rows(seasons=[prior_season]):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        totals[row["player_id"]] = totals.get(row["player_id"], 0.0) + score_offensive_game(stats)
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return {pid: i + 1 for i, (pid, _) in enumerate(ranked)}


def _fantasypros_baseline(conn: sqlite3.Connection, season: int) -> RankingConfig:
    """FantasyPros preseason ECR for `season`, from the `rankings` table.
    Uses the latest snapshot on/before Aug 31 of `season` -- inherently a
    pre-Week-1 artifact, not target-season outcome data, so no cutoff
    enforcement is needed here (see docs/CLAUDE.md #6.1)."""
    rows = conn.execute(
        "SELECT player_id, adp_rank FROM rankings "
        "WHERE source = 'fantasypros_ecr' AND as_of_date = ("
        "  SELECT MAX(as_of_date) FROM rankings "
        "  WHERE source = 'fantasypros_ecr' AND as_of_date <= ?"
        ")",
        (f"{season}-08-31",),
    ).fetchall()
    return {pid: rank for pid, rank in rows}


def run_backtest(
    season_year: int,
    ranking_config: RankingConfig,
    db_path: Path = db.DB_PATH,
    levels: Optional[ReplacementLevels] = None,
) -> BacktestResult:
    levels = levels or ReplacementLevels()
    conn = db.connect(db_path)
    try:
        store = db.CutoffEnforcedStore(conn, cutoff_season=season_year)

        actuals = _season_actuals(conn, season_year)
        vbd = _vbd_lookup(actuals, levels)

        candidate_corr, n_matched = _rank_correlation(ranking_config, actuals)
        candidate_vbd_sum = _vbd_sum_for_ranking(ranking_config, actuals, vbd, levels)

        result = BacktestResult(
            season=season_year,
            n_candidate_players=len(ranking_config),
            n_matched_actuals=n_matched,
            candidate_vbd_sum=candidate_vbd_sum,
            correlation_with_actual_finish=candidate_corr,
        )

        # --- BPA: prior season's actual points, ranked ---
        try:
            bpa_ranking = _bpa_baseline(store, season_year - 1)
            bpa_corr, _ = _rank_correlation(bpa_ranking, actuals)
            bpa_vbd = _vbd_sum_for_ranking(bpa_ranking, actuals, vbd, levels)
            result.baselines["bpa_prior_season_points"] = BaselineResult(
                name="bpa_prior_season_points",
                available=True,
                vbd_sum=bpa_vbd,
                correlation_with_actual_finish=bpa_corr,
                delta_vs_candidate=candidate_vbd_sum - bpa_vbd,
            )
        except db.LookAheadViolation as e:
            result.baselines["bpa_prior_season_points"] = BaselineResult(
                name="bpa_prior_season_points", available=False, reason=str(e)
            )

        # --- consensus ADP: not ingested (see module docstring) ---
        result.baselines["consensus_adp"] = BaselineResult(
            name="consensus_adp",
            available=False,
            reason=(
                "No true ADP source ingested. FFC disallows /api/ in robots.txt; "
                "Yahoo/ESPN/Sleeper/Underdog need per-site ToS review (and in "
                "Yahoo/ESPN's case OAuth) not yet done. See docs/deferred.md."
            ),
        )

        # --- FantasyPros preseason ECR ---
        fp_ranking = _fantasypros_baseline(conn, season_year)
        if fp_ranking:
            fp_corr, _ = _rank_correlation(fp_ranking, actuals)
            fp_vbd = _vbd_sum_for_ranking(fp_ranking, actuals, vbd, levels)
            result.baselines["fantasypros_preseason"] = BaselineResult(
                name="fantasypros_preseason",
                available=True,
                vbd_sum=fp_vbd,
                correlation_with_actual_finish=fp_corr,
                delta_vs_candidate=candidate_vbd_sum - fp_vbd,
            )
        else:
            result.baselines["fantasypros_preseason"] = BaselineResult(
                name="fantasypros_preseason",
                available=False,
                reason=(
                    f"No FantasyPros preseason snapshot ingested for {season_year}. "
                    f"Run: python src/ingest_rankings.py --season {season_year}"
                ),
            )

        return result
    finally:
        conn.close()
