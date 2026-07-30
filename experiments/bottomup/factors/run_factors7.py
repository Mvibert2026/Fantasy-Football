#!/usr/bin/env python
"""Factor batch 7 -- running-back usage and efficiency. Every registered arm.

    .venv/bin/python -m experiments.bottomup.factors.run_factors7

Design: `docs/ranking/factor-batch-7-precommit.md`, content committed BEFORE any
arm was fitted. 16 registered tests, ALL AT RB.

WHY RB. It is the one position where this project's experiment has demonstrated
statistical power (ADP - heuristic +0.134, CI [+0.043, +0.223]) *and* where the
component model is negative against ADP (-0.0523 board Spearman, 7 seasons).
Power plus a measured deficit is the best place to spend a test.

BH IS APPLIED AT THE CAMPAIGN LEVEL, m = 80, not at the batch level. Four factor
batches are running concurrently against one model; correcting inside each while
ignoring the others is exactly the multiplicity failure CLAUDE.md 6.3 names. The
denominator is fixed in the pre-commitment and does not move afterwards.

FIVE OF THE SIXTEEN ARMS ARE CONTROLS, ON PURPOSE -- four coverage flags and one
binomial placebo. Batch 2 lost three arms to a coverage flag that turned out to
be 95-97% of an apparently large treatment effect (`move_known`). That trigger is
armed here in advance, mechanically, at the 50% ratio batch 3 registered.

Results are written after EVERY arm. Two agents died mid-run today and lost
everything they had computed.
"""

from __future__ import annotations

import sys
import time
import warnings
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E              # noqa: E402
from experiments.bottomup.components import pos_model as M             # noqa: E402
from experiments.bottomup.components.pos_data import build_panel       # noqa: E402
from experiments.bottomup.components.pos_features import build_features  # noqa: E402
from experiments.bottomup.factors.factor_features7 import (            # noqa: E402
    build_factor7_features, sources,
)
from experiments.bottomup.factors.run_factors import (                 # noqa: E402
    benjamini_hochberg, paired,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
POS = "RB"
FIRST, LAST = 2014, 2024

#: Target-season floors, fixed before fitting by ONE mechanical rule applied to
#: every source: the first target season whose TRAINING window contains a season
#: with real lag-1 coverage, i.e. (source first season) + 2. Batch 3 registered
#: this rule for NGS separation (2016 -> 2018); it is reused verbatim so the
#: floors are not a per-arm judgement call.
FIRST_PARTICIPATION = 2018      # participation 2016+
FIRST_SNAPS = 2015              # snap_counts 2013+

CAMPAIGN_M = 80                 # see the pre-commitment 4. Fixed in advance.
BATCH_M = 16                    # reported as a clearly-labelled SECONDARY only
VOID_RATIO = 0.50               # batch 3's control/treatment threshold
TOO_GOOD_PCT = 2.0              # batch 2's escape hatch, re-armed unchanged
INDEP_R2 = 0.90                 # the restatement gate, see the pre-commitment 5

#: coverage gates, measured ON THE ADP BOARD before any result is read
GATES = {"rz": 0.80, "i5": 0.80, "yac": 0.80, "snap": 0.80, "late": 0.80}
_GATE_COL = {"rz": "rzsnap_known", "i5": "i5_known", "yac": "yac_known",
             "snap": "snap_known", "late": "late_known",
             "recshare": "recpts_known"}

#: the model's OWN existing RB feature set. The independence gate asks whether a
#: candidate is already inside this span.
INDEP_COLS = sorted(set(M._RB_CARRY_VOLUME) | set(M._RB_TARGET_VOLUME))
AGE_COLS = ["age", "age2", "experience"]

RB_C = list(M._RB_CARRY_VOLUME)
RB_T = list(M._RB_TARGET_VOLUME)


def _add(cols, *names):
    return list(cols) + [n for n in names if n not in cols]


def _carry(*cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"carries_pg": _add(RB_C, *cols)}}}


