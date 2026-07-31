#!/usr/bin/env python
"""v1 sensitivity analyses. **All POST-HOC and labelled as such.**

    .venv/bin/python -m experiments.bottomup.ranking_v1_sensitivity

Run after `ranking_v1.py`; reads its saved player frame, fits nothing, and
touches no season the primary run did not. None of this changes a verdict in
`docs/ranking/ranking-v1-results.md` -- the pre-registered result stands as run.
These exist because three specific things about the primary result need
quantifying rather than asserting:

  S1  DEPTH. Panel E's universe (the full ECR board: 147-202 players per
      position) is roughly 3x deeper than Panel M's, and most of the extra depth
      is players nobody in a ten-team league drafts. Strategist's Ruling 1 item 5
      made `C2` -- the DRAFT-RELEVANT universe -- the endpoint precisely because
      movement among undrafted players is not decision-relevant. So: re-run
      Panel E at the depth the MARKET says is draftable (per season and position,
      the top N of ECR where N = the number of players FFC's ADP board covers at
      that position that season). N is externally determined, not chosen here.

  S2  RESOLUTION. Report the DIRECT 95% CI half-width of each v1-vs-crowd
      contrast beside the pre-registered baseline-vs-baseline MDE proxy, because
      the proxy is contrast-specific and is not guaranteed to bound the contrast
      that matters.

  S3  NON-STATIONARITY (§6.4). Per-season rho for v1 and both crowds, so a regime
      turn is visible instead of averaged away.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.ranking_v1 import (          # noqa: E402
    CONFIG_PATH, OUT, block_metrics, boot_diff)

CFG = json.loads(CONFIG_PATH.read_bytes())
REPS = CFG["evaluation"]["bootstrap"]["reps"]
SEED = CFG["evaluation"]["bootstrap"]["seed"]
PARITY = CFG["evaluation"]["decision_thresholds"]["parity_floor_rho"]


def main() -> None:
    full = pd.read_csv(OUT / "ranking_v1_v1_players.csv", low_memory=False)
    prim = pd.read_csv(OUT / "ranking_v1_v1_primary_family.csv")
    m = pd.read_csv(OUT / "ranking_v1_v1_season_metrics.csv")

    print("=" * 90)
    print("S2  RESOLUTION -- pre-registered MDE proxy vs the DIRECT half-width "
          "of the contrast tested")
    print("=" * 90)
    prim["direct_halfwidth"] = (prim["hi"] - prim["lo"]) / 2
    prim["proxy_understates"] = prim["direct_halfwidth"] > prim["mde"] + 0.02
    print(prim[["panel", "crowd", "position", "delta", "lo", "hi", "mde",
                "direct_halfwidth", "proxy_understates", "verdict"]]
          .round(4).to_string(index=False))

    print("\n" + "=" * 90)
    print("S1  DEPTH-MATCHED PANEL E -- ECR restricted to the market's own "
          "draftable depth (POST-HOC)")
    print("=" * 90)
    rows = []
    for pos in CFG["positions"]:
        k = CFG["evaluation"]["topk"][pos]
        sub = full[(full.position == pos) & full.ecr_pos_rank.notna()
                   & full.season.between(2021, 2024)]
        for season, g in sub.groupby("season"):
            n_market = int(np.isfinite(g["ffc_pos_rank"]).sum())
            if n_market < 10:
                continue
            gd = g.nsmallest(n_market, "ecr_pos_rank")
            r = block_metrics(gd, "E", pos, int(season), k)
            r["n_market_depth"] = n_market
            rows.append(r)
    md = pd.DataFrame(rows)
    md.to_csv(OUT / "ranking_v1_sensitivity_depth_matched.csv", index=False)
    print(md.groupby("position").agg(
        seasons=("season", "nunique"), depth=("n", "mean"),
        rho_v1=("rho_v1", "mean"), rho_ecr=("rho_b2_expert_ecr", "mean")
    ).round(3).to_string())
    print("\n  paired v1 - expert consensus, depth-matched, season bootstrap:")
    for pos in CFG["positions"]:
        s = md[md.position == pos]
        d, lo, hi, n, p = boot_diff(s, "rho_v1", "rho_b2_expert_ecr", REPS, SEED)
        v = ("BEATS" if lo > 0 else "LOSES" if hi < 0
             else "LOSES (pt est below parity floor)" if d < PARITY
             else "PARITY (not edge)")
        print(f"    {pos:3s} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}  p={p:.4f}  {v}")

    print("\n" + "=" * 90)
    print("S3  PER-SEASON rho (§6.4 non-stationarity) -- Panel M, then Panel E")
    print("=" * 90)
    for panel, crowd in [("M", "rho_b1_market_adp"), ("E", "rho_b2_expert_ecr")]:
        sub = m[m.panel == panel]
        t = sub.pivot_table(index="season", columns="position",
                            values=["rho_v1", crowd])
        print(f"\n  panel {panel}  (v1 vs {crowd})")
        print(t.round(3).to_string())


if __name__ == "__main__":
    main()
