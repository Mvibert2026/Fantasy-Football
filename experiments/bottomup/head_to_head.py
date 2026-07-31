#!/usr/bin/env python
"""Component model vs incumbent `projected_points`, on projection error (MAE, season
points), same universe, walk-forward. Ranker's dispatch, `docs/ranking/
fr136-q1-bottom-up-assessment.md` step 1 (S6.2).

ALIGNMENT REQUIREMENTS (S6.2, non-negotiable):
  (a) SAME UNIVERSE.  Both arms are scored on exactly the same player-seasons --
      the ADP-covered ("adpsub") subset the component walk-forward already
      restricts to when it evaluates against baseline #1 (FFC half-PPR 12-team
      ADP, 2018-2024). This is also the cheaper direction: the incumbent moves
      to FFC ADP rather than trying to force FFC coverage onto `fantasypros_ecr`.
  (b) SAME OUTPUT UNITS.  The component model already emits `proj_points` as
      full SEASON points, bonuses included, scored via
      `pos_model.score_components()` under this league's ruleset
      (`experiments/bottomup/components/pos_model.py:453-455`). The incumbent's
      curve is refit here on the identical scoring target (`points`, from
      `src/scoring.score_offensive_game`, summed over the season) -- not
      re-derived, just moved onto the same universe and the same units.

INCUMBENT, reproduced: `projected_points = a + b*ln(positional_market_rank)`,
walk-forward (curve for season S fit only on seasons < S), busts retained at
zero, 2025 untouched. This is exactly the object measured in fr136 S1.1 / S6.1 --
moved from the `fantasypros_ecr` consensus rank it ships on to FFC ADP rank, so
the same object can be scored on the same universe as the component models.
Because FFC ADP only covers 2018-2024, the incumbent curve here is fit on
whatever FFC seasons precede the target (as few as one), which is the reason
this yields SIX evaluation seasons (2019-2024) instead of three.

2025 is never touched by either arm. Component models fit through
`experiments.bottomup.components.pos_eval.WalkForward` (arm A, unmodified).
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E          # noqa: E402
from experiments.bottomup.components.pos_data import build_panel    # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024          # component model's own walk-forward range
HOLDOUT_SEASON = 2025             # sealed; never touched

POSITIONS = ["QB", "RB", "WR", "TE"]


def incumbent_curve_mae(d: pd.DataFrame) -> pd.DataFrame:
    """Walk-forward MAE of `a + b*ln(positional FFC-ADP rank)` on the ADP-covered
    universe already present in `d` (component walk-forward output, one position).

    `d` carries `season`, `average_pick`, `points` for every target season the
    component model was run over. Rows with a finite `average_pick` are the
    same ADP-covered universe `adpsub_*` metrics already use in
    `pos_eval._season_metrics`. Training pools every PRIOR season's (rank,
    points) pairs in that universe -- walk-forward, exactly as fr136 S6.1
    describes for the shipped curve, just moved onto FFC ADP rank.
    """
    sub = d[np.isfinite(d["average_pick"])].copy()
    sub["rank"] = sub.groupby("season")["average_pick"].rank(method="first")
    sub["ln_rank"] = np.log(sub["rank"])

    rows = []
    for season in sorted(sub["season"].unique()):
        train = sub[sub["season"] < season]
        test = sub[sub["season"] == season]
        if train["season"].nunique() < 1 or len(test) < 5:
            continue
        X = np.column_stack([np.ones(len(train)), train["ln_rank"].to_numpy()])
        y = train["points"].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = beta[0] + beta[1] * test["ln_rank"].to_numpy()
        actual = test["points"].to_numpy(dtype=float)
        rows.append(dict(
            season=int(season), n=len(test),
            mae_incumbent=float(np.mean(np.abs(pred - actual))),
            n_train_seasons=int(train["season"].nunique())))
    return pd.DataFrame(rows)


def component_mae_same_universe(d: pd.DataFrame) -> pd.DataFrame:
    """Component model MAE on the identical ADP-covered rows, per season."""
    sub = d[np.isfinite(d["average_pick"])].copy()
    rows = []
    for season, g in sub.groupby("season"):
        e = g["proj_points"].to_numpy(dtype=float) - g["points"].to_numpy(dtype=float)
        rows.append(dict(season=int(season), n=len(g),
                         mae_component=float(np.mean(np.abs(e)))))
    return pd.DataFrame(rows)


def run_position(pos: str) -> pd.DataFrame:
    panel = build_panel()
    wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                       last_target=LAST, avail_arm="A")
    players, _m = wf.run()
    assert players["season"].max() < HOLDOUT_SEASON, "holdout touched"

    inc = incumbent_curve_mae(players)
    comp = component_mae_same_universe(players)
    j = inc.merge(comp, on=["season", "n"], how="inner")
    j["position"] = pos
    j["delta"] = j["mae_component"] - j["mae_incumbent"]   # negative = component wins
    return j[["position", "season", "n", "n_train_seasons",
              "mae_incumbent", "mae_component", "delta"]]


def season_block_bootstrap(diffs: np.ndarray, reps: int = 4000, seed: int = 20260730):
    n = len(diffs)
    if n == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = np.array([np.mean(rng.choice(diffs, size=n, replace=True)) for _ in range(reps)])
    return float(diffs.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def main() -> None:
    all_rows = []
    for pos in POSITIONS:
        j = run_position(pos)
        all_rows.append(j)
        print(f"\n{'='*78}\n{pos}\n{'='*78}")
        print(j.round(2).to_string(index=False))

    full = pd.concat(all_rows, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    full.to_csv(OUT / "head_to_head_mae.csv", index=False)

    print(f"\n{'='*78}\nSUMMARY -- mean MAE (points), walk-forward, same universe,"
          f" busts retained, 2025 untouched\n{'='*78}")
    summary = full.groupby("position").agg(
        n_seasons=("season", "nunique"),
        mean_mae_incumbent=("mae_incumbent", "mean"),
        mean_mae_component=("mae_component", "mean")).round(2)
    print(summary.to_string())

    print("\nseason-block bootstrap, paired difference (component - incumbent), "
          "negative = component wins:")
    for pos in POSITIONS:
        sub = full[full.position == pos]
        d, lo, hi = season_block_bootstrap(sub["delta"].to_numpy(dtype=float))
        verdict = "COMPONENT CLEARS 0 (wins)" if hi < 0 else \
                  ("INCUMBENT CLEARS 0 (component loses)" if lo > 0 else "does NOT clear 0")
        print(f"  {pos:3s} {d:+8.3f} [{lo:+8.3f}, {hi:+8.3f}]  n={len(sub)}  {verdict}")


if __name__ == "__main__":
    main()