def _tgt(*cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"tpg": _add(RB_T, *cols)}}}


# ===================================================== the rate-covariate hook
@dataclass
class RateCovariateRB(M.RBComponentModel):
    """RB model with ONE linear covariate on ONE declared shrunk rate.

    WHY THIS EXISTS AND WHY IT IS A SUBCLASS. Two of batch 7's factors --
    inside-5 TD conversion (N15) and YAC per reception (N16) -- are efficiency
    claims. Their hypotheses live in `tdpc` and `ypr`, not in a volume spec.
    `volume_cols` cannot reach them, and adding them to `carries_pg` instead
    would test a proposition nobody made (that goal-line conversion predicts
    how many carries a back gets). `pos_model.py` is shared with three other
    concurrent factor agents and is not edited here; the hook is a batch-local
    subclass and `_make_model` is overridden rather than `MODELS` monkeypatched.

    THE MECHANISM IS ONE PARAMETER. After the ordinary fit, the residual of the
    realised rate against the model's own shrunk prediction is regressed on the
    centred covariate by weighted least squares, weights = the rate's own
    denominator. At predict time the fitted slope times the centred covariate is
    added before clipping. Veterans only -- rookies keep `rookie_rates`, which
    have no prior season for the covariate to be built from.
    """

    rate_cov: Optional[Tuple[str, str]] = None      # (rate name, feature column)
    cov_beta: float = 0.0
    cov_mean: float = 0.0
    cov_n: int = 0

    def fit(self, feats, outs, rate_pool=None):
        super().fit(feats, outs, rate_pool=rate_pool)
        if self.rate_cov is None:
            return self
        name, col = self.rate_cov
        spec = {r[0]: r for r in self.RATE_SPECS}.get(name)
        if spec is None:
            raise KeyError(f"no RB rate {name!r} to attach a covariate to")
        _, _, _, ynum, yden = spec
        outs = outs.copy()
        outs["opportunity"] = outs["carries"] + outs["targets"]
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y"))
        d = d[d["entry"] == "veteran"]
        if col not in d.columns or not len(d):
            return self
        den = d[yden].to_numpy(dtype=float)
        num = d[ynum].to_numpy(dtype=float)
        ok = np.isfinite(den) & (den > 0)
        if int(ok.sum()) < 30:
            return self
        base = self.rates[name].predict(d)
        y = num[ok] / den[ok] - base[ok]
        x = np.nan_to_num(d[col].to_numpy(dtype=float))[ok]
        w = den[ok]
        self.cov_mean = float(np.average(x, weights=w))
        xc = x - self.cov_mean
        sxx = float(np.sum(w * xc * xc))
        self.cov_beta = float(np.sum(w * xc * y) / sxx) if sxx > 1e-12 else 0.0
        self.cov_n = int(ok.sum())
        return self

    def _rate(self, name, f, is_rk, lo, hi):
        v = super()._rate(name, f, is_rk, lo, hi)
        if self.rate_cov is None or self.rate_cov[0] != name:
            return v
        col = self.rate_cov[1]
        if col not in f.columns:
            return v
        x = np.nan_to_num(f[col].to_numpy(dtype=float))
        adj = self.cov_beta * (x - self.cov_mean)
        return np.clip(np.where(is_rk, v, v + adj), lo, hi)


@dataclass
class WF7(E.WalkForward):
    """WalkForward that can build the rate-covariate model. Identical to the
    parent in every other respect; with `rate_cov=None` it IS the parent."""

    rate_cov: Optional[Tuple[str, str]] = None

    def _make_model(self):
        if self.rate_cov is None:
            return super()._make_model()
        return RateCovariateRB(position=self.position, avail_arm=self.avail_arm,
                               rate_cov=self.rate_cov, **self.model_kwargs)


