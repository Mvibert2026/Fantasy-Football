"""Compute and cache LEAGUE-LEVEL season metrics for regime analysis (Task 3).

These are aggregate, league-wide descriptive series (pass rate, plays/game,
positional scoring shares, usage concentration) across the full 1999-2025
window. Per docs/CLAUDE.md this is the one place the long window genuinely
pays off -- player-level factor models remain bounded by each feature's own
availability (docs/data-availability.md).

Look-ahead note: these series are descriptive league history, not player-level
ranking inputs. If a regime indicator is ever fed into a model predicting
season N, the caller must use only regimes derived from seasons < N. This
module does not enforce that, because it is not a ranking-input path; the
enforcement lives in db.CutoffEnforcedStore for anything that is.

Metrics derived from `targets` are set to NULL for 2003-2008, where receiver
attribution is broken (docs/data-availability.md §0). They are not zero-filled.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

import db as dbmod
from scoring import score_offensive_game

TABLE_NAME = "league_season_metrics"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

# Seasons where receiver attribution in PBP is unreliable; target-derived
# metrics are NULL here rather than zero. See docs/data-availability.md.
TARGET_BROKEN_SEASONS = set(range(2003, 2009))

_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
    season INTEGER PRIMARY KEY,
    games INTEGER,
    plays INTEGER,
    pass_plays INTEGER,
    rush_plays INTEGER,
    pass_rate REAL,
    neutral_pass_rate REAL,
    plays_per_game REAL,
    points_per_team_game REAL,
    qb_point_share REAL,
    rb_point_share REAL,
    wr_point_share REAL,
    te_point_share REAL,
    rb_carry_top30_share REAL,
    wr_target_top45_share REAL,
    ingested_at TEXT NOT NULL
)
"""


def pbp_season_metrics(season: int) -> dict:
    """Pass rate, play volume and neutral-script pass rate from play-by-play."""
    pbp = nfl.load_pbp(seasons=[season])
    scrimmage = pbp.filter(
        (pl.col("play_type").is_in(["pass", "run"]))
        & (pl.col("season_type") == "REG")
    )
    n_pass = scrimmage.filter(pl.col("play_type") == "pass").height
    n_rush = scrimmage.filter(pl.col("play_type") == "run").height
    plays = n_pass + n_rush
    games = scrimmage["game_id"].n_unique()

    # Neutral script: early downs, competitive win probability, before the
    # 4th quarter -- strips garbage-time pass inflation that would otherwise
    # masquerade as a scheme trend.
    neutral = scrimmage.filter(
        (pl.col("down").is_in([1, 2]))
        & (pl.col("qtr") <= 3)
        & (pl.col("wp") >= 0.2)
        & (pl.col("wp") <= 0.8)
    )
    n_neutral = neutral.height
    neutral_pass = neutral.filter(pl.col("play_type") == "pass").height

    return {
        "season": season,
        "games": games,
        "plays": plays,
        "pass_plays": n_pass,
        "rush_plays": n_rush,
        "pass_rate": (n_pass / plays) if plays else None,
        "neutral_pass_rate": (neutral_pass / n_neutral) if n_neutral else None,
        "plays_per_game": (plays / games) if games else None,
    }


def schedule_points(season: int) -> float | None:
    sched = nfl.load_schedules(seasons=[season])
    reg = sched.filter(pl.col("game_type") == "REG").drop_nulls(["home_score", "away_score"])
    if reg.height == 0:
        return None
    total = reg["home_score"].sum() + reg["away_score"].sum()
    return total / (2 * reg.height)


def player_stats_season_metrics(conn: sqlite3.Connection, season: int) -> dict:
    """Positional fantasy-point shares and usage concentration, scored under
    THIS league's rules (so the shares reflect our bonuses and negatives)."""
    rows = list(dbmod.actual_season_outcomes(conn, season))

    totals: dict[str, float] = {}
    carries: dict[str, int] = {}
    targets: dict[str, int] = {}
    positions: dict[str, str] = {}
    for r in rows:
        pid = r["player_id"]
        stats = {c: r[c] for c in dbmod.SCORING_STAT_COLUMNS}
        totals[pid] = totals.get(pid, 0.0) + score_offensive_game(stats)
        positions[pid] = r["position"]

    # carries/targets come from the raw table (not in the scoring view)
    cur = conn.execute(
        "SELECT player_id, position, SUM(COALESCE(carries,0)) AS c, "
        "SUM(COALESCE(targets,0)) AS t FROM player_weekly_stats "
        "WHERE season = ? AND season_type = 'REG' GROUP BY player_id, position",
        (season,),
    )
    for pid, pos, c, t in cur.fetchall():
        carries[pid] = c
        targets[pid] = t
        positions.setdefault(pid, pos)

    def point_share(pos: str) -> float | None:
        grand = sum(v for v in totals.values())
        if not grand:
            return None
        pos_total = sum(v for p, v in totals.items() if positions.get(p) == pos)
        return pos_total / grand

    def top_n_share(counts: dict[str, int], pos: str, n: int) -> float | None:
        vals = sorted((v for p, v in counts.items() if positions.get(p) == pos), reverse=True)
        total = sum(vals)
        if not total:
            return None
        return sum(vals[:n]) / total

    return {
        "qb_point_share": point_share("QB"),
        "rb_point_share": point_share("RB"),
        "wr_point_share": point_share("WR"),
        "te_point_share": point_share("TE"),
        "rb_carry_top30_share": top_n_share(carries, "RB", 30),
        # NULL rather than a fabricated 0.0 where receiver attribution is broken
        "wr_target_top45_share": (
            None if season in TARGET_BROKEN_SEASONS else top_n_share(targets, "WR", 45)
        ),
    }


def build_season_row(conn: sqlite3.Connection, season: int) -> dict:
    row = pbp_season_metrics(season)
    row["points_per_team_game"] = schedule_points(season)
    row.update(player_stats_season_metrics(conn, season))
    return row


def upsert(conn: sqlite3.Connection, rows: list[dict]) -> int:
    conn.execute(_CREATE_SQL)
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cols = [
        "season", "games", "plays", "pass_plays", "rush_plays", "pass_rate",
        "neutral_pass_rate", "plays_per_game", "points_per_team_game",
        "qb_point_share", "rb_point_share", "wr_point_share", "te_point_share",
        "rb_carry_top30_share", "wr_target_top45_share",
    ]
    placeholders = ", ".join("?" for _ in cols + ["ingested_at"])
    sql = (
        f'INSERT OR REPLACE INTO "{TABLE_NAME}" '
        f'({", ".join(cols)}, ingested_at) VALUES ({placeholders})'
    )
    conn.executemany(sql, [tuple(r.get(c) for c in cols) + (ingested_at,) for r in rows])
    conn.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--first", type=int, default=1999)
    parser.add_argument("--last", type=int, default=2025)
    args = parser.parse_args()

    update_config(cache_mode="filesystem")
    conn = dbmod.connect(args.db)
    rows = []
    try:
        for season in range(args.first, args.last + 1):
            row = build_season_row(conn, season)
            rows.append(row)
            print(
                f"{season}: plays={row['plays']} pass_rate={row['pass_rate']:.4f} "
                f"neutral={row['neutral_pass_rate']:.4f} ppg={row['plays_per_game']:.1f}",
                flush=True,
            )
        n = upsert(conn, rows)
    finally:
        conn.close()
    print(f"Wrote {n} league-season rows into {args.db} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
