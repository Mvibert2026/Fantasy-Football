"""Batch-D1 data layer — the three ingested-but-unread tables, aggregated to
(player_id, season) and served behind the same gate discipline as everything else.

WHAT IS NEW HERE, and why it is not already in the model:

`injuries` (79,816 rows, 2009-2024) is read today by exactly one feature pair
(`inj_out_wks`, `inj_report_wks`, `pos_data.load_injury_seasons`) which counts
weeks on the report and weeks ruled Out. **`practice_status` has never been
read by any model** -- Did Not Participate / Limited / Full, the raw material a
beat reporter reports *on*, structured and fully backtestable. Nor has
`practice_primary_injury` / `report_primary_injury`, which names the body part.

`rosters_weekly` (888,786 rows, 2002-2025) is read today only at `week = 1` of
season N (`pos_data.load_preseason_rosters`), which is the G2a proxy strategist
has NOT admitted. **Season N-1's weekly status history is ordinary N-1
information with no as-of question at all**, and nothing reads it.

MEASURED COVERAGE, before any of this is used (recon, 2026-08-01):

  source            usable from   note
  injuries            2010        2009 holds 17 rows; practice_status populated
                                  on every row from 2010
  rosters_weekly RES  2002        BUT end-of-season RES *capture* breaks at 2017:
                                  prevalence in the missed->=40%-of-season
                                  population is 0.012-0.045 for 2012-2016 and
                                  0.17-0.28 for 2017-2024. Pre-2017 it is a time
                                  dummy in exactly batch 7 D2's geometry, so the
                                  roster block is registered against a control
                                  whose TRAINING window also starts at 2017 --
                                  restricting the target window alone is the
                                  mistake batch 5 made.
  depth_charts_weekly 2001        stable coverage, and ELIMINATED as a substitute:
                                  its end-of-season presence flag carries no
                                  contrast (4.26 vs 4.44 mean games in N, sign
                                  flips season to season).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from ..components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation,
)
from .weekshape import V2Panel, build_v2_panel

#: first season each source may be trusted. Used to build the `*_known`
#: SEASON-LEVEL coverage flags. A player-level "did he appear" indicator is a
#: TREATMENT, not a coverage control, and the two are kept separate here on
#: purpose -- conflating them is how batch 5 read a calendar as a feature.
SRC_FIRST_SEASON: Dict[str, int] = {"injuries": 2010, "rosters": 2017}

# --------------------------------------------------------------- injuries
_PRAC_SQL = """
SELECT gsis_id AS player_id, CAST(season AS INTEGER) AS season,
       CAST(week AS INTEGER) AS week, report_status, practice_status,
       COALESCE(NULLIF(practice_primary_injury, ''),
                NULLIF(report_primary_injury, '')) AS body_part
FROM injuries
WHERE game_type = 'REG' AND gsis_id IS NOT NULL AND gsis_id <> ''
  AND week IS NOT NULL AND season < ?
