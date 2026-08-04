#!/usr/bin/env python
"""Batch C1 runner — the factor inclusion test against ranking v2.

    .venv/bin/python -m experiments.bottomup.v2.run_c1 --arms F0,F1
    .venv/bin/python -m experiments.bottomup.v2.run_c1 --regrade

Registration: `docs/ranking/factor-campaign-manifest/batch-C1.md`, committed at
29410c1 before any of this ran.

WRITTEN TO BE INTERRUPTED. Every arm appends its cells and its graded contrasts
to CSVs on disk the moment it finishes, and `--regrade` recomputes the BH column
over whatever has accumulated. A run that dies after three arms leaves three
graded arms, not nothing.

THE CONTROL IS PINNED AND MATCHED. v2's registered default games arm is G0, and
plain `WalkForward` with empty `model_kwargs` IS G0 (`model_v2.make_model`
returns the unmodified incumbent for that arm), so no games-arm plumbing is
needed here. Each arm is differenced against a control run at the SAME
`first_feature_season` and the SAME target span — see CTRL-A/B/C below — because
a late-starting source forces a shorter training window and a shorter window
degrades the model on its own.
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
from experiments.bottomup.v2.factors_c1 import (                    # noqa: E402
    COVERAGE_FLOOR, FACTOR_BLOCKS, KNOWN_COL, PAIRED_CONTROL,
    build_features_c1, steep_recency, volume_cols_for)
from experiments.bottomup.v2.weekshape import build_v2_panel        # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
CELLS_CSV = OUT / "factor_c1_cells.csv"
CONTRASTS_CSV = OUT / "factor_c1_contrasts.csv"

HOLDOUT_SEASON = 2025
BOOT_REPS, BOOT_SEED = 4000, 20260801

#: campaign multiplicity at grading time: 56 (batches 5/6/7) + 16 (M2 incl.
#: Amendment 1) + 20 (B1 incl. Amendment 1) + 23 (this batch) = 115 > floor 80.
#: PR-007's 4 sit in their own family (`pr007.md`) and are excluded, exactly as
#: `run_v2.py` excluded them at M=92.
M_CAMPAIGN = 130
Q_FDR = 0.10

#: Deltas below this in absolute value are treated as exactly zero. Spearman on
#: 10-19 players is a ratio of integers; any real difference is >= ~1e-3. A
#: delta of 1e-17 is float64 noise from two rhos taking different code paths,
#: never a model difference.
DELTA_EPS = 1e-9

#: registered in batch-C1: {control: (first_feature_season, first_target, last)}
CONTROLS: Dict[str, Tuple[int, int, int]] = {
    "CTRL-A": (2012, 2018, 2024),
    "CTRL-B": (2015, 2018, 2024),
    "CTRL-C": (2017, 2019, 2024),
}

#: registered in batch-C1: arm -> (control, positions)
ARMS: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "F0": ("CTRL-A", ("QB", "RB", "WR", "TE")),
    "F1": ("CTRL-B", ("RB", "WR", "TE")),
    "F2": ("CTRL-A", ("RB", "WR", "TE")),
    "F3": ("CTRL-A", ("QB", "RB", "WR", "TE")),
    "F4": ("CTRL-C", ("WR", "TE")),
    "F5": ("CTRL-C", ("RB", "WR", "TE")),
    "F6": ("CTRL-A", ("QB", "RB", "WR", "TE")),
}

FACTOR_NAME = {
    "F0": "PLACEBO (seeded N(0,1) noise)",
    "F1": "offensive snap share, recency-weighted",
    "F2": "red-zone (inside-20) usage share of team",
    "F3": "expected fantasy points per game + realised-minus-expected residual",
    "F4": "NGS average separation (lag 1)",
    "F5": "route participation and targets per route run (LABELLED PROXY)",
    "F6": "steeper recency weighting of prior seasons (0.70/0.22/0.08)",
}

# Amendment 1: the paired `*_known` control arms inherit their treatment's
# control and positions, so the pair provably differs by the value column alone.
for _k, _f in PAIRED_CONTROL.items():
    ARMS[_k] = ARMS[_f]
    FACTOR_NAME[_k] = f"CONTROL — {KNOWN_COL[_f]} indicator alone (pairs {_f})"
del _k, _f

# carry the C1 factor columns into the output frame so coverage is measurable on
# the graded population rather than on the feature frame. Additive module-level
# patch, read by `run()` at call time — deliberately not an edit to the shared
# harness while other agents run against it.
E._CARRY = E._CARRY + [c for c in (
    "placebo_noise", "snapshare_w", "snap_known", "rz_use_share_w",
    "rz_use_known", "xfp_pg_w", "xfp_resid_pg_w", "xfp_known", "sep_1",
    "sep_known_1", "tprr_w", "rpg_w", "routes_known") if c not in E._CARRY]


# --------------------------------------------------------------------- running
def _feature_fn(blocks: Tuple[str, ...]):
    def fn(panel, universe, target_season):
        return build_features_c1(panel, universe, target_season, blocks=blocks)
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
            feature_fn=_feature_fn(blocks),
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
    """Per (position, season) on the graded population: the ADR-069 absolute
    steering metric, the cell size, and the factor's coverage."""
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
        rows.append(row)
    return pd.DataFrame(rows)


