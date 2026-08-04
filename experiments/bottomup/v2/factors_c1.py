"""Batch C1 factor blocks — the inclusion test against ranking v2.

Registration: `docs/ranking/factor-campaign-manifest/batch-C1.md`, committed
before any of this ran.

WHAT AN ARM IS, PRECISELY. v2's ordering path is `proj_points` computed from
stat lines; the player-level opinion lives in the **volume** models
(`pos_model.BaseComponentModel.VOLUME_SPECS`), which are OLS on a declared
feature list. An arm therefore appends exactly one factor's column block to that
list at the positions the factor applies to, via the existing `volume_cols`
hook, and changes nothing else — availability arm, rate specs, bonus curves,
scoring, ordering and evaluation population are all inherited.

MOST BLOCKS ARE NOT NEW CODE. Snap share, xFP, NGS separation and route
participation already exist as gated, audited blocks written for batches 3/5/6/7
and are imported rather than reimplemented — a second implementation of a
feature is a second chance to get its cutoff wrong. Two blocks are new:
red-zone usage share (batch 7 built red-zone *snaps* from `participation`, 2016+;
this is red-zone *usage* from `pbp`, 2009+, so it grades on the full window) and
the placebo.

EVERY READ IS GATED. Each imported block logs a `("feature", target_season - 1)`
entry on the panel's own access log, so the WalkForward audit assertion
`max_feature_cutoff < season` covers them with no change to the harness. No
block here reads a season-N proxy; every C1 arm asserts
`n_preseason_proxy_reads == 0`.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..components import pos_features
from ..components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation, SeasonPanel,
    season_length,
)
from ..components.pos_features import LAG_WEIGHTS, N_LAGS
from ..components.pos_model import (
    _QB_ATT_VOLUME, _QB_RUSH_VOLUME, _RB_CARRY_VOLUME, _RB_TARGET_VOLUME,
    _RECEIVER_VOLUME,
)
from ..factors.factor_features3 import _separation
from ..factors.factor_features5 import _routes_block
from ..factors.factor_features6 import _xfp
from ..factors.factor_features7 import _snap_share, _weighted_lag
from .features_v2 import build_features_v2

# ------------------------------------------------------------------ F6 weights
#: Registered a priori in batch-C1, NOT tuned and NOT selected from a sweep.
#: Roughly halves the half-life of the incumbent (0.55, 0.30, 0.15).
STEEP_LAG_WEIGHTS = (0.70, 0.22, 0.08)


@contextmanager
def steep_recency():
    """Swap `pos_features.LAG_WEIGHTS` for the duration of a fit.

    A module-global patch rather than a parameter because that constant is read
    at call time by `build_features` in three places — the per-season weight
    matrix, the per-game weighted averages, and every efficiency (num, den)
    pair. Changing it in one place is what makes F6 one change rather than
    three, which is the arm discipline this batch is registered under.
    """
    old = pos_features.LAG_WEIGHTS
    pos_features.LAG_WEIGHTS = STEEP_LAG_WEIGHTS
    try:
        yield
    finally:
        pos_features.LAG_WEIGHTS = old


# ------------------------------------------------------- F2: red-zone usage
_RZ_SQL = """
SELECT season, week, posteam AS team,
       receiver_player_id AS rec_id, rusher_player_id AS rush_id,
       pass_attempt, rush_attempt
FROM pbp
WHERE season < ? AND yardline_100 <= 20 AND posteam IS NOT NULL
  AND (pass_attempt = 1 OR rush_attempt = 1)
