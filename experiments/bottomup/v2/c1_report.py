#!/usr/bin/env python
"""Regenerate the results table and verdict table in `docs/ranking/batch-C1-results.md`
from the graded CSV, in place, between the marker comments.

Exists so the live results document can never drift from
`experiments/bottomup/results/factor_c1_contrasts.csv` — a hand-typed table that
disagrees with the artifact is worse than no table, and this batch is expected to
be interrupted and resumed. The narrative sections above and below the markers
are hand-written and are never touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.v2.run_c1 import (                        # noqa: E402
    CONTRASTS_CSV, FACTOR_NAME, factor_verdict, grade)

DOC = _REPO / "docs" / "ranking" / "batch-C1-results.md"
START, END = "<!--C1-TABLE-START-->", "<!--C1-TABLE-END-->"

#: placebo null maxima per position, from `factor_c1_placebo_replication.csv`.
#: The interim floor a treatment delta must clear while the strategist ruling on
#: the WIN criterion is outstanding. Read from the artifact, never hand-typed.
REP_CSV = _REPO / "experiments" / "bottomup" / "results" / \
    "factor_c1_placebo_replication.csv"


def placebo_bounds() -> dict:
    if not REP_CSV.exists():
        return {}
    r = pd.read_csv(REP_CSV)
    return {p: (float(g["delta"].min()), float(g["delta"].max()),
                float(np.quantile(g["delta"], 0.95)), len(g))
            for p, g in r.groupby("position")}


def fmt(df: pd.DataFrame) -> str:
    pb = placebo_bounds()
    out = ["| factor | position | n | coverage | control ρ | arm ρ | Δ | 95% CI | "
           "vs placebo null | verdict | BH |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        cov = "—" if not np.isfinite(r["coverage"]) else f"{r['coverage']:.3f}"
        b = pb.get(r["position"])
        if b is None or not np.isfinite(r["delta"]):
            vs = "—"
        else:
            lo_p, hi_p, q95, k = b
            vs = ("**clears**" if r["delta"] > hi_p else
                  ("**below**" if r["delta"] < lo_p else "inside"))
        name = "F0 PLACEBO" if r["factor"] == "F0" else r["factor"]
        out.append(
            f"| {name} | {r['position']} | {int(r['n_seasons'])} | {cov} | "
            f"{r['ctrl_mean_rho']:.4f} | {r['arm_mean_rho']:.4f} | "
            f"{r['delta']:+.4f} | [{r['lo']:+.4f}, {r['hi']:+.4f}] | {vs} | "
            f"{r['verdict']} | {'yes' if r['bh_reject_campaign'] else '—'} |")
    return "\n".join(out)


def main() -> None:
    df = grade(pd.read_csv(CONTRASTS_CSV))
    order = {f: i for i, f in enumerate(
        ["F0", "F1", "F1k", "F2", "F2k", "F3", "F3k", "F4", "F4k", "F5", "F5k",
         "F6"])}
    df = df.sort_values(["factor", "position"],
                        key=lambda s: s.map(order) if s.name == "factor" else s)

    treat = [f for f in df["factor"].unique() if not f.endswith("k") and f != "F0"]
    verdicts = ["| factor | verdict | positions won | basis |", "|---|---|---|---|"]
    n_inc = 0
    for f in ["F0"] + treat:
        g = df[df["factor"] == f]
        v = ("HARNESS DEFECT — not a factor verdict" if f == "F0"
             else factor_verdict(g))
        won = ", ".join(g.loc[g["verdict"] == "WIN", "position"]) or "—"
        if v.startswith("INCLUDE"):
            n_inc += 1
        verdicts.append(f"| **{f}** {FACTOR_NAME[f]} | **{v}** | {won} | "
                        f"{len(g)} cells graded |")

    n_graded = len([f for f in treat])
    tally = (f"\n**Included factors: {n_inc}. Candidate factors measured: "
             f"{n_graded} of 6.**\n")

    body = ("\n### Results table\n\n" + fmt(df)
            + "\n\n### Factor verdicts\n\n" + "\n".join(verdicts) + "\n" + tally)

    doc = DOC.read_text()
    a, b = doc.index(START) + len(START), doc.index(END)
    DOC.write_text(doc[:a] + body + doc[b:])
    print(fmt(df))
    print("\n".join(verdicts))
    print(tally)


if __name__ == "__main__":
    main()
