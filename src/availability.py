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

ADR-034 -- THREE INPUTS, NONE OF THEM PRIOR-YEAR MANAGER BEHAVIOUR. This module
previously (pre-2026-07-25) let a caller force NAMED teams to draft a position
with a hand-set probability, used to model "two managers who took a TE in round 3
of 2025 might do it again". ADR-033 found that circular: the entire spread of the
old TE-scenario table (0.60 at 0% repeat, 0.13 at 100% repeat) came from an
assumption about two specific people, not a measurement. That mechanism
(`ScenarioPick`) is gone. The three inputs now are:

  (a) A ranking MIXTURE per manager (`RankingSource` + `source_weights`). Each
      simulated draft samples, per opponent team, which ranking source drives
      their board -- never hard-assigned to a team, never collapsed to argmax.
      With a single source (today: FantasyPros ECR only) this is a no-op, but
      the sampling path is real so a second source (MFL ADP, ADR-035) plugs in
      without a rewrite.
  (b) Positional NEED, mechanical: `ds.MECHANICAL_NEED_TARGETS`, derived from
      STARTERS + FLEX_SLOTS, not a hand-tuned constant (contrast
      `ds.NEED_TARGETS`, which stays a judgement call for the PR-003 strategy
      simulator so those already-verified numbers do not move).
  (c) Rank NOISE (sigma), unchanged, drawn once per simulated draft.
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
class RankingSource:
    """One board an opponent might be drafting from.

    `rank` must be aligned to the SAME player order as the SeasonData it will be
    used with (positional index i means the same player in both arrays).
    """

    name: str
    rank: np.ndarray


def default_ranking_sources(data: ds.SeasonData) -> List[RankingSource]:
    """The only source SHIPPED by default. A second entry (MFL ADP, ADR-035,
    `load_mfl_adp_source`) is available and tested but deliberately NOT wired
    in here -- see that function's docstring for why."""
    return [RankingSource("fantasypros_ecr", data.consensus_rank)]


def load_mfl_adp_source(
    conn: sqlite3.Connection, data: ds.SeasonData, adp_source: str = "mfl_proxy"
) -> Optional[RankingSource]:
    """A second RankingSource built from ingested MFL ADP (ADR-035),
    mfl_id-joined via the ADR-036 identity hub. Real, tested, and NOT the
    default -- three reasons, stated so a future session does not "fix" this
    into the default without addressing them:

    1. MFL's own sample behind the snapshot ingested this session was
       `totalDrafts=50` -- thin enough that treating it as an equal-weight
       peer to FantasyPros ECR (built from far more analyst input) would be an
       assumption, not a measurement, in exactly the sense CLAUDE.md SS6.3 warns
       against ("every added parameter must earn its place against a
       holdout"). No holdout comparison has been run.
    2. MFL only covers the top ~230 players in a 10-team snapshot; the rest of
       the ~600+ player universe has no MFL opinion at all. Unresolved players
       fall back to their FantasyPros ECR rank (see below) so the array stays
       usable, but that means "the MFL source" is actually a blend of real
       MFL data at the top and a copy of the other source beneath it -- worth
       knowing before trusting a mixture weight against it.
    3. Wiring a second source into the SHIPPED availability.json changes its
       output as a side effect of an ingestion task, which was not asked for
       and was not the kind of change this session's other numeric moves
       (ADR-034's TE T1@23) were bounds-checked for.

    Returns None if no adp_snapshots rows exist for `adp_source` (never raises
    -- an ingestion that has not run yet is a normal state, not an error).
    """
    row = conn.execute(
        "SELECT MAX(retrieved_at) FROM adp_snapshots WHERE adp_source=?", (adp_source,)
    ).fetchone()
    if row is None or row[0] is None:
        return None
    latest = row[0]

    mfl_to_pick: Dict[str, float] = {
        r[0]: r[1] for r in conn.execute(
            "SELECT mfl_id, average_pick FROM adp_snapshots "
            "WHERE adp_source=? AND retrieved_at=?", (adp_source, latest),
        ).fetchall()
    }
    gsis_to_mfl: Dict[str, str] = {
        r[0]: r[1] for r in conn.execute(
            "SELECT source_id, mfl_id FROM player_ids WHERE source='gsis'"
        ).fetchall()
    }

    rank = data.consensus_rank.copy()  # fallback: FP-ECR rank for MFL-uncovered players
    n_resolved = 0
    for i, pid in enumerate(data.player_ids):
        mfl_id = gsis_to_mfl.get(pid)
        if mfl_id is not None and mfl_id in mfl_to_pick:
            rank[i] = mfl_to_pick[mfl_id]
            n_resolved += 1

    return RankingSource(f"{adp_source}_{n_resolved}_of_{len(rank)}_resolved", rank)


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
    track_top_n: int = 80,
    sources: Optional[Sequence[RankingSource]] = None,
    source_weights: Optional[Sequence[float]] = None,
) -> AvailabilityResult:
    """Record who is on the board at each user pick, across many drafts.

    The user drafts BPA here. Their own picks remove players from the board, but
    the user knows their own roster at draft time, so what matters for planning
    is what the other nine teams take -- which BPA reproduces neutrally.

    ADR-034's three inputs, applied per simulated draft:
      (a) each of the 9 opponent teams is assigned a ranking source by sampling
          from `sources`/`source_weights` -- a fresh draw every draft, never a
          fixed per-team identity, which is what "marginalised over, never
          hard-assigned" means in practice;
      (b) `ds.MECHANICAL_NEED_TARGETS` drives the positional-need penalty inside
          `ds.opponent_pick`, derived from roster rules rather than assumed;
      (c) one shared Gaussian noise draw per draft (unchanged from before).
    """
    rng = np.random.default_rng(seed)
    order = ds.pick_order()
    me = ds.USER_SLOT - 1
    user_picks = ds.user_pick_numbers()
    pos_rank = positional_ranks(data)
    n = len(data.player_ids)
    top_ids = list(np.argsort(data.consensus_rank)[:track_top_n])

    sources = list(sources) if sources else default_ranking_sources(data)
    weights = np.array(source_weights if source_weights else [1.0] * len(sources), dtype=float)
    weights = weights / weights.sum()
    source_ranks = np.stack([s.rank for s in sources])  # (n_sources, n_players)

    avail_counts = {i: {p: 0 for p in user_picks} for i in top_ids}
    tier_counts = {
        pos: {t: {p: 0 for p in user_picks} for t in TIERS[pos]} for pos in TIERS
    }
    best_dist: Dict[str, Dict[int, List[int]]] = {
        pos: {p: [] for p in user_picks} for pos in ds.POSITIONS
    }

    for _ in range(n_sims):
        # (a) per-team ranking-source assignment, freshly sampled this draft --
        # never fixed to a team across sims, i.e. marginalised, not hard-assigned.
        team_source_idx = rng.choice(len(sources), size=ds.N_TEAMS, p=weights)
        team_base_rank = source_ranks[team_source_idx]  # (N_TEAMS, n)
        # (c) one shared noise draw for the room this draft.
        room_noise = rng.normal(0.0, sigma, size=n)
        effective_by_team = team_base_rank + room_noise[None, :]
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
                # (b) mechanical need, not the judgement-call NEED_TARGETS.
                choice = ds.opponent_pick(
                    effective_by_team[team], available, counts[team], data,
                    targets=ds.MECHANICAL_NEED_TARGETS,
                )

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
