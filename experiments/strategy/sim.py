"""FR-085 draft-strategy simulator. Rules in
`docs/ranking/fr085-strategy-sim-precommit.md`, fixed before this ran.

This is a SEPARATE implementation from `src/draft_sim.py` and deliberately so:
that module's PR-003 numbers are ADR-028-verified byte-reproducible and are not
worth perturbing. What is inherited is its opponent model and its stated
assumptions; what changes is listed in the pre-commitment §4 (per-player measured
sigma, randomised draft slot, a real head-to-head season, and the three-layer
board).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from experiments.strategy.board import Board, POSITIONS

N_TEAMS = 10
N_ROUNDS_FULL = 16          # 15 offensive + 1 reserved for DEF
STARTERS = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
FLEX_SLOTS = 2
FLEX_ELIGIBLE = ("RB", "WR", "TE")
# Hard caps. QB and TE are tightened from src/draft_sim.py's {QB:3, TE:3} to 2,
# and the reason is a measurement rather than taste: this league starts one QB,
# and ADR-029 measured the TE share of flex slots at 0.00 over 26 seasons (a TE
# won a flex slot in 2 of 26). A third QB or third TE therefore cannot enter a
# lineup in any week, so allowing one only lets a deep-tail artifact in the value
# curve spend a roster spot on a player who is structurally unstartable.
MAX_AT_POSITION = {"QB": 2, "RB": 8, "WR": 9, "TE": 2}
NEED_TARGETS = {"QB": 2, "RB": 5, "WR": 6, "TE": 2}
NEED_PENALTY_PER_SURPLUS = 25.0
REGULAR_WEEKS = 15
PLAYOFF_WEEKS = (16, 17)
INF = float("inf")


# --------------------------------------------------------------------- schedule
def round_robin(n: int = N_TEAMS, weeks: int = REGULAR_WEEKS) -> List[List[Tuple[int, int]]]:
    """Circle-method round robin, repeated to fill `weeks`. Fixed and identical
    for every strategy, so schedule luck cannot favour one of them."""
    teams = list(range(n))
    rounds = []
    for _ in range(n - 1):
        pairs = [(teams[i], teams[n - 1 - i]) for i in range(n // 2)]
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return [rounds[w % len(rounds)] for w in range(weeks)]


SCHEDULE = round_robin()


# -------------------------------------------------------------------- strategies
@dataclass
class State:
    round_number: int
    counts: Dict[str, int]


Strategy = Callable[[State, np.ndarray, Board, np.ndarray, np.ndarray], int]


def need_penalty_vector(counts: Dict[str, int], board: Board) -> np.ndarray:
    """The project's EXISTING positional-need penalty (src/draft_sim.py), in RANK
    units, applied to the user exactly as it is applied to the nine opponents.

    AMENDMENT to the pre-commitment, made 2026-07-30 after a 5-simulation smoke
    test and BEFORE any strategy comparison was computed -- see
    `docs/ranking/fr085-strategy-sim-precommit.md` §5.2. Pure unconstrained
    "always take the highest VBD" drafts 9 WR and 3 QB, because WR VBD stays
    positive down to the WR40 replacement level while RB's crosses zero at RB30.
    That is arithmetically correct and is not what anyone means by drafting to
    VBD. Rather than invent a new constant, the user now carries the same
    NEED_TARGETS / NEED_PENALTY_PER_SURPLUS the opponent model has always used,
    so the need model is the project's, not one chosen today."""
    pen = np.zeros(len(board.pos_idx))
    for p, name in enumerate(POSITIONS):
        have = counts.get(name, 0)
        surplus = have - NEED_TARGETS[name] + 1
        if surplus > 0:
            pen[board.pos_idx == p] = NEED_PENALTY_PER_SURPLUS * surplus
    return pen


