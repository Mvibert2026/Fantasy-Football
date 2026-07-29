"""
Produce data/availability_2026.csv and a draft-clock summary.

The summary is written to be read in under 90 seconds with a pick on the line,
so it leads with the decision, states the number, and puts the caveat last.

MULTI-SLOT (FR-057 part 1, ADR pending). The draft-slot selector (FR-034)
changes the pick sequence everywhere in the app, but availability used to be
computed for exactly one slot (`cfg.user_draft_slot`) -- change slot in the
UI and the CSV/JSON simply had no rows for the new pick numbers, so numbers
went absent rather than wrong.

THE FIX EXPLOITS A STRUCTURAL FACT, not a schema change: for a FIXED team
count and round count, `pick_order()` (which team owns which overall pick
number) does not depend on which team is "the user" -- only the ROLE played
by that team (best-player-available vs. need-driven opponent model) does.
Consequently, at any given pick number, exactly one slot's simulation ever
records a value there (the slot that pick belongs to), and running the sweep
for every slot 1..teams produces a UNION of disjoint pick numbers -- no two
slots' runs ever write the same (player, pick) cell. Verified empirically
before this was built (no overlap across all 10 slots of the primary
league, scratchpad check, 2026-07-29) and is asserted again in
`tests/test_run_availability_multi_slot.py`.

That means `by_player`/`by_tier` do NOT need a new nesting level keyed by
slot -- they need FULL pick-number coverage instead of the ~16-pick slice
one slot's simulation used to produce. A client that knows which pick
numbers belong to whichever slot is currently selected (the same snake-order
arithmetic the slot selector already uses elsewhere in the app) can look
those pick numbers up directly in the existing `by_player`/`by_tier` shape.
See `docs/data-contract.md` and handoff thread 093 for the frontend-facing
explanation.

The founder's OWN slot (`cfg.user_draft_slot`) keeps using the exact legacy
code path (module-level free functions for the primary league, `engine=None`)
so its numbers are BYTE-IDENTICAL to what shipped before this change -- see
`_engine_for_slot`'s docstring for why the generic `DraftEngine` path is not
used there even though it would probably converge to the same numbers.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

import availability as av
import db as dbmod
import draft_sim as ds
import league_config as lc
from config import DEFAULT_CONFIG

SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _out_paths(league_id: str) -> tuple[Path, Path]:
    if league_id == lc.PRIMARY_LEAGUE_ID:
        return DATA_DIR / "availability_2026.csv", DATA_DIR / "availability_2026_summary.txt"
    d = DATA_DIR / "leagues" / league_id
    return d / "availability.csv", d / "availability_summary.txt"


def _engine_for_slot(cfg: lc.LeagueConfig, slot: int) -> Optional[ds.DraftEngine]:
    """Draft engine for treating `slot` as the user, for any slot in
    [1, cfg.teams] -- not just cfg.user_draft_slot.

    The founder's own slot keeps the EXACT pre-existing code path: for the
    primary league that is `engine=None` (the original module-level free
    functions ds.pick_order()/ds.opponent_pick()/ds.strategy_bpa(), driven by
    module constants N_TEAMS/N_ROUNDS/USER_SLOT/MECHANICAL_NEED_TARGETS), for
    any other league it is `ds.DraftEngine(cfg)` unmodified -- both exactly
    what this module called before this function existed.

    Every OTHER slot uses `ds.DraftEngine` on a copy of `cfg` with only
    `user_draft_slot` swapped. This is deliberately NOT unified with the
    founder's-own-slot path even though DraftEngine should reproduce the
    free-function numbers for the primary league at slot 3: a scratchpad
    check (2026-07-29) found the two paths differ by up to ~0.02 in absolute
    probability at late picks (200-sim comparison, sigma=10, seed=42) --
    almost certainly a legal_mask "picks left" off-by-one between the two
    parallel implementations (ds._legal_mask counts only the DEF reserved
    round; DraftEngine.legal_mask counts ALL unscored_starter_positions,
    which is the same set of exactly one round for the primary league, so
    the two SHOULD match and the discrepancy deserves its own investigation
    -- logged in docs/ideas-inbox.md, not chased down here). Keeping the
    founder's own slot on its already-shipped, already-verified path means
    this change cannot silently move a number the founder has already seen.
    """
    if slot == cfg.user_draft_slot:
        return None if cfg.is_primary else ds.DraftEngine(cfg)
    return ds.DraftEngine(dataclasses.replace(cfg, user_draft_slot=slot))


def _merge_player(dst: Dict[int, Dict[int, float]], src: Dict[int, Dict[int, float]]) -> None:
    for i, picks in src.items():
        dst.setdefault(i, {}).update(picks)


def _merge_tier(
    dst: Dict[str, Dict[str, Dict[int, float]]], src: Dict[str, Dict[str, Dict[int, float]]]
) -> None:
    for pos, tiers in src.items():
        d_pos = dst.setdefault(pos, {})
        for t, picks in tiers.items():
            d_pos.setdefault(t, {}).update(picks)


def _merge_best(
    dst: Dict[str, Dict[int, List[int]]], src: Dict[str, Dict[int, List[int]]]
) -> None:
    for pos, picks in src.items():
        dst.setdefault(pos, {}).update(picks)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    ap.add_argument(
        "--league", default=lc.PRIMARY_LEAGUE_ID,
        help="league_id of a saved config under data/leagues/, or 'primary' (default)",
    )
    ap.add_argument(
        "--slots", default="all",
        help="'all' (default, FR-057 part 1) to sweep every draft slot 1..teams, or a "
             "comma-separated list of slot numbers for a faster partial run.",
    )
    args = ap.parse_args()
    cfg = (
        lc.CURRENT_LEAGUE if args.league == lc.PRIMARY_LEAGUE_ID else lc.LeagueConfig.load(args.league)
    )
    OUT_CSV, OUT_TXT = _out_paths(cfg.league_id)

    if args.slots == "all":
        slots = list(range(1, cfg.teams + 1))
    else:
        slots = [int(s) for s in args.slots.split(",")]

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

    t0 = time.monotonic()
    per_slot_seconds: Dict[int, float] = {}
    # sigma -> merged, ALL-SLOTS structures (union of disjoint pick numbers --
    # see module docstring for why this merge never collides).
    player_avail: Dict[float, Dict[int, Dict[int, float]]] = {s: {} for s in ds.SIGMA_SWEEP}
    tier_avail: Dict[float, Dict[str, Dict[str, Dict[int, float]]]] = {s: {} for s in ds.SIGMA_SWEEP}
    best_dist: Dict[float, Dict[str, Dict[int, List[int]]]] = {s: {} for s in ds.SIGMA_SWEEP}
    picks_by_slot: Dict[int, List[int]] = {}

    for slot in slots:
        t_slot = time.monotonic()
        engine = _engine_for_slot(cfg, slot)
        picks_by_slot[slot] = ds.user_pick_numbers() if engine is None else engine.user_pick_numbers()
        for sigma in ds.SIGMA_SWEEP:
            r = av.simulate_availability(
                data, sigma, args.sims, args.seed + int(sigma * 100) + slot * 100_000,
                sources=sources, engine=engine,
            )
            _merge_player(player_avail[sigma], r.player_avail)
            _merge_tier(tier_avail[sigma], r.tier_avail)
            _merge_best(best_dist[sigma], r.best_avail_dist)
        per_slot_seconds[slot] = time.monotonic() - t_slot
        print(f"  slot {slot}: {per_slot_seconds[slot]:.1f}s "
              f"(picks {picks_by_slot[slot]})")

    total_seconds = time.monotonic() - t0
    own_picks = picks_by_slot[cfg.user_draft_slot]

    # ------------------------------------------------------------------ CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["record_type", "sigma", "player", "position", "consensus_rank",
                    "positional_rank", "tier", "pick", "value", "note"])
        for sigma in ds.SIGMA_SWEEP:
            for i, per_pick in player_avail[sigma].items():
                pos = ds.POSITIONS[data.positions[i]]
                pr = int(pos_rank[i])
                tier = next((t for t, (lo, hi) in av.TIERS[pos].items() if lo <= pr <= hi), "T5+")
                for pk, prob in per_pick.items():
                    w.writerow(["player_available", sigma, data.names[i], pos,
                                int(data.consensus_rank[i]), pr, tier, pk,
                                round(prob, 4), ""])
            for pos, tiers in tier_avail[sigma].items():
                for t, per_pick in tiers.items():
                    for pk, prob in per_pick.items():
                        w.writerow(["tier_available", sigma, "", pos, "", "", t, pk,
                                    round(prob, 4), f"P(>=1 of {pos} {t} on board)"])
            for pos, per_pick in best_dist[sigma].items():
                for pk, vals in per_pick.items():
                    s = av.distribution_summary(vals)
                    for k, v in s.items():
                        w.writerow(["best_available_dist", sigma, "", pos, "", "", "", pk,
                                    round(v, 2), f"{k} of best-available {pos} positional rank"])

    # ------------------------------------------------------------- summary
    lines: List[str] = []
    A = lines.append
    A("=" * 78)
    A(f"DRAFT-CLOCK AVAILABILITY SHEET -- {SEASON}, slot {cfg.user_draft_slot} "
      f"(full sweep: slots {slots[0]}-{slots[-1]})")
    A("=" * 78)
    A(f"Board: FantasyPros consensus as of {meta[0]}"
      + ("" if meta[1] else "  [NOT FINAL -- will move before Week 1]"))
    A(f"{args.sims:,} simulated drafts per setting, per slot. Your picks: {own_picks}")
    A(f"Full sweep across {len(slots)} slots took {total_seconds:.1f}s "
      f"({total_seconds / max(len(slots), 1):.1f}s/slot average).")
    A("")
    A("HOW TO READ THIS. Percentages are the chance a player is STILL ON THE BOARD")
    A("when your pick arrives. They come from simulating the other nine teams")
    A("drafting to consensus with noise. They do NOT depend on any projection of")
    A("how many points anyone scores, which is why they are the most reliable")
    A("numbers in this project.")
    A("")
    A("Three columns because the room's discipline is unknown:")
    A("  TIGHT (sigma 5)  = everyone drafts close to consensus")
    A("  NORMAL (sigma 10) = about a round of slippage -- the default assumption")
    A("  CHAOTIC (sigma 20) = reaches and slides everywhere")
    A("If a number is similar across all three, trust it. If it swings, the answer")
    A("depends on how your league behaves and you should plan for both.")
    A("")
    A("NOTE (FR-057 part 1): the CSV/JSON this run produces cover EVERY draft")
    A("slot's own pick numbers, not just the slot above -- switching slots in the")
    A("app now finds real numbers instead of absent ones. This text summary")
    A("still narrates only the slot configured above (cfg.user_draft_slot).")
    A("")

    # --- headline: who survives to the user's 2nd and 3rd picks ------------
    for pk in own_picks[1:3]:
        A("-" * 78)
        A(f"PICK {pk} -- players most likely to still be there")
        A(f"  {'player':<24} {'pos':<4} {'ECR':>4}   TIGHT  NORMAL CHAOTIC")
        rows = []
        for i in player_avail[ds.DEFAULT_SIGMA]:
            probs = [player_avail[s][i].get(pk) for s in ds.SIGMA_SWEEP]
            if any(p is None for p in probs):
                continue
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
    A("TIER SURVIVAL -- chance at least one player of that tier is still there")
    A("  (tiers are consensus rank bands: see TIERS in src/availability.py)")
    for pos in ("RB", "WR", "TE", "QB"):
        A("")
        A(f"  {pos}")
        A(f"    {'tier':<6} {'ranks':<8} " + " ".join(f"{('pk'+str(p)):>7}" for p in own_picks[:5]))
        for tname, (lo, hi) in av.TIERS[pos].items():
            cells = []
            for pk in own_picks[:5]:
                v = tier_avail[ds.DEFAULT_SIGMA].get(pos, {}).get(tname, {}).get(pk, float("nan"))
                cells.append(f"{v:6.0%} ")
            A(f"    {tname:<6} {f'{lo}-{hi}':<8} " + " ".join(cells))

    # --- best available distribution ---------------------------------------
    A("")
    A("-" * 78)
    A("BEST AVAILABLE BY POSITION -- full distribution of positional rank")
    A("  Read: at pick 23 the best RB on the board is usually around the median,")
    A("  but a tenth of the time it is as good as p10 and a tenth as bad as p90.")
    for pk in own_picks[:4]:
        A(f"\n  PICK {pk}   {'pos':<5} {'p10':>6} {'p25':>6} {'med':>6} {'p75':>6} {'p90':>6}")
        for pos in ("RB", "WR", "TE", "QB"):
            s = av.distribution_summary(best_dist[ds.DEFAULT_SIGMA].get(pos, {}).get(pk, []))
            if not s:
                continue
            A(f"          {pos:<5} " + " ".join(
                f"{s[k]:6.0f}" for k in ("p10", "p25", "median", "p75", "p90")))

    A("")
    A("=" * 78)
    A("CAVEATS -- read once now, not during the draft")
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
    A("   player is GOOD -- that question runs through a projection whose R-squared")
    A("   is 0.16-0.27, and is much less certain than anything on this sheet.")
    A("6. These are UNCONDITIONAL marginals (Prep mode): they average over every")
    A("   possible draft, not the one actually in progress. Mid-draft, a client")
    A("   simulator re-runs conditioned on real picks made -- see data-contract.md.")
    A("7. All slots but your own (cfg.user_draft_slot) use a generalized draft")
    A("   engine (ds.DraftEngine) instead of the original hand-tuned primary-league")
    A("   code path. A scratchpad check found up to ~0.02 absolute probability")
    A("   difference between the two paths at late picks for the SAME slot -- not")
    A("   yet root-caused (docs/ideas-inbox.md). Your own slot is unaffected.")

    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print()
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_TXT}")
    print(f"total sweep time: {total_seconds:.1f}s across {len(slots)} slots "
          f"({args.sims:,} sims x {len(ds.SIGMA_SWEEP)} sigmas each)")


if __name__ == "__main__":
    main()
