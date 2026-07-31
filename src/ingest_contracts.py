"""Ingest OverTheCap contract data (via nflreadpy `load_contracts`) into
`data/nfl.db`.

WHY THIS EXISTS. docs/test-registry.md #27 (contract year) names
`nflverse (contracts)` as its source; this is that loader.

**THIS TABLE IS A PRESENT-DAY SNAPSHOT, NOT A TIME SERIES -- READ THIS BEFORE
USING IT FOR ANY HISTORICAL SEASON.** `load_contracts()` returns OverTheCap's
current view of every contract on record; there is no `season`/`as_of_date`
column and no per-fetch history. Two columns are a live trap:
  - `is_active` reflects contract status **as of the fetch date** (this
    ingest's `ingested_at`), not as of any historical season. A contract that
    was active in 2019 but has since expired reads `is_active=false` today.
    Using this column to ask "was this player under contract in season N" for
    any N before the fetch date is exactly the Wikipedia-navbox trap named in
    this task: it silently imports present-day status into historical rows.
  - `year_signed` + `years` can reconstruct a contract's nominal span
    (`year_signed` through `year_signed + years - 1`), which *is* a
    historically defensible time key -- but that reconstruction is a
    downstream computation, not done here (CLAUDE.md Sec2/Sec9: ingestion
    only). A consumer must compute it, not assume `is_active` answers it.

DATA QUALITY, STATED NOT FIXED. `year_signed` contains at least one row with
value `0` (verified: min=0 across 51,772 rows, source data as delivered).
Left as-is -- not fabricated, not silently dropped. A consumer filtering on
`year_signed` should treat `0` as a sentinel for "unknown," not year 1 CE.

NO SEASON PARAMETER. The source loader takes no `seasons` argument; it always
returns its full, current table. `--seasons` is accepted here for CLI
consistency with sibling scripts but is unused.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "contracts"
# player + otc_id + year_signed is unique per row (verified: no duplicates in
# the 51,772-row pull). gsis_id is frequently null (unmatched player), so it
# cannot anchor the key.
PRIMARY_KEY = ("otc_id", "year_signed", "player")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"


def fetch_contracts() -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_contracts()
    # `cols` is a source-internal metadata column (list of column names used
    # during their own build), not player data -- drop it, it can't cast to
    # a SQLite column type cleanly and carries nothing useful downstream.
    if "cols" in df.columns:
        df = df.drop("cols")
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
    df = fetch_contracts()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(build_create_table_sql(TABLE_NAME, df, PRIMARY_KEY))
        written = upsert_dataframe(conn, TABLE_NAME, df)
        conn.commit()
    finally:
        conn.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, nargs="+", default=None, help="Unused; kept for CLI parity.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print("Fetching contracts (full current snapshot, no season filter available)")
    written = ingest(args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
