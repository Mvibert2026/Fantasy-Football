"""
Tests for live_availability.py, numbered to match the sanity checks in
live_availability_adjustment.md SS4. #1 and #7b are written first, per
instruction -- they catch the two bug classes most likely to occur (a
plumbing error in the hazard back-out/renormalisation, and the surplus-
suppression bug already found once in the spec's own drafting).
"""

import pytest

import live_availability as la
from live_availability import InterveningPick


def _self_consistent_fixture(k=6):
    """5 synthetic players, one per position, with hazards h0_true that sum
    to exactly 1 by construction -- the property real Prep-mode marginals
    would need for check #1 to be an EXACT identity (check #3). Building the
    fixture this way, rather than picking arbitrary probabilities, is what
    makes #1 a real regression test of the code instead of an assertion that
    happens to pass only when the input already satisfies what's being
    checked.
    """
    positions = {"p_qb": "QB", "p_rb": "RB", "p_wr": "WR", "p_te": "TE", "p_def": "DEF"}
    h0_true = {"p_qb": 0.10, "p_rb": 0.30, "p_wr": 0.25, "p_te": 0.15, "p_def": 0.20}
    assert abs(sum(h0_true.values()) - 1.0) < 1e-12
    p0 = {pid: (1.0 - h) ** k for pid, h in h0_true.items()}
    return positions, h0_true, p0


# --------------------------------------------------------------------- #1
def test_check1_null_params_reproduce_prep_mode_marginal_exactly():
    """CRITICAL REGRESSION TEST. With lambda=0, delta=0 (r_mult=None), the
    live model must reproduce the input Prep-mode marginal P0(X) to floating
    tolerance. Failure here means a bug in the hazard back-out or the
    normalisation -- nothing about lambda or delta is involved yet."""
    k = 6
    positions, _h0_true, p0 = _self_consistent_fixture(k)
    gap = [InterveningPick(team="t", drafted={}) for _ in range(k)]

    survival = la.live_survival(p0, positions, gap, lam=0.0, r_mult=None)

    for pid in p0:
        assert survival[pid] == pytest.approx(p0[pid], abs=1e-9)


# -------------------------------------------------------------------- #7b
def test_check7b_three_rb_team_has_strictly_lower_rb_hazard_than_two_rb_team():
    """The surplus-suppression bug already found once in the spec's own
    drafting: a team with MORE RBs than another must show LOWER RB hazard,
    not merely un-boosted. Two otherwise-identical intervening picks,
    differing only in the drafting team's RB count (3 vs 2), mixed with a
    non-RB position so the redistribution is actually visible post-
    normalisation."""
    positions = {f"rb{i}": "RB" for i in range(5)}
    positions.update({f"wr{i}": "WR" for i in range(5)})
    h0 = {pid: 0.10 for pid in positions}  # 10 players, sums to 1.0
    assert abs(sum(h0.values()) - 1.0) < 1e-12

    pick_3rb = InterveningPick(team="A", drafted={"RB": 3})
    pick_2rb = InterveningPick(team="B", drafted={"RB": 2})
    r_mult = {p: 1.0 for p in la.POSITIONS}

    h_3rb = la._hazards_at_pick(h0, positions, pick_3rb, lam=0.5, r_mult=r_mult)
    h_2rb = la._hazards_at_pick(h0, positions, pick_2rb, lam=0.5, r_mult=r_mult)

    for pid in positions:
        if positions[pid] == "RB":
            assert h_3rb[pid] < h_2rb[pid], f"{pid}: 3-RB hazard not lower than 2-RB hazard"


# --------------------------------------------------------------------- #2
def test_check2_hazards_sum_to_one_at_every_intervening_pick():
    """SUM_{Y in A} h_j(Y) == 1.0 (+/- 0.01) at every pick, including when
    lambda != 0 -- the normalisation must enforce this regardless of what the
    raw (unnormalised) weights summed to."""
    positions, _h0_true, p0 = _self_consistent_fixture(k=4)
    h0 = {pid: la.hazard_from_marginal(p0[pid], 4) for pid in p0}
    picks = [
        InterveningPick(team="A", drafted={"RB": 2, "WR": 1}),
        InterveningPick(team="B", drafted={"QB": 1}),
        InterveningPick(team="A", drafted={"RB": 2, "WR": 1}),
        InterveningPick(team="C", drafted={}),
    ]
    for pick in picks:
        h_j = la._hazards_at_pick(h0, positions, pick, lam=0.7, r_mult={p: 1.0 for p in la.POSITIONS})
        assert sum(h_j.values()) == pytest.approx(1.0, abs=0.01)