# ================================================================== the arms
@dataclass
class Arm:
    idx: int
    factor: str
    arm: str
    e1: str                                  # E1 component
    col: Optional[str] = None                # the ONE column that changes
    kwargs: Dict = field(default_factory=dict)
    rate_cov: Optional[Tuple[str, str]] = None
    blocks: Tuple[str, ...] = ()
    first: int = FIRST
    block: Optional[str] = None              # coverage-gate key
    role: str = "treatment"                  # treatment | control
    pair: Optional[int] = None               # control -> its treatment's idx


ARMS: List[Arm] = [
    # ---- Z: red-zone SNAP rate (N14). Presence, not touches.
    Arm(1, "N14 red-zone snap rate", "Z1 RZ-20 snap rate -> carries", "carries",
        "rz20_snap_w", _carry("rz20_snap_w"), blocks=("rz",),
        first=FIRST_PARTICIPATION, block="rz"),
    Arm(2, "N14 red-zone snap rate", "Z2 INSIDE-5 snap rate -> carries", "carries",
        "i5_snap_w", _carry("i5_snap_w"), blocks=("rz",),
        first=FIRST_PARTICIPATION, block="rz"),
    Arm(3, "N14 red-zone snap rate", "Z3 RZ-20 snap rate -> targets", "targets",
        "rz20_snap_w", _tgt("rz20_snap_w"), blocks=("rz",),
        first=FIRST_PARTICIPATION, block="rz"),
    Arm(4, "N14 red-zone snap rate", "Z1c CONTROL coverage flag", "carries",
        "rzsnap_known", _carry("rzsnap_known"), blocks=("rz",),
        first=FIRST_PARTICIPATION, block="rz", role="control", pair=1),
    # ---- G: inside-5 TD conversion vs base rate (N15). A RATE covariate.
    Arm(5, "N15 inside-5 TD conversion", "G1 conversion vs base -> tdpc",
        "rush_tds", "i5_conv_w", rate_cov=("tdpc", "i5_conv_w"), blocks=("i5",),
        block="i5"),
    Arm(6, "N15 inside-5 TD conversion", "G1p CONTROL binomial placebo",
        "rush_tds", "i5_conv_placebo_w",
        rate_cov=("tdpc", "i5_conv_placebo_w"), blocks=("i5",), block="i5",
        role="control", pair=5),
    Arm(7, "N15 inside-5 TD conversion", "G1c CONTROL coverage flag", "rush_tds",
        "i5_known", rate_cov=("tdpc", "i5_known"), blocks=("i5",), block="i5",
        role="control", pair=5),
    # ---- Y: YAC per reception (N16). A RATE covariate on yards per reception.
    Arm(8, "N16 YAC per reception", "Y1 YAC/rec vs base -> ypr", "rec_yards",
        "yac_per_rec_w", rate_cov=("ypr", "yac_per_rec_w"), blocks=("yac",),
        block="yac"),
    Arm(9, "N16 YAC per reception", "Y1c CONTROL coverage flag", "rec_yards",
        "yac_known", rate_cov=("ypr", "yac_known"), blocks=("yac",), block="yac",
        role="control", pair=8),
    # ---- S: receiving share of his OWN fantasy points (N17)
    Arm(10, "N17 receiving share of own points", "S1 receiving points share",
        "targets", "recpts_share_w", _tgt("recpts_share_w"),
        blocks=("recshare",), block="recshare"),
    Arm(11, "N17 receiving share of own points", "S2 >=40% bin (McFarland cut)",
        "targets", "recpts_ge40", _tgt("recpts_ge40"), blocks=("recshare",),
        block="recshare"),
    # ---- P: snap-share persistence (N18)
    Arm(12, "N18 snap-share persistence", "P1 prior snap share", "carries",
        "snapshare_w", _carry("snapshare_w"), blocks=("snap",),
        first=FIRST_SNAPS, block="snap"),
    Arm(13, "N18 snap-share persistence", "P2 >=60% GATE (McFarland cut)",
        "carries", "snap_ge60_w", _carry("snap_ge60_w"), blocks=("snap",),
        first=FIRST_SNAPS, block="snap"),
    Arm(14, "N18 snap-share persistence", "P1c CONTROL coverage flag", "carries",
        "snap_known", _carry("snap_known"), blocks=("snap",),
        first=FIRST_SNAPS, block="snap", role="control", pair=12),
    # ---- L: late-season role trajectory (N19)
    Arm(15, "N19 late-season role trajectory", "L1 his OWN late/early ratio",
        "carries", "late_ratio_w", _carry("late_ratio_w"), blocks=("late",),
        block="late"),
    Arm(16, "N19 late-season role trajectory",
        "L2 GROUP lift, draft round x career year", "carries", "late_lift_grp",
        _carry("late_lift_grp"), blocks=("late",), block="late"),
]


