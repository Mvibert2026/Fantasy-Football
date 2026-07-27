import csv
import math
import sqlite3

import pytest

import db as dbmod
import make_board
from scoring import ReplacementLevels


# --------------------------- pure-function tests ---------------------------


def test_board_row_carries_player_id_field():
    """Thread 052: BoardRow must carry the gsis-style player_id so
    export_contract.py can populate board.json's player_id_gsis instead of
    hardcoding None. A field that silently vanished here would resurrect the
    null-join bug without any test noticing."""
    row = make_board.BoardRow(
        overall_rank=1, player="Test Player", position="RB",
        projected_points=100.0, vbd=50.0, vbd_lo=40.0, vbd_hi=60.0,
        consensus_rank=1, delta_vs_consensus=0, player_id="00-0000001",
    )
    assert row.player_id == "00-0000001"


def test_fit_one_recovers_a_known_log_curve():
    # points = 300 - 50*ln(rank), exactly
    pairs = [(r, 300 - 50 * math.log(r)) for r in range(1, 31)]
    curve = make_board._fit_one("RB", pairs)
    assert curve.intercept == pytest.approx(300, abs=1e-6)
    assert curve.slope_log_rank == pytest.approx(-50, abs=1e-6)
    assert curve.r_squared == pytest.approx(1.0, abs=1e-9)


def test_fit_one_slope_is_negative_on_realistic_declining_data():
    pairs = [(r, 300 - 50 * math.log(r) + (5 if r % 2 else -5)) for r in range(1, 31)]
    curve = make_board._fit_one("WR", pairs)
    assert curve.slope_log_rank < 0


def test_fit_one_returns_none_on_insufficient_data():
    assert make_board._fit_one("TE", [(1, 100.0), (2, 90.0)]) is None


def test_rank_curve_predict_clamps_rank_below_one():
    curve = make_board.RankCurve("QB", 300.0, -50.0, 0.5, 10.0, 100, 20)
    assert curve.predict(0) == pytest.approx(300.0)
    assert curve.predict(1) == pytest.approx(300.0)


def test_rank_curve_is_monotone_decreasing():
    curve = make_board.RankCurve("QB", 300.0, -50.0, 0.5, 10.0, 100, 20)
    vals = [curve.predict(r) for r in range(1, 21)]
    assert all(a > b for a, b in zip(vals, vals[1:]))


# --------------------------- fixture-backed tests ---------------------------


@pytest.fixture
def seeded_conn():
    """Small synthetic DB: two prior seasons of consensus + outcomes."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE rankings (
            ranking_source TEXT, source TEXT, season INTEGER, player_id TEXT,
            player_name TEXT, adp_rank INTEGER, adp_value REAL, as_of_date TEXT,
            position TEXT, is_preseason_final INTEGER, ingested_at TEXT)"""
    )
    conn.execute(
        """CREATE TABLE player_weekly_stats (
            player_id TEXT, player_name TEXT, position TEXT, team TEXT,
            season INTEGER, season_type TEXT, week INTEGER,
            passing_yards INTEGER, passing_tds INTEGER, passing_interceptions INTEGER,
            rushing_yards INTEGER, rushing_tds INTEGER,
            receptions INTEGER, receiving_yards INTEGER, receiving_tds INTEGER,
            fumbles_lost_total INTEGER, special_teams_tds INTEGER,
            passing_2pt_conversions INTEGER, rushing_2pt_conversions INTEGER,
            receiving_2pt_conversions INTEGER, fumble_recovery_tds INTEGER,
            carries INTEGER, targets INTEGER)"""
    )
    for season in (2023, 2024, 2025):
        for i in range(1, 13):
            pid = f"RB{i}"
            conn.execute(
                "INSERT INTO rankings VALUES ('expert','fantasypros_ecr',?,?,?,?,?, '2024-08-30','RB',1,'x')",
                (season, pid, f"Runner {i}", i, float(i)),
            )
            # rushing yards decline with rank -> points decline with rank
            yards = max(0, 1200 - 80 * i)
            conn.execute(
                "INSERT INTO player_weekly_stats VALUES (?,?,'RB','AAA',?,'REG',1,"
                "0,0,0,?,0,0,0,0,0,0,0,0,0,0,?,0)",
                (pid, f"Runner {i}", season, yards, 10),
            )
    conn.commit()
    conn.execute(dbmod._CREATE_SCORING_VIEW_SQL)
    conn.commit()
    yield conn
    conn.close()


def test_fit_rank_curves_rejects_training_on_the_target_season(seeded_conn):
    """Fitting the curve on the season it will rank is look-ahead leakage."""
    with pytest.raises(ValueError, match="at or after target_season"):
        make_board.fit_rank_curves(seeded_conn, 2024, training_seasons=[2023, 2024])