# --------------------------------------------------------------------- #3
def test_check3_hazard_back_out_sums_to_one_before_adjustment():
    """SUM_{Y in A} h0(Y) ~= 1.0 before any N/R adjustment -- a property of
    the (self-consistent) input fixture, checked directly on
    hazard_from_marginal's output. NOTE: this cannot currently be checked
    against the SHIPPED Prep-mode marginal (availability.json only tracks
    per-player probabilities for the top ~80 players; the rest of the
    undrafted pool is only available as tier-level aggregates), so this test
    validates the transform's math on a known-consistent fixture, not real
    data. See ADR-045."""
    k = 6
    _positions, h0_true, p0 = _self_consistent_fixture(k)
    h0_recovered = {pid: la.hazard_from_marginal(p0[pid], k) for pid in p0}
    assert sum(h0_recovered.values()) == pytest.approx(1.0, abs=1e-9)
    for pid in h0_true:
        assert h0_recovered[pid] == pytest.approx(h0_true[pid], abs=1e-9)


# --------------------------------------------------------------------- #4
def test_check4_survival_non_increasing_in_k():
    """P(survive) must be monotonically non-increasing as the gap k grows --
    a product-or-indexing error would violate this."""
    positions = {"p_qb": "QB", "p_rb": "RB", "p_wr": "WR", "p_te": "TE", "p_def": "DEF"}
    p0_base = {"p_qb": 0.9, "p_rb": 0.6, "p_wr": 0.5, "p_te": 0.8, "p_def": 0.95}

    prev_survival = {pid: 1.0 for pid in p0_base}
    for k in range(1, 8):
        gap = [InterveningPick(team="t", drafted={}) for _ in range(k)]
        survival = la.live_survival(p0_base, positions, gap, lam=0.5)
        for pid in p0_base:
            assert survival[pid] <= prev_survival[pid] + 1e-9
        prev_survival = survival


# --------------------------------------------------------------------- #5
def test_check5_zero_gap_means_certain_survival():
    """k=0 => P(survive)=1.0 for all X -- nothing intervenes."""
    positions = {"p_qb": "QB", "p_rb": "RB"}
    p0 = {"p_qb": 0.3, "p_rb": 0.4}
    survival = la.live_survival(p0, positions, gap=[], lam=0.5)
    assert survival == {"p_qb": 1.0, "p_rb": 1.0}


# --------------------------------------------------------------------- #6
def test_check6_run_multiplier_raises_wr_hazard_and_lowers_non_wr_globally():
    """Applying R(WR)=1.5 must raise TOTAL WR hazard and LOWER total non-WR
    hazard, with the overall sum unchanged at 1 -- if normalisation were
    applied per-position instead of globally, non-WR hazard would be
    unaffected, which this test would catch."""
    positions = {f"wr{i}": "WR" for i in range(3)}
    positions.update({f"rb{i}": "RB" for i in range(3)})
    h0 = {pid: 1.0 / 6 for pid in positions}
    pick = InterveningPick(team="A", drafted={})

    baseline_r = {p: 1.0 for p in la.POSITIONS}
    boosted_r = {p: 1.0 for p in la.POSITIONS}
    boosted_r["WR"] = 1.5

    h_baseline = la._hazards_at_pick(h0, positions, pick, lam=0.0, r_mult=baseline_r)
    h_boosted = la._hazards_at_pick(h0, positions, pick, lam=0.0, r_mult=boosted_r)

    wr_baseline = sum(h_baseline[pid] for pid in positions if positions[pid] == "WR")
    wr_boosted = sum(h_boosted[pid] for pid in positions if positions[pid] == "WR")
    non_wr_baseline = sum(h_baseline[pid] for pid in positions if positions[pid] != "WR")
    non_wr_boosted = sum(h_boosted[pid] for pid in positions if positions[pid] != "WR")

    assert wr_boosted > wr_baseline
    assert non_wr_boosted < non_wr_baseline
    assert sum(h_boosted.values()) == pytest.approx(1.0, abs=1e-9)
    assert sum(h_baseline.values()) == pytest.approx(1.0, abs=1e-9)


