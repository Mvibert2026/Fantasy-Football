"""
Backtest harness (Phase 1, Step 3), statistically corrected (Task 9; ADR-B thread 021).

WHAT CHANGED AND WHY
--------------------
0. ADR-B (docs/adr-drafts/ADR-B-rank-correlation-aggregation.md, thread 021).
   `_rank_correlation_by_position` returns Kendall's tau_b as PRIMARY (Spearman
   kept as a fixed secondary), computed within a pre-registered, position-specific
   depth cutoff (`DEPTH_CUTOFFS`), with NO aggregate across positions permitted
   anywhere -- not computed, not stored, not logged, not even on explicit
   request. `weighted_aggregate` (the previous Task-9 escape hatch) is DELETED,
   not merely unused: a field that does not exist cannot be misquoted. No
   minimum-games-played filter exists anywhere in this module; ranked players
   with no realized production score zero and stay in the sample. Realized
   producers outside the ranked top-K are excluded from tau_b (no prediction to
   pair) and reported as a mandatory `misses` line instead of being dropped
   silently.

1. NO BLENDED CORRELATION. Pooling QB/RB/WR/TE into one Spearman was the
   original defect: QBs score on a different scale, so a pooled correlation
   mostly measures whether the ranking sorted positions by scale, not whether it
   ranked players well.

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

5. NEVER-PLAYED RANKED PLAYERS SCORE THE REPLACEMENT DEFICIT, NOT ZERO VBD
   (2026-07-30, strategist finding, docs/adr-drafts/ADR-DRAFT-primary-
   evaluation-metric.md SS4.1). `vbd.get(pid, 0.0)` used to silently score a
   ranked player with no weekly row at all (retired, cut, season-ending
   injury) as exactly replacement level -- a materially better outcome than
   the wasted premium pick that actually happened. `_slot_value` now scores
   that player's slot at `0 - replacement_points[pos]`. This is an
   evaluation-harness fix only: no ranking logic, weight, or export field
   changed. ADR-025's published board-vs-consensus figures were computed
   under the defect and have been re-reported alongside the originals, not
   overwritten -- see ADR-025's correction note in docs/decisions.md.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import kendalltau, spearmanr

import db
import holdout as holdout_mod
from config import DEFAULT_CONFIG, stable_offset
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

# ADR-B: per-position depth cutoffs, frozen. (primary K = 2x replacement,
# secondary K = at replacement). NOT to be tuned after seeing results -- see
# ADR-B "Exact computation" for the a-priori justification of 2x. DEF has no
# replacement level in this codebase (no DST scoring ingested -- CURRENT-STATE)
# so it is listed for documentation completeness but never populated.
DEPTH_CUTOFFS: Dict[str, Tuple[int, int]] = {
    "RB": (60, 30),
    "WR": (80, 40),
    "TE": (20, 10),
    "QB": (20, 10),
    "DEF": (20, 10),
}
# ADR-B instability override: primary-vs-secondary-K disagreement, or
# tau_b-vs-Spearman disagreement, beyond this magnitude demotes the position to
# `unstable` regardless of the band its tau_b would otherwise land in.
INSTABILITY_DELTA = 0.15
# ADR-B specifies "a 10,000-draw seeded permutation reference distribution."
# DEFAULT here is lowered to 2,000 for wall-clock reasons ONLY (scipy's
# kendalltau has real per-call overhead; a full multi-arm/multi-season/
# multi-position backtest at 10,000 draws runs into tens of minutes). This is
# a compute-budget deviation, not a statistical one -- percentile bootstrap
# intervals are stable to ~2 decimal places by 2,000 draws for these sample
# sizes. `n_permutation` is threaded through every public entry point so a
# final, careful run can be taken at the ADR's literal 10,000. Flagged in the
# thread 021 reply rather than silently substituted.
DEFAULT_N_PERMUTATION = 2_000

# ADR-B pre-committed decision bands, keyed by primary-K tau_b. Ordered
# weakest-first so the uninformative override can step one band down.
DECISION_BANDS: List[Tuple[float, str]] = [
    (0.10, "no_ordering_skill"),
    (0.25, "weak"),
    (0.40, "moderate"),
    (float("inf"), "strong"),
]
BAND_ORDER = [name for _, name in DECISION_BANDS]


def _band_for_tau(tau: float) -> str:
    if np.isnan(tau):
        return "no_ordering_skill"
    for hi, name in DECISION_BANDS:
        if tau < hi:
            return name
    return "strong"


def _lower_band(band: str) -> str:
    idx = BAND_ORDER.index(band)
    return BAND_ORDER[max(0, idx - 1)]


# --------------------------------------------------------------------------
# Result containers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PositionCorrelation:
    """ADR-B per-position result. There is deliberately no field anywhere in
    this module that aggregates across positions -- "no aggregate may be
    computed, stored, or logged" (ADR-B). A field that does not exist cannot be
    misquoted."""

    position: str
    tau_b: float                     # PRIMARY (ADR-B)
    spearman: float                  # secondary, fixed, never swapped in
    n_players: int                   # size of the primary-K ranked pool
    n_with_actuals: int
    k_primary: int
    k_secondary: int
    tau_b_secondary: float           # tau_b recomputed at the secondary (at-replacement) K
    permutation_lo: Optional[float]
    permutation_hi: Optional[float]
    permutation_seed: int
    permutation_n: int
    unstable: bool                   # primary/secondary or tau_b/Spearman disagree by > 0.15
    band: str                        # ADR-B decision band, after overrides
    misses_n: int                    # realized top-K producers outside our ranked set
    misses: Tuple[str, ...]          # their player_ids -- never silently dropped


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
    per_position_correlation: Dict[str, PositionCorrelation]
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
    tau_b_ci: Dict[str, MetricCI] = field(default_factory=dict)      # PRIMARY (ADR-B)
    spearman_ci: Dict[str, MetricCI] = field(default_factory=dict)   # secondary
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


def _tau_and_rho(ranks: Sequence[int], pts: Sequence[float]) -> Tuple[float, float]:
    """Kendall's tau_b (primary, ADR-B) and Spearman's rho (fixed secondary) for
    one paired sample. NaN when fewer than 3 pairs or when either side is
    constant (both coefficients are undefined there, not zero)."""
    if len(ranks) < 3 or len(set(pts)) < 2:
        return float("nan"), float("nan")
    goodness = [-r for r in ranks]  # rank 1 (best) -> highest "goodness"
    tau, _ = kendalltau(goodness, pts, variant="b")
    rho, _ = spearmanr(goodness, pts)
    return float(tau), float(rho)


def _permutation_ci_tau_b(
    ranks: Sequence[int], pts: Sequence[float], seed: int, n_draws: int = DEFAULT_N_PERMUTATION
) -> Tuple[Optional[float], Optional[float]]:
    """95% interval on tau_b via a seeded percentile bootstrap of the PAIRED
    sample (resample players with replacement, recompute tau_b each draw).

    ADR-B calls this a "permutation reference distribution"; implemented here
    as a pair-level bootstrap, not a label-shuffle null, because it is the
    observed estimate's own uncertainty that the ADR's override rule needs
    ("if the position's 95% permutation interval contains 0") -- a label-shuffle
    null is centered on zero by construction and would trigger the override
    almost everywhere regardless of signal, which cannot be the intent. Uses
    the same percentile-bootstrap style as `bootstrap_season_ci` elsewhere in
    this module for consistency. Flagged approximate at n <= 20 per ADR-B.
    """
    n = len(ranks)
    if n < 3 or len(set(pts)) < 2:
        return None, None
    ranks_arr = np.asarray(ranks)
    pts_arr = np.asarray(pts, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_draws, n))
    taus = np.empty(n_draws, dtype=float)
    for i in range(n_draws):
        r = ranks_arr[idx[i]]
        p = pts_arr[idx[i]]
        if len(set(p.tolist())) < 2:
            taus[i] = np.nan
            continue
        tau, _ = kendalltau(-r, p, variant="b")
        taus[i] = tau
    taus = taus[~np.isnan(taus)]
    if len(taus) == 0:
        return None, None
    return float(np.percentile(taus, 2.5)), float(np.percentile(taus, 97.5))


def _rank_correlation_by_position(
    ranking: RankingConfig,
    actuals: Dict[str, Tuple[float, Optional[str]]],
    positions: Dict[str, str],
    seed: int = DEFAULT_CONFIG.random_seed,
    n_permutation: int = DEFAULT_N_PERMUTATION,
) -> Dict[str, PositionCorrelation]:
    """ADR-B (thread 021): Kendall's tau_b PRIMARY, within each position's
    pre-registered depth cutoff. No pooled cross-position figure exists in this
    module -- see module docstring point 0. No minimum-games-played filter:
    ranked players with no realized production score 0.0 and stay in the
    sample (the survivorship error this whole harness exists to avoid).

    Polarity: +1.0 means the ranking ordered that position perfectly (rank 1
    scored the most).

    `positions` supplies position for players who never recorded a stat line
    (from `build_position_lookup`); `actuals`' own position (from the observed
    stat line) wins when both are known, since it reflects what the player
    actually played, not just where the model or board filed them.
    """
    # Full within-position predicted order, from the RANKED set only (ADR-B:
    # "prospective, by predicted rank" -- selecting on realized rank would be
    # look-ahead selection).
    grouped: Dict[str, List[Tuple[str, int]]] = {}
    for pid, rank in ranking.items():
        pos = actuals.get(pid, (0.0, None))[1] or positions.get(pid)
        if pos not in DEPTH_CUTOFFS:
            continue
        grouped.setdefault(pos, []).append((pid, rank))

    out: Dict[str, PositionCorrelation] = {}
    for pos, ranked_pairs in grouped.items():
        k_primary, k_secondary = DEPTH_CUTOFFS[pos]
        ranked_pairs.sort(key=lambda kv: kv[1])  # ascending predicted rank = best first
        top_primary = ranked_pairs[:k_primary]
        top_secondary = ranked_pairs[:k_secondary]

        r_primary = [rank for _, rank in top_primary]
        p_primary = [actuals.get(pid, (0.0, None))[0] for pid, _ in top_primary]
        r_secondary = [rank for _, rank in top_secondary]
        p_secondary = [actuals.get(pid, (0.0, None))[0] for pid, _ in top_secondary]

        tau_b, spearman = _tau_and_rho(r_primary, p_primary)
        tau_b_secondary, _ = _tau_and_rho(r_secondary, p_secondary)
        perm_lo, perm_hi = _permutation_ci_tau_b(
            r_primary, p_primary, seed=seed + stable_offset(pos), n_draws=n_permutation
        )

        unstable = False
        if not (np.isnan(tau_b) or np.isnan(tau_b_secondary)):
            unstable = unstable or abs(tau_b - tau_b_secondary) > INSTABILITY_DELTA
        if not (np.isnan(tau_b) or np.isnan(spearman)):
            unstable = unstable or abs(tau_b - spearman) > INSTABILITY_DELTA

        band = _band_for_tau(tau_b)
        if unstable:
            band = "unstable"
        elif perm_lo is not None and perm_lo <= 0.0 <= perm_hi:
            band = _lower_band(band)

        # Mandatory misses line: realized top-K producers at this position who
        # were never in our ranked top-K. Excluded from tau_b (no prediction to
        # pair against) but never silently dropped.
        realized_this_pos = [
            (pid, pts) for pid, (pts, p) in actuals.items()
            if (p or positions.get(pid)) == pos
        ]
        realized_this_pos.sort(key=lambda kv: -kv[1])
        top_realized_ids = {pid for pid, _ in realized_this_pos[:k_primary]}
        ranked_ids = {pid for pid, _ in top_primary}
        misses = tuple(sorted(top_realized_ids - ranked_ids))

        out[pos] = PositionCorrelation(
            position=pos,
            tau_b=tau_b,
            spearman=spearman,
            n_players=len(top_primary),
            n_with_actuals=sum(1 for pid, _ in top_primary if pid in actuals),
            k_primary=k_primary,
            k_secondary=k_secondary,
            tau_b_secondary=tau_b_secondary,
            permutation_lo=perm_lo,
            permutation_hi=perm_hi,
            permutation_seed=seed + stable_offset(pos),
            permutation_n=n_permutation,
            unstable=unstable,
            band=band,
            misses_n=len(misses),
            misses=misses,
        )
    return out


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
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Returns (vbd, replacement_points).

    `vbd` covers only players present in `actuals` (i.e. with at least one
    weekly stat row), same as before. `replacement_points` is the per-position
    POINT VALUE (not a player count) at the replacement baseline, computed
    from the exact same universe and the exact same index arithmetic
    `scoring.compute_vbd` uses internally -- duplicated here (not imported)
    because `compute_vbd` does not expose it. It is what a ranked player who
    resolves a position but has NO row in `actuals` must be scored against:
    his true contribution is `0 - replacement_points[pos]`, never `0.0`. See
    docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md SS4.1.
    """
    by_position: Dict[str, List[Tuple[str, float]]] = {}
    for pid, (points, pos) in actuals.items():
        if pos is None:
            continue
        by_position.setdefault(pos, []).append((pid, points))
    vbd = compute_vbd(by_position, levels)
    baselines = levels.baselines()
    replacement_points: Dict[str, float] = {}
    for pos, players in by_position.items():
        ranked = sorted((pts for _, pts in players), reverse=True)
        if not ranked:
            continue
        idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1)
        replacement_points[pos] = ranked[idx]
    return vbd, replacement_points


