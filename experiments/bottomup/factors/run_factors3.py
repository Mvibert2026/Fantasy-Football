#!/usr/bin/env python
"""Factor batch 3 -- run every arm declared in the pre-commitment.

    .venv/bin/python -m experiments.bottomup.factors.run_factors3

Design: `docs/ranking/factor-batch-3-precommit.md`, content committed `1c452a1`
BEFORE any arm was fitted. 24 registered tests in two families; BH is applied at
the CAMPAIGN level, m = 24, not per family and not per test.

  F1  16 model arms.   E1a = full-universe component MAE, arm - primary.
  F2   8 baselines.    E3  = full-universe Spearman, candidate - incumbent.

  E1b  the same MAE on the ADP board, 7 seasons -- a REQUIRED DIRECTION CHECK,
       not the significance test.
  E2   ADP-board Spearman, 7 seasons, the bar. NOT in the FDR family.

THREE OF THE SIXTEEN ARMS ARE CONTROLS, ON PURPOSE. `sep_known_1`,
`expl_known` and `oc_tenure_known` each enter the model ALONE, so that batch 2's
defect -- a coverage flag turning out to be 95-97% of an apparently large
treatment effect -- is measured in advance instead of discovered afterwards. The
VOID rule at 50% is in the pre-commitment and is applied here mechanically.

Results are written after EVERY arm, not at the end. Two prior runs died on a
session limit and lost everything they had computed.
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

from experiments.bottomup.components import pos_eval as E             # noqa: E402
from experiments.bottomup.components import pos_model as M            # noqa: E402
from experiments.bottomup.components.pos_data import build_panel      # noqa: E402
from experiments.bottomup.factors.factor_features3 import (           # noqa: E402
    build_factor3_features,
)
from experiments.bottomup.factors.run_factors import (                # noqa: E402
    benjamini_hochberg, paired,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024
NGS_FIRST = 2018            # 4 of the pre-commitment: fixed before fitting
CAMPAIGN_M = 24             # 4: fixed regardless of how many arms compute
VOID_RATIO = 0.50           # 5: control/treatment threshold, fixed in advance
TOO_GOOD_PCT = 2.0          # 5: batch 2's escape hatch, re-armed unchanged

GATES = {"oc": 0.80, "sep": 0.60, "expl": 0.80}

FEAT = partial(build_factor3_features)                       # primaries
FEAT_SEP = partial(build_factor3_features, blocks=("sep",))
FEAT_EXPL = partial(build_factor3_features, blocks=("expl",))
FEAT_OC = partial(build_factor3_features, blocks=("oc",))
FEAT_C1 = partial(build_factor3_features, use_batch2=True)

REC_V = list(M._RECEIVER_VOLUME)
RB_C = list(M._RB_CARRY_VOLUME)
QB_A = list(M._QB_ATT_VOLUME)
QB_R = list(M._QB_RUSH_VOLUME)


#: which feature column each block's coverage gate is measured on. C1Q overrides
#: it, because batch 2's block ships `oc_known`, not `oc_tenure_known`.
_GATE_COL = {"sep": "sep_known_1", "expl": "expl_known", "oc": "oc_tenure_known"}


def _add(cols, *names):
    return list(cols) + [n for n in names if n not in cols]


def _drop(cols, *names):
    return [c for c in cols if c not in names]


@dataclass
class Arm:
    idx: int
    factor: str
    arm: str
    position: str
    e1: str
    kwargs: Dict = field(default_factory=dict)
    feat: str = "base"
    first: int = FIRST
    block: Optional[str] = None      # coverage gate + control pairing key
    role: str = "treatment"          # treatment | control | ablation
    pair: Optional[int] = None       # control arm's treatment idx
    gate_col: Optional[str] = None   # defaults from `block`; C1Q uses batch 2's

    @property
    def gate_key(self):
        return (self.block, self.position, self.gate_col or _GATE_COL[self.block])


def _rec(*cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"tpg": _add(REC_V, *cols)}}}


def _rb(*cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"carries_pg": _add(RB_C, *cols)}}}


def _qb_att(*cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"att_pg": _add(QB_A, *cols)}}}


ARMS: List[Arm] = [
    # ---- A: QB rushing (sweep N9). One ablation, one addition.
    Arm(1, "N9 QB rushing volume", "A1 QB rush block ABLATION", "QB", "carries",
        {"model_kwargs": {"volume_cols": {
            "carries_pg": _drop(QB_R, "carries_pg_w", "rushyds_pg_w")}}},
        "base", role="ablation"),
    Arm(2, "N9 QB rushing volume", "A2 QB rush -> PASSING volume", "QB", "attempts",
        _qb_att("carries_pg_w"), "base"),
    # ---- S: NGS average separation (sweep N5). 7 seasons, declared in advance.
    Arm(3, "N5 NGS separation", "S1 avg separation", "WR", "targets",
        _rec("sep_1"), "sep", first=NGS_FIRST, block="sep"),
    Arm(4, "N5 NGS separation", "S1 avg separation", "TE", "targets",
        _rec("sep_1"), "sep", first=NGS_FIRST, block="sep"),
    Arm(5, "N5 NGS separation", "S1c CONTROL coverage flag", "WR", "targets",
        _rec("sep_known_1"), "sep", first=NGS_FIRST, block="sep",
        role="control", pair=3),
    Arm(6, "N5 NGS separation", "S1c CONTROL coverage flag", "TE", "targets",
        _rec("sep_known_1"), "sep", first=NGS_FIRST, block="sep",
        role="control", pair=4),
    # ---- X: explosive rushing (sweep N13)
    Arm(7, "N13 explosive rush rate", "X1 own explosive rate", "RB", "carries",
        _rb("expl_w"), "expl", block="expl"),
    Arm(8, "N13 explosive rush rate", "X2 CLUB-RELATIVE explosive rate", "RB",
        "carries", _rb("expl_rel_w"), "expl", block="expl"),
    Arm(9, "N13 explosive rush rate", "X1c CONTROL coverage flag", "RB", "carries",
        _rb("expl_known"), "expl", block="expl", role="control", pair=7),
    # ---- T: coordinator TENURE, four positions incl. QB
    Arm(10, "#29 coordinator tenure", "T1 OC tenure", "QB", "attempts",
        _qb_att("oc_tenure"), "oc", block="oc"),
    Arm(11, "#29 coordinator tenure", "T1 OC tenure", "WR", "targets",
        _rec("oc_tenure"), "oc", block="oc"),
    Arm(12, "#29 coordinator tenure", "T1 OC tenure", "TE", "targets",
        _rec("oc_tenure"), "oc", block="oc"),
    Arm(13, "#29 coordinator tenure", "T1 OC tenure", "RB", "carries",
        _rb("oc_tenure"), "oc", block="oc"),
    Arm(14, "#29 coordinator tenure", "T1c CONTROL coverage flag", "QB", "attempts",
        _qb_att("oc_tenure_known"), "oc", block="oc", role="control", pair=10),
    Arm(15, "#29 coordinator tenure", "T1c CONTROL coverage flag", "WR", "targets",
        _rec("oc_tenure_known"), "oc", block="oc", role="control", pair=11),
    # ---- C: batch 2's own new_oc block, at the position batch 2 never ran
    Arm(16, "#29 coordinator change", "C1Q new_oc (batch-2 spec) AT QB", "QB",
        "attempts", _qb_att("new_oc"), "c1", block="oc", gate_col="oc_known"),
]

_FEATS = {"base": FEAT, "sep": FEAT_SEP, "expl": FEAT_EXPL, "oc": FEAT_OC,
          "c1": FEAT_C1}
_PROXY = {"base": False, "sep": False, "expl": False, "oc": True, "c1": True}


# --------------------------------------------------------------- F2 baselines
def _baseline_rhos(players: pd.DataFrame) -> pd.DataFrame:
    """Per season: rank correlation with realised points for each candidate
    reference ranker. No model is refitted -- these are alternative BASELINES,
    and every column below is a function of season N-1 only."""
    rows = []
    for s, g in players.groupby("season"):
        act = g["points"].to_numpy(dtype=float)
        pts1 = g["pts_1"].fillna(0.0).to_numpy(dtype=float)
        gm1 = g["games_1"].fillna(0.0).to_numpy(dtype=float)
        gs1 = g["gshare_1"].fillna(0.0).to_numpy(dtype=float)
        ppg1 = np.where(gm1 > 0, pts1 / np.where(gm1 > 0, gm1, 1.0), 0.0)
        row = {"season": int(s), "n": len(g)}
        cand = {"b2": pts1, "b2r": ppg1, "b2ra": ppg1 * gs1,
                "b3": (g["ppg_w"].fillna(0.0) * g["gshare_w"].fillna(0.0)
                       ).to_numpy(dtype=float)}
        has_adp = np.isfinite(g["average_pick"].to_numpy(dtype=float))
        for k, v in cand.items():
            row[f"rho_{k}"] = E.spearman(v, act)
            if has_adp.sum() >= 10:
                row[f"adpsub_rho_{k}"] = E.spearman(v[has_adp], act[has_adp])
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- driver
def main() -> None:
    t0 = time.time()
    panel = build_panel()
    print(f"panel: {len(panel.seasons)} seasons {panel.seasons[0]}-"
          f"{panel.seasons[-1]} (2025 sealed)  [{time.time()-t0:.0f}s]")
    print(f"  ngs_receiving rows {len(panel._ngs)}"
          + (f" {panel._ngs['season'].min()}-{panel._ngs['season'].max()}"
             if len(panel._ngs) else ""))
    print(f"  pbp rush rows {len(panel._rush)}"
          + (f" {panel._rush['season'].min()}-{panel._rush['season'].max()}"
             if len(panel._rush) else ""))
    print(f"  preseason OC rows {len(panel._coord)}"
          + (f" {panel._coord['season'].min()}-{panel._coord['season'].max()}"
             if len(panel._coord) else ""))

    OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict] = []

    # ---- primaries, one per position, on the SAME builder as the arms
    prim: Dict[str, pd.DataFrame] = {}
    prim_players: Dict[str, pd.DataFrame] = {}
    for pos in ("WR", "TE", "RB", "QB"):
        t = time.time()
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=FEAT)
        pl, m = wf.run()
        prim[pos], prim_players[pos] = m, pl
        px = sum(a["n_preseason_proxy_reads"] for a in wf.audit)
        print(f"primary {pos}: {len(pl)} player-seasons, {len(m)} seasons, "
              f"proxy reads {px}  [{time.time()-t:.0f}s]")
        if px:
            raise RuntimeError(f"primary {pos} touched a season-N proxy read")

    # ---- coverage gates, evaluated on the ADP board BEFORE any arm's result
    cov: Dict[Tuple, float] = {}
    for a in ARMS:
        if a.block is None or a.gate_key in cov:
            continue
        col, vals = a.gate_key[2], []
        for s in range(a.first, LAST + 1):
            board = E.adp.load_adp(s, position=a.position)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            u = E.universe_for(panel, s, a.position, extra_ids=extra)
            f = _FEATS[a.feat](panel, u, s)
            if col not in f.columns or not extra:
                continue
            on_board = f["player_id"].isin(extra)
            if on_board.any():
                vals.append(float(f.loc[on_board, col].mean()))
        cov[a.gate_key] = float(np.mean(vals)) if vals else float("nan")
    print("\ncoverage on the ADP board (gate applied BEFORE results are read):")
    for (b, p, c), v in sorted(cov.items()):
        print(f"  {b:5s} {p:3s} {c:18s} {v:.3f}   gate {GATES[b]:.2f}   "
              f"{'PASS' if v >= GATES[b] else 'NO DATA'}")

    # ---- F1
    for a in ARMS:
        c = cov.get(a.gate_key, float("nan")) if a.block else float("nan")
        if a.block and not (c >= GATES[a.block]):
            rows.append(dict(family="F1", idx=a.idx, factor=a.factor, arm=a.arm,
                             position=a.position, e1_comp=a.e1, role=a.role,
                             pair=a.pair, coverage=c, grade="NO DATA"))
            print(f"[{a.idx:2d}/24] {a.position:3s} {a.arm:36s} NO DATA "
                  f"(coverage {c:.3f} < {GATES[a.block]})")
            _flush(rows)
            continue
        t = time.time()
        wf = E.WalkForward(panel=panel, position=a.position, first_target=a.first,
                           last_target=LAST, avail_arm="A",
                           feature_fn=_FEATS[a.feat],
                           allow_preseason_proxy=_PROXY[a.feat], **a.kwargs)
        pl, m = wf.run()
        px = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        e1a = paired(m, prim[a.position], f"mae_{a.e1}")
        e1b = paired(m, prim[a.position], f"adpsub_mae_{a.e1}")
        e2 = paired(m, prim[a.position], "adpsub_rho_model")
        sub = prim[a.position][prim[a.position]["season"] >= a.first]
        base = float(sub[f"mae_{a.e1}"].mean())
        base_b = float(sub[f"adpsub_mae_{a.e1}"].mean())
        rows.append(dict(
            family="F1", idx=a.idx, factor=a.factor, arm=a.arm,
            position=a.position, e1_comp=a.e1, role=a.role, pair=a.pair,
            coverage=c, p=e1a[3],
            d=e1a[0], lo=e1a[1], hi=e1a[2], n=e1a[4],
            pct=100.0 * e1a[0] / base if base else np.nan,
            e1b_d=e1b[0], e1b_n=e1b[4], e1b_pct=100.0 * e1b[0] / base_b if base_b else np.nan,
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            proxy_reads=px, n_players=len(pl), primary_err=base,
            primary_adpsub_err=base_b))
        print(f"[{a.idx:2d}/24] {a.position:3s} {a.arm:36s} "
              f"E1a {e1a[0]:+8.4f} ({rows[-1]['pct']:+5.2f}%) "
              f"[{e1a[1]:+7.4f},{e1a[2]:+7.4f}] p={e1a[3]:.4f} n={e1a[4]}  "
              f"E1b {e1b[0]:+8.4f}  E2 {e2[0]:+.4f}  proxy={px}  "
              f"[{time.time()-t:.0f}s]")
        _flush(rows)

    # ---- F2, from the primaries' own player frames. No refit.
    for pos in ("QB", "RB", "WR", "TE"):
        b = _baseline_rhos(prim_players[pos])
        inc = b[["season", "rho_b2"]].rename(columns={"rho_b2": "rho"})
        for idx, cand, label in ((17, "b2r", "B2r prior points PER GAME PLAYED"),
                                 (21, "b2ra", "B2ra prior ppg x prior games share")):
            k = idx + ["QB", "RB", "WR", "TE"].index(pos)
            cd = b[["season", f"rho_{cand}"]].rename(columns={f"rho_{cand}": "rho"})
            e3 = paired(cd, inc, "rho")
            ad = paired(b[["season", f"adpsub_rho_{cand}"]].rename(
                columns={f"adpsub_rho_{cand}": "rho"}),
                b[["season", "adpsub_rho_b2"]].rename(
                    columns={"adpsub_rho_b2": "rho"}), "rho")
            rows.append(dict(
                family="F2", idx=k, factor="§6.5 baseline #2 respecified",
                arm=label, position=pos, e1_comp="rho_vs_actual", role="baseline",
                d=e3[0], lo=e3[1], hi=e3[2], p=e3[3], n=e3[4],
                e1b_d=ad[0], e1b_n=ad[4],
                primary_err=float(b["rho_b2"].mean()),
                b3_ref=float((b["rho_b3"] - b["rho_b2"]).mean())))
            print(f"[{k:2d}/24] {pos:3s} {label:36s} "
                  f"E3 {e3[0]:+8.4f} [{e3[1]:+7.4f},{e3[2]:+7.4f}] "
                  f"p={e3[3]:.4f} n={e3[4]}  board {ad[0]:+.4f}  "
                  f"(b3-b2 {rows[-1]['b3_ref']:+.4f})")
        b.insert(0, "position", pos)
        b.to_csv(OUT / f"factor_batch3_baselines_{pos}.csv", index=False)
        _flush(rows)

    _grade(pd.DataFrame(rows))
    print(f"\ntotal {time.time()-t0:.0f}s")


def _flush(rows: List[Dict]) -> None:
    pd.DataFrame(rows).to_csv(OUT / "factor_batch3_results.csv", index=False)


def _grade(res: pd.DataFrame) -> None:
    res = res.copy()
    if "grade" not in res.columns:
        res["grade"] = np.nan
    computable = res["grade"].isna() if "grade" in res else pd.Series(True, index=res.index)
    pv = res.loc[computable, "p"].fillna(1.0).tolist()
    pv = pv + [1.0] * max(0, CAMPAIGN_M - len(pv))
    res["bh_10"] = False
    res["bh_05"] = False
    for q in (0.10, 0.05):
        keep = benjamini_hochberg(pv, q)[:int(computable.sum())]
        res.loc[computable, f"bh_{int(q*100):02d}"] = keep

    # VOID rule: a control arm reaching 50% of its treatment's effect voids the
    # treatment's INTERPRETATION (its numbers stand; its meaning does not).
    ctrl = {int(r.pair): abs(r.d) for r in res.itertuples()
            if r.role == "control" and np.isfinite(r.d) and r.pair == r.pair}
    void = {i for i, cd in ctrl.items()
            if any(np.isfinite(r.d) and abs(r.d) > 0
                   and cd >= VOID_RATIO * abs(r.d)
                   for r in res.itertuples() if r.idx == i)}

    def grade(r) -> str:
        if isinstance(getattr(r, "grade", None), str):
            return r.grade
        if not np.isfinite(getattr(r, "d", np.nan)):
            return "NO DATA"
        if r.role == "ablation":
            if r.bh_10 and r.d > 0:
                return "EARNS-ITS-PLACE"
            if r.bh_10 and r.d < 0:
                return "HARMFUL-TO-KEEP"
            return "NO-MEASURABLE-CONTRIBUTION"
        better = r.d < 0
        if r.family == "F2":
            if r.bh_10 and better:
                return "BASELINE-WORSE"       # E3 is rho: lower = worse
            if r.bh_10 and not better:
                return "BASELINE-BETTER"
            return "NULL"
        if r.bh_10 and better:
            if int(r.idx) in void:
                return "VOID - COVERAGE ARTIFACT"
            if not (np.isfinite(r.e1b_d) and r.e1b_d < 0):
                return "BOARD-NEUTRAL"
            return "SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0) \
                else "PROJECTION-ONLY"
        if r.bh_10 and not better:
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

    print("\n" + "=" * 104)
    print(f"RESULTS -- campaign BH m={CAMPAIGN_M} at q=0.10.  F1: E1a component MAE "
          f"(negative = better).  F2: E3 Spearman (positive = better)")
    print("=" * 104)
    for f_, g in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in g.itertuples():
            if r.grade == "NO DATA":
                print(f"  {r.position:3s} {r.arm:36s} NO DATA")
                continue
            print(f"  {r.position:3s} {r.arm:36s} {r.d:+8.4f} "
                  f"[{r.lo:+8.4f},{r.hi:+8.4f}] p={r.p:.4f} "
                  f"bh10={'Y' if r.bh_10 else 'n'}  {r.grade}")
    print("\ngrade counts:")
    print(res["grade"].value_counts().to_string())
    if res["too_good"].any():
        print("\n!! TOO-GOOD TRIGGER FIRED (>2% of primary error) -- escalate "
              "before write-up, per CLAUDE.md §8:")
        print(res.loc[res["too_good"], ["idx", "position", "arm", "pct"]].to_string(index=False))
    res.to_csv(OUT / "factor_batch3_results.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch3_results.csv'}")


if __name__ == "__main__":
    main()