def _feat(blocks: Tuple[str, ...]):
    return partial(build_factor7_features, blocks=blocks, position=POS)


# ------------------------------------------------------- independence gate
def _r2(y: np.ndarray, X: np.ndarray) -> float:
    """R^2 of an OLS of y on X (intercept added). The question the gate asks is
    'does the model already hold this column?', so a high value is a finding
    about the candidate, not about the fit."""
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    if ok.sum() < 20 or float(np.std(y[ok])) < 1e-12:
        return float("nan")
    Xd = np.column_stack([np.ones(int(ok.sum())), X[ok]])
    beta, *_ = np.linalg.lstsq(Xd, y[ok], rcond=None)
    resid = y[ok] - Xd @ beta
    ss_tot = float(np.sum((y[ok] - y[ok].mean()) ** 2))
    return 1.0 - float(np.sum(resid ** 2)) / ss_tot if ss_tot > 0 else float("nan")


def _board_frames(panel, arm: Arm) -> List[pd.DataFrame]:
    """The arm's feature frame restricted to players on the consensus ADP board,
    for every target season it will be graded on. Coverage and independence are
    both measured HERE -- on the decision-relevant population -- and both are
    computed before any arm's result is read."""
    out = []
    fn = _feat(arm.blocks)
    for s in range(arm.first, LAST + 1):
        board = E.adp.load_adp(s, position=POS)
        extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                 if len(board) else None)
        if not extra:
            continue
        u = E.universe_for(panel, s, POS, extra_ids=extra)
        f = fn(panel, u, s)
        sub = f[f["player_id"].isin(extra)]
        if len(sub):
            out.append(sub)
    return out


