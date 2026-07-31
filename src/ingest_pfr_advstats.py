"""Ingest Pro Football Reference advanced stats (via nflreadpy
`load_pfr_advstats`) into `data/nfl.db`.

WHY THIS EXISTS. docs/test-registry.md #23 (O-line) is tagged `external`,
implying a PFR scrape (previously 403-blocked here, per docs/environment.md).
This loader ships the same PFR advanced-stat tables (yards-before-contact,
broken tackles, drops, pressure/hurry/blitz counts) as a free nflverse mirror
-- no scrape, no 403 (docs/research/analyst-factor-sweep-2026-07-30.md Sec1).

FOUR STAT TYPES, ONE TABLE EACH. `pass`/`rush`/`rec`/`def` have different,
non-overlapping column sets, so each is written to its own table
(`pfr_advstats_pass`, `pfr_advstats_rush`, `pfr_advstats_rec`,
`pfr_advstats_def`) rather than force-unioned into one wide table.

SEASON COVERAGE. 2018-current only (source limitation, stated in nflreadpy's
own docstring). Verified empirically below.

LOOK-AHEAD / TIME KEY. `season`/`week`/`game_id` are native columns -- a
box-score-level stat, not a "current state" table. No invented as_of_date
needed. Downstream consumers still must respect CLAUDE.md Sec6.1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

STAT_TYPES = ("pass", "rush", "rec", "def")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

FIRST_AVAILABLE_SEASON = 2018


def latest_season(today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year - 1 if today.month < 9 else today.year


def all_available_seasons(today: dt.date | None = None) -> list[int]:
    return list(range(FIRST_AVAILABLE_SEASON, latest_season(today) + 1))


def table_name(stat_type: str) -> str:
    return f"pfr_advstats_{stat_type}"


def primary_key(df: pl.DataFrame) -> tuple[str, ...]:
    # game_id + pfr_player_id is unique per row for every stat_type observed
    # (verified: pass/rush/rec/def all carry both, 2018-2025 samples).
    return ("game_id", "pfr_player_id")


def fetch_pfr_advstats(stat_type: str, seasons: list[int]) -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_pfr_advstats(seasons=seasons, stat_type=stat_type, summary_level="week")
    return df.drop_nulls(list(primary_key(df)))


def _polars_dtype_to_sqlite(dtype: pl.DataType) -> str:
    if dtype.is_integer() or dtype == pl.Boolean:
        return "INTEGER"
    if dtype.is_float():
        return "REAL"
    return "TEXT"


def build_create_table_sql(table: str, df: pl.DataFrame, pk: tuple[str, ...]) -> str:
    columns = [f'"{name}" {_polars_dtype_to_sqlite(dtype)}' for name, dtype in zip(df.columns, df.dtypes)]
    columns.append('"ingested_at" TEXT NOT NULL')
    pk_sql = ", ".join(f'"{c}"' for c in pk)
    columns_sql = ",\n    ".join(columns)
    return f'CREATE TABLE IF NOT EXISTS "{table}" (\n    {columns_sql},\n    PRIMARY KEY ({pk_sql})\n)'


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


def ingest(seasons: list[int], db_path: Path) -> dict[str, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    written = {}
    try:
        for stat_type in STAT_TYPES:
            df = fetch_pfr_advstats(stat_type, seasons)
            table = table_name(stat_type)
            pk = primary_key(df)
            conn.execute(build_create_table_sql(table, df, pk))
            n = upsert_dataframe(conn, table, df)
            conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table}_season_week" ON "{table}"(season, week)')
            written[stat_type] = n
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

    print(f"Fetching pfr_advstats for seasons: {seasons}")
    written = ingest(seasons, args.db)
    for stat_type, n in written.items():
        print(f"Wrote {n} rows into {args.db} ({table_name(stat_type)})")


if __name__ == "__main__":
    main()
