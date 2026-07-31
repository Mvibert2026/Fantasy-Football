import sqlite3

import numpy as np
import pytest

import backtest
import db
import holdout
from scoring import ReplacementLevels

# Development seasons only -- 2025 is the locked holdout (src/holdout.py) and
# reading it from a test would be exactly the leak the lock exists to prevent.
DEV_SEASONS = [2022, 2023, 2024]


# ----------------------------- per-position correlation -----------------------------


def _actuals(pairs):
    """{pid: (points, position)}"""
    return {pid: (pts, pos) for pid, pts, pos in pairs}


def test_correlation_is_returned_per_position_not_pooled():
    ranking = {"q1": 1, "q2": 2, "q3": 3, "r1": 4, "r2": 5, "r3": 6}
    actuals = _actuals([
        ("q1", 300.0, "QB"), ("q2", 250.0, "QB"), ("q3", 200.0, "QB"),
        ("r1", 150.0, "RB"), ("r2", 120.0, "RB"), ("r3", 90.0, "RB"),
    ])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert set(out) == {"QB", "RB"}
    assert out["QB"].tau_b == pytest.approx(1.0)
    assert out["RB"].tau_b == pytest.approx(1.0)
    assert out["QB"].spearman == pytest.approx(1.0)


def test_no_pooled_scalar_is_exposed_on_the_result():
    """Regression guard: the original defect was a single blended correlation.
    ADR-B (thread 021) goes further -- no aggregate across positions may exist
    anywhere in this module, not even behind an explicit-request function."""
    assert not hasattr(backtest, "_rank_correlation")
    assert not hasattr(backtest, "weighted_aggregate")
    assert not hasattr(backtest, "WeightedAggregate")
    assert "correlation_with_actual_finish" not in backtest.SeasonMetrics.__annotations__


