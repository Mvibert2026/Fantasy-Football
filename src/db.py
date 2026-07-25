"""
Data access layer for data/nfl.db.

Two access paths, intentionally kept separate so the separation is visible in
the code rather than relying on caller discipline:

- `CutoffEnforcedStore.player_week_rows(...)` — the only path ranking-input
  code should ever use. Structurally refuses any row from `season >=
  cutoff_season` (see docs/CLAUDE.md #6.1: ranking inputs for season N may use
  data through end of season N-1 and preseason N only).
- `actual_season_outcomes(...)` — the evaluation-only path. Reads the target
  season itself. Only the backtest harness's scoring step should call this.

`player_week_scoring_inputs` is a SQL view over the raw `player_weekly_stats`
cache (built by ingest_weekly_stats.py), reshaped to the column names
scoring.score_offensive_game() expects. It's a view, not a second copy, so it
can't drift out of sync with the raw cache (see docs/deferred.md).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

SCORING_VIEW = "player_week_scoring_inputs"
LEAGUE_METRICS_TABLE = "league_season_metrics"

_CREATE_SCORING_VIEW_SQL = f"""
CREATE VIEW IF NOT EXISTS {SCORING_VIEW} AS
SELECT
    player_id,
    player_name,
    position,
    team,
    season,
    season_type,
    week,
    passing_yards,
    passing_tds,
    passing_interceptions AS interceptions,
    rushing_yards,
    rushing_tds,
    receptions,
    receiving_yards,
    receiving_tds,
    fumbles_lost_total AS fumbles_lost,
    special_teams_tds AS return_tds,
    (COALESCE(passing_2pt_conversions, 0)
        + COALESCE(rushing_2pt_conversions, 0)
        + COALESCE(receiving_2pt_conversions, 0)) AS two_point_conversions,
    COALESCE(fumble_recovery_tds, 0) AS offensive_fumble_return_tds
FROM player_weekly_stats
"""

# Columns from the view that map directly onto scoring.score_offensive_game()'s
# expected stats dict keys.
SCORING_STAT_COLUMNS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "fumbles_lost",
    "return_tds",
    "two_point_conversions",
    "offensive_fumble_return_tds",
)


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_SCORING_VIEW_SQL)
    return conn


class LookAheadViolation(Exception):
    """Raised when ranking-input code asks for data at or after the cutoff."""


class CutoffEnforcedStore:
    """Ranking-input access, structurally barred from seeing cutoff_season+."""

    def __init__(self, conn: sqlite3.Connection, cutoff_season: int):
        self.conn = conn
        self.cutoff_season = cutoff_season

    def player_week_rows(
        self, seasons: list[int] | None = None, season_type: str = "REG"
    ) -> Iterator[sqlite3.Row]:
        """Historical rows strictly before cutoff_season. Refuses otherwise.

        `seasons`, if given, must all be < cutoff_season. Omit it to fetch all
        available history before the cutoff.
        """
        if seasons is not None:
            bad = [s for s in seasons if s >= self.cutoff_season]
            if bad:
                raise LookAheadViolation(
                    f"Requested season(s) {bad} are at or after cutoff_season="
                    f"{self.cutoff_season}; ranking inputs may only use data "
                    f"through the end of the prior season."
                )
            season_filter = f"AND season IN ({','.join('?' * len(seasons))})"
            params = list(seasons)
        else:
            season_filter = "AND season < ?"
            params = [self.cutoff_season]

        sql = (
            f"SELECT * FROM {SCORING_VIEW} WHERE season_type = ? {season_filter} "
            "ORDER BY season, week"
        )
        cur = self.conn.execute(sql, [season_type] + params)
        yield from cur


def actual_season_outcomes(
    conn: sqlite3.Connection, season: int, season_type: str = "REG"
) -> Iterator[sqlite3.Row]:
    """Evaluation-only: the target season's real results. Not look-ahead-safe
    by design — only the harness's scoring step may call this."""
    sql = f"SELECT * FROM {SCORING_VIEW} WHERE season = ? AND season_type = ? ORDER BY week"
    yield from conn.execute(sql, (season, season_type))
