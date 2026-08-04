"""Standalone predictiveness screen 2 -- supersedes screen 1, extending it to
the FULL v3 candidate pool: C1's 6, C2's 6, C3's 6, C4's 6, the six
predictive incumbents (depth chart/role, injury designations, age,
prior-year target/touch share, air yards/aDOT, draft capital), everything
Task 1 of this dispatch reclassifies from BLOCKED to NOW AVAILABLE (PROE,
OC-level coordinator continuity), and the within-cluster contrasts.

============================================================================
WHY THIS FILE IS SELF-CONTAINED (does not import screen 1 or factors_c1..c4)
============================================================================
This worktree's `git log` (`fd3bed1`) does NOT contain `experiments/bottomup/
v2/standalone_screen1.py`, `factors_c1.py`, `factors_c2.py`, `factors_c3.py`,
or `factors_c4.py` -- verified with `ls`/`git status` before writing a line
of this file. Those exist only as uncommitted work in a SIBLING checkout
sharing this repo's `.git` (a concurrent `ranker`/`backend` session's working
directory, per `docs/environment.md`'s worktree-isolation model) that this
worktree cannot see on disk. This is the exact situation screen 1's own
header describes for itself, and the C3/C4 candidate-definition docs
describe for their own sessions -- each concurrent agent independently hits
the same isolation and each resolves it the same documented way: read the
sibling content where reachable (informs mechanism/discipline, per the
dispatch's own note that this is legitimate), but write fresh, independently
against tables reachable from THIS worktree's own `data/nfl.db` copy and
THIS worktree's own COMMITTED `experiments/bottomup/components/{pos_data,
pos_features}.py` (those two ARE committed on this branch, so the six
predictive incumbents ARE built by calling `pos_features.build_features`
directly -- no reimplementation risk there).

The C1/C4 factor MECHANISMS below (xFP, NGS separation, TPRR, target-share
stability, team pace, contract-year, coaching disruption, O-line YBC,
two-WR rate) reproduce the SQL and construction the sibling `factors_c1.py`/
`factors_c4.py`/`batch-C3-candidates.md`/`batch-C4-candidates.md` documents
describe (read via the coordinator's shared filesystem access before writing
this file), so that when those land on `main` and this branch merges, the
numbers are directly comparable -- but every line of code here is this
file's own, reachable from this worktree alone, importing nothing from any
uncommitted sibling file.

============================================================================
METHOD -- unchanged from screen 1, restated briefly (full detail:
docs/ranking/standalone-screen-1.md)
============================================================================
- Model-independent: does a factor value, on its own, carry ANY rank
  relationship to next-season fantasy points.
- Screens ONLY 2013-2019. 2020-2024 untouched. Sealed 2025 holdout never
  read (`HOLDOUT_SEASON` gates every SQL read).
- Every factor value is built from strictly-prior-season data.
- EXOGENOUS / CONSTITUENT / AMBIGUOUS classified BEFORE any number is
  computed. Partialling out prior-season points is a valid predictiveness
  test only for EXOGENOUS factors.
- Noise benchmark (seeded placebo) run through the identical pipeline.
- Collinearity is diagnostic, never a filter -- within-cluster contrasts are
  constructed and screened as their own candidates.
- Nothing here is INCLUDE/EXCLUDE. Nothing enters any campaign multiplicity
  denominator.
"""

from __future__ import annotations

import hashlib
import re
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

from experiments.bottomup.components import pos_features                # noqa: E402
from experiments.bottomup.components.pos_data import (                   # noqa: E402
    DEFAULT_DB, HOLDOUT_SEASON, aggregate_seasons, build_panel, load_weekly,
    season_length,
)
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS  # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
OUT.mkdir(parents=True, exist_ok=True)

SCREEN_SEASONS: Tuple[int, ...] = (2013, 2014, 2015, 2016, 2017, 2018, 2019)
POSITIONS: Tuple[str, ...] = ("QB", "RB", "WR", "TE")
DB = DEFAULT_DB

INJURIES_FIRST = 2010
DEPTH_FIRST = 2001
COMBINE_FIRST = 2000
PBP_FIRST = 2009
FF_OPP_FIRST = 2006
NGS_FIRST = 2016
ROUTES_FIRST = 2016
ODDS_FIRST = 2018
TSHARE_FIRST = 2009
SCHEDULES_FIRST = 1999
CONTRACTS_FIRST = 2011
OL_FIRST = 2018
PARTICIPATION_FIRST = 2016
PLAYCALLER_FIRST = 2007
PRACTICE_K0_WEEKS = 8.0
YOE_K0_OPPORTUNITIES = 40.0
TPRR_K0 = 100.0
TSHARE_K0_SEASONS = 2.0

