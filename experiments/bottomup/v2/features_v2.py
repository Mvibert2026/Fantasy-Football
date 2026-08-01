"""v2 feature builders. Wrap `build_features` (unchanged, byte-for-byte the
batches-1-7 features), then add the registered blocks of batch-B1 §3.

Two builders, because the arms must differ by exactly one thing and the audit
must be able to prove it:

  build_features_v2        G0/G1 — adds the week-shape block. Zero proxy reads.
  build_features_v2_proxy  G2    — the above PLUS the week-1-of-N roster-status
                                   indicators, via `panel.preseason_roster(N)`,
                                   which logs under the `proxy` audit tag. A run
                                   that did not declare the proxy still asserts
                                   `n_preseason_proxy_reads == 0` and would
                                   crash on contact.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..components.pos_features import build_features
from .weekshape import V2Panel

#: batch-B1 §3, frozen at registration. Order matters only for readability.
G1_FEATURES = [
    "late4_share_1", "endgap_share_1", "played_thru_1",
    "gshare_w", "gshare_max3", "present_1", "evidence", "age", "age2",
    "chronic_missed_share", "miss1_x_endgap", "miss1_x_resolved",
]
WK1_FEATURES = ["wk1_available", "wk1_reserve"]


def _weekshape_block(panel: V2Panel, f: pd.DataFrame,
                     target_season: int) -> pd.DataFrame:
    """The registered G1 block. Absence conventions, fixed here: a player with
    no N−1 week-shape row (absent the whole season) gets late4_share_1 = 0,
    endgap_share_1 = 1, played_thru_1 = 0 — i.e. maximally unresolved, which is
    what a full missed season is from the September vantage point."""
    s1 = target_season - 1
    ws = panel.weekshape_before(s1)
    w1 = ws[ws["season"] == s1].set_index("player_id")
    idx = f["player_id"]

    def col(name, default):
        if len(w1) and name in w1.columns:
            return np.asarray(idx.map(w1[name]).astype(float).fillna(default))
        return np.full(len(f), default, dtype=float)

    # schedule length of N−1, from the data; fall back to 18/17 by era only if
    # the season is somehow absent from the frame (it cannot be, post-1999)
    wk_max_default = 18.0 if s1 >= 2021 else 17.0
    wk_max = col("wk_max", wk_max_default)
    last_wk = col("last_wk", 0.0)
    late4 = col("late4", 0.0)

    f = f.copy()
    f["late4_share_1"] = np.clip(late4 / 4.0, 0.0, 1.0)
    f["endgap_share_1"] = np.clip((wk_max - last_wk) / np.maximum(wk_max, 1.0),
                                  0.0, 1.0)
    f["played_thru_1"] = (last_wk >= wk_max - 1).astype(float)

    # chronic missed share over the three lags, counting only lags the player
    # was present for; a veteran absent from all three lags gets 1.0
    miss_terms = np.zeros(len(f))
    present_ct = np.zeros(len(f))
    for k in (1, 2, 3):
        pres = f[f"present_{k}"].fillna(0.0).to_numpy(dtype=float) \
            if f"present_{k}" in f.columns else np.zeros(len(f))
        gs = f[f"gshare_{k}"].fillna(0.0).to_numpy(dtype=float) \
            if f"gshare_{k}" in f.columns else np.zeros(len(f))
        miss_terms += pres * np.clip(1.0 - gs, 0.0, 1.0)
        present_ct += pres
    f["chronic_missed_share"] = np.where(present_ct > 0,
                                         miss_terms / np.maximum(present_ct, 1.0),
                                         1.0)

    pres1 = f["present_1"].fillna(0.0).to_numpy(dtype=float)
    gs1 = f["gshare_1"].fillna(0.0).to_numpy(dtype=float)
    miss1 = np.where(pres1 > 0, np.clip(1.0 - gs1, 0.0, 1.0), 1.0)
    f["miss1_x_endgap"] = miss1 * f["endgap_share_1"].to_numpy(dtype=float)
    f["miss1_x_resolved"] = miss1 * f["late4_share_1"].to_numpy(dtype=float)
    return f


def build_features_v2(panel: V2Panel, universe: pd.DataFrame,
                      target_season: int) -> pd.DataFrame:
    f = build_features(panel, universe, target_season)
    return _weekshape_block(panel, f, target_season)


def build_features_v2_proxy(panel: V2Panel, universe: pd.DataFrame,
                            target_season: int) -> pd.DataFrame:
    """G2 only. Week-1-of-N roster status; reference class = on no week-1
    roster. The as-of caveat travels with the arm (batch-B1): week-1 status is
    set at the late-August cutdown, around a real draft rather than strictly
    before it. Its ADOPTION is conditional on a strategist ruling; its
    MEASUREMENT is what this builder exists for."""
    f = build_features_v2(panel, universe, target_season)
    r = panel.preseason_roster(target_season)
    if len(r):
        avail = r.groupby("player_id")["available"].max()
        contract = r.groupby("player_id")["under_contract"].max()
        a = np.asarray(f["player_id"].map(avail).astype(float).fillna(0.0))
        c = np.asarray(f["player_id"].map(contract).astype(float).fillna(0.0))
    else:
        a = np.zeros(len(f))
        c = np.zeros(len(f))
    f = f.copy()
    f["wk1_available"] = a
    f["wk1_reserve"] = np.clip(c - a, 0.0, 1.0)   # under contract, cannot play
    return f
