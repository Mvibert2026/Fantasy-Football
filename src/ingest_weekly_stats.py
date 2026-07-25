"""Ingest nflverse weekly player stats (via nflreadpy) into a local SQLite cache.

Phase 1, Step 1 of docs/CLAUDE.md: raw historical data caching only. No scoring,
no ranking, no look-ahead-safe access controls here -- those belong to later
steps (see docs/decisions.md for why this table is intentionally "dumb").
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "player_weekly_stats"
PRIMARY_KEY = ("player_id", "season", "season_type", "week")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"


def default_seasons(today: dt.date | None = None, years: int = 5) -> list[int]:
    """Most recent `years` completed NFL seasons as of `today`.

    A season is considered complete once its start month (September) of the
    following calendar year has passed, i.e. before September we treat last
    calendar year as the latest available season.
    """
    today = today or dt.date.today()
    latest_season = today.year - 1 if today.month < 9 else today.year
    return list(range(latest_season - years + 1, latest_season + 1))


def fetch_weekly_stats(seasons: list[int]) -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_player_stats(seasons=seasons, summary_level="week")
    # A handful of rows per season carry no player_id: team-level penalty/safety
    # aggregates with no individual attribution (verified: only def_safeties,
    # penalties, penalty_yards are ever non-zero on them). They aren't a player
    # performance and, left in, would violate the primary key (NULL is not
    # unique in SQLite), silently duplicating on every re-ingest.
    return df.filter(pl.col("player_id").is_not_null())


def _polars_dtype_to_sqlite(dtype: pl.DataType) -> str:
    if dtype.is_integer() or dtype == pl.Boolean:
        return "INTEGER"
    if dtype.is_float():
        return "REAL"
    return "TEXT"


def build_create_table_sql(table: str, df: pl.DataFrame, primary_key: tuple[str, ...]) -> str:
    columns = [f'"{name}" {_polars_dtype_to_sqlite(dtype)}' for name, dtype in zip(df.columns, df.dtypes)]
    columns.append('"ingested_at" TEXT NOT NULL')
    pk = ", ".join(f'"{c}"' for c in primary_key)
    columns_sql = ",\n    ".join(columns)
    return f'CREATE TABLE IF NOT EXISTS "{table}" (\n    {columns_sql},\n    PRIMARY KEY ({pk})\n)'


def ensure_table(conn: sqlite3.Connection, table: str, df: pl.DataFrame, primary_key: tuple[str, ...]) -> None:
    conn.execute(build_create_table_sql(table, df, primary_key))


def upsert_dataframe(conn: sqlite3.Connection, table: str, df: pl.DataFrame) -> int:
    """Insert or replace rows keyed on the table's primary key. Returns rows written."""
    if df.height == 0:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    columns = list(df.columns) + ["ingested_at"]
    placeholders = ", ".join("?" for _ in columns)
    columns_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT OR REPLACE INTO "{table}" ({columns_sql}) VALUES ({placeholders})'
    rows = [tuple(row) + (ingested_at,) for row in df.iter_rows()]
    conn.executemany(sql, rows)
    return len(rows)


def ingest(seasons: list[int], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_weekly_stats(seasons)
    conn = sqlite3.connect(db_path)
    try:
        ensure_table(conn, TABLE_NAME, df, PRIMARY_KEY)
        written = upsert_dataframe(conn, TABLE_NAME, df)
        conn.commit()
    finally:
        conn.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=None,
        help="Season years to ingest (default: 5 most recently completed seasons).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite cache file (default: {DEFAULT_DB_PATH}).",
    )
    args = parser.parse_args()
    seasons = args.seasons or default_seasons()

    print(f"Fetching weekly player stats for seasons: {seasons}")
    written = ingest(seasons, args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
