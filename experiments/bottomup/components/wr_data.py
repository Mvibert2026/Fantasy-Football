"""Data assembly for the WR component model.

LOOK-AHEAD DISCIPLINE IS STRUCTURAL IN THIS MODULE, NOT CONVENTIONAL.

`SeasonPanel.before(cutoff)` is the only way to reach player-season rows, and it
returns a copy filtered to `season <= cutoff` with an assertion. Nothing
downstream ever sees the full frame. `HOLDOUT_SEASON = 2025` is refused
outright: it is never loaded, never featured, never evaluated.

The universe for target season N is built by `universe_for(N)` from rows with
season <= N-1 plus the season-N draft class only -- i.e. from information that
existed before Week 1 of N. Players who then played zero snaps in N remain in
the universe and score 0. Building it from who produced would delete every bust.

DATA BOUNDARY, MEASURED NOT ASSUMED (this is the constraint that shapes the
whole design):
  - box-score stats: 1999+
  - targets:         1999-2002 and 2009+; 2003-2008 are effectively empty
                     (measured: WR target sums of 3, 1, 0, 29, 6, 5)
  - air yards / target share / air-yards share: 2009+ only
The strong feature set therefore has 2009-2024 = 16 seasons, of which the first
three are consumed as lags. That is 13 usable target seasons, not 26.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

_SRC = Path(__file__).resolve().parents[3] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scoring import score_offensive_game  # noqa: E402

HOLDOUT_SEASON = 2025          # sealed. never read, for features or outcomes.
FIRST_USAGE_SEASON = 2009      # air yards / target share become real here
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "nfl.db"

# Regular-season length by season -- known before Week 1, so legal as an input.
def season_length(season: int) -> int:
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
       COALESCE(passing_yards,0)        AS passing_yards,
       COALESCE(passing_tds,0)          AS passing_tds,
       COALESCE(passing_interceptions,0) AS interceptions,
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

_PASS_BONUS = ((300, 1.0), (350, 1.5), (400, 2.0))
_YDS_BONUS = ((100, 1.0), (150, 1.5), (200, 2.0))


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
    # Points under THIS league's rules, per game, bonuses stacked.
    stats = wk[list(_SCORING_KEYS)].to_dict("records")
    wk["points"] = [score_offensive_game(s) for s in stats]
    wk["rec_bonus"] = [_bonus(y, _YDS_BONUS) for y in wk["receiving_yards"]]
    return wk


def aggregate_seasons(wk: pd.DataFrame) -> pd.DataFrame:
    """Player-season aggregates, plus the per-game exceedance counts the
    stacking-bonus model needs (they cannot be recovered from season totals)."""
    wk = wk.copy()
    wk["g100"] = (wk["receiving_yards"] >= 100).astype(int)
    wk["g150"] = (wk["receiving_yards"] >= 150).astype(int)
    wk["g200"] = (wk["receiving_yards"] >= 200).astype(int)
    wk["rec_yd_sq"] = wk["receiving_yards"] ** 2

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
        fumbles_lost=("fumbles_lost", "sum"),
        return_tds=("return_tds", "sum"),
        two_pt=("two_point_conversions", "sum"),
        rec_bonus=("rec_bonus", "sum"),
        g100=("g100", "sum"),
        g150=("g150", "sum"),
        g200=("g200", "sum"),
        rec_yd_sq=("rec_yd_sq", "sum"),
    ).reset_index()

    # modal position and team
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
    return out


def team_target_totals(wk: pd.DataFrame) -> pd.DataFrame:
    """Team-season target totals -- the denominator for target share, computed
    from the same rows rather than trusting nflverse's per-week column (which is
    NULL before 2009 and is a per-week, not per-season, share)."""
    t = wk.groupby(["team", "season"], sort=False)["targets"].sum().reset_index()
    return t.rename(columns={"targets": "team_targets"})


# --------------------------------------------------------------- birthdates
def load_birthdates(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    # Birthdate is time-invariant, so a current-snapshot table is safe here --
    # it cannot encode anything about season N. `ff_playerids` carries both the
    # gsis id (the player_weekly_stats key) and the birthdate directly.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        m = pd.read_sql_query(
            "SELECT gsis_id AS player_id, birthdate FROM ff_playerids "
            "WHERE gsis_id IS NOT NULL AND birthdate IS NOT NULL", conn)
    finally:
        conn.close()
    return m.drop_duplicates("player_id")


def load_draft(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Draft capital. A season-N rookie's draft slot is April-of-N information,
    so it is legal as a season-N input."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(
            "SELECT gsis_id AS player_id, season AS draft_season, round AS draft_round, "
            "pick AS draft_pick, position AS draft_pos FROM draft_picks "
            "WHERE gsis_id IS NOT NULL", conn)
    finally:
        conn.close()
    return d.drop_duplicates("player_id")


# ------------------------------------------------------------------- panel
@dataclass
class SeasonPanel:
    """Player-season panel with a hard cutoff gate.

    The frame is private. `before(cutoff)` is the only accessor, and it asserts
    on the way out. There is deliberately no method that returns everything.
    """

    _frame: pd.DataFrame
    _team: pd.DataFrame
    birthdates: pd.DataFrame
    draft: pd.DataFrame
    # Audit trail. Every read records the highest season it could have seen, so
    # a look-ahead bug is detectable after the fact rather than only by review.
    access_log: List[tuple] = field(default_factory=list)

    def before(self, cutoff: int) -> pd.DataFrame:
        """Rows from seasons <= cutoff. `cutoff` is normally target_season - 1."""
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        out = self._frame[self._frame["season"] <= cutoff].copy()
        if len(out) and out["season"].max() > cutoff:
            raise CutoffViolation("cutoff gate failed")
        self.access_log.append(("feature", cutoff))
        return out

    def team_before(self, cutoff: int) -> pd.DataFrame:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        self.access_log.append(("feature", cutoff))
        return self._team[self._team["season"] <= cutoff].copy()

    def outcomes(self, season: int) -> pd.DataFrame:
        """Realised season-N results. ONLY for evaluation, never for features.
        Separate method so a look-ahead bug has to be written on purpose."""
        if season >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"season {season} is sealed")
        self.access_log.append(("outcome", season))
        return self._frame[self._frame["season"] == season].copy()

    def audit(self, target_season: int) -> Dict[str, int]:
        """Highest season reached by each access class since `reset_audit()`.

        For a legitimate season-N fit: every 'feature' read must be <= N-1, and
        every 'outcome' read used for TRAINING must be <= N-1. The single
        'outcome' read at N is the evaluation itself and is expected.
        """
        feat = [s for kind, s in self.access_log if kind == "feature"]
        outc = [s for kind, s in self.access_log if kind == "outcome"]
        return {
            "max_feature_cutoff": max(feat) if feat else -1,
            "max_outcome_season": max(outc) if outc else -1,
            "n_outcome_reads_at_target": sum(1 for s in outc if s == target_season),
        }

    def reset_audit(self) -> None:
        self.access_log.clear()

    @property
    def seasons(self) -> List[int]:
        return sorted(self._frame["season"].unique().tolist())


def build_panel(db_path: Path = DEFAULT_DB) -> SeasonPanel:
    wk = load_weekly(db_path)
    seasons = aggregate_seasons(wk)
    team = team_target_totals(wk)
    return SeasonPanel(seasons, team, load_birthdates(db_path), load_draft(db_path))


# ---------------------------------------------------------------- universe
MIN_PRIOR_TARGETS = 15   # "demonstrably an NFL receiver before season N"
ROOKIE_MAX_ROUND = 4     # rookie WRs with real draft capital


def universe_for(panel: SeasonPanel, target_season: int,
                 position: str = "WR",
                 extra_ids: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """The season-N player universe, frozen from pre-N information only.

    Inclusion (any one is sufficient):
      (a) >= MIN_PRIOR_TARGETS targets at `position` in season N-1 or N-2
      (b) drafted at `position` in rounds 1..ROOKIE_MAX_ROUND of the N draft
      (c) `extra_ids` -- used to add that season's pre-draft ADP board, which is
          itself dated strictly before Week 1 and so is legal pre-season
          information. Passing anything derived from season-N *results* here
          would be survivorship contamination; the caller owns that.

    Nothing here consults season N production. A player who is cut, retires or
    is injured all year stays in and scores 0 -- which is the point.

    `entry` is decided by whether the player has ANY pre-N NFL season, not by
    which rule admitted them, so the veteran/rookie sub-models always see the
    feature set they were fitted on.
    """
    hist = panel.before(target_season - 1)
    recent = hist[hist["season"].isin([target_season - 1, target_season - 2])]
    vets = recent[(recent["position"] == position)
                  & (recent["targets"] >= MIN_PRIOR_TARGETS)]
    ids = set(vets["player_id"].unique())

    rk = panel.draft
    rookies = rk[(rk["draft_season"] == target_season)
                 & (rk["draft_round"] <= ROOKIE_MAX_ROUND)
                 & (rk["draft_pos"] == position)]
    ids |= set(rookies["player_id"].dropna().unique())
    if extra_ids is not None:
        ids |= {p for p in extra_ids if isinstance(p, str) and p}

    seen_before = set(hist["player_id"].unique())
    u = pd.DataFrame({"player_id": sorted(ids)})
    u["entry"] = np.where(u["player_id"].isin(seen_before), "veteran", "rookie")
    u["season"] = target_season
    return u


def actual_points(panel: SeasonPanel, universe: pd.DataFrame,
                  target_season: int) -> pd.DataFrame:
    """Realised season-N points for the frozen universe. Absent => 0.0 points,
    0 games. Evaluation only."""
    out = panel.outcomes(target_season)
    keep = ["player_id", "points", "games", "targets", "receptions", "rec_yards",
            "rec_tds", "rec_bonus", "g100", "g150", "g200", "name", "position"]
    m = universe.merge(out[keep], on="player_id", how="left")
    for c in ["points", "games", "targets", "receptions", "rec_yards", "rec_tds",
              "rec_bonus", "g100", "g150", "g200"]:
        m[c] = m[c].fillna(0.0)
    return m
