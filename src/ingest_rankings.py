"""Ingest preseason consensus rankings into the `rankings` table in data/nfl.db.

WHAT THIS IS. FantasyPros Expert Consensus Rankings (ECR), via
nflreadpy.load_ff_rankings() -> DynastyProcess.com's public mirror. This is
aggregated EXPERT OPINION, stored as ranking_source='expert'. It is NOT observed
average draft position from real drafts, and must never be relabelled "ADP"
downstream (CLAUDE.md §4: ranking sources stay separate, never blended).

WHAT IS NOT AVAILABLE (investigated 2026-07-25, Task 4):
  - nflverse:        no ADP in any of its 20 loaders (verified individually).
  - DynastyProcess:  player IDs, FP ECR, and dynasty trade values only. No ADP.
  - Fantasy Football Calculator: HAS historical ADP back to 2007, but
    robots.txt disallows /api/ and /adp/csv/. Blocked, not attempted.
  - FantasyPros ADP pages: /nfl/adp/overall.php is not in their robots.txt
    disallow list, but their Terms of Use were not affirmatively verified.
    CLAUDE.md §10 requires checking terms BEFORE building a scraper, so this
    was not built. It is the most promising remaining path if the user wants
    market ADP and is willing to review those terms.

CONSEQUENCE: ranking_source='market_adp' has no rows. The alpha track is
measured against expert consensus only. See docs/data-availability.md §5.

CONSENSUS IS NEVER A MODEL INPUT. It is the yardstick for the alpha track.

SCORING FORMAT (investigated 2026-07-26, handoff 018): this league is half-PPR, and the
DynastyProcess mirror's "redraft-overall" page has no PPR variant at all (only full-PPR
position pages like ppr-rb.php, and non-PPR/standard "redraft-*"). Switching to FantasyPros'
live API (api.fantasypros.com, `type=ST&scoring=HALF`) *would* fix the scoring mismatch, but
its free tier caps every response at 10 players regardless of position filter or offset/page
params (re-confirmed live: RB call reported count=209, returned 10 rows) -- per
docs/deferred.md's prior probe. Four position-filtered calls would yield ~40 players/season,
down from ~500 via the current mirror. That is not a usable substitute for backtest coverage
(RB30/WR40 replacement-level cutoffs alone exceed a single position's 10-row cap), so this
ingestion deliberately stays on the DynastyProcess mirror and stays unscored-format as a
result. The scoring mismatch is real and not fixed by this file; it needs either paid
FantasyPros API tier (see docs/CURRENT-STATE.md open item 4) or a different half-PPR-native
source. Do not "fix" this by pointing at the live API without addressing the row cap first.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

TABLE_NAME = "rankings"
PRIMARY_KEY = ("source", "season", "player_id", "as_of_date")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

SOURCE = "fantasypros_ecr"
RANKING_SOURCE = "expert"  # CLAUDE.md §4 enum: proprietary|expert|league_adp|market_adp
PAGE_TYPE = "redraft-overall"

# A preseason board is the last one published before Week 1.
PRESEASON_CUTOFF_MONTH_DAY = (8, 31)
# Snapshots before this month in the season's calendar year belong to the prior
# season's cycle, not this one -- without this bound, a season with no snapshot
# yet would silently inherit last season's board.
SEASON_WINDOW_START_MONTH = 3

_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
    ranking_source TEXT NOT NULL,
    source TEXT NOT NULL,
    season INTEGER NOT NULL,
    player_id TEXT NOT NULL,
    player_name TEXT,
    team TEXT,
    adp_rank INTEGER,
    adp_value REAL,
    -- Cross-source dispersion. NEVER collapse these away: VONA at pick 18
    -- needs P(player survives to pick 23), which requires a distribution over
    -- where the room might take him, not a consensus point estimate. Once
    -- ingestion discards spread it is permanently unrecoverable for that date.
    spread_sd REAL,
    rank_best REAL,
    rank_worst REAL,
    as_of_date TEXT NOT NULL,
    position TEXT,
    is_preseason_final INTEGER NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY ({", ".join(f'"{c}"' for c in PRIMARY_KEY)})
)
"""


def available_snapshot_dates(all_rankings: pl.DataFrame) -> list[str]:
    return sorted(
        all_rankings.filter(pl.col("page_type") == PAGE_TYPE)["scrape_date"].unique().to_list()
    )


def resolve_snapshot_date(dates: list[str], season: int) -> tuple[str, bool]:
    """Latest snapshot within `season`'s cycle and on/before Aug 31 of it.

    Returns (as_of_date, is_preseason_final). `is_preseason_final` is False when
    the chosen snapshot predates the Aug 31 cutoff because the season hasn't
    reached it yet -- i.e. an in-progress board that will move before the draft.
    """
    lower = dt.date(season, SEASON_WINDOW_START_MONTH, 1)
    upper = dt.date(season, *PRESEASON_CUTOFF_MONTH_DAY)
    in_window = [d for d in dates if lower <= dt.date.fromisoformat(d) <= upper]
    if not in_window:
        raise ValueError(
            f"No {PAGE_TYPE} snapshot for season {season} between {lower} and {upper}"
        )
    chosen = max(in_window)
    # If today is before the cutoff, this board is still moving.
    is_final = dt.date.today() > upper
    return chosen, is_final


