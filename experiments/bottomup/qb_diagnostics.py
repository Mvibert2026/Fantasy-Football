"""Priority-2 QB diagnostics — DESCRIPTIVE ONLY, not a model configuration.

Registered as accompanying diagnostics in FABLE-EXT2-2026-07-27.md (V4 block).
Question: WHY does the composition model lose to last-season-rank at QB?
The PM's hypothesis: QB scoring is dominated by team-stable passing volume,
so last-season-rank is an unusually strong baseline and usage features add
variance without signal.

These are within-universe, walk-forward-shaped reads (prior season vs target
season, target < 2025). Nothing here fits anything.

Usage:
  python -m experiments.bottomup.qb_diagnostics --db <nfl.db>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
from scipy.stats import kendalltau

from .data import POSITIONS, SeasonStore, frozen_universe

FOLDS = list(range(2012, 2025))


def _tau(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 8:
        return float("nan")
    t, _ = kendalltau(xs, ys, variant="b")
    return float(t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", default=str(Path(__file__).parent / "results"
                                         / "qb_diagnostics.json"))
    args = ap.parse_args()
    store = SeasonStore(Path(args.db))

    per_pos: Dict[str, Dict[str, List[float]]] = {
        pos: {"tau_prior_points": [], "tau_prior_ppg": [],
              "tau_prior_volume_pg": [], "y2y_volume_pg": [],
              "y2y_games": [], "changed_team_share": []}
        for pos in POSITIONS
    }
    for t in FOLDS:
        universe = frozen_universe(store, t)
        prior = store.player_seasons(t - 1, for_target=t)
        actual = store.actuals(t)
        early = store.early_rosters(t)
        from .data import canon_team
        for pos in POSITIONS:
            pids = [p for p in universe[pos] if p in prior]
            act = [actual[p].points if p in actual else 0.0 for p in pids]
            pr = [prior[p] for p in pids]
            vol = [(ps.attempts if pos == "QB" else ps.targets + ps.carries)
                   / ps.games if ps.games else 0.0 for ps in pr]
            d = per_pos[pos]
            d["tau_prior_points"].append(_tau([ps.points for ps in pr], act))
            d["tau_prior_ppg"].append(_tau([ps.ppg or 0.0 for ps in pr], act))
            d["tau_prior_volume_pg"].append(_tau(vol, act))
            # year-over-year stability among players WITH a target season
            both = [(v, (actual[p].attempts if pos == "QB" else
                         actual[p].targets + actual[p].carries)
                     / actual[p].games)
                    for p, v, in zip(pids, vol)
                    if p in actual and actual[p].games >= 4]
            if len(both) >= 8:
                a, b = zip(*both)
                d["y2y_volume_pg"].append(float(np.corrcoef(a, b)[0, 1]))
            g_both = [(ps.games, float(actual[p].games))
                      for p, ps in zip(pids, pr) if p in actual]
            if len(g_both) >= 8:
                a, b = zip(*g_both)
                d["y2y_games"].append(float(np.corrcoef(a, b)[0, 1]))
            changed = [1.0 for p, ps in zip(pids, pr)
                       if early.get(p) is not None
                       and early[p] != canon_team(ps.team)]
            d["changed_team_share"].append(len(changed) / len(pids)
                                           if pids else float("nan"))

    summary = {
        pos: {k: {"mean": float(np.nanmean(v)), "n": len(v)}
              for k, v in d.items()}
        for pos, d in per_pos.items()
    }
    out = {"folds": FOLDS, "per_position_series": per_pos, "summary": summary,
           "note": "descriptive; registered in FABLE-EXT2-2026-07-27.md V4"}
    Path(args.out).write_text(json.dumps(out, indent=1))
    for pos in POSITIONS:
        s = summary[pos]
        print(f"{pos}: tau(prior pts)={s['tau_prior_points']['mean']:+.3f} "
              f"tau(prior ppg)={s['tau_prior_ppg']['mean']:+.3f} "
              f"tau(prior vol/g)={s['tau_prior_volume_pg']['mean']:+.3f} "
              f"y2y vol/g r={s['y2y_volume_pg']['mean']:+.3f} "
              f"y2y games r={s['y2y_games']['mean']:+.3f} "
              f"team-change={s['changed_team_share']['mean']:.1%}")


if __name__ == "__main__":
    main()
