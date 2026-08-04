"""Batches C5 + CT1 — the rest of the 75-factor pool, wired for the sweep.

Pool authority: `docs/ranking/standalone-screen-2.md` (75 = 35 base + 40
within-cluster contrasts). Coverage after this module: every base factor is a
registered arm somewhere (C1 6, C2 6, C3 6, C4 6, AB1 ablates the two channels
actually in the specs, C5 the rest), and every screened contrast construct is
a CT1 arm at the position cells the screen screened.

C5 — base factors not yet covered by any batch (registration `batch-C5.md`):

  C5P  PROE (pbp.xpass residual; never actually blocked)        T2P, 4 pos
  C5O  OC continuity (play_callers_preseason Wikipedia proxy)   T2P, 4 pos
  C5D  draft capital, veteran-additive (log_draft_pick,
       undrafted — in the frame, consumed by no veteran spec)   T2A, 4 pos
  C5A  aDOT (adot_num/adot_den, lag-weighted ratio)             T2P, RB/WR/TE
  C5R  roster/depth status trio (rostered_absent_share_1,
       offroster_share_1, depth_first_share_1 — lag-1)          T2P, 4 pos
  C5I  injury designations pair (inj_missed_share_1,
       unexp_missed_share_1 — lag-1)                            T2P, 4 pos
  F0C5 placebo                                                  T2A, 4 pos

CT1 — the 40 contrast constructs (registration `batch-CT1.md`). Construction
replicates the screen exactly: percentile-rank each component within the
frame (one season per frame, so within-season by construction), gap =
pr(a) − pr(b), known = both components known. Components are built by the
SAME block functions the batches use — no screen-only reimplementation.
The arm set and position cells come from `standalone_screen2_contrasts.csv`,
fixed by the screen before this module existed. Window per contrast = the
later of its two components' families. F0CT placebo = pr(noise1) − pr(noise2).
"""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..components.pos_data import DEFAULT_DB, HoldoutViolation
from ..factors.factor_features7 import _snap_share, _weighted_lag
from ..factors.factor_features5 import _routes_block
from ..factors.factor_features6 import _xfp
from . import ensemble070 as ens
from . import factors_c3_adapter as c3a
from . import factors_c4_adapter as c4a
from .ensemble070 import Arm070, POSITIONS
from .factors_c1 import _BASE_SPECS, _redzone_usage
from .factors_c2 import _implied_total, _wopr
from .features_v2 import build_features_v2

HOLDOUT_SEASON = 2025
_REPO_DB = DEFAULT_DB


# ------------------------------------------------------------- C5 loaders
_PROE_SQL = """SELECT season, posteam AS team, pass_attempt, xpass
FROM pbp WHERE season < ? AND posteam IS NOT NULL
  AND (pass_attempt = 1 OR rush_attempt = 1) AND xpass IS NOT NULL"""

_OC_SQL = """SELECT team, season, coach_id, confidence FROM play_callers_preseason
WHERE season < ? AND title = 'OC' AND coach_id IS NOT NULL"""

_PROE: Optional[pd.DataFrame] = None
_OC: Optional[pd.DataFrame] = None


def _load_proe() -> pd.DataFrame:
    global _PROE
    if _PROE is None:
        conn = sqlite3.connect(f"file:{_REPO_DB}?mode=ro", uri=True)
        try:
            d = pd.read_sql_query(_PROE_SQL, conn, params=(HOLDOUT_SEASON,))
        finally:
            conn.close()
        if len(d) and (d["season"] >= HOLDOUT_SEASON).any():
            raise HoldoutViolation("proe rows leaked past the SQL gate")
        out = d.groupby(["season", "team"], as_index=False).agg(
            pass_rate=("pass_attempt", "mean"), xpass_rate=("xpass", "mean"),
            plays=("pass_attempt", "size"))
        out["proe"] = out["pass_rate"] - out["xpass_rate"]
        _PROE = out[["season", "team", "proe", "plays"]]
    return _PROE


