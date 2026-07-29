"""Pass 3, part 3 closing measurement -- is the thing recency weighting would
chase actually persistent?

EXPLORATORY.

The board's fitted slope decomposes (pass3_artifacts.py check E) into

    b_consensus(pos, season) ~ rho(pos, season) * b_realised(pos, season)
                               ^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^
                               market ordering    positional value spread
                               skill that year    that year

Recency-weighting the board's curve is a bet that BOTH terms persist season to
season. This file measures the lag-1 persistence of each, separately, so the
bet is priced instead of assumed:

  1. lag-1 autocorrelation of consensus ordering skill (tau_b), pooled across
     positions because n = 5 per position is 4 transitions.
  2. lag-1 autocorrelation of the realised value slope, on 1999-2024, which has
     enough transitions to say something.
  3. the same for the board's own fitted consensus slope.

If (1) is ~0 and (2) is positive, then the component recency weighting can
legitimately track is the VALUE curve, and the component it would actually be
chasing on the board's consensus fit is noise.

Section 4b: does the board movement under reweighting fall INSIDE the VBD
intervals the board already publishes? A reordering entirely inside its own
error bars is not a decision change.

2025 consensus outcomes are read for the descriptive tau_b series only, on the
same footing as pass3_rank_curve_regimes 1. No selection is made from them.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
_SRC = REPO / "src"
for _p in (str(REPO), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_board as mb  # noqa: E402
from scoring import ReplacementLevels  # noqa: E402
from pass3_rank_curve_regimes import (  # noqa: E402
    CONSENSUS_SEASONS, POSITIONS, consensus_obs, fit_log_rank, realised_obs,
)
from pass3_weighting import scheme_weights, weighted_fit  # noqa: E402

SEED = 20260729


def lag1(series, n_boot=8000, seed=SEED):
    """Lag-1 Pearson autocorrelation with a bootstrap CI over the PAIRS.
    Reported with n because with 4 pairs the CI is close to uninformative and
    that is the point being made, not a defect to hide."""
    x = np.asarray([a for a, b in series], dtype=float)
    y = np.asarray([b for a, b in series], dtype=float)
    if len(x) < 3:
        return None
    r = float(np.corrcoef(x, y)[0, 1])
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        if np.std(x[i]) < 1e-12 or np.std(y[i]) < 1e-12:
            continue
        draws.append(float(np.corrcoef(x[i], y[i])[0, 1]))
    return r, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)), len(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(REPO / "data" / "nfl.db"))
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    from scipy.stats import kendalltau

    print("=" * 78)
    print("1. PERSISTENCE of consensus ordering skill (tau_b), 2021-2025")
    print("   pooled across positions (4 transitions each, 16 pairs). Each")
    print("   position is z-scored within itself first so a pooled correlation")
    print("   measures within-position persistence, not between-position level.")
    print("=" * 78)
    taus = {}
    for pos in POSITIONS:
        row = []
        for s in CONSENSUS_SEASONS:
            r, y, _ = consensus_obs(conn, s)[pos]
            order = np.argsort(-y)
            fin = np.empty(len(y))
            fin[order] = np.arange(1, len(y) + 1)
            row.append(float(kendalltau(r, fin).statistic))
        taus[pos] = np.array(row)
        print(f"   {pos}  " + "  ".join(f"{v:+.3f}" for v in row))
    pairs = []
    for pos in POSITIONS:
        v = taus[pos]
        z = (v - v.mean()) / (v.std(ddof=1) if v.std(ddof=1) > 0 else 1.0)
        pairs += list(zip(z[:-1], z[1:]))
    res = lag1(pairs)
    print(f"\n   lag-1 autocorr of consensus ordering skill: r = {res[0]:+.3f} "
          f"[{res[1]:+.3f}, {res[2]:+.3f}]  (n pairs = {res[3]})")

    print()
    print("=" * 78)
    print("2. PERSISTENCE of the REALISED value slope, 1999-2024 (25 transitions")
    print("   per position). This is the component with enough sample to judge.")
    print("=" * 78)
    for pos in POSITIONS:
        v = []
        for s in range(1999, 2025):
            r, y = realised_obs(conn, s)[pos]
            v.append(fit_log_rank(r, y).slope)
        v = np.array(v)
        res = lag1(list(zip(v[:-1], v[1:])))
        # variance decomposition: how much of the season-to-season movement is
        # a persistent level vs white noise
        print(f"   {pos}  lag-1 r = {res[0]:+.3f} [{res[1]:+.3f}, {res[2]:+.3f}]  "
              f"(n pairs = {res[3]})   sd across seasons = {v.std(ddof=1):5.1f}")

    print()
    print("=" * 78)
    print("3. PERSISTENCE of the BOARD's fitted consensus slope, 2021-2025")
    print("   (4 transitions per position, 16 pooled pairs -- reported so the")
    print("    reader can see it is uninformative, not to draw a conclusion)")
    print("=" * 78)
    pairs = []
    for pos in POSITIONS:
        v = np.array([fit_log_rank(*consensus_obs(conn, s)[pos][:2]).slope
                      for s in CONSENSUS_SEASONS])
        z = (v - v.mean()) / (v.std(ddof=1) if v.std(ddof=1) > 0 else 1.0)
        pairs += list(zip(z[:-1], z[1:]))
    res = lag1(pairs)
    print(f"   lag-1 autocorr = {res[0]:+.3f} [{res[1]:+.3f}, {res[2]:+.3f}]  "
          f"(n pairs = {res[3]})")

    print()
    print("=" * 78)
    print("4b. Does reweighting move any player OUTSIDE the VBD interval the")
    print("    board already publishes for him? (2026 board, season-level")
    print("    bootstrap intervals, exactly as make_board computes them)")
    print("=" * 78)
    levels = ReplacementLevels()
    base = levels.baselines()
    train = [2021, 2022, 2023, 2024, 2025]
    intervals = mb.bootstrap_vbd_intervals(conn, 2026, levels, train, n_bootstrap=2000)
    cache = {s: consensus_obs(conn, s) for s in train}
    live = mb._positional_ranks(mb._consensus_board(conn, 2026, source=mb.SOURCE))

    def curves_for(scheme):
        out = {}
        for pos in POSITIONS:
            per = {s: (cache[s][pos][0], cache[s][pos][1]) for s in train}
            f = weighted_fit(per, scheme_weights(scheme, train, 2026))
            if f:
                out[pos] = f
        return out

    flat = curves_for("flat")
    for scheme in ("last1", "last2", "last3", "hl1", "hl2", "hl3", "hl5"):
        cur = curves_for(scheme)
        outside = tot = 0
        worst = None
        for pos, rows in live.items():
            if pos not in cur:
                continue
            for i, r in enumerate(rows, start=1):
                lo, hi = intervals.get(pos, {}).get(i, (float("nan"), float("nan")))
                if not np.isfinite(lo):
                    continue
                v_new = cur[pos][1] * (np.log(i) - np.log(base[pos]))
                tot += 1
                if v_new < lo or v_new > hi:
                    outside += 1
                    d = max(lo - v_new, v_new - hi)
                    if worst is None or d > worst[0]:
                        worst = (d, r["player_name"], pos, i, v_new, lo, hi)
        pct = 100.0 * outside / tot if tot else 0.0
        s = f"   {scheme:<6} {outside:4d}/{tot} ({pct:5.1f}%) reweighted VBDs fall OUTSIDE the published 95% CI"
        print(s)
        if worst:
            print(f"          worst: {worst[1]} ({worst[2]}{worst[3]}) new VBD "
                  f"{worst[4]:+.1f} vs published [{worst[5]:+.1f},{worst[6]:+.1f}]")


if __name__ == "__main__":
    main()
