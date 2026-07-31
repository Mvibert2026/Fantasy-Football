"""Expert-consensus baseline -- `CLAUDE.md` §6.5 baseline #2.

**This is the second crowd, and it is a different object from `adp_baseline`.**
Market ADP is the empirical distribution of drafter behaviour; expert consensus
is analyst opinion. §6.5 as amended 2026-07-31 (founder's ruling) requires both,
and requires that a version beating one and losing to the other reports exactly
that rather than the flattering half.

Source: `rankings` where `source = 'fantasypros_ecr'`, the DynastyProcess mirror,
seasons 2021-2026. This is what the **shipped board** trains its curve on
(`make_board.TRAINING_SOURCE`) and what `draft_sim.py:120` runs on.

LOOK-AHEAD: only `is_preseason_final = 1` rows are served, and this module
re-asserts that every served row's `as_of_date` is strictly before that season's
real Week 1 kickoff (measured from PFR game ids via
`adp_baseline.kickoff_dates`, not assumed) rather than trusting the flag.

KNOWN, UNRESOLVED: `scoring_format` is NULL on all 2,948 mirror rows -- the
format these ranks were produced under is unrecorded
(`fr136-q1-bottom-up-assessment.md` §0). Expert overall ranks are broadly
format-insensitive near the top, but this is an unlabelled assumption and it
travels with every number computed from this source.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from .adp_baseline import DEFAULT_DB, kickoff_dates

SOURCE = "fantasypros_ecr"


def ecr_seasons(db_path: Path = DEFAULT_DB) -> list:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT DISTINCT season FROM rankings WHERE source=? "
            "AND is_preseason_final=1 ORDER BY season", (SOURCE,)).fetchall()
    finally:
        conn.close()
    return [int(r[0]) for r in rows]


def load_ecr(season: int, position: Optional[str] = None,
             db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """That season's preseason-final expert consensus board.

    Returns `player_id` (gsis), `ecr_overall_rank`, `ecr_pos_rank`. The
    within-position rank is computed from the overall rank restricted to the
    position, which is the ordering a positional draft board actually uses.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(
            "SELECT player_id, player_name, position, adp_rank, as_of_date "
            "FROM rankings WHERE source=? AND is_preseason_final=1 AND season=?",
            conn, params=(SOURCE, season))
    finally:
        conn.close()
    if not len(df):
        # DTYPES MATTER. A bare `pd.DataFrame(columns=[...])` yields object-dtype
        # columns; concatenating one of these with real seasons silently promotes
        # `season` to object and every downstream merge then matches ZERO rows
        # while looking perfectly healthy. That bug produced a fake all-NaN
        # expert-consensus panel on the first v1 run.
        return pd.DataFrame({
            "player_id": pd.Series(dtype="object"),
            "player_name": pd.Series(dtype="object"),
            "position": pd.Series(dtype="object"),
            "ecr_overall_rank": pd.Series(dtype="float64"),
            "ecr_pos_rank": pd.Series(dtype="float64"),
            "season": pd.Series(dtype="int64")})

    ts = pd.to_datetime(df["as_of_date"], errors="coerce")
    cutoff = kickoff_dates(db_path).get(season, pd.Timestamp(f"{season}-09-01"))
    bad = ts.isna() | (ts >= cutoff)
    if bad.any():
        raise ValueError(
            f"{season} ECR: {int(bad.sum())} rows are not strictly pre-kickoff "
            f"({cutoff.date()}); refusing to use them")

    df = df[df["player_id"].notna() & (df["player_id"] != "")]
    if position:
        df = df[df["position"] == position]
    df = df.dropna(subset=["adp_rank"]).drop_duplicates("player_id").copy()
    df["ecr_overall_rank"] = df["adp_rank"].astype(float)
    df["ecr_pos_rank"] = df["ecr_overall_rank"].rank(method="first")
    df["season"] = season
    return df[["player_id", "player_name", "position", "ecr_overall_rank",
               "ecr_pos_rank", "season"]]
