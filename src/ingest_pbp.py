"""Ingest nflverse play-by-play (via nflreadpy) into `data/nfl.db`, slimmed to the
24 columns needed for red-zone/goal-line, xFP, team pace, and PROE (test-registry
#10, #18, #21, #22 -- see docs/handoffs/2026-07-30-five-datasets-30-seconds-total-all-measured-toda.md).

Ingestion-only. No feature computation here -- red-zone rates, xFP, pace, and PROE
are derived elsewhere, by whoever owns that step (not data-ops; CLAUDE.md Sec9/Sec2).

WHY SLIMMED. The full frame is 372 columns. The 24 selected here cover every input
those four factors need and were confirmed present column-by-column before this
script was written. Slimming keeps the cached parquet at ~15 MB instead of several
hundred, with no loss to the columns actually consumed downstream.

WHY NOT EARLIER THAN 2009. Usage analytics (target share, snap share, air yards,
PROE) are only reliable from 2009 onward per `experiments/bottomup/data.py`; pre-
2009 PBP would add rows supporting only a weak feature set. If a future consumer
needs 1999-2008, that is a new decision, not an oversight here.

LOOK-AHEAD. Every row carries `season`/`week`, which is the granularity this table
supports (there is no finer per-play timestamp in the source). A downstream reader
enforcing CLAUDE.md Sec6.1 must filter on season/week directly -- there is no
as_of_date column to enforce it structurally at ingest time, and inventing one
would manufacture precision the source does not have.

PLAYER ID SPACE. `rusher_player_id` / `receiver_player_id` / `passer_player_id`
are already gsis ids, matching `player_weekly_stats.player_id` -- verified: no
crosswalk needed to join.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "pbp"
PRIMARY_KEY = ("game_id", "play_id")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

FIRST_AVAILABLE_SEASON = 2009  # see module docstring

COLUMNS = [
    "season", "week", "posteam", "defteam", "play_id", "game_id", "down",
    "yardline_100", "goal_to_go", "pass", "rush", "pass_attempt", "rush_attempt",
    "complete_pass", "touchdown", "yards_gained", "air_yards",
    "rusher_player_id", "receiver_player_id", "passer_player_id",
    "xpass", "wp", "half_seconds_remaining", "score_differential",
]


def latest_season(today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year - 1 if today.month < 9 else today.year


def all_available_seasons(today: dt.date | None = None) -> list[int]:
    return list(range(FIRST_AVAILABLE_SEASON, latest_season(today) + 1))


def fetch_pbp(seasons: list[int]) -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_pbp(seasons=seasons)
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"pbp: expected columns absent from source: {missing}")
    sub = df.select(COLUMNS)
    # play_id/game_id form the natural key; a null in either is not a real play
    # (verified empirically: none in 2009-2025, but don't assume it holds forever).
    return sub.drop_nulls(list(PRIMARY_KEY))


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
    df = fetch_pbp(seasons)
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

    print(f"Fetching play-by-play for seasons: {seasons}")
    written = ingest(seasons, args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
