"""
Live-draft availability adjustment (ADR-045), per the Strategist's
live_availability_adjustment.md.

WHAT THIS ADDS ON TOP OF THE PREP-MODE MARGINAL (availability.py). Prep-mode
answers "across every possible draft, how often does X survive to pick M" --
unconditional, averaged over all opponent behaviour. This module answers the
LIVE question: given the ACTUAL picks made so far in a real draft (who is
gone, what each team's roster looks like right now), re-weight that marginal
using the two mechanisms that survived red-team review -- roster-need
arithmetic (`N_t(p)`) and positional-run detection (`R(p)`). No latent
per-manager strategy variable, no per-manager parameters: n=1 (this league)
cannot support them.

STRUCTURE: multiplicative on PER-PICK HAZARD, then renormalised across the
undrafted pool at every intervening pick -- never a multiplicative adjustment
to survival probability directly, which would break "exactly one player is
taken per pick" (boost WR survival without touching anything else and the
model implicitly drafts 1.3 players at that pick). See the spec's SS1 for the
full argument. The renormalisation in `_hazards_at_pick` is the step that
makes boosting one position's hazard REDISTRIBUTE probability away from
others rather than manufacture it -- do not skip it.

lambda (roster-need exponent) and delta (run-detection magnitude) are BOTH
UNVALIDATED PRIORS shipped this session, not measurements:
  - lambda: the spec's SS5(a) test (`lambda_estimation.py`, run against the
    one real 2025 league draft this project has) either confirms 0.5 or
    supplies a measured replacement -- see that module and ADR-045 for which
    happened.
  - delta=0.10: SS5(b) needs mock drafts with PER-PICK draft state logged,
    which does not exist (out of scope this session, per instruction). Ships
    flagged, with the spec's own decision rule stated in ADR-045: if a future
    session accumulates >=30 conforming mocks with per-pick state and Arm 2
    (need+runs) does not beat Arm 0 (the marginal) on Brier score, set
    lambda = delta = 0 and ship the marginal alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

# DEF is included here even though draft_sim.POSITIONS excludes it (DEF has no
# scoring engine, so the draft simulator auto-fills it via reserved rounds).
# For THIS module, DEF is a real, contested pick that competes with other
# positions for opponents' attention -- excluding it would misrepresent every
# other position's share in exactly the rounds DEF gets taken.
POSITIONS: tuple = ("QB", "RB", "WR", "TE", "DEF")

# SS2: 2025 observed final-roster means, 10-team primary league. MUST sum to
# 16 (= N_ROUNDS, the league's drafted-round count) -- checked below, not
# assumed, because every share_bar denominator is wrong if it doesn't.
TARGET: Dict[str, float] = {"QB": 1.0, "RB": 5.5, "WR": 7.0, "TE": 1.5, "DEF": 1.0}
if abs(sum(TARGET.values()) - 16.0) > 1e-9:
    raise AssertionError(
        f"TARGET must sum to 16 (roster size); got {sum(TARGET.values())}. "
        "Every share_bar denominator downstream is wrong until this is fixed."
    )

# Empirical second-QB / zero-DEF rate (1 of 10 teams did each, 2025) -- a
# filled position never goes hard to zero.
EPS: Dict[str, float] = {"QB": 0.1, "DEF": 0.1, "RB": 0.25, "WR": 0.25, "TE": 0.25}

SHARE_BAR: Dict[str, float] = {p: TARGET[p] / sum(TARGET.values()) for p in POSITIONS}

# SS5(a) MEASURED, not the 0.5 prior: conditional-logit fit on the 2025 real
# draft (160 picks, 10 teams; see lambda_estimation.py) gave
# lambda_hat=0.352, se_clustered=0.070 (cluster-robust by team), z=5.04,
# n_obs=160, n_teams=10. Clearly nonzero and correctly signed (a saturated
# position's need share drops, suppressing further picks there) -- but per
# the spec's own limits, DO NOT over-read the precision: 10 clusters is a
# small-cluster regime where cluster-robust SEs are known to under-cover, one
# season confounds need with round, and this is a hypothesis-supporting prior
# with a wide true interval, not a validated measurement. See ADR-045.
DEFAULT_LAMBDA = 0.352
DEFAULT_DELTA = 0.10  # SS3 prior; UNVALIDATED this session, see module docstring
RUN_WINDOW = 10  # SS3 W
RUN_CLIP = 2.0  # SS3 clip, in SD


def need_share(drafted: Dict[str, int]) -> Dict[str, float]:
    """share_t(p) for one team's current drafted counts (SS2). `drafted` may
    omit positions (treated as 0) -- a fresh team has never drafted anything."""
    need = {p: max(EPS[p], TARGET[p] - drafted.get(p, 0)) for p in POSITIONS}
    total = sum(need.values())
    return {p: need[p] / total for p in POSITIONS}


def n_need(drafted: Dict[str, int], lam: float = DEFAULT_LAMBDA) -> Dict[str, float]:
    """N_t(p) = (share_t(p) / share_bar(p)) ^ lambda (SS2). lambda=0 -> all 1s
    (no-op), which is exactly what check #1 requires."""
    if lam == 0.0:
        return {p: 1.0 for p in POSITIONS}
    share = need_share(drafted)
    return {p: (share[p] / SHARE_BAR[p]) ** lam for p in POSITIONS}


