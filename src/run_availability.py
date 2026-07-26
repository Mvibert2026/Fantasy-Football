"""
Produce data/availability_2026.csv and a draft-clock summary.

The summary is written to be read in under 90 seconds with a pick on the line,
so it leads with the decision, states the number, and puts the caveat last.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import numpy as np

import availability as av
import db as dbmod
import draft_sim as ds
from config import DEFAULT_CONFIG

SEASON = 2026
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "availability_2026.csv"
OUT_TXT = Path(__file__).resolve().parent.parent / "data" / "availability_2026_summary.txt"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    args = ap.parse_args()

    conn = dbmod.connect()
    try:
        data = ds.load_season(conn, SEASON)
        meta = conn.execute(
            "SELECT DISTINCT as_of_date, is_preseason_final FROM rankings "
            "WHERE source='fantasypros_ecr' AND season=?", (SEASON,)
        ).fetchone()
    finally:
        conn.close()

    pos_rank = av.positional_ranks(data)
    sources = av.default_ranking_sources(data)
    results: Dict[float, av.AvailabilityResult] = {}
    for sigma in ds.SIGMA_SWEEP:
        results[sigma] = av.simulate_availability(
            data, sigma, args.sims, args.seed + int(sigma * 100), sources=sources
        )

    picks = results[ds.DEFAULT_SIGMA].user_picks

    # ------------------------------------------------------------------ CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["record_type", "sigma", "player", "position", "consensus_rank",
                    "positional_rank", "tier", "pick", "value", "note"])
        for sigma, res in results.items():
            for i, per_pick in res.player_avail.items():
                pos = ds.POSITIONS[data.positions[i]]
                pr = int(pos_rank[i])
                tier = next((t for t, (lo, hi) in av.TIERS[pos].items() if lo <= pr <= hi), "T5+")
                for pk, prob in per_pick.items():
                    w.writerow(["player_available", sigma, data.names[i], pos,
                                int(data.consensus_rank[i]), pr, tier, pk,
                                round(prob, 4), ""])
            for pos, tiers in res.tier_avail.items():
                for t, per_pick in tiers.items():
                    for pk, prob in per_pick.items():
                        w.writerow(["tier_available", sigma, "", pos, "", "", t, pk,
                                    round(prob, 4), f"P(>=1 of {pos} {t} on board)"])
            for pos, per_pick in res.best_avail_dist.items():
                for pk, vals in per_pick.items():
                    s = av.distribution_summary(vals)
                    for k, v in s.items():
                        w.writerow(["best_available_dist", sigma, "", pos, "", "", "", pk,
                                    round(v, 2), f"{k} of best-available {pos} positional rank"])

    # ------------------------------------------------------------- summary
    lines: List[str] = []
    A = lines.append
    A("=" * 78)
    A("DRAFT-CLOCK AVAILABILITY SHEET — 2026, slot 3")
    A("=" * 78)
    A(f"Board: FantasyPros consensus as of {meta[0]}"
      + ("" if meta[1] else "  [NOT FINAL — will move before Week 1]"))
    A(f"{args.sims:,} simulated drafts per setting. Your picks: {picks}")
    A("")
    A("HOW TO READ THIS. Percentages are the chance a player is STILL ON THE BOARD")
    A("when your pick arrives. They come from simulating the other nine teams")
    A("drafting to consensus with noise. They do NOT depend on any projection of")
    A("how many points anyone scores, which is why they are the most reliable")
    A("numbers in this project.")
    A("")
    A("Three columns because the room's discipline is unknown:")
    A("  TIGHT (sigma 5)  = everyone drafts close to consensus")
    A("  NORMAL (sigma 10) = about a round of slippage — the default assumption")
    A("  CHAOTIC (sigma 20) = reaches and slides everywhere")
    A("If a number is similar across all three, trust it. If it swings, the answer")
    A("depends on how your league behaves and you should plan for both.")
    A("")

    # --- headline: who survives to 18 and 23 -------------------------------
    for pk in (18, 23):
        A("-" * 78)
        A(f"PICK {pk} — players most likely to still be there")
        A(f"  {'player':<24} {'pos':<4} {'ECR':>4}   TIGHT  NORMAL CHAOTIC")
        rows = []
        for i in results[ds.DEFAULT_SIGMA].player_avail:
            probs = [results[s].player_avail[i][pk] for s in ds.SIGMA_SWEEP]
            if probs[1] < 0.15 or probs[1] > 0.97:
                continue
            rows.append((probs[1], i, probs))
        rows.sort(key=lambda t: -t[0])
        for _, i, probs in rows[:14]:
            pos = ds.POSITIONS[data.positions[i]]
            A(f"  {data.names[i][:24]:<24} {pos:<4} {int(data.consensus_rank[i]):>4}   "
              + "  ".join(f"{p:5.0%}" for p in probs))
        A("")

    # --- tier survival ------------------------------------------------------
    A("-" * 78)
    A("TIER SURVIVAL — chance at least one player of that tier is still there")
    A("  (tiers are consensus rank bands: see TIERS in src/availability.py)")
    for pos in ("RB", "WR", "TE", "QB"):
        A("")
        A(f"  {pos}")
        A(f"    {'tier':<6} {'ranks':<8} " + " ".join(f"{('pk'+str(p)):>7}" for p in picks[:5]))
        for tname, (lo, hi) in av.TIERS[pos].items():
            cells = []
            for pk in picks[:5]:
                v = results[ds.DEFAULT_SIGMA].tier_avail[pos][tname].get(pk, float("nan"))
                cells.append(f"{v:6.0%} ")
            A(f"    {tname:<6} {f'{lo}-{hi}':<8} " + " ".join(cells))

    # --- best available distribution ---------------------------------------
    A("")
    A("-" * 78)
    A("BEST AVAILABLE BY POSITION — full distribution of positional rank")
    A("  Read: at pick 23 the best RB on the board is usually around the median,")
    A("  but a tenth of the time it is as good as p10 and a tenth as bad as p90.")
    for pk in picks[:4]:
        A(f"\n  PICK {pk}   {'pos':<5} {'p10':>6} {'p25':>6} {'med':>6} {'p75':>6} {'p90':>6}")
        for pos in ("RB", "WR", "TE", "QB"):
            s = av.distribution_summary(
                results[ds.DEFAULT_SIGMA].best_avail_dist[pos][pk]
            )
            if not s:
                continue
            A(f"          {pos:<5} " + " ".join(
                f"{s[k]:6.0f}" for k in ("p10", "p25", "median", "p75", "p90")))

    A("")
    A("=" * 78)
    A("CAVEATS — read once now, not during the draft")
    A("=" * 78)
    A("1. Opponents are modelled with a positional-need penalty derived from this")
    A("   league's roster rules (mechanical, ADR-034) and do NOT react to what you")
    A("   do. A real room responds to positional runs.")
    A("2. The noise level (sigma) is a guess. It is not fitted to any observed")
    A("   draft data, because none exists for this league. That is why every")
    A("   number is shown across three settings.")
    A("3. Opponent boards are drawn from a mixture of ranking sources -- currently")
    A("   one (FantasyPros ECR) -- so this is a no-op today, but it means a second")
    A("   source (MFL ADP, ADR-035) plugs in without changing this model's shape.")
    A("4. The board is consensus as of the date above and will move before Week 1.")
    A("   Re-run this script closer to the draft.")
    A("5. These are availability odds only. They say nothing about whether a")
    A("   player is GOOD — that question runs through a projection whose R-squared")
    A("   is 0.16-0.27, and is much less certain than anything on this sheet.")
    A("6. These are UNCONDITIONAL marginals (Prep mode): they average over every")
    A("   possible draft, not the one actually in progress. Mid-draft, a client")
    A("   simulator re-runs conditioned on real picks made -- see data-contract.md.")

    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print()
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_TXT}")


if __name__ == "__main__":
    main()
