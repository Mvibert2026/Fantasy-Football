#!/usr/bin/env python
"""Driver for the WR component model. Reproduces every number in
`docs/ranking/component-model-wr-pass-1.md`.

    .venv/bin/python -m experiments.bottomup.components.run_wr

EXPLORATORY. Nothing here is a registered confirmatory test. The one test worth
registering is named at the end of the report and has not been run.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import wr_eval as E          # noqa: E402
from experiments.bottomup.components.wr_data import build_panel    # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024


def banner(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


def main() -> None:
    panel = build_panel()
    wf = E.WalkForward(panel=panel, first_target=FIRST, last_target=LAST)
    players, m = wf.run()

    banner("0. LOOK-AHEAD AUDIT -- every fit must have seen only earlier seasons")
    aud = pd.DataFrame(wf.audit)
    print(aud.to_string(index=False))
    assert (aud.max_feature_cutoff < aud.season).all()
    assert (aud.max_outcome_season < aud.season).all()
    assert (aud.n_outcome_reads_at_target == 0).all()
    print("PASS")

    banner("1. UNIVERSE -- frozen before each season, busts retained")
    u = players.groupby("season").agg(
        n=("player_id", "size"),
        n_on_adp_board=("average_pick", "count"),
        zero_game=("games", lambda s: int((s == 0).sum())),
        rookies=("entry", lambda s: int((s == "rookie").sum())),
        mean_actual_pts=("points", "mean"),
    )
    print(u.round(1).to_string())

    banner("2. HEADLINE -- rank correlation vs the three required baselines")
    show = ["season", "n_adp", "adpsub_rho_model", "adpsub_rho_b1_adp",
            "adpsub_rho_b2_prior_points", "adpsub_rho_b3_wavg_ppg"]
    print(m[show].round(3).to_string(index=False))
    print("\nseason-block bootstrap, 4000 reps, paired differences, 95% CI:")
    pairs = [
        ("vs B1 consensus ADP     ", "adpsub_rho_model", "adpsub_rho_b1_adp"),
        ("vs B2 prior-season pts  ", "adpsub_rho_model", "adpsub_rho_b2_prior_points"),
        ("vs B3 weighted prior ppg", "adpsub_rho_model", "adpsub_rho_b3_wavg_ppg"),
        ("B1 ADP vs B3 heuristic  ", "adpsub_rho_b1_adp", "adpsub_rho_b3_wavg_ppg"),
    ]
    for lab, a, b in pairs:
        d, lo, hi, n = E.season_block_bootstrap(m, a, b)
        verdict = "CLEARS 0" if (lo > 0 or hi < 0) else "does NOT clear 0"
        print(f"  {lab} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}  {verdict}")

    banner("2b. same, on the full pre-season universe (no ADP restriction)")
    show2 = ["season", "n", "rho_model", "rho_b2_prior_points", "rho_b3_wavg_ppg"]
    print(m[show2].round(3).to_string(index=False))
    for lab, a, b in [("vs B2 prior pts ", "rho_model", "rho_b2_prior_points"),
                      ("vs B3 heuristic ", "rho_model", "rho_b3_wavg_ppg")]:
        d, lo, hi, n = E.season_block_bootstrap(m, a, b)
        print(f"  {lab} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}")

    banner("3. DECISION-RELEVANT -- what the top 24 actually scored")
    show3 = ["season", "adpsub_top24_model", "adpsub_top24_b1_adp",
             "adpsub_pts_top24_model", "adpsub_pts_top24_b1_adp"]
    print(m[show3].round(3).to_string(index=False))
    for lab, a, b in [("top-24 capture, model - ADP", "adpsub_top24_model",
                       "adpsub_top24_b1_adp"),
                      ("mean pts of top 24, model - ADP", "adpsub_pts_top24_model",
                       "adpsub_pts_top24_b1_adp")]:
        d, lo, hi, n = E.season_block_bootstrap(m, a, b)
        print(f"  {lab:34s} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}")

    banner("4. COMPONENTS -- MAE vs naive persistence (last season's own total)")
    comp = m[["season", "mae_receptions", "mae_naive_receptions",
              "mae_rec_yards", "mae_naive_rec_yards", "mae_rec_tds",
              "mae_naive_rec_tds", "mae_games", "mae_naive_games"]]
    print(comp.round(2).to_string(index=False))
    for c in ["receptions", "rec_yards", "rec_tds", "games", "targets"]:
        d, lo, hi, n = E.season_block_bootstrap(m, f"mae_{c}", f"mae_naive_{c}")
        print(f"  MAE {c:11s} model - naive: {d:+.3f} [{lo:+.3f}, {hi:+.3f}]  "
              f"(negative = model better)")

    banner("5. THE STACKING BONUS -- calibration, reordering, and its ceiling")
    b = m[["season", "bonus_pred_total", "bonus_actual_total"]].copy()
    b["ratio"] = b.bonus_pred_total / b.bonus_actual_total
    print(b.round(2).to_string(index=False))
    print(f"\nmean calibration ratio {b.ratio.mean():.2f} "
          f"(sd {b.ratio.std():.2f})")

    shift = []
    for s in sorted(players.season.unique()):
        ss = players[players.season == s]
        d = (ss.proj_points_base.rank(ascending=False)
             - ss.proj_points.rank(ascending=False)).abs()
        shift.append(dict(season=s, mean_rank_shift=d.mean(), max_rank_shift=d.max(),
                          n_moved_3plus=int((d >= 3).sum()),
                          bonus_share=float(ss.proj_bonus_points.sum()
                                            / ss.proj_points.sum())))
    print("\nhow many WRs the bonus term actually moves:")
    print(pd.DataFrame(shift).round(3).to_string(index=False))

    print("\nORACLE ceiling -- realised bonus substituted for the projected one:")
    orc = []
    for s in sorted(players.season.unique()):
        ss = players[players.season == s]
        act = ss.points.to_numpy(float)
        row = dict(season=s,
                   rho_no_bonus=E.spearman(ss.proj_points_base.to_numpy(float), act),
                   rho_model=E.spearman(ss.proj_points.to_numpy(float), act),
                   rho_oracle=E.spearman(
                       (ss.proj_points_base + ss.rec_bonus).to_numpy(float), act))
        sub = ss[np.isfinite(ss.average_pick)]
        if len(sub) >= 20:
            a = sub.points.to_numpy(float)
            row["adpsub_rho_no_bonus"] = E.spearman(
                sub.proj_points_base.to_numpy(float), a)
            row["adpsub_rho_model"] = E.spearman(sub.proj_points.to_numpy(float), a)
            row["adpsub_rho_oracle"] = E.spearman(
                (sub.proj_points_base + sub.rec_bonus).to_numpy(float), a)
        orc.append(row)
    orc = pd.DataFrame(orc)
    print(orc.round(4).to_string(index=False))
    for lab, a, bb in [("modelled bonus vs none (full universe)", "rho_model", "rho_no_bonus"),
                       ("ORACLE   bonus vs none (full universe)", "rho_oracle", "rho_no_bonus"),
                       ("modelled bonus vs none (ADP board)    ", "adpsub_rho_model", "adpsub_rho_no_bonus"),
                       ("ORACLE   bonus vs none (ADP board)    ", "adpsub_rho_oracle", "adpsub_rho_no_bonus")]:
        d, lo, hi, n = E.season_block_bootstrap(orc, a, bb)
        print(f"  {lab} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}")

    banner("6. IS THERE ANY CEILING SIGNAL LEFT? variance decomposition")
    q = players[players.games >= 8].copy()
    q["ypg_act"] = q.rec_yards / q.games
    q["rate100"] = q.g100 / q.games
    edges = [20, 30, 40, 50, 60, 70, 80]
    q["bin"] = np.digitize(q.ypg_act.to_numpy(float), edges)
    g = q.groupby("bin")
    q["p_hat"] = q["bin"].map(g.g100.sum() / g.games.sum()).astype(float)
    w = q.games.to_numpy(float)
    obs = float(np.average((q.rate100 - q.p_hat) ** 2, weights=w))
    binv = float(np.average(q.p_hat * (1 - q.p_hat) / w, weights=w))
    print(f"n = {len(q)} WR player-seasons with >= 8 games")
    print(f"  observed variance of 100-yd-game rate around the ypg curve : {obs:.5f}")
    print(f"  variance implied by binomial sampling noise alone          : {binv:.5f}")
    print(f"  EXCESS (real between-player spike ability)                 : {obs - binv:+.5f}")

    q["resid"] = q.rate100 - q.p_hat
    lag = q[["player_id", "season", "resid", "games"]].rename(
        columns={"resid": "resid_prev", "games": "games_prev"})
    lag["season"] = lag.season + 1
    j = q.merge(lag, on=["player_id", "season"]).dropna(subset=["resid", "resid_prev"])
    j = j[(j.games >= 8) & (j.games_prev >= 8)]
    r = float(np.corrcoef(j.resid_prev, j.resid)[0, 1])
    se = (1 - r ** 2) / np.sqrt(max(len(j) - 3, 1))
    print(f"  year-over-year persistence of that residual: n={len(j)}  "
          f"r = {r:+.4f}  95% CI [{r - 1.96 * se:+.4f}, {r + 1.96 * se:+.4f}]")

    # the trap: controlling for PRIOR ypg is not controlling for CURRENT ypg
    j2 = players[players.games >= 8].copy()
    j2["bonus_pg"] = j2.rec_bonus / j2.games
    j2["proj_ypg"] = j2.proj_rec_yards / j2.proj_games.replace(0, np.nan)
    lag2 = j2[["player_id", "season", "bonus_pg"]].rename(
        columns={"bonus_pg": "bonus_pg_prev"})
    lag2["season"] = lag2.season + 1
    j3 = j2.merge(lag2, on=["player_id", "season"]).dropna(
        subset=["bonus_pg", "bonus_pg_prev", "proj_ypg"])
    X = np.column_stack([np.ones(len(j3)), j3.proj_ypg.to_numpy(float)])

    def _res(y):
        bta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return y - X @ bta

    pr = float(np.corrcoef(_res(j3.bonus_pg.to_numpy(float)),
                           _res(j3.bonus_pg_prev.to_numpy(float)))[0, 1])
    se2 = (1 - pr ** 2) / np.sqrt(max(len(j3) - 3, 1))
    print(f"  partial corr of bonus/game on its own lag, controlling for the "
          f"model's OWN projected ypg:")
    print(f"    n={len(j3)}  r = {pr:+.4f}  95% CI [{pr - 1.96 * se2:+.4f}, "
          f"{pr + 1.96 * se2:+.4f}]")

    OUT.mkdir(parents=True, exist_ok=True)
    players.to_csv(OUT / "wr_components_walkforward.csv", index=False)
    m.to_csv(OUT / "wr_components_metrics.csv", index=False)
    print(f"\nwrote {OUT / 'wr_components_walkforward.csv'}")
    print(f"wrote {OUT / 'wr_components_metrics.csv'}")


if __name__ == "__main__":
    main()
