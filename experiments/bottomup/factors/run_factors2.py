#!/usr/bin/env python
"""Factor batch 2 -- run every arm declared in the pre-commitment.

    .venv/bin/python -m experiments.bottomup.factors.run_factors2

Design: `docs/ranking/factor-batch-2-precommit.md`, committed BEFORE any arm was
fitted. 15 registered tests, BH at q=0.10 on E1b (ADP-board component MAE).
E1a (full universe) is reported for comparability with batch 1 and is NOT the
gate. E2 (ADP-board rho) is the bar and is NOT in the FDR family.

Plus one REFERENCE arm per position -- batch 1's Week-1 depth-chart V1, re-run
unchanged so that "was the harm a proxy artifact?" is answered by a direct
head-to-head rather than by comparing two different harness versions.
"""

from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E             # noqa: E402
from experiments.bottomup.components import pos_model as M            # noqa: E402
from experiments.bottomup.components.pos_data import (                # noqa: E402
    build_panel, unknown_status_codes,
)
from experiments.bottomup.factors.factor_features import (            # noqa: E402
    build_factor_features,
)
from experiments.bottomup.factors.factor_features2 import (           # noqa: E402
    build_factor2_features,
)
from experiments.bottomup.factors.run_factors import (                # noqa: E402
    benjamini_hochberg, paired,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024
OC_COVERAGE_GATE = 0.80          # §5 of the pre-commitment, fixed in advance

FEAT = partial(build_factor2_features, use_proxy=False, use_batch2=False)
FEAT_V1 = partial(build_factor2_features, use_proxy=True, use_batch2=False)
FEAT_B2 = partial(build_factor2_features, use_proxy=False, use_batch2=True)

REC_V = list(M._RECEIVER_VOLUME)
RB_C = list(M._RB_CARRY_VOLUME)
RB_T = list(M._RB_TARGET_VOLUME)

E1_COMPONENT = {"WR": "targets", "TE": "targets", "RB": "carries"}


def _add(cols, *names):
    return list(cols) + [n for n in names if n not in cols]


@dataclass
class Arm:
    factor: str
    arm: str
    position: str
    e1: str
    kwargs: Dict = field(default_factory=dict)
    feat: str = "b2"                 # "base" | "v1" | "b2"
    in_family: bool = True


def _rec(pos: str, *cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {"tpg": _add(REC_V, *cols)}}}


def _rb(carry_cols, tgt_cols) -> Dict:
    return {"model_kwargs": {"volume_cols": {
        "carries_pg": _add(RB_C, *carry_cols), "tpg": _add(RB_T, *tgt_cols)}}}


ARMS: List[Arm] = []

_BLOCKS = [
    # (id, factor label, arm label, receiver cols, RB carry cols, RB target cols)
    ("V2", "#28 vacated opportunity", "V2 departure share (team, REAL ROSTERS)",
     ("vac2_tshare",), ("vac2_cshare",), ("vac2_tshare",)),
    ("V3", "#28 vacated opportunity", "V3 absence share (team, REAL ROSTERS)",
     ("vac3_tshare",), ("vac3_cshare",), ("vac3_tshare",)),
    ("V4", "#28 vacated opportunity", "V4 opportunity ahead of me (PLAYER)",
     ("vac_ahead_t",), ("vac_ahead_c",), ("vac_ahead_t",)),
    ("M1", "#28 vacated opportunity", "M1 this player moved clubs (PLAYER)",
     ("moved_club", "move_known"), ("moved_club", "move_known"),
     ("moved_club", "move_known")),
    ("C1", "#29 coordinator continuity", "C1 new offensive coordinator (PLAYER)",
     ("new_oc", "oc_known"), ("new_oc", "oc_known"), ("new_oc", "oc_known")),
]

for _id, factor, label, rec_cols, rbc, rbt in _BLOCKS:
    for pos in ("WR", "TE"):
        ARMS.append(Arm(factor, label, pos, E1_COMPONENT[pos], _rec(pos, *rec_cols)))
    ARMS.append(Arm(factor, label, "RB", E1_COMPONENT["RB"], _rb(rbc, rbt)))

# ---- reference arms, OUTSIDE the family, not re-graded
for pos in ("WR", "TE"):
    ARMS.append(Arm("#28 vacated opportunity", "V1 depth-chart proxy (BATCH 1 REFERENCE)",
                    pos, E1_COMPONENT[pos], _rec(pos, "vac_tshare"),
                    feat="v1", in_family=False))
