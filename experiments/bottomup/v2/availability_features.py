"""Batch-D1 feature blocks for the projected-games component.

Every column here is a function of season N-1 (and N-2 for the recurrence flag)
only. Nothing reads season N. `week1_roster`/`preseason_roster` -- the G2a proxy
strategist has not admitted -- is never touched, and an arm built here still
asserts `n_preseason_proxy_reads == 0`.

BLOCK STRUCTURE, one block per registered arm (batch-D1 §3):

  B0   the incumbent availability feature list (`pos_features.AVAIL_A`), so an
       arm differing only in ESTIMATOR FORM can be measured on its own.
  P    practice participation from `injuries` -- DNP / Limited / Full weeks.
  C    injury class (structural / soft-tissue / head / rest) and cross-season
       recurrence of the dominant class.
  R    roster status from `rosters_weekly` season N-1 -- weeks on reserve, and
       whether the reserve stint was ONGOING at season end or RESOLVED.

Each block adds ONE interaction with lag-1 missed share, and only where the
recon motivated it, because the GLM is linear in the logit and the whole
resolved-vs-ongoing hypothesis is conditional: an ongoing IR designation is
informative GIVEN that a lot of the season was missed, and near-vacuous
otherwise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..components.pos_data import season_length
from .availability_data import SRC_FIRST_SEASON
from .features_v2 import build_features_v2

#: the incumbent list, verbatim from `pos_features.AVAIL_A`. Arm B0 is this
#: feature set under the binomial GLM instead of clipped OLS -- form only.
B0_FEATURES = ["gshare_w", "gshare_1", "present_1", "age", "age2", "evidence"]

P_FEATURES = ["prac_rep_share_1", "prac_dnp_share_1", "prac_lim_share_1",
              "prac_out_share_1", "prac_dnp_of_rep_1", "prac_dnp_late3_1",
              "miss1_x_dnp_share"]
C_FEATURES = ["inj_struct_share_1", "inj_soft_share_1", "inj_head_share_1",
              "inj_rest_share_1", "inj_nclass_1", "inj_recur_1",
              "inj_recur_known_1"]
R_FEATURES = ["res_share_1", "res_end_1", "res_resolved_1", "act_share_1",
              "miss1_x_res_end"]

#: bare player-level presence indicators. Each is the paired control for its
#: block, in batch 5's `routes_known` geometry: if "he appears in this source at
#: all" does as much as the block built on top of it, the block is an EMPLOYMENT
#: proxy and not an injury signal. Recon measured rho(rep_wks, games_N) = +0.236
#: on the full population -- positive, because appearing on an injury report
#: means you were on a roster. That confound is the reason these arms exist.
PRESENCE_CONTROL = {"A1": "prac_present_1", "A3": "ros_present_1"}

PLACEBO_COL = "avail_placebo"
PLACEBO_SEED = 20260802

BLOCKS = {
    "B0": [],
    "P": P_FEATURES,
    "C": C_FEATURES,
    "R": R_FEATURES,
}


def _miss1(f: pd.DataFrame) -> np.ndarray:
    """Lag-1 missed share, with the same convention `features_v2` uses: a player
    absent from N-1 entirely counts as having missed all of it."""
    pres1 = f["present_1"].fillna(0.0).to_numpy(dtype=float)
    gs1 = f["gshare_1"].fillna(0.0).to_numpy(dtype=float)
    return np.where(pres1 > 0, np.clip(1.0 - gs1, 0.0, 1.0), 1.0)


def _practice_block(panel, f: pd.DataFrame, target_season: int) -> pd.DataFrame:
    s1 = target_season - 1
    pr = panel.practice_before(s1)
    p1 = pr[pr["season"] == s1].set_index("player_id") if len(pr) else pd.DataFrame()
    idx = f["player_id"]
    slen1 = float(season_length(s1))

    def col(name, default=0.0):
        if len(p1) and name in p1.columns:
            return np.asarray(idx.map(p1[name]).astype(float).fillna(default))
        return np.full(len(f), default, dtype=float)

    rep = col("rep_wks")
    dnp = col("dnp_wks")
    lim = col("lim_wks")
    out = col("out_wks")
    dnp3 = col("dnp_late3")
    f = f.copy()
    f["prac_present_1"] = (rep > 0).astype(float)
    f["prac_rep_share_1"] = rep / slen1
    f["prac_dnp_share_1"] = dnp / slen1
    f["prac_lim_share_1"] = lim / slen1
    f["prac_out_share_1"] = out / slen1
    f["prac_dnp_of_rep_1"] = np.where(rep > 0, dnp / np.maximum(rep, 1.0), 0.0)
    f["prac_dnp_late3_1"] = dnp3 / 3.0
    f["miss1_x_dnp_share"] = _miss1(f) * f["prac_dnp_share_1"].to_numpy(dtype=float)
    f["prac_src_known_1"] = float(s1 >= SRC_FIRST_SEASON["injuries"])
    return f


def _class_block(panel, f: pd.DataFrame, target_season: int) -> pd.DataFrame:
    s1, s2 = target_season - 1, target_season - 2
    pr = panel.practice_before(s1)
    idx = f["player_id"]
    slen1 = float(season_length(s1))
    p1 = pr[pr["season"] == s1].set_index("player_id") if len(pr) else pd.DataFrame()
    p2 = pr[pr["season"] == s2].set_index("player_id") if len(pr) else pd.DataFrame()

    def col(frame, name, default=0.0):
        if len(frame) and name in frame.columns:
            return np.asarray(idx.map(frame[name]).astype(float).fillna(default))
        return np.full(len(f), default, dtype=float)

    f = f.copy()
    for k, out in (("structural", "inj_struct_share_1"), ("soft", "inj_soft_share_1"),
                   ("head", "inj_head_share_1"), ("rest", "inj_rest_share_1")):
        f[out] = col(p1, f"cls_{k}_wks") / slen1
    f["inj_nclass_1"] = col(p1, "n_cls")

    d1 = idx.map(p1["dom_cls"]) if len(p1) and "dom_cls" in p1.columns \
        else pd.Series([None] * len(f), index=f.index)
    d2 = idx.map(p2["dom_cls"]) if len(p2) and "dom_cls" in p2.columns \
        else pd.Series([None] * len(f), index=f.index)
    both = d1.notna() & d2.notna()
    f["inj_recur_known_1"] = both.astype(float).to_numpy()
    f["inj_recur_1"] = (both & (d1 == d2)).astype(float).to_numpy()
    return f


def _roster_block(panel, f: pd.DataFrame, target_season: int) -> pd.DataFrame:
    s1 = target_season - 1
    rs = panel.rstatus_before(s1)
    r1 = rs[rs["season"] == s1].set_index("player_id") if len(rs) else pd.DataFrame()
    idx = f["player_id"]
    slen1 = float(season_length(s1))

    def col(name, default=0.0):
        if len(r1) and name in r1.columns:
            return np.asarray(idx.map(r1[name]).astype(float).fillna(default))
        return np.full(len(f), default, dtype=float)

    res = col("res_wks")
    act = col("act_wks")
    res_end = col("res_end")
    act_end = col("act_end")
    rwks = col("roster_wks")
    f = f.copy()
    f["ros_present_1"] = (rwks > 0).astype(float)
    f["res_share_1"] = np.clip(res / slen1, 0.0, 1.5)
    f["act_share_1"] = np.clip(act / slen1, 0.0, 1.5)
    f["res_end_1"] = res_end
    # RESOLVED: went on reserve during N-1 but was back on the active roster for
    # the final three weeks. The distinction the founder named and no arm in B1
    # could express.
    f["res_resolved_1"] = ((res > 0) & (act_end > 0) & (res_end <= 0)).astype(float)
    f["miss1_x_res_end"] = _miss1(f) * res_end
    f["ros_src_known_1"] = float(s1 >= SRC_FIRST_SEASON["rosters"])
    return f


def build_features_d1(panel, universe: pd.DataFrame, target_season: int,
                      blocks=(), placebo: bool = False,
                      presence_only: str = "") -> pd.DataFrame:
    """`blocks` is a subset of {'P','C','R'}; the base frame is always
    `build_features_v2` so the D1 arms sit on the same frame batch B1 used.

    `presence_only` builds ONE block purely to expose its bare player-level
    presence indicator (the paired control arms A1k / A3k) -- the block's value
    columns are computed but the arm's feature list will not name them.
    """
    f = build_features_v2(panel, universe, target_season)
    want = set(blocks)
    if presence_only:
        want.add(presence_only)
    if "P" in want:
        f = _practice_block(panel, f, target_season)
    if "C" in want:
        # the class block reads the same source; ensure the practice columns
        # exist too so `_known` accounting is complete
        if "prac_present_1" not in f.columns:
            f = _practice_block(panel, f, target_season)
        f = _class_block(panel, f, target_season)
    if "R" in want:
        f = _roster_block(panel, f, target_season)
    if placebo:
        rng = np.random.default_rng(PLACEBO_SEED + target_season)
        f = f.copy()
        f[PLACEBO_COL] = rng.standard_normal(len(f))
    return f
