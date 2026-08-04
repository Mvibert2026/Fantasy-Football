"""Ingest Vegas odds into the `odds_snapshots` table in data/nfl.db.

WHAT THIS IS. Pregame game-level betting lines (spread, total, moneyline) via
nflreadpy.load_schedules() -> nflverse-data's own schedules release, which
already carries `spread_line`/`total_line`/`{home,away}_moneyline` columns.
This is the nflverse dataset already used everywhere else in this project
(CC-BY, no separate licensing question), NOT a new scrape.

Coverage verified 2026-08-01: `spread_line`/`total_line`/`{away,home}_moneyline`
are populated with ZERO nulls for every REG-season game 2018-2024 (the window
CLAUDE.md's factor-testing needs). Data goes back further (nflverse's own
history), but this project's stated need is 2018-2024, so that's the default.

CONVENTION (verified against 2024 week 1: home_moneyline is negative --
favored -- everywhere spread_line is positive in the same row):
  spread_line > 0  =>  HOME team favored by that many points.
  spread_line < 0  =>  AWAY team favored.
Team-level `team_spread` below is normalized to "this team's own spread"
(negative = this team favored), matching the sign convention bettors use for
a team's own line, not the schedule table's home-relative one.

WHAT THIS IS NOT (unavailable, not fabricated):
  - Player props (passing/rushing/receiving yards, TDs): not in nflverse and
    no free public source with historical (2018-2024) coverage was found in
    this session's budget. NOT ingested.
  - Season win totals (preseason, one line per team per year): not in
    nflverse. A public archive (sportsoddshistory.com) exists but its win-
    totals page is JS/graph-rendered, not a static table reachable with the
    time budget this session had -- and CLAUDE.md/the FR explicitly rank this
    the WEAKEST of the four instruments, so it was deprioritized rather than
    forced. NOT ingested. Left as a clearly-scoped follow-up, not silently
    dropped: see docs/deferred.md.

AS_OF_DATE. This table stores one row per team per game. `as_of_date` is set
to `gameday` itself (the date of kickoff) -- NOT the true line-setting date,
which nflverse does not expose and which is typically a few days earlier.
Using gameday is a deliberately CONSERVATIVE choice: it understates how early
this information was actually public (real bettors had it days sooner), so it
can never create look-ahead into the game's own result -- the line is fixed
well before kickoff regardless of final score. A future ingest with a real
line-movement/opening-line feed could tighten `as_of_date` further; this one
does not claim precision it doesn't have.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl

TABLE_NAME = "odds_snapshots"
PRIMARY_KEY = ("source", "season", "game_id", "team")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

SOURCE = "nflverse_schedules"

_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
    source TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER,
    game_type TEXT,
    game_id TEXT NOT NULL,
    gameday TEXT,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    is_home INTEGER NOT NULL,
    team_spread REAL,          -- this team's own line; negative = favored
    game_total_line REAL,
    implied_team_total REAL,
    moneyline INTEGER,
    as_of_date TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY ({", ".join(f'"{c}"' for c in PRIMARY_KEY)})
)
"""


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_SQL)


def fetch_odds(seasons: list[int]) -> pl.DataFrame:
    sched = nfl.load_schedules()
    sub = sched.filter(pl.col("season").is_in(seasons))

    # One row per game -> two rows per game (home perspective, away perspective).
    home = sub.select(
        pl.lit(SOURCE).alias("source"),
        pl.col("season"),
        pl.col("week"),
        pl.col("game_type"),
        pl.col("game_id"),
        pl.col("gameday"),
        pl.col("home_team").alias("team"),
        pl.col("away_team").alias("opponent"),
        pl.lit(1).alias("is_home"),
        (-pl.col("spread_line")).alias("team_spread"),
        pl.col("total_line").alias("game_total_line"),
        (pl.col("total_line") / 2 + pl.col("spread_line") / 2).alias("implied_team_total"),
        pl.col("home_moneyline").alias("moneyline"),
    )
    away = sub.select(
        pl.lit(SOURCE).alias("source"),
        pl.col("season"),
        pl.col("week"),
        pl.col("game_type"),
        pl.col("game_id"),
        pl.col("gameday"),
        pl.col("away_team").alias("team"),
        pl.col("home_team").alias("opponent"),
        pl.lit(0).alias("is_home"),
        pl.col("spread_line").alias("team_spread"),
        pl.col("total_line").alias("game_total_line"),
        (pl.col("total_line") / 2 - pl.col("spread_line") / 2).alias("implied_team_total"),
        pl.col("away_moneyline").alias("moneyline"),
    )
    out = pl.concat([home, away])
    # Drop games with no line at all (bye-adjacent/placeholder rows, if any).
    out = out.filter(pl.col("game_total_line").is_not_null() & pl.col("team_spread").is_not_null())
    out = out.with_columns(pl.col("gameday").alias("as_of_date"))
    return out


def upsert_dataframe(conn: sqlite3.Connection, df: pl.DataFrame) -> int:
    if df.height == 0:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    columns = list(df.columns) + ["ingested_at"]
    placeholders = ", ".join("?" for _ in columns)
    sql = (
        f'INSERT OR REPLACE INTO "{TABLE_NAME}" ({", ".join(columns)}) '
        f"VALUES ({placeholders})"
    )
    conn.executemany(sql, [tuple(r) + (ingested_at,) for r in df.iter_rows()])
    return df.height


def ingest(seasons: list[int], db_path: Path) -> dict[int, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    results: dict[int, int] = {}
    try:
        ensure_table(conn)
        df = fetch_odds(seasons)
        for season in seasons:
            sub = df.filter(pl.col("season") == season)
            n = upsert_dataframe(conn, sub)
            results[season] = n
            print(f"  {season}: {n} team-game rows")
        conn.commit()
    finally:
        conn.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, nargs="+", default=list(range(2018, 2025)))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print(f"Ingesting {SOURCE} odds for seasons {args.seasons}")
    results = ingest(args.seasons, args.db)
    print(f"Done: {sum(results.values())} rows across {len(results)} seasons")


if __name__ == "__main__":
    main()
