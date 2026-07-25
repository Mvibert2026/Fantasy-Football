import datetime as dt
import sqlite3

import polars as pl
import pytest

import ingest_weekly_stats as ingest_mod


def test_default_seasons_before_season_start():
    seasons = ingest_mod.default_seasons(today=dt.date(2026, 7, 25), years=5)
    assert seasons == [2021, 2022, 2023, 2024, 2025]


def test_default_seasons_after_season_start():
    seasons = ingest_mod.default_seasons(today=dt.date(2026, 10, 1), years=5)
    assert seasons == [2022, 2023, 2024, 2025, 2026]


def _sample_df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={
            "player_id": pl.String,
            "season": pl.Int32,
            "season_type": pl.String,
            "week": pl.Int32,
            "passing_yards": pl.Int32,
            "passing_epa": pl.Float64,
        },
    )


def test_create_table_sql_maps_dtypes():
    df = _sample_df([])
    sql = ingest_mod.build_create_table_sql(ingest_mod.TABLE_NAME, df, ingest_mod.PRIMARY_KEY)
    assert '"player_id" TEXT' in sql
    assert '"season" INTEGER' in sql
    assert '"passing_epa" REAL' in sql
    assert '"ingested_at" TEXT NOT NULL' in sql
    assert 'PRIMARY KEY ("player_id", "season", "season_type", "week")' in sql


def test_upsert_is_idempotent():
    conn = sqlite3.connect(":memory:")
    df = _sample_df(
        [
            {"player_id": "P1", "season": 2024, "season_type": "REG", "week": 1, "passing_yards": 250, "passing_epa": 1.5},
            {"player_id": "P2", "season": 2024, "season_type": "REG", "week": 1, "passing_yards": 100, "passing_epa": 0.2},
        ]
    )
    ingest_mod.ensure_table(conn, ingest_mod.TABLE_NAME, df, ingest_mod.PRIMARY_KEY)

    written_first = ingest_mod.upsert_dataframe(conn, ingest_mod.TABLE_NAME, df)
    written_second = ingest_mod.upsert_dataframe(conn, ingest_mod.TABLE_NAME, df)

    assert written_first == 2
    assert written_second == 2
    row_count = conn.execute(f'SELECT COUNT(*) FROM "{ingest_mod.TABLE_NAME}"').fetchone()[0]
    assert row_count == 2


def test_upsert_replaces_changed_values_without_duplicating():
    conn = sqlite3.connect(":memory:")
    df_v1 = _sample_df(
        [{"player_id": "P1", "season": 2024, "season_type": "REG", "week": 1, "passing_yards": 250, "passing_epa": 1.5}]
    )
    ingest_mod.ensure_table(conn, ingest_mod.TABLE_NAME, df_v1, ingest_mod.PRIMARY_KEY)
    ingest_mod.upsert_dataframe(conn, ingest_mod.TABLE_NAME, df_v1)

    df_v2 = _sample_df(
        [{"player_id": "P1", "season": 2024, "season_type": "REG", "week": 1, "passing_yards": 999, "passing_epa": 1.5}]
    )
    ingest_mod.upsert_dataframe(conn, ingest_mod.TABLE_NAME, df_v2)

    row_count = conn.execute(f'SELECT COUNT(*) FROM "{ingest_mod.TABLE_NAME}"').fetchone()[0]
    stored_yards = conn.execute(
        f'SELECT passing_yards FROM "{ingest_mod.TABLE_NAME}" WHERE player_id = ?', ("P1",)
    ).fetchone()[0]
    assert row_count == 1
    assert stored_yards == 999


def test_upsert_empty_dataframe_writes_nothing():
    conn = sqlite3.connect(":memory:")
    df = _sample_df([])
    ingest_mod.ensure_table(conn, ingest_mod.TABLE_NAME, df, ingest_mod.PRIMARY_KEY)
    written = ingest_mod.upsert_dataframe(conn, ingest_mod.TABLE_NAME, df)
    assert written == 0


@pytest.mark.network
def test_fetch_weekly_stats_real_single_season():
    df = ingest_mod.fetch_weekly_stats([2024])
    assert df.height > 0
    for col in ("player_id", "season", "week", "season_type", "passing_yards", "receiving_yards", "fantasy_points"):
        assert col in df.columns
    assert set(df["season"].unique().to_list()) == {2024}
    # Regression: team-level rows with no player_id must be filtered before
    # they ever reach the DB layer (see fetch_weekly_stats docstring/comment).
    assert df["player_id"].null_count() == 0


@pytest.mark.network
def test_ingest_end_to_end(tmp_path):
    db_path = tmp_path / "nfl_test.db"
    written = ingest_mod.ingest([2024], db_path)
    assert written > 0
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        row_count = conn.execute(f'SELECT COUNT(*) FROM "{ingest_mod.TABLE_NAME}"').fetchone()[0]
        assert row_count == written

        # Re-running ingestion for the same season must not create duplicates.
        written_again = ingest_mod.ingest([2024], db_path)
        row_count_again = conn.execute(f'SELECT COUNT(*) FROM "{ingest_mod.TABLE_NAME}"').fetchone()[0]
        assert written_again == written
        assert row_count_again == row_count
    finally:
        conn.close()
