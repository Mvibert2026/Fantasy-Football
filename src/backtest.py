"""
Backtest harness (Phase 1, Step 3), statistically corrected (Task 9).

WHAT CHANGED AND WHY
--------------------
1. NO BLENDED CORRELATION. `_rank_correlation_by_position` returns a per-position
   dict. Pooling QB/RB/WR/TE into one Spearman was the original defect: QBs score
   on a different scale, so a pooled correlation mostly measures whether the
   ranking sorted positions by scale, not whether it ranked players well. Any
   aggregate must be requested explicitly via `weighted_aggregate`, which forces
   the caller to name a weighting and returns it carrying that label.

2. SEASON-LEVEL BOOTSTRAP ONLY. Confidence intervals resample SEASONS, never
   player-weeks (statistical-guardrails.md §7). Player-weeks inside a season are
   correlated, so resampling them would produce intervals far too narrow.
   The cost is honest: with 5 consensus seasons the resample has 5 units, and a
   single-season backtest cannot produce a season-level interval at all. Both
   cases are reported as such (`MetricCI.degenerate`, `.note`) rather than
   silently substituting a narrower method.

3. SEEDED THROUGHOUT. Every bootstrap takes an explicit seed, recorded in the
   result. Unreproducible numbers are not results.

4. PRIMARY BASELINE IS THE RE-SCORED CONSENSUS BOARD (Task 5). The old primary,
   prior-season points, is a weak arm that a candidate should beat trivially.
   The board is the arm that genuinely threatens this project's value.
   Its caveat travels with it in `Arm.label`: it captures POSITIONAL value
   structure under our scoring rules, not player-level scoring-rule edges,
   because no component-level projection source exists (test-registry.md #2).

PAIRED BOOTSTRAP. Arm-vs-baseline deltas resample the same season indices for
both arms within a replication. Independent resampling would inflate the delta's
variance and understate real differences.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import spearmanr

import db
import holdout as holdout_mod
from config import DEFAULT_CONFIG
from scoring import ReplacementLevels, compute_vbd, score_offensive_game

RankingConfig = Dict[str, int]  # player_id -> rank (1 = best)
RankingBuilder = Callable[[sqlite3.Connection, int], RankingConfig]

SCORING_POSITIONS = ("QB", "RB", "WR", "TE")
DEFAULT_N_BOOTSTRAP = 2000
# Deltas below this in absolute terms are treated as arithmetic noise, not wins.
DELTA_TOLERANCE = 1e-6
# Below this many seasons a season-level bootstrap is too degenerate to report
# without a prominent warning attached to every interval it produces.
MIN_SEASONS_FOR_STABLE_CI = 8


# --------------------------------------------------------------------------
# Result containers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PositionCorrelation:
    position: str
    spearman: float
    n_players: int
    n_with_actuals: int


@dataclass(frozen=True)
class WeightedAggregate:
    """A single number across positions. Only produced on explicit request, and
    it carries the weighting used so it can never be mistaken for a pooled
    correlation."""

    value: float
    weighting: str
    label: str


@dataclass(frozen=True)
class MetricCI:
    point: float
    lo: Optional[float]
    hi: Optional[float]
    n_seasons: int
    n_bootstrap: int
    seed: int
    degenerate: bool
    note: str


@dataclass(frozen=True)
class SeasonMetrics:
    season: int
    per_position_spearman: Dict[str, PositionCorrelation]
    vbd_sum: float
    starter_vbd: float


@dataclass
class Arm:
    name: str
    label: str
    build: RankingBuilder
    available: bool = True
    reason: Optional[str] = None


@dataclass
class ArmResult:
    name: str
    label: str
    available: bool
    reason: Optional[str] = None
    per_season: List[SeasonMetrics] = field(default_factory=list)
    vbd_sum_ci: Optional[MetricCI] = None
    starter_vbd_ci: Optional[MetricCI] = None
    spearman_ci: Dict[str, MetricCI] = field(default_factory=dict)
    # Seasons this arm could not be built for, and why. Recorded rather than
    # silently dropped: an arm evaluated on fewer seasons than its comparators
    # is a fact the reader needs.
    skipped_seasons: Dict[int, str] = field(default_factory=dict)


@dataclass
class MultiSeasonResult:
    seasons: List[int]
    primary_baseline: str
    arms: Dict[str, ArmResult] = field(default_factory=dict)
    # {arm_name: {"vbd_sum": MetricCI, "spearman_QB": MetricCI, ...}}
    deltas_vs_primary: Dict[str, Dict[str, MetricCI]] = field(default_factory=dict)
    seed: int = DEFAULT_CONFIG.random_seed
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP
    config: Dict[str, object] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Core metrics
# --------------------------------------------------------------------------


def build_position_lookup(conn: sqlite3.Connection, season: int) -> Dict[str, str]:
    """player_id -> position, for grouping the per-position correlation.

    Sourced from the consensus board for `season` first (which knows positions
    for players who never record a snap) and backfilled from observed weekly
    stats. Without this, a ranked player who busted to zero would be dropped
    from the correlation entirely -- which is the survivorship error the whole
    harness exists to avoid (statistical-guardrails.md §2).
    """
    lookup: Dict[str, str] = {}
    for pid, pos in conn.execute(
        "SELECT player_id, position FROM player_weekly_stats "
        "WHERE season <= ? AND position IS NOT NULL GROUP BY player_id",
        (season,),
    ).fetchall():
        lookup[pid] = pos
    # rankings win: they are the pre-season view of the player's role
    for pid, pos in conn.execute(
        "SELECT player_id, position FROM rankings WHERE season = ? AND position IS NOT NULL",
        (season,),
    ).fetchall():
        lookup[pid] = pos
    return lookup


def _rank_correlation_by_position(
    ranking: RankingConfig,
    actuals: Dict[str, Tuple[float, Optional[str]]],
    positions: Dict[str, str],
) -> Dict[str, PositionCorrelation]:
    """Spearman correlation WITHIN each position group.

    Polarity: +1.0 means the ranking ordered that position perfectly (rank 1
    scored the most). Ranked players absent from `actuals` score 0.0 -- a bust
    is an outcome, not a missing observation.
    """
    grouped: Dict[str, List[Tuple[int, float, bool]]] = {}
    for pid, rank in ranking.items():
        pos = actuals.get(pid, (0.0, None))[1] or positions.get(pid)
        if pos not in SCORING_POSITIONS:
            continue
        pts = actuals.get(pid, (0.0, None))[0]
        grouped.setdefault(pos, []).append((rank, pts, pid in actuals))

    out: Dict[str, PositionCorrelation] = {}
    for pos, entries in grouped.items():
        if len(entries) < 3:
            out[pos] = PositionCorrelation(pos, float("nan"), len(entries),
                                           sum(1 for e in entries if e[2]))
            continue
        goodness = [-e[0] for e in entries]  # rank 1 -> highest
        pts = [e[1] for e in entries]
        if len(set(pts)) < 2:
            corr = float("nan")
        else:
            corr, _ = spearmanr(goodness, pts)
        out[pos] = PositionCorrelation(
            position=pos,
            spearman=float(corr),
            n_players=len(entries),
            n_with_actuals=sum(1 for e in entries if e[2]),
        )
    return out


def weighted_aggregate(
    per_position: Dict[str, PositionCorrelation], weighting: str = "by_n_players"
) -> WeightedAggregate:
    """Collapse per-position correlations into ONE number, on explicit request.

    This is not a pooled correlation and must never be reported as one. It is a
    weighted mean of within-position correlations, and the weighting is part of
    the result so it cannot be quoted without its definition.
    """
    items = [(p, c) for p, c in per_position.items() if not np.isnan(c.spearman)]
    if not items:
        return WeightedAggregate(float("nan"), weighting, "no position had a computable correlation")
    if weighting == "by_n_players":
        w = np.array([c.n_players for _, c in items], dtype=float)
    elif weighting == "equal":
        w = np.ones(len(items), dtype=float)
    else:
        raise ValueError(f"unknown weighting {weighting!r}")
    vals = np.array([c.spearman for _, c in items], dtype=float)
    value = float((vals * w).sum() / w.sum())
    return WeightedAggregate(
        value=value,
        weighting=weighting,
        label=(
            f"weighted mean of WITHIN-position Spearman ({weighting}); "
            f"NOT a pooled cross-position correlation"
        ),
    )


def _season_actuals(
    conn: sqlite3.Connection, season: int
) -> Dict[str, Tuple[float, Optional[str]]]:
    totals: Dict[str, float] = {}
    pos_counts: Dict[str, Dict[str, int]] = {}
    for row in db.actual_season_outcomes(conn, season):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        pid = row["player_id"]
        totals[pid] = totals.get(pid, 0.0) + score_offensive_game(stats)
        counts = pos_counts.setdefault(pid, {})
        counts[row["position"]] = counts.get(row["position"], 0) + 1
    return {
        pid: (total, max(pos_counts[pid].items(), key=lambda kv: kv[1])[0])
        for pid, total in totals.items()
    }


def _vbd_lookup(
    actuals: Dict[str, Tuple[float, Optional[str]]], levels: ReplacementLevels
) -> Dict[str, float]:
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
    positions: Optional[Dict[str, str]] = None,
) -> float:
    """Actual value-over-replacement of the top-N ranked players per position,
    N = that position's replacement baseline.

    KNOWN LIMITATION (docs/deferred.md): this is blind to draft ORDER beyond the
    positional cutoff, so it cannot evaluate strategies whose whole effect is
    *when* a player is taken (Hero RB, Zero RB). It answers "did this ranking
    put the right players in the startable pool", not "was the draft cost worth
    it".
    """
    positions = positions or {}
    baselines = levels.baselines()
    by_position: Dict[str, List[Tuple[int, str]]] = {}
    for pid, rank in ranking.items():
        pos = actuals.get(pid, (0.0, None))[1] or positions.get(pid)
        if pos is None or pos not in baselines:
            continue
        by_position.setdefault(pos, []).append((rank, pid))

    total = 0.0
    for pos, entries in by_position.items():
        entries.sort()
        for _, pid in entries[: baselines[pos]]:
            total += vbd.get(pid, 0.0)
    return total


# Starting lineup for this league: 1QB / 2RB / 3WR / 1TE / 2FLEX (+1DEF, not
# modelled -- no DST ingestion). 15 total picks = 9 starters + 6 bench.
STARTER_SLOTS = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
FLEX_SLOTS = 2
FLEX_ELIGIBLE = ("RB", "WR", "TE")
ROSTER_PICKS = 15


def top_k_starter_vbd(
    ranking: RankingConfig,
    actuals: Dict[str, Tuple[float, Optional[str]]],
    vbd: Dict[str, float],
    positions: Dict[str, str],
    k: int = ROSTER_PICKS,
) -> float:
    """Actual VBD of the best starting lineup fillable from the ranking's top-K.

    WHY THIS EXISTS. `vbd_sum` takes the top-N *per position*, so it is
    invariant to how positions are ordered against each other -- it cannot tell
    the re-scored board apart from raw consensus, because cross-positional
    reordering is the board's only effect. Taking a fixed budget of K picks in
    ranking order makes cross-position ordering matter: spend early picks on a
    position you did not need and the lineup is worse.

    LIMITATION: no opponents. This assumes you receive your top-K uncontested,
    so it measures ordering quality, not draft-day scarcity. A real draft
    simulation (test-registry.md #44) is still the missing piece.
    """
    ordered = sorted(ranking.items(), key=lambda kv: kv[1])[:k]
    open_slots = dict(STARTER_SLOTS)
    flex_left = FLEX_SLOTS
    total = 0.0
    for pid, _ in ordered:
        pos = actuals.get(pid, (0.0, None))[1] or positions.get(pid)
        if pos is None:
            continue
        if open_slots.get(pos, 0) > 0:
            open_slots[pos] -= 1
            total += vbd.get(pid, 0.0)
        elif flex_left > 0 and pos in FLEX_ELIGIBLE:
            flex_left -= 1
            total += vbd.get(pid, 0.0)
    return total


def compute_season_metrics(
    conn: sqlite3.Connection,
    season: int,
    ranking: RankingConfig,
    levels: ReplacementLevels,
) -> SeasonMetrics:
    actuals = _season_actuals(conn, season)
    positions = build_position_lookup(conn, season)
    vbd = _vbd_lookup(actuals, levels)
    return SeasonMetrics(
        season=season,
        per_position_spearman=_rank_correlation_by_position(ranking, actuals, positions),
        vbd_sum=_vbd_sum_for_ranking(ranking, actuals, vbd, levels, positions),
        starter_vbd=top_k_starter_vbd(ranking, actuals, vbd, positions),
    )


# --------------------------------------------------------------------------
# Season-level bootstrap
# --------------------------------------------------------------------------


def _ci_note(n_seasons: int) -> Tuple[bool, str]:
    if n_seasons <= 1:
        return True, (
            "SEASON-LEVEL CI NOT COMPUTABLE: a single season provides one resampling "
            "unit. Reported as a point estimate with no interval. A player-level "
            "bootstrap would look narrower and would be wrong (statistical-guardrails §7)."
        )
    if n_seasons < MIN_SEASONS_FOR_STABLE_CI:
        return True, (
            f"DEGENERATE: only {n_seasons} seasons to resample. The interval is wide and "
            f"itself poorly estimated; treat as an order-of-magnitude indication of "
            f"uncertainty, not a calibrated {int(95)}% interval."
        )
    return False, ""


def bootstrap_season_ci(
    per_season_values: Sequence[float],
    seed: int,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
) -> MetricCI:
    """CI on the across-season mean, resampling SEASONS with replacement."""
    vals = np.array([v for v in per_season_values if not np.isnan(v)], dtype=float)
    n = len(vals)
    degenerate, note = _ci_note(n)
    if n == 0:
        return MetricCI(float("nan"), None, None, 0, 0, seed, True, "no seasons with a value")
    point = float(vals.mean())
    if n <= 1:
        return MetricCI(point, None, None, n, 0, seed, degenerate, note)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_bootstrap, n))
    means = vals[idx].mean(axis=1)
    return MetricCI(
        point=point,
        lo=float(np.percentile(means, 2.5)),
        hi=float(np.percentile(means, 97.5)),
        n_seasons=n,
        n_bootstrap=n_bootstrap,
        seed=seed,
        degenerate=degenerate,
        note=note,
    )


def paired_bootstrap_delta_ci(
    arm_values: Sequence[float],
    baseline_values: Sequence[float],
    seed: int,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
) -> MetricCI:
    """CI on (arm - baseline), resampling the SAME seasons for both arms.

    Paired, because the arms are evaluated on identical seasons. Independent
    resampling would add between-arm variance that does not exist and would
    understate real differences.
    """
    a = np.array(arm_values, dtype=float)
    b = np.array(baseline_values, dtype=float)
    mask = ~(np.isnan(a) | np.isnan(b))
    a, b = a[mask], b[mask]
    n = len(a)
    degenerate, note = _ci_note(n)
    if n == 0:
        return MetricCI(float("nan"), None, None, 0, 0, seed, True, "no paired seasons")
    point = float((a - b).mean())
    if n <= 1:
        return MetricCI(point, None, None, n, 0, seed, degenerate, note)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_bootstrap, n))
    deltas = (a[idx] - b[idx]).mean(axis=1)
    return MetricCI(
        point=point,
        lo=float(np.percentile(deltas, 2.5)),
        hi=float(np.percentile(deltas, 97.5)),
        n_seasons=n,
        n_bootstrap=n_bootstrap,
        seed=seed,
        degenerate=degenerate,
        note=note,
    )


# --------------------------------------------------------------------------
# Standard arms
# --------------------------------------------------------------------------


def bpa_prior_season_ranking(conn: sqlite3.Connection, season: int) -> RankingConfig:
    """Prior season's actual points, ranked. Routed through the cutoff-enforced
    store so baselines get the same structural guarantee as candidates."""
    store = db.CutoffEnforcedStore(conn, cutoff_season=season)
    totals: Dict[str, float] = {}
    for row in store.player_week_rows(seasons=[season - 1]):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        totals[row["player_id"]] = totals.get(row["player_id"], 0.0) + score_offensive_game(stats)
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return {pid: i + 1 for i, (pid, _) in enumerate(ranked)}


def fantasypros_ranking(conn: sqlite3.Connection, season: int) -> RankingConfig:
    """Raw consensus rank as published -- no re-scoring."""
    rows = conn.execute(
        "SELECT player_id, adp_rank FROM rankings "
        "WHERE source = 'fantasypros_ecr' AND season = ?",
        (season,),
    ).fetchall()
    return {pid: rank for pid, rank in rows}


def rescored_board_ranking(conn: sqlite3.Connection, season: int) -> RankingConfig:
    """PRIMARY baseline: consensus re-scored into our league's positional value
    structure (src/make_board.py). Imported lazily to keep the import graph
    acyclic."""
    from make_board import board_ranking_for_season

    return board_ranking_for_season(conn, season)


def standard_arms() -> Dict[str, Arm]:
    return {
        "rescored_consensus_board": Arm(
            name="rescored_consensus_board",
            label=(
                "PRIMARY BASELINE. Consensus ranks re-scored into our positional value "
                "structure via E[our_points | position, consensus positional rank]. "
                "CAVEAT: captures positional structure only, NOT player-level "
                "scoring-rule edges -- every player at the same positional rank shares "
                "a projection, because no component-level projection source exists "
                "(test-registry.md #2)."
            ),
            build=rescored_board_ranking,
        ),
        "fantasypros_ecr_raw": Arm(
            name="fantasypros_ecr_raw",
            label="Consensus expert rank as published, no re-scoring.",
            build=fantasypros_ranking,
        ),
        "bpa_prior_season_points": Arm(
            name="bpa_prior_season_points",
            label=(
                "Prior season's actual points, ranked. Weak arm, retained because "
                "CLAUDE.md §6.5 requires it."
            ),
            build=bpa_prior_season_ranking,
        ),
        "consensus_adp": Arm(
            name="consensus_adp",
            label="Observed market average draft position.",
            build=lambda conn, season: {},
            available=False,
            reason=(
                "No market ADP source is obtainable within CLAUDE.md §10 constraints. "
                "nflverse has none; DynastyProcess has none; FFC has it but robots.txt "
                "disallows /api/ and /adp/csv/; FantasyPros ADP pages need a Terms-of-Use "
                "review first. See docs/decisions.md ADR-018."
            ),
        ),
    }


# --------------------------------------------------------------------------
# Runners
# --------------------------------------------------------------------------


def run_backtest_multi(
    seasons: Sequence[int],
    candidate: Optional[RankingBuilder] = None,
    candidate_name: str = "candidate",
    candidate_label: str = "candidate ranking under test",
    db_path: Path = db.DB_PATH,
    levels: Optional[ReplacementLevels] = None,
    arms: Optional[Dict[str, Arm]] = None,
    primary_baseline: str = "rescored_consensus_board",
    seed: int = DEFAULT_CONFIG.random_seed,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    enforce_holdout: bool = True,
) -> MultiSeasonResult:
    # Structural enforcement, not a convention: evaluating on the locked
    # holdout raises unless the caller has opened an explicit, logged
    # final-evaluation context (src/holdout.py).
    if enforce_holdout:
        holdout_mod.DEFAULT_LOCK.guard(seasons, purpose="backtest evaluation")
    levels = levels or ReplacementLevels()
    arms = dict(arms or standard_arms())
    if candidate is not None:
        arms[candidate_name] = Arm(candidate_name, candidate_label, candidate)

    conn = db.connect(db_path)
    try:
        results: Dict[str, ArmResult] = {}
        for name, arm in arms.items():
            if not arm.available:
                results[name] = ArmResult(name, arm.label, False, arm.reason)
                continue
            per_season: List[SeasonMetrics] = []
            skipped: Dict[int, str] = {}
            for season in seasons:
                try:
                    ranking = arm.build(conn, season)
                except (ValueError, db.LookAheadViolation) as e:
                    # e.g. the re-scored board needs >=1 prior consensus season,
                    # so it cannot exist for the first year of consensus coverage.
                    skipped[season] = str(e)
                    continue
                if not ranking:
                    skipped[season] = "arm produced an empty ranking for this season"
                    continue
                per_season.append(compute_season_metrics(conn, season, ranking, levels))
            results[name] = ArmResult(
                name, arm.label, True, None, per_season, skipped_seasons=skipped
            )
    finally:
        conn.close()

    # Confidence intervals per arm
    for name, res in results.items():
        if not res.available or not res.per_season:
            continue
        res.vbd_sum_ci = bootstrap_season_ci(
            [m.vbd_sum for m in res.per_season], seed=seed, n_bootstrap=n_bootstrap
        )
        res.starter_vbd_ci = bootstrap_season_ci(
            [m.starter_vbd for m in res.per_season], seed=seed + 1, n_bootstrap=n_bootstrap
        )
        for pos in SCORING_POSITIONS:
            vals = [
                m.per_position_spearman[pos].spearman
                for m in res.per_season
                if pos in m.per_position_spearman
            ]
            if vals:
                res.spearman_ci[pos] = bootstrap_season_ci(
                    vals, seed=seed + hash(pos) % 1000, n_bootstrap=n_bootstrap
                )

    # Paired deltas against the primary baseline
    deltas: Dict[str, Dict[str, MetricCI]] = {}
    base = results.get(primary_baseline)
    if base is not None and base.available and base.per_season:
        base_by_season = {m.season: m for m in base.per_season}
        for name, res in results.items():
            if name == primary_baseline or not res.available or not res.per_season:
                continue
            shared = [m.season for m in res.per_season if m.season in base_by_season]
            if not shared:
                continue
            arm_by_season = {m.season: m for m in res.per_season}
            d: Dict[str, MetricCI] = {
                "vbd_sum": paired_bootstrap_delta_ci(
                    [arm_by_season[s].vbd_sum for s in shared],
                    [base_by_season[s].vbd_sum for s in shared],
                    seed=seed,
                    n_bootstrap=n_bootstrap,
                ),
                "starter_vbd": paired_bootstrap_delta_ci(
                    [arm_by_season[s].starter_vbd for s in shared],
                    [base_by_season[s].starter_vbd for s in shared],
                    seed=seed + 1,
                    n_bootstrap=n_bootstrap,
                ),
            }
            for pos in SCORING_POSITIONS:
                a, b = [], []
                for s in shared:
                    pa = arm_by_season[s].per_position_spearman.get(pos)
                    pb = base_by_season[s].per_position_spearman.get(pos)
                    if pa and pb:
                        a.append(pa.spearman)
                        b.append(pb.spearman)
                if a:
                    d[f"spearman_{pos}"] = paired_bootstrap_delta_ci(
                        a, b, seed=seed + hash(pos) % 1000, n_bootstrap=n_bootstrap
                    )
            deltas[name] = d

    return MultiSeasonResult(
        seasons=list(seasons),
        primary_baseline=primary_baseline,
        arms=results,
        deltas_vs_primary=deltas,
        seed=seed,
        n_bootstrap=n_bootstrap,
        config=DEFAULT_CONFIG.describe(),
    )


def format_report(result: MultiSeasonResult) -> str:
    lines: List[str] = []
    lines.append("BACKTEST REPORT")
    lines.append("=" * 78)
    lines.append(f"seasons evaluated : {result.seasons}  (n={len(result.seasons)})")
    lines.append(f"primary baseline  : {result.primary_baseline}")
    lines.append(f"seed              : {result.seed}   bootstrap reps: {result.n_bootstrap}")
    lines.append(f"config            : {result.config}")
    lines.append("")
    lines.append("Correlations are WITHIN position. There is deliberately no pooled")
    lines.append("cross-position correlation -- pooling was the original defect.")
    lines.append("")

    for name, arm in result.arms.items():
        marker = " [PRIMARY]" if name == result.primary_baseline else ""
        lines.append(f"--- {name}{marker} ---")
        if not arm.available:
            lines.append(f"  UNAVAILABLE: {arm.reason}")
            lines.append("")
            continue
        lines.append(f"  {arm.label}")
        if arm.skipped_seasons:
            for s, why in sorted(arm.skipped_seasons.items()):
                lines.append(f"  SKIPPED {s}: {why}")
        for metric_name, c in (("vbd_sum", arm.vbd_sum_ci), ("starter_vbd", arm.starter_vbd_ci)):
            if not c:
                continue
            ci = f"[{c.lo:.1f}, {c.hi:.1f}]" if c.lo is not None else "[no interval]"
            lines.append(
                f"  {metric_name:<12}: {c.point:8.1f}  95% CI {ci}   (n_seasons={c.n_seasons})"
            )
        if arm.vbd_sum_ci and arm.vbd_sum_ci.degenerate:
            lines.append(f"    ! {arm.vbd_sum_ci.note}")
        for pos in SCORING_POSITIONS:
            c = arm.spearman_ci.get(pos)
            if not c:
                continue
            ci = f"[{c.lo:+.3f}, {c.hi:+.3f}]" if c.lo is not None else "[no interval]"
            lines.append(f"  spearman {pos:<3}: {c.point:+.3f}  95% CI {ci}")
        lines.append("")

    if result.deltas_vs_primary:
        lines.append(f"--- DELTAS vs {result.primary_baseline} (paired season bootstrap) ---")
        lines.append("  A CI spanning zero means no demonstrated difference.")
        for name, d in result.deltas_vs_primary.items():
            lines.append(f"  {name}:")
            for metric, c in d.items():
                ci = f"[{c.lo:+.3f}, {c.hi:+.3f}]" if c.lo is not None else "[no interval]"
                verdict = ""
                if c.lo is not None:
                    # Tolerance, not a bare sign test: a delta of ~1e-13 with a
                    # CI of the same width is arithmetic noise, not a win.
                    if abs(c.point) < DELTA_TOLERANCE and abs(c.hi - c.lo) < DELTA_TOLERANCE:
                        verdict = "  IDENTICAL (metric cannot distinguish these arms)"
                    elif c.lo > DELTA_TOLERANCE:
                        verdict = "  BEATS"
                    elif c.hi < -DELTA_TOLERANCE:
                        verdict = "  LOSES"
                    else:
                        verdict = "  no difference"
                lines.append(f"    {metric:<18} {c.point:+9.3f}  95% CI {ci}{verdict}")
            first = next(iter(d.values()), None)
            if first is not None and first.degenerate:
                lines.append(f"    ! {first.note}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=None,
        help="Seasons to evaluate. Defaults to the development set (holdout excluded).",
    )
    parser.add_argument("--db", type=Path, default=db.DB_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_N_BOOTSTRAP)
    parser.add_argument(
        "--final-evaluation",
        metavar="REASON",
        default=None,
        help=(
            "Open a logged final-evaluation context so the locked holdout season may be "
            "read. One-time use per pre-registered test."
        ),
    )
    args = parser.parse_args()

    seasons = args.seasons or holdout_mod.DEFAULT_LOCK.development_seasons()

    def _run():
        return run_backtest_multi(
            seasons, db_path=args.db, seed=args.seed, n_bootstrap=args.bootstrap
        )

    if args.final_evaluation:
        with holdout_mod.DEFAULT_LOCK.final_evaluation(reason=args.final_evaluation):
            result = _run()
    else:
        result = _run()

    print(format_report(result))
    print(f"holdout season (locked): {holdout_mod.HOLDOUT_SEASON}")
    if holdout_mod.HOLDOUT_SEASON not in seasons:
        print("  holdout NOT touched by this run")


if __name__ == "__main__":
    main()
