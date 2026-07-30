#!/usr/bin/env python
"""The availability defect: five arms, four positions, one factor apart.

    .venv/bin/python -m experiments.bottomup.components.run_availability

WR pass 1 §7 diagnosed the model's largest error class -- a receiver coming off a
season lost to injury read as permanently finished -- and proposed `nfl.db`'s
79,816 unread injury rows as the fix. This measures that proposal, at every
position, against a free control and against a source nobody had considered.

  A  baseline                    the WR pass 1 availability spec
  B  injury decomposition        + weeks missed carrying an Out/Doubtful report
  C  free control                + gshare_max3. USES NO INJURY DATA.
  D  roster decomposition        + weeks rostered-but-absent / weeks off-roster
  E  roster + depth role         + share of N-1 spent first on the depth chart

A, B and C are pre-committed (`component-model-multipos-precommit.md` §4).
D and E are POST-HOC, added after A-C were run, because measuring B produced the
data-quality finding in §0 below. They are reported at a lower evidential
standard and must not be quoted as if pre-registered.
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
from experiments.bottomup.components.pos_data import (             # noqa: E402
    build_panel, season_length)

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024
ARMS = [("A", "baseline (pre-committed)"),
        ("B", "injury report (pre-committed)"),
        ("C", "free gshare_max3 control (pre-committed)"),
        ("D", "depth-chart roster decomposition (POST-HOC)"),
        ("E", "roster + depth role (POST-HOC)")]


def banner(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


def coverage_table(panel) -> pd.DataFrame:
    """§0. Why arms D and E exist. What share of MISSED WEEKS does each source
    actually account for? Measured on the panel, not asserted."""
    fr, inj, dep = panel._frame, panel._injury, panel._depth
    rows = []
    for pos in ["QB", "RB", "WR", "TE"]:
        d = fr[(fr.position == pos) & (fr.season.between(2011, 2024))].copy()
        d["slen"] = d.season.map(season_length)
        d = d.merge(inj, on=["player_id", "season"], how="left") \
             .merge(dep, on=["player_id", "season"], how="left")
        for c in ["inj_out_wks", "depth_wks"]:
            d[c] = d[c].fillna(0)
        d["missed"] = (d.slen - d.games).clip(lower=0)
        d["dc_absent"] = np.minimum((d.depth_wks - d.games).clip(lower=0), d.missed)
        for lab, lo, hi in [("1-3", 1, 3), ("4-8", 4, 8), ("9+", 9, 99)]:
            s = d[(d.missed >= lo) & (d.missed <= hi)]
            if len(s) < 10:
                continue
            rows.append(dict(
                pos=pos, missed_games=lab, n=len(s),
                injury_report_covers=100 * s.inj_out_wks.clip(upper=s.missed).sum()
                / max(s.missed.sum(), 1),
                depth_chart_covers=100 * s.dc_absent.sum() / max(s.missed.sum(), 1)))
    return pd.DataFrame(rows)


def main() -> None:
    panel = build_panel()

    banner("0. WHY ARMS D AND E EXIST -- share of MISSED WEEKS each source explains")
    print(coverage_table(panel).round(1).to_string(index=False))
    print("""