def test_fit_rank_curves_rejects_future_training_seasons(seeded_conn):
    with pytest.raises(ValueError, match="at or after target_season"):
        make_board.fit_rank_curves(seeded_conn, 2024, training_seasons=[2025])


def test_fit_rank_curves_raises_when_no_prior_seasons_exist(seeded_conn):
    with pytest.raises(ValueError, match="no consensus seasons before"):
        make_board.fit_rank_curves(seeded_conn, 2023)


def test_fit_rank_curves_defaults_to_strictly_prior_seasons(seeded_conn):
    curves = make_board.fit_rank_curves(seeded_conn, 2025)
    assert "RB" in curves
    assert curves["RB"].slope_log_rank < 0


def test_collect_observations_scores_unranked_players_as_zero(seeded_conn):
    """A ranked player who never records a stat busted; that is an outcome,
    not a missing value (statistical-guardrails.md §2 survivorship)."""
    seeded_conn.execute(
        "INSERT INTO rankings VALUES ('expert','fantasypros_ecr',2023,'GHOST','Ghost',13,13.0,"
        "'2024-08-30','RB',1,'x')"
    )
    seeded_conn.commit()
    obs = make_board.collect_observations(seeded_conn, [2023])
    ghost = [p for p in obs[2023]["RB"] if p[0] == 13]
    assert ghost and ghost[0][1] == 0.0


def test_collect_observations_respects_relevant_depth(seeded_conn):
    obs = make_board.collect_observations(seeded_conn, [2023])
    assert all(rank <= make_board.RELEVANT_DEPTH["RB"] for rank, _ in obs[2023]["RB"])


def test_build_board_is_sorted_by_vbd_descending(seeded_conn):
    board, _ = make_board.build_board(seeded_conn, 2025, n_bootstrap=0)
    vbds = [r.vbd for r in board]
    assert vbds == sorted(vbds, reverse=True)
    assert [r.overall_rank for r in board] == list(range(1, len(board) + 1))


def test_delta_vs_consensus_sign_convention(seeded_conn):
    """Positive delta means OUR board is higher on the player than consensus."""
    board, _ = make_board.build_board(seeded_conn, 2025, n_bootstrap=0)
    for r in board:
        assert r.delta_vs_consensus == r.consensus_rank - r.overall_rank


def test_board_as_ranking_maps_back_to_player_ids(seeded_conn):
    board, _ = make_board.build_board(seeded_conn, 2025, n_bootstrap=0)
    ranking = make_board.board_as_ranking(board, seeded_conn, 2025)
    assert set(ranking.values()) == set(range(1, len(board) + 1))
    assert all(pid.startswith("RB") for pid in ranking)


def test_write_board_csv_includes_confidence_interval_columns(seeded_conn, tmp_path):
    board, _ = make_board.build_board(seeded_conn, 2025, n_bootstrap=50)
    out = tmp_path / "board_test.csv"
    make_board.write_board_csv(board, out)
    with out.open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert "vbd_lo95" in header and "vbd_hi95" in header


def test_bootstrap_intervals_are_reproducible_under_a_fixed_seed(seeded_conn):
    levels = ReplacementLevels()
    a = make_board.bootstrap_vbd_intervals(seeded_conn, 2025, levels, n_bootstrap=100, seed=42)
    b = make_board.bootstrap_vbd_intervals(seeded_conn, 2025, levels, n_bootstrap=100, seed=42)
    assert a == b


def test_bootstrap_interval_brackets_the_point_estimate(seeded_conn):
    board, _ = make_board.build_board(seeded_conn, 2025, n_bootstrap=300)
    top = board[0]
    assert top.vbd_lo <= top.vbd <= top.vbd_hi


# --------------------------- real-data integration ---------------------------


@pytest.mark.requires_db
def test_real_2026_board_builds_and_is_position_complete():
    conn = dbmod.connect()
    try:
        board, curves = make_board.build_board(conn, 2026, n_bootstrap=100)
    finally:
        conn.close()
    assert len(board) > 100
    assert set(curves) == set(make_board.BOARD_POSITIONS)
    # every curve must slope downward: a worse consensus rank cannot project higher
    assert all(c.slope_log_rank < 0 for c in curves.values())
    # no kicker in this league -- K must never reach the board
    assert all(r.position in make_board.BOARD_POSITIONS for r in board)


@pytest.mark.requires_db
def test_real_board_curve_r_squared_is_reported_and_low():
    """Guards the honesty claim in the module docstring: consensus rank is a
    weak predictor. If R2 ever jumps high, suspect leakage before celebrating."""
    conn = dbmod.connect()
    try:
        curves = make_board.fit_rank_curves(conn, 2026)
    finally:
        conn.close()
    for pos, c in curves.items():
        assert 0.0 < c.r_squared < 0.6, f"{pos} R2={c.r_squared} outside expected weak-signal range"
