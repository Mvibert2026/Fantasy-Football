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

import league_config as lc

# DEF is included here even though draft_sim.POSITIONS excludes it (DEF has no
# scoring engine, so the draft simulator auto-fills it via reserved rounds).
# For THIS module, DEF is a real, contested pick that competes with other
# positions for opponents' attention -- excluding it would misrepresent every
# other position's share in exactly the rounds DEF gets taken.
#
# This is the PRIMARY LEAGUE'S positions tuple specifically, kept as a
# module constant so every existing caller that does not pass a `cfg`
# (draft_sim.py's `la.n_need(...)`, lambda_estimation.py, every test written
# before ADR-055) keeps behaving byte-for-byte as before. `positions_for(cfg)`
# below is the general form; it returns this exact tuple for the primary
# league.
POSITIONS: tuple = ("QB", "RB", "WR", "TE", "DEF")

# SS2: 2025 observed final-roster means, 10-team primary league. MUST sum to
# 16 (= N_ROUNDS, the league's drafted-round count) -- checked below, not
# assumed, because every share_bar denominator is wrong if it doesn't.
#
# THIS IS A MEASUREMENT, SPECIFIC TO ONE LEAGUE'S ONE OBSERVED DRAFT. It has
# no equivalent for any other league -- there is no history to measure a mean
# from. `target_for(cfg)` below returns this dict unchanged for the primary
# league and an explicitly-flagged DERIVED (not measured) placeholder for any
# other league. See ADR-055.
TARGET: Dict[str, float] = {"QB": 1.0, "RB": 5.5, "WR": 7.0, "TE": 1.5, "DEF": 1.0}
if abs(sum(TARGET.values()) - 16.0) > 1e-9:
    raise AssertionError(
        f"TARGET must sum to 16 (roster size); got {sum(TARGET.values())}. "
        "Every share_bar denominator downstream is wrong until this is fixed."
    )

# Empirical second-QB / zero-DEF rate (1 of 10 teams did each, 2025) -- a
# filled position never goes hard to zero. Primary-league measurement, same
# caveat as TARGET above; see `eps_for(cfg)`.
EPS: Dict[str, float] = {"QB": 0.1, "DEF": 0.1, "RB": 0.25, "WR": 0.25, "TE": 0.25}

SHARE_BAR: Dict[str, float] = {p: TARGET[p] / sum(TARGET.values()) for p in POSITIONS}


# ============================================================= config-derived (ADR-055)
#
# WHY THIS BLOCK EXISTS. TARGET/EPS/SHARE_BAR/POSITIONS above are correct for
# the primary league (Westwood) and were, until ADR-055, the ONLY numbers
# this module could produce -- every consumer got Westwood's roster shape and
# positional demand regardless of which league it was actually asked about.
# Correct today by accident: nothing enforced that a second, differently-
# shaped league (e.g. data/leagues/ethans_expert_league.json -- 10 teams, no
# yardage bonuses, INT -1, a kicker slot, 1 FLEX where Westwood has 2, no
# DEF... no wait, Ethan's DOES have DEF, but Westwood has NO kicker) would
# get different numbers out of this module.
#
# `positions_for` / `target_for` / `eps_for` / `share_bar_for` are the
# general form. Each returns the EXACT primary-league constant above,
# unchanged, when `cfg.is_primary` -- so nothing about Westwood's output
# moves. For any other league they DERIVE a value from `cfg` instead, and
# are explicit in their docstrings about which of those derivations are
# defensible arithmetic (starters, mandatory) versus an unmeasured
# placeholder (bench allocation, flex split with no measured
# `cfg.flex_split`, EPS for a league with no draft history).
#
# `need_share` / `n_need` grow an optional `cfg` parameter that threads
# through to these. Passing no `cfg` (the default) uses the module constants
# exactly as before -- every existing call site (draft_sim.py, lambda_estimation.py,
# the pre-ADR-055 tests) is unaffected.