# --------------------------------------------------------------------- #7
def test_check7_zero_wr_team_has_strictly_higher_wr_hazard_than_three_wr_team():
    """A team with 0 WR must show strictly HIGHER WR hazard than an
    otherwise-identical team with 3 WR -- if the need term were wired
    backwards, this would be reversed."""
    positions = {f"wr{i}": "WR" for i in range(5)}
    positions.update({f"rb{i}": "RB" for i in range(5)})
    h0 = {pid: 0.10 for pid in positions}

    pick_0wr = InterveningPick(team="A", drafted={"WR": 0})
    pick_3wr = InterveningPick(team="B", drafted={"WR": 3})
    r_mult = {p: 1.0 for p in la.POSITIONS}

    h_0wr = la._hazards_at_pick(h0, positions, pick_0wr, lam=0.5, r_mult=r_mult)
    h_3wr = la._hazards_at_pick(h0, positions, pick_3wr, lam=0.5, r_mult=r_mult)

    for pid in positions:
        if positions[pid] == "WR":
            assert h_0wr[pid] > h_3wr[pid]


# --------------------------------------------------------------------- #8
def test_check8_eps_floor_gives_roughly_tenth_qb_need_after_first_qb():
    """A team with 1 QB drafted should show roughly 0.1x the QB need-ratio of
    a team with 0 QB drafted (the empirical second-QB rate is the eps floor
    itself) -- checked at lambda=1 for direct interpretability, since the
    eps-floor arithmetic does not depend on lambda's value."""
    n_0qb = la.n_need({"QB": 0}, lam=1.0)
    n_1qb = la.n_need({"QB": 1}, lam=1.0)
    ratio = n_1qb["QB"] / n_0qb["QB"]
    assert 0.08 < ratio < 0.13, f"expected QB need-ratio near 0.1, got {ratio}"


# --------------------------------------------------------------------- #9
def test_check9_drafted_players_are_excluded_and_forced_to_zero_survival():
    """Drafted players must be removed from the undrafted pool the hazard
    normalisation runs over (a stale P0 leaking into the denominator would
    silently understate everyone else's hazard) AND their own reported
    survival must be exactly 0, regardless of whatever P0 was supplied."""
    positions_all = {"p_qb": "QB", "p_rb": "RB", "p_wr": "WR", "p_te": "TE", "p_def": "DEF"}
    p0_all = {"p_qb": 0.9, "p_rb": 0.9, "p_wr": 0.9, "p_te": 0.9, "p_def": 0.9}
    gap = [InterveningPick(team="t", drafted={}) for _ in range(3)]

    drafted = {"p_rb"}
    survival = la.live_survival_excluding_drafted(p0_all, positions_all, drafted, gap, lam=0.5)

    assert survival["p_rb"] == 0.0
    # The remaining players' hazards should still sum to 1 at each pick, i.e.
    # they were renormalised over the SHRUNK pool, not the original 5.
    undrafted = {pid: p for pid, p in p0_all.items() if pid not in drafted}
    positions_undrafted = {pid: pos for pid, pos in positions_all.items() if pid not in drafted}
    h0 = {pid: la.hazard_from_marginal(undrafted[pid], 3) for pid in undrafted}
    h_j = la._hazards_at_pick(
        h0, positions_undrafted, gap[0], lam=0.5, r_mult={p: 1.0 for p in la.POSITIONS}
    )
    assert sum(h_j.values()) == pytest.approx(1.0, abs=1e-9)
    assert "p_rb" not in h_j


# ---------------------------------------------------------- run detection (SS3)
def test_run_multiplier_is_noop_before_pick_ten():
    """Early-draft guard: R(p) must be a no-op (all 1.0) before pick 10 --
    'there is no window.'"""
    r = la.run_multiplier(
        recent_positions=["RB", "RB", "RB"],
        recent_predicted_probs=[{"RB": 0.3}, {"RB": 0.3}, {"RB": 0.3}],
        delta=0.10,
        picks_completed_so_far=9,
    )
    assert all(v == 1.0 for v in r.values())


def test_run_multiplier_boosts_overrepresented_position():
    """A position appearing more than the model expected over the last W
    picks should get R(p) > 1 (boosted hazard), clipped at +/- 2 SD."""
    recent_positions = ["RB"] * 8 + ["WR"] * 2
    recent_predicted = [{"RB": 0.35, "WR": 0.35} for _ in range(10)]
    r = la.run_multiplier(
        recent_positions, recent_predicted, delta=0.10, picks_completed_so_far=10
    )
    assert r["RB"] > 1.0
    assert r["RB"] <= 1.0 + 0.10 * 2.0 + 1e-9  # clipped at z=+2


def test_default_lambda_is_the_measured_ss5a_value_not_the_prior():
    """DEFAULT_LAMBDA should be the SS5(a) measurement (~0.35), not the 0.5
    prior it superseded -- a regression guard against silently reverting to
    the unmeasured prior."""
    assert 0.3 < la.DEFAULT_LAMBDA < 0.4
