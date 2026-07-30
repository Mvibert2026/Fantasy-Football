"""Factor batch 6 features -- QB passing efficiency, sack avoidance, and xFP.

Design: `docs/ranking/factor-batch-6-precommit.md`, committed BEFORE any arm was
fitted. Wraps `factor_features.build_factor_features` and only ever APPENDS
columns, so batches 1-3 keep reproducing bit for bit and every batch-6 arm
differs from its primary by exactly the block it declares.

NOTHING IN THIS MODULE READS SEASON N. There is no proxy block here at all --
every source is seasons <= N-1 -- so every batch-6 arm runs with
`allow_preseason_proxy=False` and the harness PROVES zero season-N reads rather
than the write-up asserting them.

WHY THE SOURCES ARE LOADED HERE AND NOT ADDED TO `SeasonPanel`. Batch 3 added
`_ngs`/`_rush` fields to `pos_data.SeasonPanel`. Three factor batches are running
concurrently against that file, so batch 6 loads its own two sources behind its
own cutoff gate and appends the SAME `("feature", cutoff)` entry to
`panel.access_log` that `panel.before()` would. The existing look-ahead audit
therefore sees these reads exactly as it sees every other feature read; no shared
file is touched.

FOUR BLOCKS.

  P  PASSING EFFICIENCY (QB)  `epa_db_w`, `anya_w`, `pratg_w`, `cpoe_w`,
     `qbeff_known`, `cpoe_known`.

     A MEASURED CORRECTION TO THE DISPATCH THAT COMMISSIONED THIS BATCH, made
     before any arm was fitted. The dispatch states that `passing_cpoe` in
     `player_weekly_stats` is "only 11% populated" and that EPA must therefore be
     derived from `pbp`. Both halves are wrong on this database:

       * `passing_cpoe` is 2.7% populated across ALL rows -- because a wide
         receiver has no completion percentage. Restricted to the rows that can
         have one (QB, >=10 attempts, 2006+) it is **99.9%** populated.
       * `passing_epa` is **100%** populated for QB weeks with >=10 attempts,
         **1999-2025**.
       * `pbp` as ingested has **no `epa`, `cpoe`, `sack` or `success` column at
         all** (24 columns; see `PRAGMA table_info(pbp)`), so deriving EPA from it
         is not merely unnecessary, it is impossible.

     So the strongest external QB claim in the sweep -- EPA/dropback, r~0.60 --
     is testable here on the DEEP sample rather than being blocked or proxied.

  K  SACK AVOIDANCE (QB)  `sackrate_w`. Sacks per dropback. `sacks_suffered` is
     100% populated in `player_weekly_stats` 1999+, so this needs neither `pbp`
     nor `pfr_advstats_pass`.

  X  EXPECTED FANTASY POINTS (QB, RB, WR, TE)  `xfp_pg_w`, `xfp_resid_pg_w`,
     `xfp_known`, from `ff_opportunity`.

     WHAT xFP ACTUALLY IS, stated before it is used. `ff_opportunity` is the
     ffverse `ffopportunity` package's output: a set of prebuilt **xgboost models
     over nflverse play-by-play** that predict, for each play, the expected
     completions / yards / touchdowns / first downs / two-point conversions /
     interceptions given PLAY CONTEXT (down, distance, yardline, air yards, pass
     location and so on). It prices the OPPORTUNITY, not the player: two
     receivers running the same route from the same spot on the same down get the
     same expected value. Those per-play expectations are then summed and
     converted to fantasy points.

     THREE CONSEQUENCES, none of them optional to state:

     1. **It is PPR, not this league.** Verified rather than assumed: Jahan
        Dotson 2023 REG = 49 rec / 518 yds / 4 TD, and `total_fantasy_points` =
        124.8 = 49*1.0 + 51.8 + 24.0 exactly. Full PPR, no yardage bonuses. So
        `total_fantasy_points_exp` is NOT "expected points in our league" and is
        used here only as a usage-quality INDEX. Anything on screen calling it
        expected points would be a false claim about our own product.

     2. **It overlaps what the model already holds.** Expected receiving points
        are close to a nonlinear function of targets and air-yards context, and
        the volume specs already carry `tpg_w`, `tshare_w`, `adot` and `ppg_w`.
        The genuinely new content is the removal of realised-touchdown noise --
        and registry #19 already measured that the model's existing empirical-
        Bayes TD shrinkage extracts most of it (discarding own TD rate was
        HARMFUL at all four positions). A large effect here is therefore a
        suspected overlap or leak first and a finding second.

     3. **The model was fitted on all seasons, including the target season.** The
        published artifact is one global play-context map trained on 2006-current;
        it cannot be refitted per season from here. This does not put
        player-specific season-N information into an N-1 feature -- the map has no
        player identity in it -- but it is a real, non-zero, non-player-specific
        contamination and it is named rather than hidden.

     REG-SEASON FILTER. `ff_opportunity` has no `season_type` column and carries
     playoff weeks (max week 21 pre-2021, 22 after). Rows are filtered to
     `week <= season_length(season) + 1`, which is exactly the REG-season week
     count the rest of the harness uses.

  --  CONVENTION SHARED WITH `ppg_w`, chosen so an arm is one change and not two.
     `xfp_pg_w` is built with the IDENTICAL weighting `pos_features` uses for
     `ppg_w`: weight `LAG_WEIGHTS[k] * min(gshare_k, 1)`, a lag with no source row
     contributing 0 to the numerator and its full weight to the denominator.
     Median-imputing the missing lags instead would have made the "replace
     `ppg_w` with `xfp_pg_w`" arm differ by two things. The coverage difference
     that convention creates is exactly what the registered `xfp_known` control
     arm exists to detect.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation, SeasonPanel,
    season_length,
)
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS
from experiments.bottomup.factors.factor_features import build_factor_features

#: Empirical-Bayes shrinkage constant for every QB efficiency rate, in units of
#: the rate's own denominator (dropbacks, or attempts for passer rating). FIXED A
#: PRIORI at 100 -- roughly three starts, and the same order of magnitude as the
#: QB universe's own qualification bar of 30 attempts -- and never tuned against
#: any result. One constant for all five metrics, so no metric gets a bespoke
#: knob the others did not.
QBEFF_K0 = 100.0

#: First season with `passing_cpoe`. EPA, ANY/A, passer rating and sack rate all
#: go back to 1999; CPOE does not exist before this.
CPOE_FIRST_SEASON = 2006


# ---------------------------------------------------------------- QB efficiency
_QBEFF_SQL = """
SELECT season, player_id,
       SUM(COALESCE(attempts,0))              AS att,
       SUM(COALESCE(completions,0))           AS cmp,
       SUM(COALESCE(passing_yards,0))         AS pass_yards,
       SUM(COALESCE(passing_tds,0))           AS pass_tds,
       SUM(COALESCE(passing_interceptions,0)) AS ints,
       SUM(COALESCE(sacks_suffered,0))        AS sacks,
       SUM(COALESCE(passing_epa,0))           AS epa,
       SUM(CASE WHEN passing_cpoe IS NOT NULL
                THEN passing_cpoe * COALESCE(attempts,0) ELSE 0 END) AS cpoe_num,
       SUM(CASE WHEN passing_cpoe IS NOT NULL
                THEN COALESCE(attempts,0) ELSE 0 END)                AS cpoe_den
