#!/usr/bin/env python
"""C1 diagnostic — replicate the placebo arm across independent noise draws.

    .venv/bin/python -m experiments.bottomup.v2.placebo_replication [--draws 12]

DESCRIPTIVE, CONTRIBUTES 0 TESTS to the batch-C1 family. It is not an arm and it
makes no claim about any factor.

WHY IT EXISTS. The registered placebo F0 — a column of seeded noise that
provably cannot carry signal — returned a BH-robust WIN at TE (+0.030, CI
[0.013, 0.046], p=0.0002) and the registered inclusion rule graded it INCLUDE.
Two very different mechanisms produce that, and they demand different responses:

  (A) SYSTEMATIC — adding *any* column to the volume design improves TE
      ordering, e.g. because a noise regressor damps an ill-conditioned
      small-sample fit. Then every TE cell in the batch is uninterpretable and
      the design must change.
  (B) A LUCKY DRAW MEETING A BROKEN TEST — the per-season deltas at TE were
      {0, 0, +.020, +.035, +.049, +.055, +.055}: five positive, two exactly
      zero, none negative. A season-block bootstrap on such a sample puts
      essentially all its mass above zero, so the 95% CI excludes zero almost
      by construction whenever no season goes the other way, at any effect
      size. Then the estimator, not the model, is what needs replacing.

Drawing many independent placebos separates them: under (A) the win rate across
draws is high at TE and near zero elsewhere; under (B) the delta sign is a coin
flip across draws and the WIN rate measures the test's real false-positive rate
against its nominal 5%.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.v2 import factors_c1                      # noqa: E402
from experiments.bottomup.v2.run_c1 import (                        # noqa: E402
    CONTROLS, boot_diff, cell_metrics, run_one)
from experiments.bottomup.v2.weekshape import build_v2_panel        # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=12)
    ap.add_argument("--positions", default="QB,RB,WR,TE")
    args = ap.parse_args()
    positions = tuple(args.positions.split(","))

    panel = build_v2_panel()
    ff, ft, lt = CONTROLS["CTRL-A"]

    ctl = cell_metrics(run_one(panel, "CTRL-A", None, positions, ff, ft, lt),
                       "CTRL-A", None)

    rows = []
    for i in range(args.draws):
        factors_c1.PLACEBO_SALT = f"-rep{i:02d}"
        try:
            m = cell_metrics(
                run_one(panel, f"P{i:02d}", "F0", positions, ff, ft, lt),
                f"P{i:02d}", "F0")
        finally:
            factors_c1.PLACEBO_SALT = ""
        for pos in positions:
            a = m[m.position == pos].set_index("season")[["rho_points"]] \
                .rename(columns={"rho_points": "a"})
            b = ctl[ctl.position == pos].set_index("season")[["rho_points"]] \
                .rename(columns={"rho_points": "b"})
            j = a.join(b, how="inner")
            d, lo, hi, n, p = boot_diff(j)
            per = (j["a"] - j["b"]).to_numpy()
            rows.append(dict(
                draw=i, position=pos, delta=d, lo=lo, hi=hi, p=p, n=n,
                n_pos=int((per > 1e-12).sum()), n_neg=int((per < -1e-12).sum()),
                n_zero=int((np.abs(per) <= 1e-12).sum()),
                verdict="WIN" if lo > 0 else ("HARM" if hi < 0 else "NULL")))
        print(f"draw {i}: " + "  ".join(
            f"{r['position']}={r['delta']:+.4f}/{r['verdict']}"
            for r in rows[-len(positions):]), flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "factor_c1_placebo_replication.csv", index=False)

    print(f"\n{'='*88}\nPLACEBO REPLICATION — {args.draws} independent noise "
          f"draws, same harness, same control\n{'='*88}")
    s = df.groupby("position").agg(
        mean_delta=("delta", "mean"), sd_delta=("delta", "std"),
        win_rate=("verdict", lambda v: float((v == "WIN").mean())),
        harm_rate=("verdict", lambda v: float((v == "HARM").mean())),
        mean_pos_seasons=("n_pos", "mean"), mean_neg_seasons=("n_neg", "mean"),
        mean_zero_seasons=("n_zero", "mean"))
    print(s.round(4).to_string())
    print("\nA nominal 95% CI should WIN on ~2.5% of draws per position "
          "(one-sided) if the test is calibrated.")


if __name__ == "__main__":
    main()
