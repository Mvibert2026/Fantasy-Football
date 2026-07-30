#!/usr/bin/env python
"""Driver for the RB / QB / TE (and WR re-run) component models.

    .venv/bin/python -m experiments.bottomup.components.run_position RB
    .venv/bin/python -m experiments.bottomup.components.run_position QB --deep
    .venv/bin/python -m experiments.bottomup.components.run_position TE

EXPLORATORY. Nothing here is a registered confirmatory test; thread 094 asks
`strategist` for the one registration worth making and has had no reply. The
sealed 2025 holdout is never opened by this code.

Every section printed here corresponds to a numbered section of
`docs/ranking/component-model-rb-qb-te-pass-1.md`.
"""

from __future__ import annotations

import argparse
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


def banner(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


def run_arm(panel, position, arm="A", **kw):
    wf = E.WalkForward(panel=panel, position=position, first_target=FIRST,
                       last_target=LAST, avail_arm=arm, **kw)
    players, m = wf.run()
    return wf, players, m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("position", choices=["RB", "QB", "TE", "WR"])
    ap.add_argument("--deep", action="store_true",
                    help="QB only: deep 1999+ box-score sample (SECONDARY)")
    args = ap.parse_args()
    pos = args.position

    panel = build_panel()
    wf, players, m = run_arm(panel, pos, arm="A")

    banner(f"{pos} 0. LOOK-AHEAD AUDIT -- every fit saw only earlier seasons")
    aud = pd.DataFrame(wf.audit)
    print(aud.to_string(index=False))
    assert (aud.max_feature_cutoff < aud.season).all()
    assert (aud.max_outcome_season < aud.season).all()
    assert (aud.n_outcome_reads_at_target == 0).all()
    print("PASS")

    banner(f"{pos} 1. UNIVERSE -- frozen before each season, busts retained")
    u = players.groupby("season").agg(
        n=("player_id", "size"), n_on_adp_board=("average_pick", "count"),
        zero_game=("games", lambda s: int((s == 0).sum())),
        rookies=("entry", lambda s: int((s == "rookie").sum())),
        mean_actual_pts=("points", "mean"))
    print(u.round(1).to_string())
    print(f"\nSURVIVORSHIP GUARD: {int((players.games == 0).sum())} of "
          f"{len(players)} player-seasons played zero games and are retained.")

    banner(f"{pos} 2. HEADLINE -- rank correlation vs the three required baselines")
    show = ["season", "n_adp", "adpsub_rho_model", "adpsub_rho_b1_adp",
            "adpsub_rho_b2_prior_points", "adpsub_rho_b3_wavg_ppg"]
    show = [c for c in show if c in m.columns]
    print(m[show].round(3).to_string(index=False))
    print("\nseason-block bootstrap, 4000 reps, paired differences, 95% CI:")
    for lab, a, b in [
            ("vs B1 consensus ADP", "adpsub_rho_model", "adpsub_rho_b1_adp"),
            ("vs B2 prior-season points", "adpsub_rho_model", "adpsub_rho_b2_prior_points"),
            ("vs B3 weighted prior ppg", "adpsub_rho_model", "adpsub_rho_b3_wavg_ppg"),
            ("[power check] B1 ADP vs B3 heuristic", "adpsub_rho_b1_adp",
             "adpsub_rho_b3_wavg_ppg")]:
        print(E.fmt(lab, *E.season_block_bootstrap(m, a, b)))

    banner(f"{pos} 2b. same, on the full pre-season universe (no ADP restriction)")
    print(m[["season", "n", "rho_model", "rho_b2_prior_points",
             "rho_b3_wavg_ppg"]].round(3).to_string(index=False))
    for lab, a, b in [("vs B2 prior points", "rho_model", "rho_b2_prior_points"),
                      ("vs B3 heuristic", "rho_model", "rho_b3_wavg_ppg")]:
        print(E.fmt(lab, *E.season_block_bootstrap(m, a, b)))

    banner(f"{pos} 3. DECISION-RELEVANT -- what the drafted top-k actually scored")
    k = int(m["k"].iloc[0])
    cols = [c for c in ["season", "adpsub_top_model", "adpsub_top_b1_adp",
                        "adpsub_pts_top_model", "adpsub_pts_top_b1_adp"]
            if c in m.columns]
    print(f"k = {k} (what this league starts at {pos}, flex-adjusted)")
    print(m[cols].round(3).to_string(index=False))
    for lab, a, b in [(f"top-{k} capture, model - ADP", "adpsub_top_model",
                       "adpsub_top_b1_adp"),
                      (f"mean pts of top {k}, model - ADP", "adpsub_pts_top_model",
                       "adpsub_pts_top_b1_adp")]:
        print(E.fmt(lab, *E.season_block_bootstrap(m, a, b)))

    banner(f"{pos} 4. COMPONENTS -- MAE vs naive persistence (last season's total)")
    for _, acol, _n in E.COMPONENT_LEDGER[pos]:
        d, lo, hi, n = E.season_block_bootstrap(m, f"mae_{acol}", f"mae_naive_{acol}")
        if np.isfinite(d):
            print(f"  MAE {acol:16s} model - naive: {d:+8.3f} "
                  f"[{lo:+8.3f}, {hi:+8.3f}]   (negative = model better)")

    banner(f"{pos} 5. STACKING BONUS -- calibration, reordering, and its ceiling")
    b = m[["season", "bonus_pred_total", "bonus_actual_total"]].copy()
    b["ratio"] = b.bonus_pred_total / b.bonus_actual_total
    print(b.round(2).to_string(index=False))
    print(f"\nmean calibration ratio {b.ratio.mean():.2f} (sd {b.ratio.std():.2f})")
    fam_cols = [c for c in m.columns if c.startswith("bonus_actual_")
                and c != "bonus_actual_total"]
    if fam_cols:
        tot = m["bonus_actual_total"].sum()
        print("realised bonus points by family, share of all bonus points:")
        for c in fam_cols:
            print(f"    {c.replace('bonus_actual_',''):5s} {m[c].sum():9.1f}"
                  f"   {m[c].sum()/tot:6.1%}")
    print(f"bonus as share of realised points: "
          f"{m.bonus_actual_total.sum()/players.points.sum():.2%}")

    shift = []
    for s in sorted(players.season.unique()):
        ss = players[players.season == s]
        dd = (ss.proj_points_base.rank(ascending=False)
              - ss.proj_points.rank(ascending=False)).abs()
        shift.append(dict(season=s, mean_rank_shift=dd.mean(), max_rank_shift=dd.max(),
                          n_moved_3plus=int((dd >= 3).sum()),
                          bonus_share_of_proj=float(ss.proj_bonus_points.sum()
                                                    / ss.proj_points.sum())))
    sh = pd.DataFrame(shift)
    print("\nhow many players the bonus term actually moves:")
    print(sh.round(3).to_string(index=False))
    print(f"TOTAL moved >= 3 rank positions: {int(sh.n_moved_3plus.sum())} "
          f"of {len(players)} player-seasons; largest single move "
          f"{int(sh.max_rank_shift.max())}")

    print("\nORACLE ceiling -- realised bonus substituted for the projected one:")
    orc = []
    for s in sorted(players.season.unique()):
        ss = players[players.season == s]
        act = ss.points.to_numpy(float)
        row = dict(season=s,
                   rho_no_bonus=E.spearman(ss.proj_points_base.to_numpy(float), act),
                   rho_model=E.spearman(ss.proj_points.to_numpy(float), act),
                   rho_oracle=E.spearman(
                       (ss.proj_points_base + ss.total_bonus).to_numpy(float), act))
        sub = ss[np.isfinite(ss.average_pick)]
        if len(sub) >= 10:
            a = sub.points.to_numpy(float)
            row["adpsub_rho_no_bonus"] = E.spearman(
                sub.proj_points_base.to_numpy(float), a)
            row["adpsub_rho_model"] = E.spearman(sub.proj_points.to_numpy(float), a)
            row["adpsub_rho_oracle"] = E.spearman(
                (sub.proj_points_base + sub.total_bonus).to_numpy(float), a)
        orc.append(row)
    orc = pd.DataFrame(orc)
    print(orc.round(4).to_string(index=False))
    for lab, a, bb in [("modelled bonus vs none (full universe)", "rho_model", "rho_no_bonus"),
                       ("ORACLE   bonus vs none (full universe)", "rho_oracle", "rho_no_bonus"),
                       ("modelled bonus vs none (ADP board)", "adpsub_rho_model", "adpsub_rho_no_bonus"),
                       ("ORACLE   bonus vs none (ADP board)", "adpsub_rho_oracle", "adpsub_rho_no_bonus")]:
        print(E.fmt(lab, *E.season_block_bootstrap(orc, a, bb)))

    banner(f"{pos} 6. IS THERE CEILING SIGNAL LEFT? variance decomposition")
    fams = {"WR": [("rec", "g100", "rec_yards", 100)],
            "TE": [("rec", "g100", "rec_yards", 100)],
            "RB": [("rush", "r100", "rush_yards", 100),
                   ("rec", "g100", "rec_yards", 100)],
            "QB": [("pass", "p300", "pass_yards", 300),
                   ("rush", "r100", "rush_yards", 100)]}[pos]
    q0 = players[players.games >= 8].copy()
    for fam, cnt, ycol, thr in fams:
        q = q0.copy()
        q["ypg_act"] = q[ycol] / q.games
        q["rate"] = q[cnt] / q.games
        edges = np.percentile(q.ypg_act.dropna(), [12.5, 25, 37.5, 50, 62.5, 75, 87.5])
        q["bin"] = np.digitize(q.ypg_act.to_numpy(float), edges)
        g = q.groupby("bin")
        q["p_hat"] = q["bin"].map(g[cnt].sum() / g.games.sum()).astype(float)
        w = q.games.to_numpy(float)
        obs = float(np.average((q.rate - q.p_hat) ** 2, weights=w))
        binv = float(np.average(q.p_hat * (1 - q.p_hat) / w, weights=w))
        print(f"\n  [{fam} >= {thr}]  n = {len(q)} player-seasons with >= 8 games; "
              f"{int(q[cnt].sum())} qualifying games observed")
        print(f"    observed variance of the rate around the ypg curve : {obs:.5f}")
        print(f"    variance implied by binomial sampling noise alone   : {binv:.5f}")
        print(f"    EXCESS (real between-player spike ability)          : {obs - binv:+.5f}")
        q["resid"] = q.rate - q.p_hat
        lag = q[["player_id", "season", "resid", "games"]].rename(
            columns={"resid": "resid_prev", "games": "games_prev"})
        lag["season"] = lag.season + 1
        j = q.merge(lag, on=["player_id", "season"]).dropna(subset=["resid", "resid_prev"])
        j = j[(j.games >= 8) & (j.games_prev >= 8)]
        if len(j) > 30:
            r = float(np.corrcoef(j.resid_prev, j.resid)[0, 1])
            se = (1 - r ** 2) / np.sqrt(max(len(j) - 3, 1))
            print(f"    YoY persistence of that residual: n={len(j)}  r = {r:+.4f}  "
                  f"95% CI [{r - 1.96 * se:+.4f}, {r + 1.96 * se:+.4f}]")

    # ---------------------------------------------------------------- ARMS
    banner(f"{pos} 7. AVAILABILITY -- three arms, one factor apart (pre-declared)")
    _, pB, mB = run_arm(panel, pos, arm="B")
    _, pC, mC = run_arm(panel, pos, arm="C")
    arms = {"A baseline": (players, m), "B injury decomposition": (pB, mB),
            "C free gshare_max3 control": (pC, mC)}
    av = {k2: E.per_season_availability(v[0]) for k2, v in arms.items()}
    print("availability sub-model, mean over seasons:")
    for k2, a in av.items():
        print(f"  {k2:28s} MAE games {a.mae_games.mean():6.3f}   "
              f"bias {a.bias_games.mean():+6.3f}   "
              f"MAE games | returning-from-absent {a.mae_games_returning.mean():6.3f}   "
              f"n_ret/season {a.n_returning.mean():.1f}")
    base_av = av["A baseline"]
    for k2 in ["B injury decomposition", "C free gshare_max3 control"]:
        j = base_av.merge(av[k2], on="season", suffixes=("_A", "_X"))
        for col, lab in [("mae_games", "MAE games, all"),
                         ("mae_games_returning", "MAE games, returning-from-absent")]:
            print(E.fmt(f"{k2[0]} - A  {lab}",
                        *E.season_block_bootstrap(j, f"{col}_X", f"{col}_A")))
    print("\nranking effect of each arm (paired, same seasons):")
    for k2 in ["B injury decomposition", "C free gshare_max3 control"]:
        j = m.merge(arms[k2][1], on="season", suffixes=("_A", "_X"))
        for col, lab in [("rho_model", "full universe rho"),
                         ("adpsub_rho_model", "ADP-board rho")]:
            if f"{col}_A" in j.columns:
                print(E.fmt(f"{k2[0]} - A  {lab}",
                            *E.season_block_bootstrap(j, f"{col}_X", f"{col}_A")))

    banner(f"{pos} 8. WORST CALLS vs the market (arm A), and what arm B did to them")
    adpp = players[np.isfinite(players.average_pick)].copy()
    worst = []
    for s, ss in adpp.groupby("season"):
        ss = ss.copy()
        ss["mrank"] = ss.proj_points.rank(ascending=False)
        ss["arank"] = ss.average_pick.rank()
        ss["trank"] = ss.points.rank(ascending=False)
        ss["cost"] = (ss.mrank - ss.trank).abs() - (ss.arank - ss.trank).abs()
        worst.append(ss)
    worst = pd.concat(worst).nlargest(12, "cost")
    bmap = pB.set_index(["player_id", "season"]).proj_points.rank(ascending=False)
    bb = pB.copy()
    bb["mrank_B"] = bb.groupby("season").proj_points.rank(ascending=False)
    worst = worst.merge(bb[["player_id", "season", "mrank_B", "proj_games"]]
                        .rename(columns={"proj_games": "proj_games_B"}),
                        on=["player_id", "season"], how="left")
    cols = ["season", "name", "arank", "mrank", "mrank_B", "trank", "gshare_1",
            "inj_missed_share_1", "unexp_missed_share_1", "proj_games",
            "proj_games_B", "games"]
    print(worst[[c for c in cols if c in worst.columns]].round(2).to_string(index=False))

    OUT.mkdir(parents=True, exist_ok=True)
    players.to_csv(OUT / f"{pos.lower()}_components_walkforward.csv", index=False)
    m.to_csv(OUT / f"{pos.lower()}_components_metrics.csv", index=False)
    pB.to_csv(OUT / f"{pos.lower()}_components_armB.csv", index=False)
    print(f"\nwrote {OUT / (pos.lower() + '_components_walkforward.csv')}")


if __name__ == "__main__":
    main()
