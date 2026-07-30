"""Does a player's OWN measured game-to-game dispersion improve the exceedance
curve beyond his mean?

THE DEFECT THIS TESTS. `experiments/bottomup/components/pos_model.py:300`:

    def _bonus_design(ypg):
        return np.column_stack([np.ones(len(ypg)), np.log1p(np.clip(ypg, 0, None))])

P(a game clears threshold t) is a function of MEAN yards per game and nothing
else. Two players at 60 yards a game get identical bonus expectations whether
their weekly lines are 60/60/60 or 20/20/140. `CLAUDE.md` §7 says this league's
stacking bonuses reward ceiling over floor; that claim is only *operational* if
tail shape carries information the mean does not. This measures whether it does.

THIS IS NOT PR-002 AND IT IS NOT PASS-1 §6.1. Three different questions:

  PR-002 (`src/spike_persistence.py`)  Is "spike-week player" a persistent
      CATEGORY? Between-player, categorical. Found nothing.
  pass-1 §6.1                          Does the RESIDUAL CLEARANCE RATE (observed
      minus binomial-implied) persist year over year? Same idea, but the
      instrument is a count of threshold crossings -- order ten events a season,
      so it is extremely noisy.
  THIS                                 Does a player's own measured DISPERSION OF
      YARDS, estimated from every game he played rather than from the handful
      that crossed a line, predict clearance beyond his mean? Within-player,
      continuous, and a far lower-noise instrument than either of the above.

A null here does not follow from either earlier null, and a positive here would
not contradict them.

DESIGN, fixed before any number was read
----------------------------------------
Feature       excess log dispersion in season N-1: log(SD of game yards) minus
              its fit on log(mean game yards), within (family, position, season),
              then shrunk toward 0 by n/(n+k). Prior season only -- using season
              N's own dispersion to predict season N's clearance is circular and
              would look spectacular.
Shrinkage     k = 8 games primary; k in {0, 4, 16} reported as sensitivity. The
              target is 0, i.e. "no more variable than his scoring level implies",
              which is the population mean of the residual by construction.
Arms          baseline  [1, log1p(ypg_N)]              -- the shipped design
              test      [1, log1p(ypg_N), disp_(N-1)]  -- one added parameter
Validation    WALK-FORWARD. For target season N the GLM is fitted on panel rows
              with season < N only, then scored on N. Never training fit
              (`CLAUDE.md` §6.3).
Metrics       out-of-sample binomial log-loss per game-trial (the fit), and MAE
              of expected BONUS POINTS against realised bonus points (the money).

THE SETTING IS DELIBERATELY THE MOST FAVOURABLE ONE THAT EXISTS. Both arms are
given the player's REALISED mean ypg for the target season. In production the
mean is a projection and is noisy, which can only make an added term work harder.
So if the dispersion term does not help here, it cannot help in the shipped
pipeline, and the convexity correction at `pos_model.py:320` never has to be
extended to cover it.

Run:
    .venv/bin/python -m experiments.volatility.exceedance_dispersion
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import db  # noqa: E402
from experiments.bottomup.components.pos_model import binom_glm  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
HOLDOUT_SEASON = 2025
FIRST_SEASON = 1999
RNG_SEED = 20260730

# PR-002's qualifying rules, reused unchanged so the two are comparable.
MIN_GAMES = 8
MIN_YPG_SCRIMMAGE = 25.0
MIN_YPG_PASSING = 150.0

FAMILIES = {
    "rec": dict(col="receiving_yards", thresholds=(100, 150, 200),
                bonus={100: 1.0, 150: 1.5, 200: 2.0},
                positions=("WR", "RB", "TE"), min_ypg=MIN_YPG_SCRIMMAGE),
    "rush": dict(col="rushing_yards", thresholds=(100, 150, 200),
                 bonus={100: 1.0, 150: 1.5, 200: 2.0},
                 positions=("RB", "QB"), min_ypg=MIN_YPG_SCRIMMAGE),
    "pass": dict(col="passing_yards", thresholds=(300, 350, 400),
                 bonus={300: 1.0, 350: 1.5, 400: 2.0},
                 positions=("QB",), min_ypg=MIN_YPG_PASSING),
}

SHRINK_K_PRIMARY = 8.0
SHRINK_K_SWEEP = (0.0, 4.0, 8.0, 16.0)


@dataclass
class Row:
    season: int
    player_id: str
    position: str
    family: str
    games: int
    mean_ypg: float
    sd_ypg: float
    clears: Dict[int, int]
    excess_log_sd: float = float("nan")
    disp_prior: float = float("nan")


def load(conn: sqlite3.Connection) -> List[Row]:
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
            out.append(Row(season, pid, pos, fam, len(a), mean, float(a.std(ddof=1)),
                           {t: int((a >= t).sum()) for t in cfg["thresholds"]}))
    return out


def add_excess_log_sd(rows: List[Row]) -> None:
    """log(SD) on log(mean), fitted WITHIN (family, position, season). Within
    season as well, because a league-wide scoring shift would otherwise be
    charged to individual players as volatility."""
    groups: Dict[Tuple[str, str, int], List[Row]] = defaultdict(list)
    for r in rows:
        groups[(r.family, r.position, r.season)].append(r)
    for grp in groups.values():
        xs, ys, keep = [], [], []
        for r in grp:
            if r.mean_ypg > 0 and r.sd_ypg > 0:
                xs.append(math.log(r.mean_ypg))
                ys.append(math.log(r.sd_ypg))
                keep.append(r)
        if len(keep) < 10:
            continue
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
        a = my - b * mx
        for r, x, y in zip(keep, xs, ys):
            r.excess_log_sd = y - (a + b * x)


def attach_prior(rows: List[Row], k: float) -> List[Row]:
    """disp_prior = shrunk excess log SD from season N-1, same player, same
    family. Rows without a qualifying prior season are dropped, not guessed."""
    by_key = {(r.player_id, r.family, r.season): r for r in rows}
    out = []
    for r in rows:
        p = by_key.get((r.player_id, r.family, r.season - 1))
        if p is None or math.isnan(p.excess_log_sd):
            continue
        w = p.games / (p.games + k) if (p.games + k) > 0 else 1.0
        r.disp_prior = w * p.excess_log_sd
        out.append(r)
    return out


def _design(rows: Sequence[Row], with_disp: bool) -> np.ndarray:
    ypg = np.array([r.mean_ypg for r in rows])
    cols = [np.ones(len(rows)), np.log1p(np.clip(ypg, 0, None))]
    if with_disp:
        cols.append(np.array([r.disp_prior for r in rows]))
    return np.column_stack(cols)


def _logloss(p: np.ndarray, succ: np.ndarray, trials: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -(succ * np.log(p) + (trials - succ) * np.log(1 - p))


def walk_forward(rows: List[Row], fam: str) -> Dict:
    cfg = FAMILIES[fam]
    sub = sorted([r for r in rows if r.family == fam], key=lambda r: r.season)
    seasons = sorted({r.season for r in sub})
    res: Dict = {"n_rows": len(sub), "seasons": seasons, "thresholds": {}}
    # per-season accumulators for the bonus-points comparison
    bonus_err_base: Dict[int, List[float]] = defaultdict(list)
    bonus_err_disp: Dict[int, List[float]] = defaultdict(list)
    coef_by_season: Dict[int, float] = {}

    for t in cfg["thresholds"]:
        ll_base: Dict[int, List[float]] = defaultdict(list)
        ll_disp: Dict[int, List[float]] = defaultdict(list)
        for target in seasons:
            train = [r for r in sub if r.season < target]
            test = [r for r in sub if r.season == target]
            if len(train) < 200 or not test:
                continue
            succ_tr = np.array([r.clears[t] for r in train], dtype=float)
            tri_tr = np.array([r.games for r in train], dtype=float)
            succ_te = np.array([r.clears[t] for r in test], dtype=float)
            tri_te = np.array([r.games for r in test], dtype=float)
            for tag, with_disp, store in (("base", False, ll_base), ("disp", True, ll_disp)):
                beta = binom_glm(_design(train, with_disp), succ_tr, tri_tr)
                eta = np.clip(_design(test, with_disp) @ beta, -30, 30)
                p = 1.0 / (1.0 + np.exp(-eta))
                store[target].extend((_logloss(p, succ_te, tri_te) / tri_te).tolist())
                if with_disp and t == cfg["thresholds"][0]:
                    coef_by_season[target] = float(beta[2])
        res["thresholds"][t] = dict(
            base=statistics.fmean(v for vs in ll_base.values() for v in vs),
            disp=statistics.fmean(v for vs in ll_disp.values() for v in vs),
            delta=_paired_season_delta(ll_disp, ll_base))

    # ---- the money metric: expected BONUS POINTS, walk-forward, both arms
    for target in seasons:
        train = [r for r in sub if r.season < target]
        test = [r for r in sub if r.season == target]
        if len(train) < 200 or not test:
            continue
        exp_base = np.zeros(len(test))
        exp_disp = np.zeros(len(test))
        actual = np.zeros(len(test))
        tri_te = np.array([r.games for r in test], dtype=float)
        for t in cfg["thresholds"]:
            succ_tr = np.array([r.clears[t] for r in train], dtype=float)
            tri_tr = np.array([r.games for r in train], dtype=float)
            b_base = binom_glm(_design(train, False), succ_tr, tri_tr)
            b_disp = binom_glm(_design(train, True), succ_tr, tri_tr)
            pb = 1.0 / (1.0 + np.exp(-np.clip(_design(test, False) @ b_base, -30, 30)))
            pd_ = 1.0 / (1.0 + np.exp(-np.clip(_design(test, True) @ b_disp, -30, 30)))
            exp_base += pb * tri_te * cfg["bonus"][t]
            exp_disp += pd_ * tri_te * cfg["bonus"][t]
            actual += np.array([r.clears[t] for r in test], dtype=float) * cfg["bonus"][t]
        bonus_err_base[target].extend(np.abs(exp_base - actual).tolist())
        bonus_err_disp[target].extend(np.abs(exp_disp - actual).tolist())
    res["bonus_points_mae"] = dict(
        base=statistics.fmean(v for vs in bonus_err_base.values() for v in vs),
        disp=statistics.fmean(v for vs in bonus_err_disp.values() for v in vs),
        delta=_paired_season_delta(bonus_err_disp, bonus_err_base))
    if coef_by_season:
        vals = list(coef_by_season.values())
        res["dispersion_coefficient"] = dict(
            mean=statistics.fmean(vals), by_season=coef_by_season,
            **_boot_mean(coef_by_season))
    return res


def _boot_mean(by_season: Dict[int, float], n_boot: int = 4000) -> Dict[str, float]:
    seasons = sorted(by_season)
    if len(seasons) < 2:
        return dict(lo=float("nan"), hi=float("nan"))
    rng = random.Random(RNG_SEED)
    vals = []
    for _ in range(n_boot):
        vals.append(statistics.fmean([by_season[rng.choice(seasons)] for _ in seasons]))
    vals.sort()
    return dict(lo=vals[int(0.025 * len(vals))], hi=vals[int(0.975 * len(vals)) - 1])


def _paired_season_delta(a: Dict[int, List[float]], b: Dict[int, List[float]],
                         n_boot: int = 4000) -> Dict[str, float]:
    """mean(a) - mean(b), resampling SEASONS jointly so the two arms stay paired.
    Negative = the dispersion arm is better (both metrics are losses)."""
    seasons = sorted(set(a) & set(b))
    if not seasons:
        return dict(point=float("nan"), lo=float("nan"), hi=float("nan"), grade="NO-CI")
    fa = [v for s in seasons for v in a[s]]
    fb = [v for s in seasons for v in b[s]]
    point = statistics.fmean(fa) - statistics.fmean(fb)
    rng = random.Random(RNG_SEED)
    diffs = []
    for _ in range(n_boot):
        chosen = [rng.choice(seasons) for _ in seasons]
        x = [v for s in chosen for v in a[s]]
        y = [v for s in chosen for v in b[s]]
        if x and y:
            diffs.append(statistics.fmean(x) - statistics.fmean(y))
    diffs.sort()
    lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]
    return dict(point=point, lo=lo, hi=hi, grade=_grade(point, lo, hi), n_seasons=len(seasons))


def _grade(point: float, lo: float, hi: float) -> str:
    if any(math.isnan(x) for x in (point, lo, hi)):
        return "NO-CI"
    if lo <= 0.0 <= hi:
        return "NULL"
    half = (hi - lo) / 2.0
    if half <= 0:
        return "NO-CI"
    return "SURVIVES" if abs(point) / (half / 1.96) >= 3.0 else "MARGINAL"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    base_rows = load(conn)
    add_excess_log_sd(base_rows)
    print(f"qualifying player-season-family rows {FIRST_SEASON}-{HOLDOUT_SEASON - 1}: "
          f"{len(base_rows)}")
    for fam in FAMILIES:
        print(f"   {fam}: {sum(1 for r in base_rows if r.family == fam)}")

    out: Dict = {"shrink_primary": SHRINK_K_PRIMARY, "results": {}}
    n_tests = 0
    for k in SHRINK_K_SWEEP:
        tag = f"k={k:g}" + (" (PRIMARY)" if k == SHRINK_K_PRIMARY else "")
        rows = attach_prior([Row(**{**r.__dict__}) for r in base_rows], k)
        print(f"\n########## shrinkage {tag} -- panel rows with a qualifying prior "
              f"season: {len(rows)}")
        kres: Dict = {}
        for fam in FAMILIES:
            r = walk_forward(rows, fam)
            kres[fam] = r
            print(f"\n  --- family {fam} (n={r['n_rows']}) ---")
            for t, d in r["thresholds"].items():
                dd = d["delta"]
                n_tests += 1
                print(f"    logloss/game >= {t:3d}:  base {d['base']:.5f}  "
                      f"disp {d['disp']:.5f}  delta {dd['point']:+.6f} "
                      f"[{dd['lo']:+.6f},{dd['hi']:+.6f}]  {dd['grade']}")
            bm = r["bonus_points_mae"]
            n_tests += 1
            print(f"    BONUS POINTS MAE:      base {bm['base']:.4f}  disp {bm['disp']:.4f}  "
                  f"delta {bm['delta']['point']:+.5f} "
                  f"[{bm['delta']['lo']:+.5f},{bm['delta']['hi']:+.5f}]  "
                  f"{bm['delta']['grade']}")
            if "dispersion_coefficient" in r:
                c = r["dispersion_coefficient"]
                n_tests += 1
                print(f"    dispersion coefficient (lowest threshold): {c['mean']:+.4f} "
                      f"[{c['lo']:+.4f},{c['hi']:+.4f}]  {_grade(c['mean'], c['lo'], c['hi'])}")
        out["results"][f"k{k:g}"] = kres

    out["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} interval tests; at 5% that is ~{0.05 * n_tests:.1f} false "
          f"'clears zero' results by chance. Negative delta = dispersion arm better. ====")
    dest = REPO / "data" / "qa" / "fr086-exceedance-dispersion-2026-07-30.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