# ---------------------------------------------------------------------------
# Factor classification, fixed BEFORE any number below was computed.
# ---------------------------------------------------------------------------
FACTOR_CLASS: Dict[str, str] = {
    # ---- screen-1 base 14 (C3's six + earlier batches' six + placebo)
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
    # ---- C1 remainder
    "xfp_diff":            "CONSTITUENT",   # built from the player's own points
    "ngs_separation":      "EXOGENOUS",     # tracking-derived skill metric, not box-score
    "tprr":                "CONSTITUENT",   # rate over the player's own targets
    # ---- C2 remainder
    "implied_team_total":  "EXOGENOUS",     # Vegas market read, not player box score
    # ---- C4 (I-N)
    "tshare_stability":    "AMBIGUOUS",     # stability of a constituent quantity
    "team_pace":           "EXOGENOUS",     # team environment, not the player's box score
    "is_contract_year":    "EXOGENOUS",     # calendar/business event
    "hc_disruption":       "EXOGENOUS",     # coaching context
    "ol_ybc":               "EXOGENOUS",    # O-line environment, not the RB's own box score
    "two_wr_rate":          "EXOGENOUS",    # team personnel identity
    # ---- Task-1 newly-unblocked
    "proe":                 "EXOGENOUS",    # team scheme identity (xpass residual)
    "oc_disruption":        "EXOGENOUS",    # coordinator-context, same class as hc_disruption
    # ---- six predictive incumbents (no grandfather clause, FR-2026-08-04)
    "age":                   "EXOGENOUS",
    "draft_capital":         "EXOGENOUS",
    "share_level":            "CONSTITUENT",
    "adot":                    "AMBIGUOUS",
    "depth_rostered_absent":   "EXOGENOUS",
    "depth_offroster":         "EXOGENOUS",
    "depth_first_share":       "EXOGENOUS",
    "inj_missed_share":        "EXOGENOUS",
    "inj_unexp_missed_share":  "EXOGENOUS",
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
    "xfp_diff":              POSITIONS,
    "ngs_separation":        ("WR", "TE"),
    "tprr":                  ("RB", "WR", "TE"),
    "implied_team_total":    POSITIONS,
    "tshare_stability":      ("WR", "TE"),
    "team_pace":             POSITIONS,
    "is_contract_year":      POSITIONS,
    "hc_disruption":         POSITIONS,
    "ol_ybc":                ("RB",),
    "two_wr_rate":           POSITIONS,
    "proe":                  POSITIONS,
    "oc_disruption":         POSITIONS,
    "age":                   POSITIONS,
    "draft_capital":         POSITIONS,
    "share_level":           ("RB", "WR", "TE"),
    "adot":                  ("RB", "WR", "TE"),
    "depth_rostered_absent": POSITIONS,
    "depth_offroster":       POSITIONS,
    "depth_first_share":     POSITIONS,
    "inj_missed_share":      POSITIONS,
    "inj_unexp_missed_share": POSITIONS,
}

#: which ledger row each factor answers, for the write-up's mapping table --
#: documentation only, not used by any computation below.
LEDGER_ROW = {
    "injury_burden": "T0-6-adjacent (leading, C3-C)", "practice_severity": "C3-D",
    "depth_end_rank": "C3-E", "combine_z": "N34/C3-F", "neutral_pass_rate": "N20/C3-G",
    "yoe_rate": "T1-18-adjacent/C3-H", "wopr": "T1-15/C2", "snap_share": "T0-9/N18/C1-F1",
    "redzone_share": "T0-10/C1-F2", "yac_per_rec": "N16/C2", "rb_receiving_share": "N17/C2",
    "late_season_trend": "N19/C2", "qb_rush_att_pg": "N9", "explosive_rush_rate": "screen1",
    "xfp_diff": "T1-18/C1-F3", "ngs_separation": "N5/C1-F4", "tprr": "T1-16/T1-17/N3/C1-F5",
    "implied_team_total": "T0-11/N12/C2", "tshare_stability": "T1-13/C4-I",
    "team_pace": "T1-21/C4-J", "is_contract_year": "T1-27/C4-K",
    "hc_disruption": "T1-29b/C4-L", "ol_ybc": "T1-23/N27/C4-M", "two_wr_rate": "T1-31/N25/C4-N",
    "proe": "T1-22", "oc_disruption": "T1-29/T1-30/N21/N22",
    "age": "T0-7", "draft_capital": "T1-25", "share_level": "T0-8",
    "adot": "T1-14", "depth_rostered_absent": "T0-5", "depth_offroster": "T0-5",
    "depth_first_share": "T0-5", "inj_missed_share": "T0-6", "inj_unexp_missed_share": "T0-6",
}


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


# ===========================================================================
# 1. OUTCOME PANEL (byte-identical construction to screen 1)
# ===========================================================================
def build_points_panel() -> pd.DataFrame:
    wk = load_weekly(DB, max_season=HOLDOUT_SEASON)
    sp = aggregate_seasons(wk)
    return sp[["player_id", "season", "position", "team", "games", "points",
               "rec_yards", "receptions", "rec_bonus", "rec_tds"]]