def fetch_preseason_rankings(season: int) -> tuple[pl.DataFrame, str, bool]:
    """Preseason ECR for `season`, joined to gsis_id.

    Rows nflreadpy cannot resolve to a gsis_id are dropped, this table is
    player-keyed to match player_weekly_stats. Two distinct populations fall
    into that bucket, and thread 023 asked that the drop be a deliberate
    decision, not an incidental join side effect:

    - Team DSTs ("DST" position rows) have no gsis_id by construction --
      nflverse's player-id crosswalk is individual-player-only, and this
      league's `league.json` declares no DEF replacement level and never
      will without ingested DST scoring (CURRENT-STATE.md). Retaining these
      rows through the identity hub would mean carrying player_id=NULL rows
      that nothing downstream can ever join to a stat line -- permanent,
      unresolvable dead weight, not a gap that a future ingest closes. They
      are discarded permanently and on purpose.
    - Fringe/unrostered individual players occasionally fail the crosswalk
      too (a real gap, not a structural one -- a future nflverse ID release
      could resolve them). Those are also dropped here today because this
      function has no quarantine sink to hold them in, but that is the
      cheaper, still-imperfect half of the same line; DST is the
      permanent, by-design half.
    """
    update_config(cache_mode="filesystem")
    all_rankings = nfl.load_ff_rankings(type="all")
    dates = available_snapshot_dates(all_rankings)
    as_of_date, is_final = resolve_snapshot_date(dates, season)

    snap = all_rankings.filter(
        (pl.col("page_type") == PAGE_TYPE) & (pl.col("scrape_date") == as_of_date)
    )
    # Cast both join keys to Utf8 before joining. These are identifiers, not
    # numbers, and upstream is inconsistent about it: `id` arrives as str while
    # `fantasypros_id` arrives as i64. Older polars silently coerced; 1.43
    # raises SchemaError ("datatypes of join keys don't match"), which broke the
    # database rebuild at step 4/9 on a clean machine (GitHub Actions run 1,
    # 2026-08-07) while working fine on the dev box's pinned polars.
    #
    # Casting to string rather than to int is deliberate: an int cast would
    # null out any non-numeric id and silently drop a real player. Verified
    # 2026-08-07 against the live feed -- of 4,930 unique ranking ids, ZERO
    # have a leading zero and ZERO are non-numeric, so int -> str is lossless
    # here. If upstream ever breaks that, the mismatch surfaces in the
    # unresolved-rows count printed below rather than passing silently.
    ids = nfl.load_ff_playerids().select(["fantasypros_id", "gsis_id"]).with_columns(
        pl.col("fantasypros_id").cast(pl.Utf8)
    )
    joined = snap.with_columns(pl.col("id").cast(pl.Utf8)).join(
        ids, left_on="id", right_on="fantasypros_id", how="left"
    )

    unresolved = joined.filter(pl.col("gsis_id").is_null())
    n_dst = unresolved.filter(pl.col("pos") == "DST").height
    n_other = unresolved.height - n_dst
    if unresolved.height:
        print(
            f"  {season}: dropping {unresolved.height} unresolved rows "
            f"({n_dst} DST -- permanent, by design; {n_other} non-DST -- "
            "crosswalk gap)"
        )
    joined = joined.filter(pl.col("gsis_id").is_not_null())

    ranked = joined.sort("ecr").with_row_index("adp_rank", offset=1)
    out = ranked.select(
        pl.lit(RANKING_SOURCE).alias("ranking_source"),
        pl.lit(SOURCE).alias("source"),
        pl.lit(season).cast(pl.Int64).alias("season"),
        pl.col("gsis_id").alias("player_id"),
        pl.col("player").alias("player_name"),
        pl.col("team").alias("team"),
        pl.col("adp_rank").cast(pl.Int64),
        pl.col("ecr").alias("adp_value"),
        pl.col("sd").alias("spread_sd"),
        pl.col("best").alias("rank_best"),
        pl.col("worst").alias("rank_worst"),
        pl.lit(as_of_date).alias("as_of_date"),
        pl.col("pos").alias("position"),
        pl.lit(1 if is_final else 0).cast(pl.Int64).alias("is_preseason_final"),
    )
    return out, as_of_date, is_final


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_SQL)
    existing = {r[1] for r in conn.execute(f'PRAGMA table_info("{TABLE_NAME}")')}
    if not {"ranking_source", "player_name", "team", "spread_sd", "rank_best", "rank_worst"} <= existing:
        # Legacy table from an earlier schema -- rebuild rather than migrate;
        # every row is re-derivable from the source.
        conn.execute(f'DROP TABLE "{TABLE_NAME}"')
        conn.execute(_CREATE_SQL)


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


def ingest(seasons: list[int], db_path: Path) -> dict[int, tuple[int, str, bool]]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    results: dict[int, tuple[int, str, bool]] = {}
    try:
        ensure_table(conn)
        for season in seasons:
            try:
                df, as_of, is_final = fetch_preseason_rankings(season)
            except ValueError as e:
                print(f"  {season}: SKIPPED -- {e}")
                continue
            n = upsert_dataframe(conn, df)
            results[season] = (n, as_of, is_final)
            flag = "" if is_final else "  [IN-PROGRESS: board will move before Week 1]"
            print(f"  {season}: {n} rows, as_of={as_of}{flag}")
        conn.commit()
    finally:
        conn.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", type=int, nargs="+", default=list(range(2021, 2027)))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print(f"Ingesting {SOURCE} (ranking_source={RANKING_SOURCE}) for {args.seasons}")
    results = ingest(args.seasons, args.db)
    print(f"Done: {sum(v[0] for v in results.values())} rows across {len(results)} seasons")


if __name__ == "__main__":
    main()
