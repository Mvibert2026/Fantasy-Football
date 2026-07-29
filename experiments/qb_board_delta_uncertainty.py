"""Part 2 of the QB-board diagnostic: how much of the +20 survives uncertainty,
and what is actually driving the QB curve's steepness.

Run: python experiments/qb_board_delta_uncertainty.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import db as dbmod  # noqa: E402
import make_board as mb  # noqa: E402
from scoring import LEAGUE, ReplacementLevels  # noqa: E402

SEASON = 2026


def main():
    conn = dbmod.connect(dbmod.DB_PATH)
    levels = ReplacementLevels()
    base = levels.baselines()
    train = mb.resolve_training_seasons(conn, SEASON)

    # ---- A. bootstrap CIs on the shipped board
    print("=" * 78)
    print("A. SHIPPED BOARD, TOP 15, WITH BOOTSTRAP 95% CI ON VBD")
    print("   (season-level resample, 5 units -- CIs are wide by construction)")
    print("=" * 78)
    board, curves = mb.build_board(conn, SEASON, n_bootstrap=2000)
    print(f"{'#':>3} {'player':<22} {'pos':<3} {'vbd':>7} {'95% CI':>19} {'cons':>5} {'d':>5}")
    for r in board[:15]:
        print(f"{r.overall_rank:>3} {r.player[:22]:<22} {r.position:<3} {r.vbd:>7.1f} "
              f"[{r.vbd_lo:>7.1f},{r.vbd_hi:>7.1f}] {r.consensus_rank:>5} "
              f"{r.delta_vs_consensus:>+5d}")
    allen = next(r for r in board if "Allen" in r.player)
    print(f"\n  Allen VBD {allen.vbd:.1f}, 95% CI [{allen.vbd_lo:.1f}, {allen.vbd_hi:.1f}]")
    overlapping = [r for r in board[:40]
                   if not (r.vbd_lo > allen.vbd_hi or r.vbd_hi < allen.vbd_lo)]
    print(f"  Players in the top 40 whose VBD CI OVERLAPS Allen's: {len(overlapping)}")
    print(f"    overall ranks {overlapping[0].overall_rank} .. "
          f"{overlapping[-1].overall_rank}")

    # ---- B. per-season QB slope: is this a regime, or stable?
    print()
    print("=" * 78)
    print("B. LEAVE-ONE-SEASON-OUT AND PER-SEASON QB CURVE SLOPE")
    print("   The whole QB result is b_QB. If b_QB is one or two seasons, say so.")
    print("=" * 78)
    obs = mb.collect_observations(conn, train)
    print(f"{'seasons used':<28} {'b_QB':>8} {'VBD@QB1':>9} {'b_RB':>8} {'VBD@RB1':>9}")
    for pos_label, seasons in (
        [("ALL " + str(train), train)]
        + [(f"single {s}", [s]) for s in train]
        + [(f"drop {s}", [x for x in train if x != s]) for s in train]
    ):
        row = {}
        for pos in ("QB", "RB"):
            pairs = []
            for s in seasons:
                pairs.extend(obs[s].get(pos, []))
            f = mb._fit_one(pos, pairs)
            row[pos] = (f.slope_log_rank, f.slope_log_rank * (0 - np.log(base[pos])))
        print(f"{pos_label:<28} {row['QB'][0]:>8.1f} {row['QB'][1]:>9.1f} "
              f"{row['RB'][0]:>8.1f} {row['RB'][1]:>9.1f}")

    # ---- C. who were the consensus QB1-3, and how much did they rush?
    print()
    print("=" * 78)
    print("C. CONSENSUS TOP-3 QBs BY TRAINING SEASON -- rushing share of their points")
    print("=" * 78)
    for s in train:
        rows = mb._positional_ranks(
            mb._consensus_board(conn, s, source=mb.TRAINING_SOURCE)
        ).get("QB", [])[:3]
        pts = {}
        rush = {}
        for g in dbmod.actual_season_outcomes(conn, s):
            st = {c: g[c] for c in dbmod.SCORING_STAT_COLUMNS}
            pid = g["player_id"]
            from scoring import score_offensive_game
            pts[pid] = pts.get(pid, 0.0) + score_offensive_game(st)
            rush[pid] = rush.get(pid, 0.0) + (st.get("rushing_yards") or 0) / 10.0 + (
                st.get("rushing_tds") or 0) * 6
        line = []
        for i, r in enumerate(rows, 1):
            p = pts.get(r["player_id"], 0.0)
            ru = rush.get(r["player_id"], 0.0)
            share = (ru / p * 100) if p > 0 else 0.0
            line.append(f"QB{i} {(r['player_name'] or '')[:16]:<16} {p:6.1f}pts rush {share:4.0f}%")
        print(f"  {s}: " + " | ".join(line))

    # ---- D. replacement-level sensitivity
    print()
    print("=" * 78)
    print("D. QB REPLACEMENT-LEVEL SENSITIVITY (streaming raises effective replacement)")
    print("=" * 78)
    cQB = curves["QB"]
    print(f"{'QB replacement rank':<24} {'VBD@QB1':>9} {'Allen board rank (approx)':>28}")
    for br in (8, 10, 12, 14, 16, 18):
        v = cQB.predict(1) - cQB.predict(br)
        others = sorted(
            [curves[p].predict(i) - curves[p].predict(base[p])
             for p in ("RB", "WR", "TE") for i in range(1, mb.RELEVANT_DEPTH[p] + 1)],
            reverse=True,
        )
        rank = sum(1 for x in others if x > v) + 1
        print(f"QB{br:<22} {v:>9.1f} {rank:>28}")

    conn.close()


if __name__ == "__main__":
    main()