def _load_oc() -> pd.DataFrame:
    global _OC
    if _OC is None:
        conn = sqlite3.connect(f"file:{_REPO_DB}?mode=ro", uri=True)
        try:
            d = pd.read_sql_query(_OC_SQL, conn, params=(HOLDOUT_SEASON,))
        finally:
            conn.close()
        if not len(d):
            _OC = pd.DataFrame(columns=["season", "team", "oc_changed"])
            return _OC
        d["conf_rank"] = (d["confidence"] == "medium").astype(int)
        d = d.sort_values("conf_rank", ascending=False) \
            .drop_duplicates(["team", "season"], keep="first") \
            .sort_values(["team", "season"])
        d["prev_coach"] = d.groupby("team")["coach_id"].shift(1)
        d["prev_season"] = d.groupby("team")["season"].shift(1)
        consec = (d["season"] - d["prev_season"]) == 1
        d["oc_changed"] = np.where(
            consec, (d["coach_id"] != d["prev_coach"]).astype(float), np.nan)
        _OC = d[["season", "team", "oc_changed"]]
    return _OC


def _team_of(panel, f, ts) -> pd.Series:
    hist = panel.before(ts - 1)
    team = hist.sort_values("season").groupby("player_id")["team"].last()
    return f["player_id"].map(team)


def _block_proe(panel, f, ts):
    src = _load_proe()
    src = src[src["season"] <= ts - 1]
    panel.access_log.append(("feature", ts - 1))
    team = _team_of(panel, f, ts)
    lag = src[src["season"] == ts - 1].set_index("team")
    v = team.map(lag["proe"]) if len(lag) else pd.Series(np.nan, index=f.index)
    known = np.isfinite(v.to_numpy(dtype=float))
    med = float(np.nanmedian(v)) if known.any() else 0.0
    return {"proe_1": np.where(known, v, med),
            "proe_known": known.astype(float)}


def _block_oc(panel, f, ts):
    src = _load_oc()
    src = src[src["season"] <= ts - 1]
    panel.access_log.append(("feature", ts - 1))
    team = _team_of(panel, f, ts)
    lag = src[src["season"] == ts - 1].set_index("team")
    v = team.map(lag["oc_changed"]) if len(lag) else pd.Series(np.nan, index=f.index)
    known = np.isfinite(v.to_numpy(dtype=float))
    return {"oc_disruption_1": np.where(known, v, 0.0),
            "oc_known": known.astype(float)}


def _block_draft(panel, f, ts):
    return {"log_draft_pick_v": f["log_draft_pick"].fillna(
                np.log(300.0)).to_numpy(dtype=float),
            "undrafted_v": f["undrafted"].fillna(1).to_numpy(dtype=float)}


def _block_adot(panel, f, ts):
    num = f["adot_num"].to_numpy(dtype=float)
    den = f["adot_den"].to_numpy(dtype=float)
    known = np.isfinite(num) & np.isfinite(den) & (den > 0)
    v = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), np.nan)
    med = float(np.nanmedian(v)) if known.any() else 0.0
    return {"adot_w": np.where(known, v, med), "adot_known": known.astype(float)}


def _frame_pair(cols_map: Dict[str, str]):
    def block(panel, f, ts):
        out = {}
        for new, src in cols_map.items():
            v = f[src].to_numpy(dtype=float) if src in f.columns \
                else np.full(len(f), np.nan)
            out[new] = np.nan_to_num(v, nan=0.0)
        # base features carry a real value for every veteran with a prior
        # season; rookies have none, which is the correct unknown state
        out[list(cols_map)[0].rsplit("_", 1)[0] + "_known"] = \
            (f["evidence"].fillna(0.0) > 0).to_numpy(dtype=float) \
            if "evidence" in f.columns else np.ones(len(f))
        return out
    return block


def _block_c5_placebo(panel, f, ts):
    def draw(pid, salt):
        h = hashlib.sha256(f"C5-placebo{salt}|{ts}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    return {"placebo_noise_c5": np.array(
        [draw(p, "") for p in f["player_id"]], dtype=float)}


