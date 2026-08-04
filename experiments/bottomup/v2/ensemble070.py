"""ADR-070 §4.1 — matched per-cell permutation null ensembles, on the tier-2 panel.

This is the DRAW ENGINE. `adr070.py` is the pure decision machinery that consumes
draws; `sweep070.py` is the detached queue driver that schedules them. This module
owns everything in between:

  * the tier-2 window map (ADR-070 §4.8 ruling, 2026-08-01): grading universe
    `m_panel_ppr12` (FFC ppr 12-team archive, 2013-2024), deepest clean training
    window per position. WR/TE cannot reach target 2013 without either
    `min_train_seasons=1` or training across the 2003-2008 targets hole, so their
    span is 2014-2024 (S_pos=11) — logged as decision D1 in
    `docs/ranking/adr070-tier2-execution.md`, not silently absorbed.
  * the §4.1 primary null: joint within-season row permutation of the arm's own
    column block, seed = sha256(f"{arm}|{position}|{season}|{k}") — the season,
    not the call, keys the permutation, so a season's null column is a fixed
    property of the draw. Matches column count, marginals, within-block
    correlation and `*_known` coverage by construction.
  * dimension-matched Gaussian placebo cells (§4.1 secondary; §6.2(b) agreement),
    d ∈ {1,2,3} seeded noise columns.
  * per-(position, season) cell metrics for BOTH registered endpoint families —
    per-season Spearman on points (C1/C2 re-runs) and games MAE (D1 Amendment 1),
    plus the §4.6 item-5 Pearson diagnostic and the mandatory tier-3 co-report
    (`rho_points_fullvet`).
  * canonical delta extraction (positive = better, §4.7 derived snap), with the
    §4.8 provenance key asserted identical between arm and control by
    `adr070.assert_joinable` — a cross-universe or cross-span delta RAISES.

Look-ahead: nothing here hand-rolls a cutoff. Every run goes through the audited
`WalkForward` (panel gates + per-target audit assertions), targets end 2024, the
2025 holdout is sealed by the panel's own gates. No week-1-of-target-season
roster status is read anywhere (`allow_preseason_proxy=False` on every run).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..components import pos_eval as E
from ..components.pos_eval import WalkForward
from .adr070 import ProvKey, assert_joinable, snap_deltas
from .weekshape import build_v2_panel
from .features_v2 import build_features_v2

# import for the side effect too: both extend E._CARRY with their factor columns
from . import run_c1 as _rc1
from . import run_c2 as _rc2
from .factors_c1 import (
    FACTOR_BLOCKS as C1_BLOCKS, FACTOR_COLS as C1_COLS, KNOWN_COL as C1_KNOWN,
    build_features_c1, steep_recency, volume_cols_for as c1_volume_cols_for,
    _BASE_SPECS,
)
from .factors_c2 import (
    FACTOR_BLOCKS as C2_BLOCKS, FACTOR_COLS as C2_COLS, KNOWN_COL as C2_KNOWN,
    build_features_c2, volume_cols_for as c2_volume_cols_for,
)
from . import d1a1_models as q0m

HOLDOUT_SEASON = 2025
POSITIONS = ("QB", "RB", "WR", "TE")

# ---------------------------------------------------------------- tier-2 map
UNIVERSE = "m_panel_ppr12"
ADP_FMT = "ppr_12team"
LAST_TARGET = 2024

#: family -> position -> (first_feature_season, first_target).
#: T2A is the adopted deep window (ff=2002 QB/RB; WR/TE bounded by the targets
#: hole at ff=2012 -> first target 2014 with min_train_seasons=2). T2B/C/D are
#: the C1/C2 late-source families re-based onto the tier-2 universe, unchanged
#: ff, targets extended to the earliest their own window reaches.
TIER2: Dict[str, Dict[str, Tuple[int, int]]] = {
    "T2A": {"QB": (2002, 2013), "RB": (2002, 2013),
            "WR": (2012, 2014), "TE": (2012, 2014)},
    "T2B": {p: (2015, 2017) for p in POSITIONS},
    "T2C": {p: (2017, 2019) for p in POSITIONS},
    "T2D": {p: (2018, 2021) for p in POSITIONS},
    # Q0's own family: board-membership history (the ppr12 archive) starts
    # 2013, and Q0-restrict requires >= 2 board training seasons, so its first
    # target is 2015 — the CTRL-A/B/C late-source discipline applied to the
    # board archive itself. S_pos = 10 at all four positions. Deviation from
    # the amendment's blanket "targets 2013-2024" logged as D7 in
    # docs/ranking/adr070-tier2-execution.md.
    "T2Q": {"QB": (2002, 2015), "RB": (2002, 2015),
            "WR": (2012, 2015), "TE": (2012, 2015)},
}

C1_FAMILY = {"CTRL-A": "T2A", "CTRL-B": "T2B", "CTRL-C": "T2C"}
C2_FAMILY = {"CTRL-A2": "T2A", "CTRL-D": "T2D"}


def window_for(family: str, position: str) -> Tuple[int, int, int]:
    ff, ft = TIER2[family][position]
    return ff, ft, LAST_TARGET


def key_for(family: str, position: str) -> ProvKey:
    ff, ft, lt = window_for(family, position)
    return ProvKey(universe=UNIVERSE, targets=f"{ft}-{lt}", S=lt - ft + 1,
                   first_feature_season=ff)


# ------------------------------------------------------------------ arm spec
@dataclass(frozen=True)
class Arm070:
    """One arm of one batch, tier-2. `block_cols` empty => no §4.1 permutation
    ensemble exists for it (the F6/Q0 class); Q0 uses the membership-permutation
    null implemented in `d1a1_models` instead (decision D3)."""
    batch: str                    # "C1" | "C2" | "D1A1" | "VERIFY"
    arm: str
    family: str
    positions: Tuple[str, ...]
    endpoint: str                 # "rho_points" | "mae_games"
    block_cols: Tuple[str, ...]
    known_col: Optional[str]
    null_kind: str                # "perm_block" | "perm_membership" | "none"


def _c1_arms() -> Dict[str, Arm070]:
    out = {}
    for arm, (ctrl, poss) in _rc1.ARMS.items():
        out[arm] = Arm070(
            batch="C1", arm=arm, family=C1_FAMILY[ctrl], positions=tuple(poss),
            endpoint="rho_points", block_cols=tuple(C1_COLS[arm]),
            known_col=C1_KNOWN.get(arm),
            null_kind="perm_block" if C1_COLS[arm] else "none")
    return out


def _c2_arms() -> Dict[str, Arm070]:
    out = {}
    for arm, (ctrl, poss) in _rc2.ARMS.items():
        out[arm] = Arm070(
            batch="C2", arm=arm, family=C2_FAMILY[ctrl], positions=tuple(poss),
            endpoint="rho_points", block_cols=tuple(C2_COLS[arm]),
            known_col=C2_KNOWN.get(arm),
            null_kind="perm_block" if C2_COLS[arm] else "none")
    return out


#: D1 Amendment 1 (registered by strategist 2026-08-01, before any arm was
#: fitted). Q0 runs FIRST. Endpoint is games MAE on the M-panel — points never
#: enters the endpoint (the amendment's §4). Q0w is the registered weighting
#: variant of the same arm, co-reported, NOT a separate graded cell (m_b = 12
#: counts three arms; grading two Q0 variants would spend an unregistered slot).
#: PG0 is the standing-placebo calibration arm on this endpoint (decision D4):
#: graded through the full rule, contributes 0 tests.
D1A1_ARMS: Dict[str, Arm070] = {
    "Q0": Arm070("D1A1", "Q0", "T2Q", POSITIONS, "mae_games", (),
                 None, "perm_membership"),
    "Q0w": Arm070("D1A1", "Q0w", "T2Q", POSITIONS, "mae_games", (),
                  None, "perm_membership"),
    "Q1": Arm070("D1A1", "Q1", "T2A", POSITIONS, "mae_games",
                 tuple(q0m.QUALITY_BLOCK), None, "perm_block"),
    "Q2": Arm070("D1A1", "Q2", "T2A", POSITIONS, "mae_games",
                 tuple(q0m.QUALITY_BLOCK_NO_PPG), None, "perm_block"),
    "PG0": Arm070("D1A1", "PG0", "T2A", POSITIONS, "mae_games",
                  (q0m.AVAIL_PLACEBO_COL,), None, "perm_block"),
}

#: §6.2 verification cells: dimension-matched seeded-noise arms, d ∈ {1,2,3},
#: on the primary (rho_points) endpoint at the base window. VD1 doubles as the
#: §6.2(a) leave-one-out implementation check (K = 200 fixed draws).
VERIFY_ARMS: Dict[str, Arm070] = {
    f"VD{d}": Arm070("VERIFY", f"VD{d}", "T2A", POSITIONS, "rho_points",
                     tuple(f"v070_placebo_{j}" for j in range(d)),
                     None, "perm_block")
    for d in (1, 2, 3)
}

ARMS070: Dict[Tuple[str, str], Arm070] = {}
for _a in _c1_arms().values():
    ARMS070[("C1", _a.arm)] = _a
for _a in _c2_arms().values():
    ARMS070[("C2", _a.arm)] = _a
for _a in D1A1_ARMS.values():
    ARMS070[("D1A1", _a.arm)] = _a
for _a in VERIFY_ARMS.values():
    ARMS070[("VERIFY", _a.arm)] = _a
del _a


# ----------------------------------------------------------- seeds & permute
def seed_from(s: str) -> int:
    """sha256, never builtin hash() (guardrails §11.1)."""
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


def _noise_col(salt: str, target_season: int, ids: Sequence[str]) -> np.ndarray:
    """Deterministic standard normal per (salt, season, player) — the C1 F0
    construction, reused for the dimension-matched verification arms."""
    def draw(pid: str) -> float:
        h = hashlib.sha256(f"{salt}|{target_season}|{pid}".encode()).digest()
        u1 = (int.from_bytes(h[0:8], "big") + 1) / (2 ** 64 + 1)
        u2 = int.from_bytes(h[8:16], "big") / (2 ** 64)
        return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))
    return np.array([draw(p) for p in ids], dtype=float)


def permuted_fn(base_fn: Callable, block_cols: Sequence[str], arm: str,
                position: str, k: int) -> Callable:
    """§4.1 primary null: joint within-season row permutation of the arm's own
    column block, every frame the walk-forward builds, training and target
    alike. k = 0 returns the base builder untouched."""
    if k == 0 or not block_cols:
        return base_fn

    def fn(panel, universe, target_season):
        f = base_fn(panel, universe, target_season)
        present = [c for c in block_cols if c in f.columns]
        if present:
            rng = np.random.default_rng(
                seed_from(f"{arm}|{position}|{int(target_season)}|{int(k)}"))
            perm = rng.permutation(len(f))
            f = f.copy()
            f[present] = f[present].to_numpy()[perm]
        return f
    return fn


# ------------------------------------------------------------- feature fns
#: batch -> {"feature_fn": (arm, position) -> builder,
#:           "model_kwargs": (arm, position) -> dict}. Adapter-registered
#: batches (C3) plug in here without editing this module's dispatch.
BATCH_HOOKS: Dict[str, Dict[str, Callable]] = {}


def _base_feature_fn(a: Arm070, position: str, is_control: bool) -> Callable:
    if is_control:
        # every family's control is bit-for-bit build_features_v2
        return lambda panel, universe, ts: build_features_v2(panel, universe, ts)
    if a.batch == "C1":
        blocks = C1_BLOCKS[a.arm]
        return lambda panel, universe, ts: build_features_c1(
            panel, universe, ts, blocks=blocks)
    if a.batch == "C2":
        blocks = C2_BLOCKS[a.arm]
        return lambda panel, universe, ts: build_features_c2(
            panel, universe, ts, blocks=blocks, position=position)
    if a.batch == "VERIFY":
        d = len(a.block_cols)

        def fn(panel, universe, ts):
            f = build_features_v2(panel, universe, ts)
            f = f.copy()
            for j in range(d):
                f[f"v070_placebo_{j}"] = _noise_col(f"V070-{j}", ts,
                                                    f["player_id"].tolist())
            return f
        return fn
    if a.batch == "D1A1":
        if a.arm == "PG0":
            def fn(panel, universe, ts):
                f = build_features_v2(panel, universe, ts)
                f = f.copy()
                f[q0m.AVAIL_PLACEBO_COL] = _noise_col("PG0", ts,
                                                      f["player_id"].tolist())
                return f
            return fn
        return lambda panel, universe, ts: build_features_v2(panel, universe, ts)
    if a.batch in BATCH_HOOKS:
        return BATCH_HOOKS[a.batch]["feature_fn"](a.arm, position)
    raise KeyError(f"no feature fn for {a}")


def _model_kwargs(a: Arm070, position: str, is_control: bool) -> Dict:
    if is_control:
        return {}
    if a.batch == "C1":
        return ({"volume_cols": c1_volume_cols_for(a.arm, position)}
                if C1_COLS[a.arm] else {})
    if a.batch == "C2":
        return ({"volume_cols": c2_volume_cols_for(a.arm, position)}
                if C2_COLS[a.arm] else {})
    if a.batch == "VERIFY":
        return {"volume_cols": {spec: list(base) + list(a.block_cols)
                                for spec, base in _BASE_SPECS[position].items()}}
    if a.batch == "D1A1":
        return {}   # model factory handles the games channel
    if a.batch in BATCH_HOOKS:
        return BATCH_HOOKS[a.batch]["model_kwargs"](a.arm, position)
    raise KeyError(f"no model kwargs for {a}")


# ------------------------------------------------- audit-preserving cache
class CachedFeatureFn:
    """Memoise BASE (pre-permutation) feature frames across draws of the same
    cell. The expensive part of a null draw is rebuilding ~20 identical
    training frames; only the permutation and the fits differ between draws.

    AUDIT SEMANTICS PRESERVED: the access-log entries generated by the first
    build are recorded and REPLAYED on every cache hit — the same discipline
    `WalkForward._season_pair` documents for its own memo. A cache that
    silently suppressed audit entries would weaken the one check that makes
    the harness trustworthy.

    The key includes a digest of the universe's player ids: the same season
    appears with different universes depending on its role (training frames
    carry no board extras; the target frame does), and those frames must not
    be conflated.
    """

    def __init__(self, base_fn: Callable, cache: Dict, prefix: str) -> None:
        self.base_fn = base_fn
        self.cache = cache
        self.prefix = prefix

    def __call__(self, panel, universe, target_season):
        uhash = hashlib.md5("|".join(sorted(universe["player_id"].astype(str)))
                            .encode()).hexdigest()[:12]
        key = (self.prefix, int(target_season), uhash)
        hit = self.cache.get(key)
        if hit is None:
            n0 = len(panel.access_log)
            f = self.base_fn(panel, universe, target_season)
            self.cache[key] = (f, list(panel.access_log[n0:]))
            return f
        f, entries = hit
        panel.access_log.extend(entries)
        return f


# ------------------------------------------------------------ the runner
@dataclass
class Run070WalkForward(WalkForward):
    """WalkForward + an optional model factory (the run_d1 pattern), so the
    D1A1 arms can swap the games channel without touching the shared harness."""
    model_factory: Optional[Callable] = None

    def _make_model(self):
        if self.model_factory is not None:
            return self.model_factory()
        return super()._make_model()


def run_players(panel, batch: str, arm: str, position: str,
                k: int = 0, frame_cache: Optional[Dict] = None) -> pd.DataFrame:
    """One run of one arm at permutation draw k. k=0 is the observed run.
    Controls are separate labels via `run_control`. `frame_cache` (worker-local
    dict) memoises base frames across draws of the same cell — see
    CachedFeatureFn for why the audit survives it."""
    a = ARMS070[(batch, arm)]
    ff, ft, lt = window_for(a.family, position)
    base_fn = _base_feature_fn(a, position, is_control=False)
    if frame_cache is not None:
        base_fn = CachedFeatureFn(base_fn, frame_cache,
                                  f"{batch}:{a.arm}:{position}")
    if a.null_kind == "perm_ablate":
        # INVERTED §4.1 for incumbent ablations. Observed arm (k=0): the
        # incumbent specs with the channel REMOVED. Null draw (k>=1): the FULL
        # incumbent specs with the channel's rows permuted within season —
        # under H0 (channel uninformative) the removal differs from the
        # control only by the variance cost of a noise block, which is
        # exactly what the permuted block mimics. Both difference against the
        # same unmodified control.
        if k == 0:
            fn = base_fn
            kwargs = _model_kwargs(a, position, is_control=False)
        else:
            fn = permuted_fn(base_fn, a.block_cols, f"{batch}:{a.arm}",
                             position, k)
            kwargs = {}
    else:
        fn = permuted_fn(base_fn, a.block_cols, f"{batch}:{a.arm}", position, k)
        kwargs = _model_kwargs(a, position, is_control=False)

    factory = None
    if a.batch == "D1A1":
        factory = q0m.model_factory(a.arm, position, perm_k=(
            k if a.null_kind == "perm_membership" else 0))

    wf = Run070WalkForward(
        panel=panel, position=position, first_target=ft, last_target=lt,
        min_train_seasons=2, avail_arm="A", calibrate_bonus=True,
        first_feature_season=ff, feature_fn=fn,
        model_kwargs=kwargs,
        allow_preseason_proxy=False, adp_fmt=ADP_FMT, model_factory=factory)

    if batch == "C1" and a.arm == "F6":
        with steep_recency():
            players, _ = wf.run()
    else:
        players, _ = wf.run()
    _assert_clean(wf, players, f"{batch}:{a.arm}:{position}:k{k}")
    players["position"] = position
    return players


def run_control(panel, family: str, position: str) -> pd.DataFrame:
    ff, ft, lt = window_for(family, position)
    wf = Run070WalkForward(
        panel=panel, position=position, first_target=ft, last_target=lt,
        min_train_seasons=2, avail_arm="A", calibrate_bonus=True,
        first_feature_season=ff,
        feature_fn=lambda p, u, ts: build_features_v2(p, u, ts),
        model_kwargs={}, allow_preseason_proxy=False, adp_fmt=ADP_FMT)
    players, _ = wf.run()
    _assert_clean(wf, players, f"CTRL:{family}:{position}")
    players["position"] = position
    return players


def _assert_clean(wf: WalkForward, players: pd.DataFrame, label: str) -> None:
    aud = pd.DataFrame(wf.audit)
    assert (aud.max_feature_cutoff < aud.season).all(), f"{label} feature leak"
    assert (aud.max_outcome_season < aud.season).all(), f"{label} outcome leak"
    assert (aud.n_outcome_reads_at_target == 0).all(), f"{label} target read"
    assert (aud.n_preseason_proxy_reads == 0).all(), f"{label} proxy read"
    assert players["season"].max() < HOLDOUT_SEASON, f"{label} HOLDOUT TOUCHED"


# --------------------------------------------------------------- cell metrics
def season_cells(players: pd.DataFrame, run_label: str, batch: str,
                 position: str, family: str, known_col: Optional[str],
                 k: int) -> pd.DataFrame:
    """One row per season, all metrics both endpoint families need, tagged with
    the §4.8 provenance key. Board = M-panel veterans (average_pick from the
    ppr12 archive); full-veteran co-report mandatory."""
    key = key_for(family, position)
    rows: List[Dict] = []
    for season, g in players.groupby("season"):
        vet = g[g["entry"] == "veteran"]
        sub = vet[vet["average_pick"].notna()]
        row: Dict = {"batch": batch, "run": run_label, "position": position,
                     "season": int(season), "k": int(k),
                     **key.as_dict(),
                     "n_board_vet": len(sub), "n_vet": len(vet)}
        if len(sub) >= 10:
            pp = sub["proj_points"].to_numpy(dtype=float)
            ap = sub["points"].to_numpy(dtype=float)
            row["rho_points"] = E.spearman(pp, ap)
            if np.std(pp) > 0 and np.std(ap) > 0:
                row["pearson_points"] = float(np.corrcoef(pp, ap)[0, 1])
            pg = sub["proj_games"].to_numpy(dtype=float)
            gm = sub["games"].to_numpy(dtype=float)
            row["mae_games"] = float(np.mean(np.abs(pg - gm)))
            row["bias_games"] = float(np.mean(pg - gm))
            row["rho_games"] = E.spearman(pg, gm)
            g1 = (sub["games_1"] if "games_1" in sub.columns
                  else pd.Series(0.0, index=sub.index))
            row["mae_naive_games"] = float(
                np.mean(np.abs(g1.fillna(0.0).to_numpy(dtype=float) - gm)))
        if len(vet) >= 10:
            row["rho_points_fullvet"] = E.spearman(
                vet["proj_points"].to_numpy(dtype=float),
                vet["points"].to_numpy(dtype=float))
            row["mae_games_fullvet"] = float(np.mean(np.abs(
                vet["proj_games"].to_numpy(dtype=float)
                - vet["games"].to_numpy(dtype=float))))
            row["bias_games_fullvet"] = float(np.mean(
                vet["proj_games"].to_numpy(dtype=float)
                - vet["games"].to_numpy(dtype=float)))
        if known_col and known_col in sub.columns and len(sub):
            row["coverage"] = float(pd.to_numeric(
                sub[known_col], errors="coerce").fillna(0.0).mean())
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------- delta extraction
KEY_FIELDS = ("universe", "targets", "S", "first_feature_season")


def _key_of(cells: pd.DataFrame) -> ProvKey:
    u = cells[list(KEY_FIELDS)].drop_duplicates()
    if len(u) != 1:
        raise RuntimeError(f"cells carry {len(u)} distinct provenance keys")
    r = u.iloc[0]
    return ProvKey(universe=str(r["universe"]), targets=str(r["targets"]),
                   S=int(r["S"]), first_feature_season=int(r["first_feature_season"]))


def canonical_deltas(arm_cells: pd.DataFrame, ctrl_cells: pd.DataFrame,
                     endpoint: str) -> pd.DataFrame:
    """Per-season canonical deltas (positive = arm better), §4.7-snapped.
    RAISES on any provenance-key mismatch (§4.8 rule 1/4)."""
    assert_joinable(_key_of(arm_cells), _key_of(ctrl_cells),
                    what=f"{endpoint} cells")
    a = arm_cells.set_index("season")
    b = ctrl_cells.set_index("season")
    seasons = sorted(set(a.index) & set(b.index))
    rows = []
    for s in seasons:
        av, bv = a.loc[s], b.loc[s]
        n = int(min(av["n_board_vet"], bv["n_board_vet"]))
        if endpoint == "rho_points":
            d = float(av.get("rho_points", np.nan)) - float(bv.get("rho_points", np.nan))
            continuous = False
        elif endpoint == "mae_games":
            d = float(bv.get("mae_games", np.nan)) - float(av.get("mae_games", np.nan))
            continuous = True
        else:
            raise KeyError(f"unknown endpoint {endpoint!r}")
        rows.append({"season": int(s), "delta": d, "n_graded": n,
                     "continuous": continuous})
    df = pd.DataFrame(rows)
    if len(df):
        df["delta"] = snap_deltas(df["delta"].to_numpy(dtype=float),
                                  df["n_graded"].tolist(),
                                  continuous=bool(df["continuous"].iloc[0]))
    return df


_PANEL = None


def shared_panel():
    """One panel per process (memoised); the sweep's worker initializer."""
    global _PANEL
    if _PANEL is None:
        _PANEL = build_v2_panel()
    return _PANEL
