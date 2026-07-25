"""Ingest preseason rankings into the `rankings` table in data/nfl.db.

Source is FantasyPros Expert Consensus Rankings (ECR), accessed via
nflreadpy.load_ff_rankings() -> DynastyProcess.com's public mirror of
FantasyPros' weekly rankings snapshots. This is NOT observed average draft
position from any live draft platform -- it's an aggregate of expert opinion.
Stored under source="fantasypros_ecr" so provenance stays honest; do not
relabel this "ADP" downstream.

True multi-source ADP (FFC, Yahoo, ESPN, Sleeper, Underdog) is NOT ingested
here. See docs/deferred.md for why: FFC disallows /api/ in robots.txt, and
the other four require per-site ToS review (and in Yahoo/ESPN's case, OAuth)
that hasn't been done. CLAUDE.md #10 requires checking terms before building
a scraper, not after.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl

TABLE_NAME = "rankings"
PRIMARY_KEY = ("source", "player_id", "as_of_date")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"
SOURCE = "fantasypros_ecr"
PAGE_TYPE = "redraft-overall"  # overall redraft rankings, not dynasty/weekly/positional


def _closest_snapshot_date(available_dates: list[str], target: dt.date) -> str:
    """Latest available scrape_date on or before `target` (never look forward)."""
    candidates = [d for d in available_dates if dt.date.fromisoformat(d) <= target]
    if not candidates:
        raise ValueError(f"No FantasyPros snapshot on or before {target}")
    return max(candidates)


def fetch_preseason_rankings(season: int, target_date: dt.date | None = None) -> pl.DataFrame:
    """Preseason ECR snapshot for `season`, closest available on/before target_date
    (default: end of August of `season`). Joined to gsis_id via the DynastyProcess
    player-ID crosswalk; rows nflreadpy can't resolve to a gsis_id (team DSTs,
    a handful of unrostered fringe players) are dropped -- this table is
    player-keyed, matching player_weekly_stats.
    """
    target_date = target_date or dt.date(season, 8, 31)

    all_rankings = nfl.load_ff_rankings(type="all")
    snapshots = all_rankings.filter(pl.col("page_type") == PAGE_TYPE)
    available_dates = snapshots["scrape_date"].unique().to_list()
    as_of_date = _closest_snapshot_date(available_dates, target_date)

    snap = snapshots.filter(pl.col("scrape_date") == as_of_date)

    ids = nfl.load_ff_playerids().select(["fantasypros_id", "gsis_id"])
    joined = snap.join(ids, left_on="id", right_on="fantasypros_id", how="left")
    joined = joined.filter(pl.col("gsis_id").is_not_null())

    ranked = joined.sort("ecr").with_row_index("adp_rank", offset=1)
    out = ranked.select(
        pl.lit(SOURCE).alias("source"),
        pl.col("gsis_id").alias("player_id"),
        pl.col("adp_rank").cast(pl.Int64),
        pl.col("ecr").alias("adp_value"),
        pl.lit(as_of_date).alias("as_of_date"),
        pl.col("pos").alias("position"),
    )
    return out


def build_create_table_sql() -> str:
    pk = ", ".join(f'"{c}"' for c in PRIMARY_KEY)
    return f"""
CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
    "source" TEXT NOT NULL,
    "player_id" TEXT NOT NULL,
    "adp_rank" INTEGER,
    "adp_value" REAL,
    "as_of_date" TEXT NOT NULL,
    "position" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ({pk})
)"""


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(build_create_table_sql())


def upsert_dataframe(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    if df.height == 0:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    columns = list(df.columns) + ["ingested_at"]
    placeholders = ", ".join("?" for _ in columns)
    columns_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT OR REPLACE INTO "{TABLE_NAME}" ({columns_sql}) VALUES ({placeholders})'
    rows = [tuple(row) + (ingested_at,) for row in df.iter_rows()]
    conn.executemany(sql, rows)
    return len(rows)


def ingest(season: int, db_path: Path, target_date: dt.date | None = None) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_preseason_rankings(season, target_date)
    conn = sqlite3.connect(db_path)
    try:
        ensure_table(conn)
        written = upsert_dataframe(conn, df)
        conn.commit()
    finally:
        conn.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    written = ingest(args.season, args.db)
    print(f"Wrote {written} rows into {args.db} ({TABLE_NAME}, source={SOURCE})")


if __name__ == "__main__":
    main()