def positions_for(cfg: "lc.LeagueConfig") -> tuple:
    """Scoreable positions (QB/RB/WR/TE, whichever the league actually
    starts) plus any starter position with NO scoring model (DEF, K, ...) --
    generalizes the primary league's hardcoded ("QB","RB","WR","TE","DEF")
    to any roster shape. An unscored position is still a real, contested
    pick (ADR-039's point about DEF applies just as much to K) even though
    the scoring engine has no ranking for it, so it stays IN the model here
    rather than being silently dropped.

    For the primary league this returns the module POSITIONS tuple exactly
    (QB, RB, WR, TE, DEF, in that order) -- verified by
    test_league_config_availability.py.
    """
    if cfg.is_primary:
        return POSITIONS
    from scoring import ReplacementLevels

    scoreable = [p for p in ("QB", "RB", "WR", "TE") if p in cfg.starters]
    unscored = [
        p for p in cfg.starters
        if p not in ReplacementLevels.SCOREABLE_POSITIONS and cfg.starters.get(p, 0) > 0
    ]
    return tuple(scoreable + unscored)


def _flex_allocation(cfg: "lc.LeagueConfig") -> Dict[str, float]:
    """Flex slots spread across cfg.flex_eligible. Uses cfg.flex_split when
    the league has one measured (ADR-029, primary league only); otherwise
    splits flex slots evenly across flex-eligible positions -- an explicit,
    UNMEASURED placeholder, not a fitted number."""
    if cfg.flex_split:
        return {p: cfg.flex_slots * cfg.flex_split.get(p, 0.0) for p in cfg.flex_eligible}
    n = len(cfg.flex_eligible) or 1
    return {p: cfg.flex_slots / n for p in cfg.flex_eligible}


def target_for(cfg: "lc.LeagueConfig") -> Dict[str, float]:
    """Expected final-roster composition by position, keyed to
    `positions_for(cfg)`.

    PRIMARY LEAGUE: returns SS2's measured TARGET unchanged (2025 observed
    final-roster means, Westwood's actual draft) -- byte-identical to the
    module constant, so no Westwood number moves.

    ANY OTHER LEAGUE: DERIVED, not measured -- there is no draft history to
    measure a mean from for a league with no prior season. Starters are
    exact (mandatory slots, arithmetic, defensible); flex slots are
    allocated via `_flex_allocation`; bench slots are allocated
    proportionally to each position's starters+flex share (also arithmetic:
    it is the only allocation that both sums to cfg.rounds exactly and
    doesn't invent a number for any one position). This is NOT a
    measurement and is flagged as such in ADR-055 -- callers must not treat
    it as equally well-founded to the primary league's TARGET.
    """
    if cfg.is_primary:
        return dict(TARGET)
    positions = positions_for(cfg)
    flex_alloc = _flex_allocation(cfg)
    base = {p: float(cfg.starters.get(p, 0)) + flex_alloc.get(p, 0.0) for p in positions}
    base_total = sum(base.values())
    bench = float(cfg.bench)
    if base_total <= 0:
        target = dict(base)
    else:
        target = {p: base[p] + bench * (base[p] / base_total) for p in positions}
    total = sum(target.values())
    expected = float(cfg.rounds)
    if abs(total - expected) > 1e-6:
        raise AssertionError(
            f"target_for({cfg.league_id!r}) sums to {total}, expected "
            f"cfg.rounds={expected}. Every share_bar denominator downstream "
            "is wrong until this is fixed."
        )
    return target


def eps_for(cfg: "lc.LeagueConfig") -> Dict[str, float]:
    """Floor so a filled position's need share never goes hard to zero.

    PRIMARY LEAGUE: returns SS2's measured EPS unchanged (2025 observed
    second-QB / zero-DEF rate).

    ANY OTHER LEAGUE: UNMEASURED PLACEHOLDER mirroring the primary league's
    pattern (scoreable skill positions get a higher floor than positions
    with no scoring model) -- not a fitted empirical rate, because no draft
    history exists to fit one against. Flagged in ADR-055.
    """
    if cfg.is_primary:
        return dict(EPS)
    from scoring import ReplacementLevels

    return {
        p: (0.25 if p in ReplacementLevels.SCOREABLE_POSITIONS else 0.1)
        for p in positions_for(cfg)
    }


