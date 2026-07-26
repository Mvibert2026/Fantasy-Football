import sqlite3

import polars as pl
import pytest

import db


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE player_weekly_stats (
            player_id TEXT, player_name TEXT, position TEXT, team TEXT,
            season INTEGER, season_type TEXT, week INTEGER,
            passing_yards INTEGER, passing_tds INTEGER, passing_interceptions INTEGER,
            rushing_yards INTEGER, rushing_tds INTEGER,
            receptions INTEGER, receiving_yards INTEGER, receiving_tds INTEGER,
            fumbles_lost_total INTEGER, special_teams_tds INTEGER,
            passing_2pt_conversions INTEGER, rushing_2pt_conversions INTEGER,
            receiving_2pt_conversions INTEGER, fumble_recovery_tds INTEGER
        )
        """
    )
    rows = [
        ("P1", "Player One", "WR", "AAA", 2023, "REG", 1, 0, 0, 0, 0, 0, 5, 80, 1, 0, 0, 0, 0, 0, 0),
        ("P1", "Player One", "WR", "AAA", 2024, "REG", 1, 0, 0, 0, 0, 0, 6, 90, 1, 0, 0, 0, 0, 0, 0),
        ("P1", "Player One", "WR", "AAA", 2025, "REG", 1, 0, 0, 0, 0, 0, 7, 100, 2, 0, 0, 0, 0, 0, 0),
    ]
    c.executemany(
        "INSERT INTO player_weekly_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    c.execute(db._CREATE_SCORING_VIEW_SQL)
    c.commit()
    yield c
    c.close()


def test_cutoff_store_allows_strictly_prior_seasons(conn):
    store = db.CutoffEnforcedStore(conn, cutoff_season=2025)
    rows = list(store.player_week_rows(seasons=[2023, 2024]))
    assert {r["season"] for r in rows} == {2023, 2024}


def test_cutoff_store_refuses_cutoff_season_itself(conn):
    store = db.CutoffEnforcedStore(conn, cutoff_season=2025)
    with pytest.raises(db.LookAheadViolation):
        list(store.player_week_rows(seasons=[2025]))


def test_cutoff_store_refuses_season_after_cutoff(conn):
    store = db.CutoffEnforcedStore(conn, cutoff_season=2024)
    with pytest.raises(db.LookAheadViolation):
        list(store.player_week_rows(seasons=[2025]))


def test_cutoff_store_refuses_mixed_valid_and_invalid_seasons(conn):
    store = db.CutoffEnforcedStore(conn, cutoff_season=2025)
    with pytest.raises(db.LookAheadViolation):
        list(store.player_week_rows(seasons=[2023, 2025]))


def test_cutoff_store_default_omits_cutoff_season(conn):
    store = db.CutoffEnforcedStore(conn, cutoff_season=2025)
    rows = list(store.player_week_rows())
    assert all(r["season"] < 2025 for r in rows)
    assert {r["season"] for r in rows} == {2023, 2024}


def test_actual_season_outcomes_reads_target_season(conn):
    rows = list(db.actual_season_outcomes(conn, 2025))
    assert len(rows) == 1
    assert rows[0]["season"] == 2025
    assert rows[0]["receiving_yards"] == 100


def test_scoring_view_maps_interceptions_and_fumbles_lost(conn):
    row = list(db.actual_season_outcomes(conn, 2025))[0]
    assert "interceptions" in row.keys()
    assert "fumbles_lost" in row.keys()