"""

#: body-part classes. Ordered: the first class whose pattern matches wins, so
#: "not injury related - resting player" is REST and never STRUCTURAL via a
#: stray substring. Patterns are lowercase substrings of the free text.
INJURY_CLASSES: List[tuple] = [
    ("rest", ("not injury related", "resting player", "personal matter",
              "load management", "illness", "coach")),
    ("head", ("concussion", "head")),
    ("structural", ("knee", "acl", "achilles", "lisfranc", "foot", "ankle",
                    "shoulder", "labrum", "pectoral", "hip", "back", "neck",
                    "spine", "clavicle", "fibula", "tibia")),
    ("soft", ("hamstring", "groin", "quad", "calf", "thigh", "oblique",
              "abdom", "adductor", "hip flexor")),
]
CLASS_NAMES = [c for c, _ in INJURY_CLASSES] + ["other"]


def classify_body_part(x) -> str:
    s = str(x).strip().lower()
    if not s or s in ("none", "nan"):
        return "none"
    for name, pats in INJURY_CLASSES:
        if any(p in s for p in pats):
            return name
    return "other"


def load_practice_seasons(db_path: Path = DEFAULT_DB,
                          max_season: int = HOLDOUT_SEASON) -> pd.DataFrame:
    """Per (player_id, season), from the weekly injury report:

      rep_wks       weeks carrying any injury-report row
      dnp_wks       weeks listed Did Not Participate In Practice
      lim_wks       weeks listed Limited Participation
      full_wks      weeks listed Full Participation
      out_wks       weeks whose GAME status was Out or Doubtful
      dnp_late3     DNP weeks inside the final three scheduled weeks
      cls_<k>_wks   DNP weeks whose body part classified to <k>
      dom_cls       the class holding the most DNP weeks (ties -> first by
                    CLASS_NAMES order); NaN when the player never DNP'd
      wk_max        that season's max scheduled week, from the data

    A player-week appears at most once: a traded player can file under two clubs
    in the same week, and the aggregation takes the max of each indicator.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        inj = pd.read_sql_query(_PRAC_SQL, conn, params=(max_season,))
    finally:
        conn.close()
    if len(inj) and (inj["season"] >= max_season).any():
        raise HoldoutViolation("injury/practice rows leaked past the SQL gate")
    if not len(inj):
        return pd.DataFrame(columns=["player_id", "season", "rep_wks", "dnp_wks",
                                     "lim_wks", "full_wks", "out_wks",
                                     "dnp_late3", "dom_cls", "wk_max"])

    ps = inj["practice_status"].fillna("")
    inj["dnp"] = ps.str.startswith("Did Not").astype(int)
    inj["lim"] = ps.str.startswith("Limited").astype(int)
    inj["full"] = ps.str.startswith("Full").astype(int)
    inj["out"] = inj["report_status"].isin(["Out", "Doubtful"]).astype(int)
    inj["cls"] = inj["body_part"].map(classify_body_part)

    wk_max = inj.groupby("season")["week"].max().rename("wk_max")
    inj = inj.merge(wk_max, on="season")
    inj["late3"] = (inj["week"] > inj["wk_max"] - 3).astype(int)

    # collapse traded-week duplicates first
    pw = inj.groupby(["player_id", "season", "week"], sort=False).agg(
        dnp=("dnp", "max"), lim=("lim", "max"), full=("full", "max"),
        out=("out", "max"), late3=("late3", "max"), wk_max=("wk_max", "max"),
        cls=("cls", "first")).reset_index()
    pw["dnp_late3"] = pw["dnp"] * pw["late3"]

    agg = pw.groupby(["player_id", "season"], sort=False).agg(
        rep_wks=("week", "size"), dnp_wks=("dnp", "sum"), lim_wks=("lim", "sum"),
        full_wks=("full", "sum"), out_wks=("out", "sum"),
        dnp_late3=("dnp_late3", "sum"), wk_max=("wk_max", "max"),
    ).reset_index()

    # per-class DNP week counts, then the dominant class
    dnp_rows = pw[pw["dnp"] == 1]
    if len(dnp_rows):
        wide = dnp_rows.assign(v=1).pivot_table(
            index=["player_id", "season"], columns="cls", values="v",
            aggfunc="sum", fill_value=0).reset_index()
        for k in CLASS_NAMES:
            if k not in wide.columns:
                wide[k] = 0
        keep = ["player_id", "season"] + CLASS_NAMES
        wide = wide[keep].rename(columns={k: f"cls_{k}_wks" for k in CLASS_NAMES})
        counts = wide[[f"cls_{k}_wks" for k in CLASS_NAMES]].to_numpy()
        dom_idx = counts.argmax(axis=1)
        wide["dom_cls"] = [CLASS_NAMES[i] if counts[r].max() > 0 else None
                           for r, i in enumerate(dom_idx)]
        wide["n_cls"] = (counts > 0).sum(axis=1)
        agg = agg.merge(wide, on=["player_id", "season"], how="left")
    for k in CLASS_NAMES:
        col = f"cls_{k}_wks"
        if col not in agg.columns:
            agg[col] = 0.0
        agg[col] = agg[col].fillna(0.0)
    if "n_cls" not in agg.columns:
        agg["n_cls"] = 0.0
    agg["n_cls"] = agg["n_cls"].fillna(0.0)
    if "dom_cls" not in agg.columns:
        agg["dom_cls"] = None
    return agg


# ---------------------------------------------------------- roster status
_RSTAT_SQL = """
SELECT gsis_id AS player_id, season, week, status
FROM rosters_weekly
WHERE game_type = 'REG' AND gsis_id IS NOT NULL AND gsis_id <> ''
  AND week IS NOT NULL AND season < ?
"""

#: ACT and INA are both "on the active roster"; INA is the game-day inactive
#: list and only exists from 2019, so it is folded into ACT rather than used as
#: its own signal -- a bare INA feature would be a 2019 time dummy.
_ON_ROSTER = ("ACT", "INA")


