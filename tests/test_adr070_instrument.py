"""Unit tests for the ADR-070 decision instrument (pure machinery, no DB).

Every numeric expectation below is derived by hand from the ADR's own formulas,
so a regression here is a rule change, not a flake.
"""

import numpy as np
import pytest

from experiments.bottomup.v2.adr070 import (
    Consistency, KeyMismatchError, ProvKey, SeqResult, assert_joinable,
    bc_sequential_p, bh_reject, carried_by_one_or_two, consistency,
    draws_needed, ensemble_stats, snap_deltas, snap_tolerance, tolerances,
    verdict,
)


# ------------------------------------------------------------------- §4.8 key
def test_key_mismatch_raises_on_universe():
    a = ProvKey("m_panel_ppr12", "2013-2024", 12, 2002)
    b = ProvKey("full_veteran_roster", "2013-2024", 12, 2002)
    with pytest.raises(KeyMismatchError):
        assert_joinable(a, b)


def test_key_mismatch_raises_on_span():
    a = ProvKey("m_panel_ppr12", "2013-2024", 12, 2002)
    b = ProvKey("m_panel_ppr12", "2018-2024", 7, 2002)
    with pytest.raises(KeyMismatchError):
        assert_joinable(a, b)


def test_key_mismatch_raises_on_ff():
    a = ProvKey("m_panel_ppr12", "2013-2024", 12, 2002)
    b = ProvKey("m_panel_ppr12", "2013-2024", 12, 2012)
    with pytest.raises(KeyMismatchError):
        assert_joinable(a, b)


def test_identical_keys_join():
    a = ProvKey("m_panel_ppr12", "2013-2024", 12, 2002)
    assert_joinable(a, ProvKey("m_panel_ppr12", "2013-2024", 12, 2002))


def test_unknown_universe_rejected():
    with pytest.raises(KeyMismatchError):
        ProvKey("consensus_board", "2013-2024", 12, 2002)


# ------------------------------------------------------------- §4.7 tolerance
def test_snap_tolerance_is_half_quantum():
    # Spearman quantum on n=14 is 12/(n^3-n) = 12/2730; tol is half that
    assert snap_tolerance(14) == pytest.approx(6.0 / 2730.0)
    # n=50: 4.8e-5 per the ADR's own arithmetic
    assert snap_tolerance(50) == pytest.approx(6.0 / (50 ** 3 - 50))
    assert snap_tolerance(50) == pytest.approx(4.8e-5, rel=1e-3)


def test_snap_zeroes_subquantum_only():
    d = snap_deltas(np.array([1e-17, 0.01, -1e-5]), [14, 14, 14])
    assert d[0] == 0.0 and d[1] == 0.01 and d[2] == 0.0  # 1e-5 < 6/2730
    # continuous endpoints snap float noise only
    d2 = snap_deltas(np.array([1e-17, 1e-5]), [14, 14], continuous=True)
    assert d2[0] == 0.0 and d2[1] == 1e-5


# --------------------------------------------------------------- §4.3 Besag–C
def test_draws_needed_matches_adr_arithmetic():
    assert draws_needed(130) == 2599
    assert draws_needed(230) == 4599


def test_bc_p_h_reached():
    # observation +0.01; draws where 20th exceedance lands at draw 40 -> p1=0.5
    draws = [0.02 if k % 2 == 0 else -0.02 for k in range(1, 201)]
    r = bc_sequential_p(0.01, draws, h=20, L=4599)
    assert r.stop_reason == "h_reached"
    assert r.n_exceed == 20
    assert r.p_one == pytest.approx(20 / r.n_draws_used)
    assert r.p_two == pytest.approx(min(1.0, 2 * r.p_one))


def test_bc_p_L_exhausted_floor():
    # no draw ever exceeds: p_one = 1/(L+1), p_two = 2/(L+1) = the hard floor
    L = 99
    r = bc_sequential_p(0.5, [0.0] * L, h=20, L=L)
    assert r.stop_reason == "L_exhausted"
    assert r.p_one == pytest.approx(1 / (L + 1))
    assert r.p_two == pytest.approx(2 / (L + 1))
    assert r.p_two == pytest.approx(r.p_floor)


def test_bc_p_two_sided_direction_harm():
    draws = [-0.02] * 30 + [0.0] * 70
    r = bc_sequential_p(-0.01, draws, h=20, L=4599)
    assert r.direction == "HARM"
    assert r.stop_reason == "h_reached"


def test_bc_p_insufficient_never_authorises():
    # 100 draws, 0 exceedances: p_two = 2/101 <= 0.05, but the ensemble is
    # incomplete -> HYPOTHESIS at best, even if BH would have rejected (§5:
    # no reduced-L inclusion)
    r = bc_sequential_p(0.5, [0.0] * 100, h=20, L=4599)
    assert r.stop_reason == "insufficient"
    v = verdict(r.p_two, bh_robust=True, direction="WIN", consistent=True,
                voided=False, coverage=1.0, stop_reason=r.stop_reason)
    assert v == "HYPOTHESIS"
    # and an incomplete ensemble with p > 0.05 cannot claim a CALIBRATED null
    r2 = bc_sequential_p(0.5, [0.0] * 10, h=20, L=4599)
    v2 = verdict(r2.p_two, bh_robust=False, direction="WIN", consistent=True,
                 voided=False, coverage=1.0, stop_reason=r2.stop_reason)
    assert v2 == "NO DATA"


def test_bc_ties_count_as_exceedances():
    r = bc_sequential_p(0.01, [0.01] * 40, h=20, L=4599)
    assert r.n_exceed == 20 and r.n_draws_used == 20


