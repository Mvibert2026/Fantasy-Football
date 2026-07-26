"""
Draft simulator (deferred item P3-4). Unblocks test-registry #44, #45, the TE/QB
timing question, and #68.

WHY THIS EXISTS. Every metric built before this one measures which players ended
up in a lineup, not what was given up to acquire them. `starter_vbd` (ADR-020)
made cross-positional ordering visible but assumes you receive your top-K picks
uncontested — which is precisely wrong for any "take X earlier than consensus"
strategy, whose entire content is opportunity cost under contention. Taking a
back at pick 3 means not taking the receiver who will be gone by pick 18. Only a
simulator with opponents can price that.

=======================================================================
ASSUMPTIONS. Read these before believing any number this module prints.
=======================================================================

1. OPPONENT NOISE (sigma) IS THE DOMINANT ASSUMPTION AND IS NOT CALIBRATED.
   Opponents draft to consensus ECR perturbed by Gaussian noise. Sigma is in
   units of draft picks. It is NOT fitted to anything: no observed draft-position
   data exists in this repo or is obtainable (ADR-018 — no ADP source). Sigma is
   therefore a guess, and every conclusion must be reported across the sweep in
   SIGMA_SWEEP. A result that holds at one sigma only is an artifact of the
   guess. Default 10.0 = roughly one round in a 10-team league.

2. NOISE IS DRAWN ONCE PER DRAFT, NOT PER PICK. Each simulated draft realises a
   board: every player gets one perturbation held for the whole draft. This
   models "the room collectively valued him a round higher this year", which is
   how players actually slide. Re-drawing per pick would model each team as
   independently confused, which is both less realistic and much noisier.

3. OPPONENTS DO NOT ADAPT. They ignore what the user does and never respond to
   positional runs. This is the known gap in test-registry ("Opponent adaptation
   is unmodelled") and it biases in a specific direction: it makes reaching
   look cheaper than it is, because no one punishes you for it.

4. POSITIONAL NEED IS AN ADDITIVE RANK PENALTY, NOT A UTILITY MODEL. A team at
   or past its target count for a position takes a fixed penalty per surplus
   player, plus a hard cap that forbids absurd rosters. Targets in NEED_TARGETS
   are a judgement call about how real managers behave, not a measurement.

5. DEFENCE IS A CONSTANT. No DST data is ingested (dropped for lack of a
   gsis_id), so the mandatory DEF slot is auto-filled with the final pick and
   contributes zero. It consumes a roster spot for every strategy equally, so it
   cancels in comparisons — but roster totals are understated by one real
   starter's worth of points in absolute terms.

6. LINEUPS ARE SET WITH PERFECT HINDSIGHT. Each week the optimal legal lineup is
   chosen from the roster using that week's ACTUAL points. This is an upper
   bound no manager achieves, applied equally to all strategies. It is exactly
   the decision-cost gap flagged as test-registry #58, and it flatters deep
   rosters relative to top-heavy ones.

7. NO IN-SEASON MANAGEMENT. No waivers, trades, or IR. test-registry #62 notes
   that in-season acquisition may account for much of a championship roster, so
   this simulator measures the draft in isolation, not season outcomes.
"""

from __future__ import annotations

import argparse
import sqlite3
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

import db as dbmod
import holdout as holdout_mod
from config import DEFAULT_CONFIG, stable_offset
from scoring import score_offensive_game

# ----------------------------------------------------------------- league setup
N_TEAMS = 10
N_ROUNDS = 16
USER_SLOT = 3  # 1-indexed; picks 3, 18, 23, 38, 43, ...
STARTERS = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
FLEX_SLOTS = 2
FLEX_ELIGIBLE = ("RB", "WR", "TE")
POSITIONS = ("QB", "RB", "WR", "TE")

# Hard caps: no sane manager drafts a 4th QB in a 1-QB league.
MAX_AT_POSITION = {"QB": 3, "RB": 8, "WR": 9, "TE": 3}
# Counts past which an opponent starts deprioritising a position (assumption 4).
# This is a JUDGEMENT CALL about depth-chart hoarding behaviour, not derived from
# the roster rules -- kept as the default for opponent_pick/simulate_one so the
# PR-003 strategy-comparison numbers (already ADR-028-verified reproducible) do
# not move silently. See MECHANICAL_NEED_TARGETS for the alternative used by the
# availability model (ADR-034), which is derived instead of assumed.
NEED_TARGETS = {"QB": 2, "RB": 5, "WR": 6, "TE": 2}
NEED_PENALTY_PER_SURPLUS = 25.0

