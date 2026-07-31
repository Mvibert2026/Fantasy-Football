"""Ingest player/pick trade history (via nflreadpy `load_trades`) into
`data/nfl.db`.

WHY THIS EXISTS. Named unused project-wide in
docs/research/analyst-factor-sweep-2026-07-30.md Sec1: "fetch and record what
they contain rather than deciding their value" -- no named registry consumer
today. Recorded here so a future factor design has it available without a
re-fetch.

TIME KEY. `trade_date` / `season` are native, fixed historical facts -- no
look-ahead risk. `season 2026` rows are current-offseason trades, legitimately
knowable pre-2026-season.

PRIMARY KEY. No column combination in the source is guaranteed unique: 18 of
4,975 rows are exact full-row duplicates as delivered (verified below), and
pick-only trade legs carry a null `pfr_id`. A `dupe_ordinal` column (row
number within each identical group) is added at ingest time purely to make
upsert idempotent -- it disambiguates re-runs, it is not a claim that the
source's duplicate rows represent distinct real-world trades.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "trades"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

NATURAL_COLUMNS = (
    "trade_id", "season", "trade_date", "gave", "received",
    "pick_season", "pick_round", "pick_number", "conditional", "pfr_id", "pfr_name",
)
PRIMARY_KEY = NATURAL_COLUMNS + ("dupe_ordinal",)


def fetch_trades() -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_trades()
    df = df.with_columns(
        pl.int_range(pl.len()).over(list(NATURAL_COLUMNS)).alias("dupe_ordinal")
    )
    return df


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
    df = fetch_trades()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(build_create_table_sql(TABLE_NAME, df, PRIMARY_KEY))
        written = upsert_dataframe(conn, TABLE_NAME, df)
        conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{TABLE_NAME}_season" ON "{TABLE_NAME}"(season)')
        conn.commit()
    finally:
        conn.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print("Fetching trades (full history, no season filter available)")
    written = ingest(args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