"""


def load_redzone_usage(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (season, player_id): inside-20 targets + carries, and the inside-20
    plays his club ran that season.

    THE FACTOR IS A SHARE, not a count, so the denominator matters. It is the
    club's own inside-20 pass attempts plus rush attempts, joined on the club
    the player actually accumulated his red-zone work for — so a player who
    changed teams is measured against the offence he was in, not a league mean.

    REG-SEASON FILTER, applied here rather than assumed: `pbp` carries no
    `season_type` column and does contain playoff weeks, so weeks are bounded by
    `season_length(season) + 1` — the same convention batch 6 applies to
    `ff_opportunity` for the same reason. Without it a January run would inflate
    a contender's backs against a non-contender's.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_RZ_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "rz_use", "team_rz_use"])
    if (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("red-zone rows leaked past the SQL gate")
    reg = d["season"].map(lambda s: season_length(int(s)) + 1)
    d = d[d["week"] <= reg]

    team = d.groupby(["season", "team"], as_index=False).size() \
        .rename(columns={"size": "team_rz_use"})

    tg = d.loc[d["pass_attempt"] == 1, ["season", "team", "rec_id"]] \
        .rename(columns={"rec_id": "player_id"})
    ca = d.loc[d["rush_attempt"] == 1, ["season", "team", "rush_id"]] \
        .rename(columns={"rush_id": "player_id"})
    use = pd.concat([tg, ca], ignore_index=True)
    use = use[use["player_id"].notna() & (use["player_id"].astype(str) != "")]
    out = use.groupby(["season", "team", "player_id"], as_index=False).size() \
        .rename(columns={"size": "rz_use"})
    out = out.merge(team, on=["season", "team"], how="left")
    # a player who split a season across clubs contributes both club rows; sum
    # numerator and denominator so his share is weighted by where he actually was
    return out.groupby(["season", "player_id"], as_index=False).agg(
        rz_use=("rz_use", "sum"), team_rz_use=("team_rz_use", "sum"))


class _RZGate:
    """Same contract as `SeasonPanel.before()` for the one C1-owned source.

    Loaded once per process; every read is bounded by the sealed holdout,
    asserted against its own cutoff on the way out, and logged onto the panel's
    access log as a `feature` read — never a `proxy`, because `pbp` for seasons
    <= N-1 contains nothing dated in season N.
    """

    def __init__(self, db_path: Path = DEFAULT_DB) -> None:
        self._rz = load_redzone_usage(db_path)

    def before(self, panel: SeasonPanel, cutoff: int) -> pd.DataFrame:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")
        out = self._rz[self._rz["season"] <= cutoff]
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation("red-zone cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out


_RZ_GATE: Optional[_RZGate] = None


def rz_gate(db_path: Path = DEFAULT_DB) -> _RZGate:
    global _RZ_GATE
    if _RZ_GATE is None:
        _RZ_GATE = _RZGate(db_path)
    return _RZ_GATE


def _redzone_usage(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                   ) -> Dict[str, np.ndarray]:
    hist = rz_gate().before(panel, target_season - 1)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"rz_use_share_w": z, "rz_use_known": z.copy()}
    num, den = _weighted_lag(f, hist, "rz_use", "team_rz_use", target_season)
    known = den > 0
    share = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), 0.0)
    return {"rz_use_share_w": share, "rz_use_known": known.astype(float)}


# ------------------------------------------------------------- F0: the placebo
#: Empty string reproduces the registered F0 arm byte-for-byte. The REPLICATION
#: diagnostic varies it to draw independent placebos from the same generator,
#: which is how "did this one draw get lucky" is separated from "does adding any
#: column help here". Never set outside that diagnostic.
PLACEBO_SALT = ""


def _placebo(panel: SeasonPanel, f: pd.DataFrame, target_season: int
             ) -> Dict[str, np.ndarray]:
    """A seeded standard-normal column with no relationship to anything.

    THIS IS THE BATCH'S CALIBRATION INSTRUMENT, not a passenger. The registered
    hazard is that v2, holding less knowledge than the consensus-derived board
    the old campaign tested against, has more room for anything at all to look
    useful. F0 measures how often this exact harness — same population, same
    bootstrap, same BH denominator — hands a WIN to a column that provably
    cannot carry signal.

    Deterministic in (player_id, target_season) via a hash rather than a row
    counter, so the value a player gets does not depend on how the universe
    happened to be sorted and the whole arm is reproducible from the seed alone.
    """
    def draw(pid: str) -> float:
        h = hashlib.sha256(
            f"C1-placebo{PLACEBO_SALT}|{target_season}|{pid}".encode()).digest()
        # two independent uniforms from disjoint bytes -> Box-Muller
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))

    return {"placebo_noise": np.array([draw(p) for p in f["player_id"]],
                                      dtype=float)}


# --------------------------------------------------------------- the builder
_BLOCKS = {
    "placebo": _placebo,      # F0
    "snap": _snap_share,      # F1  (batch 7)
    "rzuse": _redzone_usage,  # F2  (new here)
    "xfp": _xfp,              # F3  (batch 6)
    "sep": _separation,       # F4  (batch 3)
    "routes": _routes_block,  # F5  (batch 5, LABELLED PROXY for route counts)
}


def build_features_c1(panel, universe: pd.DataFrame, target_season: int,
                      blocks: Tuple[str, ...] = ()) -> pd.DataFrame:
    """v2's feature set, plus exactly the declared blocks and nothing else.

    With `blocks=()` this IS `build_features_v2` — so the control an arm is
    differenced against is bit-for-bit the object batch-B1 graded, and a NULL can
    never be blamed on a column the arm did not declare.
    """
    f = build_features_v2(panel, universe, target_season)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    for b in blocks:
        if b not in _BLOCKS:
            raise KeyError(f"no C1 block {b!r}")
        block.update(_BLOCKS[b](panel, f, target_season))
    out = pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
    # median-fill after assembly, over the season's own known players — the
    # convention batches 3 and 5 use and the one their write-ups claim
    for c in ("tprr_w",):
        if c in out.columns:
            v = out[c].to_numpy(dtype=float)
            med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
            out[c] = np.where(np.isfinite(v), v, med)
    return out


# ------------------------------------------------------------ the arm registry
#: factor -> the columns it appends to a volume spec. `*_known` indicators travel
#: with their factor: a coverage indicator left out turns "no data" into "zero",
#: which is the `move_known` failure batch 2 was burned by.
FACTOR_COLS: Dict[str, List[str]] = {
    "F0": ["placebo_noise"],
    "F1": ["snapshare_w", "snap_known"],
    "F2": ["rz_use_share_w", "rz_use_known"],
    "F3": ["xfp_pg_w", "xfp_resid_pg_w", "xfp_known"],
    "F4": ["sep_1", "sep_known_1"],
    "F5": ["tprr_w", "rpg_w", "routes_known"],
    "F6": [],                      # F6 changes a constant, not a design matrix
}

FACTOR_BLOCKS: Dict[str, Tuple[str, ...]] = {
    "F0": ("placebo",), "F1": ("snap",), "F2": ("rzuse",), "F3": ("xfp",),
    "F4": ("sep",), "F5": ("routes",), "F6": (),
}

#: the `*_known` column whose mean is the coverage measurement, per factor.
#: F0 is synthetic (always known) and F6 adds no column.
KNOWN_COL: Dict[str, Optional[str]] = {
    "F0": None, "F1": "snap_known", "F2": "rz_use_known", "F3": "xfp_known",
    "F4": "sep_known_1", "F5": "routes_known", "F6": None,
}

# ---------------------------------------------------------- Amendment 1 arms
# Five paired CONTROL arms, registered in batch-C1 Amendment 1 before any arm
# was fitted. Each appends ONLY its factor's coverage indicator to the same
# volume specs at the same positions.
#
# WHY THEY EXIST. Every `*_known` flag above is a presence/join condition, not a
# measurement: `snap_known` is really "did the PFR->gsis crosswalk resolve",
# `sep_known_1` is really "was he inside the NGS QUALIFIED set", and so on. A
# treatment arm can win entirely on that indicator while the metric it is
# attached to contributes nothing. Batch 7 measured this artifact at 215% of its
# own treatment effect and batch 3 wrote a VOID rule for it. Deriving the
# control's column list from the treatment's, rather than retyping it, is what
# guarantees the pair actually differs by exactly the value column.
PAIRED_CONTROL = {f"{f}k": f for f in ("F1", "F2", "F3", "F4", "F5")}

for _k, _f in PAIRED_CONTROL.items():
    FACTOR_COLS[_k] = [KNOWN_COL[_f]]
    FACTOR_BLOCKS[_k] = FACTOR_BLOCKS[_f]
    KNOWN_COL[_k] = KNOWN_COL[_f]
del _k, _f

#: which volume specs a factor column joins, per position (batch-C1 §"Which
#: volume spec each factor enters"). Base lists are imported, never retyped.
_BASE_SPECS: Dict[str, Dict[str, List[str]]] = {
    "WR": {"tpg": _RECEIVER_VOLUME},
    "TE": {"tpg": _RECEIVER_VOLUME},
    "RB": {"carries_pg": _RB_CARRY_VOLUME, "tpg": _RB_TARGET_VOLUME},
    "QB": {"att_pg": _QB_ATT_VOLUME, "carries_pg": _QB_RUSH_VOLUME},
}


def volume_cols_for(factor: str, position: str) -> Dict[str, List[str]]:
    """`{spec name: base features + the factor's columns}` for `volume_cols`."""
    add = FACTOR_COLS[factor]
    if not add:
        return {}
    return {spec: list(base) + list(add)
            for spec, base in _BASE_SPECS[position].items()}


#: coverage floor from the registration: an arm is NO DATA in a cell where fewer
#: than 80% of graded rows carry a real value for the factor's `*_known` flag.
COVERAGE_FLOOR = 0.80
