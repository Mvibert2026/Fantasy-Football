#!/usr/bin/env python
"""Batch C2 runner — more factors, plus the RB high-carry breakpoint, against
ranking v2.

    python3 -m experiments.bottomup.v2.run_c2 --arms A1,A2
    python3 -m experiments.bottomup.v2.run_c2 --regrade

Registration: `docs/ranking/factor-campaign-manifest/batch-C2.md`, committed
at `ee87b53` before any of this ran.

GRADING IS SUSPENDED. C1's registered inclusion rule handed a BH-robust WIN
to seeded noise (false-positive rate measured at 9.6% of cells against a
nominal 2.5%; `docs/ranking/batch-C1-results.md`). This runner therefore
computes and records the CI-level verdict (WIN/HARM/NULL, estimator-
independent) and a placebo-percentile comparison per cell, but NEVER emits
an INCLUDE/EXCLUDE call. `factor_verdict()` always reports `PENDING-RULE`.
Re-grading once `strategist` lands a replacement rule is mechanical: the
per-season deltas on disk do not change, only the decision function applied
to them does.

WRITTEN TO BE INTERRUPTED, same discipline as `run_c1.py`: every arm appends
its cells and its computed contrasts to CSVs on disk the moment it finishes.

THE CONTROL IS PINNED AND MATCHED, same discipline as C1. Each arm is
differenced against a control run at the SAME `first_feature_season` and the
SAME target span (CTRL-A2 / CTRL-D below) so a late-starting source is never
confounded with a shorter training window.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E          # noqa: E402
from experiments.bottomup.components.pos_eval import WalkForward    # noqa: E402
from experiments.bottomup.v2.factors_c2 import (                    # noqa: E402
    COVERAGE_FLOOR, FACTOR_BLOCKS, KNOWN_COL, PAIRED_CONTROL,
    build_features_c2, volume_cols_for)
from experiments.bottomup.v2.weekshape import build_v2_panel        # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
CELLS_CSV = OUT / "factor_c2_cells.csv"
CONTRASTS_CSV = OUT / "factor_c2_contrasts.csv"

HOLDOUT_SEASON = 2025
BOOT_REPS, BOOT_SEED = 4000, 20260801  # unchanged from C1 -- same estimator

#: registration-time multiplicity note (batch-C2.md): m_b = 29,
#: M_campaign = max(130 + 29, 80) = 159. NOT applied in this run -- no BH is
#: computed while the WIN rule it would feed is suspended. Kept here as a
#: constant so the number the manifest recorded is not silently lost.
M_CAMPAIGN_PENDING = 159
Q_FDR = 0.10

#: same numerical-hygiene snap as C1 -- deltas below this are float64 noise
#: from two rhos taking different code paths, never a model difference.
DELTA_EPS = 1e-9

#: registered in batch-C2: {control: (first_feature_season, first_target, last)}
CONTROLS: Dict[str, Tuple[int, int, int]] = {
    "CTRL-A2": (2012, 2018, 2024),
    "CTRL-D": (2018, 2021, 2024),
}

#: registered in batch-C2: arm -> (control, positions)
ARMS: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "A1": ("CTRL-A2", ("WR", "TE")),
    "A2": ("CTRL-A2", ("RB",)),
    "A3": ("CTRL-A2", ("RB",)),
    "A4": ("CTRL-A2", ("RB", "WR", "TE")),
    "A5": ("CTRL-D", ("QB", "RB", "WR", "TE")),
    "B1": ("CTRL-A2", ("RB",)),
    "F0": ("CTRL-A2", ("QB", "RB", "WR", "TE")),
    "F0D": ("CTRL-D", ("QB", "RB", "WR", "TE")),
}

FACTOR_NAME = {
    "A1": "WOPR, recency-weighted (WR/TE)",
    "A2": "YAC per reception, EB-shrunk (RB) -- batch-7 block, reused",
    "A3": "receiving share of RB's own points (RB) -- batch-7 block, reused",
    "A4": "late-season role trajectory (RB/WR/TE) -- batch-7 block, reused",
    "A5": "implied team total, lagged (QB/RB/WR/TE)",
    "B1": "RB high-carry-season breakpoint (350/375/400 hinge spline)",
    "F0": "PLACEBO (seeded N(0,1) noise) at CTRL-A2",
    "F0D": "PLACEBO (seeded N(0,1) noise) at CTRL-D",
}

for _k, _f in PAIRED_CONTROL.items():
    ARMS[_k] = ARMS[_f]
    FACTOR_NAME[_k] = f"CONTROL -- {KNOWN_COL[_f]} indicator alone (pairs {_f})"
del _k, _f

# carry the C2 factor columns into the output frame so coverage is measurable
# on the graded population. Additive module-level patch, same pattern C1 used.
E._CARRY = E._CARRY + [c for c in (
    "placebo_noise", "wopr_w", "yac_per_rec_w", "yac_known", "recpts_share_w",
    "recpts_known", "late_ratio_w", "late_known", "itt_w", "itt_known",
    "carry_hinge_350", "carry_hinge_375", "carry_hinge_400", "carries_1"
) if c not in E._CARRY]


# --------------------------------------------------------------------- running
def _feature_fn(blocks: Tuple[str, ...], position: Optional[str]):
    def fn(panel, universe, target_season):
        return build_features_c2(panel, universe, target_season, blocks=blocks,
                                 position=position)
    return fn


def run_one(panel, label: str, factor: Optional[str], positions: Tuple[str, ...],
            first_feature: int, first_target: int, last_target: int
            ) -> pd.DataFrame:
    """One arm or one control, all its positions, full walk-forward."""
    blocks = FACTOR_BLOCKS[factor] if factor else ()
    frames = []
    for pos in positions:
        wf = WalkForward(
            panel=panel, position=pos, first_target=first_target,
            last_target=last_target, min_train_seasons=2, avail_arm="A",
            calibrate_bonus=True, first_feature_season=first_feature,
            feature_fn=_feature_fn(blocks, pos),
            model_kwargs=({"volume_cols": volume_cols_for(factor, pos)}
                          if factor else {}),
            allow_preseason_proxy=False)
        players, _ = wf.run()
        aud = pd.DataFrame(wf.audit)
        assert (aud.max_feature_cutoff < aud.season).all(), f"{label}/{pos} feature leak"
        assert (aud.max_outcome_season < aud.season).all(), f"{label}/{pos} outcome leak"
        assert (aud.n_outcome_reads_at_target == 0).all(), f"{label}/{pos} target read"
        assert (aud.n_preseason_proxy_reads == 0).all(), f"{label}/{pos} proxy read"
        assert players["season"].max() < HOLDOUT_SEASON, "HOLDOUT TOUCHED"
        players["position"] = pos
        players["run"] = label
        frames.append(players)
    return pd.concat(frames, ignore_index=True)


def cell_metrics(full: pd.DataFrame, label: str, factor: Optional[str]
                 ) -> pd.DataFrame:
    """Per (position, season): the ADR-069 absolute steering metric, cell
    size, and the factor's coverage (or, for B1, its threshold-clearance
    rate -- reported, not gated)."""
    known = KNOWN_COL.get(factor) if factor else None
    rows = []
    for (pos, season), g in full.groupby(["position", "season"]):
        vet = g[g["entry"] == "veteran"]
        sub = vet[vet["average_pick"].notna()]
        row: Dict = {"run": label, "position": pos, "season": int(season),
                     "n_board_vet": len(sub), "n_vet": len(vet)}
        if len(sub) >= 10:
            row["rho_points"] = E.spearman(
                sub["proj_points"].to_numpy(dtype=float),
                sub["points"].to_numpy(dtype=float))
        if len(vet) >= 10:
            row["rho_points_fullvet"] = E.spearman(
                vet["proj_points"].to_numpy(dtype=float),
                vet["points"].to_numpy(dtype=float))
        if known and known in sub.columns and len(sub):
            row["coverage"] = float(
                pd.to_numeric(sub[known], errors="coerce").fillna(0.0).mean())
        if factor == "B1" and "carries_1" in sub.columns and len(sub):
            c1 = pd.to_numeric(sub["carries_1"], errors="coerce")
            row["n_ge350"] = int((c1 >= 350).sum())
        rows.append(row)
    return pd.DataFrame(rows)


# -------------------------------------------------------------------- grading
def boot_diff(joined: pd.DataFrame) -> Tuple[float, float, float, int, float]:
    """Paired season-block bootstrap on the per-season deltas -- identical
    estimator, reps, and seed to C1. NOT a second instrument."""
    sub = joined[["a", "b"]].dropna()
    diffs = np.array((sub["a"] - sub["b"]).to_numpy(dtype=float), copy=True)
    diffs[np.abs(diffs) < DELTA_EPS] = 0.0
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


def contrast_rows(cells: pd.DataFrame, factor: str) -> List[Dict]:
    ctrl, positions = ARMS[factor]
    arm_cells = cells[cells["run"] == factor]
    ctl_cells = cells[cells["run"] == ctrl]
    rows = []
    for pos in positions:
        a = arm_cells[arm_cells.position == pos].set_index("season")[["rho_points"]] \
            .rename(columns={"rho_points": "a"})
        b = ctl_cells[ctl_cells.position == pos].set_index("season")[["rho_points"]] \
            .rename(columns={"rho_points": "b"})
        j = a.join(b, how="inner")
        d, lo, hi, n, p = boot_diff(j)
        cov = np.nan
        if "coverage" in arm_cells.columns:
            c = arm_cells.loc[arm_cells.position == pos, "coverage"]
            cov = float(c.mean()) if c.notna().any() else np.nan
        n_ge350 = np.nan
        if "n_ge350" in arm_cells.columns:
            v = arm_cells.loc[arm_cells.position == pos, "n_ge350"]
            n_ge350 = float(v.sum()) if v.notna().any() else np.nan
        rows.append(dict(
            factor=factor, name=FACTOR_NAME[factor], control=ctrl, position=pos,
            delta=d, lo=lo, hi=hi, n_seasons=n, p=p, coverage=cov,
            n_ge350_carries=n_ge350,
            ctrl_mean_rho=float(j["b"].mean()) if len(j) else np.nan,
            arm_mean_rho=float(j["a"].mean()) if len(j) else np.nan,
            games_arm="G0"))
    return rows


def _ci_verdict(r) -> str:
    if not np.isfinite(r["delta"]):
        return "NO DATA"
    if np.isfinite(r["coverage"]) and r["coverage"] < COVERAGE_FLOOR:
        return "NO DATA (coverage)"
    if abs(r["delta"]) < DELTA_EPS:
        return "NULL (no change)"
    if r["lo"] > DELTA_EPS:
        return "WIN"
    if r["hi"] < -DELTA_EPS:
        return "HARM"
    return "NULL"


def _placebo_lookup(df: pd.DataFrame) -> Dict[Tuple[str, str], float]:
    """(position, control) -> this batch's own placebo delta at that cell,
    for the per-row 'vs placebo' comparison. F0 covers CTRL-A2, F0D covers
    CTRL-D."""
    out = {}
    for pf, ctrl in (("F0", "CTRL-A2"), ("F0D", "CTRL-D")):
        sub = df[df["factor"] == pf]
        for _, r in sub.iterrows():
            out[(r["position"], ctrl)] = r["delta"]
    return out


def grade(df: pd.DataFrame) -> pd.DataFrame:
    """CI verdict + this batch's own placebo comparison. NO BH, NO
    INCLUDE/EXCLUDE -- grading is suspended (batch-C2.md). Kept as a
    separate, clearly-labelled column (`bh_reject_campaign`) fixed to False
    throughout, so the CSV schema matches C1's for a future mechanical
    `--regrade` once the replacement rule lands, without implying a rule
    was applied here."""
    df = df.copy()
    df["verdict"] = df.apply(_ci_verdict, axis=1)
    df["bh_reject_campaign"] = False  # not computed this batch -- see above

    placebo = _placebo_lookup(df)
    def vs_placebo(r):
        if r["factor"] in ("F0", "F0D"):
            return "n/a (is the placebo)"
        key = (r["position"], r["control"])
        pd_delta = placebo.get(key)
        if pd_delta is None or not np.isfinite(pd_delta) or not np.isfinite(r["delta"]):
            return "no placebo cell"
        if r["delta"] > pd_delta:
            return f"clears (placebo {pd_delta:+.4f})"
        return f"inside/below (placebo {pd_delta:+.4f})"
    df["vs_placebo"] = df.apply(vs_placebo, axis=1)

    # Amendment-1-style VOID note: recorded, not acted on (grading suspended).
    treat_of = PAIRED_CONTROL
    ctrl_win = {(r["factor"], r["position"])
                for _, r in df.iterrows() if r["verdict"] == "WIN"}
    for i, r in df.iterrows():
        if r["verdict"] != "WIN":
            continue
        kname = f"{r['factor']}k"
        if kname not in treat_of:
            continue
        if (kname, r["position"]) in ctrl_win:
            df.at[i, "verdict"] = "WIN (VOID: control wins)"
    return df


def factor_verdict(g: pd.DataFrame) -> str:
    """Grading is suspended this batch (batch-C2.md). This ALWAYS returns
    PENDING-RULE regardless of what the CI verdicts say -- the CI-level
    column is informative and estimator-independent, but it is not fed to
    any INCLUDE/EXCLUDE decision here."""
    del g
    return "PENDING-RULE"


# ----------------------------------------------------------------------- main
def read_contrasts() -> pd.DataFrame:
    return pd.read_csv(CONTRASTS_CSV, keep_default_na=False, na_values=[""])


def recontrast(cells: pd.DataFrame) -> pd.DataFrame:
    runs = set(cells["run"].unique())
    rows: List[Dict] = []
    for f in ARMS:
        if f in runs:
            rows.extend(contrast_rows(cells, f))
    return grade(pd.DataFrame(rows))


def _append(path: Path, new: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    old = (read_contrasts() if path == CONTRASTS_CSV else pd.read_csv(path)) \
        if path.exists() else pd.DataFrame()
    if len(old):
        merged = pd.concat([old, new], ignore_index=True)
        merged = merged.drop_duplicates(subset=keys, keep="last")
    else:
        merged = new
    merged.to_csv(path, index=False)
    return merged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="", help="comma list, e.g. A1,A2")
    ap.add_argument("--regrade", action="store_true",
                    help="recompute CI verdicts + placebo comparison over "
                         "accumulated contrasts")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if args.regrade and not args.arms:
        df = recontrast(pd.read_csv(CELLS_CSV))
        df.to_csv(CONTRASTS_CSV, index=False)
        _report(df)
        return

    arms = [a for a in args.arms.split(",") if a]
    for a in arms:
        if a not in ARMS:
            raise SystemExit(f"unknown arm {a!r}; registered: {sorted(ARMS)}")

    print(f"HOLDOUT {HOLDOUT_SEASON}: sealed, never read. Panel gates enforce.")
    print("GRADING SUSPENDED this batch -- see docs/ranking/batch-C2-results.md")
    panel = build_v2_panel()
    print(f"panel {panel.seasons[0]}-{panel.seasons[-1]}, "
          f"feature_gate={panel.feature_gate}, outcome_gate={panel.outcome_gate}",
          flush=True)

    cells = pd.read_csv(CELLS_CSV) if CELLS_CSV.exists() else pd.DataFrame()

    for factor in arms:
        ctrl, positions = ARMS[factor]
        ff, ft, lt = CONTROLS[ctrl]

        have = set()
        if len(cells):
            have = set(cells.loc[cells["run"] == ctrl, "position"].unique())
        need = tuple(p for p in positions if p not in have)
        if need:
            print(f"\n### control {ctrl} (ff={ff}, targets {ft}-{lt}) "
                  f"positions {need}", flush=True)
            c = run_one(panel, ctrl, None, need, ff, ft, lt)
            cells = _append(CELLS_CSV, cell_metrics(c, ctrl, None),
                            ["run", "position", "season"])

        print(f"\n### arm {factor} -- {FACTOR_NAME[factor]} "
              f"(vs {ctrl}, positions {positions})", flush=True)
        full = run_one(panel, factor, factor, positions, ff, ft, lt)
        cells = _append(CELLS_CSV, cell_metrics(full, factor, factor),
                        ["run", "position", "season"])

        allc = recontrast(cells)
        allc.to_csv(CONTRASTS_CSV, index=False)
        _report(allc[allc["factor"] == factor])
        print(f"[recorded] {CELLS_CSV.name} + {CONTRASTS_CSV.name}", flush=True)

    _report(recontrast(pd.read_csv(CELLS_CSV)))


def _report(df: pd.DataFrame) -> None:
    cols = ["factor", "position", "control", "n_seasons", "coverage",
            "ctrl_mean_rho", "arm_mean_rho", "delta", "lo", "hi", "p",
            "verdict", "vs_placebo"]
    print(f"\n{'='*100}\nBATCH-C2 (grading SUSPENDED; control = v2 games arm G0; "
          f"M_campaign pending = {M_CAMPAIGN_PENDING})\n{'='*100}")
    print(df[cols].round(4).to_string(index=False))
    print("\nfactor status (grading suspended, always PENDING-RULE):")
    for f, g in df.groupby("factor"):
        print(f"  {f}  {factor_verdict(g):14s}  {FACTOR_NAME[f]}")


if __name__ == "__main__":
    main()
