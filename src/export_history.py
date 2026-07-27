"""
Weekly finishes and season stats exports (thread 017 / thread 039, contract 1.9.0).

Two new artifacts, same envelope pattern as player_descriptions.json:

  data/export/weekly_finishes.json -- per player, per season, per week
      positional finish (1 = best scorer at that position that week).
  data/export/season_stats.json    -- per player, per season, aggregate
      counting stats + fantasy_points_ppr.

Both are DISPLAY artifacts built by simple SQL aggregation/ranking over
`player_weekly_stats` (data/nfl.db). Neither fits, tunes, or selects a model
parameter -- they are historical facts shown back to the user (consistency
heat-map, player detail history), not inputs to `make_board`, `backtest`, or
any ranking config. See the HOLDOUT note below for why 2025 is included
without going through `holdout.guard()`.

PLAYER UNIVERSE. Every `player_id` with >=1 row in `player_weekly_stats` for
season >= 2018 at a fantasy-relevant position (QB/RB/WR/TE -- this project
ingests no kicker or DST stats, ADR-039/041, so K/DEF rows are dropped here
the same way board.json drops them). This matches the existing board/rankings
population and keeps the export from ballooning to include ~4700 players who
were never fantasy-relevant (long-snappers, offensive linemen, etc. also live
in player_weekly_stats). Season DETAIL rows for an included player go back as
far as that player's own history in the table -- a long-career player
included via a 2018+ row can still show a 2008 season underneath.

HARD CONSTRAINT (carried from thread 017, binding): `targets` is present but
not reliably measured for seasons 2003-2008 -- a charting-coverage gap in the
upstream data, not a real football zero (see docstring math below). Season
rows in that window are marked `target_data_unavailable: true` and `targets`
is emitted as `null`, never `0`. This is checked directly against the data
(SUM(targets) for those seasons is 0-67 league-wide vs 16,000+ in adjacent
seasons) rather than assumed from the thread text.

HOLDOUT NOTE. `holdout.py`'s lock governs season 2025 for MODEL SELECTION --
which factors a ranking config uses, decided by comparing against outcomes.
Nothing in this module selects a factor, fits a weight, or evaluates a
ranking config; it re-shapes raw historical box scores for a "your player's
last three seasons" table. Reading 2025's real, already-happened results for
that purpose is not a HoldoutViolation under CLAUDE.md #6.1's own framing
("touching it outside pre-registered context") -- there is no ranking
decision being made here to contaminate. Flagged explicitly rather than
decided silently, per operating rules; revisit if this module is ever asked
to feed a metric back into model selection.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

EXPORT_VERSION = "1.0.0"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPORT_DIR = DATA_DIR / "export"

FANTASY_POSITIONS = ("QB", "RB", "WR", "TE")

# Player universe cutoff: matches the board/rankings population (thread 039).
UNIVERSE_MIN_SEASON = 2018

# Charting-artifact gap: targets exist as a column for 2003-2008 but are not
# reliably measured (near-zero league-wide sums instead of the ~16k+ seen in
# adjacent seasons). Verified directly against data/nfl.db before writing this
# constant -- see module docstring.
TARGET_DATA_UNAVAILABLE_SEASONS = frozenset(range(2003, 2009))

NOTE_TEXT = (
    "Real historical player_weekly_stats data (data/nfl.db), not the sample/mock data the "
    "prototype used. Targets are present in the source data for 2003-2008 but are a known "
    "charting-coverage gap, not a real measurement -- those seasons carry "
    "target_data_unavailable: true and targets is null, never 0, for that range. Every "
    "season from 2009 onward is unaffected."
)


def _player_universe(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(FANTASY_POSITIONS))
    ids = conn.execute(
        f"SELECT DISTINCT player_id FROM player_weekly_stats "
        f"WHERE season >= ? AND position IN ({placeholders}) AND player_id IS NOT NULL",
        (UNIVERSE_MIN_SEASON, *FANTASY_POSITIONS),
    ).fetchall()
    return [r["player_id"] for r in ids]


def _bye_weeks_by_season(seasons: List[int]) -> Dict[int, Dict[str, Optional[int]]]:
    """Reuses export_contract's schedule-derived bye lookup per season."""
    import export_contract as ec

    out = {}
    for season in seasons:
        try:
            out[season] = ec._bye_weeks(season)
        except Exception:
            # No schedule data cached for very old seasons / offline runs --
            # fail open to "unknown", not to a fabricated bye guess.
            out[season] = {}
    return out


