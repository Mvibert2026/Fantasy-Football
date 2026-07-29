"""Pass 3, part 1 -- is the QB slope collapse a property of the data or of the
way the curve is fitted?

EXPLORATORY. Five artifact checks, each of which could produce the observed
series without any regime change:

  A. DEPTH.        RELEVANT_DEPTH pins QB and TE at 20. A slope fitted over
                   ranks 1-20 is a different estimand from one over 1-32.
  B. INFLUENCE.    Jackknife-drop-one. With n=20 and R^2 ~ 0.2, one injured
                   consensus QB1 can carry the whole slope.
  C. FUNCTIONAL FORM. ln(rank) is an assumption. If the collapse only appears
                   under ln, it is a form artifact.
  D. SCALE.        A raw-points slope moves with league-wide scoring. Normalise
                   points within season (divide by the position's mean) and the
                   scale channel is removed.
  E. ATTENUATION.  slope_consensus ~ slope_realised * reliability(consensus).
                   Decompose: did the VALUE spread move, or did consensus stop
                   ordering the position?

2025 outcomes are read here for the same reason as pass3_rank_curve_regimes 1:
the question IS whether the published -4.1 is real. Nothing in this file feeds
a model choice.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

REPO = Path(__file__).resolve().parents[2]
_SRC = REPO / "src"
for _p in (str(REPO), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pass3_rank_curve_regimes import (  # noqa: E402
    CONSENSUS_SEASONS, POSITIONS, RELEVANT_DEPTH, boot_slope_ci,
    consensus_obs, fit_log_rank, realised_obs,
)

SEED = 20260729


def check_depth(conn):
    print("=" * 78)
    print("A. DEPTH SENSITIVITY -- fitted slope by how deep the curve is fitted")
    print("   shipped depths: QB 20, RB 45, WR 60, TE 20")
    print("=" * 78)
    grids = {"QB": [12, 16, 20, 24, 32], "TE": [12, 16, 20, 24, 32],
             "RB": [24, 32, 45, 55, 70], "WR": [30, 45, 60, 75, 90]}
    for pos in POSITIONS:
        print(f"\n{pos}")
        print("   depth  " + "  ".join(f"{s:>7}" for s in CONSENSUS_SEASONS))
        for d in grids[pos]:
            vals = []
            for s in CONSENSUS_SEASONS:
                obs = consensus_obs(conn, s, {**RELEVANT_DEPTH, pos: d})
                r, y, _ = obs[pos]
                f = fit_log_rank(r, y)
                vals.append(f.slope if f else float("nan"))
            mark = " <- shipped" if d == RELEVANT_DEPTH[pos] else ""
            print(f"   {d:>5}  " + "  ".join(f"{v:+7.1f}" for v in vals) + mark)


def check_influence(conn):
    print()
    print("=" * 78)
    print("B. INFLUENCE -- jackknife drop-one, per position-season")
    print("   'range' = span of the slope across all n drop-one refits.")
    print("   If dropping ONE player moves the slope by more than the gap the")
    print("   regime story rests on, the story is one player.")
    print("=" * 78)
    for pos in POSITIONS:
        print(f"\n{pos}")
        for s in CONSENSUS_SEASONS:
            r, y, names = consensus_obs(conn, s)[pos]
            full = fit_log_rank(r, y).slope
            jk = []
            for i in range(len(r)):
                m = np.ones(len(r), dtype=bool)
                m[i] = False
                jk.append((fit_log_rank(r[m], y[m]).slope, names[i], int(r[i]), y[i]))
            jk.sort()
            lo, hi = jk[0], jk[-1]
            print(f"   {s}  full {full:+7.1f}   drop-one range [{lo[0]:+7.1f},{hi[0]:+7.1f}]"
                  f"  span {hi[0]-lo[0]:6.1f}")
            print(f"          steepest-if-dropped: {hi[1]} (rank {hi[2]}, {hi[3]:.0f} pts)"
                  f"  |  flattest-if-dropped: {lo[1]} (rank {lo[2]}, {lo[3]:.0f} pts)")


def check_form(conn):
    print()
    print("=" * 78)
    print("C. FUNCTIONAL FORM -- does the pattern survive a different curve?")
    print("   reported as R^2 of each form, plus the top-vs-replacement SPREAD")
    print("   in points, which is the form-free version of 'slope'.")
    print("   spread = E[pts at rank 1] - E[pts at replacement rank], fitted.")
    print("=" * 78)
    base = {"QB": 10, "RB": 30, "WR": 40, "TE": 10}
    for pos in POSITIONS:
        print(f"\n{pos}  (replacement rank {base[pos]})")
        print("   season   ln-spread   lin-spread   pow-spread   R2ln   R2lin  R2pow"
              "   RAW top3-repl")
        for s in CONSENSUS_SEASONS:
            r, y, _ = consensus_obs(conn, s)[pos]
            out = []
            for name, tf in (("ln", np.log), ("lin", lambda v: v),
                             ("pow", lambda v: v ** -0.5)):
                x = tf(r)
                X = np.column_stack([np.ones(len(x)), x])
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                resid = y - X @ beta
                r2 = 1 - float(resid @ resid) / float(((y - y.mean()) ** 2).sum())
                sp = float(beta[0] + beta[1] * tf(np.array([1.0]))[0]) - float(
                    beta[0] + beta[1] * tf(np.array([float(base[pos])]))[0])
                out.append((sp, r2))
            # raw, model-free: mean of realised top-3 consensus ranks minus the
            # realised points of the consensus player AT the replacement rank
            raw = float(y[:3].mean() - y[base[pos] - 1])
            print(f"    {s}   {out[0][0]:9.1f}   {out[1][0]:10.1f}   {out[2][0]:10.1f}"
                  f"   {out[0][1]:.3f}  {out[1][1]:.3f}  {out[2][1]:.3f}   {raw:9.1f}")


def check_scale(conn):
    print()
    print("=" * 78)
    print("D. SCALE -- slope on points NORMALISED by that season's positional")
    print("   mean. Removes league-wide scoring drift. A collapse that vanishes")
    print("   here was scoring inflation, not a regime.")
    print("=" * 78)
    for pos in POSITIONS:
        vals, raws = [], []
        for s in CONSENSUS_SEASONS:
            r, y, _ = consensus_obs(conn, s)[pos]
            raws.append(fit_log_rank(r, y).slope)
            vals.append(fit_log_rank(r, y / y.mean()).slope)
        print(f"{pos}  raw  " + "  ".join(f"{v:+7.1f}" for v in raws))
        print(f"     norm " + "  ".join(f"{v:+7.3f}" for v in vals))


def check_attenuation(conn):
    print()
    print("=" * 78)
    print("E. DECOMPOSITION -- value spread vs consensus ordering skill")
    print("   realised slope = shape of the value distribution (order-statistic")
    print("     fit, 1999-2025 available but 2025 shown descriptively only)")
    print("   ratio = consensus slope / realised slope = attenuation. A ratio")
    print("     falling while the realised slope holds means the MARKET changed,")
    print("     not the position. Ratio < 1 is MECHANICAL and proves nothing on")
    print("     its own; only its MOVEMENT is informative.")
    print("   tau_b = Kendall tau, consensus rank vs realised finish rank, on")
    print("     the frozen pre-season universe. Direct measure of ordering skill.")
    print("=" * 78)
    from scipy.stats import kendalltau
    for pos in POSITIONS:
        print(f"\n{pos}")
        print("   season   consensus   realised    ratio    tau_b   R2(cons)")
        for s in CONSENSUS_SEASONS:
            rc, yc, _ = consensus_obs(conn, s)[pos]
            fc = fit_log_rank(rc, yc)
            rr, yr = realised_obs(conn, s)[pos]
            fr = fit_log_rank(rr, yr)
            # ordering skill on the frozen universe: consensus rank vs realised
            # finish rank AMONG THE CONSENSUS-LISTED PLAYERS ONLY
            order = np.argsort(-yc)
            fin = np.empty(len(yc))
            fin[order] = np.arange(1, len(yc) + 1)
            tau = float(kendalltau(rc, fin).statistic)
            print(f"    {s}   {fc.slope:+9.1f}  {fr.slope:+9.1f}   {fc.slope/fr.slope:6.3f}"
                  f"   {tau:+.3f}   {fc.r2:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(REPO / "data" / "nfl.db"))
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    checks = {"A": check_depth, "B": check_influence, "C": check_form,
              "D": check_scale, "E": check_attenuation}
    for k, fn in checks.items():
        if args.only and k not in args.only:
            continue
        fn(conn)


if __name__ == "__main__":
    main()