# -------------------------------------------------------------------- grading
def boot_diff(joined: pd.DataFrame) -> Tuple[float, float, float, int, float]:
    """Paired season-block bootstrap on the per-season deltas. Same estimator,
    reps and seed as batch-B1 — this batch extends that harness rather than
    inventing a second one."""
    sub = joined[["a", "b"]].dropna()
    diffs = np.array((sub["a"] - sub["b"]).to_numpy(dtype=float), copy=True)
    # NUMERICAL HYGIENE, not a rule change, and it can only remove a WIN.
    # An arm that changes nothing produces per-season deltas at the float64
    # representation limit (~1e-17) rather than exact zeros, because the two
    # rhos travel different code paths. Every such delta then shares a sign, so
    # every bootstrap resample mean sits above zero and the CI excludes zero:
    # arm F2k graded a BH-robust WIN on a mean delta of 3.97e-17 (p = 0.00025).
    # Snapping sub-epsilon deltas to zero is arithmetic, not judgment. It does
    # NOT address the separate calibration defect measured by the placebo, where
    # the deltas are real.
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
        rows.append(dict(
            factor=factor, name=FACTOR_NAME[factor], control=ctrl, position=pos,
            delta=d, lo=lo, hi=hi, n_seasons=n, p=p, coverage=cov,
            ctrl_mean_rho=float(j["b"].mean()) if len(j) else np.nan,
            arm_mean_rho=float(j["a"].mean()) if len(j) else np.nan,
            games_arm="G0"))
    return rows


def grade(df: pd.DataFrame) -> pd.DataFrame:
    """CI verdict + BH at the campaign denominator, recomputed over every row
    accumulated so far. Conservative by construction: this batch's p-values are
    ranked among themselves against M_CAMPAIGN, the convention M2-4 recorded and
    `run_v2.py` implements."""
    df = df.copy()

    def verdict(r):
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

    df["verdict"] = df.apply(verdict, axis=1)

    # ---- Amendment 1's VOID rule, applied before BH so a voided cell cannot
    # spend a BH slot. A treatment WIN is VOID where the paired `*_known`-only
    # control also WINS at the CI level: the win is then attributable to the
    # coverage indicator, not to the factor. Deliberately asymmetric — voiding
    # needs the loose bar, claiming needs the BH-robust one. A treatment WIN
    # whose control has not been run yet is marked as such and may NOT be
    # claimed; that is what stops an INCLUDE being declared on a half-run pair.
    treat_of = PAIRED_CONTROL
    ctrl_win = {(r["factor"], r["position"])
                for _, r in df.iterrows() if r["verdict"] == "WIN"}
    ctrl_ran = set(zip(df["factor"], df["position"]))
    for i, r in df.iterrows():
        if r["verdict"] != "WIN":
            continue
        kname = f"{r['factor']}k"
        if kname not in treat_of:
            continue
        if (kname, r["position"]) in ctrl_win:
            df.at[i, "verdict"] = "WIN (VOID: control wins)"
        elif (kname, r["position"]) not in ctrl_ran:
            df.at[i, "verdict"] = "WIN (control pending)"

    ok = df["p"].notna() & ~df["verdict"].str.startswith("NO DATA")
    df["bh_reject_campaign"] = False
    if ok.any():
        ps = df.loc[ok, "p"].to_numpy()
        order = np.argsort(ps)
        keep = np.zeros(len(ps), dtype=bool)
        thresh = 0
        for rank, i in enumerate(order, start=1):
            if ps[i] <= Q_FDR * rank / M_CAMPAIGN:
                thresh = rank
        if thresh > 0:
            keep[order[:thresh]] = True
        df.loc[ok, "bh_reject_campaign"] = keep
    return df