# ------------------------------------------------------------------ driver
def main() -> None:
    t0 = time.time()
    panel = build_panel()
    src = sources()
    print(f"panel: {len(panel.seasons)} seasons {panel.seasons[0]}-"
          f"{panel.seasons[-1]} (2025 sealed)  [{time.time()-t0:.0f}s]")
    for nm in ("rz", "i5", "yac", "snaps", "half"):
        d = getattr(src, nm)
        print(f"  {nm:6s} {len(d):7d} rows  "
              + (f"{int(d['season'].min())}-{int(d['season'].max())}" if len(d) else "EMPTY"))

    OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict] = []

    # ---- primary, on the SAME builder as the arms with no block declared
    t = time.time()
    wf = E.WalkForward(panel=panel, position=POS, first_target=FIRST,
                       last_target=LAST, avail_arm="A",
                       feature_fn=_feat(()))
    prim_players, prim = wf.run()
    px = sum(a["n_preseason_proxy_reads"] for a in wf.audit)
    print(f"\nprimary {POS}: {len(prim_players)} player-seasons, {len(prim)} seasons, "
          f"proxy reads {px}  [{time.time()-t:.0f}s]")
    if px:
        raise RuntimeError("primary touched a season-N proxy read")

    # ---- REPRODUCTION CHECK against batch 3's own RB primary, asserted not assumed
    b3 = OUT / "factor_batch3_results.csv"
    repro = float("nan")
    if b3.exists():
        r3 = pd.read_csv(b3)
        r3 = r3[(r3["position"] == POS) & (r3["e1_comp"] == "carries")]
        if len(r3) and np.isfinite(r3["primary_err"].iloc[0]):
            repro = float(r3["primary_err"].iloc[0]) - float(prim["mae_carries"].mean())
            print(f"reproduction vs batch 3 primary RB mae_carries: {repro:+.6e}")

    # ---- the RB deficit this batch exists to attack, restated from the primary
    d_prim = (prim["adpsub_rho_model"] - prim["adpsub_rho_b1_adp"]).dropna()
    print(f"primary RB board deficit vs ADP: {d_prim.mean():+.4f} "
          f"over {len(d_prim)} seasons")

    # ---- coverage + independence, on the ADP board, BEFORE any arm's result
    cov: Dict[Tuple, float] = {}
    ind: Dict[str, Tuple[float, float]] = {}
    for a in ARMS:
        key = (a.block, a.first, a.blocks)
        frames = None
        gc = _GATE_COL.get(a.block)
        if key not in cov and gc:
            frames = _board_frames(panel, a)
            vals = [float(f[gc].mean()) for f in frames if gc in f.columns]
            cov[key] = float(np.mean(vals)) if vals else float("nan")
        if a.col and a.col not in ind:
            frames = frames if frames is not None else _board_frames(panel, a)
            if frames:
                big = pd.concat(frames, ignore_index=True)
                # `age2` is created by the model's own `_prep`, not by the
                # feature builder, so the gate has to construct it the same way
                big["age"] = big["age"].fillna(big["age"].median())
                big["age2"] = big["age"] ** 2
                y = big[a.col].to_numpy(dtype=float)
                ind[a.col] = (_r2(y, big[INDEP_COLS].to_numpy(dtype=float)),
                              _r2(y, big[AGE_COLS].to_numpy(dtype=float)))
        a_cov = cov.get(key, float("nan"))

    print("\ncoverage on the ADP board (gate applied BEFORE results are read):")
    for (b, fs, _bl), v in sorted(cov.items(), key=lambda kv: str(kv[0])):
        g = GATES.get(b, 0.80)
        print(f"  {b:9s} from {fs}  {v:.3f}  gate {g:.2f}  "
              f"{'PASS' if v >= g else 'NO DATA'}")
    print("\nindependence R^2 on the ADP board "
          f"(gate: >= {INDEP_R2:.2f} vs the model's own RB columns = RESTATEMENT):")
    for c, (r_all, r_age) in ind.items():
        print(f"  {c:20s} vs model cols {r_all:.4f}   vs age/experience {r_age:.4f}")

    # ---- the arms
    for a in ARMS:
        key = (a.block, a.first, a.blocks)
        c = cov.get(key, float("nan"))
        gate = GATES.get(a.block, 0.80)
        if a.block and not (c >= gate):
            rows.append(dict(idx=a.idx, factor=a.factor, arm=a.arm, position=POS,
                             e1_comp=a.e1, role=a.role, pair=a.pair, coverage=c,
                             grade="NO DATA"))
            print(f"[{a.idx:2d}/16] {a.arm:40s} NO DATA (coverage {c:.3f} < {gate})")
            _flush(rows)
            continue
        t = time.time()
        wf = WF7(panel=panel, position=POS, first_target=a.first, last_target=LAST,
                 avail_arm="A", feature_fn=_feat(a.blocks), rate_cov=a.rate_cov,
                 **a.kwargs)
        pl, m = wf.run()
        px = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        if px:
            raise RuntimeError(f"arm {a.idx} touched a season-N proxy read")
        e1a = paired(m, prim, f"mae_{a.e1}")
        e1b = paired(m, prim, f"adpsub_mae_{a.e1}")
        e2 = paired(m, prim, "adpsub_rho_model")
        sub = prim[prim["season"] >= a.first]
        base = float(sub[f"mae_{a.e1}"].mean())
        base_b = float(sub[f"adpsub_mae_{a.e1}"].mean())
        # E4 -- the deficit itself, not a delta. Does this arm close -0.0523?
        gap = (m["adpsub_rho_model"] - m["adpsub_rho_b1_adp"]).dropna()
        gap_p = (sub["adpsub_rho_model"] - sub["adpsub_rho_b1_adp"]).dropna()
        r2a, r2b = ind.get(a.col, (float("nan"), float("nan")))
        rows.append(dict(
            idx=a.idx, factor=a.factor, arm=a.arm, position=POS, e1_comp=a.e1,
            role=a.role, pair=a.pair, coverage=c, col=a.col,
            indep_r2_model=r2a, indep_r2_age=r2b,
            p=e1a[3], d=e1a[0], lo=e1a[1], hi=e1a[2], n=e1a[4],
            pct=100.0 * e1a[0] / base if base else np.nan,
            e1b_d=e1b[0], e1b_n=e1b[4],
            e1b_pct=100.0 * e1b[0] / base_b if base_b else np.nan,
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            e4_deficit=float(gap.mean()) if len(gap) else np.nan,
            e4_primary=float(gap_p.mean()) if len(gap_p) else np.nan,
            proxy_reads=px, n_players=len(pl), primary_err=base,
            primary_adpsub_err=base_b, first=a.first, repro_vs_batch3=repro))
        print(f"[{a.idx:2d}/16] {a.arm:40s} "
              f"E1a {e1a[0]:+8.4f} ({rows[-1]['pct']:+5.2f}%) "
              f"[{e1a[1]:+7.4f},{e1a[2]:+7.4f}] p={e1a[3]:.4f} n={e1a[4]}  "
              f"E1b {e1b[0]:+7.4f}  E2 {e2[0]:+.4f}  "
              f"E4 {rows[-1]['e4_deficit']:+.4f} (prim {rows[-1]['e4_primary']:+.4f})"
              f"  [{time.time()-t:.0f}s]")
        _flush(rows)

    _grade(pd.DataFrame(rows))
    print(f"\ntotal {time.time()-t0:.0f}s")


