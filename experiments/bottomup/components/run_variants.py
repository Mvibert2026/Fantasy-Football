#!/usr/bin/env python
"""Secondary variants, declared in `component-model-multipos-precommit.md` §3.

    .venv/bin/python -m experiments.bottomup.components.run_variants

REPORTED, NEVER SELECTED ON. Each variant is one modelling choice away from its
position's primary, and the primary was named in a committed document before any
of these numbers existed. Promoting a secondary because it won here would be
selection on the outcome, which is the thing the pre-commitment exists to stop.

  RB  opportunity-share  -- project (carries + targets)/game and the receiving
                            share of it, instead of the two streams separately
  QB  deep sample        -- 2002+ instead of 2012+, because passing volume is
                            complete from 1999 and the 2003-08 hole is a TARGETS
                            hole that does not touch QB
  TE  pooled rates       -- efficiency rates borrow WR rows for the prior and the
                            shrinkage constant; recalibration stays TE-only
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E          # noqa: E402
from experiments.bottomup.components.pos_data import build_panel    # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024

VARIANTS = [
    ("RB", "primary: independent streams", {}),
    ("RB", "secondary: opportunity-share", {"model_kwargs": {"opportunity_share": True}}),
    ("QB", "primary: 2012+ sample", {}),
    ("QB", "secondary: deep 2002+ sample",
     {"first_feature_season": E.DEEP_FIRST_FEATURE_SEASON}),
    ("TE", "primary: TE-only rates", {}),
    ("TE", "secondary: WR-pooled rates", {"pool_position": "WR"}),
]


def banner(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


def main() -> None:
    panel = build_panel()
    results = {}
    for pos, label, kw in VARIANTS:
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", **kw)
        players, m = wf.run()
        results[(pos, label)] = (players, m)
        print(f"ran {pos:3s} {label:34s} "
              f"{len(players)} player-seasons, {len(m)} seasons")

    for pos in ["RB", "QB", "TE"]:
        keys = [k for k in results if k[0] == pos]
        prim = [k for k in keys if k[1].startswith("primary")][0]
        sec = [k for k in keys if k[1].startswith("secondary")][0]
        banner(f"{pos}: {sec[1]}  MINUS  {prim[1]}")
        mp, ms = results[prim][1], results[sec][1]
        cols = [c for c in ["season", "n", "n_adp", "rho_model", "adpsub_rho_model"]
                if c in mp.columns and c in ms.columns]
        side = mp[cols].merge(ms[cols], on=["season"], suffixes=("_prim", "_sec"))
        print(side.round(3).to_string(index=False))
        j = mp.merge(ms, on="season", suffixes=("_P", "_S"))
        for col, lab in [("rho_model", "full-universe rho"),
                         ("adpsub_rho_model", "ADP-board rho"),
                         ("rho_b1_adp", "[sanity: ADP baseline must be identical]")]:
            if f"{col}_P" in j.columns:
                print(E.fmt(f"secondary - primary, {lab}",
                            *E.season_block_bootstrap(j, f"{col}_S", f"{col}_P"), width=52))
        # component-level: did the reparameterisation change the projections?
        for _, acol, _n in E.COMPONENT_LEDGER[pos]:
            c = f"mae_{acol}"
            if f"{c}_P" in j.columns:
                d, lo, hi, n = E.season_block_bootstrap(j, f"{c}_S", f"{c}_P")
                if np.isfinite(d) and abs(d) > 1e-9:
                    print(f"    MAE {acol:16s} sec - prim: {d:+8.3f} "
                          f"[{lo:+8.3f}, {hi:+8.3f}]")

    # ---- QB regime: is the rushing stream growing, and does the model see it?
    banner("QB REGIME -- rushing share of realised QB points, by season")
    qp = results[("QB", "primary: 2012+ sample")][0]
    qp = qp[qp.games >= 8].copy()
    rows = []
    for s, g in qp.groupby("season"):
        rush_pts = (g.rush_yards / 10.0 + 6.0 * g.rush_tds + g.rush_bonus).sum()
        pass_pts = (g.pass_yards / 25.0 + 4.0 * g.pass_tds - 2.0 * g.interceptions
                    + g.pass_bonus).sum()
        pr = (g.proj_rush_yards / 10.0 + 6.0 * g.proj_rush_tds).sum()
        pp = (g.proj_pass_yards / 25.0 + 4.0 * g.proj_pass_tds
              - 2.0 * g.proj_interceptions).sum()
        rows.append(dict(season=s, n=len(g),
                         actual_rush_share=rush_pts / (rush_pts + pass_pts),
                         projected_rush_share=pr / (pr + pp)))
    reg = pd.DataFrame(rows)
    print(reg.round(4).to_string(index=False))
    x = reg.season.to_numpy(float)
    for c in ["actual_rush_share", "projected_rush_share"]:
        y = reg[c].to_numpy(float)
        b, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x - x.mean()]),
                                y, rcond=None)
        resid = y - np.column_stack([np.ones(len(x)), x - x.mean()]) @ b
        se = np.sqrt((resid @ resid) / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
        print(f"  {c:22s} slope {b[1]*100:+.3f} pct-points/season "
              f"95% CI [{(b[1]-1.96*se)*100:+.3f}, {(b[1]+1.96*se)*100:+.3f}]")
    print("\n  A model that TRACKS the regime has a projected slope matching the")
    print("  actual one. A model that LAGS it has a flatter projected slope --")
    print("  which is the mechanical signature of averaging a trend.")

    OUT.mkdir(parents=True, exist_ok=True)
    for (pos, label), (players, m) in results.items():
        tag = "primary" if label.startswith("primary") else "secondary"
        m.to_csv(OUT / f"{pos.lower()}_variant_{tag}_metrics.csv", index=False)
    print(f"\nwrote variant metrics to {OUT}")


if __name__ == "__main__":
    main()