ARMS.append(Arm("#28 vacated opportunity", "V1 depth-chart proxy (BATCH 1 REFERENCE)",
                "RB", E1_COMPONENT["RB"],
                _rb(("vac_cshare",), ("vac_tshare",)), feat="v1", in_family=False))


def _feature_fn(kind: str):
    return {"base": FEAT, "v1": FEAT_V1, "b2": FEAT_B2}[kind]


def main() -> None:
    panel = build_panel()
    print(f"panel: {len(panel.seasons)} seasons, {panel.seasons[0]}-"
          f"{panel.seasons[-1]} (2025 sealed)")
    print(f"preseason rosters: {len(panel._roster)} rows "
          f"{panel._roster['season'].min()}-{panel._roster['season'].max()}")
    unk = unknown_status_codes(panel._roster)
    print(f"unclassified roster status codes: "
          f"{unk.to_dict() if len(unk) else 'none'}")
    print(f"preseason OC rows: {len(panel._coord)}"
          + (f" {panel._coord['season'].min()}-{panel._coord['season'].max()}"
             if len(panel._coord) else ""))

    # ---- primaries, one per position, on the SAME builder as the arms
    prim: Dict[str, pd.DataFrame] = {}
    for pos in ("WR", "TE", "RB"):
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=FEAT)
        pl, m = wf.run()
        prim[pos] = m
        px = sum(a["n_preseason_proxy_reads"] for a in wf.audit)
        print(f"primary {pos}: {len(pl)} player-seasons, {len(m)} seasons, "
              f"proxy reads {px}")
        if px:
            raise RuntimeError(f"primary {pos} touched a season-N proxy read")

    # ---- C1 coverage gate, evaluated BEFORE C1's result is looked at
    cov, cov_adp = {}, {}
    for pos in ("WR", "TE", "RB"):
        vals, vals_adp = [], []
        for s in range(FIRST, LAST + 1):
            # same universe construction the arms use, board extras included, so
            # the gate is measured on the population it gates
            board = E.adp.load_adp(s, position=pos)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            u = E.universe_for(panel, s, pos, extra_ids=extra)
            f = FEAT_B2(panel, u, s)
            vals.append(float(f["oc_known"].mean()))
            if extra:
                on_board = f["player_id"].isin(extra)
                if on_board.any():
                    vals_adp.append(float(f.loc[on_board, "oc_known"].mean()))
        cov[pos] = float(np.mean(vals))
        cov_adp[pos] = float(np.mean(vals_adp)) if vals_adp else float("nan")
    print("C1 coverage on the ADP board only: "
          + ", ".join(f"{k} {v:.3f}" for k, v in cov_adp.items()))
    print("\nC1 coverage (mean oc_known across 11 seasons): "
          + ", ".join(f"{k} {v:.3f}" for k, v in cov.items())
          + f"   gate = {OC_COVERAGE_GATE}")

    rows = []
    for i, a in enumerate(ARMS, start=1):
        gated_out = (a.arm.startswith("C1") and cov[a.position] < OC_COVERAGE_GATE)
        if gated_out:
            rows.append(dict(idx=i, factor=a.factor, arm=a.arm, position=a.position,
                             e1_comp=a.e1, in_family=a.in_family, grade="NO DATA",
                             oc_coverage=cov[a.position]))
            print(f"[{i:2d}/{len(ARMS)}] {a.position:3s} {a.arm:44s} "
                  f"NO DATA (oc_known {cov[a.position]:.3f} < {OC_COVERAGE_GATE})")
            continue
        wf = E.WalkForward(panel=panel, position=a.position, first_target=FIRST,
                           last_target=LAST, avail_arm="A",
                           feature_fn=_feature_fn(a.feat),
                           allow_preseason_proxy=(a.feat != "base"), **a.kwargs)
        pl, m = wf.run()
        px = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        e1b = paired(m, prim[a.position], f"adpsub_mae_{a.e1}")
        e1a = paired(m, prim[a.position], f"mae_{a.e1}")
        e2 = paired(m, prim[a.position], "adpsub_rho_model")
        base = float(prim[a.position][f"adpsub_mae_{a.e1}"].mean())
        rows.append(dict(
            idx=i, factor=a.factor, arm=a.arm, position=a.position, e1_comp=a.e1,
            in_family=a.in_family,
            e1b_d=e1b[0], e1b_lo=e1b[1], e1b_hi=e1b[2], e1b_p=e1b[3], e1b_n=e1b[4],
            e1b_pct=100.0 * e1b[0] / base if base else np.nan,
            e1a_d=e1a[0], e1a_lo=e1a[1], e1a_hi=e1a[2], e1a_p=e1a[3],
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            proxy_reads=px, n_players=len(pl), primary_adpsub_mae=base,
            oc_coverage=cov[a.position]))
        tag = "" if a.in_family else "  [REFERENCE]"
        print(f"[{i:2d}/{len(ARMS)}] {a.position:3s} {a.arm:44s} "
              f"E1b {e1b[0]:+8.4f} ({rows[-1]['e1b_pct']:+5.2f}%) p={e1b[3]:.3f}  "
              f"E1a {e1a[0]:+8.4f}  E2 {e2[0]:+.4f}  proxy={px}{tag}")

    res = pd.DataFrame(rows)
    fam = res["in_family"] & res["grade"].isna() if "grade" in res.columns \
        else res["in_family"]
    # BH denominator is 15 regardless of how many arms were computable (§5)
    m_family = int((res["in_family"]).sum())
    pv = res.loc[fam, "e1b_p"].fillna(1.0).tolist()
    pv = pv + [1.0] * (m_family - len(pv))
    for q in (0.10, 0.05):
        keep = benjamini_hochberg(pv, q)[:int(fam.sum())]
        res.loc[fam, f"bh_{int(q*100):02d}"] = keep

    def grade(r) -> str:
        if isinstance(getattr(r, "grade", None), str):
            return r.grade
        if not r.in_family:
            return "REFERENCE"
        if not np.isfinite(r.e1b_d):
            return "NO DATA"
        better = r.e1b_d < 0
        if bool(r.bh_10) and better:
            return "SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0) \
                else "PROJECTION-ONLY"
        if bool(r.bh_10) and not better:
            return "HARMFUL"
        if r.e1b_lo < 0 and r.e1b_hi < 0:
            return "MARGINAL"
        if r.e1b_lo > 0 and r.e1b_hi > 0:
            return "MARGINAL-HARMFUL"
        return "NULL"

    res["grade"] = [grade(r) for r in res.itertuples()]

    print("\n" + "=" * 96)
    print(f"RESULTS -- E1b = ADP-BOARD component MAE (negative = better), "
          f"family m={m_family}, BH q=0.10")
    print("=" * 96)
    for f_, g in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in g.itertuples():
            if r.grade == "NO DATA":
                print(f"  {r.position:3s} {r.arm:44s} NO DATA")
                continue
            print(f"  {r.position:3s} {r.arm:44s} "
                  f"E1b {r.e1b_d:+8.4f} [{r.e1b_lo:+8.4f},{r.e1b_hi:+8.4f}] "
                  f"p={r.e1b_p:.4f} bh10={'Y' if r.bh_10 else 'n'}  "
                  f"E2 {r.e2_d:+.4f}  {r.grade}")

    # ---- the headline comparison: V2 (real rosters) - V1 (depth chart proxy)
    print("\n" + "=" * 96)
    print("HEADLINE -- was batch 1's #28 harm a proxy artifact?  V2 vs V1, same harness")
    print("=" * 96)
    for pos in ("WR", "TE", "RB"):
        v1 = res[(res.position == pos) & res.arm.str.startswith("V1")]
        v2 = res[(res.position == pos) & res.arm.str.startswith("V2")]
        if len(v1) and len(v2):
            print(f"  {pos:3s}  V1 depth-chart proxy E1b {v1.e1b_d.iloc[0]:+8.4f}"
                  f" | E1a {v1.e1a_d.iloc[0]:+8.4f}"
                  f"   ->   V2 real rosters E1b {v2.e1b_d.iloc[0]:+8.4f}"
                  f" | E1a {v2.e1a_d.iloc[0]:+8.4f}")

    print("\ngrade counts (family only):")
    print(res.loc[res.in_family, "grade"].value_counts().to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "factor_batch2_results.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch2_results.csv'}")


if __name__ == "__main__":
    main()
