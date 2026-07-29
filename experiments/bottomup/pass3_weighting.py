"""Pass 3, parts 3 and 4 -- what weighting a holdout supports, and what the flat
fit costs in board positions.

EXPLORATORY. No result here is registered or corrected for multiplicity.

THE TWO WEIGHTING QUESTIONS ARE NOT THE SAME QUESTION
-----------------------------------------------------
Q3a  The board's own curve: E[points | pre-season CONSENSUS rank]. Needs
     `rankings`, so training seasons come from 2021-2025 and evaluable targets
     from 2022-2024 (2025 sealed). A weighting scheme needs >=2 training
     seasons, so the evaluable targets are 2023 and 2024. n = 2. This is
     reported because it is the decision-relevant object, and its n is reported
     louder because n = 2 selects nothing.

Q3b  The value-spread curve: E[points | REALISED finish rank]. Needs no
     consensus, so 1999-2024 -- 20+ evaluable targets and a real train/test
     split. This answers CLAUDE.md 6.4's "how far back to weight, per position"
     for the component that CAN be tested, and bounds how much of the board's
     slope movement could be a genuine value regime.

Q3a and Q3b differ by the consensus-skill attenuation factor. Both are
reported; neither is presented as the other.

LOOK-AHEAD
----------
Every evaluation is strictly out of sample: for target N, training uses seasons
<= N-1 only, asserted at the call site. 2025 is never a target and never
contributes to any selection. Section 4 builds 2026 boards, whose training
window (2021-2025) is entirely prior to 2026 and is what the shipped board
already uses -- no outcome after 2025 exists to leak.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
_SRC = REPO / "src"
for _p in (str(REPO), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import make_board as mb  # noqa: E402
from scoring import ReplacementLevels  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pass3_rank_curve_regimes import (  # noqa: E402
    POSITIONS,
    RELEVANT_DEPTH,
    consensus_obs,
    fit_log_rank,
    realised_obs,
)

SEED = 20260729
SEALED = 2025


# --------------------------------------------------------------------------
# weighted fit
# --------------------------------------------------------------------------
def weighted_fit(
    per_season: Dict[int, Tuple[np.ndarray, np.ndarray]], weights: Dict[int, float]
) -> Optional[Tuple[float, float]]:
    """Weighted least squares of points ~ a + b ln(rank), pooling seasons with
    per-season weight w_s applied to every observation in that season.

    Weighting seasons (not observations) is the point: a season with 60 WRs and
    a season with 20 QBs must not have their relative influence set by roster
    depth. Weights are normalised so each season contributes w_s / n_s per
    observation -- i.e. every season carries equal total mass before the recency
    weight is applied."""
    xs, ys, ws = [], [], []
    for s, (r, y) in per_season.items():
        w = weights.get(s, 0.0)
        if w <= 0 or len(r) < 2:
            continue
        xs.append(np.log(r))
        ys.append(y)
        ws.append(np.full(len(r), w / len(r)))
    if not xs:
        return None
    lr = np.concatenate(xs)
    y = np.concatenate(ys)
    w = np.concatenate(ws)
    if len(lr) < 5:
        return None
    X = np.column_stack([np.ones(len(lr)), lr])
    W = w
    xtwx = X.T @ (W[:, None] * X)
    beta = np.linalg.solve(xtwx, X.T @ (W * y))
    return float(beta[0]), float(beta[1])


def scheme_weights(scheme: str, train: Sequence[int], target: int) -> Dict[int, float]:
    """Recency schemes. `age` = target - season, so age 1 is last season."""
    out = {}
    for s in train:
        age = target - s
        if scheme == "flat":
            w = 1.0
        elif scheme.startswith("last"):
            k = int(scheme[4:])
            w = 1.0 if age <= k else 0.0
        elif scheme.startswith("hl"):
            h = float(scheme[2:])
            w = 0.5 ** ((age - 1) / h)
        else:
            raise ValueError(scheme)
        out[s] = w
    return out


SCHEMES = ["flat", "last1", "last2", "last3", "last5", "last8", "last12",
           "hl1", "hl2", "hl3", "hl5", "hl10"]


# --------------------------------------------------------------------------
# Q3b -- value-spread curve, deep sample
# --------------------------------------------------------------------------
def q3b(conn, first_target=2005, split=2016, out=None):
    """For each target season, fit the value curve on prior seasons under each
    scheme, predict the target season's realised points at each finish rank,
    score RMSE. Universe for the target is that season's realised top-N -- an
    order-statistic evaluation, deliberately, because the estimand is the shape
    of the value distribution and not a player forecast."""
    seasons = list(range(1999, 2025))
    cache = {s: realised_obs(conn, s) for s in seasons}
    rows = []
    for target in range(first_target, 2025):
        train = [s for s in seasons if s < target]
        assert max(train) < target
        for pos in POSITIONS:
            r_t, y_t = cache[target][pos]
            if len(r_t) < 5:
                continue
            per_season = {s: cache[s][pos] for s in train}
            for sch in SCHEMES:
                w = scheme_weights(sch, train, target)
                fit = weighted_fit(per_season, w)
                if fit is None:
                    continue
                a, b = fit
                pred = a + b * np.log(r_t)
                rmse = float(np.sqrt(np.mean((pred - y_t) ** 2)))
                rows.append(dict(target=target, pos=pos, scheme=sch, rmse=rmse,
                                 slope=b, actual_slope=float(fit_log_rank(r_t, y_t).slope)))
    return rows, split


def summarise_q3b(rows, split, label, seasons_filter=None):
    out = {}
    for pos in POSITIONS:
        sub = [r for r in rows if r["pos"] == pos and
               (seasons_filter is None or seasons_filter(r["target"]))]
        targets = sorted({r["target"] for r in sub})
        by = {sch: np.array([next(r["rmse"] for r in sub if r["target"] == t and r["scheme"] == sch)
                             for t in targets]) for sch in SCHEMES}
        base = by["flat"]
        rng = np.random.default_rng(SEED)
        res = []
        for sch in SCHEMES:
            d = by[sch] - base  # negative = better than flat
            draws = []
            for _ in range(4000):
                idx = rng.integers(0, len(d), len(d))
                draws.append(float(d[idx].mean()))
            res.append((sch, float(by[sch].mean()), float(d.mean()),
                        float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))))
        out[pos] = dict(n_targets=len(targets), rows=res)
    return out


# --------------------------------------------------------------------------
# Q3a -- the board's own curve
# --------------------------------------------------------------------------
def q3a(conn):
    """Target seasons 2022-2024. Predict each consensus-ranked player's realised
    points from a curve fitted on prior consensus seasons under each scheme.

    Two metrics:
      rmse   -- points error, what the curve nominally estimates
      tau_b  -- Kendall tau of the INDUCED CROSS-POSITIONAL BOARD (vbd =
                b_pos * ln(rank/base_pos)) against the realised VBD ordering.
                This is the metric that matches what the board is for; RMSE can
                improve while the ordering does not move at all, because the
                intercept cancels out of VBD entirely."""
    from scipy.stats import kendalltau

    train_pool = [2021, 2022, 2023, 2024]
    cache = {s: consensus_obs(conn, s) for s in train_pool}
    base = ReplacementLevels().baselines()
    rows = []
    for target in (2022, 2023, 2024):
        train = [s for s in train_pool if s < target]
        assert max(train) < target
        # realised VBD ordering for the target season's consensus universe
        obs_t = cache[target]
        for sch in SCHEMES:
            if sch.startswith("last") and int(sch[4:]) > len(train):
                continue
            curves = {}
            for pos in POSITIONS:
                per_season = {s: (cache[s][pos][0], cache[s][pos][1]) for s in train}
                w = scheme_weights(sch, train, target)
                f = weighted_fit(per_season, w)
                if f:
                    curves[pos] = f
            if len(curves) < 4:
                continue
            preds, actual, sqerr, n = [], [], 0.0, 0
            for pos in POSITIONS:
                a, b = curves[pos]
                r, y, _ = obs_t[pos]
                p = a + b * np.log(r)
                sqerr += float(((p - y) ** 2).sum())
                n += len(y)
                repl_pred = a + b * np.log(base[pos])
                preds.extend((p - repl_pred).tolist())
                # realised VBD for the same players, using the same replacement
                # rank measured on that season's realised points within the
                # consensus universe (an evaluation quantity, target season)
                srt = np.sort(y)[::-1]
                bidx = min(int(base[pos]) - 1, len(srt) - 1)
                actual.extend((y - srt[bidx]).tolist())
            tau = float(kendalltau(preds, actual).statistic)
            rows.append(dict(target=target, scheme=sch, rmse=float(np.sqrt(sqerr / n)),
                             tau=tau, slopes={p: curves[p][1] for p in POSITIONS}))
    return rows


# --------------------------------------------------------------------------
# Section 4 -- what the flat fit costs in board positions
# --------------------------------------------------------------------------
def section4(conn, out=None):
    """Build the real 2026 board under flat pooling (shipped) and under each
    recency scheme, and count movement. Uses src.make_board's own board
    construction so the object measured is the shipped one, with only the curve
    fit swapped."""
    train = [2021, 2022, 2023, 2024, 2025]
    cache = {s: consensus_obs(conn, s) for s in train}
    base = ReplacementLevels().baselines()
    live = mb._positional_ranks(mb._consensus_board(conn, 2026, source=mb.SOURCE))

    def board_for(scheme: str):
        curves = {}
        for pos in POSITIONS:
            per_season = {s: (cache[s][pos][0], cache[s][pos][1]) for s in train}
            f = weighted_fit(per_season, scheme_weights(scheme, train, 2026))
            if f:
                curves[pos] = f
        scored = []
        for pos, rws in live.items():
            if pos not in curves:
                continue
            a, b = curves[pos]
            for i, r in enumerate(rws, start=1):
                vbd = b * (np.log(i) - np.log(base[pos]))
                scored.append((vbd, r["player_name"] or r["player_id"], pos, i,
                               r["adp_rank"]))
        scored.sort(key=lambda t: -t[0])
        return {f"{s[1]}|{s[2]}": (n, s[0], s[3], s[4])
                for n, s in enumerate(scored, start=1)}, curves

    flat, flat_curves = board_for("flat")
    result = {"flat_slopes": {p: flat_curves[p][1] for p in POSITIONS}, "schemes": {}}
    for sch in ["last1", "last2", "last3", "hl1", "hl2", "hl3", "hl5"]:
        b, curves = board_for(sch)
        moves = []
        for k, (rank_f, vbd_f, pr, cr) in flat.items():
            if k not in b:
                continue
            rank_n = b[k][0]
            moves.append((k, rank_f, rank_n, rank_n - rank_f, pr, cr))
        top150 = [m for m in moves if m[1] <= 150]
        d = np.array([abs(m[3]) for m in top150], dtype=float)
        # positional composition of the top 100 under each
        comp_f = {}
        comp_n = {}
        for k, (rk, _, _, _) in flat.items():
            if rk <= 100:
                comp_f[k.split("|")[1]] = comp_f.get(k.split("|")[1], 0) + 1
        for k, v in b.items():
            if v[0] <= 100:
                comp_n[k.split("|")[1]] = comp_n.get(k.split("|")[1], 0) + 1
        biggest = sorted(top150, key=lambda m: -abs(m[3]))[:12]
        result["schemes"][sch] = dict(
            slopes={p: curves[p][1] for p in POSITIONS},
            n_top150=len(top150),
            n_moved=int((d > 0).sum()),
            n_moved_ge5=int((d >= 5).sum()),
            n_moved_ge10=int((d >= 10).sum()),
            n_moved_ge25=int((d >= 25).sum()),
            median_abs=float(np.median(d)),
            p90_abs=float(np.percentile(d, 90)),
            max_abs=float(d.max()) if len(d) else 0.0,
            comp_flat_top100=comp_f, comp_new_top100=comp_n,
            biggest=[(m[0], m[1], m[2], m[3]) for m in biggest],
        )
    return result


def pooled_slope_ci(conn, train, n_boot=4000, seed=SEED):
    """Season-level bootstrap CI on the POOLED (flat) slope -- the shipped
    board's own uncertainty, resampling seasons exactly as
    make_board.bootstrap_vbd_intervals does. If the pooled slope's own interval
    already spans the reweighted values, reweighting moves inside noise."""
    cache = {s: consensus_obs(conn, s) for s in train}
    rng = np.random.default_rng(seed)
    out = {}
    for pos in POSITIONS:
        draws = []
        for _ in range(n_boot):
            picks = rng.choice(train, size=len(train), replace=True)
            rr, yy = [], []
            for s in picks:
                r, y, _ = cache[int(s)][pos]
                rr.append(r)
                yy.append(y)
            f = fit_log_rank(np.concatenate(rr), np.concatenate(yy))
            if f:
                draws.append(f.slope)
        pt = fit_log_rank(
            np.concatenate([cache[s][pos][0] for s in train]),
            np.concatenate([cache[s][pos][1] for s in train]),
        )
        out[pos] = (pt.slope, float(np.percentile(draws, 2.5)),
                    float(np.percentile(draws, 97.5)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(REPO / "data" / "nfl.db"))
    ap.add_argument("--section", default="all")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    res = {}

    if args.section in ("all", "3b"):
        print("=" * 78)
        print("Q3b -- VALUE-SPREAD curve (realised finish rank), deep sample")
        print("RMSE of predicted season-N value curve, by recency scheme.")
        print("negative delta = BETTER than flat pooling of all prior seasons")
        print("=" * 78)
        rows, split = q3b(conn)
        for label, filt in (("TRAIN targets 2005-2015", lambda t: t <= 2015),
                            ("TEST  targets 2016-2024", lambda t: t >= 2016)):
            print(f"\n--- {label} ---")
            s = summarise_q3b(rows, split, label, filt)
            for pos in POSITIONS:
                d = s[pos]
                print(f"\n{pos}  (n targets = {d['n_targets']})")
                print("   scheme     RMSE   d vs flat   [season-boot 95%]")
                for sch, rmse, dd, lo, hi in d["rows"]:
                    star = "  *" if hi < 0 else ""
                    print(f"   {sch:<8} {rmse:7.2f}   {dd:+8.2f}   [{lo:+7.2f},{hi:+7.2f}]{star}")
            res[f"q3b_{label[:5].strip()}"] = s

    if args.section in ("all", "3a"):
        print()
        print("=" * 78)
        print("Q3a -- THE BOARD'S OWN curve (consensus rank). n targets = 3,")
        print("and only 2 of them (2023, 2024) have >1 training season, so no")
        print("scheme can be selected here. Printed for the record, not to pick.")
        print("=" * 78)
        rows = q3a(conn)
        for target in (2022, 2023, 2024):
            sub = [r for r in rows if r["target"] == target]
            print(f"\ntarget {target}  (train {[s for s in (2021,2022,2023) if s < target]})")
            print("   scheme     RMSE    tau_b(board vs realised VBD)   bQB    bRB    bWR    bTE")
            for r in sub:
                s = r["slopes"]
                print(f"   {r['scheme']:<8} {r['rmse']:7.2f}   {r['tau']:+.4f}"
                      f"                    {s['QB']:+6.1f} {s['RB']:+6.1f} "
                      f"{s['WR']:+6.1f} {s['TE']:+6.1f}")
        res["q3a"] = rows

    if args.section in ("all", "4"):
        print()
        print("=" * 78)
        print("SECTION 4 -- what flat pooling costs in BOARD POSITIONS (2026 board)")
        print("=" * 78)
        train = [2021, 2022, 2023, 2024, 2025]
        ci = pooled_slope_ci(conn, train)
        print("\nShipped pooled slope, season-level bootstrap 95% CI")
        print("(the board's own resampling unit, make_board.bootstrap_vbd_intervals):")
        for pos in POSITIONS:
            pt, lo, hi = ci[pos]
            print(f"   {pos}  {pt:+7.1f}  [{lo:+7.1f}, {hi:+7.1f}]   width {hi-lo:6.1f}")
        res["pooled_ci"] = ci
        s4 = section4(conn)
        print("\nflat (shipped) slopes: " + "  ".join(
            f"{p}={s4['flat_slopes'][p]:+.1f}" for p in POSITIONS))
        for sch, d in s4["schemes"].items():
            print(f"\n--- {sch} ---")
            print("   slopes: " + "  ".join(f"{p}={d['slopes'][p]:+.1f}" for p in POSITIONS))
            print(f"   top-150: {d['n_moved']}/{d['n_top150']} move at all; "
                  f">=5: {d['n_moved_ge5']}  >=10: {d['n_moved_ge10']}  >=25: {d['n_moved_ge25']}")
            print(f"   |move| median {d['median_abs']:.0f}  p90 {d['p90_abs']:.0f}  "
                  f"max {d['max_abs']:.0f}")
            print(f"   top-100 composition  flat {d['comp_flat_top100']}  ->  {d['comp_new_top100']}")
            print("   biggest movers: " + ", ".join(
                f"{k.split('|')[0]} {a}->{b}" for k, a, b, _ in d["biggest"][:8]))
        res["section4"] = s4

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1, default=float))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