def share_bar_for(cfg: "lc.LeagueConfig") -> Dict[str, float]:
    """SHARE_BAR generalized: target_for(cfg), normalized to sum to 1. Exact
    primary-league SHARE_BAR when cfg.is_primary."""
    if cfg.is_primary:
        return dict(SHARE_BAR)
    target = target_for(cfg)
    total = sum(target.values())
    return {p: target[p] / total for p in target}

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


def need_share(
    drafted: Dict[str, int], cfg: Optional["lc.LeagueConfig"] = None
) -> Dict[str, float]:
    """share_t(p) for one team's current drafted counts (SS2). `drafted` may
    omit positions (treated as 0) -- a fresh team has never drafted anything.

    `cfg=None` (default): uses the module-level TARGET/EPS/POSITIONS exactly
    as before ADR-055 -- primary-league behaviour is unchanged byte-for-byte.
    `cfg=<LeagueConfig>`: uses that league's own target_for/eps_for/
    positions_for, which equal the module constants when cfg.is_primary and
    derive/flag placeholders otherwise (see target_for/eps_for docstrings).
    """
    positions = positions_for(cfg) if cfg is not None else POSITIONS
    eps = eps_for(cfg) if cfg is not None else EPS
    target = target_for(cfg) if cfg is not None else TARGET
    need = {p: max(eps[p], target[p] - drafted.get(p, 0)) for p in positions}
    total = sum(need.values())
    return {p: need[p] / total for p in positions}


def n_need(
    drafted: Dict[str, int],
    lam: float = DEFAULT_LAMBDA,
    cfg: Optional["lc.LeagueConfig"] = None,
) -> Dict[str, float]:
    """N_t(p) = (share_t(p) / share_bar(p)) ^ lambda (SS2). lambda=0 -> all 1s
    (no-op), which is exactly what check #1 requires. See need_share for the
    `cfg` parameter's semantics (None = primary-league module constants,
    unchanged)."""
    positions = positions_for(cfg) if cfg is not None else POSITIONS
    if lam == 0.0:
        return {p: 1.0 for p in positions}
    share_bar = share_bar_for(cfg) if cfg is not None else SHARE_BAR
    share = need_share(drafted, cfg)
    return {p: (share[p] / share_bar[p]) ** lam for p in positions}


# --------------------------------------------------------------- run detection (SS3)
def run_z_scores(
    recent_positions: Sequence[str],
    recent_predicted_probs: Sequence[Dict[str, float]],
    cfg: Optional["lc.LeagueConfig"] = None,
) -> Dict[str, float]:
    """z(p) over the last W picks (SS3). `recent_positions[j]` is the position
    ACTUALLY taken at real pick j; `recent_predicted_probs[j]` is the model's
    own predicted {position: P(pick j takes that position)} at the time --
    i.e. exp(p) and sd(p) are built from these. Both sequences must be the
    same length (<= RUN_WINDOW; the caller is responsible for windowing).

    Returns R(p) = 1 + delta*z(p) is NOT computed here -- see `run_multiplier`,
    which applies `delta` and the early-draft guard. This function only
    produces the standardised, clipped z-scores.

    `cfg=None` (default): module POSITIONS, unchanged primary-league
    behaviour. `cfg=<LeagueConfig>`: positions_for(cfg) instead.
    """
    positions = positions_for(cfg) if cfg is not None else POSITIONS
    if len(recent_positions) == 0:
        return {p: 0.0 for p in positions}
    obs = {p: sum(1 for x in recent_positions if x == p) for p in positions}
    exp = {p: sum(pred.get(p, 0.0) for pred in recent_predicted_probs) for p in positions}
    sd = {
        p: (sum(pred.get(p, 0.0) * (1 - pred.get(p, 0.0)) for pred in recent_predicted_probs)) ** 0.5
        for p in positions
    }
    z = {}
    for p in positions:
        denom = max(sd[p], 0.5)
        z[p] = float(np.clip((obs[p] - exp[p]) / denom, -RUN_CLIP, RUN_CLIP))
    return z


