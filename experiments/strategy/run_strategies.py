"""FR-085 driver: run every strategy against every season and report the paired
comparison against VBD.

    .venv/bin/python -m experiments.strategy.run_strategies              # primary
    .venv/bin/python -m experiments.strategy.run_strategies --sims 100   # quick
    .venv/bin/python -m experiments.strategy.run_strategies --rounds 11  # no-tail check
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from experiments.strategy import board as boardmod  # noqa: E402
from experiments.strategy import sim as simmod  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
FFC_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
ECR_SEASONS = (2021, 2022, 2023, 2024)
RNG_SEED = 20260730

# sigma configs. "ffc_measured" uses FFC's own per-player std_dev of realised mock
# pick position -- the calibration `src/draft_sim.py` assumption 1 says does not
# exist. It does; it is the std_dev column.
SIGMA_CONFIGS = {
    "ffc": [("measured", None), ("flat5", 5.0), ("flat10", 10.0), ("flat20", 20.0)],
    "ecr": [("flat10", 10.0), ("flat5", 5.0), ("flat20", 20.0)],
}
PRIMARY_SIGMA = {"ffc": "measured", "ecr": "flat10"}
BASELINE_STRATEGY = "vbd"


def season_bootstrap_paired(margins_by_season: Dict[int, float], n_boot: int = 8000,
                            seed: int = RNG_SEED) -> Tuple[float, float, float]:
    seasons = sorted(margins_by_season)
    d = [margins_by_season[s] for s in seasons]
    if not d:
        return float("nan"), float("nan"), float("nan")
    point = statistics.fmean(d)
    if len(d) < 2:
        return point, float("nan"), float("nan")
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        vals.append(statistics.fmean([d[rng.randrange(len(d))] for _ in d]))
    vals.sort()
    return point, vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


def sign_test(margins: Sequence[float]) -> Tuple[int, int, float, float]:
    d = [x for x in margins if x != 0]
    n = len(d)
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    k = sum(1 for x in d if x > 0)
    from math import comb
    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1))
    return k, n, min(1.0, 2.0 * tail / (2 ** n)), min(1.0, 2.0 / (2 ** n))


def grade(point: float, lo: float, hi: float) -> str:
    if any(math.isnan(x) for x in (point, lo, hi)):
        return "NO-CI"
    if lo <= 0.0 <= hi:
        return "NULL"
    half = (hi - lo) / 2.0
    if half <= 0:
        return "NO-CI"
    return "SURVIVES" if abs(point) / (half / 1.96) >= 3.0 else "MARGINAL"


def run(sims: int, rounds_total: int, sources: Sequence[str], out_path: Path) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(db._CREATE_SCORING_VIEW_SQL)
    min_players = simmod.N_TEAMS * (rounds_total - 1)

    results: Dict = {"sims": sims, "rounds_total": rounds_total,
                     "min_players_needed": min_players, "sources": {}}
    n_tests = 0

    for source in sources:
        seasons = FFC_SEASONS if source == "ffc" else ECR_SEASONS
        src_out: Dict = {"seasons": list(seasons), "board_layers": {}, "sigma": {}}
        boards = {}
        for s in seasons:
            b = boardmod.build_board(conn, s, source, min_players)
            boards[s] = b
            layers = {int(k): int((b.layer == k).sum()) for k in (1, 2, 3)}
            src_out["board_layers"][s] = dict(total=len(b.pos_idx), by_layer=layers,
                                              n_weeks=b.n_weeks)
            print(f"[{source} {s}] board n={len(b.pos_idx)} layers={layers} weeks={b.n_weeks}")

        for sig_name, sig_val in SIGMA_CONFIGS[source]:
            per_strategy: Dict[str, Dict[int, Dict[str, float]]] = defaultdict(dict)
            per_strategy_slot: Dict[str, Dict[str, List[float]]] = defaultdict(
                lambda: defaultdict(list))
            illegal: Dict[str, int] = defaultdict(int)
            first_rb: Dict[str, List[float]] = defaultdict(list)

            for season in seasons:
                b = boards[season]
                n = len(b.pos_idx)
                if sig_val is None:
                    sd = np.where(np.isnan(b.pick_sd), np.nanmedian(b.pick_sd), b.pick_sd)
                else:
                    sd = np.full(n, sig_val)
                # Common random numbers: one z-draw and one slot per (season, sim),
                # shared by every strategy AND every sigma config.
                rng = np.random.default_rng(RNG_SEED + season * 1000)
                zs = rng.standard_normal((sims, n))
                slots = rng.integers(0, simmod.N_TEAMS, size=sims)

                acc: Dict[str, Dict[str, List[float]]] = {
                    name: defaultdict(list) for name in simmod.ALL_STRATEGIES}
                for i in range(sims):
                    noise = zs[i] * sd
                    slot = int(slots[i])
                    for name, strat in simmod.ALL_STRATEGIES.items():
                        rosters, legal = simmod.simulate_draft(
                            b, strat, slot, noise, rounds_total)
                        if not legal:
                            illegal[name] += 1
                            continue
                        r = simmod.evaluate(rosters, b, slot)
                        acc[name]["A"].append(r.points_A)
                        acc[name]["B"].append(r.points_B)
                        acc[name]["playoff"].append(float(r.made_playoffs))
                        acc[name]["title"].append(float(r.won_title))
                        acc[name]["seed"].append(float(r.seed))
                        acc[name]["wins"].append(float(r.wins))
                        first_rb[name].append(float(r.first_rb_round))
                        grp = "early_1_3" if slot < 3 else ("mid_4_7" if slot < 7 else "late_8_10")
                        per_strategy_slot[name][grp].append(float(r.made_playoffs))
                for name in simmod.ALL_STRATEGIES:
                    per_strategy[name][season] = {
                        k: statistics.fmean(v) if v else float("nan")
                        for k, v in acc[name].items()}

            sig_out: Dict = {"per_season": {k: v for k, v in per_strategy.items()},
                             "illegal_rosters": dict(illegal),
                             "mean_first_rb_round": {k: statistics.fmean(v) if v else float("nan")
                                                     for k, v in first_rb.items()},
                             "comparisons": {}}
            print(f"\n=== source={source} sigma={sig_name} "
                  f"{'(PRIMARY)' if sig_name == PRIMARY_SIGMA[source] else '(sensitivity)'} ===")
            hdr = f"{'strategy':16s} {'A best-ball':>13s} {'B realistic':>13s} " \
                  f"{'P(playoff)':>11s} {'P(title)':>9s} {'1st RB rd':>10s}"
            print(hdr)
            for name in simmod.ALL_STRATEGIES:
                ps = per_strategy[name]
                print(f"{name:16s} "
                      f"{statistics.fmean(v['A'] for v in ps.values()):13.1f} "
                      f"{statistics.fmean(v['B'] for v in ps.values()):13.1f} "
                      f"{statistics.fmean(v['playoff'] for v in ps.values()):11.3f} "
                      f"{statistics.fmean(v['title'] for v in ps.values()):9.3f} "
                      f"{sig_out['mean_first_rb_round'][name]:10.2f}")

            print(f"\n  paired margins vs '{BASELINE_STRATEGY}', resampling SEASONS "
                  f"(n={len(seasons)}, min attainable two-sided sign-test p="
                  f"{min(1.0, 2.0 / 2 ** len(seasons)):.4f})")
            for metric, label in (("B", "realistic points"), ("A", "best-ball points"),
                                  ("playoff", "P(make playoffs)"), ("title", "P(win title)")):
                print(f"  -- {label}")
                for name in simmod.ALL_STRATEGIES:
                    if name == BASELINE_STRATEGY:
                        continue
                    margins = {s: per_strategy[name][s][metric] - per_strategy[BASELINE_STRATEGY][s][metric]
                               for s in seasons}
                    pt, lo, hi = season_bootstrap_paired(margins)
                    k, nn, p, minp = sign_test(list(margins.values()))
                    g = grade(pt, lo, hi)
                    n_tests += 1
                    sig_out["comparisons"].setdefault(metric, {})[name] = dict(
                        point=pt, lo=lo, hi=hi, grade=g, per_season=margins,
                        sign_k=k, sign_n=nn, sign_p=p, sign_min_p=minp)
                    print(f"     {name:16s} {pt:+9.3f}  [{lo:+9.3f},{hi:+9.3f}]  {g:9s} "
                          f"sign {k}/{nn} p={p:.4f}")
            # BUG FIX (FR-109, 2026-07-30). This block used to sit OUTSIDE the
            # sigma loop and read `per_strategy_slot`, which is rebound at the
            # top of each sigma iteration -- so the only slot table that ever
            # survived was the LAST sigma cell (flat20 for ffc, flat20 for ecr),
            # not the primary one. `docs/ranking/fr085-zero-rb.md` §5.4 printed
            # that table under the heading "FFC primary sigma". It is the sigma=20
            # cell, which is why its P(playoff) values (0.71-0.80) do not
            # reconcile with the primary-sigma pooled values (~0.40) three
            # sections above. Now keyed per sigma.
            sig_out["playoff_rate_by_slot"] = {
                name: {grp: statistics.fmean(v) for grp, v in d.items()}
                for name, d in per_strategy_slot.items()}
            print(f"\n  P(make playoffs) by draft slot group, sigma={sig_name}"
                  f"{' (PRIMARY)' if sig_name == PRIMARY_SIGMA[source] else ''}:")
            for name, d in sig_out["playoff_rate_by_slot"].items():
                print("   ", f"{name:16s}", {k: round(v, 3) for k, v in sorted(d.items())})
            src_out["sigma"][sig_name] = sig_out
        results["sources"][source] = src_out

    results["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} paired interval tests in this run; at 5% that is "
          f"~{0.05 * n_tests:.1f} false 'clears zero' results expected by chance. ====")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"wrote {out_path}")
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=300)
    ap.add_argument("--rounds", type=int, default=simmod.N_ROUNDS_FULL)
    ap.add_argument("--sources", default="ffc,ecr")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    tag = f"r{a.rounds}"
    out = Path(a.out) if a.out else REPO / "data" / "qa" / f"fr085-strategy-sim-{tag}.json"
    run(a.sims, a.rounds, a.sources.split(","), out)


if __name__ == "__main__":
    main()