C5_BLOCKS: Dict[str, Callable] = {
    "C5P": _block_proe,
    "C5O": _block_oc,
    "C5D": _block_draft,
    "C5A": _block_adot,
    "C5R": _frame_pair({"ros_absent_v": "rostered_absent_share_1",
                        "offroster_v": "offroster_share_1",
                        "depth_first_v": "depth_first_share_1"}),
    "C5I": _frame_pair({"injm_v": "inj_missed_share_1",
                        "injum_v": "unexp_missed_share_1"}),
    "F0C5": _block_c5_placebo,
}

C5_COLS: Dict[str, List[str]] = {
    "C5P": ["proe_1", "proe_known"],
    "C5O": ["oc_disruption_1", "oc_known"],
    "C5D": ["log_draft_pick_v", "undrafted_v"],
    "C5A": ["adot_w", "adot_known"],
    "C5R": ["ros_absent_v", "offroster_v", "depth_first_v", "ros_absent_known"],
    "C5I": ["injm_v", "injum_v", "injm_known"],
    "F0C5": ["placebo_noise_c5"],
}

C5_KNOWN: Dict[str, Optional[str]] = {
    "C5P": "proe_known", "C5O": "oc_known", "C5D": None,
    "C5A": "adot_known", "C5R": "ros_absent_known", "C5I": "injm_known",
    "F0C5": None,
}

C5_FAMILY: Dict[str, str] = {
    "C5P": "T2P", "C5O": "T2P", "C5D": "T2A", "C5A": "T2P",
    "C5R": "T2P", "C5I": "T2P", "F0C5": "T2A",
}

C5_POSITIONS: Dict[str, tuple] = {
    "C5P": POSITIONS, "C5O": POSITIONS, "C5D": POSITIONS,
    "C5A": ("RB", "WR", "TE"), "C5R": POSITIONS, "C5I": POSITIONS,
    "F0C5": POSITIONS,
}

C5_PAIRED = {f"{a}k": a for a in ("C5P", "C5O", "C5A", "C5R", "C5I")}


# --------------------------------------------------- CT1 component registry
#: screen component name -> (builder(panel, f, ts) -> Dict, value col, known col)
def _share_level(position: str):
    col = "cshare_w" if position == "RB" else "tshare_w"

    def block(panel, f, ts):
        v = f[col].to_numpy(dtype=float) if col in f.columns \
            else np.full(len(f), np.nan)
        return {"share_level_v": np.nan_to_num(v, nan=0.0),
                "share_level_known": np.isfinite(v).astype(float)}
    return block, "share_level_v", "share_level_known"


def _component(name: str, position: str) -> Tuple[Callable, str, Optional[str]]:
    if name == "share_level":
        return _share_level(position)
    fixed = {
        "snap_share": (_snap_share, "snapshare_w", "snap_known"),
        "redzone_share": (_redzone_usage, "rz_use_share_w", "rz_use_known"),
        "xfp_diff": (_xfp, "xfp_resid_pg_w", "xfp_known"),
        "tprr": (_routes_block, "tprr_w", "routes_known"),
        "wopr": (_wopr, "wopr_w", None),
        "implied_team_total": (_implied_total, "itt_w", "itt_known"),
        "injury_burden": (c3a._block_injury, "injury_burden_prior_w",
                          "injury_known"),
        "practice_severity": (c3a._block_practice,
                              "practice_severity_prior_w", "practice_known"),
        "neutral_pass_rate": (c3a._block_neutral,
                              "neutral_pass_rate_prior_w",
                              "neutral_pass_known"),
        "yoe_rate": (c3a._block_yoe, "yoe_rate_prior_w", "yoe_known"),
        "depth_end_rank": (c3a._block_depth, "depth_end_rank_prior1",
                           "depth_end_known"),
        "tshare_stability": (c4a._block_tshare, "tshare_stability_prior",
                             "tshare_stability_known"),
        "proe": (_block_proe, "proe_1", "proe_known"),
        "depth_first_share": (C5_BLOCKS["C5R"], "depth_first_v",
                              "ros_absent_known"),
        "depth_offroster": (C5_BLOCKS["C5R"], "offroster_v",
                            "ros_absent_known"),
        "depth_rostered_absent": (C5_BLOCKS["C5R"], "ros_absent_v",
                                  "ros_absent_known"),
        "inj_missed_share": (C5_BLOCKS["C5I"], "injm_v", "injm_known"),
        "inj_unexp_missed_share": (C5_BLOCKS["C5I"], "injum_v", "injm_known"),
    }
    if name not in fixed:
        raise KeyError(f"no CT1 component builder for {name!r}")
    return fixed[name]


