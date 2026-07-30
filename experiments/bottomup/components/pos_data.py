"""Data assembly for the multi-position component model (RB / QB / TE / WR).

This is a superset of `wr_data.py`, not a replacement for it: `wr_data` is left
untouched so `run_wr` keeps reproducing pass 1 byte for byte, and every number in
`component-model-wr-pass-1.md` stays checkable against unchanged code.

WHAT IS NEW HERE, AND WHY EACH THING EXISTS

1. Passing components. QB scoring is a different ledger -- attempts, yards per
   attempt, TD rate, interception rate -- and the 300/350/400 passing bonuses are
   a THIRD bonus family with its own per-game exceedance counts.

2. Rushing exceedance counts. A running back collects 100/150/200 RUSHING
   bonuses, which the WR panel never counted because a receiver essentially never
   earns one. RB is where that channel is actually live.

3. The injury decomposition. `nfl.db.injuries` (79,816 rows) has never been read
   by any model in this project. It is the only thing in the database that can
   tell a season lost to injury apart from a season lost to being cut, and that
   distinction is WR pass 1's single largest error class.

DATA BOUNDARY, MEASURED NOT ASSUMED -- and it is NOT the same at every position:

  position | core volume stat | available          | usage analytics
  ---------|------------------|--------------------|-----------------
  QB       | pass attempts    | 1999+ COMPLETE     | air yards 2006+
  RB       | carries          | 1999+ COMPLETE     | targets 2009+ (gap 2003-08)
  WR/TE    | targets          | 2009+ (gap 2003-08)| 2009+

The 2003-2008 hole is a TARGETS hole. It does not touch passing or rushing
volume. That is why QB alone can be fitted on a deep sample, and it is a measured
fact about this database rather than an inherited assumption.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

_SRC = Path(__file__).resolve().parents[3] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scoring import score_offensive_game  # noqa: E402

HOLDOUT_SEASON = 2025          # sealed. never read, for features or outcomes.
FIRST_USAGE_SEASON = 2009      # targets / air yards become real here
FIRST_INJURY_SEASON = 2010     # measured: 2009 has 17 rows, i.e. nothing
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "nfl.db"


def season_length(season: int) -> int:
    """Regular-season length. Known before Week 1, so legal as an input."""
    return 17 if season >= 2021 else (16 if season >= 1978 else 14)


class HoldoutViolation(Exception):
    pass


class CutoffViolation(Exception):
    pass


_WEEK_SQL = """
SELECT player_id, player_display_name AS name, position, season, week, team,
       COALESCE(targets,0)              AS targets,
       COALESCE(receptions,0)           AS receptions,
       COALESCE(receiving_yards,0)      AS receiving_yards,
       COALESCE(receiving_tds,0)        AS receiving_tds,
       COALESCE(receiving_air_yards,0)  AS receiving_air_yards,
       COALESCE(carries,0)              AS carries,
       COALESCE(rushing_yards,0)        AS rushing_yards,
       COALESCE(rushing_tds,0)          AS rushing_tds,
       COALESCE(attempts,0)             AS attempts,
       COALESCE(completions,0)          AS completions,
       COALESCE(passing_yards,0)        AS passing_yards,
       COALESCE(passing_tds,0)          AS passing_tds,
       COALESCE(passing_interceptions,0) AS interceptions,
       COALESCE(sacks_suffered,0)       AS sacks,
       COALESCE(fumbles_lost_total,0)   AS fumbles_lost,
       COALESCE(special_teams_tds,0)    AS return_tds,
       (COALESCE(passing_2pt_conversions,0)+COALESCE(rushing_2pt_conversions,0)
        +COALESCE(receiving_2pt_conversions,0)) AS two_point_conversions,
       COALESCE(fumble_recovery_tds,0)  AS offensive_fumble_return_tds
FROM player_weekly_stats
WHERE season_type = 'REG' AND season < ?
  AND position IN ('QB','RB','WR','TE','FB')