The injury report answers the question backwards. It covers a quarter to a third
of SHORT absences and 2.5-4.8% of absences of nine games or more -- because a
player placed on season-ending IR drops off the weekly report entirely. The
absences that destroy a projection are exactly the ones it cannot see. Verified
by hand: Dak Prescott has NO injury rows for 2020 (ankle, Week 5, season over);
Deshaun Watson has two for 2017 with zero 'Out' (ACL, season over); J.K. Dobbins
and Michael Thomas have none for 2021 (both missed the whole year).""")

    results = {}
    for pos in ["RB", "QB", "TE", "WR"]:
        for arm, _lab in ARMS:
            wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                               last_target=LAST, avail_arm=arm)
            players, m = wf.run()
            results[(pos, arm)] = (players, E.per_season_availability(players), m)
        print(f"ran {pos}: {len(ARMS)} arms")

    banner("1. AVAILABILITY SUB-MODEL -- does the arm predict GAMES better?")
    for pos in ["RB", "QB", "TE", "WR"]:
        print(f"\n--- {pos} ---")
        base = results[(pos, "A")][1]
        print(f"  arm A absolute: MAE games {base.mae_games.mean():.3f}, "
              f"MAE on returning-from-absent {base.mae_games_returning.mean():.3f} "
              f"(n={base.n_returning.mean():.0f}/season)")
        for arm, lab in ARMS[1:]:
            j = base.merge(results[(pos, arm)][1], on="season", suffixes=("_A", "_X"))
            for col, cl in [("mae_games", "all players"),
                            ("mae_games_returning", "returning-from-absent")]:
                print(E.fmt(f"{arm} - A  MAE games, {cl}",
                            *E.season_block_bootstrap(j, f"{col}_X", f"{col}_A"),
                            width=44))

    banner("2. DOES IT MOVE THE RANKING? (the question that actually matters)")
    for pos in ["RB", "QB", "TE", "WR"]:
        print(f"\n--- {pos} ---")
        bm = results[(pos, "A")][2]
        for arm, lab in ARMS[1:]:
            j = bm.merge(results[(pos, arm)][2], on="season", suffixes=("_A", "_X"))
            for col, cl in [("rho_model", "full universe"),
                            ("adpsub_rho_model", "ADP board")]:
                if f"{col}_A" in j.columns:
                    print(E.fmt(f"{arm} - A  rho, {cl}",
                                *E.season_block_bootstrap(j, f"{col}_X", f"{col}_A"),
                                width=44))

    banner("3. THE NAMED CASES -- projected games, arm by arm")
    cases = [("A.J. Green", 2020), ("Keenan Allen", 2023), ("Adam Thielen", 2020),
             ("DeAndre Hopkins", 2023), ("Cooper Kupp", 2024),
             ("Deebo Samuel Sr.", 2021), ("Davante Adams", 2020),
             ("Patrick Mahomes", 2018), ("Deshaun Watson", 2018),
             ("Dak Prescott", 2021), ("Saquon Barkley", 2021),
             ("Michael Thomas", 2022), ("J.K. Dobbins", 2022)]
    frames = {}
    for pos in ["RB", "QB", "TE", "WR"]:
        for arm, _ in ARMS:
            frames[(pos, arm)] = results[(pos, arm)][0]
    rows = []
    for name, season in cases:
        for pos in ["RB", "QB", "TE", "WR"]:
            base = frames[(pos, "A")]
            hit = base[(base.name == name) & (base.season == season)]
            if not len(hit):
                continue
            r = dict(player=name, season=season, pos=pos,
                     actual_games=float(hit.games.iloc[0]))
            for arm, _ in ARMS:
                fdf = frames[(pos, arm)]
                h2 = fdf[(fdf.name == name) & (fdf.season == season)]
                r[f"proj_g_{arm}"] = float(h2.proj_games.iloc[0]) if len(h2) else np.nan
            r["inj_share"] = float(hit.inj_missed_share_1.iloc[0])
            r["rostered_absent"] = float(hit.rostered_absent_share_1.iloc[0])
            r["offroster"] = float(hit.offroster_share_1.iloc[0])
            rows.append(r)
    print(pd.DataFrame(rows).round(2).to_string(index=False))

    OUT.mkdir(parents=True, exist_ok=True)
    allm = []
    for (pos, arm), (_p, av, m) in results.items():
        mm = m.copy()
        mm["position"], mm["arm"] = pos, arm
        allm.append(mm.merge(av, on="season", how="left"))
    pd.concat(allm, ignore_index=True).to_csv(
        OUT / "availability_arms_metrics.csv", index=False)
    print(f"\nwrote {OUT / 'availability_arms_metrics.csv'}")


if __name__ == "__main__":
    main()
