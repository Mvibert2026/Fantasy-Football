#!/usr/bin/env python
"""Residuals by prior-season-games bucket -- the discovery pass's own terms.

The concurrent discovery pass measured v2 under-reverting toward the mean on
prior-season games: players with 0-4 games in N-1 carry a +0.23 SD residual
(t = 9.3, n = 595) and players with 14-17 carry -0.29 SD (t = -8.8, n = 707).
This reports the same two buckets for every batch-D1 arm, so a fix is
verifiable in the terms the defect was stated in.

Residual = z(realised) - z(projected), standardised WITHIN (position, season)
so a season-level scoring shift cannot enter. Positive = under-projected.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
PLAYERS = _REPO / "experiments" / "bottomup" / "results" / "avail_d1_players"

BUCKETS = [("0-4", 0, 4), ("5-8", 5, 8), ("9-13", 9, 13), ("14-17", 14, 17)]


def _z(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * 0.0


def residuals(d: pd.DataFrame, value: str, proj: str) -> pd.DataFrame:
    d = d.copy()
    d["z_act"] = d.groupby(["position", "season"])[value].transform(_z)
    d["z_proj"] = d.groupby(["position", "season"])[proj].transform(_z)
    d["resid"] = d["z_act"] - d["z_proj"]
    return d


def table(d: pd.DataFrame, label: str, value="points", proj="proj_points") -> pd.DataFrame:
    d = residuals(d, value, proj)
    rows = []
    for name, lo, hi in BUCKETS:
        g = d[(d["games_1"] >= lo) & (d["games_1"] <= hi)]
        if len(g) < 10:
            continue
        r = g["resid"].to_numpy(dtype=float)
        se = r.std(ddof=1) / np.sqrt(len(r)) if len(r) > 1 else np.nan
        rows.append(dict(arm=label, endpoint=f"{value}", bucket=name, n=len(r),
                         resid_sd=r.mean(), t=r.mean() / se if se else np.nan))
    return pd.DataFrame(rows)


def main() -> None:
    which = sys.argv[1:] or ["CTRL-A", "CTRL-D", "B0", "A3", "A5"]
    for pop, flt in (("board (M-panel) veterans",
                      lambda x: x[(x.entry == "veteran") & x.average_pick.notna()]),
                     ("full veteran universe",
                      lambda x: x[x.entry == "veteran"])):
        out = []
        for arm in which:
            p = PLAYERS / f"{arm}.csv.gz"
            if not p.exists():
                continue
            d = flt(pd.read_csv(p))
            out.append(table(d, arm, "points", "proj_points"))
            out.append(table(d, arm, "games", "proj_games"))
        if out:
            df = pd.concat(out, ignore_index=True)
            print(f"\n### {pop}")
            print(df.pivot_table(index=["endpoint", "arm"], columns="bucket",
                                 values="resid_sd").round(3).to_string())
            print("n per bucket:")
            print(df[df.arm == which[0]].pivot_table(
                index="endpoint", columns="bucket", values="n").to_string())


if __name__ == "__main__":
    main()