def _flush(rows: List[Dict]) -> None:
    pd.DataFrame(rows).to_csv(OUT / "factor_batch7_results.csv", index=False)


def _grade(res: pd.DataFrame) -> None:
    res = res.copy()
    if "grade" not in res.columns:
        res["grade"] = np.nan
    computable = res["grade"].isna()
    pv = res.loc[computable, "p"].fillna(1.0).tolist()
    for q, m_, tag in ((0.10, CAMPAIGN_M, "bh_c10"), (0.05, CAMPAIGN_M, "bh_c05"),
                       (0.10, BATCH_M, "bh_b10")):
        padded = pv + [1.0] * max(0, m_ - len(pv))
        res[tag] = False
        res.loc[computable, tag] = benjamini_hochberg(padded, q)[:int(computable.sum())]

    ctrl = {int(r.pair): abs(r.d) for r in res.itertuples()
            if r.role == "control" and np.isfinite(getattr(r, "d", np.nan))
            and r.pair == r.pair}
    void = {i for i, cd in ctrl.items()
            if any(np.isfinite(r.d) and abs(r.d) > 0 and cd >= VOID_RATIO * abs(r.d)
                   for r in res.itertuples() if r.idx == i)}

    def grade(r) -> str:
        if isinstance(getattr(r, "grade", None), str):
            return r.grade
        if not np.isfinite(getattr(r, "d", np.nan)):
            return "NO DATA"
        if np.isfinite(getattr(r, "indep_r2_model", np.nan)) \
                and r.indep_r2_model >= INDEP_R2 and r.role == "treatment":
            return "RESTATEMENT"
        better = r.d < 0
        if r.bh_c10 and better:
            if int(r.idx) in void:
                return "VOID - COVERAGE ARTIFACT"
            if not (np.isfinite(r.e1b_d) and r.e1b_d < 0):
                return "BOARD-NEUTRAL"
            return "SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0) \
                else "PROJECTION-ONLY"
        if r.bh_c10 and not better:
            return "HARMFUL"
        if np.isfinite(r.lo) and np.isfinite(r.hi):
            if r.lo < 0 and r.hi < 0:
                return "MARGINAL"
            if r.lo > 0 and r.hi > 0:
                return "MARGINAL-HARMFUL"
        return "NULL"

    res["grade"] = [grade(r) for r in res.itertuples()]
    res["void_interpretation"] = res["idx"].isin(void)
    res["too_good"] = res.get("pct", pd.Series(np.nan, index=res.index)).abs() > TOO_GOOD_PCT

    print("\n" + "=" * 110)
    print(f"RESULTS -- CAMPAIGN BH m={CAMPAIGN_M} at q=0.10 (batch-level m={BATCH_M} "
          f"reported as SECONDARY only). E1a = component MAE, negative = better.")
    print("=" * 110)
    for f_, g in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in g.itertuples():
            if r.grade == "NO DATA":
                print(f"  {r.arm:40s} NO DATA")
                continue
            print(f"  {r.arm:40s} {r.d:+8.4f} [{r.lo:+8.4f},{r.hi:+8.4f}] "
                  f"p={r.p:.4f} bhC={'Y' if r.bh_c10 else 'n'} "
                  f"bhB={'Y' if r.bh_b10 else 'n'}  {r.grade}")
    print("\ngrade counts:")
    print(res["grade"].value_counts().to_string())
    if res["too_good"].any():
        print("\n!! TOO-GOOD TRIGGER FIRED (>2% of primary error) -- escalate before "
              "write-up, per CLAUDE.md 8:")
        print(res.loc[res["too_good"], ["idx", "arm", "pct"]].to_string(index=False))
    res.to_csv(OUT / "factor_batch7_results.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch7_results.csv'}")


