"""Standalone predictiveness screen 1 -- founder's idea, model-independent.

============================================================================
NEXT STEP (read this first)
============================================================================
This file is SELF-CONTAINED and does NOT import `experiments/bottomup/v2/
factors_c1.py`/`factors_c2.py`/`factors_c3.py`/`run_c1.py`/`sweep070/` etc.
Verified before writing a line of this file: this worktree's `git log` is
byte-identical to `origin/main` (both at `fd3bed1`), and `experiments/
bottomup/v2/` does not exist anywhere in this worktree's tracked tree --
`ls experiments/bottomup/v2` fails. Those files DO exist, uncommitted, in
the coordinator's "main checkout" (a sibling working directory sharing this
repo's `.git`, per `docs/environment.md`'s worktree-isolation model) where a
ranker session and another backend session are actively writing them
(`run_c4.py`/`factors_c4.py`, `sweep070/`), per this task's own dispatch:
"do not touch it, the manifest, or factors_c1/c2/c3.py ... another backend
agent is writing factors_c4.py". Reading those files earlier in this session
(via the coordinator's shared filesystem access) informed this file's
factor MECHANISMS and DISCIPLINE (lag-weighting, `*_known` companions,
look-ahead gating) but every line of code below is independently written
against tables reachable from THIS worktree's own `data/nfl.db` copy and
THIS worktree's own committed `experiments/bottomup/components/{pos_data,
pos_features}.py` -- nothing here imports, edits, or depends on the
in-flight `v2/factors_c*.py` files. When those land on `main` and this
branch merges, there is no collision: this file's name and directory
(`v2/standalone_screen1.py`) does not exist in either concurrent effort.

============================================================================
WHAT THIS IS, AND WHAT IT IS NOT
============================================================================
Every factor batch (C1/C2/C3/C4/factor_features1-7) tests whether adding a
factor to a FITTED v2 walk-forward model changes that model's ordering.
This script asks a cheaper, prior, model-independent question: on its own,
does a factor value (constructible before Week 1 of season N) carry ANY
rank relationship to realised season-N fantasy points?

**This screen makes no decisions and grades nothing.** There is no INCLUDE
or EXCLUDE anywhere in this output. Nothing here enters any campaign
multiplicity denominator, because nothing is decided. Per the founder's
mid-session redirection, the deliverable is now also an input to a future
joint multivariate fit (v3): a SURVIVOR SET (inclusive, not pre-selecting
winners -- regularisation in that fit decides weight) and a COLLINEARITY
MAP (diagnostic for that fit, not a pruning instrument here).

============================================================================
THE CONTROL-VALIDITY CORRECTION (founder, mid-session)
============================================================================
Prior-season fantasy points is a deterministic function of last year's
targets, receptions, yards, TDs and games. For a factor that is a
CONSTITUENT of that box score (snap share, red-zone usage, WOPR, YAC/rec,
role trajectory, a player's own receiving-points share, QB rush attempts),
partialling out prior-season points removes most of the factor's variance
BY CONSTRUCTION -- a near-zero partial there is an arithmetic artifact, not
a null finding. Partialling is a valid predictiveness test only for
EXOGENOUS factors (outside last year's box score entirely: age/draft
capital/combine, scheme/coaching context, injury/practice history,
depth-chart role). Every factor carries an explicit CLASS tag, assigned
BEFORE any number below was computed:

  EXOGENOUS   -> partial-beyond-prior-points is the headline.
  CONSTITUENT -> "does the decomposition beat the aggregate?" is the
                 headline: raw rho of factor vs. raw rho of prior-season
                 points, SAME matched population. Partial is printed but
                 flagged uninterpretable-as-predictiveness for this class.
  AMBIGUOUS   -> both reported, neither privileged.

Both raw and controlled numbers are printed for EVERY factor, always.

============================================================================
COLLINEARITY -- DIAGNOSTIC, NOT A FILTER (founder's second correction)
============================================================================
"There is some collinearity. And sometimes it is predictive." The map below
does NOT prune anything. Two factors correlated at r=0.8 still carry ~36%
independent variance and that remainder is frequently where the
information is; manual pruning on a threshold would discard it
permanently -- regularisation in the joint fit is the right instrument.
For every TIGHT cluster found (|rho| >= 0.6 within a position), this script
also constructs and screens the WITHIN-CLUSTER CONTRAST (percentile-rank
gap: high-A-low-B is a role signal the raw components individually wash
out) -- e.g. high snap share / low red-zone share is a between-the-tackles
non-scoring role. These contrasts are reported as their own candidate rows,
same treatment as every other factor, not as a replacement for the pair.

============================================================================
DISCIPLINE
============================================================================
- Screens ONLY 2013-2019 (`SCREEN_SEASONS`). 2020-2024 untouched here.
  Sealed 2025 holdout never read (`HOLDOUT_SEASON = 2025` gates every SQL
  read via `season < ?`).
- Every factor value is constructed from data strictly BEFORE the target
  season (lag-1 or up-to-3-lag weighted) -- never week-1-of-target status.
- A seeded-noise placebo runs through the identical pipeline per position,
  the falsifiability instrument this project's own history (C1: 14.6%
  false-positive rate on an unguarded rule) says is mandatory.
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats as sstats

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components.pos_data import (   # noqa: E402
    DEFAULT_DB, HOLDOUT_SEASON, aggregate_seasons, load_weekly, season_length,
)
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS  # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
OUT.mkdir(parents=True, exist_ok=True)

SCREEN_SEASONS: Tuple[int, ...] = (2013, 2014, 2015, 2016, 2017, 2018, 2019)
POSITIONS: Tuple[str, ...] = ("QB", "RB", "WR", "TE")
DB = DEFAULT_DB

INJURIES_FIRST = 2010   # measured floor: 2009 has 17 rows total, not coverage
DEPTH_FIRST = 2001
COMBINE_FIRST = 2000
PBP_FIRST = 2009
FF_OPP_FIRST = 2006
PRACTICE_K0_WEEKS = 8.0
YOE_K0_OPPORTUNITIES = 40.0

# ---------------------------------------------------------------------------
# Factor classification, fixed BEFORE any number below was computed.
# ---------------------------------------------------------------------------
FACTOR_CLASS: Dict[str, str] = {
    "placebo":              "EXOGENOUS",
    "injury_burden":        "EXOGENOUS",
    "practice_severity":    "EXOGENOUS",
    "depth_end_rank":       "EXOGENOUS",
    "combine_z":             "EXOGENOUS",
    "neutral_pass_rate":     "EXOGENOUS",
    "yoe_rate":               "CONSTITUENT",
    "wopr":                   "CONSTITUENT",
    "snap_share":             "CONSTITUENT",
    "redzone_share":          "CONSTITUENT",
    "yac_per_rec":             "CONSTITUENT",
    "rb_receiving_share":      "CONSTITUENT",
    "late_season_trend":       "CONSTITUENT",
    "qb_rush_att_pg":          "CONSTITUENT",
    "explosive_rush_rate":     "AMBIGUOUS",
}

APPLICABLE_POSITIONS: Dict[str, Tuple[str, ...]] = {
    "placebo":               POSITIONS,
    "injury_burden":         POSITIONS,
    "practice_severity":     POSITIONS,
    "depth_end_rank":        POSITIONS,
    "combine_z":              POSITIONS,
    "neutral_pass_rate":      POSITIONS,
    "yoe_rate":                POSITIONS,
    "wopr":                    ("WR", "TE"),
    "snap_share":              ("RB", "WR", "TE"),
    "redzone_share":           ("RB", "WR", "TE"),
    "yac_per_rec":              ("RB", "WR", "TE"),
    "rb_receiving_share":       ("RB",),
    "late_season_trend":        ("RB", "WR", "TE"),
    "qb_rush_att_pg":           ("QB",),
    "explosive_rush_rate":      ("RB",),
}


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


# ===========================================================================
# 1. OUTCOME PANEL
# ===========================================================================
def build_points_panel() -> pd.DataFrame:
    wk = load_weekly(DB, max_season=HOLDOUT_SEASON)
    sp = aggregate_seasons(wk)
    return sp[["player_id", "season", "position", "team", "games", "points",
               "rec_yards", "receptions", "rec_bonus", "rec_tds"]]


def universe_for(points: pd.DataFrame, position: str, season: int) -> pd.DataFrame:
    """STATED LIMITATION: players who played >=1 game that season at that
    position -- not a pre-season ADP/roster universe. Undercounts total busts
    who never accrued a game (CLAUDE.md SS6.2 survivorship risk), not solved
    here; repeated in the write-up."""
    u = points[(points["position"] == position) & (points["season"] == season)
               & (points["games"] >= 1)]
    return u[["player_id", "season", "team", "points", "games"]].copy()


def prior_points_lookup(points: pd.DataFrame) -> pd.DataFrame:
    """(player_id, season) -> points scored in season-1. Labelled by the
    season it serves as a PRIOR for (season+1 of the original row), so the
    caller merges on (player_id, season) directly with no further shift --
    this is the fix for a bug caught in this session's own QA: the first
    draft of this function relabelled a row's OWN season as `prior_season`
    without shifting it, so every factor's partial/beats-aggregate number
    was computed against a same-season points duplicate (rho ~1.0) instead
    of a real lag. Caught before any number in the write-up was drawn from
    it -- see the write-up's Data-quality note."""
    p = points.groupby(["player_id", "season"], as_index=False)["points"].sum()
    p = p.copy()
    p["season"] = p["season"] + 1
    return p.rename(columns={"points": "prior_points"})