def universe_for(points: pd.DataFrame, position: str, season: int) -> pd.DataFrame:
    u = points[(points["position"] == position) & (points["season"] == season)
               & (points["games"] >= 1)]
    return u[["player_id", "season", "team", "points", "games"]].copy()


def prior_points_lookup(points: pd.DataFrame) -> pd.DataFrame:
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


def attach_lagw_team(req: pd.DataFrame, raw: pd.DataFrame, value_col: str,
                     n_col: str, out_col: str, min_n: float) -> pd.DataFrame:
    """3-lag weighted TEAM-level attach with a per-lag minimum-sample-size
    coverage gate (pace/PROE/O-line/implied-total shape)."""
    base = req[["player_id", "season", "team"]].drop_duplicates().copy()
    lag_vals, lag_known = [], []
    for k in range(1, N_LAGS + 1):
        j = base.copy(); j["lag_season"] = j["season"] - k
        m = j.merge(raw, left_on=["team", "lag_season"], right_on=["team", "season"],
                    how="left", suffixes=("", "_r"))
        v = m[value_col].to_numpy(dtype=float)
        n = m[n_col].to_numpy(dtype=float)
        ok = np.isfinite(n) & (n >= min_n)
        lag_vals.append(np.where(ok, v, np.nan)); lag_known.append(ok)
    w = _median_fill(_lag_weighted(lag_vals))
    known_any = np.any(np.column_stack(lag_known), axis=1).astype(int)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          out_col: w, f"{out_col}_known": known_any})


def placebo_series(req: pd.DataFrame) -> pd.DataFrame:
    def draw(pid: str, season: int) -> float:
        h = hashlib.sha256(f"standalone-screen2|{season}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    v = [draw(p, s) for p, s in zip(req["player_id"], req["season"])]
    return pd.DataFrame({"player_id": req["player_id"].to_numpy(),
                          "season": req["season"].to_numpy(),
                          "placebo": v, "placebo_known": 1})


# ===========================================================================
# 2. RAW SOURCE LOADERS -- screen-1 base 14 (unchanged construction)
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


def attach_neutral_pass_rate(req: pd.DataFrame, npr: pd.DataFrame) -> pd.DataFrame:
    return attach_lagw_team(req, npr, "neutral_pass_rate", "plays", "neutral_pass_rate", 50.0)


# ===========================================================================
# 3. RAW SOURCE LOADERS -- C1 remainder (xFP, NGS separation, TPRR)
# ===========================================================================
def load_xfp_raw() -> pd.DataFrame:
    sql = """SELECT CAST(season AS INTEGER) AS season, player_id,
                     CAST(week AS INTEGER) AS week,
                     COALESCE(total_fantasy_points_exp, 0.0) AS xfp,
                     COALESCE(total_fantasy_points, 0.0) AS fp
              FROM ff_opportunity
              WHERE CAST(season AS INTEGER) < ? AND player_id IS NOT NULL AND player_id <> ''"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["player_id", "season", "xfp_diff_pg"])
    reg = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg]
    per = d.groupby(["player_id", "season"], as_index=False).agg(
        xfp=("xfp", "sum"), fp=("fp", "sum"), wks=("week", "size"))
    per["xfp_diff_pg"] = (per["fp"] - per["xfp"]) / per["wks"].clip(lower=1)
    return per[["player_id", "season", "xfp_diff_pg"]]


def load_ngs_separation_raw() -> pd.DataFrame:
    sql = """SELECT season, player_gsis_id AS player_id, AVG(avg_separation) AS avg_separation
              FROM ngs_receiving
              WHERE season < ? AND season_type='REG' AND player_gsis_id IS NOT NULL
                AND avg_separation IS NOT NULL
              GROUP BY season, player_gsis_id"""
    conn = _conn()
    try:
        return pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()


_ROUTE_SQL = """
SELECT p.season AS season, p.offense_players AS offense_players
FROM participation p JOIN pbp b
  ON p.nflverse_game_id = b.game_id AND p.play_id = b.play_id
WHERE b.pass_attempt = 1 AND p.offense_players IS NOT NULL AND p.offense_players <> ''
  AND p.season < ?
"""


def load_routes_raw() -> pd.DataFrame:
    """Per (player, season): dropbacks he was on the field for -- a LABELLED
    PROXY for routes run (`participation.offense_players`), same three
    departures from a charted count C1's F5 documents: a pass-blocking back
    is counted; the denominator includes sacks/scrambles/penalty-wiped
    plays; `offense_positions` is null throughout so no position filter is
    applied at load time (the join to the universe below does that)."""
    conn = _conn()
    try:
        d = pd.read_sql_query(_ROUTE_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "routes"])
    d["player_id"] = d["offense_players"].str.split(";")
    d = d[["season", "player_id"]].explode("player_id")
    d = d[d["player_id"].astype(str).str.len() > 0]
    return d.groupby(["season", "player_id"], as_index=False).size().rename(
        columns={"size": "routes"})


def load_targets_raw() -> pd.DataFrame:
    sql = """SELECT season, player_id, SUM(COALESCE(targets,0)) AS targets
              FROM player_weekly_stats WHERE season < ? AND season_type='REG'
              GROUP BY season, player_id"""
    conn = _conn()
    try:
        return pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()


def attach_tprr(req: pd.DataFrame, routes: pd.DataFrame, tgt_raw: pd.DataFrame,
                 k0: float = TPRR_K0) -> pd.DataFrame:
    base = req[["player_id", "season"]].drop_duplicates().copy()
    num = np.zeros(len(base)); den = np.zeros(len(base))
    for k in range(1, N_LAGS + 1):
        j = base.copy(); j["lag_season"] = j["season"] - k
        r = j.merge(routes, left_on=["player_id", "lag_season"],
                    right_on=["player_id", "season"], how="left", suffixes=("", "_r"))
        t = j.merge(tgt_raw, left_on=["player_id", "lag_season"],
                    right_on=["player_id", "season"], how="left", suffixes=("", "_t"))
        rv = r["routes"].fillna(0.0).to_numpy(dtype=float)
        tv = t["targets"].fillna(0.0).to_numpy(dtype=float)
        num += LAG_WEIGHTS[k - 1] * tv
        den += LAG_WEIGHTS[k - 1] * rv
    pooled = float(num.sum() / den.sum()) if den.sum() > 0 else 0.0
    rate = (num + k0 * pooled) / (den + k0)
    known = (den > 0).astype(int)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          "tprr": rate, "tprr_known": known})


# ===========================================================================
# 4. RAW SOURCE LOADER -- C2 remainder: implied team total
# ===========================================================================
def load_implied_team_total_raw() -> pd.DataFrame:
    sql = """SELECT season, team, AVG(implied_team_total) AS itt, COUNT(*) AS n
              FROM odds_snapshots WHERE season < ? AND implied_team_total IS NOT NULL
              GROUP BY season, team"""
    conn = _conn()
    try:
        return pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()


# ===========================================================================
# 5. RAW SOURCE LOADERS -- C4 (I-N), reproducing the sibling factors_c4.py
#    construction (read via shared filesystem, reimplemented independently
#    per this file's own header)
# ===========================================================================
def load_target_share_raw() -> pd.DataFrame:
    sql = """SELECT season, player_id, target_share
              FROM player_weekly_stats
              WHERE season < ? AND season >= ? AND season_type='REG'
                AND position IN ('WR','TE') AND target_share IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, TSHARE_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["player_id", "season", "tshare_mean"])
    return d.groupby(["player_id", "season"], as_index=False).agg(
        tshare_mean=("target_share", "mean"))


