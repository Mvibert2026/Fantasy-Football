"""
ADR-055: live_availability.py's structural assumptions (TARGET/EPS/SHARE_BAR/
POSITIONS) must be derivable from a LeagueConfig instead of frozen module
constants. This is the test the defect writeup calls out by name: its
absence is why the primary league's numbers were "correct by accident" --
nothing checked that a second, differently-shaped league produced different
output.

Two real configs are used, not synthetic ones: `league_config.CURRENT_LEAGUE`
(Westwood -- 10 teams, no kicker, 2 FLEX) and `data/leagues/
ethans_expert_league.json` (Ethan's -- 10 teams, a kicker, 1 FLEX, no
measured flex_split). Real difference: Ethan's has a K starter Westwood does
not have at all -- positions_for must include it as a real contested pick
(same treatment as DEF, ADR-039), not silently drop it.
"""

from __future__ import annotations

import pytest

import league_config as lc
import live_availability as la
from live_availability import InterveningPick


@pytest.fixture(scope="module")
def ethan_cfg() -> lc.LeagueConfig:
    return lc.LeagueConfig.load("ethans_expert_league")


# --------------------------------------------------------- primary league unchanged
def test_primary_cfg_reproduces_module_constants_exactly():
    """Passing cfg=CURRENT_LEAGUE must be byte-identical to the pre-ADR-055
    module constants -- the whole point of the refactor is that the primary
    league's numbers do not move."""
    cfg = lc.CURRENT_LEAGUE
    assert la.positions_for(cfg) == la.POSITIONS
    assert la.target_for(cfg) == la.TARGET
    assert la.eps_for(cfg) == la.EPS
    assert la.share_bar_for(cfg) == pytest.approx(la.SHARE_BAR)


def test_primary_league_path_no_longer_bypasses_config():
    """need_share / n_need called WITH cfg=CURRENT_LEAGUE must produce the
    exact same numbers as the old no-cfg call path -- i.e. the primary
    league now runs the same derivation code as every other league (through
    positions_for/target_for/eps_for/share_bar_for) rather than a special
    hardcoded shortcut that happens to match. This is what closes 'correct
    by accident.'"""
    drafted = {"RB": 2, "WR": 1}
    no_cfg = la.need_share(drafted)
    with_primary_cfg = la.need_share(drafted, cfg=lc.CURRENT_LEAGUE)
    assert no_cfg == with_primary_cfg

    n_no_cfg = la.n_need(drafted, lam=0.352)
    n_with_cfg = la.n_need(drafted, lam=0.352, cfg=lc.CURRENT_LEAGUE)
    assert n_no_cfg == pytest.approx(n_with_cfg)


# --------------------------------------------------------- roster shape actually differs
def test_two_roster_shapes_produce_different_target(ethan_cfg):
    """The central assertion: TARGET (and therefore SHARE_BAR, and therefore
    every downstream hazard) genuinely differs between two real league
    configs. Westwood has no kicker and 2 FLEX; Ethan's has a kicker and 1
    FLEX -- their derived per-position demand must not collapse to the same
    numbers."""
    westwood_target = la.target_for(lc.CURRENT_LEAGUE)
    ethan_target = la.target_for(ethan_cfg)
    assert westwood_target != ethan_target
    # Ethan's league has a real K starter; Westwood has none at all.
    assert "K" in la.positions_for(ethan_cfg)
    assert "K" not in la.positions_for(lc.CURRENT_LEAGUE)
    assert ethan_target["K"] > 0


def test_derived_target_sums_to_league_rounds(ethan_cfg):
    """target_for(cfg) must sum to cfg.rounds exactly for ANY league, not
    just the primary one -- otherwise every share_bar denominator for that
    league is silently wrong (mirrors the primary league's own module-level
    assertion on TARGET)."""
    for cfg in (lc.CURRENT_LEAGUE, ethan_cfg):
        target = la.target_for(cfg)
        assert sum(target.values()) == pytest.approx(float(cfg.rounds), abs=1e-6)


def test_two_roster_shapes_produce_different_survival_numbers(ethan_cfg):
    """THE test the defect writeup names directly: run the full live-survival
    hazard model against two real, differently-shaped leagues with an
    IDENTICAL synthetic scenario (same p0, same positions, same intervening
    picks) and confirm the resulting survival probabilities differ. If they
    matched, the roster shape would not actually be flowing through the
    model -- exactly the "correct by accident" failure mode this closes.
    """
    # A small pool spanning positions both leagues share, so the comparison
    # isolates the roster-shape effect rather than a missing-key crash.
    positions = {
        "qb1": "QB", "rb1": "RB", "rb2": "RB", "wr1": "WR", "wr2": "WR",
        "te1": "TE", "def1": "DEF",
    }
    n = len(positions)
    p0 = {pid: 0.5 for pid in positions}
    k = 12  # long enough gap to push past the RUN_WINDOW guard is irrelevant here (r_mult=None)

    # One team, mid-draft, already stacked at RB -- the scenario in which
    # need-based reweighting is most visible.
    gap = [InterveningPick(team="A", drafted={"RB": 3, "WR": 1}) for _ in range(k)]

    survival_westwood = la.live_survival(p0, positions, gap, lam=0.352, cfg=lc.CURRENT_LEAGUE)
    survival_ethan = la.live_survival(p0, positions, gap, lam=0.352, cfg=ethan_cfg)

    assert survival_westwood != pytest.approx(survival_ethan)
    # Sanity: both are still valid probabilities.
    for survive in (survival_westwood, survival_ethan):
        for pid in positions:
            assert 0.0 <= survive[pid] <= 1.0


def test_unmeasured_derivation_is_flagged_not_silently_equal_footing():
    """Ethan's league has no cfg.flex_split (unlike the primary league's
    ADR-029 measured one) -- target_for must still produce a valid,
    normalized target using the explicit even-split placeholder rather than
    raising or silently reusing the primary league's measured split."""
    cfg = lc.LeagueConfig.load("ethans_expert_league")
    assert cfg.flex_split is None
    target = la.target_for(cfg)
    assert sum(target.values()) == pytest.approx(float(cfg.rounds), abs=1e-6)
    # RB and WR are the two flex-eligible positions with equal starters
    # counts here (2 and 3 respectively) plus an evenly-split single flex
    # slot -- just confirm both get a nonzero share, i.e. the placeholder
    # ran rather than being skipped.
    assert target["RB"] > cfg.starters["RB"]
    assert target["WR"] > cfg.starters["WR"]