def _median_fill(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


def _lag_weighted(values_by_lag: List[np.ndarray]) -> np.ndarray:
    n = len(values_by_lag[0])
    num = np.zeros(n); den = np.zeros(n)
    for k in range(min(N_LAGS, len(values_by_lag))):
        v = np.asarray(values_by_lag[k], dtype=float)
        present = np.isfinite(v)
        num[present] += LAG_WEIGHTS[k] * v[present]
        den[present] += LAG_WEIGHTS[k]
    out = np.full(n, np.nan)
    have = den > 0
    out[have] = num[have] / den[have]
    return out


def attach_3lag(req: pd.DataFrame, season_vals: pd.DataFrame, value_col: str,
                out_col: str, min_season: int) -> pd.DataFrame:
    """`season_vals`: columns player_id, season, value_col. 3-lag weighted
    attach, unknown-fill = median of what IS known."""
    base = req[["player_id", "season"]].drop_duplicates().copy()
    lag_vals, lag_known = [], []
    for k in range(1, N_LAGS + 1):
        j = base.copy(); j["lag_season"] = j["season"] - k
        m = j.merge(season_vals.rename(columns={"season": "lag_season"}),
                    on=["player_id", "lag_season"], how="left")
        v = m[value_col].to_numpy(dtype=float)
        known = np.isfinite(v) & (j["lag_season"].to_numpy() >= min_season)
        lag_vals.append(v); lag_known.append(known)
    w = _median_fill(_lag_weighted(lag_vals))
    known_any = np.any(np.column_stack(lag_known), axis=1).astype(int)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          out_col: w, f"{out_col}_known": known_any})


