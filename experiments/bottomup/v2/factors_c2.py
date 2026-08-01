"""Batch C2 factor blocks — more factors, plus the RB high-carry breakpoint,
against ranking v2.

Registration: `docs/ranking/factor-campaign-manifest/batch-C2.md`, committed
before any of this ran (`ee87b53`).

GRADING IS SUSPENDED THIS BATCH. C1's registered inclusion rule handed a
BH-robust WIN to seeded noise (measured false-positive rate 9.6% of cells
against a nominal 2.5%). `run_c2.py` records CI-level verdicts and a
placebo comparison per cell but never emits INCLUDE/EXCLUDE — see
`docs/ranking/batch-C2-results.md`.

PART A REUSES BATCH-7 CODE VERBATIM WHERE IT EXISTS. `_yac`,
`_rec_points_share`, `_late_season` were built and gated for batch 7
(the old consensus-derived primary) and never run against v2. Per the
ledger's Section 0 rule, a row measured NULL under the old frame is
untested for v2 — reusing the same gated implementation (rather than a
second one) is the same discipline C1 applied to snap share / xFP / NGS
separation / routes: a second implementation of a feature is a second
chance to get its cutoff wrong.

TWO NEW BLOCKS. WOPR (A1) reads a column `player_weekly_stats` already
computes and stores — no new source. Implied team total (A5) is new: the
first read of `odds_snapshots` by any model in this project.

PART B NEEDS NO NEW SOURCE AT ALL. `carries_1` — the player's raw lag-1
carries — already exists in every v2 feature frame
(`pos_features.build_features`'s own per-lag accumulator). The hinge
terms are derived arithmetic on an already-gated column.

EVERY READ IS GATED. New sources here log a `("feature", cutoff)` entry on
the panel's access log exactly like batch 7's and C1's blocks, so the
WalkForward audit assertion `max_feature_cutoff < season` covers them with
no harness change. No block reads a season-N proxy; every C2 arm asserts
`n_preseason_proxy_reads == 0`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation, SeasonPanel,
)
from ..factors.factor_features7 import (
    _late_season, _rec_points_share, _weighted_lag, _yac,
)
from .factors_c1 import PLACEBO_SALT, _BASE_SPECS, _placebo  # reused verbatim
from .features_v2 import build_features_v2

__all__ = [
    "build_features_c2", "volume_cols_for", "FACTOR_BLOCKS", "FACTOR_COLS",
    "KNOWN_COL", "PAIRED_CONTROL", "COVERAGE_FLOOR",
]

#: same instrument as C1 (factors_c1.PLACEBO_SALT == ""), imported not
#: reimplemented, so F0/F0D here are the byte-identical generator run fresh
#: against this batch's own controls.
assert PLACEBO_SALT == ""


# ==================================================================== A1: WOPR
_WOPR_SQL = """
SELECT season, player_id,
       SUM(COALESCE(wopr, 0.0)) AS wopr_sum,
       SUM(CASE WHEN wopr IS NOT NULL THEN 1 ELSE 0 END) AS wopr_games
FROM player_weekly_stats
WHERE season < ? AND season_type = 'REG' AND position IN ('WR', 'TE')
GROUP BY season, player_id
"""


def load_wopr(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """(season, player_id) -> WOPR sum and game count, WR/TE only.

    `wopr` is dense on `player_weekly_stats` from 2009 (measured: 100% of
    WR/TE rows 2009-2025; near-empty 2003-2008 — see batch-C2 registration).
    No `*_known` control is registered for this factor because there is no
    join/presence gate to void against.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_WOPR_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(d) and (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("WOPR rows leaked past the SQL gate")
    return d


class _WOPRGate:
    def __init__(self, db_path: Path = DEFAULT_DB) -> None:
        self._d = load_wopr(db_path)

    def before(self, panel: SeasonPanel, cutoff: int) -> pd.DataFrame:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        out = self._d[self._d["season"] <= cutoff]
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation("WOPR cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out


_WOPR_GATE: Optional[_WOPRGate] = None


def wopr_gate(db_path: Path = DEFAULT_DB) -> _WOPRGate:
    global _WOPR_GATE
    if _WOPR_GATE is None:
        _WOPR_GATE = _WOPRGate(db_path)
    return _WOPR_GATE


def _wopr(panel: SeasonPanel, f: pd.DataFrame, target_season: int
         ) -> Dict[str, np.ndarray]:
    hist = wopr_gate().before(panel, target_season - 1)
    n = len(f)
    if not len(hist):
        return {"wopr_w": np.zeros(n)}
    num, den = _weighted_lag(f, hist, "wopr_sum", "wopr_games", target_season)
    known = den > 0
    val = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), 0.0)
    return {"wopr_w": val}


