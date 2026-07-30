"""Ingest the ffverse `ffopportunity` prebuilt xFP model (via nflreadpy
`load_ff_opportunity`) into `data/nfl.db`.

WHY THIS EXISTS. docs/test-registry.md #18 (xFP) was costed at effort H,
"highest-value unbuilt Tier 1 item". It is not unbuilt -- ffverse ships a
versioned, prebuilt xgboost model over nflverse PBP, 2006-current, as a free
download (docs/research/analyst-factor-sweep-2026-07-30.md Sec1). This script
is that download; #18's cost is now a fetch, not a model build. No formula
work happens here (CLAUDE.md Sec2/Sec9 -- ingestion only).

MODEL VERSIONING. The source is versioned by GitHub release tag
(`{model_version}-data`); nflreadpy only exposes two literals, "latest" and
"v1.0.0". This script always calls with "latest" and records the literal
requested, NOT a resolved semantic version -- the source does not expose one
at read time. Reproducing a run later means re-running the same code on the
same day; if the upstream "latest" release changes, that is a source-side
version bump this project cannot detect from the data alone. Flagged rather
than hidden.

WEEKLY STAT TYPE ONLY. `stat_type="weekly"` is fetched (the player-week
opportunity table). `pbp_pass`/`pbp_rush` (row-per-play xFP) are a much larger
pull and have no named registry consumer yet -- left for a future ingest if
one appears.

LOOK-AHEAD / TIME KEY. `season`/`week` are native source columns (this is a
box-score-level model output, not a "current state" table) -- no invented
as_of_date needed. Downstream consumers still must respect CLAUDE.md Sec6.1:
season N inputs may only use data through season N-1 plus preseason N.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "ff_opportunity"
PRIMARY_KEY = ("player_id", "season", "week")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"
MODEL_VERSION_REQUESTED = "latest"

FIRST_AVAILABLE_SEASON = 2006


def latest_season(today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year - 1 if today.month < 9 else today.year


def all_available_seasons(today: dt.date | None = None) -> list[int]:
    return list(range(FIRST_AVAILABLE_SEASON, latest_season(today) + 1))


def fetch_ff_opportunity(seasons: list[int]) -> pl.DataFrame:
    update_config(cache_mode="filesystem")
    frames = []
    for season in seasons:
        df = nfl.load_ff_opportunity(
            seasons=season, stat_type="weekly", model_version=MODEL_VERSION_REQUESTED
        )
        frames.append(df)
    df = pl.concat(frames, how="diagonal_relaxed")
    df = df.with_columns(pl.lit(MODEL_VERSION_REQUESTED).alias("model_version_requested"))
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
    df = fetch_ff_opportunity(seasons)
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

    print(f"Fetching ff_opportunity for seasons: {seasons}")
    written = ingest(seasons, args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