#: component -> window family; a contrast takes the LATER of its two
_FAM_ORDER = ["T2A", "T2P", "T2I", "T2B", "T2C", "T2D"]
_COMP_FAMILY = {
    "share_level": "T2A", "tshare_stability": "T2A", "depth_end_rank": "T2A",
    "wopr": "T2P", "xfp_diff": "T2P", "redzone_share": "T2P", "proe": "T2P",
    "neutral_pass_rate": "T2P", "yoe_rate": "T2P",
    "depth_first_share": "T2P", "depth_offroster": "T2P",
    "depth_rostered_absent": "T2P", "inj_missed_share": "T2P",
    "inj_unexp_missed_share": "T2P",
    "injury_burden": "T2I", "practice_severity": "T2I",
    "snap_share": "T2B", "tprr": "T2C", "implied_team_total": "T2D",
}


def _pctrank(v: np.ndarray) -> np.ndarray:
    s = pd.Series(v)
    return s.rank(pct=True).to_numpy(dtype=float)


def _contrast_block(a: str, b: str, position: str) -> Callable:
    def block(panel, f, ts):
        fa, ca, ka = _component(a, position)
        fb, cb, kb = _component(b, position)
        da = fa(panel, f, ts)
        db = fb(panel, f, ts)
        va = np.asarray(da[ca], dtype=float)
        vb = np.asarray(db[cb], dtype=float)
        known = np.isfinite(va) & np.isfinite(vb)
        if ka and ka in da:
            known &= np.asarray(da[ka], dtype=float) > 0
        if kb and kb in db:
            known &= np.asarray(db[kb], dtype=float) > 0
        gap = _pctrank(np.where(known, va, np.nan)) \
            - _pctrank(np.where(known, vb, np.nan))
        gap = np.where(np.isfinite(gap), gap, 0.0)
        return {"ct_gap": gap, "ct_known": known.astype(float)}
    return block