def build_tshare_stability(req: pd.DataFrame, tshare: pd.DataFrame) -> pd.DataFrame:
    base = req[["player_id", "season"]].drop_duplicates().copy()
    lag_vals, lag_known = [], []
    for k in range(1, N_LAGS + 1):
        j = base.copy(); j["lag_season"] = j["season"] - k
        m = j.merge(tshare, left_on=["player_id", "lag_season"],
                    right_on=["player_id", "season"], how="left", suffixes=("", "_t"))
        v = m["tshare_mean"].to_numpy(dtype=float)
        known = (m["lag_season"] >= TSHARE_FIRST).to_numpy() & np.isfinite(v)
        lag_vals.append(v); lag_known.append(known)
    vals = np.column_stack(lag_vals)
    known_mask = np.column_stack(lag_known)
    n_known = known_mask.sum(axis=1)
    mean = np.full(len(base), np.nan); cv = np.full(len(base), np.nan)
    for i in range(len(base)):
        vv = vals[i][known_mask[i]]
        if len(vv) >= 1:
            mean[i] = float(np.mean(vv))
        if len(vv) >= 2 and mean[i] > 0:
            cv[i] = float(np.std(vv, ddof=1) / mean[i])
    pooled_cv = float(np.nanmean(cv)) if np.isfinite(cv).any() else 0.0
    shrunk_cv = np.where(
        n_known >= 2,
        (np.nan_to_num(cv) * (n_known - 1) + TSHARE_K0_SEASONS * pooled_cv)
        / (np.where(n_known >= 2, n_known - 1, 1) + TSHARE_K0_SEASONS),
        pooled_cv)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          "tshare_stability": -shrunk_cv,
                          "tshare_stability_known": (n_known >= 2).astype(int)})