def test_scalar_return_type_is_rejected():
    """ADR-B: 'a scalar return type is a lint failure.' The function must always
    return a per-position dict, never a bare float, even for a single position."""
    ranking = {"w1": 1, "w2": 2, "w3": 3}
    actuals = _actuals([("w1", 300.0, "WR"), ("w2", 200.0, "WR"), ("w3", 100.0, "WR")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert isinstance(out, dict)
    assert all(isinstance(v, backtest.PositionCorrelation) for v in out.values())


def test_inverted_ranking_gives_negative_within_position_correlation():
    ranking = {"w1": 3, "w2": 2, "w3": 1}
    actuals = _actuals([("w1", 300.0, "WR"), ("w2", 200.0, "WR"), ("w3", 100.0, "WR")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert out["WR"].tau_b == pytest.approx(-1.0)
    assert out["WR"].spearman == pytest.approx(-1.0)


def test_busted_players_are_scored_zero_not_dropped():
    """A ranked player with no stat line busted; dropping him would be the
    survivorship error (statistical-guardrails.md §2). No minimum-games filter
    exists anywhere in this module (ADR-B)."""
    ranking = {"w1": 1, "ghost": 2, "w3": 3}
    actuals = _actuals([("w1", 300.0, "WR"), ("w3", 100.0, "WR")])
    positions = {"ghost": "WR"}
    out = backtest._rank_correlation_by_position(ranking, actuals, positions, n_permutation=200)
    assert out["WR"].n_players == 3
    assert out["WR"].n_with_actuals == 2


def test_position_group_with_too_few_players_returns_nan_not_a_number():
    ranking = {"t1": 1, "t2": 2}
    actuals = _actuals([("t1", 100.0, "TE"), ("t2", 50.0, "TE")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert np.isnan(out["TE"].tau_b)
    assert np.isnan(out["TE"].spearman)


def test_depth_cutoff_restricts_the_ranked_pool_to_primary_k():
    """WR primary K is 80 (ADR-B table). A 90-deep ranking must only pull the
    top 80 into the primary-K sample, and the top 40 into the secondary."""
    ranking = {f"w{i}": i for i in range(1, 91)}
    actuals = _actuals([(f"w{i}", 1000.0 - i, "WR") for i in range(1, 91)])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert out["WR"].k_primary == 80
    assert out["WR"].k_secondary == 40
    assert out["WR"].n_players == 80


def test_realized_producers_outside_ranked_set_are_reported_as_misses_not_dropped():
    """ADR-B: undrafted breakouts cannot enter a paired correlation (no
    prediction to pair), but must never be silently omitted."""
    ranking = {"w1": 1, "w2": 2, "w3": 3}
    actuals = _actuals([
        ("w1", 300.0, "WR"), ("w2", 200.0, "WR"), ("w3", 100.0, "WR"),
        ("breakout", 500.0, "WR"),  # highest scorer of the four, never ranked
    ])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    assert out["WR"].misses_n == 1
    assert out["WR"].misses == ("breakout",)
    # the miss must not have entered the paired sample
    assert out["WR"].n_players == 3


def test_instability_flag_trips_when_primary_and_secondary_k_disagree():
    """Construct a ranking that is perfect within the secondary-K (at-
    replacement) group but scrambled in the extra players between secondary
    and primary K, so primary-K tau_b and secondary-K tau_b diverge by more
    than the 0.15 ADR-B threshold."""
    # secondary K for TE is 10: perfectly ordered.
    perfect = {f"t{i}": i for i in range(1, 11)}
    perfect_pts = [(f"t{i}", 100.0 - i, "TE") for i in range(1, 11)]
    # primary K for TE is 20: the extra 10 are anti-ordered against their rank.
    scrambled = {f"t{i}": i for i in range(11, 21)}
    scrambled_pts = [(f"t{i}", float(i), "TE") for i in range(11, 21)]  # low rank -> high pts
    ranking = {**perfect, **scrambled}
    actuals = _actuals(perfect_pts + scrambled_pts)
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=200)
    te = out["TE"]
    assert abs(te.tau_b - te.tau_b_secondary) > backtest.INSTABILITY_DELTA
    assert te.unstable is True
    assert te.band == "unstable"


def test_permutation_interval_is_seeded_and_reproducible():
    ranking = {f"w{i}": i for i in range(1, 21)}
    actuals = _actuals([(f"w{i}", 100.0 - i * 1.7 % 13, "WR") for i in range(1, 21)])
    a = backtest._rank_correlation_by_position(ranking, actuals, {}, seed=99, n_permutation=500)
    b = backtest._rank_correlation_by_position(ranking, actuals, {}, seed=99, n_permutation=500)
    assert a["WR"].permutation_lo == b["WR"].permutation_lo
    assert a["WR"].permutation_hi == b["WR"].permutation_hi
    assert a["WR"].permutation_seed == b["WR"].permutation_seed


def test_band_for_tau_thresholds_match_the_adr_b_table():
    assert backtest._band_for_tau(0.05) == "no_ordering_skill"
    assert backtest._band_for_tau(0.15) == "weak"
    assert backtest._band_for_tau(0.30) == "moderate"
    assert backtest._band_for_tau(0.50) == "strong"


def test_uninformative_override_lowers_the_band_when_permutation_ci_spans_zero():
    """A small, noisy sample should land in a band no higher than what its
    tau_b implies, and drop one band if the 95% interval contains zero."""
    ranking = {"t1": 1, "t2": 2, "t3": 3, "t4": 4}
    # weak positive ordering, small n -- permutation interval should span 0.
    actuals = _actuals([("t1", 50.0, "TE"), ("t2", 60.0, "TE"), ("t3", 40.0, "TE"), ("t4", 55.0, "TE")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {}, n_permutation=500)
    te = out["TE"]
    if te.permutation_lo is not None and te.permutation_lo <= 0.0 <= te.permutation_hi:
        implied = backtest._band_for_tau(te.tau_b)
        assert backtest.BAND_ORDER.index(te.band) <= backtest.BAND_ORDER.index(implied)


# ----------------------------- bootstrap CIs -----------------------------


def test_single_season_yields_no_interval_and_says_why():
    ci = backtest.bootstrap_season_ci([12.0], seed=1)
    assert ci.lo is None and ci.hi is None
    assert ci.degenerate
    assert "NOT COMPUTABLE" in ci.note
    assert ci.point == 12.0


def test_few_seasons_flags_degeneracy_but_still_returns_an_interval():
    ci = backtest.bootstrap_season_ci([1.0, 2.0, 3.0, 4.0], seed=1, n_bootstrap=200)
    assert ci.lo is not None
    assert ci.degenerate
    assert "DEGENERATE" in ci.note
    assert ci.n_seasons == 4


def test_many_seasons_is_not_flagged_degenerate():
    ci = backtest.bootstrap_season_ci(list(range(10)), seed=1, n_bootstrap=200)
    assert not ci.degenerate
    assert ci.note == ""


def test_bootstrap_is_reproducible_under_a_fixed_seed():
    a = backtest.bootstrap_season_ci([1.0, 5.0, 3.0, 9.0], seed=7, n_bootstrap=300)
    b = backtest.bootstrap_season_ci([1.0, 5.0, 3.0, 9.0], seed=7, n_bootstrap=300)
    assert (a.lo, a.hi) == (b.lo, b.hi)
    assert a.seed == 7


def test_bootstrap_seed_is_recorded_in_the_result():
    ci = backtest.bootstrap_season_ci([1.0, 2.0, 3.0], seed=4242, n_bootstrap=50)
    assert ci.seed == 4242
    assert ci.n_bootstrap == 50


def test_paired_delta_of_identical_arms_is_exactly_zero():
    """Paired resampling must cancel; independent resampling would not."""
    vals = [10.0, 20.0, 30.0, 40.0]
    ci = backtest.paired_bootstrap_delta_ci(vals, vals, seed=3, n_bootstrap=500)
    assert ci.point == pytest.approx(0.0)
    assert ci.lo == pytest.approx(0.0)
    assert ci.hi == pytest.approx(0.0)


def test_paired_delta_detects_a_constant_offset_with_zero_width_interval():
    a = [10.0, 20.0, 30.0]
    b = [5.0, 15.0, 25.0]
    ci = backtest.paired_bootstrap_delta_ci(a, b, seed=3, n_bootstrap=500)
    assert ci.point == pytest.approx(5.0)
    assert ci.lo == pytest.approx(5.0)


def test_paired_delta_drops_seasons_missing_from_either_arm():
    ci = backtest.paired_bootstrap_delta_ci(
        [1.0, float("nan"), 3.0], [0.0, 1.0, 1.0], seed=1, n_bootstrap=100
    )
    assert ci.n_seasons == 2


# ----------------------------- starter_vbd -----------------------------


def _lineup_fixture():
    actuals = _actuals([
        ("qb1", 350.0, "QB"), ("rb1", 300.0, "RB"), ("rb2", 280.0, "RB"),
        ("wr1", 270.0, "WR"), ("wr2", 260.0, "WR"),
    ])
    vbd = {"qb1": 100.0, "rb1": 90.0, "rb2": 80.0, "wr1": 70.0, "wr2": 60.0}
    return actuals, vbd


def test_starter_vbd_is_sensitive_to_cross_position_ordering():
    """This is the whole reason the metric exists: vbd_sum takes top-N per
    position and therefore cannot see cross-positional reordering at all."""
    actuals, vbd = _lineup_fixture()
    qb_first = {"qb1": 1, "rb1": 2, "rb2": 3, "wr1": 4, "wr2": 5}
    qb_last = {"rb1": 1, "rb2": 2, "wr1": 3, "wr2": 4, "qb1": 5}
    a = backtest.top_k_starter_vbd(qb_first, actuals, vbd, {}, k=4)
    b = backtest.top_k_starter_vbd(qb_last, actuals, vbd, {}, k=4)
    assert a != b
    assert a == pytest.approx(100.0 + 90.0 + 80.0 + 70.0)  # QB + 2RB + WR
    assert b == pytest.approx(90.0 + 80.0 + 70.0 + 60.0)   # 2RB + 2WR, no QB


def test_vbd_sum_is_blind_to_cross_position_ordering():
    """Documents the blind spot that motivated starter_vbd. If this ever starts
    failing, the two metrics have stopped being complementary."""
    actuals, vbd = _lineup_fixture()
    levels = ReplacementLevels()
    qb_first = {"qb1": 1, "rb1": 2, "rb2": 3, "wr1": 4, "wr2": 5}
    qb_last = {"rb1": 1, "rb2": 2, "wr1": 3, "wr2": 4, "qb1": 5}
    a = backtest._vbd_sum_for_ranking(qb_first, actuals, vbd, levels, {})
    b = backtest._vbd_sum_for_ranking(qb_last, actuals, vbd, levels, {})
    assert a == pytest.approx(b)


def test_starter_vbd_respects_flex_eligibility():
    """A second QB cannot occupy a FLEX slot."""
    actuals = _actuals([("qb1", 350.0, "QB"), ("qb2", 340.0, "QB"), ("rb1", 300.0, "RB")])
    vbd = {"qb1": 100.0, "qb2": 95.0, "rb1": 90.0}
    ranking = {"qb1": 1, "qb2": 2, "rb1": 3}
    total = backtest.top_k_starter_vbd(ranking, actuals, vbd, {}, k=3)
    assert total == pytest.approx(100.0 + 90.0)  # qb2 gets no slot


def test_starter_vbd_uses_flex_for_surplus_skill_players():
    actuals = _actuals([(f"rb{i}", 100.0, "RB") for i in range(1, 6)])
    vbd = {f"rb{i}": 10.0 for i in range(1, 6)}
    ranking = {f"rb{i}": i for i in range(1, 6)}
    # 2 dedicated RB slots + 2 FLEX = 4 of the 5 start
    assert backtest.top_k_starter_vbd(ranking, actuals, vbd, {}, k=5) == pytest.approx(40.0)


def test_starter_vbd_budget_k_binds():
    actuals, vbd = _lineup_fixture()
    ranking = {"qb1": 1, "rb1": 2, "rb2": 3, "wr1": 4, "wr2": 5}
    assert backtest.top_k_starter_vbd(ranking, actuals, vbd, {}, k=2) == pytest.approx(190.0)


# ----------------------- never-played players are not replacement-level -----------------------
#
# Regression test for the defect the strategist found while ruling on the primary
# metric (docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md SS4.1): a ranked
# player with a resolved position but NO weekly row at all (retired, cut, a
# season-ending injury) is absent from `_season_actuals`, so `vbd.get(pid, 0.0)`
# silently scored him as exactly replacement level instead of the true disaster
# value `0 - replacement_points[pos]`.


def test_never_played_player_scores_the_replacement_deficit_not_zero_vbd():
    """A first-round RB who never takes a snap must score as a wasted pick
    (0 points - the RB replacement level), not as a merely-average, easily
    replaced player (0.0 VBD)."""
    # Only rb2 (a lesser player) has a real weekly row; rb1 (the disaster pick)
    # never appears in `actuals` at all, but IS resolved to RB via `positions`
    # -- exactly what build_position_lookup's "rankings win" query does for a
    # ranked player absent from the season's stat rows.
    actuals = _actuals([("rb2", 40.0, "RB")])
    levels = ReplacementLevels()
    vbd, replacement_points = backtest._vbd_lookup(actuals, levels)
    positions = {"rb1": "RB", "rb2": "RB"}
    ranking = {"rb1": 1, "rb2": 2}

    total = backtest._vbd_sum_for_ranking(
        ranking, actuals, vbd, levels, positions, replacement_points
    )

    rb2_contribution = vbd["rb2"]
    disaster_contribution = total - rb2_contribution

    # The defective version contributed exactly 0.0 for rb1 (replacement
    # level). The fix must contribute the true deficit: 0 points minus the RB
    # replacement level, i.e. a negative number equal to -replacement_points.
    assert disaster_contribution != pytest.approx(0.0)
    assert disaster_contribution == pytest.approx(-replacement_points["RB"])
    assert disaster_contribution < 0


def test_never_played_player_in_starter_vbd_also_scores_the_deficit():
    actuals = _actuals([("rb2", 40.0, "RB")])
    levels = ReplacementLevels()
    vbd, replacement_points = backtest._vbd_lookup(actuals, levels)
    positions = {"rb1": "RB", "rb2": "RB"}
    # rb1 ranked ahead of rb2 and consumes the first starting RB slot despite
    # never appearing in `actuals`.
    ranking = {"rb1": 1, "rb2": 2}

    total = backtest.top_k_starter_vbd(
        ranking, actuals, vbd, positions, k=2, replacement_points=replacement_points
    )

    # rb1 fills one dedicated RB slot, rb2 fills the other (STARTER_SLOTS has
    # 2 RB slots) -- both consume a slot, so the total must reflect rb1's true
    # deficit added to rb2's real vbd, not rb1 contributing nothing.
    assert total == pytest.approx(vbd["rb2"] - replacement_points["RB"])


# ----------------------------- integration -----------------------------


@pytest.mark.requires_db
def test_multi_season_run_produces_cis_and_records_seed():
    result = backtest.run_backtest_multi(DEV_SEASONS, n_bootstrap=200)
    assert result.seed == backtest.DEFAULT_CONFIG.random_seed
    assert result.primary_baseline == "rescored_consensus_board"
    board = result.arms["rescored_consensus_board"]
    assert board.available
    assert board.vbd_sum_ci is not None and board.vbd_sum_ci.lo is not None
    assert board.starter_vbd_ci is not None
    # every position correlation reported must carry an interval, both primary
    # (tau_b) and secondary (Spearman)
    for pos, ci in board.tau_b_ci.items():
        assert ci.lo is not None and ci.hi is not None
    for pos, ci in board.spearman_ci.items():
        assert ci.lo is not None and ci.hi is not None


@pytest.mark.requires_db
def test_board_arm_skips_the_first_consensus_season_with_a_reason():
    """2021 has no prior consensus season, so the rank->points curve cannot be
    fitted without look-ahead. It must be skipped and explained, not crash."""
    result = backtest.run_backtest_multi([2021, 2022], n_bootstrap=50)
    board = result.arms["rescored_consensus_board"]
    assert 2021 in board.skipped_seasons
    assert "no consensus seasons before 2021" in board.skipped_seasons[2021]


@pytest.mark.requires_db
def test_consensus_adp_arm_is_unavailable_with_an_explanation():
    result = backtest.run_backtest_multi([2023, 2024], n_bootstrap=50)
    adp = result.arms["consensus_adp"]
    assert adp.available is False
    assert "robots.txt" in adp.reason


@pytest.mark.requires_db
def test_rescored_board_and_raw_consensus_are_identical_on_within_position_metrics():
    """Structural fact worth locking down: the board only reorders ACROSS
    positions, so within-position metrics cannot distinguish it from consensus.
    starter_vbd is the metric that can."""
    result = backtest.run_backtest_multi(DEV_SEASONS, n_bootstrap=200)
    d = result.deltas_vs_primary["fantasypros_ecr_raw"]
    assert abs(d["vbd_sum"].point) < 1e-6
    assert abs(d["starter_vbd"].point) > 1.0


@pytest.mark.requires_db
def test_backtest_refuses_to_evaluate_the_locked_holdout():
    """Structural enforcement, not a convention."""
    with pytest.raises(holdout.HoldoutViolation):
        backtest.run_backtest_multi([2023, 2024, holdout.HOLDOUT_SEASON], n_bootstrap=10)


@pytest.mark.requires_db
def test_backtest_permits_the_holdout_inside_a_logged_final_evaluation():
    with holdout.DEFAULT_LOCK.final_evaluation(reason="test: verify the unlock path works"):
        result = backtest.run_backtest_multi(
            [2024, holdout.HOLDOUT_SEASON], n_bootstrap=10
        )
    assert holdout.HOLDOUT_SEASON in result.seasons