def run_multiplier(
    recent_positions: Sequence[str],
    recent_predicted_probs: Sequence[Dict[str, float]],
    delta: float = DEFAULT_DELTA,
    picks_completed_so_far: int = RUN_WINDOW,
    cfg: Optional["lc.LeagueConfig"] = None,
) -> Dict[str, float]:
    """R(p) = 1 + delta*z(p) (SS3). Early-draft guard: returns all-1.0 (no-op)
    before pick 10 -- 'do not compute R before pick 10, there is no window.'

    `cfg`: see run_z_scores.
    """
    positions = positions_for(cfg) if cfg is not None else POSITIONS
    if delta == 0.0 or picks_completed_so_far < RUN_WINDOW:
        return {p: 1.0 for p in positions}
    z = run_z_scores(recent_positions, recent_predicted_probs, cfg=cfg)
    return {p: 1.0 + delta * z[p] for p in positions}


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
    cfg: Optional["lc.LeagueConfig"] = None,
) -> Dict[str, float]:
    """Steps 2-3 for ONE intervening pick: raw weight w_j(X) = h0(X) *
    N_t(pos(X)) * R(pos(X)), then renormalise across ALL undrafted players so
    hazards sum to 1 at this pick (SS1 step 3 -- 'the whole reason the
    structure is multiplicative-then-normalised'). Normalising GLOBALLY
    across the whole pool (not per position) is what makes boosting one
    position redistribute away from every other player, not just same-position
    ones -- check #6 verifies this directly.

    `cfg=None` (default) reproduces the pre-ADR-055 primary-league behaviour
    exactly (n_need uses the module TARGET/EPS/SHARE_BAR). `cfg=<LeagueConfig>`
    threads that league's own target/eps/share_bar through n_need instead.
    """
    n_by_pos = n_need(pick.drafted, lam, cfg=cfg)
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
    cfg: Optional["lc.LeagueConfig"] = None,
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
    `cfg`: None (default) reproduces primary-league behaviour exactly
    (module TARGET/EPS/POSITIONS/SHARE_BAR, unchanged). Pass a LeagueConfig
    to run the whole hazard model against that league's own roster shape and
    positional demand (ADR-055) -- this is what makes two different roster
    shapes produce different survival numbers.
    """
    k = len(gap)
    if r_mult is None:
        model_positions = positions_for(cfg) if cfg is not None else POSITIONS
        r_mult = {p: 1.0 for p in model_positions}
    if k == 0:
        # Check #5: k=0 => survive with certainty, nothing intervenes.
        return {pid: 1.0 for pid in p0}

    h0 = {pid: hazard_from_marginal(p0[pid], k) for pid in p0}
    survive = {pid: 1.0 for pid in p0}
    for pick in gap:
        h_j = _hazards_at_pick(h0, positions, pick, lam, r_mult, cfg=cfg)
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
    cfg: Optional["lc.LeagueConfig"] = None,
) -> Dict[str, float]:
    """Convenience wrapper a live caller should use instead of `live_survival`
    directly -- enforces check #9. Any id in `drafted_player_ids` is EXCLUDED
    from the undrafted pool the hazard normalisation runs over (a stale P0 for
    an already-taken player must never leak into the denominator, which would
    silently understate every remaining player's hazard) and its own output
    is forced to 0.0 regardless of whatever P0 was supplied for it.

    `cfg`: see live_survival -- None (default) is the unchanged primary-league
    path, a LeagueConfig runs the hazard model against that league's roster
    shape (ADR-055).
    """
    undrafted = {pid: p for pid, p in p0_all.items() if pid not in drafted_player_ids}
    positions = {pid: pos for pid, pos in positions_all.items() if pid not in drafted_player_ids}
    survive = live_survival(undrafted, positions, gap, lam=lam, r_mult=r_mult, cfg=cfg)
    for pid in drafted_player_ids:
        survive[pid] = 0.0
    return survive