def load_pace_raw() -> pd.DataFrame:
    sql = """SELECT season, week, posteam AS team, play_id
              FROM pbp WHERE season < ? AND season >= ? AND posteam IS NOT NULL
                AND (pass_attempt=1 OR rush_attempt=1)"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, PBP_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "plays_pg", "games"])
    reg = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg]
    per_game = d.groupby(["season", "team", "week"], as_index=False).size()
    return per_game.groupby(["season", "team"], as_index=False).agg(
        plays_pg=("size", "mean"), games=("size", "size"))


def load_contracts_raw() -> pd.DataFrame:
    sql = """SELECT gsis_id AS player_id, year_signed, years
              FROM contracts
              WHERE year_signed >= ? AND year_signed < ? AND years IS NOT NULL
                AND years > 0 AND gsis_id IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(CONTRACTS_FIRST, HOLDOUT_SEASON + 1))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["player_id", "year_signed", "contract_end"])
    d["contract_end"] = d["year_signed"] + d["years"] - 1
    return d[["player_id", "year_signed", "contract_end"]]


def attach_contract_year(req: pd.DataFrame, contracts: pd.DataFrame) -> pd.DataFrame:
    base = req[["player_id", "season"]].drop_duplicates().copy()
    if not len(contracts):
        z = np.zeros(len(base))
        return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                              "season": base["season"].to_numpy(),
                              "is_contract_year": z, "contract_known": z.astype(int)})
    m = base.merge(contracts, on="player_id", how="left")
    m = m[m["year_signed"].isna() | (m["year_signed"] <= m["season"])]
    m = m.sort_values("year_signed").groupby(["player_id", "season"], as_index=False).last()
    out = base.merge(m[["player_id", "season", "contract_end"]], on=["player_id", "season"], how="left")
    known = out["contract_end"].notna().to_numpy()
    end = out["contract_end"].to_numpy(dtype=float)
    is_cy = np.where(known, (end == out["season"].to_numpy()).astype(float), 0.0)
    return pd.DataFrame({"player_id": out["player_id"].to_numpy(),
                          "season": out["season"].to_numpy(),
                          "is_contract_year": is_cy, "contract_known": known.astype(int)})


def load_coach_change_raw() -> pd.DataFrame:
    sql_h = """SELECT season, home_team AS team, home_coach AS coach FROM schedules
               WHERE season < ? AND game_type='REG' AND home_coach IS NOT NULL"""
    sql_a = """SELECT season, away_team AS team, away_coach AS coach FROM schedules
               WHERE season < ? AND game_type='REG' AND away_coach IS NOT NULL"""
    conn = _conn()
    try:
        h = pd.read_sql_query(sql_h, conn, params=(HOLDOUT_SEASON,))
        a = pd.read_sql_query(sql_a, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    d = pd.concat([h, a], ignore_index=True)
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "hc_changed"])
    per = d.groupby(["season", "team", "coach"], as_index=False).size()
    top = per.sort_values("size", ascending=False).groupby(["season", "team"], as_index=False).first()
    top = top[["season", "team", "coach"]].sort_values(["team", "season"])
    top["prev_coach"] = top.groupby("team")["coach"].shift(1)
    top["prev_season"] = top.groupby("team")["season"].shift(1)
    consecutive = (top["season"] - top["prev_season"]) == 1
    top["hc_changed"] = np.where(consecutive, (top["coach"] != top["prev_coach"]).astype(float), np.nan)
    return top[["season", "team", "hc_changed"]]


def attach_coaching_disruption(req: pd.DataFrame, coach_change: pd.DataFrame) -> pd.DataFrame:
    base = req[["player_id", "season", "team"]].drop_duplicates().copy()
    base["lag_season"] = base["season"] - 1
    m = base.merge(coach_change, left_on=["team", "lag_season"], right_on=["team", "season"],
                    how="left", suffixes=("", "_c"))
    val = m["hc_changed"].to_numpy(dtype=float)
    known = np.isfinite(val)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          "hc_disruption": np.where(known, val, 0.0),
                          "hc_disruption_known": known.astype(int)})


def load_ol_ybc_raw() -> pd.DataFrame:
    sql = """SELECT season, team, carries, rushing_yards_before_contact_avg AS ybc_avg
              FROM pfr_advstats_rush
              WHERE season < ? AND season >= ? AND carries IS NOT NULL
                AND rushing_yards_before_contact_avg IS NOT NULL AND carries > 0"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, OL_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "ybc_pg", "carries_sum"])
    d["ybc_weighted"] = d["ybc_avg"] * d["carries"]
    out = d.groupby(["season", "team"], as_index=False).agg(
        ybc_sum=("ybc_weighted", "sum"), carries_sum=("carries", "sum"))
    out["ybc_pg"] = out["ybc_sum"] / out["carries_sum"].clip(lower=1)
    return out[["season", "team", "ybc_pg", "carries_sum"]]


_WR_COUNT_RE = re.compile(r"(\d+)\s*WR")


def load_two_wr_rate_raw() -> pd.DataFrame:
    sql = """SELECT season, week, possession_team AS team, offense_personnel
              FROM participation WHERE season < ? AND season >= ?
                AND possession_team IS NOT NULL AND offense_personnel IS NOT NULL
                AND offense_personnel != ''"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, PARTICIPATION_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "two_wr_rate", "snaps"])
    m = d["offense_personnel"].str.extract(_WR_COUNT_RE)
    d = d.assign(wr_n=pd.to_numeric(m[0], errors="coerce")).dropna(subset=["wr_n"])
    out = d.groupby(["season", "team"], as_index=False).agg(
        snaps=("wr_n", "size"), two_wr=("wr_n", lambda s: int((s == 2).sum())))
    out["two_wr_rate"] = out["two_wr"] / out["snaps"].clip(lower=1)
    return out[["season", "team", "two_wr_rate", "snaps"]]