# MECHANICAL, not a judgement call: a position stops filling a REQUIRED roster
# slot once a team holds STARTERS[pos] plus, for flex-eligible positions, enough
# to plausibly fill every flex slot (FLEX_SLOTS is a shared pool of 2 across
# RB/WR/TE, so this is an upper bound per position, not a partition of it -- a
# team could need up to FLEX_SLOTS more of ANY eligible position, not all three
# simultaneously). Used by the availability model (ADR-034), not by
# opponent_pick's default (see NEED_TARGETS above).
MECHANICAL_NEED_TARGETS: Dict[str, int] = {
    pos: STARTERS[pos] + (FLEX_SLOTS if pos in FLEX_ELIGIBLE else 0) for pos in POSITIONS
}

DEFAULT_SIGMA = 10.0
SIGMA_SWEEP = (5.0, 10.0, 20.0)


@dataclass
class SeasonData:
    season: int
    player_ids: List[str]
    names: List[str]
    positions: np.ndarray      # index into POSITIONS
    consensus_rank: np.ndarray  # float
    weekly_points: np.ndarray   # (n_players, n_weeks) actual points
    n_weeks: int


@dataclass
class DraftState:
    season: int
    pick_number: int
    round_number: int
    my_roster: List[int]
    my_counts: Dict[str, int]
    taken: np.ndarray  # bool mask


# Strategy signature: (state, available_idx, data, board_rank) -> chosen index
Strategy = Callable[[DraftState, np.ndarray, SeasonData, np.ndarray], int]


# ----------------------------------------------------------------- data loading
def load_season(conn: sqlite3.Connection, season: int) -> SeasonData:
    rows = conn.execute(
        "SELECT player_id, player_name, position, adp_rank FROM rankings "
        "WHERE source='fantasypros_ecr' AND season=? AND position IN ('QB','RB','WR','TE') "
        "ORDER BY adp_rank",
        (season,),
    ).fetchall()
    if not rows:
        raise ValueError(f"no consensus board for {season}")

    ids = [r["player_id"] for r in rows]
    names = [r["player_name"] or r["player_id"] for r in rows]
    pos = np.array([POSITIONS.index(r["position"]) for r in rows], dtype=int)
    rank = np.array([float(r["adp_rank"]) for r in rows])

    idx_of = {pid: i for i, pid in enumerate(ids)}
    max_week = conn.execute(
        "SELECT MAX(week) w FROM player_weekly_stats WHERE season=? AND season_type='REG'",
        (season,),
    ).fetchone()["w"] or 18
    pts = np.zeros((len(ids), max_week + 1))
    for row in dbmod.actual_season_outcomes(conn, season):
        i = idx_of.get(row["player_id"])
        if i is None:
            continue
        stats = {c: row[c] for c in dbmod.SCORING_STAT_COLUMNS}
        pts[i, row["week"]] += score_offensive_game(stats)

    return SeasonData(season, ids, names, pos, rank, pts, max_week)


# ----------------------------------------------------------------- draft order
def pick_order() -> List[int]:
    """Team index (0-based) owning each of the N_TEAMS*N_ROUNDS picks, snake."""
    order = []
    for rnd in range(N_ROUNDS):
        teams = list(range(N_TEAMS))
        if rnd % 2 == 1:
            teams.reverse()
        order.extend(teams)
    return order


def user_pick_numbers() -> List[int]:
    order = pick_order()
    me = USER_SLOT - 1
    return [i + 1 for i, t in enumerate(order) if t == me]


# ----------------------------------------------------------------- opponent model
def _need_penalty(
    counts: Dict[str, int], pos_name: str, targets: Dict[str, int] = NEED_TARGETS
) -> float:
    have = counts.get(pos_name, 0)
    if have >= MAX_AT_POSITION[pos_name]:
        return np.inf
    surplus = have - targets[pos_name] + 1
    return NEED_PENALTY_PER_SURPLUS * surplus if surplus > 0 else 0.0


def opponent_pick(
    effective_rank: np.ndarray,
    available: np.ndarray,
    counts: Dict[str, int],
    data: SeasonData,
    targets: Dict[str, int] = NEED_TARGETS,
) -> int:
    """`targets` defaults to the judgement-call NEED_TARGETS so existing callers
    (simulate_one, the PR-003 strategy comparisons) are unaffected. The
    availability model passes MECHANICAL_NEED_TARGETS instead (ADR-034)."""
    scores = effective_rank.copy()
    for p, name in enumerate(POSITIONS):
        pen = _need_penalty(counts, name, targets)
        if pen:
            scores[data.positions == p] += pen
    scores[~available] = np.inf
    return int(np.argmin(scores))


# ----------------------------------------------------------------- strategies
def _best_by(board: np.ndarray, available: np.ndarray, mask: Optional[np.ndarray] = None) -> int:
    s = board.copy()
    s[~available] = np.inf
    if mask is not None:
        s[~mask] = np.inf
    return int(np.argmin(s))