def test_bc_zero_observation():
    r = bc_sequential_p(0.0, [0.1] * 10, h=20, L=4599)
    assert r.direction == "ZERO" and r.p_two == 1.0


# ------------------------------------------------------------ §4.4a consistency
def test_consistency_calibrated_against_ensemble_not_binomial():
    tols = tolerances([50] * 7)
    obs = np.array([0.02, 0.03, 0.01, 0.02, 0.04, 0.01, 0.02])   # C = 7
    rng = np.random.default_rng(0)
    draws = rng.normal(0.0, 0.02, size=(300, 7))                  # null C ~ 0
    c = consistency(obs, draws, tols, "WIN")
    assert c.w_plus == 7 and c.w_minus == 0 and c.c == 7
    assert c.consistent          # 7 > any plausible null q95
    assert 0.2 < c.pi0_hat < 0.8


def test_consistency_respects_biased_null():
    """A null that itself wins 90% of seasons must NOT let a 6-of-7 cell pass:
    the ensemble's own C distribution embeds the bias (the §1.2 fix)."""
    tols = tolerances([50] * 7)
    obs = np.array([0.02, 0.03, 0.01, 0.02, 0.04, -0.02, 0.02])   # C = 5
    rng = np.random.default_rng(1)
    draws = rng.normal(0.03, 0.01, size=(300, 7))   # biased null: most C = 7
    c = consistency(obs, draws, tols, "WIN")
    assert not c.consistent


def test_consistency_orientation_for_harm():
    tols = tolerances([50] * 7)
    obs = np.array([-0.02, -0.03, -0.01, -0.02, -0.04, -0.01, -0.02])
    rng = np.random.default_rng(2)
    draws = rng.normal(0.0, 0.02, size=(300, 7))
    c = consistency(obs, draws, tols, "HARM")
    assert c.c == 7 and c.consistent


# -------------------------------------------------------------------- §4.5 BH
def test_bh_at_campaign_denominator():
    # rank-1 threshold at M=230 q=0.10 is 4.35e-4
    ps = [4e-4, 0.03, 0.5, np.nan]
    keep = bh_reject(ps, m_campaign=230)
    assert keep.tolist() == [True, False, False, False]


def test_bh_all_null():
    assert not bh_reject([0.5, 0.9, np.nan], 230).any()


# --------------------------------------------------------------- §4.4 verdicts
def _seqok(p):
    return dict(p_two=p, stop_reason="h_reached")


def test_verdict_include_requires_consistency():
    assert verdict(4e-4, True, "WIN", True, False, 1.0, "L_exhausted") == "INCLUDE"
    assert verdict(4e-4, True, "WIN", False, False, 1.0, "L_exhausted",
                   np.array([0.2, -0.01, -0.01, -0.01])) == "FRAGILE"


def test_verdict_harm_split():
    consistent_harm = verdict(4e-4, True, "HARM", True, False, 1.0, "L_exhausted")
    assert consistent_harm == "RE-SPECIFY"
    spread_harm = verdict(4e-4, True, "HARM", False, False, 1.0, "L_exhausted",
                          np.array([-0.02, -0.02, -0.02, -0.02, -0.02, -0.019,
                                    -0.021]))
    assert spread_harm == "EXCLUDE (variance)"
    oneseason_harm = verdict(4e-4, True, "HARM", False, False, 1.0, "L_exhausted",
                             np.array([-0.2, 0.01, 0.01, 0.01, 0.005, 0.002,
                                       0.001]))
    assert oneseason_harm == "FRAGILE"


def test_verdict_void_blocks_include():
    assert verdict(4e-4, True, "WIN", True, True, 1.0,
                   "L_exhausted") == "WIN (VOID: control wins)"


def test_verdict_hypothesis_and_null():
    assert verdict(0.03, False, "WIN", True, False, 1.0, "h_reached") == "HYPOTHESIS"
    assert verdict(0.4, False, "WIN", True, False, 1.0,
                   "h_reached") == "NULL (calibrated)"


def test_verdict_coverage_floor():
    assert verdict(4e-4, True, "WIN", True, False, 0.5, "L_exhausted") == "NO DATA"


def test_carried_by_one_or_two():
    assert carried_by_one_or_two(np.array([0.3, 0.01, -0.02, -0.01, 0.0]), "WIN")
    assert not carried_by_one_or_two(
        np.array([0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]), "WIN")


# ----------------------------------------------------------------- both tails
def test_ensemble_stats_has_both_tails():
    s = ensemble_stats(np.linspace(-0.1, 0.1, 201))
    assert s["min"] < 0 < s["max"]
    for k in ("q025", "q05", "q25", "median", "q75", "q95", "q975"):
        assert np.isfinite(s[k])
    assert s["n_draws"] == 201


def test_loo_calibration_exact_uniform():
    """The §6.2(a) geometry on synthetic data: LOO p over exchangeable draws is
    uniform; p<=0.05 rate must sit near nominal. This is the same computation
    the real check runs, on a null where the answer is known."""
    rng = np.random.default_rng(7)
    draws = rng.normal(0, 1, size=400)
    hits = 0
    for i in range(len(draws)):
        rest = np.delete(draws, i)
        d = draws[i]
        if d == 0:
            continue
        exc = int(np.sum(rest >= d)) if d > 0 else int(np.sum(rest <= d))
        p = min(1.0, 2.0 * (exc + 1) / (len(rest) + 1))
        hits += p <= 0.05
    assert hits / len(draws) <= 0.095   # the ADR's own per-position bound