def _legal_mask(state: State, board: Board, rounds_total: int) -> np.ndarray:
    """Positions the user may still take without ending up unable to field a
    lineup. `picks_left` counts THIS pick and every remaining offensive pick.

    Unfilled slots are counted as (mandatory starters still short) + (flex slots
    still uncovered), not just the former -- a roster with 1 QB / 2 RB / 3 WR /
    1 TE satisfies every mandatory starter and still cannot field two flex, so
    forcing on mandatory starters alone produces illegal rosters. Caught in the
    smoke test, before any strategy comparison existed."""
    picks_left = (rounds_total - 1) - state.round_number
    m = np.ones(len(board.pos_idx), dtype=bool)
    for p, name in enumerate(POSITIONS):
        if state.counts.get(name, 0) >= MAX_AT_POSITION[name]:
            m[board.pos_idx == p] = False
    short = [nm for nm, c in STARTERS.items() if state.counts.get(nm, 0) < c]
    flex_have = sum(max(0, state.counts.get(nm, 0) - STARTERS[nm]) for nm in FLEX_ELIGIBLE)
    flex_short = max(0, FLEX_SLOTS - flex_have)
    # PLAYERS still required, not POSITIONS still short -- a roster needing two
    # more RBs needs two picks, not one. Counting positions under-forces and
    # produced rosters that could not field a lineup at 11 rounds.
    required = sum(STARTERS[nm] - state.counts.get(nm, 0) for nm in short) + flex_short
    if required and picks_left <= required:
        forced = np.zeros(len(board.pos_idx), dtype=bool)
        for nm in (short if short else FLEX_ELIGIBLE):
            forced |= board.pos_idx == POSITIONS.index(nm)
        if flex_short and not short:
            forced = np.zeros(len(board.pos_idx), dtype=bool)
            for nm in FLEX_ELIGIBLE:
                forced |= board.pos_idx == POSITIONS.index(nm)
        if (m & forced).any():
            m &= forced
    return m


def _argmin_masked(score: np.ndarray, available: np.ndarray, mask: np.ndarray) -> int:
    s = np.where(available & mask, score, INF)
    if not np.isfinite(s).any():
        s = np.where(available, score, INF)
    return int(np.argmin(s))


def strategy_vbd(state, available, board, mask, consensus_rank):
    return _argmin_masked(board.vbd_rank + need_penalty_vector(state.counts, board),
                          available, mask)


def strategy_bpa_consensus(state, available, board, mask, consensus_rank):
    return _argmin_masked(consensus_rank + need_penalty_vector(state.counts, board),
                          available, mask)


def make_zero_rb(ban_rounds: int) -> Strategy:
    rb = POSITIONS.index("RB")

    def strat(state, available, board, mask, consensus_rank):
        m = mask
        if state.round_number < ban_rounds:
            m = mask & (board.pos_idx != rb)
            if not (available & m).any():
                m = mask
        return _argmin_masked(board.vbd_rank + need_penalty_vector(state.counts, board),
                              available, m)
    return strat


def make_robust_rb(force_rounds: int = 2) -> Strategy:
    rb = POSITIONS.index("RB")

    def strat(state, available, board, mask, consensus_rank):
        m = mask
        if state.round_number < force_rounds:
            forced = mask & (board.pos_idx == rb)
            if (available & forced).any():
                m = forced
        return _argmin_masked(board.vbd_rank + need_penalty_vector(state.counts, board),
                              available, m)
    return strat


def strategy_balanced(state, available, board, mask, consensus_rank):
    score = board.vbd_rank + need_penalty_vector(state.counts, board)
    short = [nm for nm, c in STARTERS.items() if state.counts.get(nm, 0) < c]
    if short:
        m = np.zeros(len(board.pos_idx), dtype=bool)
        for nm in short:
            m |= board.pos_idx == POSITIONS.index(nm)
        m &= mask
        if (available & m).any():
            return _argmin_masked(score, available, m)
    surplus = sum(max(0, state.counts.get(nm, 0) - STARTERS[nm]) for nm in FLEX_ELIGIBLE)
    if surplus < FLEX_SLOTS:
        m = np.zeros(len(board.pos_idx), dtype=bool)
        for nm in FLEX_ELIGIBLE:
            m |= board.pos_idx == POSITIONS.index(nm)
        m &= mask
        if (available & m).any():
            return _argmin_masked(score, available, m)
    return _argmin_masked(score, available, mask)