def attach_lag1(req: pd.DataFrame, raw: pd.DataFrame, value_col: str,
                out_col: str, min_season: int) -> pd.DataFrame:
    j = req[["player_id", "season"]].drop_duplicates().copy()
    j["lag_season"] = j["season"] - 1
    m = j.merge(raw.rename(columns={"season": "lag_season"}),
                on=["player_id", "lag_season"], how="left")
    v = m[value_col].to_numpy(dtype=float)
    known = np.isfinite(v) & (j["lag_season"].to_numpy() >= min_season)
    return pd.DataFrame({"player_id": j["player_id"].to_numpy(),
                          "season": j["season"].to_numpy(),
                          out_col: v, f"{out_col}_known": known.astype(int)})


def attach_lag1_team(req: pd.DataFrame, raw: pd.DataFrame, value_col: str,
                     out_col: str, min_season: int) -> pd.DataFrame:
    j = req[["player_id", "season", "team"]].drop_duplicates().copy()
    j["lag_season"] = j["season"] - 1
    m = j.merge(raw.rename(columns={"season": "lag_season"}),
                on=["team", "lag_season"], how="left")
    v = m[value_col].to_numpy(dtype=float)
    known = np.isfinite(v) & (j["lag_season"].to_numpy() >= min_season)
    return pd.DataFrame({"player_id": j["player_id"].to_numpy(),
                          "season": j["season"].to_numpy(),
                          out_col: v, f"{out_col}_known": known.astype(int)})


def placebo_series(req: pd.DataFrame) -> pd.DataFrame:
    def draw(pid: str, season: int) -> float:
        h = hashlib.sha256(f"standalone-screen1|{season}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    v = [draw(p, s) for p, s in zip(req["player_id"], req["season"])]
    return pd.DataFrame({"player_id": req["player_id"].to_numpy(),
                          "season": req["season"].to_numpy(),
                          "placebo": v, "placebo_known": 1})


# ===========================================================================
# 2. RAW SOURCE LOADERS -- own SQL, own gate (season < HOLDOUT_SEASON)
# ===========================================================================
def load_injury_reports() -> pd.DataFrame:
    sql = """SELECT CAST(season AS INTEGER) AS season, gsis_id AS player_id,
                     CAST(week AS INTEGER) AS week, report_status, practice_status
              FROM injuries WHERE season < ? AND season >= ? AND gsis_id IS NOT NULL"""
    conn = _conn()
    try:
        return pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, INJURIES_FIRST))
    finally:
        conn.close()


_SEVERITY = {"Out": 3.0, "Doubtful": 2.0, "Questionable": 1.0, "Probable": 0.0}
_PRACTICE_SEVERITY = {
    "Did Not Participate In Practice": 1.0, "Out (Definitely Will Not Play)": 1.0,
    "Limited Participation in Practice": 0.5, "Full Participation in Practice": 0.0,
}


def build_injury_burden_season(inj: pd.DataFrame) -> pd.DataFrame:
    if not len(inj):
        return pd.DataFrame(columns=["player_id", "season", "severity_sum_n"])
    d = inj.drop_duplicates(["player_id", "season", "week"]).copy()
    d["severity"] = d["report_status"].map(_SEVERITY).fillna(0.0)
    return d.groupby(["player_id", "season"], as_index=False)["severity"].sum() \
        .rename(columns={"severity": "severity_sum_n"})


def build_practice_severity_season(inj: pd.DataFrame) -> pd.DataFrame:
    if "practice_status" not in inj.columns or not len(inj):
        return pd.DataFrame(columns=["player_id", "season", "practice_dnp_limited_rate_n"])
    d = inj.drop_duplicates(["player_id", "season", "week"]).copy()
    d["p_sev"] = d["practice_status"].map(_PRACTICE_SEVERITY)
    d = d[d["p_sev"].notna()]
    per = d.groupby(["player_id", "season"], as_index=False).agg(
        n=("p_sev", "size"), s=("p_sev", "sum"))
    pooled = per["s"].sum() / max(per["n"].sum(), 1.0)
    per["practice_dnp_limited_rate_n"] = (
        (per["s"] + PRACTICE_K0_WEEKS * pooled) / (per["n"] + PRACTICE_K0_WEEKS))
    return per[["player_id", "season", "practice_dnp_limited_rate_n"]]