"""

_SCORING_KEYS = (
    "passing_yards", "passing_tds", "interceptions", "rushing_yards",
    "rushing_tds", "receptions", "receiving_yards", "receiving_tds",
    "fumbles_lost", "return_tds", "two_point_conversions",
    "offensive_fumble_return_tds",
)

# The three bonus families this league actually pays, all stacking.
PASS_BONUS = ((300, 1.0), (350, 1.5), (400, 2.0))
YDS_BONUS = ((100, 1.0), (150, 1.5), (200, 2.0))


def _bonus(yards: float, table) -> float:
    return sum(b for t, b in table if yards >= t)


def load_weekly(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Every REG-season offensive player-week strictly before the holdout."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        wk = pd.read_sql_query(_WEEK_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if (wk["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("holdout rows leaked past the SQL gate")
    stats = wk[list(_SCORING_KEYS)].to_dict("records")
    wk["points"] = [score_offensive_game(s) for s in stats]
    wk["rec_bonus"] = [_bonus(y, YDS_BONUS) for y in wk["receiving_yards"]]
    wk["rush_bonus"] = [_bonus(y, YDS_BONUS) for y in wk["rushing_yards"]]
    wk["pass_bonus"] = [_bonus(y, PASS_BONUS) for y in wk["passing_yards"]]
    return wk


def aggregate_seasons(wk: pd.DataFrame) -> pd.DataFrame:
    """Player-season aggregates plus per-game exceedance counts for all three
    bonus families. The counts cannot be recovered from season totals -- that is
    the entire reason a component model carries a per-game distribution."""
    wk = wk.copy()
    for t in (100, 150, 200):
        wk[f"g{t}"] = (wk["receiving_yards"] >= t).astype(int)
        wk[f"r{t}"] = (wk["rushing_yards"] >= t).astype(int)
    for t in (300, 350, 400):
        wk[f"p{t}"] = (wk["passing_yards"] >= t).astype(int)

    agg = wk.groupby(["player_id", "season"], sort=False).agg(
        games=("week", "size"),
        points=("points", "sum"),
        targets=("targets", "sum"),
        receptions=("receptions", "sum"),
        rec_yards=("receiving_yards", "sum"),
        rec_tds=("receiving_tds", "sum"),
        air_yards=("receiving_air_yards", "sum"),
        carries=("carries", "sum"),
        rush_yards=("rushing_yards", "sum"),
        rush_tds=("rushing_tds", "sum"),
        attempts=("attempts", "sum"),
        completions=("completions", "sum"),
        pass_yards=("passing_yards", "sum"),
        pass_tds=("passing_tds", "sum"),
        interceptions=("interceptions", "sum"),
        sacks=("sacks", "sum"),
        fumbles_lost=("fumbles_lost", "sum"),
        return_tds=("return_tds", "sum"),
        two_pt=("two_point_conversions", "sum"),
        rec_bonus=("rec_bonus", "sum"),
        rush_bonus=("rush_bonus", "sum"),
        pass_bonus=("pass_bonus", "sum"),
        g100=("g100", "sum"), g150=("g150", "sum"), g200=("g200", "sum"),
        r100=("r100", "sum"), r150=("r150", "sum"), r200=("r200", "sum"),
        p300=("p300", "sum"), p350=("p350", "sum"), p400=("p400", "sum"),
    ).reset_index()

    def _mode(s: pd.Series) -> str:
        m = s.mode()
        return m.iloc[0] if len(m) else ""

    meta = wk.groupby(["player_id", "season"], sort=False).agg(
        position=("position", _mode),
        team=("team", _mode),
        name=("name", "first"),
    ).reset_index()
    out = agg.merge(meta, on=["player_id", "season"], how="left")
    out["season_len"] = out["season"].map(season_length)
    out["total_bonus"] = out["rec_bonus"] + out["rush_bonus"] + out["pass_bonus"]
    return out


def team_context(wk: pd.DataFrame) -> pd.DataFrame:
    """Team-season denominators. Target share needs team targets; RB opportunity
    share needs team carries. Computed from these rows rather than trusting
    nflverse's per-week share columns, which are NULL before 2009."""
    t = wk.groupby(["team", "season"], sort=False).agg(
        team_targets=("targets", "sum"),
        team_carries=("carries", "sum"),
        team_attempts=("attempts", "sum"),
    ).reset_index()
    return t


# ------------------------------------------------------------------ injuries
_INJ_SQL = """
SELECT CAST(season AS INTEGER) AS season, gsis_id AS player_id,
       CAST(week AS INTEGER) AS week, report_status
FROM injuries
WHERE game_type = 'REG' AND gsis_id IS NOT NULL AND gsis_id <> ''
  AND season < ?
"""