# ======================================================= POST-HOC diagnostics
# EVERYTHING BELOW IS POST-HOC. It was written after the 16 registered arms had
# been run, it is not in `docs/ranking/factor-batch-7-precommit.md`, and it
# carries a LOWER evidential standard than anything above -- the same rule batch
# 1 §4 and batch 3 §1 applied to their own post-hoc work. No arm's grade may be
# changed by it. It exists because two registered results demand an explanation
# that the registered endpoints cannot give:
#
#   D1  Every red-zone and snap-share arm improves the FULL-UNIVERSE component
#       MAE and DEGRADES the ADP-board MAE, by roughly ten times as much in
#       percentage terms. The registered endpoints report both numbers; they do
#       not say where the full-universe gain physically sits.
#
#   D2  `rzsnap_known` -- a binary "is this player in the participation table at
#       all" flag, registered as a control -- is the LARGEST effect in the whole
#       N14 family, more than double either treatment. What it encodes decides
#       whether the red-zone block is football or bookkeeping.

_D1_ARMS = (1, 2, 12, 16)


def _split_mae(pl: pd.DataFrame, comp: str) -> pd.DataFrame:
    """Per-season component MAE, split by whether the player is on the ADP board.
    `average_pick` is finite exactly for board players (`pos_eval.WalkForward`)."""
    rows = []
    for s, g in pl.groupby("season"):
        e = np.abs(g[f"proj_{comp}"].to_numpy(dtype=float)
                   - g[comp].to_numpy(dtype=float))
        on = np.isfinite(g["average_pick"].to_numpy(dtype=float))
        if on.sum() < 10:
            continue
        rows.append({"season": int(s), "mae_board": float(e[on].mean()),
                     "mae_off": float(e[~on].mean()), "n_board": int(on.sum()),
                     "n_off": int((~on).sum())})
    return pd.DataFrame(rows)


