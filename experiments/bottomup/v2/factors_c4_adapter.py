"""Batch C4 — adapter to the real arm interface + tier-2 registry.

`factors_c4.py` (backend, 2026-08-04) was written against the merged, current
interface in C3's Sources-pack shape; per its own §0 the arm wiring is ranker's
step, done here. No backend loader is rewritten. Registration:
`docs/ranking/factor-campaign-manifest/batch-C4.md`.

Windows (late-source discipline; §4.8 keys enforced by raise as everywhere):

  C4I  target-share stability   src 2009  -> T2A (WR/TE base window)
  C4J  team pace                src 2009  -> T2P (ff 2012, targets 2014-2024)
  C4K  contract-year status     src 2011  -> T2P; thin early coverage reported
                                             per cell, the 0.80 floor decides
  C4L  coaching disruption      src 1999  -> T2A
  C4M  O-line YBC/carry         src 2018  -> T2D (ff 2018, targets 2021-2024,
                                             S_pos = 4 — LABELLED, own control)
  C4N  two-WR personnel rate    src 2016  -> T2C (ff 2017, targets 2019-2024,
                                             S_pos = 6)
  F0C4 placebo (salt C4)                  -> T2A

Team-of-record for J/L/M/N resolved exactly as C3G: the player's club in his
most recent season <= target-1 from the panel's own gated history. Contract
year's `year_signed <= target_season` read is the one same-calendar-year read
in the batch — a March-August signing predates Week 1; backend's file flags it
and the 62% contract-year smoke rate stays flagged in the registration.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from . import ensemble070 as ens
from . import factors_c4 as c4
from .ensemble070 import Arm070, POSITIONS
from .factors_c1 import _BASE_SPECS
from .features_v2 import build_features_v2

FACTOR_COLS: Dict[str, List[str]] = {
    "C4I": ["tshare_stability_prior", "tshare_stability_known"],
    "C4J": ["pace_prior_w", "pace_known"],
    "C4K": ["is_contract_year", "contract_years_left", "contract_known"],
    "C4L": ["hc_disruption_prior1", "hc_disruption_known"],
    "C4M": ["ol_ybc_prior_w", "ol_ybc_known"],
    "C4N": ["two_wr_rate_prior_w", "two_wr_known"],
    "F0C4": ["placebo_noise_c4"],
}

KNOWN_COL: Dict[str, Optional[str]] = {
    "C4I": "tshare_stability_known", "C4J": "pace_known",
    "C4K": "contract_known", "C4L": "hc_disruption_known",
    "C4M": "ol_ybc_known", "C4N": "two_wr_known", "F0C4": None,
}

FAMILY: Dict[str, str] = {
    "C4I": "T2A", "C4J": "T2P", "C4K": "T2P", "C4L": "T2A",
    "C4M": "T2D", "C4N": "T2C", "F0C4": "T2A",
}

ARM_POSITIONS: Dict[str, tuple] = {
    "C4I": ("WR", "TE"),             # backend's own scope: RB is a different process
    "C4J": POSITIONS,
    "C4K": POSITIONS,
    "C4L": POSITIONS,
    "C4M": ("RB",),                  # ground-game blocking only
    "C4N": ("RB", "WR", "TE"),       # personnel identity moves the skill spots
    "F0C4": POSITIONS,
}

PAIRED_CONTROL = {f"{f}k": f for f in
                  ("C4I", "C4J", "C4K", "C4L", "C4M", "C4N")}


def _align(f: pd.DataFrame, out: pd.DataFrame, cols: List[str]
           ) -> Dict[str, np.ndarray]:
    m = f[["player_id"]].merge(out.drop_duplicates("player_id"),
                               on="player_id", how="left")
    return {c: m[c].to_numpy(dtype=float) for c in cols}


def _with_team(panel, f, ts) -> pd.DataFrame:
    hist = panel.before(ts - 1)
    team = hist.sort_values("season").groupby("player_id")["team"].last()
    req = f[["player_id", "season"]].copy()
    req["team"] = req["player_id"].map(team)
    return req


def _block_tshare(panel, f, ts):
    t = c4.sources().tshare_before(ts - 1, panel)
    out = c4.build_tshare_stability(f[["player_id", "season"]], t)
    return _align(f, out, FACTOR_COLS["C4I"])


def _block_pace(panel, f, ts):
    p = c4.sources().pace_before(ts - 1, panel)
    out = c4.attach_pace(_with_team(panel, f, ts), p)
    return _align(f, out, FACTOR_COLS["C4J"])


def _block_contract(panel, f, ts):
    # year_signed <= target is legitimate (pre-Week-1 calendar event); the
    # gate still bounds the SOURCE at the holdout. Cut at ts, not ts-1, is
    # deliberate and matches backend's stated convention for this factor only.
    ct = c4.sources().contracts_before(min(ts, ens.HOLDOUT_SEASON - 1), panel)
    out = c4.attach_contract_year(f[["player_id", "season"]], ct)
    return _align(f, out, FACTOR_COLS["C4K"])


def _block_coach(panel, f, ts):
    cc = c4.sources().coach_change_before(ts - 1, panel)
    out = c4.attach_coaching_disruption(_with_team(panel, f, ts), cc)
    return _align(f, out, FACTOR_COLS["C4L"])


def _block_ol(panel, f, ts):
    o = c4.sources().ol_ybc_before(ts - 1, panel)
    out = c4.attach_ol_ybc(_with_team(panel, f, ts), o)
    return _align(f, out, FACTOR_COLS["C4M"])


def _block_twowr(panel, f, ts):
    w = c4.sources().two_wr_before(ts - 1, panel)
    out = c4.attach_two_wr_rate(_with_team(panel, f, ts), w)
    return _align(f, out, FACTOR_COLS["C4N"])


def _block_placebo(panel, f, ts):
    def draw(pid: str) -> float:
        h = hashlib.sha256(f"C4-placebo|{ts}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    return {"placebo_noise_c4": np.array([draw(p) for p in f["player_id"]],
                                         dtype=float)}


_BLOCKS: Dict[str, Callable] = {
    "C4I": _block_tshare, "C4J": _block_pace, "C4K": _block_contract,
    "C4L": _block_coach, "C4M": _block_ol, "C4N": _block_twowr,
    "F0C4": _block_placebo,
}


def build_features_c4(panel, universe, target_season, arm: str) -> pd.DataFrame:
    f = build_features_v2(panel, universe, target_season)
    base = PAIRED_CONTROL.get(arm, arm)
    block = _BLOCKS[base](panel, f, target_season)
    if arm in PAIRED_CONTROL:
        block = {KNOWN_COL[base]: block[KNOWN_COL[base]]}
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)


def _feature_fn(arm: str, position: str) -> Callable:
    return lambda panel, universe, ts: build_features_c4(
        panel, universe, ts, arm)


def _cols_of(arm: str) -> List[str]:
    if arm in PAIRED_CONTROL:
        return [KNOWN_COL[PAIRED_CONTROL[arm]]]
    return FACTOR_COLS[arm]


def _model_kwargs(arm: str, position: str) -> Dict:
    return {"volume_cols": {spec: list(base) + _cols_of(arm)
                            for spec, base in _BASE_SPECS[position].items()}}


ens.BATCH_HOOKS["C4"] = {"feature_fn": _feature_fn,
                         "model_kwargs": _model_kwargs}

for _arm, _cols in FACTOR_COLS.items():
    ens.ARMS070[("C4", _arm)] = Arm070(
        batch="C4", arm=_arm, family=FAMILY[_arm],
        positions=ARM_POSITIONS[_arm], endpoint="rho_points",
        block_cols=tuple(_cols), known_col=KNOWN_COL[_arm],
        null_kind="perm_block")
for _k, _t in PAIRED_CONTROL.items():
    ens.ARMS070[("C4", _k)] = Arm070(
        batch="C4", arm=_k, family=FAMILY[_t],
        positions=ARM_POSITIONS[_t], endpoint="rho_points",
        block_cols=(KNOWN_COL[_t],), known_col=KNOWN_COL[_t],
        null_kind="perm_block")
del _arm, _cols, _k, _t

from ..components import pos_eval as E                       # noqa: E402
E._CARRY = E._CARRY + [c for cols in FACTOR_COLS.values() for c in cols
                       if c not in E._CARRY]

#: treatment cells 18 + placebo 4 (k-controls excluded, the C1 convention)
M_B = 22
