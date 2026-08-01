"""Within-season timing of a player's games — the resolved-vs-ongoing signal.

WHY THIS EXISTS (M2-1, batch-B1 §3). Every availability arm A–E sees HOW MUCH of
season N−1 a player missed; none sees WHEN. An absence that resolved (player
returned and played the final weeks of N−1) and one ongoing at season end (IR
into January) are the same number of missed games and radically different
season-N expectations — the Burrow/Hill defect class, measured at 86–131% of
v1's market-panel excess rank error.

The weekly box score itself carries the timing. No injury table is consulted
(measured coverage on ≥9-game absences: 2.5–4.8%, `pos_data.load_depth_seasons`
docstring). This loader follows `pos_data.py`'s pattern exactly: SQL-side
`season < ?` bound, HoldoutViolation on leaked rows, and a gated accessor on a
SeasonPanel subclass so every read lands in the same audit log the WalkForward
asserts on. Not a hand-rolled cutoff.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation, SeasonPanel,
    build_panel,
)

_SHAPE_SQL = """
SELECT player_id, season, week
FROM player_weekly_stats
WHERE season_type = 'REG' AND season < ?
  AND position IN ('QB','RB','WR','TE','FB')
"""


def load_week_shape(db_path: Path = DEFAULT_DB,
                    max_season: int = HOLDOUT_SEASON) -> pd.DataFrame:
    """Per (player_id, season): last week played, games in the final four
    SCHEDULED weeks, and that season's max scheduled week (measured from the
    data itself — bye-week eras make `week` run past the games count, so the
    schedule length is max(week) over the season, not season_length())."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        wk = pd.read_sql_query(_SHAPE_SQL, conn, params=(max_season,))
    finally:
        conn.close()
    if len(wk) and (wk["season"] >= max_season).any():
        raise HoldoutViolation("week-shape rows leaked past the SQL gate")
    wk_max = wk.groupby("season")["week"].max().rename("wk_max")
    wk = wk.merge(wk_max, on="season")
    wk["is_late4"] = (wk["week"] > wk["wk_max"] - 4).astype(int)
    out = wk.groupby(["player_id", "season"], sort=False).agg(
        last_wk=("week", "max"),
        first_wk=("week", "min"),
        late4=("is_late4", "sum"),
        wk_max=("wk_max", "max"),
    ).reset_index()
    return out


@dataclass
class V2Panel(SeasonPanel):
    """SeasonPanel plus the week-shape frame, behind the same gate discipline."""

    _weekshape: pd.DataFrame = field(default_factory=pd.DataFrame)

    def weekshape_before(self, cutoff: int) -> pd.DataFrame:
        self._gate(cutoff)
        out = self._weekshape[self._weekshape["season"] <= cutoff].copy() \
            if len(self._weekshape) else pd.DataFrame(
                columns=["player_id", "season", "last_wk", "first_wk",
                         "late4", "wk_max"])
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation("week-shape cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out


def build_v2_panel(db_path: Path = DEFAULT_DB,
                   feature_gate: int = HOLDOUT_SEASON,
                   outcome_gate: int = HOLDOUT_SEASON) -> V2Panel:
    """The standard panel, upgraded in place. Every gate/audit semantic is
    inherited; the only addition is the week-shape frame."""
    base = build_panel(db_path, feature_gate=feature_gate,
                       outcome_gate=outcome_gate)
    return V2Panel(
        base._frame, base._team, base._injury, base._depth,
        base.birthdates, base.draft, base._wk1, base._roster, base._coord,
        base._ngs, base._rush,
        feature_gate=base.feature_gate, outcome_gate=base.outcome_gate,
        _weekshape=load_week_shape(db_path, max_season=feature_gate))
