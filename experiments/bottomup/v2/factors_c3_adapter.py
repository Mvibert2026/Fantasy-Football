"""Batch C3 — reconciliation of backend's factor definitions to the real
v2 arm interface, plus the tier-2 arm registry.

WHY THIS FILE EXISTS. `factors_c3.py` was written by `backend` in a worktree
branched before `factors_c1.py`/`factors_c2.py` existed, against a
reconstructed interface (its own NEXT STEP section documents this honestly):
`attach_*` builders taking a `(player_id, season)` frame, batch-local
`BatchC3Sources` gates. The real interface is the C1/C2 block convention —
`(panel, f, target_season) -> Dict[str, np.ndarray]`, columns appended to the
veteran volume specs via `volume_cols`, mandatory `*_known` companions, every
source read landing on the panel's access log. This module adapts WITHOUT
rewriting backend's loaders or aggregation logic: each block calls the C3
Sources gate (which appends to `panel.access_log` under the `feature` tag) at
cutoff `target_season - 1`, feeds the cut frame to backend's own builder, and
aligns the result to the feature frame's row order.

Registration: `docs/ranking/factor-campaign-manifest/batch-C3.md` (committed
before any arm runs; the sweep reaches C3 only after VERIFY, D1A1, C1, C2).

WINDOWS — the late-source discipline, per factor:
  C3C injury burden      injuries 2010+   -> T2I (ff 2013, targets 2015-2024)
  C3D practice severity  injuries 2010+   -> T2I
  C3E depth-end rank     depth 2001+      -> T2A (base window)
  C3F combine composite  combine 2000+    -> T2A
  C3G neutral pass rate  pbp 2009+        -> T2P (ff 2012, targets 2014-2024)
  C3H yards-over-exp     ff_opportunity   -> T2P
  F0C3 placebo                            -> T2A
C and D could nominally run at the deep window with `*_known = 0` before 2010,
but nine known-zero training years at QB/RB is exactly the coverage-flag
time-dummy geometry batch 7's D2 measured; a matched control at a clean window
is cheaper than arguing with that artifact afterwards.

COMBINE AND ROOKIES. The combine column enters the VETERAN volume specs only
(the arm mechanism overrides veteran specs; the rookie path keeps ROOKIE_COLS
untouched), so the §2a rookie ruling's no-shared-slope requirement is satisfied
structurally, and cutting the source at `target_season - 1` costs nothing —
every veteran's draft class is <= target - 1 by definition. The rookie-side
combine model is a separate registration (`season-span-M4.md` §4), not this.

NEUTRAL PASS RATE'S `team`. Backend's builder requires a caller-resolved team
column. Resolved here as the player's club in his MOST RECENT season <=
target - 1 from the panel's own gated history — the September-of-N vantage
knows his N-1 club; an offseason move is season-N information this factor
deliberately does not read.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from . import ensemble070 as ens
from . import factors_c3 as c3
from .ensemble070 import Arm070, POSITIONS
from .factors_c1 import _BASE_SPECS
from .features_v2 import build_features_v2

# ------------------------------------------------------------- new families
ens.TIER2.setdefault("T2I", {p: (2013, 2015) for p in POSITIONS})
ens.TIER2.setdefault("T2P", {p: (2012, 2014) for p in POSITIONS})

# ---------------------------------------------------------------- registry
FACTOR_COLS: Dict[str, List[str]] = {
    "C3C": ["injury_burden_prior_w", "injury_known"],
    "C3D": ["practice_severity_prior_w", "practice_known"],
    "C3E": ["depth_end_rank_prior1", "depth_end_known"],
    "C3F": ["combine_z", "combine_known"],
    "C3G": ["neutral_pass_rate_prior_w", "neutral_pass_known"],
    "C3H": ["yoe_rate_prior_w", "yoe_known"],
    "F0C3": ["placebo_noise_c3"],
}

KNOWN_COL: Dict[str, Optional[str]] = {
    "C3C": "injury_known", "C3D": "practice_known", "C3E": "depth_end_known",
    "C3F": "combine_known", "C3G": "neutral_pass_known", "C3H": "yoe_known",
    "F0C3": None,
}

FAMILY: Dict[str, str] = {
    "C3C": "T2I", "C3D": "T2I", "C3E": "T2A", "C3F": "T2A",
    "C3G": "T2P", "C3H": "T2P", "F0C3": "T2A",
}

ARM_POSITIONS: Dict[str, tuple] = {
    "C3C": POSITIONS, "C3D": POSITIONS,
    "C3E": ("RB", "WR", "TE"),       # QB1 designation ~ redundant with volume
    "C3F": ("RB", "WR", "TE"),       # QB athleticism channel closed (6 configs)
    "C3G": POSITIONS,
    "C3H": ("RB", "WR", "TE"),
    "F0C3": POSITIONS,
}

#: paired coverage-indicator controls, C1 Amendment 1 discipline
PAIRED_CONTROL = {f"{f}k": f for f in
                  ("C3C", "C3D", "C3E", "C3F", "C3G", "C3H")}


# ------------------------------------------------------------------ blocks
def _align(f: pd.DataFrame, out: pd.DataFrame, cols: List[str]
           ) -> Dict[str, np.ndarray]:
    m = f[["player_id"]].merge(out.drop_duplicates("player_id"),
                               on="player_id", how="left")
    return {c: m[c].to_numpy(dtype=float) for c in cols}


def _block_injury(panel, f, ts):
    inj = c3.sources().injuries_before(ts - 1, panel)
    burden = c3.build_injury_burden(inj)
    out = c3.attach_injury_burden(f[["player_id", "season"]], burden)
    return _align(f, out, FACTOR_COLS["C3C"])


def _block_practice(panel, f, ts):
    inj = c3.sources().injuries_before(ts - 1, panel)
    sev = c3.build_practice_severity(inj)
    out = c3.attach_practice_severity(f[["player_id", "season"]], sev)
    return _align(f, out, FACTOR_COLS["C3D"])


def _block_depth(panel, f, ts):
    de = c3.sources().depth_end_before(ts - 1, panel)
    out = c3.attach_depth_end_rank(f[["player_id", "season"]], de)
    return _align(f, out, FACTOR_COLS["C3E"])


def _block_combine(panel, f, ts):
    cb = c3.sources().combine_before(ts - 1, panel)
    out = c3.attach_combine(f[["player_id", "season"]], cb)
    return _align(f, out, FACTOR_COLS["C3F"])


def _block_neutral(panel, f, ts):
    hist = panel.before(ts - 1)
    team = hist.sort_values("season").groupby("player_id")["team"].last()
    req = f[["player_id", "season"]].copy()
    req["team"] = req["player_id"].map(team)
    npr = c3.sources().pass_neutral_before(ts - 1, panel)
    out = c3.attach_neutral_pass_rate(req, npr)
    return _align(f, out, FACTOR_COLS["C3G"])


def _block_yoe(panel, f, ts):
    y = c3.sources().yoe_before(ts - 1, panel)
    out = c3.attach_yoe(f[["player_id", "season"]], y)
    return _align(f, out, FACTOR_COLS["C3H"])


def _block_placebo(panel, f, ts):
    """C3's own registered placebo — C1's construction, its own salt."""
    def draw(pid: str) -> float:
        h = hashlib.sha256(f"C3-placebo|{ts}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    return {"placebo_noise_c3": np.array([draw(p) for p in f["player_id"]],
                                         dtype=float)}


_BLOCKS: Dict[str, Callable] = {
    "C3C": _block_injury, "C3D": _block_practice, "C3E": _block_depth,
    "C3F": _block_combine, "C3G": _block_neutral, "C3H": _block_yoe,
    "F0C3": _block_placebo,
}


def build_features_c3(panel, universe, target_season, arm: str) -> pd.DataFrame:
    """v2's feature set plus exactly the arm's block — with no block this IS
    `build_features_v2`, the same object every control graded."""
    f = build_features_v2(panel, universe, target_season)
    base = PAIRED_CONTROL.get(arm, arm)
    block = _BLOCKS[base](panel, f, target_season)
    if arm in PAIRED_CONTROL:                 # k-arm: the known flag alone
        block = {KNOWN_COL[base]: block[KNOWN_COL[base]]}
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)


# ------------------------------------------------------------------- hooks
def _feature_fn(arm: str, position: str) -> Callable:
    return lambda panel, universe, ts: build_features_c3(
        panel, universe, ts, arm)


def _cols_of(arm: str) -> List[str]:
    if arm in PAIRED_CONTROL:
        return [KNOWN_COL[PAIRED_CONTROL[arm]]]
    return FACTOR_COLS[arm]


def _model_kwargs(arm: str, position: str) -> Dict:
    return {"volume_cols": {spec: list(base) + _cols_of(arm)
                            for spec, base in _BASE_SPECS[position].items()}}


ens.BATCH_HOOKS["C3"] = {"feature_fn": _feature_fn,
                         "model_kwargs": _model_kwargs}

for _arm, _cols in FACTOR_COLS.items():
    ens.ARMS070[("C3", _arm)] = Arm070(
        batch="C3", arm=_arm, family=FAMILY[_arm],
        positions=ARM_POSITIONS[_arm], endpoint="rho_points",
        block_cols=tuple(_cols), known_col=KNOWN_COL[_arm],
        null_kind="perm_block")
for _k, _t in PAIRED_CONTROL.items():
    ens.ARMS070[("C3", _k)] = Arm070(
        batch="C3", arm=_k, family=FAMILY[_t],
        positions=ARM_POSITIONS[_t], endpoint="rho_points",
        block_cols=(KNOWN_COL[_t],), known_col=KNOWN_COL[_t],
        null_kind="perm_block")
del _arm, _cols, _k, _t

# coverage measurement on the graded population needs the columns carried
from ..components import pos_eval as E                       # noqa: E402
E._CARRY = E._CARRY + [c for cols in FACTOR_COLS.values() for c in cols
                       if c not in E._CARRY]

#: registered m_b for the campaign denominator (treatment cells + placebo
#: cells; k-controls excluded, the C1 convention): C 4 + D 4 + E 3 + F 3 +
#: G 4 + H 3 + F0C3 4 = 25.
M_B = 25