def _ct_placebo_block(panel, f, ts):
    def draw(pid, j):
        h = hashlib.sha256(f"CT-placebo-{j}|{ts}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    a = np.array([draw(p, 0) for p in f["player_id"]], dtype=float)
    b = np.array([draw(p, 1) for p in f["player_id"]], dtype=float)
    return {"ct_gap": _pctrank(a) - _pctrank(b),
            "ct_known": np.ones(len(f))}


# ------------------------------------------------------- registry assembly
def _ct_registry() -> Dict[str, Tuple[str, str, tuple, str]]:
    """arm -> (component_a, component_b, positions, family), from the screen's
    own contrasts CSV — the arm set was fixed by the screen, not chosen here."""
    from pathlib import Path
    csv = pd.read_csv(Path(__file__).resolve().parents[1] / "results"
                      / "standalone_screen2_contrasts.csv")
    out: Dict[str, Tuple[str, str, tuple, str]] = {}
    for cname, grp in csv.groupby("factor"):
        core = cname.replace("contrast_", "", 1)
        a, b = core.split("_minus_")
        poss = tuple(sorted(grp["position"].unique()))
        fam = max((_COMP_FAMILY[a], _COMP_FAMILY[b]), key=_FAM_ORDER.index)
        arm = "CT_" + core
        out[arm] = (a, b, poss, fam)
    return out


CT_REGISTRY = _ct_registry()


# ------------------------------------------------------------------- hooks
def _c5_feature_fn(arm: str, position: str) -> Callable:
    base = C5_PAIRED.get(arm, arm)

    def fn(panel, universe, ts):
        f = build_features_v2(panel, universe, ts)
        block = C5_BLOCKS[base](panel, f, ts)
        if arm in C5_PAIRED:
            kc = C5_KNOWN[base]
            block = {kc: block[kc]}
        return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
    return fn


def _c5_cols(arm: str) -> List[str]:
    if arm in C5_PAIRED:
        return [C5_KNOWN[C5_PAIRED[arm]]]
    return C5_COLS[arm]


def _c5_model_kwargs(arm: str, position: str) -> Dict:
    return {"volume_cols": {spec: list(base) + _c5_cols(arm)
                            for spec, base in _BASE_SPECS[position].items()}}


def _ct_feature_fn(arm: str, position: str) -> Callable:
    if arm == "F0CT":
        block_fn = _ct_placebo_block
    else:
        a, b, _, _ = CT_REGISTRY[arm]
        block_fn = _contrast_block(a, b, position)

    def fn(panel, universe, ts):
        f = build_features_v2(panel, universe, ts)
        block = block_fn(panel, f, ts)
        return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
    return fn


def _ct_model_kwargs(arm: str, position: str) -> Dict:
    return {"volume_cols": {spec: list(base) + ["ct_gap", "ct_known"]
                            for spec, base in _BASE_SPECS[position].items()}}


ens.BATCH_HOOKS["C5"] = {"feature_fn": _c5_feature_fn,
                         "model_kwargs": _c5_model_kwargs}
ens.BATCH_HOOKS["CT1"] = {"feature_fn": _ct_feature_fn,
                          "model_kwargs": _ct_model_kwargs}

for _arm in C5_COLS:
    ens.ARMS070[("C5", _arm)] = Arm070(
        batch="C5", arm=_arm, family=C5_FAMILY[_arm],
        positions=C5_POSITIONS[_arm], endpoint="rho_points",
        block_cols=tuple(C5_COLS[_arm]), known_col=C5_KNOWN[_arm],
        null_kind="perm_block")
for _k, _t in C5_PAIRED.items():
    ens.ARMS070[("C5", _k)] = Arm070(
        batch="C5", arm=_k, family=C5_FAMILY[_t],
        positions=C5_POSITIONS[_t], endpoint="rho_points",
        block_cols=(C5_KNOWN[_t],), known_col=C5_KNOWN[_t],
        null_kind="perm_block")

for _arm, (_a, _b, _poss, _fam) in CT_REGISTRY.items():
    ens.ARMS070[("CT1", _arm)] = Arm070(
        batch="CT1", arm=_arm, family=_fam, positions=_poss,
        endpoint="rho_points", block_cols=("ct_gap", "ct_known"),
        known_col="ct_known", null_kind="perm_block")
ens.ARMS070[("CT1", "F0CT")] = Arm070(
    batch="CT1", arm="F0CT", family="T2A", positions=POSITIONS,
    endpoint="rho_points", block_cols=("ct_gap", "ct_known"),
    known_col=None, null_kind="perm_block")
del _arm, _k, _t

from ..components import pos_eval as E                       # noqa: E402
E._CARRY = E._CARRY + [c for c in
                       [x for cols in C5_COLS.values() for x in cols]
                       + ["ct_gap", "ct_known"] if c not in E._CARRY]

#: m_b: C5 treatment cells (23) + placebo (4) = 27; CT1 contrast cells (78)
#: + placebo (4) = 82.
M_B_C5 = sum(len(ens.ARMS070[("C5", a)].positions) for a in C5_COLS)
M_B_CT1 = sum(len(a.positions) for (b, n), a in ens.ARMS070.items()
              if b == "CT1")
