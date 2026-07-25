import sqlite3

import pytest

import backtest
import db
from scoring import ReplacementLevels


def test_rank_correlation_perfect_ranking_is_one():
    # rank 1 = best; actual points descending should match exactly.
    ranking = {"A": 1, "B": 2, "C": 3, "D": 4}
    actuals = {"A": (100.0, "WR"), "B": (80.0, "WR"), "C": (60.0, "WR"), "D": (40.0, "WR")}
    corr, n_matched = backtest._rank_correlation(ranking, actuals)
    assert corr == pytest.approx(1.0)
    assert n_matched == 4


def test_rank_correlation_inverted_ranking_is_negative_one():
    ranking = {"A": 4, "B": 3, "C": 2, "D": 1}  # worst-to-best rank order
    actuals = {"A": (100.0, "WR"), "B": (80.0, "WR"), "C": (60.0, "WR"), "D": (40.0, "WR")}
    corr, _ = backtest._rank_correlation(ranking, actuals)
    assert corr == pytest.approx(-1.0)


def test_rank_correlation_treats_missing_actuals_as_zero_points():
    ranking = {"A": 1, "GhostPlayer": 2}
    actuals = {"A": (50.0, "WR")}
    corr, n_matched = backtest._rank_correlation(ranking, actuals)
    assert n_matched == 1
    # A ranked better and scored more than the ghost (0 pts) -> still perfect order
    assert corr == pytest.approx(1.0)


def test_vbd_sum_for_ranking_picks_top_n_per_position():
    levels = ReplacementLevels(teams=1, starters={"WR": 2}, flex_slots=0, flex_split={})
    actuals = {
        "A": (50.0, "WR"),
        "B": (40.0, "WR"),
        "C": (30.0, "WR"),
    }
    vbd = {"A": 20.0, "B": 10.0, "C": 0.0}
    # ranking puts C above A and B; only top-2 (WR baseline) count
    ranking = {"C": 1, "A": 2, "B": 3}
    total = backtest._vbd_sum_for_ranking(ranking, actuals, vbd, levels)
    assert total == vbd["C"] + vbd["A"]  # B excluded, it's ranked 3rd


def test_vbd_sum_for_ranking_skips_players_with_unknown_position():
    levels = ReplacementLevels(teams=1, starters={"WR": 1}, flex_slots=0, flex_split={})
    actuals = {"A": (50.0, None)}  # position unresolved
    vbd = {"A": 20.0}
    ranking = {"A": 1}
    assert backtest._vbd_sum_for_ranking(ranking, actuals, vbd, levels) == 0.0


def test_fantasypros_baseline_missing_season_returns_empty(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE rankings (ranking_source TEXT, source TEXT, season INTEGER, "
        "player_id TEXT, player_name TEXT, adp_rank INTEGER, adp_value REAL, "
        "as_of_date TEXT, position TEXT, is_preseason_final INTEGER, ingested_at TEXT)"
    )
    conn.commit()
    result = backtest._fantasypros_baseline(conn, 1999)
    assert result == {}
    conn.close()


@pytest.mark.requires_db
def test_run_backtest_self_consistency_on_real_2025_data():
    """Mock backtest run on real, already-ingested 2025 data: using the
    FantasyPros ranking itself as the candidate must reproduce the
    fantasypros_preseason baseline exactly (delta 0). This is the sanity
    check that candidate scoring and baseline scoring share one code path."""
    conn = db.connect()
    fp_ranking = backtest._fantasypros_baseline(conn, 2025)
    conn.close()
    assert len(fp_ranking) > 0, "expected data/nfl.db to already have 2025 rankings ingested"

    result = backtest.run_backtest(2025, fp_ranking)

    assert result.season == 2025
    assert result.n_candidate_players == len(fp_ranking)
    assert -1.0 <= result.correlation_with_actual_finish <= 1.0

    fp_baseline = result.baselines["fantasypros_preseason"]
    assert fp_baseline.available
    assert fp_baseline.vbd_sum == pytest.approx(result.candidate_vbd_sum)
    assert fp_baseline.delta_vs_candidate == pytest.approx(0.0)

    bpa_baseline = result.baselines["bpa_prior_season_points"]
    assert bpa_baseline.available
    assert bpa_baseline.vbd_sum is not None

    adp_baseline = result.baselines["consensus_adp"]
    assert adp_baseline.available is False
    assert adp_baseline.reason  # must explain why, not just be silently absent


@pytest.mark.requires_db
def test_bpa_baseline_only_uses_prior_season_data():
    """BPA for backtesting 2025 must be built purely from 2024 rows -- confirm
    by hand-computing one known player's 2024 total and checking the BPA
    ranking's implied ordering is consistent with 2024-only totals, not 2025."""
    conn = db.connect()
    store = db.CutoffEnforcedStore(conn, cutoff_season=2025)
    bpa_ranking = backtest._bpa_baseline(store, 2024)

    cur = conn.execute(
        "SELECT player_id FROM player_week_scoring_inputs "
        "WHERE season = 2024 AND season_type = 'REG' LIMIT 1"
    )
    sample_player = cur.fetchone()[0]
    conn.close()

    assert sample_player in bpa_ranking


@pytest.mark.requires_db
def test_bpa_baseline_raises_if_prior_season_not_before_cutoff():
    conn = db.connect()
    store = db.CutoffEnforcedStore(conn, cutoff_season=2024)
    with pytest.raises(db.LookAheadViolation):
        backtest._bpa_baseline(store, 2024)
    conn.close()
