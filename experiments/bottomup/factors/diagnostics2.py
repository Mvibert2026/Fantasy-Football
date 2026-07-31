#!/usr/bin/env python
"""Post-hoc diagnostics for factor batch 2. EVERYTHING HERE IS POST-HOC and is
reported at a lower evidential standard than the pre-registered E1b/E1a/E2.

    .venv/bin/python -m experiments.bottomup.factors.diagnostics2

Written BEFORE any batch-2 arm was fitted, so the splits are not chosen to
flatter a result that already exists.

Three questions the headline table cannot answer:

  1. **Does the batch-1 harm pattern survive real rosters?** Batch 1 §4 found the
     #28 harm concentrated in the high-measured-vacancy bucket -- the bucket the
     depth-chart proxy is known to contaminate. If that was the mechanism, the
     concentration should weaken or vanish under V2. This reproduces exactly the
     batch-1 split, on both the old proxy and the new roster feature, side by
     side.

  2. **How much do the two vacancy measurements actually disagree?** A factor
     re-test on better data is only interesting if the data really is different.
     Reported as the distribution of V2 - V1 per club-season, not as an average.

  3. **How many players would an insight sentence actually fire for?** The
     founder's ask is a rendered sentence, and a factor that moves nobody cannot
     support one no matter how it grades. Counts, per season, of ADP-board
     players with a non-null new-OC / moved / vacancy signal.
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

from experiments.bottomup.components import pos_eval as E              # noqa: E402
from experiments.bottomup.components.pos_data import (                 # noqa: E402
    build_panel, universe_for,
)
from experiments.bottomup.factors.run_factors2 import (                # noqa: E402
    FEAT, FEAT_B2, FEAT_V1, RB_C, RB_T, REC_V, FIRST, LAST, _add,
)


def run(panel, pos, **kw):
    wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                       last_target=LAST, avail_arm="A", **kw)
    return wf.run()


def _features(panel, pos, fn, cols):
    out = []
    for s in range(FIRST, LAST + 1):
        u = universe_for(panel, s, pos)
        f = fn(panel, u, s)
        keep = [c for c in cols if c in f.columns]
        out.append(f[["player_id", "season"] + keep])
    return pd.concat(out, ignore_index=True)


def main() -> None:
    panel = build_panel()

    print("=" * 92)
    print("1. #28 -- does the batch-1 harm pattern survive REAL ROSTERS?")
    print("   Batch 1 §4: harm concentrated in the high-measured-vacancy bucket,")
    print("   which is exactly where the depth-chart proxy is contaminated.")
    print("=" * 92)
    for pos, v1_spec, v2_spec, acol, pcol, vac1, vac2 in [
        ("RB",
         {"carries_pg": _add(RB_C, "vac_cshare"), "tpg": _add(RB_T, "vac_tshare")},
         {"carries_pg": _add(RB_C, "vac2_cshare"), "tpg": _add(RB_T, "vac2_tshare")},
         "carries", "proj_carries", "vac_cshare", "vac2_cshare"),
        ("WR",
         {"tpg": _add(REC_V, "vac_tshare")},
         {"tpg": _add(REC_V, "vac2_tshare")},
         "targets", "proj_targets", "vac_tshare", "vac2_tshare"),
        ("TE",
         {"tpg": _add(REC_V, "vac_tshare")},
         {"tpg": _add(REC_V, "vac2_tshare")},
         "targets", "proj_targets", "vac_tshare", "vac2_tshare"),
    ]:
        pl_p, _ = run(panel, pos, feature_fn=FEAT)
        pl_1, _ = run(panel, pos, feature_fn=FEAT_V1, allow_preseason_proxy=True,
                      model_kwargs={"volume_cols": v1_spec})
        pl_2, _ = run(panel, pos, feature_fn=FEAT_B2, allow_preseason_proxy=True,
                      model_kwargs={"volume_cols": v2_spec})
        fx1 = _features(panel, pos, FEAT_V1, [vac1, "changed_team"])
        fx2 = _features(panel, pos, FEAT_B2, [vac2, "moved_club"])

        j = (pl_p[["player_id", "season", pcol, acol, "average_pick"]]
             .merge(pl_1[["player_id", "season", pcol]], on=["player_id", "season"],
                    suffixes=("_p", "_1"))
             .merge(pl_2[["player_id", "season", pcol]].rename(
                 columns={pcol: f"{pcol}_2"}), on=["player_id", "season"])
             .merge(fx1, on=["player_id", "season"], how="left")
             .merge(fx2, on=["player_id", "season"], how="left"))
        for tag in ("p", "1", "2"):
            j[f"e_{tag}"] = (j[f"{pcol}_{tag}"] - j[acol]).abs()

        print(f"\n  {pos} {acol} -- by MEASURED vacancy tercile "
              f"(each arm split on ITS OWN vacancy measure)")
        rows = []
        for lbl, vcol, ecol in (("V1 depth-chart proxy", vac1, "e_1"),
                                ("V2 real rosters", vac2, "e_2")):
            q = pd.qcut(j[vcol].rank(method="first"), 3,
                        labels=["low", "mid", "high"])
            g = j.groupby(q).agg(n=("e_p", "size"), primary=("e_p", "mean"),
                                 arm=(ecol, "mean"))
            g["delta"] = g["arm"] - g["primary"]
            for bucket, r in g.iterrows():
                rows.append(dict(arm=lbl, bucket=bucket, n=int(r["n"]),
                                 primary=r["primary"], arm_mae=r["arm"],
                                 delta=r["delta"]))
        print(pd.DataFrame(rows).round(3).to_string(index=False))

        board = j[j["average_pick"].notna()]
        if len(board) > 50:
            print(f"  ADP board only (n={len(board)}): primary "
                  f"{board.e_p.mean():.3f} | V1 {board.e_1.mean():+.3f} "
                  f"({board.e_1.mean()-board.e_p.mean():+.4f}) | V2 "
                  f"{board.e_2.mean():.3f} "
                  f"({board.e_2.mean()-board.e_p.mean():+.4f})")

        print(f"\n  {pos} -- how much do the two vacancy measures DISAGREE?")
        d = (j[vac2] - j[vac1]).dropna()
        print(f"    V2 - V1 per player-season: mean {d.mean():+.4f}, "
              f"sd {d.std():.4f}, "
              f"10th {d.quantile(0.10):+.4f}, 90th {d.quantile(0.90):+.4f}, "
              f"|diff| > 0.05 for {100*(d.abs() > 0.05).mean():.1f}% of rows")
        m1 = j["changed_team"].fillna(0.0) > 0
        m2 = j["moved_club"].fillna(0.0) > 0
        print(f"    'moved club': proxy says {int(m1.sum())}, "
              f"rosters say {int(m2.sum())}, they disagree on "
              f"{int((m1 ^ m2).sum())} of {len(j)} player-seasons")

    print("\n" + "=" * 92)
    print("3. HOW MANY PLAYERS WOULD AN INSIGHT SENTENCE FIRE FOR?")
    print("   A factor that moves nobody cannot support a sentence however it grades.")
    print("=" * 92)
    for pos in ("WR", "RB", "TE"):
        rows = []
        for s in range(FIRST, LAST + 1):
            board = E.adp.load_adp(s, position=pos)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else [])
            if not extra:
                continue
            u = universe_for(panel, s, pos, extra_ids=extra)
            f = FEAT_B2(panel, u, s)
            b = f[f["player_id"].isin(extra)]
            if not len(b):
                continue
            rows.append(dict(
                season=s, on_board=len(b),
                oc_known=int((b["oc_known"] > 0).sum()),
                new_oc=int(((b["oc_known"] > 0) & (b["new_oc"] > 0)).sum()),
                moved=int((b["moved_club"] > 0).sum()),
                high_vac=int((b["vac2_tshare"] > 0.30).sum())))
        if rows:
            t = pd.DataFrame(rows)
            print(f"\n  {pos}")
            print(t.to_string(index=False))
            print(f"  totals: {t.on_board.sum()} board player-seasons, "
                  f"new_oc fires for {t.new_oc.sum()} "
                  f"({100*t.new_oc.sum()/t.on_board.sum():.1f}%), "
                  f"moved for {t.moved.sum()} "
                  f"({100*t.moved.sum()/t.on_board.sum():.1f}%)")


if __name__ == "__main__":
    main()
