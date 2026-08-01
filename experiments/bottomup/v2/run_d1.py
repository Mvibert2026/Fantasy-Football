#!/usr/bin/env python
"""Batch D1 runner — the v2 player-availability (projected games) model.

    .venv/bin/python -m experiments.bottomup.v2.run_d1 --arms P0,B0,A1
    .venv/bin/python -m experiments.bottomup.v2.run_d1 --regrade
    .venv/bin/python -m experiments.bottomup.v2.run_d1 --cases

Registration: `docs/ranking/factor-campaign-manifest/batch-D1.md`, committed at
95e2bc9 before any arm was fitted.

WRITTEN TO BE INTERRUPTED, same as `run_c1.py`: every arm appends its per-season
cells and its recomputed contrasts to CSV the moment it finishes, and `--regrade`
recomputes verdicts over whatever has accumulated without refitting anything.

TWO MATCHED CONTROLS, because a late-starting source forces a shorter training
window and a shorter window degrades the model on its own:
    CTRL-A  first_feature_season 2012, targets 2018-2024  (n=7)
    CTRL-D  first_feature_season 2018, targets 2020-2024  (n=5)
CTRL-D exists because `rosters_weekly`'s end-of-season RES capture breaks at
2017 (batch-D1 §2). Restricting only the target window is batch 5's mistake.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E             # noqa: E402
from experiments.bottomup.components.pos_eval import WalkForward       # noqa: E402
from experiments.bottomup.v2.availability_data import build_avail_panel  # noqa: E402
from experiments.bottomup.v2.availability_features import (            # noqa: E402
    PLACEBO_COL, build_features_d1)
from experiments.bottomup.v2.availability_model import (               # noqa: E402
    ARM_SPEC, PLACEBO_ARMS, make_avail_model)
from experiments.bottomup.v2.games_model import naive_persistence_games  # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
CELLS_CSV = OUT / "avail_d1_cells.csv"
CONTRASTS_CSV = OUT / "avail_d1_contrasts.csv"
PLAYERS_DIR = OUT / "avail_d1_players"

HOLDOUT_SEASON = 2025
BOOT_REPS, BOOT_SEED = 4000, 20260801
M_CAMPAIGN = 218          # batch-D1 registration: 130 + 88
Q_FDR = 0.10
DELTA_EPS = 1e-9

#: control -> (first_feature_season, first_target, last_target)
CONTROLS: Dict[str, Tuple[int, int, int]] = {
    "CTRL-A": (2012, 2018, 2024),
    "CTRL-D": (2018, 2020, 2024),
}

POSITIONS = ("QB", "RB", "WR", "TE")

#: arm -> control. Registered in batch-D1 §3.
ARM_CONTROL: Dict[str, str] = {
    "P0": "CTRL-A", "B0": "CTRL-A", "A1": "CTRL-A", "A1k": "CTRL-A",
    "A2": "CTRL-A", "A4": "CTRL-A",
    "P0d": "CTRL-D", "B0d": "CTRL-D", "A3": "CTRL-D", "A3k": "CTRL-D",
    "A5": "CTRL-D",
}

ARM_NAME = {
    "P0": "PLACEBO seeded N(0,1), n=7 window",
    "P0d": "PLACEBO seeded N(0,1), n=5 window",
    "B0": "ESTIMATOR FORM ONLY: binomial GLM on the incumbent feature list",
    "B0d": "ESTIMATOR FORM ONLY, n=5 window",
    "A1": "practice participation (DNP / Limited / Full)",
    "A1k": "CONTROL - bare 'appeared on an injury report in N-1'",
    "A2": "injury class (structural/soft/head/rest) + cross-season recurrence",
    "A3": "roster status N-1: resolved vs ongoing absence",
    "A3k": "CONTROL - bare 'has a roster row in N-1'",
    "A4": "practice + injury class (full-window combination)",
    "A5": "practice + injury class + roster status (everything)",
}

#: paired presence control -> the treatment it controls (batch 5 geometry)
PRESENCE_PAIR = {"A1k": "A1", "A3k": "A3"}

# Carry the D1 feature columns into the output frame so the descriptive subgroup
# tables are computed on the GRADED population rather than on the feature frame.
# Additive module-level patch read by `run()` at call time -- deliberately not an
# edit to the shared harness while other agents run against it.
E._CARRY = E._CARRY + [c for c in (
    "res_share_1", "res_end_1", "res_resolved_1", "act_share_1",
    "miss1_x_res_end", "ros_present_1", "ros_src_known_1",
    "prac_present_1", "prac_rep_share_1", "prac_dnp_share_1",
    "prac_lim_share_1", "prac_out_share_1", "prac_dnp_of_rep_1",
    "prac_dnp_late3_1", "prac_src_known_1", "inj_struct_share_1",
    "inj_soft_share_1", "inj_head_share_1", "inj_rest_share_1",
    "inj_nclass_1", "inj_recur_1", "inj_recur_known_1", PLACEBO_COL,
) if c not in E._CARRY]


# --------------------------------------------------------------------- running
@dataclass
class D1WalkForward(WalkForward):
    arm: str = "G0"

    def _make_model(self):
        return make_avail_model(self.position, self.arm, **self.model_kwargs)


def _feature_fn(arm: str):
    blocks = () if arm == "G0" else ARM_SPEC[arm][0]
    placebo = arm in PLACEBO_ARMS

    def fn(panel, universe, target_season):
        return build_features_d1(panel, universe, target_season,
                                 blocks=blocks, placebo=placebo)
    return fn


def run_one(panel, label: str, arm: str, positions, first_feature: int,
            first_target: int, last_target: int) -> pd.DataFrame:
    frames = []
    for pos in positions:
        wf = D1WalkForward(
            panel=panel, position=pos, first_target=first_target,
            last_target=last_target, min_train_seasons=2, avail_arm="A",
            calibrate_bonus=True, first_feature_season=first_feature,
            feature_fn=_feature_fn(arm), arm=arm, allow_preseason_proxy=False)
        players, _ = wf.run()
        aud = pd.DataFrame(wf.audit)
        assert (aud.max_feature_cutoff < aud.season).all(), f"{label}/{pos} feature leak"
        assert (aud.max_outcome_season < aud.season).all(), f"{label}/{pos} outcome leak"
        assert (aud.n_outcome_reads_at_target == 0).all(), f"{label}/{pos} target read"
        assert (aud.n_preseason_proxy_reads == 0).all(), f"{label}/{pos} PROXY READ"
        assert players["season"].max() < HOLDOUT_SEASON, "HOLDOUT TOUCHED"
        players["position"] = pos
        players["run"] = label
        frames.append(players)
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------- metrics
def cell_metrics(full: pd.DataFrame, label: str) -> pd.DataFrame:
    """Per (position, season) on the graded population (M-panel veterans)."""
    rows: List[Dict] = []
    for (pos, season), g in full.groupby(["position", "season"]):
        vet = g[g["entry"] == "veteran"]
        sub = vet[vet["average_pick"].notna()]
        row: Dict = {"run": label, "position": pos, "season": int(season),
                     "n_board_vet": len(sub), "n_vet": len(vet)}
        if len(sub) >= 10:
            gm = sub["games"].to_numpy(dtype=float)
            pg = sub["proj_games"].to_numpy(dtype=float)
            gn = naive_persistence_games(sub)
            row["rho_points"] = E.spearman(
                sub["proj_points"].to_numpy(dtype=float),
                sub["points"].to_numpy(dtype=float))
            row["rho_games"] = E.spearman(pg, gm)
            row["rho_games_naive"] = E.spearman(gn, gm)
            row["mae_games"] = float(np.mean(np.abs(pg - gm)))
            row["mae_games_naive"] = float(np.mean(np.abs(gn - gm)))
            row["bias_games"] = float(np.mean(pg - gm))
            row["sd_proj_games"] = float(np.std(pg))
            row["sd_games"] = float(np.std(gm))
            ra = E.returning_absent(sub)
            row["n_returning"] = int(ra.sum())
            if ra.sum() >= 5:
                m = ra.to_numpy()
                row["mae_games_returning"] = float(np.mean(np.abs(pg[m] - gm[m])))
                row["bias_games_returning"] = float(np.mean(pg[m] - gm[m]))
        if len(vet) >= 10:
            row["rho_points_fullvet"] = E.spearman(
                vet["proj_points"].to_numpy(dtype=float),
                vet["points"].to_numpy(dtype=float))
        rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- grading
def boot_diff(diffs: np.ndarray) -> Tuple[float, float, float, int, float]:
    d = np.array(diffs, dtype=float, copy=True)
    d = d[np.isfinite(d)]
    d[np.abs(d) < DELTA_EPS] = 0.0
    n = len(d)
    if n == 0:
        return np.nan, np.nan, np.nan, 0, np.nan
    rng = np.random.default_rng(BOOT_SEED)
    boot = np.array([np.mean(rng.choice(d, size=n, replace=True))
                     for _ in range(BOOT_REPS)])
    p = 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean()))
    return (float(d.mean()), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), n, min(1.0, max(p, 1.0 / BOOT_REPS)))


def contrast_rows(cells: pd.DataFrame, arm: str) -> List[Dict]:
    ctrl = ARM_CONTROL[arm]
    a_all = cells[cells["run"] == arm]
    c_all = cells[cells["run"] == ctrl]
    rows: List[Dict] = []
    for pos in POSITIONS:
        a = a_all[a_all.position == pos].set_index("season")
        b = c_all[c_all.position == pos].set_index("season")
        # E1 -- absolute steering metric, arm minus matched G0 control
        j = a[["rho_points"]].join(b[["rho_points"]], how="inner", rsuffix="_c")
        d, lo, hi, n, p = boot_diff((j["rho_points"] - j["rho_points_c"]).to_numpy())
        rows.append(dict(arm=arm, name=ARM_NAME[arm], control=ctrl, endpoint="E1",
                         metric="rho_points vs G0", position=pos, delta=d, lo=lo,
                         hi=hi, n_seasons=n, p=p,
                         ctrl_mean=float(j["rho_points_c"].mean()) if len(j) else np.nan,
                         arm_mean=float(j["rho_points"].mean()) if len(j) else np.nan))
        # E2 -- games ordering, arm minus naive persistence within the same arm
        k = a[["rho_games", "rho_games_naive"]].dropna()
        d, lo, hi, n, p = boot_diff((k["rho_games"] - k["rho_games_naive"]).to_numpy())
        rows.append(dict(arm=arm, name=ARM_NAME[arm], control="naive", endpoint="E2",
                         metric="rho_games vs naive persistence", position=pos,
                         delta=d, lo=lo, hi=hi, n_seasons=n, p=p,
                         ctrl_mean=float(k["rho_games_naive"].mean()) if len(k) else np.nan,
                         arm_mean=float(k["rho_games"].mean()) if len(k) else np.nan))
    return rows


def grade(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def verdict(r):
        if not np.isfinite(r["delta"]):
            return "NO DATA"
        if abs(r["delta"]) < DELTA_EPS:
            return "NULL (no change)"
        if r["lo"] > DELTA_EPS:
            return "WIN*"
        if r["hi"] < -DELTA_EPS:
            return "HARM*"
        return "NULL"

    df["verdict"] = df.apply(verdict, axis=1)
    ok = df["p"].notna() & (df["verdict"] != "NO DATA")
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
    # placebo null per (window, endpoint, position): the calibration instrument
    df["vs_placebo"] = ""
    for ctrl, pl in (("CTRL-A", "P0"), ("CTRL-D", "P0d")):
        for ep in ("E1", "E2"):
            for pos in POSITIONS:
                m = ((df.arm == pl) & (df.endpoint == ep) & (df.position == pos))
                if not m.any():
                    continue
                q = float(df.loc[m, "delta"].iloc[0])
                tgt = ((df.control.isin([ctrl, "naive"]))
                       & (df.endpoint == ep) & (df.position == pos)
                       & df.arm.map(lambda a: ARM_CONTROL.get(a) == ctrl))
                df.loc[tgt, "placebo_delta"] = q
                df.loc[tgt, "vs_placebo"] = np.where(
                    df.loc[tgt, "delta"] > q, "clears", "inside")
    return df


def recontrast(cells: pd.DataFrame) -> pd.DataFrame:
    runs = set(cells["run"].unique())
    rows: List[Dict] = []
    for a in ARM_CONTROL:
        if a in runs and ARM_CONTROL[a] in runs:
            rows.extend(contrast_rows(cells, a))
    return grade(pd.DataFrame(rows))


def _append(path: Path, new: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    old = pd.read_csv(path) if path.exists() else pd.DataFrame()
    merged = pd.concat([old, new], ignore_index=True).drop_duplicates(
        subset=keys, keep="last") if len(old) else new
    merged.to_csv(path, index=False)
    return merged


# ----------------------------------------------------------------------- main
def _report(df: pd.DataFrame) -> None:
    cols = ["arm", "endpoint", "position", "n_seasons", "ctrl_mean", "arm_mean",
            "delta", "lo", "hi", "p", "placebo_delta", "vs_placebo", "verdict",
            "bh_reject_campaign"]
    cols = [c for c in cols if c in df.columns]
    print(f"\n{'='*118}\nBATCH-D1 (BH at campaign M={M_CAMPAIGN}, q={Q_FDR}; "
          f"* = CI verdict only, GRADING SUSPENDED per C1)\n{'='*118}")
    print(df.sort_values(["endpoint", "arm", "position"])[cols]
          .round(4).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="")
    ap.add_argument("--positions", default=",".join(POSITIONS))
    ap.add_argument("--regrade", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

    if args.regrade and not args.arms:
        df = recontrast(pd.read_csv(CELLS_CSV))
        df.to_csv(CONTRASTS_CSV, index=False)
        _report(df)
        return

    arms = [a for a in args.arms.split(",") if a]
    for a in arms:
        if a not in ARM_CONTROL:
            raise SystemExit(f"unknown arm {a!r}; registered: {sorted(ARM_CONTROL)}")
    positions = tuple(p for p in args.positions.split(",") if p)

    print(f"HOLDOUT {HOLDOUT_SEASON}: sealed, never read. Panel gates enforce.",
          flush=True)
    panel = build_avail_panel()
    print(f"panel {panel.seasons[0]}-{panel.seasons[-1]}, "
          f"feature_gate={panel.feature_gate}, outcome_gate={panel.outcome_gate}",
          flush=True)

    cells = pd.read_csv(CELLS_CSV) if CELLS_CSV.exists() else pd.DataFrame()

    for arm in arms:
        ctrl = ARM_CONTROL[arm]
        ff, ft, lt = CONTROLS[ctrl]
        have = set(cells.loc[cells["run"] == ctrl, "position"].unique()) \
            if len(cells) else set()
        need = tuple(p for p in positions if p not in have)
        if need:
            print(f"\n### control {ctrl} (ff={ff}, targets {ft}-{lt}) {need}",
                  flush=True)
            c = run_one(panel, ctrl, "G0", need, ff, ft, lt)
            c.to_csv(PLAYERS_DIR / f"{ctrl}.csv.gz", index=False)
            cells = _append(CELLS_CSV, cell_metrics(c, ctrl),
                            ["run", "position", "season"])

        print(f"\n### arm {arm} — {ARM_NAME[arm]} (vs {ctrl}, {positions})",
              flush=True)
        full = run_one(panel, arm, arm, positions, ff, ft, lt)
        full.to_csv(PLAYERS_DIR / f"{arm}.csv.gz", index=False)
        cells = _append(CELLS_CSV, cell_metrics(full, arm),
                        ["run", "position", "season"])
        allc = recontrast(cells)
        allc.to_csv(CONTRASTS_CSV, index=False)
        _report(allc[allc["arm"] == arm])
        print(f"[recorded] {CELLS_CSV.name} + {CONTRASTS_CSV.name} + "
              f"{PLAYERS_DIR.name}/{arm}.csv.gz", flush=True)

    _report(recontrast(pd.read_csv(CELLS_CSV)))


if __name__ == "__main__":
    main()