def load_injury_seasons(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season): how many REG weeks carried an injury report, and how
    many carried one that ruled the player out.

    `report_status` is the NFL's own game-status designation. `Out` and
    `Doubtful` are the two that mean "did not/almost certainly did not play";
    `Questionable` and `Probable` mean the opposite and are deliberately NOT
    counted, or every star with a Thursday ankle tweak would look absent.

    WHAT THIS CANNOT SEE, stated here rather than discovered later: a SUSPENDED
    player files no injury report. Suspension absence is invisible to this table
    and lands in the "missed with no report" bucket next to players who were
    simply cut. This feature addresses injury absence only.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        inj = pd.read_sql_query(_INJ_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(inj) and (inj["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("injury holdout rows leaked past the SQL gate")
    inj["is_out"] = inj["report_status"].isin(["Out", "Doubtful"]).astype(int)  # noqa: E501
    # distinct weeks: a traded player can appear twice in a week under two teams
    wk = inj.groupby(["player_id", "season", "week"], sort=False)["is_out"].max()
    wk = wk.reset_index()
    out = wk.groupby(["player_id", "season"], sort=False).agg(
        inj_report_wks=("week", "size"),
        inj_out_wks=("is_out", "sum"),
    ).reset_index()
    return out


_DEPTH_SQL = """
SELECT gsis_id AS player_id, season, week, depth_team
FROM depth_charts_weekly
WHERE game_type = 'REG' AND gsis_id IS NOT NULL AND gsis_id <> ''
  AND week IS NOT NULL AND season < ?
"""


def load_depth_seasons(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season): weeks the player appeared on his team's REG-season
    depth chart, and weeks he was listed first at his position.

    WHY THIS EXISTS, measured not assumed. The injury report was the obvious
    source for "why was this player absent" and it turns out to answer the
    question backwards: it covers 26-35% of missed weeks for short absences and
    **2.5-4.8% for absences of nine games or more** -- because a player placed on
    season-ending IR drops off the weekly report entirely. The absences that
    wreck a projection are precisely the ones it cannot see.

    A depth-chart appearance covers 36-97% of the same missed weeks. It does not
    say WHY a player was absent -- injury, suspension, benching and inactive all
    look alike -- but it does separate "on the roster and unavailable" from "not
    in the league", which is the distinction the availability model was missing.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dc = pd.read_sql_query(_DEPTH_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(dc) and (dc["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("depth-chart holdout rows leaked past the SQL gate")
    dc["is_first"] = (dc["depth_team"].astype(str) == "1").astype(int)
    wk = dc.groupby(["player_id", "season", "week"], sort=False)["is_first"].max()
    wk = wk.reset_index()
    return wk.groupby(["player_id", "season"], sort=False).agg(
        depth_wks=("week", "size"), depth_first_wks=("is_first", "sum"),
    ).reset_index()


# ------------------------------------------------------------------- panel
@dataclass
class SeasonPanel:
    """Player-season panel with a hard cutoff gate.

    The frame is private. `before(cutoff)` is the only accessor and it asserts on
    the way out. There is deliberately no method that returns everything, and
    `outcomes(season)` is a separate method so that reading a target season has to
    be written on purpose. Every read appends to an access log so a look-ahead bug
    is detectable after the fact rather than only by review.
    """

    _frame: pd.DataFrame
    _team: pd.DataFrame
    _injury: pd.DataFrame
    _depth: pd.DataFrame
    birthdates: pd.DataFrame
    draft: pd.DataFrame
    _wk1: pd.DataFrame = field(default_factory=pd.DataFrame)
    # factor batch 2, 2026-07-30 -- the two inputs the founder's own insight
    # examples need. Both are season-N reads and both log under the SAME `proxy`
    # audit tag as `_wk1`, so every assertion already written against
    # `n_preseason_proxy_reads == 0` keeps working unchanged and an arm that did
    # not declare them can still be proven not to have touched them.
    _roster: pd.DataFrame = field(default_factory=pd.DataFrame)
    _coord: pd.DataFrame = field(default_factory=pd.DataFrame)
    access_log: List[tuple] = field(default_factory=list)

    def _gate(self, cutoff: int) -> None:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")

    def before(self, cutoff: int) -> pd.DataFrame:
        self._gate(cutoff)
        out = self._frame[self._frame["season"] <= cutoff].copy()
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation("cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out

    def team_before(self, cutoff: int) -> pd.DataFrame:
        self._gate(cutoff)
        self.access_log.append(("feature", cutoff))
        return self._team[self._team["season"] <= cutoff].copy()

    def injury_before(self, cutoff: int) -> pd.DataFrame:
        self._gate(cutoff)
        out = self._injury[self._injury["season"] <= cutoff].copy()
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation("injury cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out

    def depth_before(self, cutoff: int) -> pd.DataFrame:
        self._gate(cutoff)
        out = self._depth[self._depth["season"] <= cutoff].copy()
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation("depth-chart cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out

    def week1_roster(self, season: int) -> pd.DataFrame:
        """PROXY ONLY. Who was on each club's season-N Week-1 depth chart.

        THIS IS NOT A `before()` READ AND IT IS NOT PRETENDING TO BE ONE. It is
        season-N information, dated at Week 1 -- roughly a week AFTER a real
        draft and therefore later than CLAUDE.md 6.1's "preseason N" bound. It
        exists because `nfl.db` contains no pre-season roster table at all
        (`depth_charts_snapshots` is a single 2026-03-14 snapshot; there is no
        `rosters` table), and the only alternative for "who left this team" --
        inferring departure from who appears in season-N box scores -- is
        outright survivorship contamination.

        It carries NO season-N production, so it cannot inflate an outcome. Its
        one known leak channel is that a player injured in Week 1 may be off the
        chart and be miscounted as departed.

        Reads are logged under their own `proxy` tag so the audit can assert that
        an arm which did not declare the proxy never touched it.
        """
        self._gate(season)
        self.access_log.append(("proxy", season))
        if not len(self._wk1):
            return pd.DataFrame(columns=["player_id", "season", "team"])
        return self._wk1[self._wk1["season"] == season].copy()

    def preseason_roster(self, season: int) -> pd.DataFrame:
        """Club membership at season-N Week 1, from `rosters_weekly`.

        THE FIX FOR `week1_roster`, NOT A SECOND COPY OF IT. Both are dated at
        Week 1 of season N; the difference is what they can see. A depth chart
        lists only players the club chose to rank, so a player on IR, on PUP,
        suspended, or simply on the bench behind three others is ABSENT from it
        and reads as departed. The roster lists everyone under contract WITH A
        STATUS CODE, so "still this club's player but unavailable" and "gone" are
        different rows rather than the same silence.

        Measured on this repo's own data (target seasons 2014-2024, players with
        >=50 carries or >=50 targets the prior season): the depth chart calls 91
        of 2,166 such players departed while the roster still has them under
        contract -- 40 of those on reserve/injured. That is the leak channel
        `docs/ranking/factor-batch-1-results.md` §4 hypothesised, now counted.

        Still a season-N read, still logged under `proxy`. Week-1 roster status
        is set at the late-August cutdown, i.e. around a real draft rather than
        strictly before it. Nothing here is backdated to look earlier than it is.
        """
        self._gate(season)
        self.access_log.append(("proxy", season))
        if not len(self._roster):
            return pd.DataFrame(columns=["player_id", "season", "team", "status",
                                         "under_contract", "available"])
        return self._roster[self._roster["season"] == season].copy()

    def preseason_coordinators(self, season: int) -> pd.DataFrame:
        """Who was calling the offence for each club GOING INTO season N.

        Sourced from the pre-Week-1 revision of each club's Wikipedia staff
        navbox (`experiments/bottomup/factors/coord_preseason.py`), NOT from the
        end-of-season `{{NFL final staff}}` rows in `play_callers` -- those name
        the replacement in any season with a mid-year firing, and a mid-year
        firing is caused by the season going badly, which is the exact direction
        that manufactures fake signal.

        Season-N dated, so it logs under `proxy` like the roster read.
        """
        self._gate(season)
        self.access_log.append(("proxy", season))
        if not len(self._coord):
            return pd.DataFrame(columns=["team", "season", "title", "coach_id",
                                         "head_coach"])
        return self._coord[self._coord["season"] == season].copy()

    def outcomes(self, season: int) -> pd.DataFrame:
        """Realised season-N results. ONLY for evaluation and for training on
        seasons strictly earlier than the one being projected."""
        if season >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"season {season} is sealed")
        self.access_log.append(("outcome", season))
        return self._frame[self._frame["season"] == season].copy()

    def audit(self, target_season: int) -> Dict[str, int]:
        feat = [s for kind, s in self.access_log if kind == "feature"]
        outc = [s for kind, s in self.access_log if kind == "outcome"]
        prox = [s for kind, s in self.access_log if kind == "proxy"]
        return {
            "max_feature_cutoff": max(feat) if feat else -1,
            "max_outcome_season": max(outc) if outc else -1,
            "n_outcome_reads_at_target": sum(1 for s in outc if s == target_season),
            "n_preseason_proxy_reads": len(prox),
            "max_proxy_season": max(prox) if prox else -1,
        }

    def reset_audit(self) -> None:
        self.access_log.clear()

    @property
    def seasons(self) -> List[int]:
        return sorted(self._frame["season"].unique().tolist())


def load_birthdates(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Birthdate is time-invariant, so a current-snapshot table cannot encode
    anything about season N. No leakage path exists here."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        m = pd.read_sql_query(
            "SELECT gsis_id AS player_id, birthdate FROM ff_playerids "
            "WHERE gsis_id IS NOT NULL AND birthdate IS NOT NULL", conn)
    finally:
        conn.close()
    return m.drop_duplicates("player_id")


def load_draft(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """A season-N rookie's draft slot is April-of-N information, so it is legal
    as a season-N input."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(
            "SELECT gsis_id AS player_id, season AS draft_season, round AS draft_round, "
            "pick AS draft_pick, position AS draft_pos FROM draft_picks "
            "WHERE gsis_id IS NOT NULL", conn)
    finally:
        conn.close()
    return d.drop_duplicates("player_id")


# Franchise relocations. `player_weekly_stats` is already normalised to the
# current code; `depth_charts_weekly.club_code` is not.
_CLUB_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

_WK1_SQL = """
SELECT season, club_code, gsis_id AS player_id, week
FROM depth_charts_weekly
WHERE game_type = 'REG' AND week IS NOT NULL AND week <= 3
  AND gsis_id IS NOT NULL AND gsis_id <> '' AND season < ?
"""


def load_week1_rosters(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Season-N Week-1 club membership, from the depth chart. PROXY -- see
    `SeasonPanel.week1_roster` for exactly what it is and is not.

    Week 1 where the club has one, else the earliest REG week it does have up to
    week 3. Two clubs are missing a Week-1 chart in 2017; without the fallback
    their entire roster would read as departed, which is a far larger error than
    the two extra weeks of staleness the fallback costs.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dc = pd.read_sql_query(_WK1_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(dc):
        return pd.DataFrame(columns=["player_id", "season", "team"])
    if (dc["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("week-1 roster holdout rows leaked past the SQL gate")
    dc["team"] = dc["club_code"].astype(str).replace(_CLUB_ALIAS)
    first = dc.groupby(["season", "team"], sort=False)["week"].transform("min")
    dc = dc[dc["week"] == first]
    out = dc[["player_id", "season", "team"]].drop_duplicates()
    out["proxy_week"] = dc.loc[out.index, "week"].to_numpy()
    return out.reset_index(drop=True)


# --------------------------------------------------------- factor batch 2
# nflverse weekly-roster status codes, split ONCE, on what the code means rather
# than on which split scored better. Two questions, two answers, both registered:
#
#   under_contract -- is this still the club's player entering Week 1? The
#                     founder's "the starter from last year left" is this one.
#   available      -- could he take a snap in Week 1? Adds IR / PUP / suspended /
#                     practice squad to the vacated side.
#
# A code seen in the data but absent from both sets is treated as NOT under
# contract and NOT available, and `unknown_status_codes()` reports it rather than
# letting it pass silently.
_STATUS_UNDER_CONTRACT = frozenset({
    "ACT", "INA", "RES", "DEV", "PUP", "SUS", "RSN", "EXE", "E14", "E01", "NFI",
})
_STATUS_AVAILABLE = frozenset({"ACT", "INA"})
# Separation codes: no longer the club's player at Week 1. Listed explicitly so
# that `unknown_status_codes()` flags a code nobody has classified rather than
# reporting every separation as unknown.
_STATUS_SEPARATED = frozenset({
    "CUT", "UFA", "RFA", "RET", "NWT", "TRC", "TRD", "TRT", "RSR", "UDF",
})

_ROSTER_SQL = """
SELECT season, team, gsis_id AS player_id, status
FROM rosters_weekly
WHERE week = 1 AND game_type = 'REG' AND season < ?
  AND gsis_id IS NOT NULL AND gsis_id <> ''
"""


def load_preseason_rosters(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Season-N Week-1 club membership WITH STATUS. See
    `SeasonPanel.preseason_roster` for exactly what it is and is not."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        r = pd.read_sql_query(_ROSTER_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(r):
        return pd.DataFrame(columns=["player_id", "season", "team", "status",
                                     "under_contract", "available"])
    if (r["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("roster holdout rows leaked past the SQL gate")
    r["team"] = r["team"].astype(str).replace(_CLUB_ALIAS)
    s = r["status"].astype(str).str.upper().str.strip()
    r["status"] = s
    r["under_contract"] = s.isin(_STATUS_UNDER_CONTRACT).astype(int)
    r["available"] = s.isin(_STATUS_AVAILABLE).astype(int)
    # one row per (player, season, team): a player can appear twice in a week if
    # a status changed; keep the most-attached row so a stale CUT does not erase
    # a live ACT.
    r = r.sort_values(["under_contract", "available"], ascending=False)
    return r.drop_duplicates(["player_id", "season", "team"]).reset_index(drop=True)


def unknown_status_codes(roster: pd.DataFrame) -> pd.Series:
    """Status codes in the data that neither set claims. Reported, never ignored."""
    known = _STATUS_UNDER_CONTRACT | _STATUS_AVAILABLE | _STATUS_SEPARATED
    unk = roster.loc[~roster["status"].isin(known), "status"]
    return unk.value_counts()


_COORD_SQL = """
SELECT team, season, title, coach_id, head_coach, as_of_date
FROM play_callers_preseason
WHERE season < ? AND title = 'OC'
"""


def load_preseason_coordinators(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Pre-Week-1 offensive coordinator per club. Empty frame (not an error) if
    the research table has not been built -- an arm that needs it then produces
    all-null features and says so, rather than silently using something else."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            co = pd.read_sql_query(_COORD_SQL, conn, params=(HOLDOUT_SEASON,))
        except Exception:
            return pd.DataFrame(columns=["team", "season", "title", "coach_id",
                                         "head_coach", "as_of_date"])
    finally:
        conn.close()
    if len(co):
        if (co["season"] >= HOLDOUT_SEASON).any():
            raise HoldoutViolation("coordinator holdout rows leaked past the SQL gate")
        co["team"] = co["team"].astype(str).replace(_CLUB_ALIAS)
    return co


def build_panel(db_path: Path = DEFAULT_DB) -> SeasonPanel:
    wk = load_weekly(db_path)
    return SeasonPanel(
        aggregate_seasons(wk), team_context(wk), load_injury_seasons(db_path),
        load_depth_seasons(db_path), load_birthdates(db_path), load_draft(db_path),
        load_week1_rosters(db_path), load_preseason_rosters(db_path),
        load_preseason_coordinators(db_path))


# ---------------------------------------------------------------- universe
@dataclass(frozen=True)
class PositionSpec:
    """Everything that is genuinely position-specific about admission.

    `qual_col`/`qual_min` is the "demonstrably an NFL <position> before season N"
    test. It is a VOLUME test on the stat that position is paid for, not a
    production test -- a back who carried 60 times for 140 yards is in the
    universe and will score badly, which is the point.
    """

    position: str
    qual_col: str
    qual_min: int
    rookie_max_round: int = 4


POSITION_SPECS: Dict[str, PositionSpec] = {
    "WR": PositionSpec("WR", "targets", 15),
    "TE": PositionSpec("TE", "targets", 15),
    "RB": PositionSpec("RB", "carries", 25),
    "QB": PositionSpec("QB", "attempts", 30),
}


def universe_for(panel: SeasonPanel, target_season: int, position: str,
                 extra_ids: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """The season-N player universe, frozen from pre-N information only.

    Inclusion (any one suffices):
      (a) cleared the position's volume bar in N-1 or N-2
      (b) drafted at the position in rounds 1..4 of the N draft
      (c) `extra_ids` -- that season's pre-draft ADP board, itself dated strictly
          before Week 1. Passing anything derived from season-N RESULTS here would
          be survivorship contamination; the caller owns that.

    Nothing consults season-N production. A player cut, retired or injured all
    year stays in and scores 0.
    """
    spec = POSITION_SPECS[position]
    hist = panel.before(target_season - 1)
    recent = hist[hist["season"].isin([target_season - 1, target_season - 2])]
    vets = recent[(recent["position"] == position)
                  & (recent[spec.qual_col] >= spec.qual_min)]
    ids = set(vets["player_id"].unique())

    rk = panel.draft
    rookies = rk[(rk["draft_season"] == target_season)
                 & (rk["draft_round"] <= spec.rookie_max_round)
                 & (rk["draft_pos"] == position)]
    ids |= set(rookies["player_id"].dropna().unique())
    if extra_ids is not None:
        ids |= {p for p in extra_ids if isinstance(p, str) and p}

    seen_before = set(hist["player_id"].unique())
    u = pd.DataFrame({"player_id": sorted(ids)})
    u["entry"] = np.where(u["player_id"].isin(seen_before), "veteran", "rookie")
    u["season"] = target_season
    u["position"] = position
    return u
