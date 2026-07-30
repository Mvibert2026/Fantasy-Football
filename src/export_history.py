"""
Weekly finishes and season stats exports (thread 017 / thread 039, contract 1.9.0;
made league-scoring-aware and per-league 2026-07-30, FR-079/FR-083, contract 1.16.0).

Two artifacts, same envelope pattern as player_descriptions.json:

  weekly_finishes.json -- per player, per season, per week positional finish
      (1 = best scorer at that position that week), under THIS export's league.
  season_stats.json    -- per player, per season, aggregate counting stats +
      fantasy_points, under THIS export's league.

Both are DISPLAY artifacts built by SQL aggregation plus this project's own
scoring engine (`scoring.score_offensive_game`) over `player_weekly_stats`
(data/nfl.db). Neither fits, tunes, or selects a model parameter -- they are
historical facts shown back to the user (consistency heat-map, player detail
history), not inputs to `make_board`, `backtest`, or any ranking config. See
the HOLDOUT note below for why 2025 is included without going through
`holdout.guard()`.

LEAGUE-SCORING-AWARE, NOT LEAGUE-BLIND (FR-079/FR-083 root-cause fix). Until
this fix, both artifacts summed/ranked `player_weekly_stats.fantasy_points_ppr`
-- a column nflreadpy ships as-is, computed under nflverse's OWN fixed full-PPR
convention. It was never this project's scoring engine, never tunable, and
never varied by league: every league's player card showed the identical
number, and Westwood's own board -- despite being the one league with a
verified custom ruleset -- was no exception. The founder's complaint ("last
few seasons should be in correct format") was literally true for every league
including the primary one.

The fix re-derives fantasy points per player-week from raw counting stats
(`db.player_week_scoring_inputs`, the same view `make_board`/backtesting read)
through `scoring.score_offensive_game(stats, cfg.scoring)` -- THIS project's
engine, THIS league's cfg -- then aggregates. This is scored per-week, never
summed-then-scored: `cfg.scoring`'s yardage bonuses are game-level thresholds
(e.g. +1 at 100 rushing yards IN A GAME), so scoring a season's summed yards
would fabricate or omit bonuses a real season of games did not actually earn.

SHAPE DECISION: PER-LEAGUE EXPORT ARTIFACTS, NOT READ-TIME APPLICATION.
board.json/league.json/availability.json/rosters.json already export one copy
per league (`export_contract.export_dir_for`); this module now follows the
same, already-established pattern rather than inventing a second one. The
alternative -- export raw per-week counting stats once and let the reader
apply a ruleset -- was rejected: the whole reason frontend escalated this
instead of patching it themselves is that scoring must never be computed
outside this project's own engine (browser-side re-scoring would be exactly
the kind of approximation CLAUDE.md forbids, and a raw-components artifact
invites exactly that temptation). Landing every artifact as an already-scored,
already-correct number keeps the "frontend never computes scoring" rule intact
structurally, not by convention -- the same reasoning `make_board.build_board`
already applies (it takes `scoring_cfg`, not a ruleset-neutral output).

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
from typing import Dict, List, Optional, Tuple

import db as dbmod
import league_config as lc
import scoring as sc

EXPORT_VERSION = "2.0.0"
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

SCORING_NOTE_TEXT = (
    "fantasy_points (weekly_finishes.json's ranking basis and season_stats.json's season "
    "total) is computed by THIS project's own scoring engine (scoring.score_offensive_game) "
    "under THIS league's cfg.scoring, scored per game and then summed -- NOT nflreadpy's "
    "fixed fantasy_points_ppr column, which is nflverse's own full-PPR convention and does "
    "not vary by league. See league_id/scoring_ruleset_note in this envelope for exactly "
    "which ruleset was applied. Yardage bonuses are game-level thresholds, so scoring happens "
    "before summing across a season, never after (a summed-then-scored season could "
    "fabricate or drop a bonus no single game actually earned)."
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


def _weekly_scored_points(
    conn: sqlite3.Connection, ids: List[str], scoring_cfg: dict
) -> Dict[Tuple[str, int, int], float]:
    """Recompute every (player_id, season, week)'s fantasy points under
    `scoring_cfg`, from raw counting stats -- never from the stored
    `fantasy_points_ppr` column (see module docstring).

    Reuses `db.player_week_scoring_inputs` (`db._CREATE_SCORING_VIEW_SQL`),
    the same view make_board/backtesting read, so the column mapping onto
    `scoring.score_offensive_game`'s expected stat keys cannot drift out of
    sync between this module and the ranking engine. `CREATE VIEW IF NOT
    EXISTS` is idempotent -- safe to call again even though `db.connect()`
    already created it for a real connection; a synthetic test connection
    that built its own `player_weekly_stats` table gets the view created
    here for the first time.
    """
    conn.row_factory = sqlite3.Row
    conn.execute(dbmod._CREATE_SCORING_VIEW_SQL)
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    stat_cols = ", ".join(dbmod.SCORING_STAT_COLUMNS)
    rows = conn.execute(
        f"SELECT player_id, season, week, {stat_cols} "
        f"FROM {dbmod.SCORING_VIEW} "
        f"WHERE player_id IN ({placeholders}) AND season_type = 'REG'",
        ids,
    ).fetchall()
    out: Dict[Tuple[str, int, int], float] = {}
    for r in rows:
        stats = {c: r[c] for c in dbmod.SCORING_STAT_COLUMNS}
        out[(r["player_id"], r["season"], r["week"])] = sc.score_offensive_game(
            stats, scoring_cfg
        )
    return out


def _rank_desc(pairs: List[Tuple[object, float]]) -> Dict[object, int]:
    """Standard SQL RANK() semantics over (key, value) pairs, sorted by value
    descending: ties share a rank, the next distinct value skips (1,1,3, not
    1,1,2) -- matches the RANK() OVER (...) this module used before it moved
    ranking into Python (required once ranking depends on `scoring_cfg`,
    which SQL cannot see)."""
    ordered = sorted(pairs, key=lambda kv: -kv[1])
    ranks: Dict[object, int] = {}
    for i, (key, value) in enumerate(ordered):
        if i == 0 or value < ordered[i - 1][1]:
            ranks[key] = i + 1
        else:
            ranks[key] = ranks[ordered[i - 1][0]]
    return ranks


def build_weekly_finishes(
    conn: sqlite3.Connection,
    player_ids: Optional[List[str]] = None,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
) -> dict:
    conn.row_factory = sqlite3.Row
    ids = player_ids if player_ids is not None else _player_universe(conn)
    if not ids:
        return {
            "export_version": EXPORT_VERSION,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "league_id": cfg.league_id,
            "note": NOTE_TEXT,
            "scoring_note": SCORING_NOTE_TEXT,
            "scoring_ruleset_note": lc.scoring_ruleset_note_for(cfg),
            "players": [],
        }

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT player_id, season, week, position, team
        FROM player_weekly_stats
        WHERE player_id IN ({placeholders})
          AND position IN ({",".join("?" * len(FANTASY_POSITIONS))})
          AND season_type = 'REG'
        ORDER BY player_id, season, week
        """,
        (*ids, *FANTASY_POSITIONS),
    ).fetchall()

    scored = _weekly_scored_points(conn, ids, cfg.scoring)

    # Rank within (season, week, position), under THIS league's scored points
    # -- SQL's RANK() can no longer do this, since the ranking basis now
    # depends on cfg.scoring, which SQL has no way to see.
    groups: Dict[Tuple[int, int, str], List[Tuple[str, float]]] = defaultdict(list)
    for r in rows:
        key = (r["player_id"], r["season"], r["week"])
        pts = scored.get(key)
        if pts is None:
            continue
        groups[(r["season"], r["week"], r["position"])].append((r["player_id"], pts))
    ranks: Dict[Tuple[int, int, str, str], int] = {}
    for (season, week, position), pairs in groups.items():
        for pid, rank in _rank_desc(pairs).items():
            ranks[(season, week, position, pid)] = rank

    by_player: Dict[str, Dict[int, Dict[int, dict]]] = defaultdict(lambda: defaultdict(dict))
    team_of_player_season: Dict[tuple, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seasons_seen = set()
    for r in rows:
        key = (r["player_id"], r["season"], r["week"])
        if key not in scored:
            # No raw-stat row in the scoring view for this player-week (the
            # view is a superset in practice, but never assume) -- honest
            # omission, not a fabricated finish.
            continue
        seasons_seen.add(r["season"])
        rank = ranks.get((r["season"], r["week"], r["position"], r["player_id"]))
        by_player[r["player_id"]][r["season"]][r["week"]] = {
            "week": r["week"], "finish": rank, "bye": False,
        }
        if r["team"]:
            team_of_player_season[(r["player_id"], r["season"])][r["team"]] += 1

    byes = _bye_weeks_by_season(sorted(seasons_seen))
    import export_contract as ec  # T9: _canonical_team, see lookup below

    players = []
    for pid in sorted(by_player):
        season_blocks = {}
        for season, weeks in sorted(by_player[pid].items()):
            team_counts = team_of_player_season.get((pid, season), {})
            primary_team = max(team_counts, key=team_counts.get) if team_counts else None
            # T9: byes' keys are canonicalized (export_contract._bye_weeks);
            # primary_team comes straight from player_weekly_stats.team,
            # which for old seasons carries THAT era's code (e.g. "OAK",
            # "STL") -- canonicalize the lookup key too, or every
            # pre-relocation season's bye silently stops resolving the
            # moment _bye_weeks' own keys became canonical.
            canonical_team = ec._canonical_team(primary_team) if primary_team else None
            bye_week = byes.get(season, {}).get(canonical_team) if canonical_team else None

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
        "league_id": cfg.league_id,
        "note": NOTE_TEXT,
        "scoring_note": SCORING_NOTE_TEXT,
        "scoring_ruleset_note": lc.scoring_ruleset_note_for(cfg),
        "no_row_semantics_note": (
            "A week with no row here and bye=false means the player had no recorded "
            "statistical output that week (inactive, injured, or off this team's active "
            "roster) -- it is not a confirmed roster/inactive-list lookup, because no such "
            "source is joined here. bye=true is schedule-derived and distinct: the player's "
            "primary team for that season had no game that week."
        ),
        "players": players,
    }


