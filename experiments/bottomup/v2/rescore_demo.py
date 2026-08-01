#!/usr/bin/env python
"""Portability demonstration (batch-B1, descriptive — 0 tests contributed).

    python3 -m experiments.bottomup.v2.rescore_demo [--arm G1a]

Claim demonstrated: the SAME stat-line artifact, re-scored under three league
configs, produces DIFFERENT within-position orders with ZERO refitting. The
"zero refitting" part is structural: this script imports no model class and the
scoring layer contains no fit call; its inputs are a committed CSV.

This is the capability the consensus-derived board structurally cannot have
(ADR-069): consensus is one fixed order produced for one generic ruleset.
"""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import pandas as pd

from .scoring_layer import CONFIGS, rank_within_position

_REPO = Path(__file__).resolve().parents[3]
OUT = _REPO / "experiments" / "bottomup" / "results"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="G1a")
    ap.add_argument("--season", type=int, default=2024)
    ap.add_argument("--depth", type=int, default=24,
                    help="within-position depth compared")
    args = ap.parse_args()

    src = OUT / f"ranking_v2_{args.arm}_players.csv"
    d = pd.read_csv(src)
    d = d[d["season"] == args.season]
    print(f"stat lines: {src.name}, season {args.season}, {len(d)} rows")

    ranked = {name: rank_within_position(d, cfg) for name, cfg in CONFIGS.items()}

    rows = []
    for (a, b) in itertools.combinations(CONFIGS, 2):
        for pos in ("QB", "RB", "WR", "TE"):
            ra = ranked[a]
            rb = ranked[b]
            ra = ra[(ra.position == pos) & (ra.pos_rank_cfg <= args.depth)]
            rb = rb[(rb.position == pos) & (rb.pos_rank_cfg <= args.depth)]
            j = ra[["player_id", "pos_rank_cfg"]].merge(
                rb[["player_id", "pos_rank_cfg"]], on="player_id",
                how="inner", suffixes=("_a", "_b"))
            moved = int((j.pos_rank_cfg_a != j.pos_rank_cfg_b).sum())
            maxmove = int((j.pos_rank_cfg_a - j.pos_rank_cfg_b).abs().max()) \
                if len(j) else 0
            rows.append(dict(config_a=a, config_b=b, position=pos,
                             top=args.depth, n_common=len(j),
                             n_rank_changed=moved, max_move=maxmove))
    rep = pd.DataFrame(rows)
    rep.to_csv(OUT / f"ranking_v2_{args.arm}_rescore_demo.csv", index=False)
    print(rep.to_string(index=False))
    print("\nZero fitting calls occurred: this script imports no model class; "
          "the scoring layer is arithmetic on stored stat-line columns.")


if __name__ == "__main__":
    main()