# ============================================== A5: implied team total (lagged)
_ODDS_TEAM_SQL = """
SELECT season, week, team, implied_team_total
FROM odds_snapshots
WHERE season < ? AND game_type = 'REG' AND implied_team_total IS NOT NULL
"""

_PLAYER_TEAM_SQL = """
SELECT season, week, team, player_id
FROM player_weekly_stats
WHERE season < ? AND season_type = 'REG'
"""


def load_implied_total(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """(season, player_id) -> sum of his own team's implied point total across
    the games he actually played, plus the count of such games.

    Joined by (season, week, team) rather than a season-level team average, so
    a mid-season trade is measured against the offence the player was
    actually in that week, not a blended figure. `odds_snapshots` starts
    2018 (T0-11/N12 were both `blocked` until this ingest landed) —
    coverage is reported per cell rather than assumed.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        odds = pd.read_sql_query(_ODDS_TEAM_SQL, conn, params=(HOLDOUT_SEASON,))
        pt = pd.read_sql_query(_PLAYER_TEAM_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(odds) and (odds["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("odds rows leaked past the SQL gate")
    if not len(odds) or not len(pt):
        return pd.DataFrame(columns=["season", "player_id", "itt_sum", "itt_games"])
    m = pt.merge(odds, on=["season", "week", "team"], how="inner")
    return m.groupby(["season", "player_id"], as_index=False).agg(
        itt_sum=("implied_team_total", "sum"),
        itt_games=("implied_team_total", "size"))


class _OddsGate:
    def __init__(self, db_path: Path = DEFAULT_DB) -> None:
        self._d = load_implied_total(db_path)

    def before(self, panel: SeasonPanel, cutoff: int) -> pd.DataFrame:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        out = self._d[self._d["season"] <= cutoff]
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation("implied-total cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out


_ODDS_GATE: Optional[_OddsGate] = None


def odds_gate(db_path: Path = DEFAULT_DB) -> _OddsGate:
    global _ODDS_GATE
    if _ODDS_GATE is None:
        _ODDS_GATE = _OddsGate(db_path)
    return _ODDS_GATE


def _implied_total(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                   ) -> Dict[str, np.ndarray]:
    hist = odds_gate().before(panel, target_season - 1)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"itt_w": z, "itt_known": z.copy()}
    num, den = _weighted_lag(f, hist, "itt_sum", "itt_games", target_season)
    known = den > 0
    val = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), 0.0)
    return {"itt_w": val, "itt_known": known.astype(float)}


# ============================================ B1: RB high-carry-season hinge
#: fixed a priori, the founder's own three candidate values (2026-07-31), used
#: as SPLINE KNOTS, never searched. See batch-C2.md Part B for why this is one
#: non-linearity test and not a three-way cutoff sweep.
CARRY_KNOTS = (350.0, 375.0, 400.0)


def _carry_hinge(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                 ) -> Dict[str, np.ndarray]:
    c1 = (f["carries_1"].to_numpy(dtype=float) if "carries_1" in f.columns
          else np.zeros(len(f)))
    out = {}
    for k in CARRY_KNOTS:
        out[f"carry_hinge_{int(k)}"] = np.clip(c1 - k, 0.0, None)
    return out


# --------------------------------------------------------------- the builder
_BLOCKS = {
    "wopr": _wopr,               # A1
    "yac": _yac,                 # A2 (batch 7, reused)
    "recshare": _rec_points_share,  # A3 (batch 7, reused)
    "late": _late_season,        # A4 (batch 7, reused)
    "odds": _implied_total,      # A5
    "hinge": _carry_hinge,       # B1
    "placebo": _placebo,         # F0 / F0D (C1's instrument, reused)
}

#: blocks whose pooled prior / group mean must be computed on the modelled
#: position's own rows — same convention as batch 7's `_POS_AWARE`.
_POS_AWARE = {"yac", "late"}


def build_features_c2(panel, universe: pd.DataFrame, target_season: int,
                      blocks: Tuple[str, ...] = (),
                      position: Optional[str] = None) -> pd.DataFrame:
    """v2's feature set, plus exactly the declared blocks and nothing else.

    With `blocks=()` this IS `build_features_v2` — bit-for-bit the same
    control C1 graded against, so a NULL can never be blamed on a column the
    arm did not declare.
    """
    f = build_features_v2(panel, universe, target_season)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    for b in blocks:
        if b not in _BLOCKS:
            raise KeyError(f"no C2 block {b!r}")
        kw = {"position": position} if b in _POS_AWARE else {}
        block.update(_BLOCKS[b](panel, f, target_season, **kw))
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)


# ------------------------------------------------------------ the arm registry
FACTOR_COLS: Dict[str, List[str]] = {
    "A1": ["wopr_w"],
    "A2": ["yac_per_rec_w", "yac_known"],
    "A3": ["recpts_share_w", "recpts_ge40", "recpts_known"],
    "A4": ["late_ratio_w", "late_lift_grp", "late_known"],
    "A5": ["itt_w", "itt_known"],
    "B1": [f"carry_hinge_{int(k)}" for k in CARRY_KNOTS],
    "F0": ["placebo_noise"],
    "F0D": ["placebo_noise"],
}

FACTOR_BLOCKS: Dict[str, Tuple[str, ...]] = {
    "A1": ("wopr",), "A2": ("yac",), "A3": ("recshare",), "A4": ("late",),
    "A5": ("odds",), "B1": ("hinge",), "F0": ("placebo",), "F0D": ("placebo",),
}

#: the `*_known` column whose mean is the coverage measurement, per factor.
#: A1 (dense column, no join gate) and B1 (rare-event indicator, not a
#: presence gate) register no control. F0/F0D are the calibration instrument.
KNOWN_COL: Dict[str, Optional[str]] = {
    "A1": None, "A2": "yac_known", "A3": "recpts_known", "A4": "late_known",
    "A5": "itt_known", "B1": None, "F0": None, "F0D": None,
}

#: paired coverage-indicator control arms, C1 Amendment 1's VOID-rule
#: discipline carried forward. Derived from the treatment's own column list.
PAIRED_CONTROL = {f"{f}k": f for f in ("A2", "A3", "A4", "A5")}

for _k, _f in PAIRED_CONTROL.items():
    FACTOR_COLS[_k] = [KNOWN_COL[_f]]
    FACTOR_BLOCKS[_k] = FACTOR_BLOCKS[_f]
    KNOWN_COL[_k] = KNOWN_COL[_f]
del _k, _f


def volume_cols_for(factor: str, position: str) -> Dict[str, List[str]]:
    """`{spec name: base features + the factor's columns}` for `volume_cols`,
    identical convention to `factors_c1.volume_cols_for` (same `_BASE_SPECS`,
    imported not retyped)."""
    add = FACTOR_COLS[factor]
    if not add:
        return {}
    return {spec: list(base) + list(add)
            for spec, base in _BASE_SPECS[position].items()}


#: coverage floor, unchanged from C1: an arm is NO DATA in a cell where fewer
#: than 80% of graded rows carry a real value for the factor's `*_known` flag.
#: Not applied to A1 (no known col) or B1 (rare-event indicator by design;
#: its sparsity is reported directly rather than gated).
COVERAGE_FLOOR = 0.80