def diagnostics() -> None:
    t0 = time.time()
    panel = build_panel()
    sources()
    out: List[Dict] = []

    prim_wf = E.WalkForward(panel=panel, position=POS, first_target=FIRST,
                            last_target=LAST, avail_arm="A", feature_fn=_feat(()))
    prim_pl, _ = prim_wf.run()

    print("=" * 96)
    print("D1 -- POST-HOC. Where does the full-universe gain physically sit?")
    print("     Component MAE, arm - primary, split by ADP-board membership.")
    print("=" * 96)
    by_idx = {a.idx: a for a in ARMS}
    for i in _D1_ARMS:
        a = by_idx[i]
        wf = WF7(panel=panel, position=POS, first_target=a.first, last_target=LAST,
                 avail_arm="A", feature_fn=_feat(a.blocks), rate_cov=a.rate_cov,
                 **a.kwargs)
        pl, _m = wf.run()
        sa = _split_mae(pl, a.e1)
        sp = _split_mae(prim_pl[prim_pl["season"] >= a.first], a.e1)
        db = paired(sa[["season", "mae_board"]].rename(columns={"mae_board": "v"}),
                    sp[["season", "mae_board"]].rename(columns={"mae_board": "v"}), "v")
        do = paired(sa[["season", "mae_off"]].rename(columns={"mae_off": "v"}),
                    sp[["season", "mae_off"]].rename(columns={"mae_off": "v"}), "v")
        pb, po = float(sp["mae_board"].mean()), float(sp["mae_off"].mean())
        out.append(dict(diag="D1", idx=i, arm=a.arm, comp=a.e1,
                        board_d=db[0], board_lo=db[1], board_hi=db[2], board_p=db[3],
                        board_pct=100 * db[0] / pb if pb else np.nan,
                        off_d=do[0], off_lo=do[1], off_hi=do[2], off_p=do[3],
                        off_pct=100 * do[0] / po if po else np.nan,
                        n_board=int(sp["n_board"].mean()),
                        n_off=int(sp["n_off"].mean())))
        r = out[-1]
        print(f"  {a.arm:40s} board {r['board_d']:+8.4f} ({r['board_pct']:+6.2f}%)  "
              f"off-board {r['off_d']:+8.4f} ({r['off_pct']:+6.2f}%)   "
              f"n {r['n_board']}/{r['n_off']}")

    print("\n" + "=" * 96)
    print("D2 -- POST-HOC. What does `rzsnap_known` actually encode?")
    print("=" * 96)
    fn = _feat(("rz", "snap"))
    frames = []
    for s in range(FIRST_PARTICIPATION, LAST + 1):
        board = E.adp.load_adp(s, position=POS)
        extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                 if len(board) else None)
        u = E.universe_for(panel, s, POS, extra_ids=extra)
        f = fn(panel, u, s)
        f["on_board"] = f["player_id"].isin(extra or [])
        frames.append(f)
    big = pd.concat(frames, ignore_index=True)
    k = big["rzsnap_known"] > 0.5
    rk = big["entry"] == "rookie"
    row = dict(diag="D2", n=len(big), known_share=float(k.mean()),
               rookie_share=float(rk.mean()),
               p_unknown_given_rookie=float(1 - k[rk].mean()),
               p_rookie_given_unknown=float(rk[~k].mean()),
               agree_known_eq_notrookie=float((k == ~rk).mean()),
               mean_games1_known=float(big.loc[k, "games_1"].mean()),
               mean_games1_unknown=float(big.loc[~k, "games_1"].mean()),
               mean_evidence_known=float(big.loc[k, "evidence"].mean()),
               mean_evidence_unknown=float(big.loc[~k, "evidence"].mean()),
               board_share_known=float(big.loc[k, "on_board"].mean()),
               board_share_unknown=float(big.loc[~k, "on_board"].mean()))
    out.append(row)
    for kk, vv in row.items():
        if kk != "diag":
            print(f"  {kk:32s} {vv}")

    pd.DataFrame(out).to_csv(OUT / "factor_batch7_diagnostics.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch7_diagnostics.csv'}  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    if "--diagnostics" in sys.argv:
        diagnostics()
    else:
        main()
