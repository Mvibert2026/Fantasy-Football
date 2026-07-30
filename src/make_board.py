"""
Re-scored consensus draft board (Task 5).

TWO PURPOSES
  (a) A usable draft artifact that stands alone regardless of whether any
      modelling work finishes. The draft date is fixed; this must work.
  (b) The PRIMARY null hypothesis for the backtest. The old "BPA" arm was
      prior-year VBD -- a weak baseline expected to lose. Consensus re-scored
      under our rules is the baseline that genuinely threatens this project's
      value. If the model cannot beat this, it has no edge.

WHAT THIS IS NOT -- READ BEFORE TRUSTING `projected_points`.
The task asked to "re-score every player under our league rules". That requires
COMPONENT-LEVEL projections (pass yds, rush yds, receptions, TDs per player).
No such source is available: FantasyPros ECR is rank-only (verified -- it has
ecr/sd/best/worst and no projection columns), and test-registry.md #2 documents
this as the project's single biggest external blocker.

So `projected_points` here is NOT a re-scored player projection. It is:

    E[our_points | position, consensus positional rank]

fitted from HISTORICAL seasons using our scoring engine (bonuses, negatives and
all). What that buys us, honestly:

  IT DOES capture our league's positional value structure -- how many points a
  positional rank is actually worth under OUR rules, which is what drives VBD
  and therefore the whole board ordering.

  IT DOES NOT capture player-specific scoring-rule edges. A spike-week WR who
  clears the 100/150/200 bonuses more often than the average WR at his rank is
  invisible to this method; he gets the average for his rank. Capturing that
  needs component projections (test-registry #2) or a player-level
  distribution model (test-registry #38).

Every player at the same positional rank gets the same projection. The board's
value is in the positional re-weighting, not in disagreeing with consensus
about individual players.

ESTIMATOR CHOICE -- AND A REJECTED ONE. The first implementation fitted an
isotonic (monotone-decreasing) regression per position on per-rank mean points.
It was discarded after inspection: with 5 training seasons there are only 5
observations per rank, and the raw rank->points relation is dominated by noise
(consensus QB10 outscored consensus QB1 in 2 of 5 seasons; RB1 season values
ranged 40 to 366). Isotonic regression responded by imposing monotonicity the
data does not support, and the resulting board put a QB at overall #1 purely
because the fit forced the QB10 replacement value ~70 points below its own raw
mean. That was an artifact of the estimator, not a finding about quarterbacks.

The current estimator fits, per position, a smooth two-parameter curve

    points ~ alpha + beta * ln(positional_rank)

on all individual player-seasons inside the DRAFT-RELEVANT depth. Two
parameters estimated from 100-300 observations is far more stable than ~50
parameters estimated from 5 observations each, and it is monotone by
construction (beta < 0) rather than by imposition.

The fit's R-squared is reported and is LOW (roughly 0.16-0.27 by position).
That is not a defect in the curve; it is the honest size of the signal.
Consensus draft rank explains under a third of the variance in what a player
actually scores. Every projection here carries a bootstrap confidence interval
for that reason -- ranks whose intervals overlap are not distinguishable.

LOOK-AHEAD: the rank->points curve for season S is fitted ONLY on seasons
strictly before S. Enforced in fit_rank_curves() and covered by tests.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

import db as dbmod
from config import DEFAULT_CONFIG
from scoring import ReplacementLevels, score_offensive_game

BOARD_POSITIONS = ("QB", "RB", "WR", "TE")  # no kicker in this league; DST handled separately
# Thread 053/067 (ADR pending): SOURCE is the CURRENT-SEASON consensus board
# the app displays and ranks against -- rewired here from the old
# `fantasypros_ecr` DynastyProcess mirror (rank-only, no scoring-format info,
# effectively capped) onto the founder's own FantasyPros Half-PPR CSV export
# (real scoring_format, tier, bye_week, sos_season columns; see
# ingest_fantasypros_csv.py).
#
# TRAINING_SOURCE stays on `fantasypros_ecr` deliberately. The rank->points
# curve (fit_rank_curves) needs MULTIPLE PRIOR SEASONS of consensus rank data
# to fit against -- `fantasypros_csv_2026draft` is a single one-off 2026 pull
# with no season history at all (see rankings table: fantasypros_ecr has
# 2021-2025, the new CSV source has only 2026). Pointing the curve fit at
# SOURCE would silently starve every position of training observations
# (collect_observations would return empty per season, _fit_one would return
# None for lack of >=5 points, and build_board would drop every position from
# the board with no error). Swapping the *training* source is a real
# statistical-methodology change (a different rank methodology / player pool
# feeding the E[points | rank] curve) and is deliberately NOT made in this
# pass -- only the current-season display/consensus source changes. Revisit
# once fantasypros_csv_2026draft (or a successor CSV source) has multiple
# seasons on file.
SOURCE = "fantasypros_csv_2026draft"
TRAINING_SOURCE = "fantasypros_ecr"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_N_BOOTSTRAP = 2000

# Draft-relevant depth per position in a 10-team league (3WR/2RB/1TE/2FLEX/1QB,
# 6 bench). Beyond these ranks players go undrafted, and including the long tail
# of never-played zeros would bend the curve in the range we actually draft
# from. Generous enough to cover every plausible pick.
RELEVANT_DEPTH = {"QB": 20, "RB": 45, "WR": 60, "TE": 20}


@dataclass(frozen=True)
class RankCurve:
    """points ~ intercept + slope_log_rank * ln(rank), fitted per position."""

    position: str
    intercept: float
    slope_log_rank: float
    r_squared: float
    residual_sd: float
    n_obs: int
    max_rank_fitted: int

    def predict(self, rank: float) -> float:
        return float(self.intercept + self.slope_log_rank * np.log(max(1.0, float(rank))))


@dataclass
class BoardRow:
    overall_rank: int
    player: str
    position: str
    projected_points: float
    vbd: float
    vbd_lo: float
    vbd_hi: float
    consensus_rank: int
    delta_vs_consensus: int
    # nflverse gsis-style id (rankings.player_id is aliased from gsis_id at
    # ingest, ingest_rankings.py). Same id space as player_weekly_stats.player_id,
    # the join key export_history.py's weekly_finishes.json/season_stats.json
    # already use (thread 017/039) -- carrying it here, not a new identifier
    # scheme, is what lets export_contract.py populate board.json's
    # player_id_gsis instead of hardcoding None (thread 052). Optional because
    # BoardRow is also hand-constructed in tests without needing an id.
    player_id: Optional[str] = None


def _season_actual_points(
    conn: sqlite3.Connection, season: int, scoring_cfg: Optional[dict] = None
) -> Dict[str, float]:
    """Total points each player actually scored in `season`, under `scoring_cfg`
    (defaults to this project's primary league's rules -- see
    score_offensive_game's own cfg=None default). ADR-041: without this param,
    a board built for a different league would silently score every player
    under the PRIMARY league's scoring rules regardless of what that league's
    LeagueConfig actually specifies -- a real parameterization gap, not a
    hypothetical one."""
    totals: Dict[str, float] = {}
    for row in dbmod.actual_season_outcomes(conn, season):
        stats = {c: row[c] for c in dbmod.SCORING_STAT_COLUMNS}
        pid = row["player_id"]
        totals[pid] = totals.get(pid, 0.0) + score_offensive_game(stats, cfg=scoring_cfg)
    return totals


def _consensus_board(
    conn: sqlite3.Connection, season: int, source: str = SOURCE
) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT player_id, player_name, position, adp_rank FROM rankings "
        "WHERE source = ? AND season = ? AND as_of_date = "
        "  (SELECT MAX(as_of_date) FROM rankings WHERE source = ? AND season = ?) "
        "ORDER BY adp_rank",
        (source, season, source, season),
    ).fetchall()


def _positional_ranks(rows: Sequence[sqlite3.Row]) -> Dict[str, List[sqlite3.Row]]:
    by_pos: Dict[str, List[sqlite3.Row]] = {}
    for r in rows:
        if r["position"] not in BOARD_POSITIONS:
            continue
        by_pos.setdefault(r["position"], []).append(r)
    for pos in by_pos:
        by_pos[pos].sort(key=lambda r: r["adp_rank"])
    return by_pos


def resolve_training_seasons(
    conn: sqlite3.Connection, target_season: int, training_seasons: Optional[Sequence[int]] = None,
    source: str = TRAINING_SOURCE,
) -> List[int]:
    if training_seasons is None:
        training_seasons = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT season FROM rankings WHERE source = ? AND season < ? "
                "ORDER BY season",
                (source, target_season),
            ).fetchall()
        ]
    leaking = [s for s in training_seasons if s >= target_season]
    if leaking:
        raise ValueError(
            f"training seasons {leaking} are at or after target_season {target_season}; "
            "the rank->points curve may only be fitted on prior seasons (CLAUDE.md §6.1)"
        )
    if not training_seasons:
        raise ValueError(
            f"no consensus seasons before {target_season} to fit a rank->points curve"
        )
    return list(training_seasons)


def collect_observations(
    conn: sqlite3.Connection, seasons: Sequence[int], scoring_cfg: Optional[dict] = None,
    source: str = TRAINING_SOURCE,
) -> Dict[int, Dict[str, List[tuple[int, float]]]]:
    """{season: {position: [(positional_rank, actual_points), ...]}}.

    A ranked player with no stat line scored zero -- a bust is an outcome, not
    a missing observation (statistical-guardrails.md §2).

    `source` defaults to TRAINING_SOURCE (the historical `fantasypros_ecr`
    mirror), not SOURCE -- these are the prior-season consensus boards the
    rank->points curve trains on, and only TRAINING_SOURCE has multi-season
    history on file.
    """
    out: Dict[int, Dict[str, List[tuple[int, float]]]] = {}
    for season in seasons:
        actuals = _season_actual_points(conn, season, scoring_cfg)
        per_pos: Dict[str, List[tuple[int, float]]] = {}
        for pos, rows in _positional_ranks(_consensus_board(conn, season, source=source)).items():
            limit = RELEVANT_DEPTH.get(pos)
            if limit is None:
                continue
            per_pos[pos] = [
                (i, actuals.get(r["player_id"], 0.0))
                for i, r in enumerate(rows, start=1)
                if i <= limit
            ]
        out[season] = per_pos
    return out


def _fit_one(pos: str, pairs: Sequence[tuple[int, float]]) -> Optional[RankCurve]:
    if len(pairs) < 5:
        return None
    arr = np.asarray(pairs, dtype=float)
    lr = np.log(arr[:, 0])
    y = arr[:, 1]
    X = np.column_stack([np.ones(len(lr)), lr])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    dof = max(1, len(y) - 2)
    return RankCurve(
        position=pos,
        intercept=float(beta[0]),
        slope_log_rank=float(beta[1]),
        r_squared=(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0,
        residual_sd=float(np.sqrt(ss_res / dof)),
        n_obs=len(y),
        max_rank_fitted=int(arr[:, 0].max()),
    )


def fit_rank_curves(
    conn: sqlite3.Connection, target_season: int, training_seasons: Optional[Sequence[int]] = None,
    scoring_cfg: Optional[dict] = None,
) -> Dict[str, RankCurve]:
    """Fit E[our_points | positional consensus rank] per position.

    Only seasons STRICTLY BEFORE `target_season` are used -- fitting on the
    target season would leak its outcomes into its own board.
    """
    seasons = resolve_training_seasons(conn, target_season, training_seasons)
    obs = collect_observations(conn, seasons, scoring_cfg)
    pooled: Dict[str, List[tuple[int, float]]] = {p: [] for p in BOARD_POSITIONS}
    for per_pos in obs.values():
        for pos, pairs in per_pos.items():
            pooled.setdefault(pos, []).extend(pairs)
    curves = {}
    for pos, pairs in pooled.items():
        c = _fit_one(pos, pairs)
        if c is not None:
            curves[pos] = c
    return curves


def bootstrap_vbd_intervals(
    conn: sqlite3.Connection,
    target_season: int,
    levels: ReplacementLevels,
    training_seasons: Optional[Sequence[int]] = None,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    seed: int = DEFAULT_CONFIG.random_seed,
    scoring_cfg: Optional[dict] = None,
) -> Dict[str, Dict[int, tuple[float, float]]]:
    """95% CI on VBD at each rank, resampling SEASONS (statistical-guardrails
    §7: season-level, not player-level, to respect within-season correlation).

    With 5 training seasons the resample has 5 units, so these intervals are
    wide. That width is the honest result, not a defect to engineer away.
    """
    seasons = resolve_training_seasons(conn, target_season, training_seasons)
    obs = collect_observations(conn, seasons, scoring_cfg)
    baselines = levels.baselines()
    rng = np.random.default_rng(seed)

    draws: Dict[str, Dict[int, List[float]]] = {p: {} for p in RELEVANT_DEPTH}
    for _ in range(n_bootstrap):
        picks = rng.choice(seasons, size=len(seasons), replace=True)
        for pos, depth in RELEVANT_DEPTH.items():
            pairs: List[tuple[int, float]] = []
            for s in picks:
                pairs.extend(obs[int(s)].get(pos, []))
            curve = _fit_one(pos, pairs)
            base_rank = baselines.get(pos)
            if curve is None or base_rank is None:
                continue
            repl = curve.predict(base_rank)
            for rank in range(1, depth + 1):
                draws[pos].setdefault(rank, []).append(curve.predict(rank) - repl)

    out: Dict[str, Dict[int, tuple[float, float]]] = {}
    for pos, by_rank in draws.items():
        out[pos] = {
            rank: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
            for rank, v in by_rank.items()
            if v
        }
    return out


def build_board(
    conn: sqlite3.Connection,
    season: int,
    levels: Optional[ReplacementLevels] = None,
    training_seasons: Optional[Sequence[int]] = None,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    seed: int = DEFAULT_CONFIG.random_seed,
    scoring_cfg: Optional[dict] = None,
    source: str = SOURCE,
) -> tuple[List[BoardRow], Dict[str, RankCurve]]:
    """`source` is the CURRENT-SEASON consensus board being ranked (default:
    SOURCE, the live fantasypros_csv_2026draft board). It is independent of
    the historical rank->points curve fit, which always trains on
    TRAINING_SOURCE via fit_rank_curves/bootstrap_vbd_intervals regardless of
    this argument -- see the SOURCE/TRAINING_SOURCE split note above."""
    levels = levels or ReplacementLevels()
    baselines = levels.baselines()
    curves = fit_rank_curves(conn, season, training_seasons, scoring_cfg=scoring_cfg)
    intervals = bootstrap_vbd_intervals(
        conn, season, levels, training_seasons, n_bootstrap=n_bootstrap, seed=seed,
        scoring_cfg=scoring_cfg,
    )
    by_pos = _positional_ranks(_consensus_board(conn, season, source=source))

    # Replacement points per position = the curve's value at that position's
    # replacement rank (QB10/RB30/WR40/TE10 for this 10-team league; ADR-029).
    replacement = {
        pos: curve.predict(baselines[pos])
        for pos, curve in curves.items()
        if pos in baselines
    }

    scored: List[tuple[float, float, sqlite3.Row, str, int]] = []
    for pos, rows in by_pos.items():
        curve = curves.get(pos)
        if curve is None:
            continue
        for i, r in enumerate(rows, start=1):
            proj = curve.predict(i)
            vbd = proj - replacement.get(pos, 0.0)
            scored.append((vbd, proj, r, pos, i))

    scored.sort(key=lambda t: -t[0])
    board: List[BoardRow] = []
    for overall, (vbd, proj, r, pos, pos_rank) in enumerate(scored, start=1):
        lo, hi = intervals.get(pos, {}).get(pos_rank, (float("nan"), float("nan")))
        board.append(
            BoardRow(
                overall_rank=overall,
                player=r["player_name"] or r["player_id"],
                position=pos,
                projected_points=round(proj, 2),
                vbd=round(vbd, 2),
                vbd_lo=round(lo, 2),
                vbd_hi=round(hi, 2),
                consensus_rank=r["adp_rank"],
                # positive => our board is higher on the player than consensus
                delta_vs_consensus=r["adp_rank"] - overall,
                player_id=r["player_id"],
            )
        )
    return board, curves


def write_board_csv(board: Sequence[BoardRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "overall_rank", "player", "position", "projected_points",
            "vbd", "vbd_lo95", "vbd_hi95", "consensus_rank", "delta_vs_consensus",
        ])
        for r in board:
            w.writerow([
                r.overall_rank, r.player, r.position, r.projected_points,
                r.vbd, r.vbd_lo, r.vbd_hi, r.consensus_rank, r.delta_vs_consensus,
            ])


def board_ranking_for_season(
    conn: sqlite3.Connection, season: int, levels: Optional[ReplacementLevels] = None
) -> Dict[str, int]:
    """The re-scored consensus board as a {player_id: rank} config, for use as
    the PRIMARY baseline arm in backtest.py (Task 5b).

    Backtests run over HISTORICAL seasons, which only exist under
    TRAINING_SOURCE ('fantasypros_ecr', 2021-2025) -- SOURCE
    ('fantasypros_csv_2026draft') is a 2026-only one-off pull with no
    historical seasons on file. Explicitly uses TRAINING_SOURCE here (not the
    build_board/board.json default of SOURCE) so this baseline arm keeps
    working for every backtest season, not just 2026."""
    board, _ = build_board(conn, season, levels=levels, n_bootstrap=0, source=TRAINING_SOURCE)
    return board_as_ranking(board, conn, season, source=TRAINING_SOURCE)


def board_as_ranking(
    board: Sequence[BoardRow], conn: sqlite3.Connection, season: int, source: str = SOURCE
) -> Dict[str, int]:
    """The board as a {player_id: rank} config, for use as a backtest baseline."""
    name_to_id = {
        (r["player_name"] or r["player_id"]): r["player_id"]
        for r in _consensus_board(conn, season, source=source)
    }
    return {
        name_to_id[r.player]: r.overall_rank
        for r in board
        if r.player in name_to_id
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--db", type=Path, default=dbmod.DB_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    conn = dbmod.connect(args.db)
    try:
        board, curves = build_board(conn, args.season)
        out = args.out_dir / f"board_{args.season}.csv"
        write_board_csv(board, out)

        meta = conn.execute(
            "SELECT DISTINCT as_of_date, is_preseason_final FROM rankings "
            "WHERE source = ? AND season = ?",
            (SOURCE, args.season),
        ).fetchone()
        train = [
            r[0] for r in conn.execute(
                "SELECT DISTINCT season FROM rankings WHERE source = ? AND season < ? "
                "ORDER BY season", (TRAINING_SOURCE, args.season)
            ).fetchall()
        ]
    finally:
        conn.close()

    print(f"Board for {args.season}: {len(board)} players -> {out}")
    print(f"  consensus as_of={meta[0]}" + ("" if meta[1] else "  [IN-PROGRESS BOARD]"))
    print(f"  rank->points curve fitted on seasons: {train}")
    print()
    print("  CURVE FITS (points ~ a + b*ln(rank)); low R2 = consensus rank is a weak")
    print("  predictor of outcome. This is the signal size, not a bug in the fit.")
    for pos in BOARD_POSITIONS:
        c = curves.get(pos)
        if c:
            print(
                f"    {pos:<3} a={c.intercept:7.1f} b={c.slope_log_rank:+7.1f}  "
                f"R2={c.r_squared:.3f}  resid_sd={c.residual_sd:5.1f}  n={c.n_obs}"
            )
    print()
    print(
        f"{'#':>3} {'player':<24} {'pos':<3} {'proj':>7} {'vbd':>7} "
        f"{'vbd 95% CI':>17} {'cons':>5} {'delta':>6}"
    )
    for r in board[:20]:
        ci = f"[{r.vbd_lo:7.1f},{r.vbd_hi:7.1f}]"
        print(
            f"{r.overall_rank:>3} {r.player[:24]:<24} {r.position:<3} "
            f"{r.projected_points:>7.1f} {r.vbd:>7.1f} {ci:>17} "
            f"{r.consensus_rank:>5} {r.delta_vs_consensus:>+6}"
        )


if __name__ == "__main__":
    main()
