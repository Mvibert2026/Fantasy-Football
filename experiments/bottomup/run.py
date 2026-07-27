"""Walk-forward driver for the bottom-up prototype.

Protocol (registered in docs/reviews/fable-ranking-design-2026-07-27.md):
expanding-window walk-forward — for target season t, everything (S1 ridge,
games model, S2 shrinkage constants, S3 bonus tables, feature
standardisation) is fitted on training pairs strictly before t. 2025 sealed.

Arms:
  long  — box-score volume (receptions, no targets), targets seasons
          2002-2024 (first fittable target: needs >=2 training pairs).
  usage — target/target-share/air-yards features, contiguous reliable window
          2009+, target seasons 2012-2024.

REGISTRATION CORRECTION (made before any fit, from data arithmetic, not from
results): the review doc registered "2000-2024, 25 folds" / "2010-2024, 15
folds". Both are impossible: the earliest targets have zero training PAIRS
(a pair needs feature-season s-1 AND outcome-season s, both < t). Corrected
fold sets: long 2002-2024 (23 folds), usage 2012-2024 (13 folds).

Baselines (registered):
  B1 last-season points (rank + value)
  B2 positional mean (value floor; no rank)
  B3 volume-only: prior opportunities/game
  B4 consensus ECR positional rank, 2021-2024, common universe, descriptive

Usage:
  python -m experiments.bottomup.run --db <path-to-nfl.db> --out <dir>
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .data import (HOLDOUT_SEASON, POSITIONS, TARGET_RELIABLE, SeasonStore,
                   frozen_universe)
from .metrics import (REPLACEMENT_K, paired_delta_ci, r2, season_bootstrap_ci,
                      tau_b, vbd_capture)
from .model import build_features, fit, predict

LONG_FOLDS = list(range(2002, 2025))
USAGE_FOLDS = list(range(2012, 2025))


def _opportunities_pg(ps) -> float:
    if ps.position == "QB":
        return (ps.attempts / ps.games) if ps.games else 0.0
    return ((ps.targets + ps.carries) / ps.games) if ps.games else 0.0


def run_arm(store: SeasonStore, arm: str, folds: List[int],
            qb_td_cap: Optional[float] = None, vacated: bool = False,
            qb_direct: bool = False, vac_exclude_self: bool = False,
            rookies: bool = False) -> dict:
    from .situation import Situation
    usage_arm = arm == "usage"
    results: Dict[str, dict] = {}
    for t in folds:
        assert t < HOLDOUT_SEASON, "attempted to evaluate the sealed holdout"
        t0 = time.time()
        # training pairs: seasons s with features s-1 available in-window
        if usage_arm:
            pair_seasons = [s for s in range(2010, t)
                            if TARGET_RELIABLE(s - 1) and s - 1 >= 2009]
        else:
            pair_seasons = list(range(2000, t))
        universe = frozen_universe(store, t)
        positions = {pid: pos for pos, pids in universe.items() for pid in pids}
        fit_kwargs = {} if qb_td_cap is None else {"qb_td_cap": qb_td_cap}
        model = fit(store, pair_seasons, usage_arm, target_season=t,
                    vacated=vacated, qb_direct=qb_direct,
                    vac_exclude_self=vac_exclude_self, rookies=rookies,
                    **fit_kwargs)
        sit = (Situation(store, t, usage_arm, exclude_self=vac_exclude_self,
                         rookies=rookies)
               if vacated else None)
        rows = build_features(store, t - 1, list(positions), positions,
                              usage_arm, target_season=t, situation=sit)
        preds = predict(model, rows)
        actual = store.actuals(t)
        prior = store.player_seasons(t - 1, for_target=t)

        actual_pts = {pid: (actual[pid].points if pid in actual else 0.0)
                      for pid in positions}
        actual_ppg = {pid: actual[pid].ppg for pid in positions
                      if pid in actual and actual[pid].games}
        actual_games = {pid: float(actual[pid].games) if pid in actual else 0.0
                        for pid in positions}

        arms_values: Dict[str, Dict[str, float]] = {
            "model": {pid: v[0] for pid, v in preds.items()},
            "b1_last_points": {pid: prior[pid].points for pid in positions
                               if pid in prior},
            "b3_volume": {pid: _opportunities_pg(prior[pid]) for pid in positions
                          if pid in prior},
        }
        # B4 consensus (2021-2024 only): negative positional rank as value
        consensus_note = None
        if 2021 <= t <= 2024:
            cons = store.consensus_ranks(t)
            arms_values["b4_consensus"] = {
                pid: -float(rank) for pid, (cpos, rank) in cons.items()
                if pid in positions
            }
            consensus_note = (
                f"ECR match: {len(arms_values['b4_consensus'])} of "
                f"{len(positions)} universe players"
            )

        season_out: dict = {"train_pairs": len(pair_seasons),
                            "consensus_note": consensus_note,
                            "positions": {}}
        for pos in POSITIONS:
            pids = universe[pos]
            entry: dict = {"n": len(pids)}
            for arm_name, values in arms_values.items():
                sub = None
                if arm_name == "b4_consensus":
                    # common universe: players consensus actually ranked
                    sub = [p for p in pids if p in values]
                    if len(sub) < 8:
                        continue
                use = sub if sub is not None else pids
                entry[arm_name] = {
                    "tau_b": tau_b(values, actual_pts, use),
                    "vbd_capture": vbd_capture(values, actual_pts, use, pos),
                }
                if arm_name == "b4_consensus":
                    entry[arm_name]["n_common"] = len(use)
                    # model on the same common subset, for the paired read
                    entry["model_on_consensus_subset"] = {
                        "tau_b": tau_b(arms_values["model"], actual_pts, use),
                        "vbd_capture": vbd_capture(arms_values["model"],
                                                   actual_pts, use, pos),
                    }
            # R^2 triplet for the model only (value baselines aren't points)
            model_pts = arms_values["model"]
            model_ppg = {pid: preds[pid][1] for pid in preds}
            model_games = {pid: preds[pid][2] for pid in preds}
            entry["model_r2"] = {
                "season_points": r2(model_pts, actual_pts, pids),
                "ppg": r2(model_ppg, actual_ppg, [p for p in pids
                                                  if p in actual_ppg]),
                "games": r2(model_games, actual_games, pids),
            }
            # B1 as a POINTS predictor (naive persistence value)
            b1_pts = arms_values["b1_last_points"]
            entry["b1_r2_season_points"] = r2(b1_pts, actual_pts, pids)
            # B2 positional-mean floor: predict train-era positional mean
            pos_pts = [prior[p].points for p in pids if p in prior]
            mean_guess = float(np.mean(pos_pts)) if pos_pts else 0.0
            entry["b2_r2_season_points"] = r2(
                {p: mean_guess for p in pids}, actual_pts, pids)
            season_out["positions"][pos] = entry
        season_out["wall_seconds"] = round(time.time() - t0, 2)
        season_out["s2_k"] = {k: s.k for k, s in model.shrinkers.items()}
        season_out["s2_cap_binds"] = {k: s.cap_binds
                                      for k, s in model.shrinkers.items()}
        results[str(t)] = season_out
        print(f"[{arm}] {t}: done in {season_out['wall_seconds']}s "
              f"(pairs={len(pair_seasons)})")
    return results


def summarise(results: dict, folds: List[int]) -> dict:
    """Across-season summary: per position, per metric, per arm-comparison."""
    out: dict = {}
    for pos in POSITIONS:
        pos_sum: dict = {}
        series: Dict[str, List[float]] = defaultdict(list)
        for t in folds:
            entry = results[str(t)]["positions"][pos]
            for arm_name in ("model", "b1_last_points", "b3_volume"):
                if arm_name in entry:
                    series[f"{arm_name}_tau"].append(entry[arm_name]["tau_b"])
                    series[f"{arm_name}_vbd"].append(
                        entry[arm_name]["vbd_capture"])
            series["model_r2_season"].append(
                entry["model_r2"]["season_points"])
            series["model_r2_ppg"].append(entry["model_r2"]["ppg"])
            series["model_r2_games"].append(entry["model_r2"]["games"])
            series["b1_r2_season"].append(entry["b1_r2_season_points"])
            if "b4_consensus" in entry:
                series["b4_tau"].append(entry["b4_consensus"]["tau_b"])
                series["model_sub_tau"].append(
                    entry["model_on_consensus_subset"]["tau_b"])
                series["b4_vbd"].append(entry["b4_consensus"]["vbd_capture"])
                series["model_sub_vbd"].append(
                    entry["model_on_consensus_subset"]["vbd_capture"])
        for key, vals in series.items():
            pt, lo, hi = season_bootstrap_ci(vals)
            pos_sum[key] = {"mean": pt, "ci": [lo, hi],
                            "n_seasons": sum(1 for v in vals
                                             if not np.isnan(v))}
        # paired: model vs B1 on tau (THE question) and vbd
        pos_sum["delta_model_minus_b1_tau"] = dict(zip(
            ("mean", "lo", "hi", "frac_positive"),
            paired_delta_ci(series["model_tau"], series["b1_last_points_tau"])))
        pos_sum["delta_model_minus_b1_vbd"] = dict(zip(
            ("mean", "lo", "hi", "frac_positive"),
            paired_delta_ci(series["model_vbd"], series["b1_last_points_vbd"])))
        pos_sum["delta_model_minus_b3_tau"] = dict(zip(
            ("mean", "lo", "hi", "frac_positive"),
            paired_delta_ci(series["model_tau"], series["b3_volume_tau"])))
        if series.get("b4_tau"):
            pos_sum["delta_model_minus_b4_tau_DESCRIPTIVE_n4"] = dict(zip(
                ("mean", "lo", "hi", "frac_positive"),
                paired_delta_ci(series["model_sub_tau"], series["b4_tau"])))
        out[pos] = pos_sum
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", default=str(Path(__file__).parent / "results"))
    ap.add_argument("--arms", default="long,usage")
    ap.add_argument("--qb-td-cap", type=float, default=None,
                    help="exploratory variant: override the QB pass-TD "
                         "shrinkage cap (registered default 0.20)")
    ap.add_argument("--vacated", action="store_true",
                    help="V3: vacated/arrived-opportunity features "
                         "(registered look-ahead: weeks-1-4 rosters)")
    ap.add_argument("--qb-direct", action="store_true",
                    help="V4: QB-only direct season-points ridge with "
                         "prior-points features")
    ap.add_argument("--exclude-self-vacated", action="store_true",
                    help="V5/V6: remove the player's own production from "
                         "his own vacated shares (kills the availability "
                         "self-leak; registered amendment)")
    ap.add_argument("--rookies", action="store_true",
                    help="V7: same-position rookie-arrival draft capital "
                         "(registered FABLE-EXT3 before this code existed; "
                         "requires --vacated)")
    ap.add_argument("--tag", default="", help="output filename suffix")
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    store = SeasonStore(Path(args.db))
    for arm in args.arms.split(","):
        folds = LONG_FOLDS if arm == "long" else USAGE_FOLDS
        if args.rookies and not args.vacated:
            raise SystemExit("--rookies requires --vacated (V7 is V5 + rookie "
                             "features, per registration)")
        results = run_arm(store, arm, folds, qb_td_cap=args.qb_td_cap,
                          vacated=args.vacated, qb_direct=args.qb_direct,
                          vac_exclude_self=args.exclude_self_vacated,
                          rookies=args.rookies)
        summary = summarise(results, folds)
        payload = {"arm": arm, "folds": folds, "per_season": results,
                   "summary": summary,
                   "qb_td_cap_override": args.qb_td_cap,
                   "vacated": args.vacated, "qb_direct": args.qb_direct,
                   "vac_exclude_self": args.exclude_self_vacated,
                   "rookies": args.rookies,
                   "registration":
                       "docs/reviews/fable-ranking-design-2026-07-27.md + "
                       "docs/reviews/FABLE-EXT2-2026-07-27.md (V3/V4) + "
                       "docs/reviews/FABLE-EXT3-2026-07-27.md (V7)",
                   "holdout_untouched": True}
        path = outdir / f"{arm}{args.tag}.json"
        path.write_text(json.dumps(payload, indent=1))
        print(f"[{arm}] written {path}")


if __name__ == "__main__":
    main()
