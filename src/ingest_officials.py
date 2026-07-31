"""Ingest game officials (via nflreadpy `load_officials`) into `data/nfl.db`.

WHY THIS EXISTS. Named unused project-wide in
docs/research/analyst-factor-sweep-2026-07-30.md Sec1: "fetch and record what
they contain rather than deciding their value" -- no named registry consumer
today.

TIME KEY. `season`/`week`/`game_id` are native, fixed historical facts (an
official's assignment to a specific game) -- no look-ahead risk.

COVERAGE. 2015-current per this pull (verified below); nflreadpy's `seasons`
argument here defaults to loading everything available (`True`).
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "officials"
PRIMARY_KEY = ("game_id", "official_id", "position")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"


def fetch_officials() -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_officials(seasons=True)
    return df.drop_nulls(list(PRIMARY_KEY))


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


def ingest(db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_officials()
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
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print("Fetching officials (full history, no season filter available)")
    written = ingest(args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
