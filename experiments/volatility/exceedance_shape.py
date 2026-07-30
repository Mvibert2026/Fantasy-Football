"""Does the SHAPE of a player's per-game yardage distribution -- its skewness and
kurtosis -- improve the exceedance curve beyond his mean?

WHY THIS IS NOT A RE-RUN OF `exceedance_dispersion.py`. That module tested the
SECOND moment and returned a decisive null. This tests the THIRD and FOURTH.
The distinction is load-bearing: two players can share a mean AND a standard
deviation while one is symmetric and the other carries a long right tail. A
threshold bonus at 100/150/200 yards is paid on the upper tail, and SD cannot
tell those two players apart.

The dispersion null is itself the argument for running this. If the mean fully
determined the exceedance curve, dispersion would have been redundant -- which is
what was measured. But right skew puts mass above a high threshold that a
symmetric distribution with identical mean and SD does not. So skew is the moment
that could still carry information the mean does not already contain, and the
TOP threshold in each family (200 rushing/receiving, 400 passing) is where it
should appear first if it appears at all, because that is where shape matters
more than centre.

ESTIMATORS -- named, because there are several conventions
-----------------------------------------------------------
  g1, g2      the SAMPLE (biased, method-of-moments) coefficients
              g1 = m3 / m2^(3/2),  g2 = m4 / m2^2 - 3   (Fisher's excess kurtosis,
              i.e. 0 for a Gaussian, not 3)
  G1, G2      the ADJUSTED Fisher-Pearson coefficients -- the bias-corrected forms
              (`scipy.stats.skew/kurtosis(bias=False)`; SAS/Excel's SKEW/KURT)
              G1 = g1 * sqrt(n(n-1))/(n-2)
              G2 = ((n+1) * g2 + 6) * (n-1)/((n-2)(n-3))

**G1/G2 are the primary.** At n ~ 17 the bias in g1/g2 is not negligible and
these are per-player estimates, so a bias that scales with n would be correlated
with games played -- which is itself correlated with everything. g1/g2 are run as
a declared sensitivity and both are reported.

SHRINKAGE -- derived, not chosen
---------------------------------
Third and fourth moments from ~17 games are very noisy: Var(G1) ~ 6/n and
Var(G2) ~ 24/n, so kurtosis is roughly four times noisier than skew at the same n
and both are far noisier than the SD the dispersion test used.

Two steps, in this order:

  1. RESIDUALISE against log mean ypg, within (family, position, season). Yardage
     is bounded below by zero, so a low-volume player's distribution is
     right-skewed almost by construction; without this the "skew" covariate would
     partly re-encode the mean, which is already in the design matrix.
  2. EMPIRICAL-BAYES shrink toward 0 (which after step 1 is the group mean, not an
     assumed value). w_i = tau^2 / (tau^2 + v_i), with v_i the exact
     normal-theory sampling variance of that estimator at that player's n, and
     tau^2 = max(0, Var(residual) - mean(v_i)) estimated from the data.
     **No hand-picked constant.** The n/(n+k) form used by the dispersion test is
     run as a declared sensitivity over k in {0, 8, 16, 32}.

ARMS (separate, as well as together -- if skew carries signal and kurtosis does
not, that is a cleaner finding than a combined term)
  base    [1, log1p(ypg)]                       -- the shipped design
  skew    [1, log1p(ypg), skew_(N-1)]
  kurt    [1, log1p(ypg), kurt_(N-1)]
  both    [1, log1p(ypg), skew_(N-1), kurt_(N-1)]
  ORACLE  [1, log1p(ypg), skew_N, kurt_N]       -- CIRCULAR ON PURPOSE, target
          season's own shape. Not a result: a BOUND. If the oracle cannot buy
          much, no honest version can, and the null is bounded rather than merely
          unfound.

GUARDRAILS
  - Prior-season moments only in every non-oracle arm.
  - Walk-forward: for target season N the GLM is fitted on rows with season < N.
    Never training fit.
  - Both arms get the player's REALISED mean ypg for the target season -- the most
    favourable setting that exists, so a null is decisive.
  - Sealed 2025 holdout excluded in code.

Run:
    .venv/bin/python -m experiments.volatility.exceedance_shape
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import db  # noqa: E402
from experiments.bottomup.components.pos_model import binom_glm  # noqa: E402
from experiments.volatility.exceedance_dispersion import (  # noqa: E402
    FAMILIES, MIN_GAMES, HOLDOUT_SEASON, FIRST_SEASON, RNG_SEED,
    _grade, _boot_mean, _paired_season_delta, _logloss)

DB_PATH = REPO / "data" / "nfl.db"

MOMENTS = ("skew", "kurt")
ARMS = ("base", "skew", "kurt", "both", "oracle")
NK_SWEEP = (0.0, 8.0, 16.0, 32.0)   # sensitivity only; primary is empirical Bayes


# ------------------------------------------------------------------- estimators
def moments(a: np.ndarray, adjusted: bool = True) -> Tuple[float, float]:
    """(skewness, excess kurtosis). `adjusted=True` -> G1/G2 (Fisher-Pearson,
    bias-corrected). `adjusted=False` -> g1/g2 (sample/method-of-moments).
    Excess kurtosis convention throughout: Gaussian = 0."""
    n = len(a)
    if n < 4:
        return float("nan"), float("nan")
    m = a.mean()
    d = a - m
    m2 = (d ** 2).mean()
    if m2 <= 0:
        return float("nan"), float("nan")
    g1 = (d ** 3).mean() / m2 ** 1.5
    g2 = (d ** 4).mean() / m2 ** 2 - 3.0
    if not adjusted:
        return float(g1), float(g2)
    G1 = g1 * math.sqrt(n * (n - 1)) / (n - 2)
    G2 = ((n + 1) * g2 + 6) * (n - 1) / ((n - 2) * (n - 3))
    return float(G1), float(G2)


def sampling_var(kind: str, n: int) -> float:
    """Exact normal-theory sampling variance of the ADJUSTED estimator at n.

    These are the standard expressions (the ones behind the familiar 6/n and
    24/n approximations); using the exact forms rather than 6/n and 24/n matters
    here because n varies from 8 to 17 across the panel and the approximations
    are poor at the bottom of that range."""
    n = float(n)
    if kind == "skew":
        if n < 4:
            return float("inf")
        return 6.0 * n * (n - 1) / ((n - 2) * (n + 1) * (n + 3))
    if n < 5:
        return float("inf")
    return 24.0 * n * (n - 1) ** 2 / ((n - 3) * (n - 2) * (n + 3) * (n + 5))


# ------------------------------------------------------------------------ data
@dataclass
class Row:
    season: int
    player_id: str
    position: str
    family: str
    games: int
    mean_ypg: float
    clears: Dict[int, int]
    raw: Dict[str, float] = field(default_factory=dict)      # G1/G2 (or g1/g2)
    resid: Dict[str, float] = field(default_factory=dict)    # after step 1
    shrunk: Dict[str, float] = field(default_factory=dict)   # after step 2
    prior: Dict[str, float] = field(default_factory=dict)    # season N-1's shrunk
    own: Dict[str, float] = field(default_factory=dict)      # own season, ORACLE only


def load(conn: sqlite3.Connection, adjusted: bool) -> List[Row]:
    out: List[Row] = []
    for season in range(FIRST_SEASON, HOLDOUT_SEASON):
        per: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for pid, pos, ry, rushy, py in conn.execute(
                "SELECT player_id, position, COALESCE(receiving_yards,0), "
                "COALESCE(rushing_yards,0), COALESCE(passing_yards,0) "
                "FROM player_weekly_stats WHERE season=? AND season_type='REG'", (season,)):
            pos_counts[pid][pos] += 1
            per[(pid, "rec")].append(float(ry))
            per[(pid, "rush")].append(float(rushy))
            per[(pid, "pass")].append(float(py))
        modal = {pid: max(c.items(), key=lambda kv: kv[1])[0] for pid, c in pos_counts.items()}
        for (pid, fam), vals in per.items():
            cfg = FAMILIES[fam]
            pos = modal.get(pid)
            if pos not in cfg["positions"] or len(vals) < MIN_GAMES:
                continue
            a = np.array(vals)
            mean = float(a.mean())
            if mean < cfg["min_ypg"]:
                continue
            sk, ku = moments(a, adjusted=adjusted)
            if math.isnan(sk) or math.isnan(ku):
                continue
            out.append(Row(season, pid, pos, fam, len(a), mean,
                           {t: int((a >= t).sum()) for t in cfg["thresholds"]},
                           raw={"skew": sk, "kurt": ku}))
    return out


def residualise(rows: List[Row]) -> None:
    """Step 1. Each moment on log(mean ypg), within (family, position, season).
    Yardage is bounded below by zero, so a low-volume player is right-skewed
    almost mechanically; leaving that in would re-encode the mean."""
    groups: Dict[Tuple[str, str, int], List[Row]] = defaultdict(list)
    for r in rows:
        groups[(r.family, r.position, r.season)].append(r)
    for grp in groups.values():
        xs = [math.log(r.mean_ypg) for r in grp if r.mean_ypg > 0]
        keep = [r for r in grp if r.mean_ypg > 0]
        if len(keep) < 10:
            for r in grp:
                for m in MOMENTS:
                    r.resid[m] = float("nan")
            continue
        mx = statistics.fmean(xs)
        den = sum((x - mx) ** 2 for x in xs)
        for m in MOMENTS:
            ys = [r.raw[m] for r in keep]
            my = statistics.fmean(ys)
            b = (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den) if den else 0.0
            a0 = my - b * mx
            for r, x, y in zip(keep, xs, ys):
                r.resid[m] = y - (a0 + b * x)


def shrink_eb(rows: List[Row]) -> Dict[str, Dict[str, float]]:
    """Step 2, PRIMARY. Empirical-Bayes toward 0 (the group mean after step 1),
    with no hand-picked constant. Returns the fitted tau^2 and mean weight per
    (family, moment) so the shrinkage is auditable rather than implicit."""
    groups: Dict[Tuple[str, str], List[Row]] = defaultdict(list)
    for r in rows:
        groups[(r.family, r.position)].append(r)
    report: Dict[str, Dict[str, float]] = defaultdict(dict)
    for (fam, pos), grp in groups.items():
        for m in MOMENTS:
            vals = [r.resid[m] for r in grp if not math.isnan(r.resid.get(m, float("nan")))]
            if len(vals) < 20:
                for r in grp:
                    r.shrunk[m] = 0.0
                continue
            vs = [sampling_var(m, r.games) for r in grp]
            tau2 = max(0.0, statistics.pvariance(vals) - statistics.fmean(vs))
            ws = []
            for r, v in zip(grp, vs):
                w = tau2 / (tau2 + v) if (tau2 + v) > 0 else 0.0
                rr = r.resid.get(m, float("nan"))
                r.shrunk[m] = 0.0 if math.isnan(rr) else w * rr
                ws.append(w)
            report[f"{fam}:{pos}"][f"{m}_tau2"] = tau2
            report[f"{fam}:{pos}"][f"{m}_mean_weight"] = statistics.fmean(ws)
    return dict(report)


def shrink_nk(rows: List[Row], k: float) -> None:
    """Sensitivity form: the n/(n+k) shrinkage the dispersion test used."""
    for r in rows:
        w = r.games / (r.games + k) if (r.games + k) > 0 else 1.0
        for m in MOMENTS:
            rr = r.resid.get(m, float("nan"))
            r.shrunk[m] = 0.0 if math.isnan(rr) else w * rr


def attach_prior(rows: List[Row]) -> List[Row]:
    by_key = {(r.player_id, r.family, r.season): r for r in rows}
    out = []
    for r in rows:
        p = by_key.get((r.player_id, r.family, r.season - 1))
        if p is None:
            continue
        r.prior = dict(p.shrunk)
        r.own = dict(r.shrunk)          # ORACLE arm only
        out.append(r)
    return out


# ------------------------------------------------------------------- modelling
def design(rows: Sequence[Row], arm: str) -> np.ndarray:
    ypg = np.array([r.mean_ypg for r in rows])
    cols = [np.ones(len(rows)), np.log1p(np.clip(ypg, 0, None))]
    if arm in ("skew", "both"):
        cols.append(np.array([r.prior["skew"] for r in rows]))
    if arm in ("kurt", "both"):
        cols.append(np.array([r.prior["kurt"] for r in rows]))
    if arm == "oracle":
        cols.append(np.array([r.own["skew"] for r in rows]))
        cols.append(np.array([r.own["kurt"] for r in rows]))
    return np.column_stack(cols)


def walk_forward(rows: List[Row], fam: str) -> Dict:
    cfg = FAMILIES[fam]
    sub = sorted([r for r in rows if r.family == fam], key=lambda r: r.season)
    seasons = sorted({r.season for r in sub})
    res: Dict = {"n_rows": len(sub), "thresholds": {}, "bonus_points_mae": {},
                 "coefficients": {}}

    ll: Dict[str, Dict[int, Dict[int, List[float]]]] = {
        a: defaultdict(lambda: defaultdict(list)) for a in ARMS}
    bonus_err: Dict[str, Dict[int, List[float]]] = {a: defaultdict(list) for a in ARMS}
    coef: Dict[str, Dict[int, float]] = {"skew": {}, "kurt": {}}

    for target in seasons:
        train = [r for r in sub if r.season < target]
        test = [r for r in sub if r.season == target]
        if len(train) < 200 or not test:
            continue
        tri_te = np.array([r.games for r in test], dtype=float)
        exp_b: Dict[str, np.ndarray] = {a: np.zeros(len(test)) for a in ARMS}
        actual = np.zeros(len(test))
        for t in cfg["thresholds"]:
            succ_tr = np.array([r.clears[t] for r in train], dtype=float)
            tri_tr = np.array([r.games for r in train], dtype=float)
            succ_te = np.array([r.clears[t] for r in test], dtype=float)
            actual += succ_te * cfg["bonus"][t]
            for arm in ARMS:
                beta = binom_glm(design(train, arm), succ_tr, tri_tr)
                p = 1.0 / (1.0 + np.exp(-np.clip(design(test, arm) @ beta, -30, 30)))
                ll[arm][t][target].extend((_logloss(p, succ_te, tri_te) / tri_te).tolist())
                exp_b[arm] += p * tri_te * cfg["bonus"][t]
                if t == cfg["thresholds"][-1]:          # TOP threshold: the one that matters
                    if arm == "skew":
                        coef["skew"][target] = float(beta[2])
                    elif arm == "kurt":
                        coef["kurt"][target] = float(beta[2])
        for arm in ARMS:
            bonus_err[arm][target].extend(np.abs(exp_b[arm] - actual).tolist())

    for t in cfg["thresholds"]:
        entry = {"base": statistics.fmean(v for vs in ll["base"][t].values() for v in vs)}
        for arm in ARMS:
            if arm == "base":
                continue
            entry[arm] = statistics.fmean(v for vs in ll[arm][t].values() for v in vs)
            entry[f"delta_{arm}"] = _paired_season_delta(ll[arm][t], ll["base"][t])
        res["thresholds"][t] = entry

    entry = {"base": statistics.fmean(v for vs in bonus_err["base"].values() for v in vs)}
    for arm in ARMS:
        if arm == "base":
            continue
        entry[arm] = statistics.fmean(v for vs in bonus_err[arm].values() for v in vs)
        entry[f"delta_{arm}"] = _paired_season_delta(bonus_err[arm], bonus_err["base"])
    res["bonus_points_mae"] = entry

    for m in MOMENTS:
        if coef[m]:
            vals = list(coef[m].values())
            res["coefficients"][m] = dict(mean=statistics.fmean(vals), by_season=coef[m],
                                          **_boot_mean(coef[m]))
    return res


def moment_persistence(rows: List[Row]) -> Dict:
    """The upstream check. If a player's shape residual in season N-1 does not
    predict his shape residual in season N, the covariate is noise and no
    downstream result can be real. Bootstrap resamples PLAYERS."""
    by_key = {(r.player_id, r.family, r.season): r for r in rows}
    out: Dict = {}
    for fam in FAMILIES:
        for m in MOMENTS:
            pairs = []
            for r in rows:
                if r.family != fam:
                    continue
                nxt = by_key.get((r.player_id, r.family, r.season + 1))
                if nxt is None:
                    continue
                a, b = r.resid.get(m, float("nan")), nxt.resid.get(m, float("nan"))
                if not (math.isnan(a) or math.isnan(b)):
                    pairs.append((r.player_id, a, b))
            if len(pairs) < 60:
                continue
            by_player: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
            for pid, a, b in pairs:
                by_player[pid].append((a, b))
            players = sorted(by_player)
            flat = [v for p in players for v in by_player[p]]

            def corr(xy):
                xs = [a for a, _ in xy]
                ys = [b for _, b in xy]
                mx, my = statistics.fmean(xs), statistics.fmean(ys)
                num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
                return num / den if den else float("nan")

            point = corr(flat)
            rng = random.Random(RNG_SEED)
            vals = []
            for _ in range(4000):
                chosen = [rng.choice(players) for _ in players]
                pooled = [v for p in chosen for v in by_player[p]]
                c = corr(pooled)
                if not math.isnan(c):
                    vals.append(c)
            vals.sort()
            lo, hi = vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]
            out[f"{fam}:{m}"] = dict(r=point, lo=lo, hi=hi, n=len(flat),
                                     grade=_grade(point, lo, hi))
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    out: Dict = {"estimator_primary": "G1/G2 adjusted Fisher-Pearson, "
                                      "excess kurtosis (Gaussian = 0)",
                 "shrinkage_primary": "empirical Bayes, tau^2 from data, no hand-picked constant",
                 "results": {}}
    n_tests = 0

    for adjusted in (True, False):
        tag = "G1/G2 adjusted (PRIMARY)" if adjusted else "g1/g2 sample (sensitivity)"
        base_rows = load(conn, adjusted=adjusted)
        residualise(base_rows)
        print(f"\n{'#' * 70}\n### estimator: {tag}   rows={len(base_rows)}")

        if adjusted:
            print("\n--- upstream check: does a player's SHAPE residual persist year to year? ---")
            pers = moment_persistence(base_rows)
            for k, v in pers.items():
                n_tests += 1
                print(f"    {k:12s} r={v['r']:+.3f} [{v['lo']:+.3f},{v['hi']:+.3f}] "
                      f"n={v['n']:5d}  {v['grade']}")
            out["moment_persistence"] = pers

        eb_report = shrink_eb(base_rows)
        rows = attach_prior(base_rows)
        print(f"\n  empirical-Bayes shrinkage actually applied (mean weight on the "
              f"player's own estimate):")
        for k in sorted(eb_report):
            r_ = eb_report[k]
            print(f"    {k:12s} skew w={r_.get('skew_mean_weight', float('nan')):.3f} "
                  f"(tau2={r_.get('skew_tau2', float('nan')):.4f})   "
                  f"kurt w={r_.get('kurt_mean_weight', float('nan')):.3f} "
                  f"(tau2={r_.get('kurt_tau2', float('nan')):.4f})")
        out[f"eb_shrinkage_{'G' if adjusted else 'g'}"] = eb_report

        key = f"{'G1G2' if adjusted else 'g1g2'}_eb"
        out["results"][key] = {}
        for fam in FAMILIES:
            r = walk_forward(rows, fam)
            out["results"][key][fam] = r
            print(f"\n  --- family {fam} (panel n={r['n_rows']}) ---")
            print(f"      {'threshold':>10s} {'base':>9s} "
                  + "".join(f"{a:>26s}" for a in ("skew", "kurt", "both", "oracle")))
            for t, d in r["thresholds"].items():
                line = f"      {t:>10d} {d['base']:9.5f} "
                for arm in ("skew", "kurt", "both", "oracle"):
                    dd = d[f"delta_{arm}"]
                    n_tests += 1
                    line += f"{dd['point']:+11.6f} {dd['grade']:>10s}   "
                print(line)
            bm = r["bonus_points_mae"]
            line = f"      {'BONUS MAE':>10s} {bm['base']:9.4f} "
            for arm in ("skew", "kurt", "both", "oracle"):
                dd = bm[f"delta_{arm}"]
                n_tests += 1
                line += f"{dd['point']:+11.5f} {dd['grade']:>10s}   "
            print(line)
            for m, c in r["coefficients"].items():
                print(f"      coef {m} at TOP threshold: {c['mean']:+.4f} "
                      f"[{c['lo']:+.4f},{c['hi']:+.4f}]  "
                      f"(interval NOT valid -- overlapping walk-forward training sets)")

        if adjusted:
            for k in NK_SWEEP:
                shrink_nk(base_rows, k)
                rows_k = attach_prior(base_rows)
                key = f"G1G2_nk{k:g}"
                out["results"][key] = {}
                print(f"\n  -- sensitivity, n/(n+k) shrinkage k={k:g} --")
                for fam in FAMILIES:
                    r = walk_forward(rows_k, fam)
                    out["results"][key][fam] = r
                    top = FAMILIES[fam]["thresholds"][-1]
                    d = r["thresholds"][top]
                    bm = r["bonus_points_mae"]
                    n_tests += 2
                    print(f"     {fam:5s} top-threshold logloss delta: "
                          f"skew {d['delta_skew']['point']:+.6f} {d['delta_skew']['grade']:9s} "
                          f"kurt {d['delta_kurt']['point']:+.6f} {d['delta_kurt']['grade']:9s} "
                          f"| bonus MAE delta: skew {bm['delta_skew']['point']:+.5f} "
                          f"kurt {bm['delta_kurt']['point']:+.5f}")

    out["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} interval tests; at 5% that is ~{0.05 * n_tests:.1f} false "
          f"'clears zero' results by chance. Negative delta = the shape arm is BETTER. ====")
    dest = REPO / "data" / "qa" / "fr086-exceedance-shape-2026-07-30.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