def load_depth_end() -> pd.DataFrame:
    sql = """SELECT season, gsis_id AS player_id, depth_team, week
              FROM depth_charts_weekly
              WHERE season < ? AND game_type='REG' AND gsis_id IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["player_id", "season", "depth_rank"])
    last_wk = d.groupby("season")["week"].transform("max")
    d = d[d["week"] == last_wk].copy()
    d["depth_rank"] = pd.to_numeric(d["depth_team"], errors="coerce")
    d = d.dropna(subset=["depth_rank"])
    return d.groupby(["player_id", "season"], as_index=False)["depth_rank"].min()


def _pfr_to_gsis(conn) -> pd.Series:
    ids = pd.read_sql_query(
        "SELECT mfl_id, source, source_id FROM player_ids WHERE source IN ('gsis','pfr')", conn)
    g = ids[ids["source"] == "gsis"].set_index("mfl_id")["source_id"]
    p = ids[ids["source"] == "pfr"].set_index("mfl_id")["source_id"]
    xw = pd.DataFrame({"gsis": g, "pfr": p}).dropna()
    return pd.Series(xw["gsis"].to_numpy(), index=xw["pfr"].to_numpy())


_COMBINE_COLS = ["forty", "bench", "vertical", "broad_jump", "cone", "shuttle"]
_COMBINE_TIME = {"forty", "cone", "shuttle"}


def load_combine() -> pd.DataFrame:
    conn = _conn()
    try:
        c = pd.read_sql_query(
            "SELECT draft_year, pfr_id, pos, forty, bench, vertical, broad_jump, cone, shuttle "
            "FROM combine WHERE draft_year IS NOT NULL", conn)
        xw = _pfr_to_gsis(conn)
    finally:
        conn.close()
    c["player_id"] = c["pfr_id"].map(xw)
    c = c.dropna(subset=["player_id"])
    z_cols = []
    for col in _COMBINE_COLS:
        v = c[col].astype(float)
        if col in _COMBINE_TIME:
            v = -v
        key = list(zip(c["pos"], c["draft_year"]))
        tmp = pd.DataFrame({"key": key, "v": v})
        gmu = tmp.groupby("key")["v"].transform("mean")
        gsd = tmp.groupby("key")["v"].transform("std")
        c[f"z_{col}"] = (tmp["v"] - gmu) / gsd.replace(0, np.nan)
        z_cols.append(f"z_{col}")
    c["combine_z"] = c[z_cols].mean(axis=1, skipna=True)
    c["combine_known"] = c[z_cols].notna().any(axis=1).astype(int)
    out = c.groupby(["player_id", "draft_year"], as_index=False).agg(
        combine_z=("combine_z", "first"), combine_known=("combine_known", "first"))
    return out.rename(columns={"draft_year": "draft_season"})


def attach_combine(req: pd.DataFrame, combine: pd.DataFrame) -> pd.DataFrame:
    """Fixed player attribute -- joined on player_id alone, used identically
    every season of the player's career."""
    j = req[["player_id", "season"]].drop_duplicates().copy()
    by_p = combine.drop_duplicates("player_id")[["player_id", "combine_z", "combine_known"]]
    m = j.merge(by_p, on="player_id", how="left")
    m["combine_z"] = m["combine_z"].fillna(0.0)
    m["combine_known"] = m["combine_known"].fillna(0).astype(int)
    return m[["player_id", "season", "combine_z", "combine_known"]]


def load_neutral_pass_rate() -> pd.DataFrame:
    sql = """SELECT season, posteam AS team, pass_attempt, rush_attempt
              FROM pbp WHERE season < ? AND season >= ?
                AND (pass_attempt=1 OR rush_attempt=1) AND down IN (1,2,3)
                AND score_differential BETWEEN -7 AND 7
                AND half_seconds_remaining > 120 AND posteam IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, PBP_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "neutral_pass_rate", "plays"])
    out = d.groupby(["team", "season"], as_index=False).agg(
        plays=("pass_attempt", "size"), pass_n=("pass_attempt", "sum"))
    out["neutral_pass_rate"] = out["pass_n"] / out["plays"].clip(lower=1)
    return out[["team", "season", "neutral_pass_rate", "plays"]]


def attach_neutral_pass_rate(req: pd.DataFrame, npr: pd.DataFrame) -> pd.DataFrame:
    base = req[["player_id", "season", "team"]].drop_duplicates().copy()
    lag_vals, lag_known = [], []
    for k in range(1, N_LAGS + 1):
        j = base.copy(); j["lag_season"] = j["season"] - k
        m = j.merge(npr, left_on=["team", "lag_season"], right_on=["team", "season"],
                    how="left", suffixes=("", "_n"))
        rate = m["neutral_pass_rate"].to_numpy(dtype=float)
        plays = m["plays"].to_numpy(dtype=float)
        ok = np.isfinite(plays) & (plays >= 50)
        lag_vals.append(np.where(ok, rate, np.nan)); lag_known.append(ok)
    w = _median_fill(_lag_weighted(lag_vals))
    known_any = np.any(np.column_stack(lag_known), axis=1).astype(int)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          "neutral_pass_rate": w, "neutral_pass_rate_known": known_any})


def load_yoe() -> pd.DataFrame:
    sql = """SELECT CAST(season AS INTEGER) AS season, player_id,
                     total_yards_gained, total_yards_gained_exp,
                     pass_attempt, rec_attempt, rush_attempt
              FROM ff_opportunity
              WHERE CAST(season AS INTEGER) < ? AND CAST(season AS INTEGER) >= ?
                AND player_id IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, FF_OPP_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["player_id", "season", "yoe_rate"])
    d["opp"] = d["pass_attempt"].fillna(0) + d["rec_attempt"].fillna(0) + d["rush_attempt"].fillna(0)
    per = d.groupby(["player_id", "season"], as_index=False).agg(
        yards=("total_yards_gained", "sum"), yards_exp=("total_yards_gained_exp", "sum"),
        opps=("opp", "sum"))
    per = per[per["opps"] > 0]
    pooled = (per["yards"] - per["yards_exp"]).sum() / per["opps"].sum()
    raw = (per["yards"] - per["yards_exp"]) / per["opps"]
    n = per["opps"].to_numpy(dtype=float)
    per["yoe_rate"] = (raw.to_numpy() * n + pooled * YOE_K0_OPPORTUNITIES) / (n + YOE_K0_OPPORTUNITIES)
    return per[["player_id", "season", "yoe_rate"]]