FROM player_weekly_stats
WHERE season_type = 'REG' AND season < ? AND COALESCE(attempts,0) > 0
GROUP BY season, player_id
"""


def load_qb_efficiency(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season) passing-efficiency ingredients, REG only.

    Not restricted to `position = 'QB'`: a running back's trick-play pass is a
    dropback and belongs in the denominator of his own rate if he has one. The
    universe already decides who is a quarterback.

    CPOE is aggregated as an ATTEMPT-WEIGHTED sum so that a 45-attempt game and a
    9-attempt game do not count equally, which an unweighted per-week mean would
    do.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_QBEFF_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(d) and (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("QB-efficiency holdout rows leaked past the SQL gate")
    d["dropbacks"] = d["att"] + d["sacks"]
    # ANY/A numerator, the standard definition: yards + 20*TD - 45*INT
    d["anya_num"] = d["pass_yards"] + 20.0 * d["pass_tds"] - 45.0 * d["ints"]
    return d


# -------------------------------------------------------------------------- xFP
_XFP_SQL = """
SELECT CAST(season AS INTEGER)                 AS season,
       player_id,
       CAST(week AS INTEGER)                   AS week,
       COALESCE(total_fantasy_points_exp, 0.0) AS xfp,
       COALESCE(total_fantasy_points, 0.0)     AS fp_ppr
FROM ff_opportunity
WHERE player_id IS NOT NULL AND player_id <> ''
  AND CAST(season AS INTEGER) < ?