# ===========================================================================
# 6. RAW SOURCE LOADERS -- Task 1 newly-unblocked: PROE, OC continuity
# ===========================================================================
def load_proe_raw() -> pd.DataFrame:
    """Never actually blocked once `pbp` landed (Task 1 finding): `pbp.xpass`
    (nflverse's own expected-pass-probability model) is already in the
    ingested schema. PROE = actual pass rate - mean(xpass), team-season,
    over every scrimmage play (REG season, xpass non-null)."""
    sql = """SELECT season, week, posteam AS team, pass_attempt, xpass
              FROM pbp WHERE season < ? AND season >= ?
                AND (pass_attempt=1 OR rush_attempt=1) AND posteam IS NOT NULL
                AND xpass IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON, PBP_FIRST))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "proe", "plays"])
    reg = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg]
    out = d.groupby(["team", "season"], as_index=False).agg(
        plays=("pass_attempt", "size"), pass_rate=("pass_attempt", "mean"),
        xpass_rate=("xpass", "mean"))
    out["proe"] = out["pass_rate"] - out["xpass_rate"]
    return out[["team", "season", "proe", "plays"]]


def load_oc_change_raw() -> pd.DataFrame:
    """OC-level coordinator continuity. Task 1 finding: `play_callers_
    preseason` has 992 rows (Wikipedia team-staff-navbox proxy, confidence
    'medium' on 957/992), NOT the PFR-403 source the ledger's `blocked`
    disposition (T1-29/T1-30/N21/N22) names -- genuinely new, different
    data, landed since that disposition was written. Team-season OC resolved
    as the max-confidence row (medium preferred over low); a rare double-
    entry at the same confidence keeps the first. Lag-1 change signal only,
    same construction as head-coach continuity (a gap reads unknown, never
    silently as continuity)."""
    sql = """SELECT team, season, coach_id, confidence FROM play_callers_preseason
              WHERE season < ? AND title = 'OC' AND coach_id IS NOT NULL"""
    conn = _conn()
    try:
        d = pd.read_sql_query(sql, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["team", "season", "oc_changed"])
    d["conf_rank"] = (d["confidence"] == "medium").astype(int)
    d = d.sort_values("conf_rank", ascending=False).drop_duplicates(["team", "season"], keep="first")
    d = d.sort_values(["team", "season"])
    d["prev_coach"] = d.groupby("team")["coach_id"].shift(1)
    d["prev_season"] = d.groupby("team")["season"].shift(1)
    consecutive = (d["season"] - d["prev_season"]) == 1
    d["oc_changed"] = np.where(consecutive, (d["coach_id"] != d["prev_coach"]).astype(float), np.nan)
    return d[["season", "team", "oc_changed"]]


def attach_oc_disruption(req: pd.DataFrame, oc: pd.DataFrame) -> pd.DataFrame:
    base = req[["player_id", "season", "team"]].drop_duplicates().copy()
    base["lag_season"] = base["season"] - 1
    m = base.merge(oc, left_on=["team", "lag_season"], right_on=["team", "season"],
                    how="left", suffixes=("", "_o"))
    val = m["oc_changed"].to_numpy(dtype=float)
    known = np.isfinite(val)
    return pd.DataFrame({"player_id": base["player_id"].to_numpy(),
                          "season": base["season"].to_numpy(),
                          "oc_disruption": np.where(known, val, 0.0),
                          "oc_disruption_known": known.astype(int)})


# ===========================================================================
# 7. SIX PREDICTIVE INCUMBENTS -- via `pos_features.build_features` directly
#    (committed on this branch). No reimplementation risk: this is the exact
#    construction the live/unshipped component model uses.
# ===========================================================================
def build_incumbents(req_by_pos: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    panel = build_panel(feature_gate=max(SCREEN_SEASONS) + 1,
                        outcome_gate=max(SCREEN_SEASONS) + 1)
    out: Dict[str, pd.DataFrame] = {}
    for pos in POSITIONS:
        rows = []
        for s in SCREEN_SEASONS:
            uni = req_by_pos[pos][req_by_pos[pos]["season"] == s][["player_id"]].drop_duplicates()
            uni = uni.assign(entry="screen2")
            f = pos_features.build_features(panel, uni, s)
            rows.append(f)
        out[pos] = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return out


# ===========================================================================
# 8. STATISTICS -- identical to screen 1
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
# 9. MAIN
# ===========================================================================
def main() -> None:
    print("Building outcome panel...")
    points = build_points_panel()
    prior_lookup = prior_points_lookup(points)

    req_by_pos = {}
    for pos in POSITIONS:
        us = [universe_for(points, pos, s) for s in SCREEN_SEASONS]
        req_by_pos[pos] = pd.concat(us, ignore_index=True)

    print("Loading screen-1-base / C3 sources...")
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

    print("Loading C1-remainder / C2-remainder sources...")
    xfp_raw = load_xfp_raw()
    sep_raw = load_ngs_separation_raw()
    routes_raw = load_routes_raw()
    tgt_raw = load_targets_raw()
    itt_raw = load_implied_team_total_raw()

    print("Loading C4 sources (I-N)...")
    tshare_raw = load_target_share_raw()
    pace_raw = load_pace_raw()
    contracts_raw = load_contracts_raw()
    coach_raw = load_coach_change_raw()
    ol_raw = load_ol_ybc_raw()
    twowr_raw = load_two_wr_rate_raw()

    print("Loading Task-1 newly-unblocked sources (PROE, OC continuity)...")
    proe_raw = load_proe_raw()
    oc_raw = load_oc_change_raw()

    print("Building the six predictive incumbents (pos_features.build_features)...")
    incumbents = build_incumbents(req_by_pos)

    def build_wide(pos: str) -> pd.DataFrame:
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

        wide = add("xfp_diff", attach_3lag(req, xfp_raw, "xfp_diff_pg", "xfp_diff_pg", FF_OPP_FIRST),
                   "xfp_diff_pg", "xfp_diff_pg_known")
        if pos in APPLICABLE_POSITIONS["ngs_separation"]:
            wide = add("ngs_separation", attach_lag1(req, sep_raw, "avg_separation",
                       "avg_separation", NGS_FIRST), "avg_separation", "avg_separation_known")
        if pos in APPLICABLE_POSITIONS["tprr"]:
            wide = add("tprr", attach_tprr(req, routes_raw, tgt_raw), "tprr", "tprr_known")

        wide = add("implied_team_total", attach_lagw_team(req, itt_raw, "itt", "n",
                   "implied_team_total", 5.0), "implied_team_total", "implied_team_total_known")

        if pos in APPLICABLE_POSITIONS["tshare_stability"]:
            wide = add("tshare_stability", build_tshare_stability(req, tshare_raw),
                       "tshare_stability", "tshare_stability_known")
        wide = add("team_pace", attach_lagw_team(req, pace_raw, "plays_pg", "games", "team_pace", 8.0),
                   "team_pace", "team_pace_known")
        wide = add("is_contract_year", attach_contract_year(req, contracts_raw),
                   "is_contract_year", "contract_known")
        wide = add("hc_disruption", attach_coaching_disruption(req, coach_raw),
                   "hc_disruption", "hc_disruption_known")
        if pos in APPLICABLE_POSITIONS["ol_ybc"]:
            wide = add("ol_ybc", attach_lagw_team(req, ol_raw, "ybc_pg", "carries_sum", "ol_ybc", 150.0),
                       "ol_ybc", "ol_ybc_known")
        wide = add("two_wr_rate", attach_lagw_team(req, twowr_raw, "two_wr_rate", "snaps",
                   "two_wr_rate", 300.0), "two_wr_rate", "two_wr_rate_known")

        wide = add("proe", attach_lagw_team(req, proe_raw, "proe", "plays", "proe", 50.0),
                   "proe", "proe_known")
        wide = add("oc_disruption", attach_oc_disruption(req, oc_raw),
                   "oc_disruption", "oc_disruption_known")

        inc = incumbents[pos]
        wide = add("age", inc.assign(age_known=inc["age"].notna().astype(int)),
                   "age", "age_known")
        wide = add("draft_capital",
                   inc.assign(draft_capital_known=1, draft_capital=inc["log_draft_pick"]),
                   "draft_capital", "draft_capital_known")
        share_col = "tshare_w" if pos in ("WR", "TE") else ("cshare_w" if pos == "RB" else None)
        if share_col is not None:
            wide = add("share_level",
                       inc.assign(share_level_known=inc[share_col].notna().astype(int),
                                  share_level=inc[share_col]),
                       "share_level", "share_level_known")
        if pos in APPLICABLE_POSITIONS["adot"]:
            adot_val = np.where(inc["adot_den"] > 0,
                                inc["adot_num"] / inc["adot_den"].replace(0, np.nan), np.nan)
            wide = add("adot", inc.assign(adot=adot_val, adot_known=(inc["adot_den"] > 0).astype(int)),
                       "adot", "adot_known")
        not_rookie = (~inc["is_rookie"].astype(bool)).astype(int)
        wide = add("depth_rostered_absent",
                   inc.assign(depth_rostered_absent=inc["rostered_absent_share_1"],
                              depth_rostered_absent_known=not_rookie),
                   "depth_rostered_absent", "depth_rostered_absent_known")
        wide = add("depth_offroster",
                   inc.assign(depth_offroster=inc["offroster_share_1"],
                              depth_offroster_known=not_rookie),
                   "depth_offroster", "depth_offroster_known")
        wide = add("depth_first_share",
                   inc.assign(depth_first_share=inc["depth_first_share_1"],
                              depth_first_share_known=not_rookie),
                   "depth_first_share", "depth_first_share_known")
        wide = add("inj_missed_share",
                   inc.assign(inj_missed_share=inc["inj_missed_share_1"],
                              inj_missed_share_known=not_rookie),
                   "inj_missed_share", "inj_missed_share_known")
        wide = add("inj_unexp_missed_share",
                   inc.assign(inj_unexp_missed_share=inc["unexp_missed_share_1"],
                              inj_unexp_missed_share_known=not_rookie),
                   "inj_unexp_missed_share", "inj_unexp_missed_share_known")

        return wide

    print("Building wide feature frames per position...")
    wide_by_pos = {pos: build_wide(pos) for pos in POSITIONS}

    # ------------------------------------------------ individual screen
    results: List[Dict] = []
    for pos in POSITIONS:
        wide = wide_by_pos[pos]
        for fname, cols in APPLICABLE_POSITIONS.items():
            if pos not in cols or fname not in wide.columns:
                continue
            frame = wide[["player_id", "season", fname]].copy()
            frame[f"{fname}_known"] = wide[fname].notna().astype(int)
            row = screen_one(fname, FACTOR_CLASS[fname], pos, frame, fname,
                             f"{fname}_known", points, prior_lookup)
            row["ledger_row"] = LEDGER_ROW.get(fname, "?")
            results.append(row)
    res_df = pd.DataFrame(results)

    # ------------------------------------------------ collinearity map
    colin_rows = []
    for pos in POSITIONS:
        wide = wide_by_pos[pos]
        cols = [c for c in wide.columns if c not in ("player_id", "season")]
        for i, c1n in enumerate(cols):
            for c2n in cols[i + 1:]:
                r, n = spearman(wide[c1n].to_numpy(dtype=float), wide[c2n].to_numpy(dtype=float))
                colin_rows.append({"position": pos, "factor_a": c1n, "factor_b": c2n, "rho": r, "n": n})
    colin_df = pd.DataFrame(colin_rows)

    # ------------------------------------------------ within-cluster contrasts
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
        cr = screen_one(cname, klass, pos, frame, cname, f"{cname}_known", points, prior_lookup)
        cr["contrast_of"] = f"{a} (rho={row['rho']:.3f} vs {b})"
        contrast_results.append(cr)

    contrast_df = pd.DataFrame(contrast_results)

    res_df.to_csv(OUT / "standalone_screen2_results.csv", index=False)
    colin_df.to_csv(OUT / "standalone_screen2_collinearity.csv", index=False)
    if len(contrast_df):
        contrast_df.to_csv(OUT / "standalone_screen2_contrasts.csv", index=False)

    print(f"\nWrote {OUT/'standalone_screen2_results.csv'} ({len(res_df)} rows)")
    print(f"Wrote {OUT/'standalone_screen2_collinearity.csv'} ({len(colin_df)} rows)")
    print(f"Wrote {OUT/'standalone_screen2_contrasts.csv'} ({len(contrast_df)} rows, "
          f"{len(seen)} tight clusters at |rho|>={TIGHT})")

    print("\n=== INDIVIDUAL FACTOR SCREEN ===")
    for _, row in res_df.sort_values(["position", "factor"]).iterrows():
        print(f"{row['position']:3s} {row['factor']:24s} [{row['class']:11s}] "
              f"raw={row['raw_rho_pooled']:.4f}(n={row['raw_n']:.0f})  "
              f"partial={row['partial_rho_pooled']:.4f}(n={row['partial_n']:.0f})  "
              f"beats_agg={row['beats_aggregate_delta']:.4f}  "
              f"seasons+/-/0={row['n_seasons_pos']}/{row['n_seasons_neg']}/{row['n_seasons_zero']}")

    print("\n=== TIGHT CLUSTERS (|rho|>=0.6) AND THEIR CONTRASTS ===")
    for _, row in contrast_df.sort_values(["position", "factor"]).iterrows():
        print(f"{row['position']:3s} {row['factor']:44s} [{row['class']:11s}] "
              f"({row.get('contrast_of','')}) "
              f"raw={row['raw_rho_pooled']:.4f}(n={row['raw_n']:.0f})  "
              f"beats_agg={row['beats_aggregate_delta']:.4f}")


if __name__ == "__main__":
    main()
