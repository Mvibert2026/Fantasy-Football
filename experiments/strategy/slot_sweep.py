"""FR-109 step 4: run every strategy at EVERY draft slot, not a random one.

`run_strategies.py` draws the user's slot uniformly 1-10 per simulation, so its
headline margins are already pooled over slots -- but nothing in it reports a
per-slot margin at the primary sigma, and its one slot table is taken from the
LAST sigma cell rather than the primary one (fixed in this session).

That matters because the VBD arm's behaviour is bimodal in slot (FR-109 step 3):
at slot 1 it takes RB1 first overall in 100% of drafts, at slots 5-10 it takes no
RB until round 11-12. So "Zero RB vs VBD" is a different comparison at every
seat, and at the seats where VBD already waits the two arms are close to the same
strategy -- which pooling hides.

Also reported: the ROSTER OVERLAP between each arm and VBD, per slot. A margin
measured between two arms that drafted the same players is not evidence about
strategy; it is evidence that the contrast was absent.

    .venv/bin/python -m experiments.strategy.slot_sweep --sims 300
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from experiments.strategy import audit_vbd as auditmod  # noqa: E402
from experiments.strategy import board as boardmod  # noqa: E402
from experiments.strategy import sim as simmod  # noqa: E402
from experiments.strategy.run_strategies import (  # noqa: E402
    FFC_SEASONS, RNG_SEED, grade, season_bootstrap_paired, sign_test)

BASELINE = "vbd"
METRICS = (("B", "realistic points"), ("A", "best-ball points"),
           ("playoff", "P(make playoffs)"), ("title", "P(win title)"))


def run(sims: int, source: str, seasons: Sequence[int], rounds_total: int,
        out_path: Path) -> Dict:
    conn = auditmod._conn()
    min_players = simmod.N_TEAMS * (rounds_total - 1)
    strategies = simmod.PRIMARY_STRATEGIES

    boards = {}
    for s in seasons:
        boards[s] = boardmod.build_board(conn, s, source, min_players)
        print(f"[{source} {s}] board n={len(boards[s].pos_idx)} weeks={boards[s].n_weeks}")

    # acc[slot][strategy][season][metric] -> list
    acc: Dict[int, Dict[str, Dict[int, Dict[str, List[float]]]]] = {
        slot: {name: {s: defaultdict(list) for s in seasons} for name in strategies}
        for slot in range(simmod.N_TEAMS)}
    first_rb: Dict[int, Dict[str, List[int]]] = {
        slot: defaultdict(list) for slot in range(simmod.N_TEAMS)}
    overlap: Dict[int, Dict[str, List[float]]] = {
        slot: defaultdict(list) for slot in range(simmod.N_TEAMS)}
    illegal: Dict[int, Dict[str, int]] = {slot: defaultdict(int)
                                          for slot in range(simmod.N_TEAMS)}

    for season in seasons:
        b = boards[season]
        n = len(b.pos_idx)
        sd = np.where(np.isnan(b.pick_sd), np.nanmedian(b.pick_sd), b.pick_sd)
        # Same z-draws as run_strategies.py for this season, so the numbers are
        # comparable to the pooled run rather than a fresh realisation.
        rng = np.random.default_rng(RNG_SEED + season * 1000)
        zs = rng.standard_normal((sims, n))
        for i in range(sims):
            noise = zs[i] * sd
            for slot in range(simmod.N_TEAMS):
                rosters_by_strategy = {}
                for name, strat in strategies.items():
                    rosters, legal = simmod.simulate_draft(b, strat, slot, noise, rounds_total)
                    if not legal:
                        illegal[slot][name] += 1
                        continue
                    r = simmod.evaluate(rosters, b, slot)
                    a = acc[slot][name][season]
                    a["A"].append(r.points_A)
                    a["B"].append(r.points_B)
                    a["playoff"].append(float(r.made_playoffs))
                    a["title"].append(float(r.won_title))
                    first_rb[slot][name].append(r.first_rb_round)
                    rosters_by_strategy[name] = set(rosters[slot])
                base = rosters_by_strategy.get(BASELINE)
                if base:
                    for name, rs in rosters_by_strategy.items():
                        if name == BASELINE:
                            continue
                        overlap[slot][name].append(len(rs & base) / max(len(base), 1))
        print(f"  season {season} done")

    out: Dict = {"source": source, "sims": sims, "rounds_total": rounds_total,
                 "seasons": list(seasons), "slots": {}}

    print(f"\n{'='*104}")
    print(f"PER-SLOT BEHAVIOUR -- {source}, primary sigma (FFC measured std_dev), "
          f"{sims} sims x {len(seasons)} seasons per slot")
    print(f"{'='*104}")
    print(f"{'slot':>4s} " + " ".join(f"{n:>13s}" for n in strategies))
    print(f"{'':>4s} " + " ".join(f"{'mean 1st RB rd':>13s}" for _ in strategies))
    for slot in range(simmod.N_TEAMS):
        row = []
        for name in strategies:
            v = first_rb[slot][name]
            row.append(f"{statistics.fmean(v):13.2f}" if v else f"{'--':>13s}")
        print(f"{slot+1:4d} " + " ".join(row))

    print(f"\n{'roster overlap with the VBD arm (fraction of VBD picks also taken)':^104s}")
    others = [n for n in strategies if n != BASELINE]
    print(f"{'slot':>4s} " + " ".join(f"{n:>15s}" for n in others))
    for slot in range(simmod.N_TEAMS):
        row = [f"{statistics.fmean(overlap[slot][n]):15.3f}" if overlap[slot][n]
               else f"{'--':>15s}" for n in others]
        print(f"{slot+1:4d} " + " ".join(row))

    n_tests = 0
    for metric, label in METRICS:
        print(f"\n--- paired margin vs '{BASELINE}' by slot, resampling SEASONS "
              f"(n={len(seasons)}); metric: {label}")
        print(f"{'slot':>4s} " + " ".join(f"{n:>27s}" for n in others))
        for slot in range(simmod.N_TEAMS):
            cells = []
            for name in others:
                margins = {}
                for s in seasons:
                    a, bb = acc[slot][name][s][metric], acc[slot][BASELINE][s][metric]
                    if not a or not bb:
                        continue
                    margins[s] = statistics.fmean(a) - statistics.fmean(bb)
                pt, lo, hi = season_bootstrap_paired(margins)
                g = grade(pt, lo, hi)
                k, nn, p, minp = sign_test(list(margins.values()))
                n_tests += 1
                out["slots"].setdefault(str(slot + 1), {}).setdefault(metric, {})[name] = dict(
                    point=pt, lo=lo, hi=hi, grade=g, sign_k=k, sign_n=nn, sign_p=p,
                    per_season=margins)
                fmt = "{:+7.3f}" if metric in ("playoff", "title") else "{:+7.1f}"
                cells.append(f"{fmt.format(pt)} [{fmt.format(lo)},{fmt.format(hi)}] {g[:4]:>4s}")
            print(f"{slot+1:4d} " + " ".join(f"{c:>27s}" for c in cells))

    for slot in range(simmod.N_TEAMS):
        out["slots"].setdefault(str(slot + 1), {})["mean_first_rb_round"] = {
            n: (statistics.fmean(first_rb[slot][n]) if first_rb[slot][n] else None)
            for n in strategies}
        out["slots"][str(slot + 1)]["roster_overlap_with_vbd"] = {
            n: (statistics.fmean(overlap[slot][n]) if overlap[slot][n] else None)
            for n in others}
        out["slots"][str(slot + 1)]["illegal_rosters"] = dict(illegal[slot])

    out["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} paired interval tests in this slot sweep; at 5% that is "
          f"~{0.05 * n_tests:.1f} false 'clears zero' results expected by chance. ====")
    print("==== These are per-slot SPLITS of an already-reported pooled comparison. "
          "They are diagnostics of where the contrast lives, not new tests. ====")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {out_path}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=300)
    ap.add_argument("--source", default="ffc")
    ap.add_argument("--rounds", type=int, default=simmod.N_ROUNDS_FULL)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else REPO / "data" / "qa" / \
        f"fr109-slot-sweep-{a.source}-r{a.rounds}.json"
    run(a.sims, a.source, FFC_SEASONS, a.rounds, out)


if __name__ == "__main__":
    main()
