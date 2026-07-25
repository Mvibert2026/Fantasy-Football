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
    out = backtest._rank_correlation_by_position(ranking, actuals, {})
    assert set(out) == {"QB", "RB"}
    assert out["QB"].spearman == pytest.approx(1.0)
    assert out["RB"].spearman == pytest.approx(1.0)


def test_no_pooled_scalar_is_exposed_on_the_result():
    """Regression guard: the original defect was a single blended correlation."""
    assert not hasattr(backtest, "_rank_correlation")
    assert "correlation_with_actual_finish" not in backtest.SeasonMetrics.__annotations__


def test_inverted_ranking_gives_negative_within_position_correlation():
    ranking = {"w1": 3, "w2": 2, "w3": 1}
    actuals = _actuals([("w1", 300.0, "WR"), ("w2", 200.0, "WR"), ("w3", 100.0, "WR")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {})
    assert out["WR"].spearman == pytest.approx(-1.0)


def test_busted_players_are_scored_zero_not_dropped():
    """A ranked player with no stat line busted; dropping him would be the
    survivorship error (statistical-guardrails.md §2)."""
    ranking = {"w1": 1, "ghost": 2, "w3": 3}
    actuals = _actuals([("w1", 300.0, "WR"), ("w3", 100.0, "WR")])
    positions = {"ghost": "WR"}
    out = backtest._rank_correlation_by_position(ranking, actuals, positions)
    assert out["WR"].n_players == 3
    assert out["WR"].n_with_actuals == 2


def test_position_group_with_too_few_players_returns_nan_not_a_number():
    ranking = {"t1": 1, "t2": 2}
    actuals = _actuals([("t1", 100.0, "TE"), ("t2", 50.0, "TE")])
    out = backtest._rank_correlation_by_position(ranking, actuals, {})
    assert np.isnan(out["TE"].spearman)


# ----------------------------- weighted aggregate -----------------------------


def test_weighted_aggregate_carries_its_weighting_label():
    per_pos = {
        "QB": backtest.PositionCorrelation("QB", 0.5, 10, 10),
        "RB": backtest.PositionCorrelation("RB", 0.9, 90, 90),
    }
    agg = backtest.weighted_aggregate(per_pos, weighting="by_n_players")
    assert agg.value == pytest.approx((0.5 * 10 + 0.9 * 90) / 100)
    assert "NOT a pooled" in agg.label
    assert agg.weighting == "by_n_players"


def test_weighted_aggregate_equal_weighting_differs_from_size_weighting():
    per_pos = {
        "QB": backtest.PositionCorrelation("QB", 0.5, 10, 10),
        "RB": backtest.PositionCorrelation("RB", 0.9, 90, 90),
    }
    assert backtest.weighted_aggregate(per_pos, "equal").value == pytest.approx(0.7)


def test_weighted_aggregate_rejects_unknown_weighting():
    per_pos = {"QB": backtest.PositionCorrelation("QB", 0.5, 10, 10)}
    with pytest.raises(ValueError):
        backtest.weighted_aggregate(per_pos, weighting="magic")


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
    # every position correlation reported must carry an interval
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