def factor_verdict(g: pd.DataFrame) -> str:
    """The registered inclusion rule, batch-C1 + Amendment 1.

    Only an unqualified `WIN` counts toward INCLUDE: a cell voided by its
    paired coverage-indicator control, or one whose control has not been run,
    is neither a WIN nor a HARM.
    """
    if (g["verdict"].str.startswith("NO DATA")).all():
        return "NO DATA"
    if (g["verdict"] == "WIN (control pending)").any():
        return "PENDING CONTROL"
    bh_win = ((g["verdict"] == "WIN") & g["bh_reject_campaign"]).any()
    bh_harm = ((g["verdict"] == "HARM") & g["bh_reject_campaign"]).any()
    ci_harm = (g["verdict"] == "HARM").any()
    voided = (g["verdict"] == "WIN (VOID: control wins)").any()
    if bh_win and not ci_harm:
        return "INCLUDE"
    if bh_win and ci_harm:
        return "INCLUDE (partial)"
    if bh_harm and not bh_win:
        return "EXCLUDE"
    return "NULL (VOIDED)" if voided else "NULL"


# ----------------------------------------------------------------------- main
def read_contrasts() -> pd.DataFrame:
    """`keep_default_na=False` because pandas reads the literal verdict string
    `NULL` back as NaN — which silently turned every graded NULL cell into a
    missing verdict on the round trip. Empty fields are still NaN."""
    return pd.read_csv(CONTRASTS_CSV, keep_default_na=False, na_values=[""])


def recontrast(cells: pd.DataFrame) -> pd.DataFrame:
    """Recompute every contrast from the per-season cells on disk, then grade.

    Cheap — no model is refitted — and it is the only correct response to a
    change in the estimator, since `lo`/`hi`/`p` stored from an earlier run are
    stale the moment `boot_diff` changes.
    """
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
    ap.add_argument("--arms", default="", help="comma list, e.g. F0,F1")
    ap.add_argument("--regrade", action="store_true",
                    help="recompute BH + verdicts over accumulated contrasts")
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

        print(f"\n### arm {factor} — {FACTOR_NAME[factor]} "
              f"(vs {ctrl}, positions {positions})", flush=True)
        if factor == "F6":
            with steep_recency():
                full = run_one(panel, factor, factor, positions, ff, ft, lt)
        else:
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
            "verdict", "bh_reject_campaign"]
    print(f"\n{'='*100}\nBATCH-C1 (BH at campaign M={M_CAMPAIGN}, q={Q_FDR}; "
          f"control = v2 games arm G0)\n{'='*100}")
    print(df[cols].round(4).to_string(index=False))
    if df["factor"].nunique() > 1 or True:
        print("\nfactor verdicts (registered inclusion rule):")
        for f, g in df.groupby("factor"):
            print(f"  {f}  {factor_verdict(g):18s}  {FACTOR_NAME[f]}")


if __name__ == "__main__":
    main()
