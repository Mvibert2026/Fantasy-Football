"""Batch AB1 — incumbent ablations. No grandfather clause (founder,
FR-2026-08-04-v3-build-strategy): every channel already inside the veteran
volume specs faces the instrument, as a REMOVAL arm.

WHAT IS ACTUALLY IN THE MODEL, measured from the shipped spec objects rather
than asserted (the spec dicts are instantiated and read at import): the veteran
volume specs carry exactly these auxiliary channels — volume level (the spec's
own lag), share (tshare_w/cshare_w), games share (gshare_w), evidence, age
(age+age2), prior points per game (ppg_w), experience. **Four "incumbents"
named in the dispatch are NOT in the running model and therefore have no
ablation**: depth chart/role (AVAIL_E only, unused; tested additively as C3E),
injury designations (AVAIL_B only, unused; tested additively as C3C/C3D),
air yards/aDOT (accumulated by the feature builder, consumed by no spec;
tested additively as C1 F4 and C2 A1/WOPR), and draft capital (rookie path
only — the graded endpoint is board VETERANS, so a rookie-path ablation cannot
move it; rookie-side testing belongs to the rookie registration,
season-span-M4 §4). The final report states this rather than inventing arms.

ARM FORM (ensemble070 `perm_ablate`): observed run = incumbent volume specs
with the channel's columns removed from EVERY spec of the position (built from
the instantiated spec objects, so no hand-typed list can drift); null draw k =
FULL incumbent specs with the channel's rows jointly permuted within season.
Both difference against the unmodified control. Under H0 the removal differs
from control only by the variance cost of a noise block — which is what the
permuted block is. Availability specs are NOT touched: the availability
channel has its own registered campaign (B1, D1, D1-A1) and mixing the two in
one arm would blur attribution.

VERDICT TRANSLATION (report layer, the instrument itself is untouched):
HARM on removal = the incumbent carries ordering signal — VALIDATED;
WIN on removal = the incumbent costs ordering — REMOVAL CANDIDATE;
NULL = not evidenced at this power on this endpoint (parsimony call for
strategist, not an automatic removal).

Registration: `docs/ranking/factor-campaign-manifest/batch-AB1.md`.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

from ..components.pos_model import MODELS
from . import ensemble070 as ens
from .ensemble070 import Arm070, POSITIONS
from .features_v2 import build_features_v2

#: channel -> columns removed wherever they appear in that position's specs
DROPS: Dict[str, List[str]] = {
    "ABAGE": ["age", "age2"],
    "ABSHARE": ["tshare_w", "cshare_w"],
    "ABGSH": ["gshare_w"],
    "ABPPG": ["ppg_w"],
    "ABEVID": ["evidence"],
    "ABEXP": ["experience"],
}

AB_PLACEBO_COL = "placebo_noise_ab"

#: the shipped spec lists, read from instantiated models — never hand-typed
_SPECS: Dict[str, Dict[str, List[str]]] = {}
for _pos in POSITIONS:
    _m = MODELS[_pos](position=_pos, avail_arm="A")
    _SPECS[_pos] = {name: list(cols)
                    for name, (cols, _yn, _yd) in _m.VOLUME_SPECS.items()}
del _pos, _m


def _positions_for(drop: List[str]) -> tuple:
    return tuple(p for p in POSITIONS
                 if any(c in cols for cols in _SPECS[p].values()
                        for c in drop))


def _ablated_specs(position: str, drop: List[str]) -> Dict[str, List[str]]:
    out = {}
    for name, cols in _SPECS[position].items():
        kept = [c for c in cols if c not in drop]
        if kept != cols:
            out[name] = kept
    return out


def _feature_fn(arm: str, position: str) -> Callable:
    if arm == "F0AB":
        def fn(panel, universe, ts):
            f = build_features_v2(panel, universe, ts)
            f = f.copy()

            def draw(pid: str) -> float:
                h = hashlib.sha256(f"AB-placebo|{ts}|{pid}".encode()).digest()
                u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
                u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
                return float(np.sqrt(-2.0 * np.log(u1))
                             * np.cos(2.0 * np.pi * u2))
            f[AB_PLACEBO_COL] = np.array(
                [draw(p) for p in f["player_id"]], dtype=float)
            return f
        return fn
    # ablation arms: the base frame already carries every column involved
    return lambda panel, universe, ts: build_features_v2(panel, universe, ts)


def _model_kwargs(arm: str, position: str) -> Dict:
    if arm == "F0AB":
        return {"volume_cols": {name: cols + [AB_PLACEBO_COL]
                                for name, cols in _SPECS[position].items()}}
    # perm_ablate arms: called only for the OBSERVED run (k=0) — the ablated
    # specs. Null draws use the incumbent specs (ensemble070 handles it).
    return {"volume_cols": _ablated_specs(position, DROPS[arm])}


ens.BATCH_HOOKS["AB1"] = {"feature_fn": _feature_fn,
                          "model_kwargs": _model_kwargs}

for _arm, _drop in DROPS.items():
    ens.ARMS070[("AB1", _arm)] = Arm070(
        batch="AB1", arm=_arm, family="T2A",
        positions=_positions_for(_drop), endpoint="rho_points",
        block_cols=tuple(_drop), known_col=None, null_kind="perm_ablate")
ens.ARMS070[("AB1", "F0AB")] = Arm070(
    batch="AB1", arm="F0AB", family="T2A", positions=POSITIONS,
    endpoint="rho_points", block_cols=(AB_PLACEBO_COL,), known_col=None,
    null_kind="perm_block")
del _arm, _drop

#: registered m_b: every treatment cell + the placebo cells
M_B = sum(len(a.positions) for (b, n), a in ens.ARMS070.items()
          if b == "AB1")