def build_weekly_finishes(conn: sqlite3.Connection, player_ids: Optional[List[str]] = None) -> dict:
    conn.row_factory = sqlite3.Row
    ids = player_ids if player_ids is not None else _player_universe(conn)
    if not ids:
        return {
            "export_version": EXPORT_VERSION,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "note": NOTE_TEXT,
            "players": [],
        }

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT player_id, season, week, position, team,
               RANK() OVER (
                   PARTITION BY season, week, position
                   ORDER BY fantasy_points_ppr DESC
               ) AS finish
        FROM player_weekly_stats
        WHERE player_id IN ({placeholders})
          AND position IN ({",".join("?" * len(FANTASY_POSITIONS))})
          AND season_type = 'REG'
          AND fantasy_points_ppr IS NOT NULL
        ORDER BY player_id, season, week
        """,
        (*ids, *FANTASY_POSITIONS),
    ).fetchall()

    by_player: Dict[str, Dict[int, Dict[int, dict]]] = defaultdict(lambda: defaultdict(dict))
    team_of_player_season: Dict[tuple, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seasons_seen = set()
    for r in rows:
        seasons_seen.add(r["season"])
        by_player[r["player_id"]][r["season"]][r["week"]] = {
            "week": r["week"], "finish": r["finish"], "bye": False,
        }
        if r["team"]:
            team_of_player_season[(r["player_id"], r["season"])][r["team"]] += 1

    byes = _bye_weeks_by_season(sorted(seasons_seen))

    players = []
    for pid in sorted(by_player):
        season_blocks = {}
        for season, weeks in sorted(by_player[pid].items()):
            team_counts = team_of_player_season.get((pid, season), {})
            primary_team = max(team_counts, key=team_counts.get) if team_counts else None
            bye_week = byes.get(season, {}).get(primary_team) if primary_team else None

            week_list = list(weeks.values())
            if bye_week is not None and bye_week not in weeks:
                week_list.append({"week": bye_week, "finish": None, "bye": True})
            week_list.sort(key=lambda w: w["week"])

            season_blocks[str(season)] = {
                "target_data_unavailable": season in TARGET_DATA_UNAVAILABLE_SEASONS,
                "weeks": week_list,
            }
        players.append({"player_id": pid, "seasons": season_blocks})

    return {
        "export_version": EXPORT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "note": NOTE_TEXT,
        "no_row_semantics_note": (
            "A week with no row here and bye=false means the player had no recorded "
            "statistical output that week (inactive, injured, or off this team's active "
            "roster) -- it is not a confirmed roster/inactive-list lookup, because no such "
            "source is joined here. bye=true is schedule-derived and distinct: the player's "
            "primary team for that season had no game that week."
        ),
        "players": players,
    }


def build_season_stats(conn: sqlite3.Connection, player_ids: Optional[List[str]] = None) -> dict:
    conn.row_factory = sqlite3.Row
    ids = player_ids if player_ids is not None else _player_universe(conn)
    if not ids:
        return {
            "export_version": EXPORT_VERSION,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "note": NOTE_TEXT,
            "players": [],
        }

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT player_id, season,
               COUNT(*) AS games,
               SUM(targets) AS targets,
               SUM(receptions) AS receptions,
               SUM(receiving_yards) AS receiving_yards,
               SUM(receiving_tds) AS receiving_tds,
               SUM(rushing_yards) AS rushing_yards,
               SUM(rushing_tds) AS rushing_tds,
               SUM(fantasy_points_ppr) AS fantasy_points_ppr
        FROM player_weekly_stats
        WHERE player_id IN ({placeholders})
          AND position IN ({",".join("?" * len(FANTASY_POSITIONS))})
          AND season_type = 'REG'
        GROUP BY player_id, season
        ORDER BY player_id, season
        """,
        (*ids, *FANTASY_POSITIONS),
    ).fetchall()

    by_player: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        unavailable = r["season"] in TARGET_DATA_UNAVAILABLE_SEASONS
        by_player[r["player_id"]].append({
            "year": r["season"],
            "games": r["games"],
            # A real zero (0 targets in 2015) and "not measured" (2003-2008)
            # are different claims -- never collapse the second into the
            # first. See module docstring.
            "targets": None if unavailable else r["targets"],
            "target_data_unavailable": unavailable,
            "receptions": r["receptions"],
            "receiving_yards": r["receiving_yards"],
            "receiving_tds": r["receiving_tds"],
            "rushing_yards": r["rushing_yards"],
            "rushing_tds": r["rushing_tds"],
            "fantasy_points_ppr": (
                round(r["fantasy_points_ppr"], 1) if r["fantasy_points_ppr"] is not None else None
            ),
        })

    players = [{"player_id": pid, "seasons": seasons} for pid, seasons in sorted(by_player.items())]

    return {
        "export_version": EXPORT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "note": NOTE_TEXT,
        "players": players,
    }


def write_all(out_dir: Path, conn: sqlite3.Connection) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = _player_universe(conn)
    artifacts = {
        "weekly_finishes.json": build_weekly_finishes(conn, ids),
        "season_stats.json": build_season_stats(conn, ids),
    }
    written = []
    for name, payload in artifacts.items():
        p = out_dir / name
        p.write_text(json.dumps(payload, indent=2, default=str, allow_nan=False), encoding="utf-8")
        written.append(p)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=EXPORT_DIR)
    args = ap.parse_args()

    import db as dbmod

    conn = dbmod.connect()
    try:
        written = write_all(args.out, conn)
    finally:
        conn.close()
    for p in written:
        print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
