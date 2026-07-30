"""Ingest NFL Scouting Combine results (via nflreadpy `load_combine`) into
`data/nfl.db`.

WHY THIS EXISTS. Named unused project-wide in
docs/research/analyst-factor-sweep-2026-07-30.md Sec1/N34: athletic-testing
inputs for Speed Score / Burst / Agility (registry N34).

ENTER WITH NO PRIOR. PlayerProfiler publishes the Speed Score / Burst /
Agility formulas, but the researcher's sweep found **no published predictive
evidence** for them (Sec2e, N34: "[VERIFIED] formulas; [GAP] predictiveness").
Ingesting the raw testing numbers here is not an endorsement that they belong
in the ranking model -- that is a Statistician-owned test, not a data-ops
decision (CLAUDE.md Sec9).

TIME KEY. `season` here is draft class year (the year a player was drafted /
tested), a genuine historical fact fixed at testing time -- no look-ahead
risk of the "current snapshot" kind. Source returns through the upcoming
draft class (season 2026 present in this pull, ahead of the 2026 season
itself starting) -- that is expected: combine testing happens in the spring
before the season, and pre-draft testing data for players not yet drafted is
legitimately part of what would have been knowable pre-season.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "combine"
# pfr_id is null for some undrafted/untracked invitees; season + player_name +
# school is unique across the full pull (verified: no duplicate triples).
PRIMARY_KEY = ("season", "player_name", "school")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"


def fetch_combine() -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    df = nfl.load_combine(seasons=True)
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
    df = fetch_combine()
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

    print("Fetching combine (all seasons, 2000-current draft class)")
    written = ingest(args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