def _slot_value(
    pid: str,
    pos: str,
    vbd: Dict[str, float],
    replacement_points: Dict[str, float],
) -> float:
    """Value contributed by a player who consumes a starting slot.

    If `pid` has a realized `vbd` entry (i.e. he appears in that season's
    `_season_actuals`, including a genuine zero-point season that actually
    happened), that value is exact and used as-is.

    If `pid` has NO entry at all -- retired, cut, a season-ending injury,
    suspended for the year, anything with zero weekly rows -- he still
    consumed a starting slot the ranking chose to spend on him. His true
    contribution is `0 - replacement_points[pos]`: exactly as bad as drafting
    the worst startable player at that position and getting nothing back for
    the pick, which is what actually happened. `vbd.get(pid, 0.0)` used to
    silently return `0.0` here -- "as good as the waiver wire" -- which is a
    materially better outcome than a wasted premium pick and is the defect
    this function exists to fix (ADR-DRAFT-primary-evaluation-metric.md SS4.1).
    """
    if pid in vbd:
        return vbd[pid]
    return -replacement_points.get(pos, 0.0)


def _vbd_sum_for_ranking(
    ranking: RankingConfig,
    actuals: Dict[str, Tuple[float, Optional[str]]],
    vbd: Dict[str, float],
    levels: ReplacementLevels,
    positions: Optional[Dict[str, str]] = None,
    replacement_points: Optional[Dict[str, float]] = None,
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
    replacement_points = replacement_points or {}
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
            total += _slot_value(pid, pos, vbd, replacement_points)
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
    replacement_points: Optional[Dict[str, float]] = None,
) -> float:
    """Actual VBD of the best starting lineup fillable from the ranking's top-K.

    WHY THIS EXISTS. `vbd_sum` takes the top-N *per position*, so it is
    invariant to how positions are ordered against each other -- it cannot tell
    the re-scored board apart from raw consensus, because cross-positional
    reordering is the board's only effect. Taking a fixed budget of K picks in
    ranking order makes cross-position ordering matter: spend early picks on a
    position you did not need and the lineup is worse.

    A ranked player who consumes a slot but has no realized production at all
    (no row in `actuals`) is scored via `_slot_value` against
    `replacement_points`, not at a silent `0.0` -- see `_slot_value`'s
    docstring and ADR-DRAFT-primary-evaluation-metric.md SS4.1.

    LIMITATION: no opponents. This assumes you receive your top-K uncontested,
    so it measures ordering quality, not draft-day scarcity. A real draft
    simulation (test-registry.md #44) is still the missing piece.
    """
    replacement_points = replacement_points or {}
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
            total += _slot_value(pid, pos, vbd, replacement_points)
        elif flex_left > 0 and pos in FLEX_ELIGIBLE:
            flex_left -= 1
            total += _slot_value(pid, pos, vbd, replacement_points)
    return total