def _legal_mask(state: DraftState, data: SeasonData) -> np.ndarray:
    """Positions the user may still draft without breaking roster legality."""
    picks_left = N_ROUNDS - 1 - state.round_number  # -1: last round reserved for DEF
    m = np.ones(len(data.positions), dtype=bool)
    for p, name in enumerate(POSITIONS):
        if state.my_counts.get(name, 0) >= MAX_AT_POSITION[name]:
            m[data.positions == p] = False
    # If remaining picks exactly equal remaining mandatory needs, force them.
    needs = [n for n, c in STARTERS.items() if state.my_counts.get(n, 0) < c]
    if needs and picks_left <= len(needs):
        forced = np.zeros(len(data.positions), dtype=bool)
        for n in needs:
            forced |= data.positions == POSITIONS.index(n)
        m &= forced
    return m


def strategy_bpa(state, available, data, board):
    return _best_by(board, available, _legal_mask(state, data))


def _positional_bias(bias: Dict[str, float], early_rounds: int):
    """Generic 'prefer position P in the first N rounds' strategy factory."""
    def strat(state, available, data, board):
        adj = board.copy()
        if state.round_number < early_rounds:
            for name, delta in bias.items():
                adj[data.positions == POSITIONS.index(name)] += delta
        return _best_by(adj, available, _legal_mask(state, data))
    return strat


# Hero RB: strongly prefer a back with the first pick, then lean receiver.
def strategy_hero_rb(state, available, data, board):
    adj = board.copy()
    if state.round_number == 0:
        adj[data.positions != POSITIONS.index("RB")] += 60.0
    elif 1 <= state.round_number <= 5:
        adj[data.positions == POSITIONS.index("RB")] += 30.0
        adj[data.positions == POSITIONS.index("WR")] -= 10.0
    return _best_by(adj, available, _legal_mask(state, data))


# Zero RB: avoid backs entirely in the early rounds.
def strategy_zero_rb(state, available, data, board):
    adj = board.copy()
    if state.round_number < 4:
        adj[data.positions == POSITIONS.index("RB")] += 100.0
    return _best_by(adj, available, _legal_mask(state, data))


strategy_elite_te = _positional_bias({"TE": -45.0}, early_rounds=3)
strategy_qb_early = _positional_bias({"QB": -45.0}, early_rounds=3)


def strategy_balanced(state, available, data, board):
    """Best value with a mild nudge toward unfilled starting slots."""
    adj = board.copy()
    for name, need in STARTERS.items():
        if state.my_counts.get(name, 0) < need:
            adj[data.positions == POSITIONS.index(name)] -= 8.0
    return _best_by(adj, available, _legal_mask(state, data))


STRATEGIES: Dict[str, Strategy] = {
    "bpa_consensus": strategy_bpa,
    "hero_rb": strategy_hero_rb,
    "zero_rb": strategy_zero_rb,
    "elite_te_early": strategy_elite_te,
    "qb_early": strategy_qb_early,
    "balanced": strategy_balanced,
}


# ----------------------------------------------------------------- scoring
def weekly_optimal_points(roster: Sequence[int], data: SeasonData) -> float:
    """Season total under a weekly-optimal legal lineup (assumption 6)."""
    if not roster:
        return 0.0
    idx = np.array(roster)
    pos = data.positions[idx]
    total = 0.0
    for wk in range(1, data.n_weeks + 1):
        pts = data.weekly_points[idx, wk]
        used = np.zeros(len(idx), dtype=bool)
        wk_total = 0.0
        for name, count in STARTERS.items():
            p = POSITIONS.index(name)
            cand = np.where((pos == p) & ~used)[0]
            if len(cand) == 0:
                continue
            best = cand[np.argsort(-pts[cand])][:count]
            wk_total += pts[best].sum()
            used[best] = True
        flex_pool = np.where(
            np.isin(pos, [POSITIONS.index(x) for x in FLEX_ELIGIBLE]) & ~used
        )[0]
        if len(flex_pool):
            best = flex_pool[np.argsort(-pts[flex_pool])][:FLEX_SLOTS]
            wk_total += pts[best].sum()
        total += wk_total
    return float(total)


def roster_is_legal(counts: Dict[str, int]) -> bool:
    for name, need in STARTERS.items():
        if counts.get(name, 0) < need:
            return False
    flex_capacity = sum(counts.get(n, 0) - STARTERS[n] for n in FLEX_ELIGIBLE)
    return flex_capacity >= FLEX_SLOTS


# ----------------------------------------------------------------- simulation
@dataclass
class SimResult:
    strategy: str
    season: int
    sigma: float
    user_points: List[float] = field(default_factory=list)
    opponent_points: List[List[float]] = field(default_factory=list)
    illegal_rosters: int = 0

    @property
    def mean_points(self) -> float:
        return float(np.mean(self.user_points)) if self.user_points else float("nan")

    @property
    def sd_points(self) -> float:
        return float(np.std(self.user_points, ddof=1)) if len(self.user_points) > 1 else float("nan")

    @property
    def p_top4(self) -> float:
        if not self.user_points:
            return float("nan")
        hits = 0
        for mine, opps in zip(self.user_points, self.opponent_points):
            rank = 1 + sum(1 for o in opps if o > mine)
            hits += int(rank <= 4)
        return hits / len(self.user_points)