def load_roster_status_seasons(db_path: Path = DEFAULT_DB,
                               max_season: int = HOLDOUT_SEASON) -> pd.DataFrame:
    """Per (player_id, season), from the weekly roster:

      act_wks      weeks with status ACT or INA (on the active roster)
      res_wks      weeks with status RES (reserve: IR / PUP / NFI / suspended-list)
      roster_wks   weeks with any row at all
      res_end      RES in the final three scheduled weeks  -> ONGOING absence
      act_end      ACT/INA in the final three scheduled weeks
      any_end      any row in the final three scheduled weeks (else: off-roster)
      wk_max       that season's max scheduled week

    `res_end` is the resolved-vs-ongoing instrument. It is NOT `week1_roster`:
    that reads season N and is the unadmitted G2a proxy. This reads season N-1
    and is ordinary lagged information.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rw = pd.read_sql_query(_RSTAT_SQL, conn, params=(max_season,))
    finally:
        conn.close()
    if len(rw) and (rw["season"] >= max_season).any():
        raise HoldoutViolation("roster-status rows leaked past the SQL gate")
    if not len(rw):
        return pd.DataFrame(columns=["player_id", "season", "act_wks", "res_wks",
                                     "roster_wks", "res_end", "act_end",
                                     "any_end", "wk_max"])
    rw["is_act"] = rw["status"].isin(_ON_ROSTER).astype(int)
    rw["is_res"] = (rw["status"] == "RES").astype(int)
    wk_max = rw.groupby("season")["week"].max().rename("wk_max")
    rw = rw.merge(wk_max, on="season")
    rw["late3"] = (rw["week"] > rw["wk_max"] - 3).astype(int)
    pw = rw.groupby(["player_id", "season", "week"], sort=False).agg(
        is_act=("is_act", "max"), is_res=("is_res", "max"),
        late3=("late3", "max"), wk_max=("wk_max", "max")).reset_index()
    pw["res_l3"] = pw["is_res"] * pw["late3"]
    pw["act_l3"] = pw["is_act"] * pw["late3"]
    return pw.groupby(["player_id", "season"], sort=False).agg(
        act_wks=("is_act", "sum"), res_wks=("is_res", "sum"),
        roster_wks=("week", "size"), res_end=("res_l3", "max"),
        act_end=("act_l3", "max"), any_end=("late3", "max"),
        wk_max=("wk_max", "max")).reset_index()


# ------------------------------------------------------------------ panel
@dataclass
class AvailPanel(V2Panel):
    """V2Panel plus the practice and roster-status frames, same gate discipline.

    Both accessors are `feature` reads -- season N-1 and earlier only -- so they
    go through `_gate` and never through the `proxy` tag. An arm using them can
    still assert `n_preseason_proxy_reads == 0` and prove it never touched
    `week1_roster`.
    """

    _practice: pd.DataFrame = field(default_factory=pd.DataFrame)
    _rstatus: pd.DataFrame = field(default_factory=pd.DataFrame)

    def _gated(self, frame: pd.DataFrame, cutoff: int, what: str) -> pd.DataFrame:
        self._gate(cutoff)
        out = frame[frame["season"] <= cutoff].copy() if len(frame) \
            else pd.DataFrame(columns=list(frame.columns) or ["player_id", "season"])
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation(f"{what} cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out

    def practice_before(self, cutoff: int) -> pd.DataFrame:
        return self._gated(self._practice, cutoff, "practice")

    def rstatus_before(self, cutoff: int) -> pd.DataFrame:
        return self._gated(self._rstatus, cutoff, "roster-status")


def build_avail_panel(db_path: Path = DEFAULT_DB,
                      feature_gate: int = HOLDOUT_SEASON,
                      outcome_gate: int = HOLDOUT_SEASON) -> AvailPanel:
    base = build_v2_panel(db_path, feature_gate=feature_gate,
                          outcome_gate=outcome_gate)
    return AvailPanel(
        base._frame, base._team, base._injury, base._depth, base.birthdates,
        base.draft, base._wk1, base._roster, base._coord, base._ngs, base._rush,
        feature_gate=base.feature_gate, outcome_gate=base.outcome_gate,
        _weekshape=base._weekshape,
        _practice=load_practice_seasons(db_path, max_season=feature_gate),
        _rstatus=load_roster_status_seasons(db_path, max_season=feature_gate))