def compute_season_metrics(
    conn: sqlite3.Connection,
    season: int,
    ranking: RankingConfig,
    levels: ReplacementLevels,
    seed: int = DEFAULT_CONFIG.random_seed,
    n_permutation: int = DEFAULT_N_PERMUTATION,
) -> SeasonMetrics:
    actuals = _season_actuals(conn, season)
    positions = build_position_lookup(conn, season)
    vbd, replacement_points = _vbd_lookup(actuals, levels)
    return SeasonMetrics(
        season=season,
        per_position_correlation=_rank_correlation_by_position(
            ranking, actuals, positions, seed=seed + season, n_permutation=n_permutation
        ),
        vbd_sum=_vbd_sum_for_ranking(
            ranking, actuals, vbd, levels, positions, replacement_points
        ),
        starter_vbd=top_k_starter_vbd(
            ranking, actuals, vbd, positions, replacement_points=replacement_points
        ),
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
    n_permutation: int = DEFAULT_N_PERMUTATION,
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
                per_season.append(
                    compute_season_metrics(
                        conn, season, ranking, levels, seed=seed, n_permutation=n_permutation
                    )
                )
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
            tau_vals = [
                m.per_position_correlation[pos].tau_b
                for m in res.per_season
                if pos in m.per_position_correlation
            ]
            if tau_vals:
                res.tau_b_ci[pos] = bootstrap_season_ci(
                    tau_vals, seed=seed + stable_offset(pos), n_bootstrap=n_bootstrap
                )
            spearman_vals = [
                m.per_position_correlation[pos].spearman
                for m in res.per_season
                if pos in m.per_position_correlation
            ]
            if spearman_vals:
                res.spearman_ci[pos] = bootstrap_season_ci(
                    spearman_vals, seed=seed + stable_offset(pos) + 1, n_bootstrap=n_bootstrap
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
                a_tau, b_tau, a_rho, b_rho = [], [], [], []
                for s in shared:
                    pa = arm_by_season[s].per_position_correlation.get(pos)
                    pb = base_by_season[s].per_position_correlation.get(pos)
                    if pa and pb:
                        a_tau.append(pa.tau_b)
                        b_tau.append(pb.tau_b)
                        a_rho.append(pa.spearman)
                        b_rho.append(pb.spearman)
                if a_tau:
                    d[f"tau_b_{pos}"] = paired_bootstrap_delta_ci(
                        a_tau, b_tau, seed=seed + stable_offset(pos), n_bootstrap=n_bootstrap
                    )
                if a_rho:
                    d[f"spearman_{pos}"] = paired_bootstrap_delta_ci(
                        a_rho, b_rho, seed=seed + stable_offset(pos) + 1, n_bootstrap=n_bootstrap
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
    lines.append("Correlations are WITHIN position, Kendall's tau_b PRIMARY / Spearman")
    lines.append("secondary (ADR-B, thread 021). There is deliberately no pooled")
    lines.append("cross-position figure, and no aggregate across positions anywhere in")
    lines.append("this report -- pooling was the original defect.")
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
            ct = arm.tau_b_ci.get(pos)
            cr = arm.spearman_ci.get(pos)
            if ct:
                ci = f"[{ct.lo:+.3f}, {ct.hi:+.3f}]" if ct.lo is not None else "[no interval]"
                lines.append(f"  tau_b    {pos:<3}: {ct.point:+.3f}  95% CI {ci}  (across-season)")
            if cr:
                ci = f"[{cr.lo:+.3f}, {cr.hi:+.3f}]" if cr.lo is not None else "[no interval]"
                lines.append(f"  spearman {pos:<3}: {cr.point:+.3f}  95% CI {ci}  (secondary)")
            # Per-season detail: band, misses, within-season permutation interval.
            for m in arm.per_season:
                pc = m.per_position_correlation.get(pos)
                if not pc:
                    continue
                perm = (
                    f"[{pc.permutation_lo:+.3f}, {pc.permutation_hi:+.3f}]"
                    if pc.permutation_lo is not None
                    else "[no interval]"
                )
                lines.append(
                    f"    {m.season} {pos:<3}: tau_b={pc.tau_b:+.3f} rho={pc.spearman:+.3f} "
                    f"n={pc.n_players} (K={pc.k_primary}/{pc.k_secondary}) "
                    f"perm95% {perm} band={pc.band}"
                    + ("  UNSTABLE" if pc.unstable else "")
                )
                if pc.misses_n:
                    lines.append(
                        f"      misses: {pc.misses_n} of the top-{pc.k_primary} realized "
                        f"{pos} were outside our ranked set: {list(pc.misses)}"
                    )
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