# --------------------------------------------------------------- run detection (SS3)
def run_z_scores(
    recent_positions: Sequence[str],
    recent_predicted_probs: Sequence[Dict[str, float]],
) -> Dict[str, float]:
    """z(p) over the last W picks (SS3). `recent_positions[j]` is the position
    ACTUALLY taken at real pick j; `recent_predicted_probs[j]` is the model's
    own predicted {position: P(pick j takes that position)} at the time --
    i.e. exp(p) and sd(p) are built from these. Both sequences must be the
    same length (<= RUN_WINDOW; the caller is responsible for windowing).

    Returns R(p) = 1 + delta*z(p) is NOT computed here -- see `run_multiplier`,
    which applies `delta` and the early-draft guard. This function only
    produces the standardised, clipped z-scores.
    """
    if len(recent_positions) == 0:
        return {p: 0.0 for p in POSITIONS}
    obs = {p: sum(1 for x in recent_positions if x == p) for p in POSITIONS}
    exp = {p: sum(pred.get(p, 0.0) for pred in recent_predicted_probs) for p in POSITIONS}
    sd = {
        p: (sum(pred.get(p, 0.0) * (1 - pred.get(p, 0.0)) for pred in recent_predicted_probs)) ** 0.5
        for p in POSITIONS
    }
    z = {}
    for p in POSITIONS:
        denom = max(sd[p], 0.5)
        z[p] = float(np.clip((obs[p] - exp[p]) / denom, -RUN_CLIP, RUN_CLIP))
    return z


def run_multiplier(
    recent_positions: Sequence[str],
    recent_predicted_probs: Sequence[Dict[str, float]],
    delta: float = DEFAULT_DELTA,
    picks_completed_so_far: int = RUN_WINDOW,
) -> Dict[str, float]:
    """R(p) = 1 + delta*z(p) (SS3). Early-draft guard: returns all-1.0 (no-op)
    before pick 10 -- 'do not compute R before pick 10, there is no window.'
    """
    if delta == 0.0 or picks_completed_so_far < RUN_WINDOW:
        return {p: 1.0 for p in POSITIONS}
    z = run_z_scores(recent_positions, recent_predicted_probs)
    return {p: 1.0 + delta * z[p] for p in POSITIONS}


# --------------------------------------------------------------- hazard model (SS1)
@dataclass
class InterveningPick:
    """One of the k picks between the user's last pick and their next one."""
    team: str
    drafted: Dict[str, int]  # that team's counts AS OF NOW (held fixed across the gap)


def hazard_from_marginal(p0: float, k: int) -> float:
    """Step 1: h0(X) = 1 - P0(X)^(1/k). Assumes intervening picks are
    homogeneous -- steps 2-3 relax this, so it is a starting point only.
    k=0 is undefined here by construction; callers must special-case it
    (check #5: k=0 => survival=1 for everyone, no hazard needed)."""
    if k <= 0:
        raise ValueError("hazard_from_marginal requires k >= 1; caller must special-case k=0")
    p0 = min(max(p0, 0.0), 1.0)
    return 1.0 - p0 ** (1.0 / k)


