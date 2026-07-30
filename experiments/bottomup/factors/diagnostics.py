#!/usr/bin/env python
"""Post-hoc diagnostics for factor batch 1. EVERYTHING HERE IS POST-HOC and is
reported at a lower evidential standard than the pre-registered E1/E2.

    .venv/bin/python -m experiments.bottomup.factors.diagnostics

Four questions the headline table cannot answer:
  1. Does the primary still reproduce pass 1 under the new feature builder?
  2. What are the MAE effect sizes in ABSOLUTE terms (a rank-free number is
     unreadable -- statistical-guardrails.md 3.5)?
  3. Is the #19 T1 gain a real signal or a low-volume artifact? Split by
     projected-volume tercile and restrict to the ADP board.
  4. Where is the #28 V1 harm concentrated -- team changers, or everyone?
"""

from __future__ import annotations

import sys
import warnings
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E             # noqa: E402
from experiments.bottomup.components.pos_data import build_panel      # noqa: E402
from experiments.bottomup.components.pos_features import build_features  # noqa: E402
from experiments.bottomup.factors.factor_features import (            # noqa: E402
    build_factor_features,
)
from experiments.bottomup.factors.run_factors import (                # noqa: E402
    FEAT, FEAT_PROXY, RB_C, RB_T, REC_V, T1_KW, _add, _td_over, paired,
)

FIRST, LAST = 2014, 2024


def run(panel, pos, **kw):
    wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                       last_target=LAST, avail_arm="A", **kw)
    return wf.run()


def main() -> None:
    panel = build_panel()

    # ---- 1. reproduction check -------------------------------------------
    print("=" * 84)
    print("1. PRIMARY REPRODUCTION -- old feature builder vs. new one")
    print("=" * 84)
    for pos in ("WR", "RB", "QB", "TE"):
        _, m_old = run(panel, pos, feature_fn=build_features)
        _, m_new = run(panel, pos, feature_fn=FEAT)
        cols = [c for c in m_old.columns if c.startswith(("rho_", "mae_", "adpsub_"))]
        same = all(np.allclose(m_old[c].fillna(-9), m_new[c].fillna(-9))
                   for c in cols)
        print(f"  {pos}: {len(cols)} metric columns identical: {same}")

    # ---- 2/3. #19 T1 -- absolute size, volume terciles, ADP board ----------
    print("\n" + "=" * 84)
    print("2/3. FACTOR #19 T1 -- effect size in absolute terms, and where it lives")
    print("=" * 84)
    e1_of = {"WR": "rec_tds", "TE": "rec_tds", "RB": "rush_tds", "QB": "pass_tds"}
    for pos in ("WR", "TE", "RB", "QB"):
        pl_p, m_p = run(panel, pos, feature_fn=FEAT)
        pl_a, m_a = run(panel, pos, feature_fn=FEAT,
                        model_kwargs=_td_over(pos, T1_KW))
        acol = e1_of[pos]
        pcol = {"rec_tds": "proj_rec_tds", "rush_tds": "proj_rush_tds",
                "pass_tds": "proj_pass_tds"}[acol]
        vcol = {"WR": "proj_targets", "TE": "proj_targets",
                "RB": "proj_carries", "QB": "proj_attempts"}[pos]
        base = float(m_p[f"mae_{acol}"].mean())
        d = float(m_a[f"mae_{acol}"].mean() - base)
        naive = float(m_p[f"mae_naive_{acol}"].mean()) \
            if f"mae_naive_{acol}" in m_p.columns else np.nan
        print(f"\n  {pos} {acol}: primary MAE {base:.3f} "
              f"(naive persistence {naive:.3f}), T1 {d:+.4f} "
              f"= {100*d/base:+.1f}% of the primary's own error")
        j = pl_p[["player_id", "season", pcol, acol, vcol]].merge(
            pl_a[["player_id", "season", pcol]], on=["player_id", "season"],
            suffixes=("_p", "_a"))
        j["e_p"] = (j[f"{pcol}_p"] - j[acol]).abs()
        j["e_a"] = (j[f"{pcol}_a"] - j[acol]).abs()
        j["terc"] = pd.qcut(j[vcol].rank(method="first"), 3,
                            labels=["low vol", "mid vol", "high vol"])
        g = j.groupby("terc").agg(n=("e_p", "size"), mae_primary=("e_p", "mean"),
                                  mae_T1=("e_a", "mean"))
        g["delta"] = g["mae_T1"] - g["mae_primary"]
        print(g.round(4).to_string())
        # ADP board only -- the players a draft actually chooses between
        if "average_pick" in pl_p.columns:
            sub = j.merge(pl_p[["player_id", "season", "average_pick"]],
                          on=["player_id", "season"], how="left")
            sub = sub[sub["average_pick"].notna()]
            if len(sub) > 50:
                print(f"    ADP board only (n={len(sub)}): primary "
                      f"{sub.e_p.mean():.3f} -> T1 {sub.e_a.mean():.3f} "
                      f"({sub.e_a.mean()-sub.e_p.mean():+.4f})")

    # ---- 4. #28 V1 -- where is the harm? ----------------------------------
    print("\n" + "=" * 84)
    print("4. FACTOR #28 V1 -- where the harm is concentrated")
    print("=" * 84)
    for pos, spec, acol, pcol in [
            ("RB", {"carries_pg": _add(RB_C, "vac_cshare"),
                    "tpg": _add(RB_T, "vac_tshare")}, "carries", "proj_carries"),
            ("WR", {"tpg": _add(REC_V, "vac_tshare")}, "targets", "proj_targets")]:
        pl_p, _ = run(panel, pos, feature_fn=FEAT)
        pl_a, _ = run(panel, pos, feature_fn=FEAT_PROXY,
                      allow_preseason_proxy=True,
                      model_kwargs={"volume_cols": spec})
        f_extra = []
        for s in range(FIRST, LAST + 1):
            from experiments.bottomup.components.pos_data import universe_for
            u = universe_for(panel, s, pos)
            ff = FEAT_PROXY(panel, u, s)
            f_extra.append(ff[["player_id", "season", "changed_team",
                               "vac_tshare", "vac_cshare"]])
        fx = pd.concat(f_extra, ignore_index=True)
        j = pl_p[["player_id", "season", pcol, acol]].merge(
            pl_a[["player_id", "season", pcol]], on=["player_id", "season"],
            suffixes=("_p", "_a")).merge(fx, on=["player_id", "season"], how="left")
        j["e_p"] = (j[f"{pcol}_p"] - j[acol]).abs()
        j["e_a"] = (j[f"{pcol}_a"] - j[acol]).abs()
        j["moved"] = j["changed_team"].fillna(0.0) > 0
        g = j.groupby("moved").agg(n=("e_p", "size"), mae_primary=("e_p", "mean"),
                                   mae_V1=("e_a", "mean"))
        g["delta"] = g["mae_V1"] - g["mae_primary"]
        print(f"\n  {pos} {acol}, by whether the Week-1 proxy says he changed club")
        print(g.round(3).to_string())
        vq = pd.qcut(j["vac_cshare" if pos == "RB" else "vac_tshare"].rank(
            method="first"), 3, labels=["low vacancy", "mid", "high vacancy"])
        g2 = j.groupby(vq).agg(n=("e_p", "size"), mae_primary=("e_p", "mean"),
                               mae_V1=("e_a", "mean"))
        g2["delta"] = g2["mae_V1"] - g2["mae_primary"]
        print(f"  {pos} {acol}, by measured vacancy on his club")
        print(g2.round(3).to_string())


if __name__ == "__main__":
    main()
