"""ADR-070 grading — assembles CellReports from what the sweep left on disk.

Standalone and idempotent: reads `results/sweep070/cells.csv` (observed runs,
k = 0) and `results/sweep070/draws/*.csv` (permutation-null draws, per-season
metrics per draw — the M-1(B) requirement, stored not summarised), applies the
§4 machinery from `adr070.py`, and writes `graded_<batch>.csv`. Re-running it
recomputes every verdict from disk; it fits nothing.

Multiplicity accounting (§4.5, and a CORRECTION flagged to strategist):
`adr070.M_CAMPAIGN_BASE` was committed as 230 = 130 (through C1) + 88 (D1)
+ 12 (D1-A1), which OMITS batch C2's registered m_b = 29 (`batch-C2.md`,
ee87b53, "M_campaign = max(130+29, 80) = 159"). Shrinking the denominator is
the textbook error (ADR-070 §2, last row), so grading here uses
M = 259 (+ C3's m_b once registered). Larger M is conservative for discovery
and costs draws; the discrepancy is reported in the thread reply, not silently
absorbed either way.

VOID rule: a treatment WIN is VOID where the paired `*k` coverage-indicator
control at the same position has p_win <= 0.05 (loose bar to void, BH bar to
claim). A WIN candidate whose k-arm ensemble has not run yet is `WIN (control
pending)` and NOT claimable — the driver enqueues the k-arm ensemble when a
treatment cell's p_two <= 0.10 in the WIN direction.
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

from experiments.bottomup.v2 import ensemble070 as ens              # noqa: E402
from experiments.bottomup.v2.adr070 import (                        # noqa: E402
    CellReport, Consistency, H_EXCEED, bc_sequential_p, bh_reject,
    consistency, descriptive_spread, ensemble_stats, snap_deltas,
    tolerances, verdict as verdict_of,
)

OUT = _REPO / "experiments" / "bottomup" / "results" / "sweep070"
DRAWS = OUT / "draws"
CELLS_CSV = OUT / "cells.csv"

#: campaign M for grading: 130 (through C1) + 29 (C2) + 88 (D1) + 12 (D1-A1)
#: = 259 base, plus every batch REGISTERED into the manifest since (a
#: registered test counts from registration, run or not): C3 25, C4 22,
#: AB1 27. Late-arrival batches add their M_B here when their registration
#: lands. Grading is idempotent — the final report regenerates every batch's
#: grades at the final cumulative M.
M_EXTRA_REGISTERED = {"C3": 25, "C4": 22, "AB1": 27, "C5": 27, "CT1": 82}
M_CAMPAIGN = 259 + sum(M_EXTRA_REGISTERED.values())
#: §4.3: resolution is bought with draws. p_floor = 2/(L+1) = 2.22e-4 stays
#: below the BH rank-1 threshold q/M for M <= 450.
L_DRAWS = 8999

#: arms never graded as primary cells
CO_REPORT_ONLY = {("D1A1", "Q0w")}
#: k-arms (paired coverage controls): graded for their p (VOID) only
K_ARMS = {a for (b, a) in ens.ARMS070 if a.endswith("k")}


def cell_id(batch: str, arm: str, pos: str) -> str:
    return f"{batch}__{arm}__{pos}"


def load_cells() -> pd.DataFrame:
    if not CELLS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(CELLS_CSV)


def load_draws(batch: str, arm: str, pos: str) -> pd.DataFrame:
    p = DRAWS / f"{cell_id(batch, arm, pos)}.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def _metric_col(endpoint: str) -> str:
    return {"rho_points": "rho_points", "mae_games": "mae_games"}[endpoint]


def obs_frames(cells: pd.DataFrame, a: ens.Arm070, pos: str
               ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    arm_c = cells[(cells["batch"] == a.batch) & (cells["run"] == a.arm)
                  & (cells["position"] == pos) & (cells["k"] == 0)]
    ctl_c = cells[(cells["run"] == f"CTRL-{a.family}")
                  & (cells["position"] == pos) & (cells["k"] == 0)]
    if not len(arm_c) or not len(ctl_c):
        return None, None
    return arm_c, ctl_c


#: Incremental cache for `draw_delta_bars`, keyed by cell.
#:
#: The sweep driver calls this between every chunk of draws to run the
#: sequential test, and the function is O(n) in draws — pivot plus a per-row
#: `snap_deltas` loop. Called O(log n) times per cell with a growing n, that
#: serial step was measured (2026-08-04) taking ~72s of a 141s chunk interval
#: at n=2,000, with all workers idle through it, and it grows with n.
#:
#: Draws are append-only and immutable once written, so rows at k <= what we
#: already folded in can never change. Cache the snapped matrix and extend it
#: with only the new rows. Results are identical because `snap_deltas` is
#: applied per row, independently.
_BARS_CACHE: Dict[Tuple, Dict] = {}


def draw_delta_bars(a: ens.Arm070, pos: str, ctrl_cells: pd.DataFrame
                    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """(ordered delta_bars by k, per-draw per-season delta matrix, seasons).
    Deltas are canonical (positive = better), §4.7-snapped per season."""
    d = load_draws(a.batch, a.arm, pos)
    seasons = sorted(ctrl_cells["season"].astype(int).tolist())
    if not len(d):
        return np.array([]), np.zeros((0, len(seasons))), seasons
    col = _metric_col(a.endpoint)
    ctl = ctrl_cells.set_index("season")
    sign = 1.0 if a.endpoint == "rho_points" else -1.0
    n_g = [int(ctl.loc[s, "n_board_vet"]) if s in ctl.index else 0
           for s in seasons]
    base = np.array([float(ctl.loc[s, col]) if s in ctl.index else np.nan
                     for s in seasons])
    cont = a.endpoint == "mae_games"

    # --- incremental fold-in ------------------------------------------------
    key = (a.batch, a.arm, pos, a.endpoint)
    c = _BARS_CACHE.get(key)
    reusable = (
        c is not None
        and c["seasons"] == seasons
        and c["n_g"] == n_g
        and np.array_equal(c["base"], base, equal_nan=True)
        # a resumed run must never re-issue a k; if one reappears the cached
        # rows could be stale, so fall back to a full recompute
        and not (d["k"] <= c["last_k"]).all()
        and int(d["k"].min()) <= c["last_k"] + 1
    )
    d_new = d[d["k"] > c["last_k"]] if reusable else d
    if reusable and not len(d_new):
        return c["bars"], c["mat"], seasons

    piv = d_new.pivot_table(index="k", columns="season", values=col,
                            aggfunc="last")
    piv = piv.reindex(columns=seasons).sort_index()
    mat = sign * (piv.to_numpy(dtype=float) - base[None, :])
    for i in range(mat.shape[0]):
        mat[i] = snap_deltas(mat[i], n_g, continuous=cont)
    bars = np.array([np.nanmean(r) if np.isfinite(r).any() else np.nan
                     for r in mat])
    if reusable:
        mat = np.vstack([c["mat"], mat])
        bars = np.concatenate([c["bars"], bars])
    _BARS_CACHE[key] = {"seasons": seasons, "n_g": n_g, "base": base,
                        "last_k": int(d["k"].max()), "mat": mat, "bars": bars}
    return bars, mat, seasons


def obs_deltas(a: ens.Arm070, pos: str, cells: pd.DataFrame
               ) -> Tuple[np.ndarray, List[int], List[int], float, float]:
    arm_c, ctl_c = obs_frames(cells, a, pos)
    if arm_c is None:
        return np.array([]), [], [], np.nan, np.nan
    dd = ens.canonical_deltas(arm_c, ctl_c, a.endpoint)
    seasons = dd["season"].tolist()
    deltas = dd["delta"].to_numpy(dtype=float)
    n_g = dd["n_graded"].astype(int).tolist()
    cov = np.nan
    if "coverage" in arm_c.columns and arm_c["coverage"].notna().any():
        cov = float(arm_c["coverage"].mean())
    # §4.6 item 5 — Pearson diagnostic (points endpoint only)
    pearson = np.nan
    if a.endpoint == "rho_points" and "pearson_points" in arm_c.columns:
        j = arm_c.set_index("season")["pearson_points"] \
            - ctl_c.set_index("season")["pearson_points"]
        pearson = float(j.mean()) if j.notna().any() else np.nan
    return deltas, seasons, n_g, cov, pearson


def grade_batch(batch: str, m_campaign: int = M_CAMPAIGN,
                l_draws: int = L_DRAWS) -> pd.DataFrame:
    cells = load_cells()
    if not len(cells):
        return pd.DataFrame()
    arms = [a for (b, _), a in ens.ARMS070.items() if b == batch]

    # ---- k-arm p-values first (the VOID inputs)
    k_p: Dict[Tuple[str, str], float] = {}
    for a in arms:
        if a.arm not in K_ARMS:
            continue
        for pos in a.positions:
            deltas, seasons, n_g, _, _ = obs_deltas(a, pos, cells)
            if not len(deltas):
                continue
            db = float(np.nanmean(deltas)) if np.isfinite(deltas).any() else np.nan
            arm_c, ctl_c = obs_frames(cells, a, pos)
            bars, _, _ = draw_delta_bars(a, pos, ctl_c)
            if np.isfinite(db) and db > 0 and len(bars):
                seq = bc_sequential_p(db, bars, h=H_EXCEED, L=l_draws)
                k_p[(a.arm, pos)] = seq.p_one   # one-sided win p for voiding
            elif np.isfinite(db) and db <= 0:
                k_p[(a.arm, pos)] = 1.0

    # ---- primary cells
    reports: List[CellReport] = []
    for a in arms:
        if (a.batch, a.arm) in CO_REPORT_ONLY or a.arm in K_ARMS:
            continue
        for pos in a.positions:
            deltas, seasons, n_g, cov, pearson = obs_deltas(a, pos, cells)
            arm_c, ctl_c = obs_frames(cells, a, pos)
            if not len(deltas) or ctl_c is None:
                continue
            key = ens.key_for(a.family, pos)
            db = float(np.nanmean(deltas)) if np.isfinite(deltas).any() else np.nan
            bars, mat, dseasons = draw_delta_bars(a, pos, ctl_c)
            if a.null_kind == "none":
                seq = bc_sequential_p(np.nan, [], h=H_EXCEED, L=l_draws)
                cons = None
            else:
                seq = bc_sequential_p(db, bars, h=H_EXCEED, L=l_draws)
                tols = tolerances(n_g, continuous=(a.endpoint == "mae_games"))
                cons = (consistency(deltas, mat, tols, seq.direction)
                        if len(mat) else None)
            kname = f"{a.arm}k"
            voided = False
            pending = False
            if seq.direction == "WIN" and (a.batch, kname) in ens.ARMS070:
                pk = k_p.get((kname, pos))
                if pk is None:
                    pending = seq.p_two is not None and np.isfinite(seq.p_two) \
                        and seq.p_two <= 0.10
                else:
                    voided = pk <= 0.05
            rep = CellReport(
                batch=batch, arm=a.arm, position=pos, key=key,
                s_pos=int(np.isfinite(deltas).sum()), endpoint=a.endpoint,
                better="higher" if a.endpoint == "rho_points" else "lower",
                delta_bar=db, deltas=[float(x) for x in deltas],
                seasons=[int(s) for s in seasons], n_graded=n_g, seq=seq,
                cons=cons, stats=ensemble_stats(bars), coverage=cov,
                voided=voided, verdict="", bh_robust=False,
                pearson_delta_bar=pearson,
                descriptive_spread=descriptive_spread(deltas),
                seed_scheme="sha256(arm|position|season|k)", h=H_EXCEED,
                L=l_draws)
            rep._pending_control = pending          # carried to verdict below
            reports.append(rep)

    if not reports:
        return pd.DataFrame()

    # ---- BH at the cumulative campaign M, over this batch's primary cells
    ps = [r.seq.p_two for r in reports]
    keep = bh_reject(ps, m_campaign)
    rows = []
    for r, bh in zip(reports, keep):
        r.bh_robust = bool(bh)
        if ens.ARMS070[(r.batch, r.arm)].null_kind == "none":
            r.verdict = "NOT GRADEABLE (no-column arm; §4.1 — separate ruling)"
        else:
            r.verdict = verdict_of(
                r.seq.p_two, r.bh_robust, r.seq.direction,
                bool(r.cons and r.cons.consistent), r.voided, r.coverage,
                r.seq.stop_reason, deltas=np.array(r.deltas))
            if getattr(r, "_pending_control", False) and r.verdict == "INCLUDE":
                r.verdict = "WIN (control pending)"   # not claimable half-run
        row = r.flat()
        # the F3-RB confirmatory design (strategist ruling): the incremental
        # pre-2018 seasons are the genuinely out-of-sample slice — report the
        # split on every cell, it costs nothing
        pre = [d for d, s in zip(r.deltas, r.seasons)
               if s < 2018 and np.isfinite(d)]
        row["delta_bar_pre2018"] = float(np.mean(pre)) if pre else np.nan
        row["n_pre2018"] = len(pre)
        row["m_campaign"] = m_campaign
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"graded_{batch}.csv", index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--m", type=int, default=M_CAMPAIGN)
    args = ap.parse_args()
    df = grade_batch(args.batch, m_campaign=args.m)
    if not len(df):
        print("nothing gradeable on disk")
        return
    cols = ["arm", "position", "S_pos", "delta_bar", "p", "p_floor",
            "n_draws_used", "stop_reason", "direction", "C", "C_q95_null",
            "consistent", "bh_robust", "verdict"]
    print(df[[c for c in cols if c in df.columns]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
