"""
Board-state / availability distributions at each of the user's picks.

WHY THIS IS THE MOST RELIABLE OUTPUT IN THE PROJECT. Every roster-value number
produced so far passes through the ADR-016 rank->points curve, whose R-squared is
0.158-0.266 -- consensus rank explains under a third of the variance in what a
player actually scores. Availability does NOT use that curve at all. It asks only
"given how the room drafts, who is still on the board at pick N", which depends
on the consensus ordering and the opponent model, not on any projection of
outcomes. The uncertainty here is about draft behaviour, not about football.

That makes it materially more trustworthy than any strategy comparison, and it is
the artifact most directly usable under a draft clock.

WHAT IT STILL DEPENDS ON. The opponent-noise parameter sigma is uncalibrated
(ADR-018: no ADP source exists to fit it against). Every number is therefore
reported across the sigma sweep, and any statement that holds at only one sigma
is an artifact of the assumption rather than a fact about the draft.

Sigma in intuitive terms:
  sigma=5   a disciplined room; players go within about half a round of consensus
  sigma=10  default; roughly one round of slippage either way
  sigma=20  a chaotic room; two rounds of slippage, reaches and slides common
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import draft_sim as ds

# Tier definitions by positional consensus rank. Fixed bands rather than
# data-derived clusters: with one board and no outcome data involved, a
# transparent rule the user can sanity-check beats a fitted one they cannot.
TIERS: Dict[str, Dict[str, Tuple[int, int]]] = {
    "QB": {"T1": (1, 2), "T2": (3, 6), "T3": (7, 12), "T4": (13, 20)},
    "RB": {"T1": (1, 4), "T2": (5, 10), "T3": (11, 20), "T4": (21, 36)},
    "WR": {"T1": (1, 5), "T2": (6, 12), "T3": (13, 24), "T4": (25, 45)},
    "TE": {"T1": (1, 2), "T2": (3, 5), "T3": (6, 10), "T4": (11, 18)},
}


@dataclass
class ScenarioPick:
    """Force the team owning `pick_number` to take `position` with probability p."""

    pick_number: int
    position: str
    probability: float


@dataclass
class AvailabilityResult:
    sigma: float
    n_sims: int
    user_picks: List[int]
    # player index -> {pick_number: probability available}
    player_avail: Dict[int, Dict[int, float]] = field(default_factory=dict)
    # position -> tier -> {pick: P(at least one available)}
    tier_avail: Dict[str, Dict[str, Dict[int, float]]] = field(default_factory=dict)
    # position -> pick -> list of best-available positional ranks (full distribution)
    best_avail_dist: Dict[str, Dict[int, List[int]]] = field(default_factory=dict)


def positional_ranks(data: ds.SeasonData) -> np.ndarray:
    """1-indexed rank within position, by consensus order."""
    out = np.zeros(len(data.player_ids), dtype=int)
    for p, _name in enumerate(ds.POSITIONS):
        idx = np.where(data.positions == p)[0]
        idx = idx[np.argsort(data.consensus_rank[idx])]
        out[idx] = np.arange(1, len(idx) + 1)
    return out


def simulate_availability(
    data: ds.SeasonData,
    sigma: float,
    n_sims: int,
    seed: int,
    scenario: Optional[Sequence[ScenarioPick]] = None,
    track_top_n: int = 80,
) -> AvailabilityResult:
    """Record who is on the board at each user pick, across many drafts.

    The user drafts BPA here. Their own picks remove players from the board, but
    the user knows their own roster at draft time, so what matters for planning
    is what the other nine teams take -- which BPA reproduces neutrally.
    """
    rng = np.random.default_rng(seed)
    order = ds.pick_order()
    me = ds.USER_SLOT - 1
    user_picks = ds.user_pick_numbers()
    pos_rank = positional_ranks(data)
    n = len(data.player_ids)
    top_ids = list(np.argsort(data.consensus_rank)[:track_top_n])

    scen_by_pick: Dict[int, ScenarioPick] = {}
    for sp in scenario or []:
        scen_by_pick[sp.pick_number] = sp

    avail_counts = {i: {p: 0 for p in user_picks} for i in top_ids}
    tier_counts = {
        pos: {t: {p: 0 for p in user_picks} for t in TIERS[pos]} for pos in TIERS
    }
    best_dist: Dict[str, Dict[int, List[int]]] = {
        pos: {p: [] for p in user_picks} for pos in ds.POSITIONS
    }

    for _ in range(n_sims):
        effective = data.consensus_rank + rng.normal(0.0, sigma, size=n)
        available = np.ones(n, dtype=bool)
        counts = [{p: 0 for p in ds.POSITIONS} for _ in range(ds.N_TEAMS)]

        for pick_i, team in enumerate(order):
            pick_no = pick_i + 1
            rnd = pick_i // ds.N_TEAMS
            if rnd == ds.N_ROUNDS - 1:
                continue

            if team == me:
                # snapshot the board BEFORE the user consumes a player
                if pick_no in avail_counts[top_ids[0]]:
                    for i in top_ids:
                        if available[i]:
                            avail_counts[i][pick_no] += 1
                    for pos, tiers in TIERS.items():
                        p = ds.POSITIONS.index(pos)
                        for tname, (lo, hi) in tiers.items():
                            m = available & (data.positions == p) & (pos_rank >= lo) & (pos_rank <= hi)
                            if m.any():
                                tier_counts[pos][tname][pick_no] += 1
                    for pos in ds.POSITIONS:
                        p = ds.POSITIONS.index(pos)
                        m = available & (data.positions == p)
                        best_dist[pos][pick_no].append(
                            int(pos_rank[m].min()) if m.any() else 999
                        )
                state = ds.DraftState(data.season, pick_no, rnd, [], counts[me], available)
                choice = ds.strategy_bpa(state, available, data, data.consensus_rank)
            else:
                sp = scen_by_pick.get(pick_no)
                choice = None
                if sp is not None and rng.random() < sp.probability:
                    p = ds.POSITIONS.index(sp.position)
                    m = available & (data.positions == p)
                    if m.any():
                        cand = np.where(m)[0]
                        choice = int(cand[np.argmin(effective[cand])])
                if choice is None:
                    choice = ds.opponent_pick(effective, available, counts[team], data)

            if choice is None or not available[choice]:
                continue
            available[choice] = False
            counts[team][ds.POSITIONS[data.positions[choice]]] += 1

    res = AvailabilityResult(sigma, n_sims, user_picks)
    res.player_avail = {
        i: {p: c / n_sims for p, c in picks.items()} for i, picks in avail_counts.items()
    }
    res.tier_avail = {
        pos: {t: {p: c / n_sims for p, c in picks.items()} for t, picks in tiers.items()}
        for pos, tiers in tier_counts.items()
    }
    res.best_avail_dist = best_dist
    return res


def distribution_summary(vals: Sequence[int]) -> Dict[str, float]:
    if not vals:
        return {}
    a = np.array([v for v in vals if v < 999])
    if a.size == 0:
        return {}
    return {
        "p10": float(np.percentile(a, 10)),
        "p25": float(np.percentile(a, 25)),
        "median": float(np.percentile(a, 50)),
        "p75": float(np.percentile(a, 75)),
        "p90": float(np.percentile(a, 90)),
        "mean": float(a.mean()),
    }
