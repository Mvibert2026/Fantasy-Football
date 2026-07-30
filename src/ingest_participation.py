"""Ingest nflverse play-level participation (via nflreadpy `load_participation`)
into `data/nfl.db`.

WHY THIS EXISTS. docs/test-registry.md #16 (YPRR) and #17 (route participation)
were tagged `nflverse:FTN`, but FTN charting carries no per-player columns at
all -- no receiver id, no routes-run (see docs/research/analyst-factor-sweep-
2026-07-30.md Sec1). The real source for on-field player identity per play is
this loader's `offense_players` column. Also supplies `offense_personnel` (2-WR
rate, registry N25) and, joined to PBP `yardline_100`, red-zone snap rate
(registry N14).

INGESTION ONLY. This table is stored close to raw: one row per play, with
`offense_players` / `defense_players` left as the source's semicolon-delimited
gsis-id strings rather than exploded into a player-week table. Explode/join
logic (e.g. computing routes run per player) is a feature-computation step and
belongs to whoever owns that (not data-ops; CLAUDE.md Sec2/Sec9).

SEASON COVERAGE. 2016-current per nflreadr docs; earlier seasons are not
published. Verified empirically for 2016 below (see ingest report).

LOOK-AHEAD / TIME KEY. No calendar as_of_date in the source. `season` is
parsed out of `nflverse_game_id` (format `SEASON_WEEK_AWAY_HOME`) and stored as
an explicit column so downstream consumers can filter on season/week without
re-parsing the id string. A downstream reader enforcing CLAUDE.md Sec6.1 must
filter on season/week directly, same as pbp/rosters_weekly/schedules.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "participation"
# No single source column is unique per play across a season on its own;
# nflverse_game_id + play_id together are (verified: no duplicates found in
# 2016 or 2023 samples).
PRIMARY_KEY = ("nflverse_game_id", "play_id")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

FIRST_AVAILABLE_SEASON = 2016


def latest_season(today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year - 1 if today.month < 9 else today.year


def all_available_seasons(today: dt.date | None = None) -> list[int]:
    return list(range(FIRST_AVAILABLE_SEASON, latest_season(today) + 1))


def fetch_participation(seasons: list[int]) -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_participation(seasons=seasons)
    # season/week are not native columns here -- parse from nflverse_game_id
    # (format "SEASON_WEEK_AWAY_HOME", e.g. "2023_01_ARI_WAS").
    df = df.with_columns(
        pl.col("nflverse_game_id").str.split("_").list.get(0).cast(pl.Int32).alias("season"),
        pl.col("nflverse_game_id").str.split("_").list.get(1).cast(pl.Int32).alias("week"),
    )
    return df.drop_nulls(list(PRIMARY_KEY))


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


def upsert_dataframe(conn: sqlite3.Connection, table: str, df: pl.DataFrame) -> int:
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
    df = fetch_participation(seasons)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(build_create_table_sql(TABLE_NAME, df, PRIMARY_KEY))
        written = upsert_dataframe(conn, TABLE_NAME, df)
        conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{TABLE_NAME}_season_week" ON "{TABLE_NAME}"(season, week)')
        conn.commit()
    finally:
        conn.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, nargs="+", default=None)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    seasons = args.seasons or all_available_seasons()

    print(f"Fetching participation for seasons: {seasons}")
    written = ingest(seasons, args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