PRIMARY_STRATEGIES: Dict[str, Strategy] = {
    "vbd": strategy_vbd,
    "zero_rb": make_zero_rb(4),
    "robust_rb": make_robust_rb(2),
    "balanced": strategy_balanced,
    "bpa_consensus": strategy_bpa_consensus,
}
SENSITIVITY_STRATEGIES: Dict[str, Strategy] = {
    "zero_rb_ban3": make_zero_rb(3),
    "zero_rb_ban5": make_zero_rb(5),
    "zero_rb_ban6": make_zero_rb(6),
}
ALL_STRATEGIES = {**PRIMARY_STRATEGIES, **SENSITIVITY_STRATEGIES}


# ------------------------------------------------------------------- one draft
def _pick_order(rounds_total: int) -> np.ndarray:
    order = []
    for rnd in range(rounds_total):
        teams = list(range(N_TEAMS))
        if rnd % 2 == 1:
            teams.reverse()
        order.extend(teams)
    return np.array(order)


def _opponent_pick(effective_rank: np.ndarray, available: np.ndarray,
                   counts: Dict[str, int], board: Board) -> int:
    scores = effective_rank.copy()
    for p, name in enumerate(POSITIONS):
        have = counts.get(name, 0)
        if have >= MAX_AT_POSITION[name]:
            scores[board.pos_idx == p] = INF
            continue
        surplus = have - NEED_TARGETS[name] + 1
        if surplus > 0:
            scores[board.pos_idx == p] += NEED_PENALTY_PER_SURPLUS * surplus
    scores = np.where(available, scores, INF)
    return int(np.argmin(scores))


def simulate_draft(board: Board, strategy: Strategy, user_slot: int,
                   noise: np.ndarray, rounds_total: int
                   ) -> Tuple[List[List[int]], bool]:
    n = len(board.pos_idx)
    effective = board.consensus_rank + noise
    available = np.ones(n, dtype=bool)
    order = _pick_order(rounds_total)
    rosters: List[List[int]] = [[] for _ in range(N_TEAMS)]
    counts = [{p: 0 for p in POSITIONS} for _ in range(N_TEAMS)]

    for pick_i, team in enumerate(order):
        rnd = pick_i // N_TEAMS
        if rnd == rounds_total - 1:
            continue                       # final round reserved for DEF
        if team == user_slot:
            st = State(rnd, counts[team])
            mask = _legal_mask(st, board, rounds_total)
            choice = strategy(st, available, board, mask, board.consensus_rank)
        else:
            choice = _opponent_pick(effective, available, counts[team], board)
        if not available[choice]:
            continue
        available[choice] = False
        rosters[team].append(choice)
        counts[team][POSITIONS[board.pos_idx[choice]]] += 1

    legal = all(counts[user_slot].get(nm, 0) >= need for nm, need in STARTERS.items()) and \
        sum(counts[user_slot].get(nm, 0) - STARTERS[nm] for nm in FLEX_ELIGIBLE) >= FLEX_SLOTS
    return rosters, legal


# ------------------------------------------------------------------ evaluation
FLEX_P = tuple(POSITIONS.index(x) for x in FLEX_ELIGIBLE)


def _take_top(eligible: np.ndarray, count: int) -> np.ndarray:
    """(m, W) bool -> the first `count` True entries down each column.

    `eligible` must already be in preference order along axis 0."""
    cum = np.cumsum(eligible, axis=0)
    return eligible & (cum <= count)


