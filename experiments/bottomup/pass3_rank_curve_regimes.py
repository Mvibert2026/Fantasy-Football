"""Pass 3 -- is the shipped board's rank-curve slope collapse real, at which
positions, and what weighting does a holdout support?

EXPLORATORY. Nothing here is registered, nothing is corrected for multiplicity,
and no number in it may be reported as an edge or wired into the board. The one
confirmatory test worth running is an *ask* in the thread this pass opens.

WHAT THE SHIPPED BOARD ACTUALLY DOES (src/make_board.py)
--------------------------------------------------------
`fit_rank_curves` pools every training season flat and fits, per position,

    points ~ a + b * ln(positional consensus rank)

then `build_board` computes VBD = predict(rank) - predict(replacement_rank).
The intercept cancels exactly:

    vbd(i) = (a + b*ln i) - (a + b*ln base) = b * ln(i / base)

so the ENTIRE board ordering is a function of four numbers -- b_QB, b_RB, b_WR,
b_TE -- and the four replacement ranks. That is why the slope question is the
board question and not a diagnostic curiosity.

LOOK-AHEAD POSTURE
------------------
Two separate universes, kept apart on purpose:

  * CONSENSUS-FIT curve (what the board ships). Needs `rankings`, so 2021-2025.
    Universe frozen from the pre-season consensus list (as_of_date late August,
    strictly before week 1). A ranked player with no stat line scores 0 and is
    RETAINED -- a bust is an outcome.
  * REALISED-FIT curve (value spread, no consensus needed). 1999-2024. Universe
    is every player with a realised finish inside RELEVANT_DEPTH that season.
    This is an order-statistic fit and is DELIBERATELY NOT a forecast; it is
    used only to ask whether positional value moved.

2025: its outcomes are read ONLY for the descriptive slope + interval in §1,
because the point estimate (-4) is already published in the repo
(docs/ideas-inbox.md:229, ADR-057) and the whole question is whether it is real.
2025 is EXCLUDED from every weighting / selection experiment (§3, §4). No model
choice in this file is made with knowledge of a 2025 outcome.

SURVIVORSHIP
------------
Consensus-fit universe is the pre-season list, frozen. Realised-fit universe is
by construction the top-N finishers, which IS a survivorship-shaped object -- it
is the definition of the value-spread curve, not a forecast, and is labelled as
such everywhere it appears.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
_SRC = REPO / "src"
for _p in (str(REPO), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import db as dbmod  # noqa: E402
from make_board import (  # noqa: E402
    RELEVANT_DEPTH,
    TRAINING_SOURCE,
    _consensus_board,
    _positional_ranks,
    _season_actual_points,
)
from scoring import ReplacementLevels, score_offensive_game  # noqa: E402

POSITIONS = ("QB", "RB", "WR", "TE")
CONSENSUS_SEASONS = (2021, 2022, 2023, 2024, 2025)
SEALED = 2025
REALISED_SEASONS = tuple(range(1999, 2025))  # 2025 excluded: sealed
SEED = 20260729


# --------------------------------------------------------------------------
# fitting
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Fit:
    slope: float
    intercept: float
    r2: float
    n: int
    se_ols: float
    se_hc3: float


def fit_log_rank(ranks: np.ndarray, points: np.ndarray) -> Optional[Fit]:
    """points ~ a + b ln(rank). Returns OLS and HC3 (heteroskedasticity-robust)
    standard errors on b -- point variance is far larger at the top of a
    position than at the bottom, so the classical SE understates."""
    if len(ranks) < 5:
        return None
    lr = np.log(np.asarray(ranks, dtype=float))
    y = np.asarray(points, dtype=float)
    X = np.column_stack([np.ones(len(lr)), lr])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta
    n, k = len(y), 2
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    sigma2 = ss_res / max(1, n - k)
    se_ols = float(np.sqrt(sigma2 * xtx_inv[1, 1]))
    # HC3
    h = np.einsum("ij,jk,ik->i", X, xtx_inv, X)
    omega = (resid / np.clip(1 - h, 1e-9, None)) ** 2
    meat = X.T @ (omega[:, None] * X)
    hc3 = xtx_inv @ meat @ xtx_inv
    return Fit(
        slope=float(beta[1]),
        intercept=float(beta[0]),
        r2=(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0,
        n=n,
        se_ols=se_ols,
        se_hc3=float(np.sqrt(max(hc3[1, 1], 0.0))),
    )


def boot_slope_ci(
    ranks: np.ndarray, points: np.ndarray, n_boot: int = 4000, seed: int = SEED
) -> Tuple[float, float]:
    """Percentile bootstrap on the slope, resampling PLAYERS within the season.

    Players are the resampling unit here because the estimand is a single
    season's fitted slope -- there is only one season, so there is nothing to
    resample at season level. Season-level resampling is used in §3/§4 where
    the estimand pools seasons (statistical-guardrails.md §7)."""
    rng = np.random.default_rng(seed)
    n = len(ranks)
    out = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        f = fit_log_rank(ranks[idx], points[idx])
        if f is not None:
            out.append(f.slope)
    if not out:
        return (float("nan"), float("nan"))
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def consensus_obs(
    conn: sqlite3.Connection, season: int, depth: Dict[str, int] = RELEVANT_DEPTH
) -> Dict[str, Tuple[np.ndarray, np.ndarray, List[str]]]:
    """{pos: (positional consensus rank, realised points, player names)}.
    Universe = the pre-season consensus list, frozen. Never-played = 0, kept."""
    actuals = _season_actual_points(conn, season)
    out = {}
    for pos, rows in _positional_ranks(
        _consensus_board(conn, season, source=TRAINING_SOURCE)
    ).items():
        lim = depth.get(pos)
        if lim is None:
            continue
        rr, pp, nn = [], [], []
        for i, r in enumerate(rows, start=1):
            if i > lim:
                break
            rr.append(i)
            pp.append(actuals.get(r["player_id"], 0.0))
            nn.append(r["player_name"] or r["player_id"])
        out[pos] = (np.array(rr, dtype=float), np.array(pp, dtype=float), nn)
    return out


_REALISED_CACHE: Dict[int, Dict[str, np.ndarray]] = {}


def realised_obs(
    conn: sqlite3.Connection, season: int, depth: Dict[str, int] = RELEVANT_DEPTH
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """{pos: (realised finish rank, points)}. Value-spread curve. 1999+.

    ORDER-STATISTIC FIT, NOT A FORECAST. Ranking players by the same points the
    curve then predicts is circular as a prediction exercise; it is the correct
    and only way to measure the *shape of the positional value distribution*,
    which is the quantity §2 needs. Labelled everywhere it is used."""
    if season not in _REALISED_CACHE:
        totals: Dict[str, float] = {}
        pos_of: Dict[str, Dict[str, int]] = {}
        for row in dbmod.actual_season_outcomes(conn, season):
            stats = {c: row[c] for c in dbmod.SCORING_STAT_COLUMNS}
            pid = row["player_id"]
            totals[pid] = totals.get(pid, 0.0) + score_offensive_game(stats)
            p = row["position"] if "position" in row.keys() else None
            if p:
                pos_of.setdefault(pid, {})
                pos_of[pid][p] = pos_of[pid].get(p, 0) + 1
        by_pos: Dict[str, List[float]] = {p: [] for p in POSITIONS}
        for pid, tot in totals.items():
            modes = pos_of.get(pid)
            if not modes:
                continue
            modal = max(modes.items(), key=lambda kv: kv[1])[0]
            if modal in by_pos:
                by_pos[modal].append(tot)
        _REALISED_CACHE[season] = {
            p: np.array(sorted(v, reverse=True), dtype=float) for p, v in by_pos.items()
        }
    cached = _REALISED_CACHE[season]
    out = {}
    for pos in POSITIONS:
        vals = cached.get(pos, np.array([]))
        lim = depth.get(pos, 0)
        vals = vals[:lim]
        out[pos] = (np.arange(1, len(vals) + 1, dtype=float), vals)
    return out


# --------------------------------------------------------------------------
# §1 / §2 -- per-season slopes with intervals
# --------------------------------------------------------------------------
def per_season_slopes(conn, kind: str, seasons: Sequence[int], depth=RELEVANT_DEPTH):
    rows = []
    for s in seasons:
        obs = consensus_obs(conn, s, depth) if kind == "consensus" else realised_obs(conn, s, depth)
        for pos in POSITIONS:
            got = obs.get(pos)
            if not got:
                continue
            r, y = got[0], got[1]
            f = fit_log_rank(r, y)
            if f is None:
                continue
            lo, hi = boot_slope_ci(r, y)
            rows.append(
                dict(kind=kind, season=s, pos=pos, slope=f.slope, intercept=f.intercept,
                     r2=f.r2, n=f.n, se_ols=f.se_ols, se_hc3=f.se_hc3,
                     boot_lo=lo, boot_hi=hi, mean_pts=float(y.mean()))
            )
    return rows


def trend_test(seasons: Sequence[int], slopes: Sequence[float], ses: Sequence[float],
               n_boot: int = 20000, seed: int = SEED):
    """Is the slope series trending? Two answers.

    (a) inverse-variance weighted OLS of slope on season, with the CI obtained
        by parametric resampling of each season's slope from N(slope, se) --
        this propagates the (large) per-season estimation error, which a plain
        regression of 5 point estimates ignores entirely.
    (b) exact permutation p on Spearman rho of (season, slope) -- 5! = 120
        orderings, so the smallest attainable two-sided p is 2/120 = 0.0167.
        A perfectly monotone 5-point series CANNOT reach p<0.0167. Stated so
        the reader knows the floor, not to dress the result up.
    """
    x = np.asarray(seasons, dtype=float)
    b = np.asarray(slopes, dtype=float)
    se = np.asarray(ses, dtype=float)
    xc = x - x.mean()
    point = float((xc @ (b - b.mean())) / (xc @ xc))
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        bb = rng.normal(b, se)
        draws.append(float((xc @ (bb - bb.mean())) / (xc @ xc)))
    lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
    # permutation on Spearman: EXACT for n<=8 (5!=120 for the consensus
    # series), sampled for the 26-season realised series where n! is
    # astronomical. p_floor is reported because a 5-point series cannot reach
    # p<2/120=0.0167 no matter how perfectly monotone it is.
    from itertools import permutations
    from scipy.stats import spearmanr
    obs_rho = float(spearmanr(x, b).statistic)
    n = len(b)
    if n <= 8:
        perms = [list(p) for p in permutations(range(n))]
        n_perm = len(perms)
    else:
        n_perm = 20000
        perms = [rng.permutation(n) for _ in range(n_perm)]
    rhos = np.array([float(spearmanr(x, b[p]).statistic) for p in perms])
    p_perm = float(np.mean(np.abs(rhos) >= abs(obs_rho) - 1e-12))
    return dict(slope_per_season=point, ci=(lo, hi), rho=obs_rho, p_perm=p_perm,
                p_floor=2.0 / n_perm)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(REPO / "data" / "nfl.db"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    result: Dict[str, object] = {}

    print("=" * 78)
    print("SECTION 1/2 -- per-season fitted slopes, consensus-rank curve (the board's)")
    print("=" * 78)
    cons = per_season_slopes(conn, "consensus", CONSENSUS_SEASONS)
    result["consensus_slopes"] = cons
    for pos in POSITIONS:
        sub = [r for r in cons if r["pos"] == pos]
        print(f"\n{pos}  (depth {RELEVANT_DEPTH[pos]})")
        print("  season   slope   [boot 95%]        se_ols  se_hc3    R2   meanPts")
        for r in sub:
            tag = "  <-- SEALED, descriptive only" if r["season"] == SEALED else ""
            print(f"   {r['season']}  {r['slope']:+7.1f}  [{r['boot_lo']:+7.1f},{r['boot_hi']:+7.1f}]"
                  f"  {r['se_ols']:6.1f} {r['se_hc3']:6.1f}  {r['r2']:.3f} {r['mean_pts']:7.1f}{tag}")
        t = trend_test([r["season"] for r in sub], [r["slope"] for r in sub],
                       [r["se_hc3"] for r in sub])
        print(f"  TREND slope-of-slopes {t['slope_per_season']:+.2f}/season "
              f"[{t['ci'][0]:+.2f},{t['ci'][1]:+.2f}]  spearman rho={t['rho']:+.2f} "
              f"p_perm={t['p_perm']:.4f} (floor {t['p_floor']:.4f})")
        result[f"trend_consensus_{pos}"] = t
        # 2021-2024 only (sealed season removed) -- the selection-safe window
        sub4 = [r for r in sub if r["season"] != SEALED]
        t4 = trend_test([r["season"] for r in sub4], [r["slope"] for r in sub4],
                        [r["se_hc3"] for r in sub4])
        print(f"  TREND 2021-2024 only  {t4['slope_per_season']:+.2f}/season "
              f"[{t4['ci'][0]:+.2f},{t4['ci'][1]:+.2f}]  p_perm={t4['p_perm']:.4f} "
              f"(floor {t4['p_floor']:.4f})")
        result[f"trend_consensus_2124_{pos}"] = t4

    print()
    print("=" * 78)
    print("SECTION 2b -- realised-finish-rank curve (value spread), 1999-2024")
    print("ORDER-STATISTIC FIT. Not a forecast. Measures the shape of the value")
    print("distribution only.")
    print("=" * 78)
    real = per_season_slopes(conn, "realised", REALISED_SEASONS)
    result["realised_slopes"] = real
    for pos in POSITIONS:
        sub = [r for r in real if r["pos"] == pos]
        eras = [(1999, 2007), (2008, 2015), (2016, 2020), (2021, 2024)]
        parts = []
        for a, b in eras:
            v = [r["slope"] for r in sub if a <= r["season"] <= b]
            parts.append(f"{a}-{b}: {np.mean(v):+6.1f}")
        print(f"{pos}  " + "   ".join(parts))
        recent = [r for r in sub if r["season"] >= 2021]
        print("      2021-2024 per season: " + "  ".join(
            f"{r['season']}:{r['slope']:+6.1f}[{r['boot_lo']:+6.1f},{r['boot_hi']:+6.1f}]"
            for r in recent))
        t = trend_test([r["season"] for r in sub], [r["slope"] for r in sub],
                       [r["se_hc3"] for r in sub], n_boot=4000)
        print(f"      full-sample trend {t['slope_per_season']:+.3f}/season "
              f"[{t['ci'][0]:+.3f},{t['ci'][1]:+.3f}]")
        result[f"trend_realised_{pos}"] = t

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=1, default=float))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