def load_wopr_raw() -> pd.DataFrame:
    sql = """SELECT season, player_id,
                     SUM(COALESCE(wopr,0.0)) AS wopr_sum,
                     SUM(CASE WHEN wopr IS NOT NULL THEN 1 ELSE 0 END) AS wopr_games
              FROM player_weekly_stats
              WHERE season < ? AND season_type='REG' AND position IN ('WR','TE')
              GROUP BY season, player_id"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d["wopr_rate"] = d["wopr_sum"] / d["wopr_games"].clip(lower=1)
    return d[["season", "player_id", "wopr_rate"]]


def load_snap_share_raw() -> pd.DataFrame:
    sql = """SELECT season, player, position, team,
                     AVG(offense_pct) AS snap_share, COUNT(*) AS n_games
              FROM snap_counts
              WHERE season < ? AND game_type='REG' AND position IN ('RB','WR','TE')
              GROUP BY season, player, position, team"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
        xw = pd.read_sql_query(
            "SELECT player_id, player_display_name AS player, season, team "
            "FROM player_weekly_stats WHERE season < ? AND season_type='REG' "
            "GROUP BY player_id, player_display_name, season, team",
            conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    m = d.merge(xw, on=["player", "season", "team"], how="left").dropna(subset=["player_id"])
    return m.groupby(["season", "player_id"], as_index=False).agg(
        snap_share=("snap_share", "mean"))


def load_redzone_share_raw() -> pd.DataFrame:
    sql = """SELECT season, week, posteam AS team, pass_attempt, rush_attempt,
                     receiver_player_id, rusher_player_id
              FROM pbp
              WHERE season < ? AND yardline_100 <= 20 AND posteam IS NOT NULL
                AND (pass_attempt=1 OR rush_attempt=1)"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    reg = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg]
    team_rz = d.groupby(["season", "team"], as_index=False).size().rename(columns={"size": "team_rz"})
    tg = d.loc[d["pass_attempt"] == 1, ["season", "team", "receiver_player_id"]].rename(
        columns={"receiver_player_id": "player_id"})
    ca = d.loc[d["rush_attempt"] == 1, ["season", "team", "rusher_player_id"]].rename(
        columns={"rusher_player_id": "player_id"})
    use = pd.concat([tg, ca], ignore_index=True)
    use = use[use["player_id"].notna() & (use["player_id"].astype(str) != "")]
    out = use.groupby(["season", "team", "player_id"], as_index=False).size().rename(columns={"size": "rz_use"})
    out = out.merge(team_rz, on=["season", "team"], how="left")
    out = out.groupby(["season", "player_id"], as_index=False).agg(
        rz_use=("rz_use", "sum"), team_rz=("team_rz", "sum"))
    out["rz_share"] = out["rz_use"] / out["team_rz"].clip(lower=1)
    return out[["season", "player_id", "rz_share"]]


def load_yac_per_rec_raw() -> pd.DataFrame:
    sql = """SELECT season, player_id,
                     SUM(COALESCE(receiving_yards_after_catch,0)) AS yac_sum,
                     SUM(COALESCE(receptions,0)) AS rec_sum
              FROM player_weekly_stats
              WHERE season < ? AND season_type='REG' AND position IN ('RB','WR','TE')
              GROUP BY season, player_id"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d = d[d["rec_sum"] >= 5]
    d["yac_per_rec"] = d["yac_sum"] / d["rec_sum"]
    return d[["season", "player_id", "yac_per_rec"]]


def load_qb_rush_raw() -> pd.DataFrame:
    sql = """SELECT season, player_id, SUM(COALESCE(carries,0)) AS carries,
                     COUNT(DISTINCT week) AS games
              FROM player_weekly_stats
              WHERE season < ? AND season_type='REG' AND position='QB'
              GROUP BY season, player_id"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d["qb_rush_att_pg"] = d["carries"] / d["games"].clip(lower=1)
    return d[["season", "player_id", "qb_rush_att_pg"]]


def load_explosive_rush_raw() -> pd.DataFrame:
    sql = """SELECT season, posteam AS team, yards_gained
              FROM pbp WHERE season < ? AND rush_attempt=1 AND posteam IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d["expl"] = (d["yards_gained"] >= 15).astype(int)
    out = d.groupby(["season", "team"], as_index=False).agg(expl_rate=("expl", "mean"), n=("expl", "size"))
    return out[out["n"] >= 100][["season", "team", "expl_rate"]]


def load_late_season_trend_raw() -> pd.DataFrame:
    sql = """SELECT season, week, player_id, team, position,
                     COALESCE(targets,0) AS targets, COALESCE(carries,0) AS carries
              FROM player_weekly_stats
              WHERE season < ? AND season_type='REG' AND position IN ('RB','WR','TE')"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d["opp"] = d["targets"] + d["carries"]
    half = d["season"].map(lambda s: (season_length(int(s)) + 1) // 2)
    d["half"] = np.where(d["week"] <= half, "h1", "h2")
    team_tot = d.groupby(["season", "team", "half"], as_index=False)["opp"].sum().rename(columns={"opp": "team_opp"})
    per = d.groupby(["season", "team", "half", "player_id"], as_index=False)["opp"].sum()
    per = per.merge(team_tot, on=["season", "team", "half"], how="left")
    per["share"] = per["opp"] / per["team_opp"].clip(lower=1)
    piv = per.pivot_table(index=["season", "player_id"], columns="half", values="share",
                          aggfunc="sum").reset_index()
    for c in ("h1", "h2"):
        if c not in piv.columns:
            piv[c] = np.nan
    piv["trend"] = piv["h2"] - piv["h1"]
    return piv[["season", "player_id", "trend"]].dropna()


def load_rb_receiving_share_raw(points: pd.DataFrame) -> pd.DataFrame:
    rb = points[points["position"] == "RB"].copy()
    rb["rec_points"] = 0.5 * rb["receptions"] + rb["rec_yards"] / 10.0 + rb["rec_bonus"] + 6 * rb["rec_tds"]
    rb = rb[rb["points"] > 0]
    rb["rb_receiving_share"] = (rb["rec_points"] / rb["points"]).clip(0, 1)
    return rb[["season", "player_id", "rb_receiving_share"]]


# ===========================================================================
# 3. STATISTICS
# ===========================================================================
def spearman(x: np.ndarray, y: np.ndarray) -> Tuple[float, int]:
    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 5 or np.nanstd(x[ok]) == 0:
        return float("nan"), n
    r, _ = sstats.spearmanr(x[ok], y[ok])
    return float(r), n


def partial_spearman(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> Tuple[float, int]:
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    n = int(ok.sum())
    if n < 8:
        return float("nan"), n
    rx = sstats.rankdata(x[ok]); ry = sstats.rankdata(y[ok]); rz = sstats.rankdata(z[ok])
    if np.std(rx) == 0 or np.std(rz) == 0:
        return float("nan"), n
    bx = np.polyfit(rz, rx, 1); resid_x = rx - np.polyval(bx, rz)
    by = np.polyfit(rz, ry, 1); resid_y = ry - np.polyval(by, rz)
    if np.std(resid_x) == 0 or np.std(resid_y) == 0:
        return float("nan"), n
    r, _ = sstats.pearsonr(resid_x, resid_y)
    return float(r), n


def screen_one(factor_name: str, klass: str, position: str, req_frame: pd.DataFrame,
               value_col: str, known_col: str, points: pd.DataFrame,
               prior_lookup: pd.DataFrame) -> Dict:
    rows = []
    for s in SCREEN_SEASONS:
        uni = universe_for(points, position, s)
        m = uni.merge(req_frame[req_frame["season"] == s], on=["player_id", "season"], how="left")
        m = m.merge(prior_lookup, on=["player_id", "season"], how="left")
        m = m[m[known_col].fillna(0) > 0]
        rows.append(m[["player_id", "season", "points", "prior_points", value_col]])
    panel = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["player_id", "season", "points", "prior_points", value_col])

    per_season = {}
    for s in SCREEN_SEASONS:
        ps = panel[panel["season"] == s]
        r_raw, n_raw = spearman(ps[value_col].to_numpy(dtype=float), ps["points"].to_numpy(dtype=float))
        per_season[s] = {"raw": r_raw, "n": n_raw}

    x = panel[value_col].to_numpy(dtype=float)
    y = panel["points"].to_numpy(dtype=float)
    z = panel["prior_points"].to_numpy(dtype=float)

    raw_rho, raw_n = spearman(x, y)
    partial_rho, partial_n = partial_spearman(x, y, z)

    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    priorpts_rho_matched, matched_n = spearman(z[ok], y[ok])
    raw_rho_matched, _ = spearman(x[ok], y[ok])
    beats_delta = (raw_rho_matched - priorpts_rho_matched) \
        if np.isfinite(raw_rho_matched) and np.isfinite(priorpts_rho_matched) else float("nan")

    vals = [v["raw"] for v in per_season.values() if np.isfinite(v["raw"])]
    n_pos = sum(1 for v in vals if v > 1e-9)
    n_neg = sum(1 for v in vals if v < -1e-9)
    n_zero = len(vals) - n_pos - n_neg

    return {
        "factor": factor_name, "class": klass, "position": position,
        "raw_rho_pooled": raw_rho, "raw_n": raw_n,
        "partial_rho_pooled": partial_rho, "partial_n": partial_n,
        "raw_rho_matched": raw_rho_matched, "priorpoints_rho_matched": priorpts_rho_matched,
        "matched_n": matched_n, "beats_aggregate_delta": beats_delta,
        "per_season": {s: (round(v["raw"], 4) if np.isfinite(v["raw"]) else None)
                        for s, v in per_season.items()},
        "n_seasons_pos": n_pos, "n_seasons_neg": n_neg, "n_seasons_zero": n_zero,
    }


def pct_rank_within_season(req: pd.DataFrame, value_col: str) -> pd.Series:
    return req.groupby("season")[value_col].rank(pct=True)


# ===========================================================================
# 4. MAIN
# ===========================================================================
def main() -> None:
    print("Building outcome panel...")
    points = build_points_panel()
    prior_lookup = prior_points_lookup(points)

    req_by_pos = {}
    for pos in POSITIONS:
        us = [universe_for(points, pos, s) for s in SCREEN_SEASONS]
        req_by_pos[pos] = pd.concat(us, ignore_index=True)

    print("Loading sources...")
    inj = load_injury_reports()
    injury_burden_season = build_injury_burden_season(inj)
    practice_season = build_practice_severity_season(inj)
    depth_end = load_depth_end()
    combine = load_combine()
    npr = load_neutral_pass_rate()
    yoe = load_yoe()
    wopr_raw = load_wopr_raw()
    snap_raw = load_snap_share_raw()
    rz_raw = load_redzone_share_raw()
    yac_raw = load_yac_per_rec_raw()
    qbrush_raw = load_qb_rush_raw()
    expl_raw = load_explosive_rush_raw()
    trend_raw = load_late_season_trend_raw()
    rbshare_raw = load_rb_receiving_share_raw(points)

    def build_wide(pos: str) -> pd.DataFrame:
        """All factor VALUES (post-lag, NaN where unknown) for `pos`, used
        both for the individual screen and for the collinearity map."""
        req = req_by_pos[pos]
        wide = req[["player_id", "season"]].drop_duplicates().copy()

        def add(name, frame, val, known):
            f2 = frame[frame[known] > 0][["player_id", "season", val]].rename(columns={val: name})
            return wide.merge(f2, on=["player_id", "season"], how="left")

        wide = add("injury_burden", attach_3lag(req, injury_burden_season, "severity_sum_n",
                   "injury_burden", INJURIES_FIRST), "injury_burden", "injury_burden_known")
        wide = add("practice_severity", attach_3lag(req, practice_season, "practice_dnp_limited_rate_n",
                   "practice_severity", INJURIES_FIRST), "practice_severity", "practice_severity_known")
        de = attach_lag1(req, depth_end, "depth_rank", "depth_end_rank", DEPTH_FIRST)
        wide = add("depth_end_rank", de, "depth_end_rank", "depth_end_rank_known")
        wide = add("combine_z", attach_combine(req, combine), "combine_z", "combine_known")
        wide = add("neutral_pass_rate", attach_neutral_pass_rate(req, npr),
                   "neutral_pass_rate", "neutral_pass_rate_known")
        wide = add("yoe_rate", attach_3lag(req, yoe, "yoe_rate", "yoe_rate", FF_OPP_FIRST),
                   "yoe_rate", "yoe_rate_known")
        if pos in APPLICABLE_POSITIONS["wopr"]:
            wide = add("wopr", attach_lag1(req, wopr_raw, "wopr_rate", "wopr_rate", 2009),
                       "wopr_rate", "wopr_rate_known")
        if pos in APPLICABLE_POSITIONS["snap_share"]:
            wide = add("snap_share", attach_lag1(req, snap_raw, "snap_share", "snap_share", 2013),
                       "snap_share", "snap_share_known")
        if pos in APPLICABLE_POSITIONS["redzone_share"]:
            wide = add("redzone_share", attach_lag1(req, rz_raw, "rz_share", "rz_share", 2009),
                       "rz_share", "rz_share_known")
        if pos in APPLICABLE_POSITIONS["yac_per_rec"]:
            wide = add("yac_per_rec", attach_lag1(req, yac_raw, "yac_per_rec", "yac_per_rec", 1999),
                       "yac_per_rec", "yac_per_rec_known")
        if pos in APPLICABLE_POSITIONS["rb_receiving_share"]:
            wide = add("rb_receiving_share",
                       attach_lag1(req, rbshare_raw, "rb_receiving_share", "rb_receiving_share", 1999),
                       "rb_receiving_share", "rb_receiving_share_known")
        if pos in APPLICABLE_POSITIONS["late_season_trend"]:
            wide = add("late_season_trend", attach_lag1(req, trend_raw, "trend", "trend", 1999),
                       "trend", "trend_known")
        if pos in APPLICABLE_POSITIONS["qb_rush_att_pg"]:
            wide = add("qb_rush_att_pg",
                       attach_lag1(req, qbrush_raw, "qb_rush_att_pg", "qb_rush_att_pg", 1999),
                       "qb_rush_att_pg", "qb_rush_att_pg_known")
        if pos in APPLICABLE_POSITIONS["explosive_rush_rate"]:
            wide = add("explosive_rush_rate",
                       attach_lag1_team(req, expl_raw, "expl_rate", "expl_rate", 1999),
                       "expl_rate", "expl_rate_known")
        pb = placebo_series(req)
        wide = add("placebo", pb, "placebo", "placebo_known")
        return wide

    wide_by_pos = {pos: build_wide(pos) for pos in POSITIONS}

    # ------------------------------------------------ individual screen
    results: List[Dict] = []
    for pos in POSITIONS:
        wide = wide_by_pos[pos]
        req_keyed = wide[["player_id", "season"]]
        for fname, cols in APPLICABLE_POSITIONS.items():
            if pos not in cols or fname not in wide.columns:
                continue
            frame = wide[["player_id", "season", fname]].copy()
            frame[f"{fname}_known"] = wide[fname].notna().astype(int)
            results.append(screen_one(fname, FACTOR_CLASS[fname], pos, frame, fname,
                                      f"{fname}_known", points, prior_lookup))
    res_df = pd.DataFrame(results)

    # ------------------------------------------------ collinearity map
    colin_rows = []
    for pos in POSITIONS:
        wide = wide_by_pos[pos]
        cols = [c for c in wide.columns if c not in ("player_id", "season")]
        for i, c1 in enumerate(cols):
            for c2 in cols[i + 1:]:
                r, n = spearman(wide[c1].to_numpy(dtype=float), wide[c2].to_numpy(dtype=float))
                colin_rows.append({"position": pos, "factor_a": c1, "factor_b": c2, "rho": r, "n": n})
    colin_df = pd.DataFrame(colin_rows)

    # ------------------------------------------------ within-cluster contrasts
    # For every pair with |rho| >= 0.6 within a position, construct the
    # percentile-rank gap (a role signal, per the founder's second
    # correction) and screen it identically to any other factor.
    TIGHT = 0.6
    contrast_results: List[Dict] = []
    contrast_pairs = colin_df[(colin_df["rho"].abs() >= TIGHT) & (colin_df["n"] >= 30)]
    seen = set()
    for _, row in contrast_pairs.iterrows():
        pos, a, b = row["position"], row["factor_a"], row["factor_b"]
        if a == "placebo" or b == "placebo":
            continue
        key = (pos, a, b)
        if key in seen:
            continue
        seen.add(key)
        wide = wide_by_pos[pos]
        cname = f"contrast_{a}_minus_{b}"
        pa = pct_rank_within_season(wide, a)
        pb = pct_rank_within_season(wide, b)
        cval = pa - pb
        frame = pd.DataFrame({"player_id": wide["player_id"], "season": wide["season"],
                              cname: cval})
        frame[f"{cname}_known"] = (wide[a].notna() & wide[b].notna()).astype(int)
        klass_a, klass_b = FACTOR_CLASS.get(a, "AMBIGUOUS"), FACTOR_CLASS.get(b, "AMBIGUOUS")
        klass = "EXOGENOUS" if klass_a == klass_b == "EXOGENOUS" else "CONSTITUENT"
        contrast_results.append(screen_one(cname, klass, pos, frame, cname, f"{cname}_known",
                                           points, prior_lookup))
        contrast_results[-1]["contrast_of"] = f"{a} (rho={row['rho']:.3f} vs {b})"

    contrast_df = pd.DataFrame(contrast_results)

    res_df.to_csv(OUT / "standalone_screen1_results.csv", index=False)
    colin_df.to_csv(OUT / "standalone_screen1_collinearity.csv", index=False)
    if len(contrast_df):
        contrast_df.to_csv(OUT / "standalone_screen1_contrasts.csv", index=False)

    print(f"\nWrote {OUT/'standalone_screen1_results.csv'} ({len(res_df)} rows)")
    print(f"Wrote {OUT/'standalone_screen1_collinearity.csv'} ({len(colin_df)} rows)")
    print(f"Wrote {OUT/'standalone_screen1_contrasts.csv'} ({len(contrast_df)} rows, "
          f"{len(seen)} tight clusters at |rho|>={TIGHT})")

    print("\n=== INDIVIDUAL FACTOR SCREEN ===")
    for _, row in res_df.sort_values(["position", "factor"]).iterrows():
        print(f"{row['position']:3s} {row['factor']:22s} [{row['class']:11s}] "
              f"raw={row['raw_rho_pooled']:.4f}(n={row['raw_n']:.0f})  "
              f"partial={row['partial_rho_pooled']:.4f}(n={row['partial_n']:.0f})  "
              f"beats_agg={row['beats_aggregate_delta']:.4f}  "
              f"seasons+/-/0={row['n_seasons_pos']}/{row['n_seasons_neg']}/{row['n_seasons_zero']}")

    print("\n=== TIGHT CLUSTERS (|rho|>=0.6) AND THEIR CONTRASTS ===")
    for _, row in contrast_df.sort_values(["position", "factor"]).iterrows():
        print(f"{row['position']:3s} {row['factor']:40s} [{row['class']:11s}] "
              f"({row.get('contrast_of','')}) "
              f"raw={row['raw_rho_pooled']:.4f}(n={row['raw_n']:.0f})  "
              f"beats_agg={row['beats_aggregate_delta']:.4f}")


if __name__ == "__main__":
    main()