def _lineup_weekly(idx: np.ndarray, board: Board, best_ball: bool) -> np.ndarray:
    """(n_weeks+1,) weekly points for one roster.

    best_ball=True  -> metric A: optimal legal lineup with perfect hindsight.
                       An upper bound no manager reaches; flatters deep rosters.
    best_ball=False -> metric B: start the highest-valued roster players (shared
                       VBD board, the same currency every strategy drafted on)
                       who actually appeared in a game that week. No in-season
                       skill, no waivers; flatters top-heavy rosters.

    Both are vectorised over weeks. The preference order for metric B is the
    shared VBD board rather than raw consensus, because that is the board every
    strategy actually drafted from -- using consensus would penalise exactly the
    strategies that deviate from it, which is the thing under test.
    """
    if len(idx) == 0:
        return np.zeros(board.n_weeks + 1)
    W = board.n_weeks + 1
    order = np.argsort(board.vbd_rank[idx], kind="stable")   # best first
    idx = idx[order]
    pos = board.pos_idx[idx]
    pts = board.weekly[idx]
    playing = board.appeared[idx] if not best_ball else np.ones_like(board.appeared[idx])

    used = np.zeros((len(idx), W), dtype=bool)
    total = np.zeros(W)
    for name, count in STARTERS.items():
        p = POSITIONS.index(name)
        rows = np.where(pos == p)[0]
        if len(rows) == 0:
            continue
        elig = playing[rows] & ~used[rows]
        if best_ball:
            # preference order is that week's realised points, not board order
            rank = np.argsort(np.argsort(-pts[rows], axis=0, kind="stable"),
                              axis=0, kind="stable")
            sel = elig & (rank < count)
        else:
            sel = _take_top(elig, count)
        total += (pts[rows] * sel).sum(axis=0)
        used[rows] |= sel
    rows = np.where(np.isin(pos, FLEX_P))[0]
    if len(rows):
        elig = playing[rows] & ~used[rows]
        if best_ball:
            masked = np.where(elig, pts[rows], -np.inf)
            rank = np.argsort(np.argsort(-masked, axis=0, kind="stable"),
                              axis=0, kind="stable")
            sel = elig & (rank < FLEX_SLOTS)
        else:
            sel = _take_top(elig, FLEX_SLOTS)
        total += (pts[rows] * sel).sum(axis=0)
    total[0] = 0.0
    return total


@dataclass
class DraftResult:
    user_slot: int
    points_A: float
    points_B: float
    made_playoffs: bool
    won_title: bool
    seed: int
    wins: int
    rb_taken_round: int
    first_rb_round: int


def evaluate(rosters: Sequence[Sequence[int]], board: Board, user_slot: int) -> DraftResult:
    weekly_A = np.array([_lineup_weekly(np.array(r), board, True) for r in rosters])
    weekly_B = np.array([_lineup_weekly(np.array(r), board, False) for r in rosters])

    wins = np.zeros(N_TEAMS)
    reg_pts = weekly_B[:, 1:min(REGULAR_WEEKS, board.n_weeks) + 1].sum(axis=1)
    for wk, pairs in enumerate(SCHEDULE, start=1):
        if wk > board.n_weeks:
            break
        for a, b in pairs:
            if weekly_B[a, wk] > weekly_B[b, wk]:
                wins[a] += 1
            elif weekly_B[b, wk] > weekly_B[a, wk]:
                wins[b] += 1
            else:
                wins[a] += 0.5
                wins[b] += 0.5
    seeding = sorted(range(N_TEAMS), key=lambda t: (-wins[t], -reg_pts[t]))
    seed_of = {t: i + 1 for i, t in enumerate(seeding)}

    champion = None
    if board.n_weeks >= PLAYOFF_WEEKS[1]:
        s1, s2, s3, s4 = seeding[:4]
        w16 = PLAYOFF_WEEKS[0]
        a = s1 if weekly_B[s1, w16] >= weekly_B[s4, w16] else s4
        b = s2 if weekly_B[s2, w16] >= weekly_B[s3, w16] else s3
        w17 = PLAYOFF_WEEKS[1]
        champion = a if weekly_B[a, w17] >= weekly_B[b, w17] else b

    ur = list(rosters[user_slot])
    rb_rounds = [i for i, p in enumerate(ur) if POSITIONS[board.pos_idx[p]] == "RB"]
    first_rb = (rb_rounds[0] + 1) if rb_rounds else 99
    # The fantasy season ends at week 17. Week 18 exists in the data from 2021 and
    # is not part of it; including it would silently add a week of points to the
    # post-expansion seasons only.
    last = min(PLAYOFF_WEEKS[1], board.n_weeks)
    return DraftResult(
        user_slot=user_slot,
        points_A=float(weekly_A[user_slot, 1:last + 1].sum()),
        points_B=float(weekly_B[user_slot, 1:last + 1].sum()),
        made_playoffs=seed_of[user_slot] <= 4,
        won_title=(champion == user_slot),
        seed=seed_of[user_slot],
        wins=float(wins[user_slot]),
        rb_taken_round=len(rb_rounds),
        first_rb_round=first_rb,
    )
