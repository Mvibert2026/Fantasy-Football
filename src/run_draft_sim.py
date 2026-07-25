"""
Run the PR-003 draft-simulation comparison and report it honestly.

Two uncertainty sources are reported SEPARATELY, never combined:
  - simulation error: shrinks with more simulated drafts. Tells you how well the
    simulator's own mean is pinned down.
  - season bootstrap: does NOT shrink with more simulations. Tells you how much
    the answer would move on a different set of seasons, and it is the one that
    actually bounds a claim about strategy.
Reporting only the first would make three seasons of data look like thousands.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np

import db as dbmod
import draft_sim as ds
import holdout as holdout_mod
import preregistration as prereg
from config import DEFAULT_CONFIG

DEV_SEASONS = [2021, 2022, 2023, 2024]
BASELINE = "bpa_consensus"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=dbmod.DB_PATH)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    ap.add_argument("--seasons", type=int, nargs="+", default=DEV_SEASONS)
    ap.add_argument("--record", action="store_true", help="write results to the FDR run log")
    args = ap.parse_args()

    prereg.require_preregistration("PR-003")
    holdout_mod.DEFAULT_LOCK.guard(args.seasons, purpose="PR-003 draft simulation")

    conn = dbmod.connect(args.db)
    try:
        data = {s: ds.load_season(conn, s) for s in args.seasons}
    finally:
        conn.close()

    print("PR-003 DRAFT SIMULATION")
    print("=" * 84)
    print(f"seasons {args.seasons}  |  holdout {holdout_mod.HOLDOUT_SEASON} excluded")
    print(f"{args.sims} sims/strategy/season/sigma  |  seed={args.seed}")
    print(f"{ds.N_TEAMS}-team snake, {ds.N_ROUNDS} rounds, user slot {ds.USER_SLOT} "
          f"(picks {ds.user_pick_numbers()[:5]}...)")
    print("Lineups set with perfect weekly hindsight; DEF is a constant. See module docstring.")
    print()

    # results[sigma][strategy][season] = SimResult
    results: Dict[float, Dict[str, Dict[int, ds.SimResult]]] = {}
    for sigma in ds.SIGMA_SWEEP:
        results[sigma] = {}
        for name, strat in ds.STRATEGIES.items():
            results[sigma][name] = {}
            for si, season in enumerate(args.seasons):
                d = data[season]
                board = d.consensus_rank.copy()
                seed = args.seed + int(sigma * 1000) + si * 97 + abs(hash(name)) % 1000
                results[sigma][name][season] = ds.run_strategy(
                    d, name, strat, board, args.sims, sigma, seed
                )

    # ---- convergence check at the default sigma -------------------------------
    ref = results[ds.DEFAULT_SIGMA][BASELINE][args.seasons[-1]]
    print(f"CONVERGENCE ({BASELINE}, {args.seasons[-1]}, sigma={ds.DEFAULT_SIGMA})")
    print(f"  {'n_sims':>7} {'mean':>10} {'sim SE':>9}")
    for n, m, se in ds.convergence_check(ref, [25, 50, 100, 200, 400, args.sims]):
        print(f"  {n:>7} {m:>10.1f} {se:>9.2f}")
    print()

    illegal = sum(
        r.illegal_rosters
        for sig in results.values() for arm in sig.values() for r in arm.values()
    )
    print(f"illegal rosters across all runs: {illegal} "
          f"(a strategy that cannot field a lineup is a failed run, not a low score)")
    print()

    # ---- power ceiling, stated before any result ------------------------------
    n_seasons = len(args.seasons)
    _, _, _, min_p = ds.sign_test(np.array([1.0] * n_seasons))
    print("POWER CEILING")
    print(f"  {n_seasons} development seasons. The exact two-sided sign test's smallest")
    print(f"  attainable p is {min_p:.3f}. NO strategy comparison can reach p<0.05 at the")
    print("  season level regardless of effect size or simulation count. More simulated")
    print("  drafts shrink the simulation SE only; they do not add seasons.")
    print()

    # ---- per-sigma strategy table ---------------------------------------------
    recorded = []
    for sigma in ds.SIGMA_SWEEP:
        print(f"--- sigma = {sigma} " + "-" * 62)
        print(f"  {'strategy':<16} {'mean pts':>9} {'simSE':>7} {'P(top4)':>8} "
              f"{'vs BPA':>9} {'season 95% CI':>20} {'signs':>7} {'sign p':>7}")
        base_means = {s: results[sigma][BASELINE][s].mean_points for s in args.seasons}
        for name in ds.STRATEGIES:
            arm = results[sigma][name]
            means = {s: arm[s].mean_points for s in args.seasons}
            pooled = float(np.mean(list(means.values())))
            sim_se = float(np.mean([
                arm[s].sd_points / np.sqrt(max(1, len(arm[s].user_points)))
                for s in args.seasons
            ]))
            ptop4 = float(np.mean([arm[s].p_top4 for s in args.seasons]))
            if name == BASELINE:
                print(f"  {name:<16} {pooled:>9.1f} {sim_se:>7.2f} {ptop4:>8.3f} "
                      f"{'(baseline)':>9}")
                continue
            pt, lo, hi, margins = ds.paired_season_bootstrap(means, base_means, seed=args.seed)
            k, n, p, _ = ds.sign_test(margins)
            ci = f"[{lo:+.1f}, {hi:+.1f}]" if np.isfinite(lo) else "[n/a]"
            print(f"  {name:<16} {pooled:>9.1f} {sim_se:>7.2f} {ptop4:>8.3f} "
                  f"{pt:>+9.1f} {ci:>20} {f'{k}/{n}':>7} {p:>7.3f}")
            recorded.append((sigma, name, pt, lo, hi, p, margins))
        print("  per-season margins vs BPA:")
        for name in ds.STRATEGIES:
            if name == BASELINE:
                continue
            m = {s: results[sigma][name][s].mean_points - base_means[s] for s in args.seasons}
            cells = "  ".join(f"{s}:{v:+7.1f}" for s, v in m.items())
            print(f"    {name:<16} {cells}")
        print()

    print("NOTE ON SIGMA. Absolute values move a lot with sigma because sigma controls how")
    print("badly the opponents draft -- at sigma=20 they are erratic and any consensus-")
    print("following roster looks strong. Only the RELATIVE ordering between strategies is")
    print("meaningful, and only where it is stable across the sweep.")
    print()

    if args.record:
        for sigma, name, pt, lo, hi, p, _m in recorded:
            prereg.record_test_run(
                test_id=f"PR-003:sigma{sigma}:{name}_vs_{BASELINE}",
                metric="paired_mean_roster_points_margin_sign_test",
                p_value=None if not np.isfinite(p) else p,
                effect_size=pt,
                seasons_used=args.seasons,
                notes=f"sims={args.sims} ci=[{lo:.1f},{hi:.1f}] "
                      f"(sign test; min attainable p={min_p:.3f})",
            )
        ps = [r[5] for r in recorded if np.isfinite(r[5])]
        res = prereg.correct_against_full_log(ps, alpha=0.05)
        print(f"BENJAMINI-HOCHBERG across n_total={res.n_total_considered} "
              f"({res.note or 'this pass only'})")
        print(f"  survived BH: {sum(res.rejected)} of {len(ps)}  "
              f"(unsurprising: the floor on raw p is {min_p:.3f})")


if __name__ == "__main__":
    main()
