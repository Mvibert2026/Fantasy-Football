"""Consensus ADP baseline -- the one that matters (CLAUDE.md 6.5).

Source: `data/adp-snapshots-ffc/*_half_ppr_12team_period{season}.csv`, landed by
`tools/backfill_ffc_adp_history.py` (thread 055). Half-PPR is this league's own
format; 12-team is the only team count FFC archives for past seasons.

LOOK-AHEAD: every row carries `as_of_date` = the END of FFC's own stated draft
sample window, verified by the backfill against that season's real Week 1
kickoff. This module re-asserts that gate rather than trusting it, and drops any
season whose snapshot is not strictly pre-kickoff.

The CSVs are read directly rather than through `nfl.db` because the backfill is
a one-time script whose output is committed as CSV while the database is not.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
ADP_DIR = _REPO / "data" / "adp-snapshots-ffc"
DEFAULT_DB = _REPO / "data" / "nfl.db"

# Real Week 1 kickoff per season (nflverse schedules, min REG gameday).
# Recomputed by `kickoffs()` rather than trusted from a doc.
_KICKOFF_SQL = """
SELECT season, MIN(week) FROM player_weekly_stats WHERE season_type='REG' GROUP BY season
"""


def _mfl_to_gsis(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        x = pd.read_sql_query(
            "SELECT mfl_id, gsis_id FROM ff_playerids "
            "WHERE mfl_id IS NOT NULL AND gsis_id IS NOT NULL", conn)
    finally:
        conn.close()
    x["mfl_id"] = x["mfl_id"].astype(str).str.strip()
    return x.drop_duplicates("mfl_id")


_KICKOFF_CACHE: Dict[int, pd.Timestamp] = {}


def kickoff_dates(db_path: Path = DEFAULT_DB) -> Dict[int, pd.Timestamp]:
    """Real Week 1 kickoff per season, MEASURED not assumed.

    nflverse's `game_id` (SEASON_WW_AWAY_HOME) carries no date, but PFR's does:
    `201809060phi` = 2018-09-06. `snap_counts` carries `pfr_game_id` for
    2013-2025, which covers every season with archived ADP. Seasons outside
    that range fall back to the conservative Sep 1 bound, which can only reject
    a snapshot, never admit a contaminated one.
    """
    if _KICKOFF_CACHE:
        return dict(_KICKOFF_CACHE)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT season, MIN(pfr_game_id) FROM snap_counts "
            "WHERE week=1 AND game_type='REG' AND pfr_game_id IS NOT NULL "
            "GROUP BY season").fetchall()
    finally:
        conn.close()
    for season, gid in rows:
        m = re.match(r"^(\d{8})", str(gid))
        if m:
            _KICKOFF_CACHE[int(season)] = pd.Timestamp(m.group(1))
    return dict(_KICKOFF_CACHE)


def load_adp(season: int, fmt: str = "half_ppr_12team",
             db_path: Path = DEFAULT_DB,
             position: Optional[str] = "WR") -> pd.DataFrame:
    """That season's pre-draft consensus board, mapped to gsis player ids."""
    matches = sorted(ADP_DIR.glob(f"*_{fmt}_period{season}.csv"))
    if not matches:
        return pd.DataFrame(columns=["player_id", "average_pick", "adp_rank"])
    df = pd.read_csv(matches[-1], dtype={"mfl_id": str})
    df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
    cutoff = kickoff_dates(db_path).get(season, pd.Timestamp(f"{season}-09-01"))
    bad = df["as_of_date"].isna() | (df["as_of_date"] >= cutoff)
    if bad.any():
        raise ValueError(
            f"{season} {fmt}: {int(bad.sum())} ADP rows are not strictly "
            f"pre-kickoff ({cutoff.date()}); refusing to use them")
    if position:
        df = df[df["position"] == position]
    xw = _mfl_to_gsis(db_path)
    df["mfl_id"] = df["mfl_id"].astype(str).str.strip()
    m = df.merge(xw, on="mfl_id", how="left").rename(columns={"gsis_id": "player_id"})
    out = m[["player_id", "player_name", "position", "average_pick", "rank"]].copy()
    out = out.rename(columns={"rank": "overall_rank"})
    out["unmatched"] = out["player_id"].isna()
    out["season"] = season
    return out


def adp_seasons(fmt: str = "half_ppr_12team") -> list:
    seasons = []
    for p in ADP_DIR.glob(f"*_{fmt}_period*.csv"):
        m = re.search(r"period(\d{4})\.csv$", p.name)
        if m:
            seasons.append(int(m.group(1)))
    return sorted(set(seasons))
