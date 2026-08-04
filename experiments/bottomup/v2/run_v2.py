#!/usr/bin/env python
"""Ranking v2 walk-forward runner — batch-B1 arms G0 / G1 / G2.

    python3 -m experiments.bottomup.v2.run_v2 [--positions QB,RB,WR,TE]
        [--first-target 2018] [--last-target 2024] [--arms G0,G1,G2]

Registration: docs/ranking/factor-campaign-manifest/batch-B1.md (committed
before any of this ran). Config: experiments/bottomup/ranking_versions/v2.json.

WHAT IS DIFFERENT FROM ranking_v1.py, BY DESIGN (ADR-069):
- The ordering path is `proj_points` computed from stat lines under the league
  scoring config. No consensus rank, no ADP rank, no rank-space assembly, no
  rookie pinning. ADP appears in exactly one role: defining the evaluation
  SUBSET (survivorship guard), the standing M-panel convention.
- No crowd baseline is computed anywhere. The steering metric is absolute
  Spearman against realised points, arm vs arm. The §6.5 four-baseline gate is
  a release gate run later, by someone other than fable.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import adp_baseline as adp        # noqa: E402
from experiments.bottomup.components import pos_eval as E              # noqa: E402
from experiments.bottomup.components.pos_eval import WalkForward       # noqa: E402
from experiments.bottomup.v2.features_v2 import (                      # noqa: E402
    build_features_v2, build_features_v2_proxy)
from experiments.bottomup.v2.games_model import naive_persistence_games  # noqa: E402
from experiments.bottomup.v2.model_v2 import make_model                # noqa: E402
from experiments.bottomup.v2.weekshape import build_v2_panel           # noqa: E402

# Carry the v2 feature columns into the output frame for diagnostics. Additive
# module-level patch, deliberately NOT an edit to the shared harness while
# another agent runs against it; run()'s `carry` list reads this module global
# at call time.
E._CARRY = E._CARRY + [c for c in (
    "late4_share_1", "endgap_share_1", "played_thru_1", "chronic_missed_share",
    "miss1_x_endgap", "miss1_x_resolved", "wk1_available", "wk1_reserve")
    if c not in E._CARRY]

OUT = _REPO / "experiments" / "bottomup" / "results"
HOLDOUT_SEASON = 2025
BOOT_REPS, BOOT_SEED = 4000, 20260801
#: campaign multiplicity at grading time: Σ m_b = 56 (batches 5/6/7) + 16 (M2,
#: incl. Amendment 1) + 20 (B1 incl. Amendment 1) = 92 > floor 80. Per the
#: manifest README the batch ranks its own p-values against the campaign M.
M_CAMPAIGN = 92
Q_FDR = 0.10


@dataclass
class V2WalkForward(WalkForward):
    arm: str = "G1"

    def _make_model(self):
        return make_model(self.position, self.arm, **self.model_kwargs)


def run_arm(panel, arm: str, positions: List[str], first_target: int,
            last_target: int) -> pd.DataFrame:
    frames = []
    for pos in positions:
        wf = V2WalkForward(
            panel=panel, position=pos, first_target=first_target,
            last_target=last_target, min_train_seasons=2,
            avail_arm="A", calibrate_bonus=True, arm=arm,
            feature_fn=(build_features_v2_proxy if arm == "G2a"
                        else build_features_v2),
            allow_preseason_proxy=(arm == "G2a"))
        players, _ = wf.run()
        aud = pd.DataFrame(wf.audit)
        assert (aud.max_feature_cutoff < aud.season).all(), f"{arm}/{pos} feature leak"
        assert (aud.max_outcome_season < aud.season).all(), f"{arm}/{pos} outcome leak"
        assert (aud.n_outcome_reads_at_target == 0).all(), f"{arm}/{pos} target read"
        if arm != "G2a":
            assert (aud.n_preseason_proxy_reads == 0).all(), f"{arm}/{pos} proxy read"
        assert players["season"].max() < HOLDOUT_SEASON, "HOLDOUT TOUCHED"
        players["position"] = pos
        players["arm"] = arm
        frames.append(players)
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------ metrics
def cell_metrics(full: pd.DataFrame, arm: str) -> pd.DataFrame:
    """Per (position, season): absolute quality + games-component metrics on the
    graded population (M-panel veterans) plus descriptive extras."""
    rows = []
    for (pos, season), g in full.groupby(["position", "season"]):
        vet = g[g["entry"] == "veteran"]
        sub = vet[vet["average_pick"].notna()]
        row: Dict = {"arm": arm, "position": pos, "season": int(season),
                     "n_board_vet": len(sub), "n_vet": len(vet),
                     "n_rookie": int((g["entry"] == "rookie").sum())}
        if len(sub) >= 10:
            gm = sub["games"].to_numpy(dtype=float)
            pg = sub["proj_games"].to_numpy(dtype=float)
            gn = naive_persistence_games(sub)
            pts = sub["points"].to_numpy(dtype=float)
            ppts = sub["proj_points"].to_numpy(dtype=float)
            row["rho_games"] = E.spearman(pg, gm)
            row["rho_games_naive"] = E.spearman(gn, gm)
            row["mae_games"] = float(np.mean(np.abs(pg - gm)))
            row["mae_games_naive"] = float(np.mean(np.abs(gn - gm)))
            row["rho_points"] = E.spearman(ppts, pts)
            # descriptive: the returning-absent (Burrow) class
            ra = E.returning_absent(sub)
            row["n_returning"] = int(ra.sum())
            if ra.sum() >= 5:
                row["mae_games_returning"] = float(
                    np.mean(np.abs(pg[ra.to_numpy()] - gm[ra.to_numpy()])))
                row["bias_games_returning"] = float(
                    np.mean(pg[ra.to_numpy()] - gm[ra.to_numpy()]))
        # descriptive: full veteran universe (no ADP filter)
        if len(vet) >= 10:
            row["rho_points_fullvet"] = E.spearman(
                vet["proj_points"].to_numpy(dtype=float),
                vet["points"].to_numpy(dtype=float))
        rows.append(row)
    return pd.DataFrame(rows)


def boot_diff(m: pd.DataFrame, a: str, b: str):
    sub = m[[a, b]].dropna()
    diffs = (sub[a] - sub[b]).to_numpy(dtype=float)
    n = len(diffs)
    if n == 0:
        return np.nan, np.nan, np.nan, 0, np.nan
    rng = np.random.default_rng(BOOT_SEED)
    boot = np.array([np.mean(rng.choice(diffs, size=n, replace=True))
                     for _ in range(BOOT_REPS)])
    p = 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean()))
    return (float(diffs.mean()), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), n,
            min(1.0, max(p, 1.0 / BOOT_REPS)))


def contrasts(metrics: Dict[str, pd.DataFrame], positions: List[str]
              ) -> pd.DataFrame:
    """The 12 graded cells of batch-B1, exactly as registered."""
    rows = []
    specs = [
        ("C-A", "G1", "rho_games", "G1", "rho_games_naive", "games ordering: G1 - naive"),
        ("C-B", "G1", "rho_points", "G0", "rho_points", "absolute quality: G1 - G0"),
        ("C-A'", "G1a", "rho_games", "G1a", "rho_games_naive", "games ordering: G1a - naive"),
        ("C-B'", "G1a", "rho_points", "G0", "rho_points", "absolute quality: G1a - G0"),
        ("C-C", "G2a", "rho_points", "G1a", "rho_points", "absolute quality: G2a - G1a"),
    ]
    for cid, arm_a, col_a, arm_b, col_b, label in specs:
        if arm_a not in metrics or arm_b not in metrics:
            continue
        for pos in positions:
            ma = metrics[arm_a]
            mb = metrics[arm_b]
            a = ma[ma.position == pos].set_index("season")[[col_a]] \
                .rename(columns={col_a: "a"})
            b = mb[mb.position == pos].set_index("season")[[col_b]] \
                .rename(columns={col_b: "b"})
            j = a.join(b, how="inner")
            d, lo, hi, n, p = boot_diff(j, "a", "b")
            rows.append(dict(contrast=cid, label=label, position=pos, delta=d,
                             lo=lo, hi=hi, n=n, p=p))
    df = pd.DataFrame(rows)
    # BH at the campaign denominator: this batch's p-values ranked among
    # themselves against M_CAMPAIGN (the implemented, conservative convention
    # recorded in M2-4).
    ok = df["p"].notna()
    df["bh_reject_campaign"] = False
    if ok.any():
        ps = df.loc[ok, "p"].to_numpy()
        order = np.argsort(ps)
        keep = np.zeros(len(ps), dtype=bool)
        thresh = -1
        for rank, i in enumerate(order, start=1):
            if ps[i] <= Q_FDR * rank / M_CAMPAIGN:
                thresh = rank
        if thresh > 0:
            keep[order[:thresh]] = True
        df.loc[ok, "bh_reject_campaign"] = keep
    def verdict(r):
        if not np.isfinite(r["delta"]):
            return "NO DATA"
        if r["lo"] > 0:
            return "WIN"
        if r["hi"] < 0:
            return "HARM"
        return "NULL"
    df["verdict"] = df.apply(verdict, axis=1)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--positions", default="QB,RB,WR,TE")
    ap.add_argument("--first-target", type=int, default=2018)
    ap.add_argument("--last-target", type=int, default=2024)
    ap.add_argument("--arms", default="G0,G1,G2")
    args = ap.parse_args()
    positions = args.positions.split(",")
    arms = args.arms.split(",")

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"HOLDOUT {HOLDOUT_SEASON}: sealed, never read. Panel gates enforce.")
    panel = build_v2_panel()
    print(f"panel seasons {panel.seasons[0]}–{panel.seasons[-1]}, "
          f"feature_gate={panel.feature_gate}, outcome_gate={panel.outcome_gate}")

    metrics: Dict[str, pd.DataFrame] = {}
    for arm in arms:
        print(f"\n{'#'*80}\n# arm {arm}\n{'#'*80}", flush=True)
        full = run_arm(panel, arm, positions, args.first_target, args.last_target)
        full.to_csv(OUT / f"ranking_v2_{arm}_players.csv", index=False)
        m = cell_metrics(full, arm)
        metrics[arm] = m
        m.to_csv(OUT / f"ranking_v2_{arm}_cells.csv", index=False)
        lv = m.groupby("position")[
            [c for c in ("rho_games", "rho_games_naive", "mae_games",
                         "mae_games_naive", "rho_points", "rho_points_fullvet")
             if c in m.columns]].mean()
        print(lv.round(4).to_string(), flush=True)

    if len(metrics) > 1:
        c = contrasts(metrics, positions)
        c.to_csv(OUT / "ranking_v2_contrasts.csv", index=False)
        print(f"\n{'='*80}\nBATCH-B1 GRADED CELLS (BH at campaign M={M_CAMPAIGN}, "
              f"q={Q_FDR})\n{'='*80}")
        print(c.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