"""


def load_xfp(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season) expected and realised PPR points, REG weeks only.

    `ff_opportunity` has no `season_type` column and does carry playoff weeks, so
    the REG filter is applied here on the same week count the rest of the harness
    uses (`season_length(season) + 1`). Without it a player's per-game xFP would
    silently include January.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_XFP_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "xfp", "fp_ppr", "wks"])
    if (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("xFP holdout rows leaked past the SQL gate")
    reg_weeks = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg_weeks]
    return d.groupby(["season", "player_id"], as_index=False).agg(
        xfp=("xfp", "sum"), fp_ppr=("fp_ppr", "sum"), wks=("week", "size"))


# ------------------------------------------------------------- the gated source
class _Batch6Source:
    """The two batch-6 tables behind one cutoff gate.

    Loaded once per process. `before(panel, cutoff)` asserts the cutoff the same
    way `SeasonPanel.before` does and appends the SAME `("feature", cutoff)`
    entry to the panel's access log, so the existing look-ahead audit covers
    these reads without `pos_data.py` being touched -- three factor batches are
    editing that file concurrently.
    """

    def __init__(self, db_path: Path = DEFAULT_DB) -> None:
        self.qbeff = load_qb_efficiency(db_path)
        self.xfp = load_xfp(db_path)

    def before(self, panel: SeasonPanel, cutoff: int
               ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        q = self.qbeff[self.qbeff["season"] <= cutoff]
        x = self.xfp[self.xfp["season"] <= cutoff]
        if (len(q) and q["season"].max() > cutoff) or \
           (len(x) and x["season"].max() > cutoff):
            raise CutoffViolation("batch-6 cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return q, x


_SOURCE: Optional[_Batch6Source] = None


def source(db_path: Path = DEFAULT_DB) -> _Batch6Source:
    global _SOURCE
    if _SOURCE is None:
        _SOURCE = _Batch6Source(db_path)
    return _SOURCE


# ------------------------------------------------------------------- utilities
def _lag_weights(f: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Reproduce `pos_features`' own weighting exactly: `LAG_WEIGHTS[k] *
    min(gshare_k, 1)`, and `wsum` which that module exposes as `evidence`.

    Rebuilt from `f`'s own columns rather than imported, because it must be the
    same numbers `ppg_w` was built with or the "replace `ppg_w`" arm is not one
    change.
    """
    n = len(f)
    w = np.zeros((n, N_LAGS))
    for k in range(1, N_LAGS + 1):
        gs = np.asarray(f.get(f"gshare_{k}", pd.Series(np.zeros(n))),
                        dtype=float)
        w[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(np.nan_to_num(gs), 1.0)
    return w, w.sum(axis=1)


def _wavg_per_game(f: pd.DataFrame, per_lag: Dict[int, np.ndarray],
                   w: np.ndarray, wsum: np.ndarray) -> np.ndarray:
    """`ppg_w`'s exact construction: weighted mean of (season total / games)."""
    num = np.zeros(len(f))
    for k in range(1, N_LAGS + 1):
        g = np.asarray(f.get(f"games_{k}", pd.Series(np.zeros(len(f)))), dtype=float)
        gl = np.where(g > 0, g, np.nan)
        num += w[:, k - 1] * np.nan_to_num(per_lag[k] / gl, nan=0.0)
    return np.where(wsum > 0, num / np.where(wsum > 0, wsum, 1.0), np.nan)


def _lag_map(tbl: pd.DataFrame, pid: pd.Series, season: int, col: str
             ) -> np.ndarray:
    lag = tbl[tbl["season"] == season]
    if not len(lag):
        return np.zeros(len(pid))
    s = lag.drop_duplicates("player_id").set_index("player_id")[col]
    return np.asarray(pid.map(s).astype(float).fillna(0.0))


# --------------------------------------------------------- P + K: QB efficiency
def _passer_rating(cmp_rate: np.ndarray, ypa: np.ndarray, tdpa: np.ndarray,
                   intpa: np.ndarray) -> np.ndarray:
    """The NFL formula, on rates that have already been shrunk.

    Applied to shrunk rates rather than raw ones so that a quarterback with 31
    attempts is not handed a 158.3 by three lucky throws. Every clip below is
    part of the official definition, not a modelling choice.
    """
    a = np.clip((cmp_rate - 0.3) * 5.0, 0.0, 2.375)
    b = np.clip((ypa - 3.0) * 0.25, 0.0, 2.375)
    c = np.clip(tdpa * 20.0, 0.0, 2.375)
    d = np.clip(2.375 - intpa * 25.0, 0.0, 2.375)
    return (a + b + c + d) / 6.0 * 100.0


def _qb_efficiency(panel: SeasonPanel, f: pd.DataFrame, target_season: int,
                   db_path: Path = DEFAULT_DB) -> Dict[str, np.ndarray]:
    qb, _ = source(db_path).before(panel, target_season - 1)
    n = len(f)
    if not len(qb):
        z = np.zeros(n)
        return {k: z.copy() for k in ("epa_db_w", "anya_w", "pratg_w", "cpoe_w",
                                      "sackrate_w", "qbeff_known", "cpoe_known")}

    # Pooled priors from every pre-cutoff dropback. One population, one prior per
    # rate, computed on exactly the rows the arm is allowed to see.
    tot_db = float(qb["dropbacks"].sum())
    tot_att = float(qb["att"].sum())
    prior = {
        "epa": float(qb["epa"].sum()) / max(tot_db, 1.0),
        "anya": float(qb["anya_num"].sum()) / max(tot_db, 1.0),
        "sack": float(qb["sacks"].sum()) / max(tot_db, 1.0),
        "cmp": float(qb["cmp"].sum()) / max(tot_att, 1.0),
        "ypa": float(qb["pass_yards"].sum()) / max(tot_att, 1.0),
        "tdpa": float(qb["pass_tds"].sum()) / max(tot_att, 1.0),
        "intpa": float(qb["ints"].sum()) / max(tot_att, 1.0),
        "cpoe": float(qb["cpoe_num"].sum()) / max(float(qb["cpoe_den"].sum()), 1.0),
    }

    pid = f["player_id"]
    acc = {c: np.zeros(n) for c in ("epa", "anya_num", "sacks", "dropbacks",
                                    "cmp", "pass_yards", "pass_tds", "ints",
                                    "att", "cpoe_num", "cpoe_den")}
    for k in range(1, N_LAGS + 1):
        wk = LAG_WEIGHTS[k - 1]
        for c in acc:
            acc[c] += wk * _lag_map(qb, pid, target_season - k, c)

    db = acc["dropbacks"]
    att = acc["att"]
    k0 = QBEFF_K0

    def eb(num, den, p):
        return (num + k0 * p) / (den + k0)

    cmp_rate = eb(acc["cmp"], att, prior["cmp"])
    ypa = eb(acc["pass_yards"], att, prior["ypa"])
    tdpa = eb(acc["pass_tds"], att, prior["tdpa"])
    intpa = eb(acc["ints"], att, prior["intpa"])

    return {
        "epa_db_w": eb(acc["epa"], db, prior["epa"]),
        "anya_w": eb(acc["anya_num"], db, prior["anya"]),
        "pratg_w": _passer_rating(cmp_rate, ypa, tdpa, intpa),
        "cpoe_w": eb(acc["cpoe_num"], acc["cpoe_den"], prior["cpoe"]),
        "sackrate_w": eb(acc["sacks"], db, prior["sack"]),
        "qbeff_known": (db > 0).astype(float),
        "cpoe_known": (acc["cpoe_den"] > 0).astype(float),
    }


# ----------------------------------------------------------------------- X: xFP
def _xfp(panel: SeasonPanel, f: pd.DataFrame, target_season: int,
         db_path: Path = DEFAULT_DB) -> Dict[str, np.ndarray]:
    _, xf = source(db_path).before(panel, target_season - 1)
    n = len(f)
    if not len(xf):
        z = np.zeros(n)
        return {"xfp_pg_w": z, "xfp_resid_pg_w": z.copy(), "xfp_known": z.copy()}

    w, wsum = _lag_weights(f)
    pid = f["player_id"]
    xfp_lag, res_lag = {}, {}
    seen = np.zeros(n)
    for k in range(1, N_LAGS + 1):
        s = target_season - k
        x = _lag_map(xf, pid, s, "xfp")
        a = _lag_map(xf, pid, s, "fp_ppr")
        xfp_lag[k] = x
        # THE LUCK TERM. Realised minus expected, both from ff_opportunity's OWN
        # PPR ledger -- never mixed with this league's points, or the residual
        # would be part scoring-rule difference and part luck.
        res_lag[k] = a - x
        has = xf[xf["season"] == s]
        if len(has):
            seen += w[:, k - 1] * pid.isin(set(has["player_id"])).to_numpy().astype(float)

    return {
        "xfp_pg_w": _wavg_per_game(f, xfp_lag, w, wsum),
        "xfp_resid_pg_w": _wavg_per_game(f, res_lag, w, wsum),
        "xfp_known": (seen > 0).astype(float),
    }


# ------------------------------------------------------------------ the builder
def build_factor6_features(panel: SeasonPanel, universe: pd.DataFrame,
                           target_season: int,
                           blocks: Tuple[str, ...] = (),
                           db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """`blocks` names exactly which batch-6 block to compute: `qbeff`, `xfp`.

    With `blocks=()` this is bit-for-bit the batch-1/2/3 primary feature set, so
    the primary every arm is differenced against is the same object those batches
    reported against.
    """
    f = build_factor_features(panel, universe, target_season, use_proxy=False)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    if "qbeff" in blocks:
        block.update(_qb_efficiency(panel, f, target_season, db_path))
    if "xfp" in blocks:
        block.update(_xfp(panel, f, target_season, db_path))
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
