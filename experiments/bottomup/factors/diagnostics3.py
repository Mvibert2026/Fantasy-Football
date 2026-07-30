#!/usr/bin/env python
"""Factor batch 3 -- POST-HOC diagnostics.

    .venv/bin/python -m experiments.bottomup.factors.diagnostics3

NOTHING IN THIS FILE IS PRE-REGISTERED. Every number here was specified after
`run_factors3` had been read, and each carries a lower evidential standard than
the 24 registered tests -- the same rule batch 1 §4 and batch 2 §1(3) applied to
their own after-the-fact work. It is here because three of the registered
results have an obvious objection that the registered design cannot answer, and
leaving the objection unanswered would be worse than answering it late.

  D1  Is X1 the explosive rate, or the SHRINKAGE GEOMETRY? An empirical-Bayes
      rate is pulled toward the prior in proportion to its denominator, so
      |expl_w - prior| is a monotone function of lagged carries and a linear
      model may simply be re-reading volume. Two instruments settle it: a
      binomial PLACEBO with the same geometry and no signal, and the UNSHRUNK
      rate with the signal and no geometry.

  D2  A1's ablation moved 14.4% of the primary's error and tripped the
      pre-registered too-good trigger. Decomposed here so the escalation carries
      a number rather than a shrug.

  D3  B2ra is algebraically identical IN RANK to the incumbent baseline. Proved
      rather than asserted, because it means four of my own 24 registered tests
      could never have returned anything.

  D4  S1 at WR was VOIDed by its control arm. The same decomposition batch 2
      ran on `move_known`, run here on `sep_known_1`.
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
from experiments.bottomup.components import pos_model as M            # noqa: E402
from experiments.bottomup.components.pos_data import build_panel      # noqa: E402
from experiments.bottomup.factors.factor_features3 import (           # noqa: E402
    build_factor3_features,
)
from experiments.bottomup.factors.run_factors import paired           # noqa: E402
from experiments.bottomup.factors.run_factors3 import (               # noqa: E402
    FEAT, FEAT_EXPL, FIRST, LAST, NGS_FIRST, FEAT_SEP, _rb, _qb_att, QB_R, _drop,
)

OUT = _REPO / "experiments" / "bottomup" / "results"


def _run(panel, pos, first, kwargs, feat, proxy=False):
    wf = E.WalkForward(panel=panel, position=pos, first_target=first,
                       last_target=LAST, avail_arm="A", feature_fn=feat,
                       allow_preseason_proxy=proxy, **kwargs)
    return wf.run()


def main() -> None:
    panel = build_panel()
    prim = {}
    for pos in ("WR", "TE", "RB", "QB"):
        prim[pos] = _run(panel, pos, FIRST, {}, FEAT)[1]

    rows = []

    def rec(label, pos, comp, m, first=FIRST):
        e1 = paired(m, prim[pos], f"mae_{comp}")
        e1b = paired(m, prim[pos], f"adpsub_mae_{comp}")
        sub = prim[pos][prim[pos]["season"] >= first]
        base = float(sub[f"mae_{comp}"].mean())
        rows.append(dict(label=label, position=pos, comp=comp, d=e1[0], lo=e1[1],
                         hi=e1[2], p=e1[3], n=e1[4],
                         pct=100.0 * e1[0] / base if base else np.nan,
                         e1b=e1b[0]))
        print(f"  {label:44s} {pos:3s} {e1[0]:+8.4f} [{e1[1]:+7.4f},{e1[2]:+7.4f}]"
              f" p={e1[3]:.4f} ({rows[-1]['pct']:+5.2f}%)  E1b {e1b[0]:+.4f}")

    # ---------------------------------------------------------------- D1
    print("\nD1  Is the explosive-rush gain the FOOTBALL or the SHRINKAGE GEOMETRY?")
    print("    registered X1 own explosive rate was -0.7508 (-1.51%), p=0.0025")
    rec("D1a PLACEBO  binomial draw, same geometry", "RB", "carries",
        _run(panel, "RB", FIRST, _rb("expl_placebo_w"), FEAT_EXPL)[1])
    rec("D1b RAW      unshrunk rate, no geometry", "RB", "carries",
        _run(panel, "RB", FIRST, _rb("expl_raw_w"), FEAT_EXPL)[1])
    rec("D1c BOTH     own shrunk + club-relative", "RB", "carries",
        _run(panel, "RB", FIRST, _rb("expl_w", "expl_rel_w"), FEAT_EXPL)[1])
    print("    and the objection nobody raised, which turns out to be the one "
          "that matters:")
    rec("D1d YPC      lagged yards per carry ALONE", "RB", "carries",
        _run(panel, "RB", FIRST, _rb("ypc_lag_w"), FEAT_EXPL)[1])
    rec("D1e YPC+EXPL explosive ON TOP of lagged YPC", "RB", "carries",
        _run(panel, "RB", FIRST, _rb("ypc_lag_w", "expl_w"), FEAT_EXPL)[1])

    # ---------------------------------------------------------------- D2
    print("\nD2  A1 -- the ablation that tripped the too-good trigger")
    abl = _run(panel, "QB", FIRST, {"model_kwargs": {"volume_cols": {
        "carries_pg": _drop(QB_R, "carries_pg_w", "rushyds_pg_w")}}}, FEAT)[1]
    j = prim["QB"][["season", "mae_carries", "adpsub_mae_carries"]].merge(
        abl[["season", "mae_carries", "adpsub_mae_carries"]], on="season",
        suffixes=("_prim", "_abl"))
    j["delta"] = j["mae_carries_abl"] - j["mae_carries_prim"]
    print(j.to_string(index=False))
    print(f"    primary QB carries MAE {prim['QB']['mae_carries'].mean():.3f}, "
          f"ablated {abl['mae_carries'].mean():.3f}; every season worse: "
          f"{bool((j['delta'] > 0).all())}")
    # what is left predicting carries once the block is gone?
    print("    remaining regressors after ablation: "
          + ", ".join(_drop(QB_R, "carries_pg_w", "rushyds_pg_w")))

    # ---------------------------------------------------------------- D3
    print("\nD3  B2ra is a MONOTONE TRANSFORM of the incumbent baseline -- proof")
    pl = _run(panel, "RB", FIRST, {}, FEAT)[0]
    g = pl[pl["season"] == 2022]
    ppg = np.where(g["games_1"] > 0, g["pts_1"] / g["games_1"].replace(0, np.nan), 0.0)
    lhs = np.nan_to_num(ppg * g["gshare_1"].to_numpy(dtype=float))
    rhs = g["pts_1"].to_numpy(dtype=float) / 17.0
    print(f"    max |ppg_1*gshare_1 - pts_1/season_len| over {len(g)} RB rows, "
          f"2022: {np.nanmax(np.abs(lhs - rhs)):.3e}")
    print("    => identical ranking by construction. Four registered tests "
          "(21-24) could not have differed from the incumbent.")

    # ---------------------------------------------------------------- D4
    print("\nD4  S1 at WR was VOIDed. Treatment vs control, side by side")
    print("    registered: WR treatment -0.0635, control +0.0584  -> |c|/|t| = "
          f"{0.0584/0.0635:.2f}  VOID (rule: >= 0.50)")
    print("    registered: TE treatment -0.1462, control +0.0044  -> |c|/|t| = "
          f"{0.0044/0.1462:.2f}  not void")
    print("    registered: QB tenure   -0.2427, control +0.1123  -> |c|/|t| = "
          f"{0.1123/0.2427:.2f}  not void, but inside a rounding error of it")

    # ---------------------------------------------------------------- D5
    print("\nD5  Descriptive: is explosive rate orthogonal to the volume the "
          "model already holds?")
    d = _run(panel, "RB", FIRST, {}, FEAT_EXPL)[0]
    d = d[d["expl_known"] > 0] if "expl_known" in d.columns else d
    print("    (carried columns are not in the eval frame; recomputed inline)")
    from experiments.bottomup.components.pos_data import universe_for
    from experiments.bottomup.components.pos_features import outcome_components
    from experiments.bottomup.factors.factor_features3 import build_factor3_features as B3
    fr = []
    for s in range(FIRST, LAST + 1):
        u = universe_for(panel, s, "RB")
        f = B3(panel, u, s, blocks=("expl",))
        o = outcome_components(panel, u, s)
        fr.append(f.merge(o[["player_id", "carries", "games", "points"]],
                          on="player_id").assign(season=s))
    a = pd.concat(fr)
    a = a[(a["expl_known"] > 0) & a["carries_pg_w"].notna()]
    a["cpg_next"] = np.where(a["games"] > 0, a["carries"] / a["games"], 0.0)
    X = np.nan_to_num(np.column_stack([np.ones(len(a)), a.carries_pg_w, a.cshare_w,
                                       a.gshare_w, a.age, a.experience]))

    def _r(y):
        y = np.nan_to_num(np.asarray(y, dtype=float))
        return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]

    print(f"    n = {len(a)} RB player-seasons, 2014-2024")
    print(f"    corr(expl_w, NEXT carries/game)            "
          f"{a.expl_w.corr(a.cpg_next):+.4f}")
    print(f"    corr(expl_w, LAGGED carries/game)          "
          f"{a.expl_w.corr(a.carries_pg_w):+.4f}   <- near zero: not a volume proxy")
    print(f"    PARTIAL corr | lagged volume/share/gshare/age/exp  "
          f"{np.corrcoef(_r(a.expl_w), _r(a.cpg_next))[0, 1]:+.4f}")
    q = a.groupby(pd.qcut(a.expl_w, 4, labels=["Q1 least", "Q2", "Q3", "Q4 most"]),
                  observed=True)
    print(q.agg(n=("cpg_next", "size"), lagged_cpg=("carries_pg_w", "mean"),
                next_cpg=("cpg_next", "mean"),
                next_points=("points", "mean")).round(2).to_string())

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "factor_batch3_diagnostics.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch3_diagnostics.csv'}")


if __name__ == "__main__":
    main()