def _hazards_at_pick(
    h0: Dict[str, float],
    positions: Dict[str, str],
    pick: InterveningPick,
    lam: float,
    r_mult: Dict[str, float],
) -> Dict[str, float]:
    """Steps 2-3 for ONE intervening pick: raw weight w_j(X) = h0(X) *
    N_t(pos(X)) * R(pos(X)), then renormalise across ALL undrafted players so
    hazards sum to 1 at this pick (SS1 step 3 -- 'the whole reason the
    structure is multiplicative-then-normalised'). Normalising GLOBALLY
    across the whole pool (not per position) is what makes boosting one
    position redistribute away from every other player, not just same-position
    ones -- check #6 verifies this directly.
    """
    n_by_pos = n_need(pick.drafted, lam)
    raw = {
        pid: h0[pid] * n_by_pos[positions[pid]] * r_mult[positions[pid]]
        for pid in h0
    }
    total = sum(raw.values())
    if total <= 0:
        return {pid: 0.0 for pid in raw}
    return {pid: w / total for pid, w in raw.items()}


def live_survival(
    p0: Dict[str, float],
    positions: Dict[str, str],
    gap: Sequence[InterveningPick],
    lam: float = DEFAULT_LAMBDA,
    r_mult: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Full procedure (SS1 steps 1-4): for each undrafted player X in `p0`,
    return P(X survives | live state) across the whole gap.

    `p0`: Prep-mode marginal survival probability for X over this SPECIFIC
    gap (i.e. already the ratio/segment for this stretch of the draft, not
    the raw from-pick-1 marginal -- see ADR-045 for why this is the quantity
    available without a live per-pick conditional simulator).
    `positions`: position of each player in `p0`, same keys.
    `gap`: the k intervening picks, in order, each with the drafting team's
    CURRENT roster counts (held fixed across the whole gap -- this module
    does not attempt to model a team's own counts changing mid-gap, since
    that would require predicting what they take at their OTHER picks within
    the same gap, which is the thing being modelled in the first place).
    `r_mult`: R(p) per position, computed ONCE for the whole gap (SS3: 'R is
    league-wide and constant across the gap'). None => all 1.0 (no-op),
    matching check #1's null-parameter requirement together with lam=0.
    """
    k = len(gap)
    if r_mult is None:
        r_mult = {p: 1.0 for p in POSITIONS}
    if k == 0:
        # Check #5: k=0 => survive with certainty, nothing intervenes.
        return {pid: 1.0 for pid in p0}

    h0 = {pid: hazard_from_marginal(p0[pid], k) for pid in p0}
    survive = {pid: 1.0 for pid in p0}
    for pick in gap:
        h_j = _hazards_at_pick(h0, positions, pick, lam, r_mult)
        for pid in survive:
            survive[pid] *= (1.0 - h_j[pid])
    return survive


def live_survival_excluding_drafted(
    p0_all: Dict[str, float],
    positions_all: Dict[str, str],
    drafted_player_ids: set,
    gap: Sequence[InterveningPick],
    lam: float = DEFAULT_LAMBDA,
    r_mult: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Convenience wrapper a live caller should use instead of `live_survival`
    directly -- enforces check #9. Any id in `drafted_player_ids` is EXCLUDED
    from the undrafted pool the hazard normalisation runs over (a stale P0 for
    an already-taken player must never leak into the denominator, which would
    silently understate every remaining player's hazard) and its own output
    is forced to 0.0 regardless of whatever P0 was supplied for it.
    """
    undrafted = {pid: p for pid, p in p0_all.items() if pid not in drafted_player_ids}
    positions = {pid: pos for pid, pos in positions_all.items() if pid not in drafted_player_ids}
    survive = live_survival(undrafted, positions, gap, lam=lam, r_mult=r_mult)
    for pid in drafted_player_ids:
        survive[pid] = 0.0
    return survive