def build_season_stats(
    conn: sqlite3.Connection,
    player_ids: Optional[List[str]] = None,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
) -> dict:
    conn.row_factory = sqlite3.Row
    ids = player_ids if player_ids is not None else _player_universe(conn)
    if not ids:
        return {
            "export_version": EXPORT_VERSION,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "league_id": cfg.league_id,
            "note": NOTE_TEXT,
            "scoring_note": SCORING_NOTE_TEXT,
            "scoring_ruleset_note": lc.scoring_ruleset_note_for(cfg),
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
               SUM(rushing_tds) AS rushing_tds
        FROM player_weekly_stats
        WHERE player_id IN ({placeholders})
          AND position IN ({",".join("?" * len(FANTASY_POSITIONS))})
          AND season_type = 'REG'
        GROUP BY player_id, season
        ORDER BY player_id, season
        """,
        (*ids, *FANTASY_POSITIONS),
    ).fetchall()

    scored = _weekly_scored_points(conn, ids, cfg.scoring)
    season_totals: Dict[Tuple[str, int], float] = defaultdict(float)
    for (pid, season, _week), pts in scored.items():
        season_totals[(pid, season)] += pts

    by_player: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        unavailable = r["season"] in TARGET_DATA_UNAVAILABLE_SEASONS
        total = season_totals.get((r["player_id"], r["season"]))
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
            # Scored under cfg.scoring per game, then summed -- see
            # SCORING_NOTE_TEXT. Absent (null), with fantasy_points_available
            # false, rather than a fabricated 0, on the rare row where no
            # scoring-view stats resolved for this player-season at all
            # (absent beats wrong).
            "fantasy_points": round(total, 1) if total is not None else None,
            "fantasy_points_available": total is not None,
        })

    players = [{"player_id": pid, "seasons": seasons} for pid, seasons in sorted(by_player.items())]

    return {
        "export_version": EXPORT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "note": NOTE_TEXT,
        "scoring_note": SCORING_NOTE_TEXT,
        "scoring_ruleset_note": lc.scoring_ruleset_note_for(cfg),
        "players": players,
    }


def write_all(
    out_dir: Path, conn: sqlite3.Connection, cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = _player_universe(conn)
    artifacts = {
        "weekly_finishes.json": build_weekly_finishes(conn, ids, cfg),
        "season_stats.json": build_season_stats(conn, ids, cfg),
    }
    written = []
    for name, payload in artifacts.items():
        p = out_dir / name
        p.write_text(json.dumps(payload, indent=2, default=str, allow_nan=False), encoding="utf-8")
        written.append(p)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--league", default=lc.PRIMARY_LEAGUE_ID,
        help="league_id of a saved config under data/leagues/, or 'primary' (default)",
    )
    args = ap.parse_args()
    cfg = (
        lc.CURRENT_LEAGUE if args.league == lc.PRIMARY_LEAGUE_ID else lc.LeagueConfig.load(args.league)
    )

    import export_contract as ec

    out_dir = args.out or ec.export_dir_for(cfg.league_id)
    conn = dbmod.connect()
    try:
        written = write_all(out_dir, conn, cfg=cfg)
    finally:
        conn.close()
    for p in written:
        print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