def simulate_one(
    data: SeasonData, strategy: Strategy, board: np.ndarray, sigma: float, rng: np.random.Generator
) -> Tuple[List[int], List[List[int]], bool]:
    n = len(data.player_ids)
    # Assumption 2: one board realisation per draft.
    effective_rank = data.consensus_rank + rng.normal(0.0, sigma, size=n)
    available = np.ones(n, dtype=bool)
    order = pick_order()
    me = USER_SLOT - 1

    rosters: List[List[int]] = [[] for _ in range(N_TEAMS)]
    counts: List[Dict[str, int]] = [{p: 0 for p in POSITIONS} for _ in range(N_TEAMS)]

    for pick_i, team in enumerate(order):
        rnd = pick_i // N_TEAMS
        if rnd == N_ROUNDS - 1:
            continue  # final round reserved for DEF (assumption 5)
        if team == me:
            state = DraftState(data.season, pick_i + 1, rnd, rosters[me], counts[me], available)
            choice = strategy(state, available, data, board)
        else:
            choice = opponent_pick(effective_rank, available, counts[team], data)
        if not np.isfinite(choice) or not available[choice]:
            continue
        available[choice] = False
        rosters[team].append(int(choice))
        counts[team][POSITIONS[data.positions[choice]]] += 1

    legal = roster_is_legal(counts[me])
    return rosters[me], [rosters[t] for t in range(N_TEAMS) if t != me], legal


def run_strategy(
    data: SeasonData, name: str, strategy: Strategy, board: np.ndarray,
    n_sims: int, sigma: float, seed: int,
) -> SimResult:
    rng = np.random.default_rng(seed)
    res = SimResult(name, data.season, sigma)
    for _ in range(n_sims):
        mine, opps, legal = simulate_one(data, strategy, board, sigma, rng)
        if not legal:
            # A strategy that cannot field a lineup is a FAILED RUN, not a low
            # score -- recording it as 0 points would silently reward it.
            res.illegal_rosters += 1
            continue
        res.user_points.append(weekly_optimal_points(mine, data))
        res.opponent_points.append([weekly_optimal_points(o, data) for o in opps])
    return res


# ----------------------------------------------------------------- uncertainty
def paired_season_bootstrap(
    arm: Dict[int, float], base: Dict[int, float], seed: int, n_boot: int = 5000
) -> Tuple[float, float, float, np.ndarray]:
    """(point, lo, hi, per_season_margins), resampling SEASONS.

    Deliberately returns NO p-value. With a handful of seasons the bootstrap
    distribution of the mean is extremely lumpy -- resampling 2 units yields
    essentially three possible means, so the tail fraction collapses to ~0 or
    ~0.5 and any "p-value" read off it is an artifact of the resampling grid,
    not evidence. Use `sign_test` instead, which is exact and makes the power
    ceiling visible.
    """
    seasons = sorted(set(arm) & set(base))
    d = np.array([arm[s] - base[s] for s in seasons])
    if len(d) == 0:
        return float("nan"), float("nan"), float("nan"), d
    point = float(d.mean())
    if len(d) == 1:
        return point, float("nan"), float("nan"), d
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    means = d[idx].mean(axis=1)
    return point, float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), d


def sign_test(margins: np.ndarray) -> Tuple[int, int, float, float]:
    """Exact two-sided paired sign test over seasons.

    Returns (n_positive, n_seasons, p_value, min_achievable_p).

    Chosen over a bootstrap p-value because it is exact at tiny n and because
    `min_achievable_p` states the power ceiling outright: with 4 seasons the
    smallest attainable two-sided p is 0.125, so NO strategy comparison can
    reach conventional significance at the season level no matter how large the
    effect or how many drafts are simulated. That is a fact about the available
    data, and it belongs in the output rather than in a footnote.
    """
    d = margins[margins != 0]
    n = len(d)
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    k = int((d > 0).sum())
    from math import comb

    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1))
    p = min(1.0, 2.0 * tail / (2 ** n))
    min_p = min(1.0, 2.0 / (2 ** n))
    return k, n, p, min_p


def convergence_check(res: SimResult, points: Sequence[int]) -> List[Tuple[int, float, float]]:
    out = []
    for n in points:
        if n > len(res.user_points):
            continue
        sub = np.array(res.user_points[:n])
        out.append((n, float(sub.mean()), float(sub.std(ddof=1) / np.sqrt(n))))
    return out
