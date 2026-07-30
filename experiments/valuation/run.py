"""Execute PR-006 (test-registry #35, global flex baseline) and PR-008 (test-registry #36,
VONA pick-gap awareness) together, as pre-registered, and print + optionally record results.

Usage: python experiments/valuation/run.py [--sims 300] [--record]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "valuation"))

import db as dbmod  # noqa: E402
import draft_sim as ds  # noqa: E402
import preregistration as prereg  # noqa: E402
import replacement_and_vona as rv  # noqa: E402

SEASONS = list(rv.TRAIN_SEASONS)
SIGMAS = list(rv.SIGMAS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=rv.N_SIMS)
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()

    pr006 = prereg.require_preregistration("PR-006")
    pr008 = prereg.require_preregistration("PR-008")
    print(f"PR-006 status={pr006.status}  PR-008 status={pr008.status}")

    conn = dbmod.connect(dbmod.DB_PATH)
    data: Dict[int, ds.SeasonData] = {}
    prior: Dict[int, Dict[str, float]] = {}
    for s in SEASONS:
        data[s] = ds.load_season(conn, s)
        prior[s] = rv.prior_season_points(conn, s)
    conn.close()

    print(f"seasons {SEASONS} | sigmas {SIGMAS} | sims/cell {args.sims}")
    print(f"user slot {ds.USER_SLOT}, picks {rv._USER_PICKS[:5]}..., gaps {rv._GAPS[:4]}...")
    print()

    # ---------------------------------------------------------- boards, per season
    boards_rank: Dict[int, Dict[str, np.ndarray]] = {}
    boards_vbd: Dict[int, Dict[str, np.ndarray]] = {}
    for s in SEASONS:
        d = data[s]
        vbd_current = rv.build_vbd_board(d, prior[s], mode="current")
        vbd_global = rv.build_vbd_board(d, prior[s], mode="global_flex")
        boards_vbd[s] = {"vbd_current": vbd_current, "vbd_global_flex": vbd_global}
        boards_rank[s] = {
            "vbd_current": rv.vbd_to_rank_board(vbd_current),
            "vbd_global_flex": rv.vbd_to_rank_board(vbd_global),
            "bpa_consensus": d.consensus_rank.copy(),
        }

    share = rv.share_bar_offense()
    print(f"share_bar_offense (QB/RB/WR/TE, renormalised): {share}")
    print()

    # ---------------------------------------------------------- run all single-strategy arms
    ARMS = ("bpa_consensus", "vbd_current", "vbd_global_flex")
    results: Dict[float, Dict[str, Dict[int, ds.SimResult]]] = {sig: {a: {} for a in ARMS} for sig in SIGMAS}
    for sigma in SIGMAS:
        for name in ARMS:
            for s in SEASONS:
                board = boards_rank[s][name]
                seed = rv.stable_seed(name, s, sigma)
                results[sigma][name][s] = ds.run_strategy(
                    data[s], name, ds.strategy_bpa, board, args.sims, sigma, seed
                )

    # VONA arms: run_strategy for summary stats
    vona_results: Dict[float, Dict[str, Dict[int, ds.SimResult]]] = {
        sig: {"vona_gap_blind": {}, "vona_gap_aware": {}} for sig in SIGMAS
    }
    for sigma in SIGMAS:
        for s in SEASONS:
            vbd_points = boards_vbd[s]["vbd_current"]
            for aware, name in ((False, "vona_gap_blind"), (True, "vona_gap_aware")):
                strat = rv.make_vona_strategy(vbd_points, aware=aware, share=share)
                board = boards_rank[s]["vbd_current"]  # unused by the strategy, kept for API shape
                seed = rv.stable_seed(name, s, sigma)
                vona_results[sigma][name][s] = ds.run_strategy(
                    data[s], name, strat, board, args.sims, sigma, seed
                )

    # ---------------------------------------------------------- report + collect p-values
    recorded = []

    def compare(sigma, name_a, means_a, name_b, means_b, tag):
        pt, lo, hi, margins = ds.paired_season_bootstrap(means_a, means_b, seed=int(sigma))
        k, n, p, min_p = ds.sign_test(margins)
        print(f"  [{tag}] sigma={sigma}: {name_a} - {name_b} = {pt:+.1f} "
              f"[{lo:+.1f},{hi:+.1f}] signs {k}/{n} sign_p={p:.3f} (min_p={min_p:.3f})")
        recorded.append((tag, sigma, name_a, name_b, pt, lo, hi, p, margins))
        return pt, lo, hi, p

    print("=" * 90)
    print("TEST 1 (PR-006, #35): global flex baseline vs current per-position baseline")
    print("=" * 90)
    for sigma in SIGMAS:
        m_global = {s: results[sigma]["vbd_global_flex"][s].mean_points for s in SEASONS}
        m_current = {s: results[sigma]["vbd_current"][s].mean_points for s in SEASONS}
        m_bpa = {s: results[sigma]["bpa_consensus"][s].mean_points for s in SEASONS}
        compare(sigma, "vbd_global_flex", m_global, "vbd_current", m_current, "PR-006:global_vs_current")
        compare(sigma, "vbd_global_flex", m_global, "bpa_consensus", m_bpa, "PR-006:global_vs_market")
        compare(sigma, "vbd_current", m_current, "bpa_consensus", m_bpa, "PR-006:current_vs_market")
        for name in ("vbd_global_flex", "vbd_current", "bpa_consensus"):
            ptop4 = np.mean([results[sigma][name][s].p_top4 for s in SEASONS])
            print(f"    p_top4[{name}, sigma={sigma}] = {ptop4:.3f}")
    print()

    print("=" * 90)
    print("TEST 2 (PR-008, #36): VONA gap-aware vs gap-blind")
    print("=" * 90)
    for sigma in SIGMAS:
        m_aware = {s: vona_results[sigma]["vona_gap_aware"][s].mean_points for s in SEASONS}
        m_blind = {s: vona_results[sigma]["vona_gap_blind"][s].mean_points for s in SEASONS}
        m_bpa = {s: results[sigma]["bpa_consensus"][s].mean_points for s in SEASONS}
        m_current = {s: results[sigma]["vbd_current"][s].mean_points for s in SEASONS}
        compare(sigma, "vona_gap_aware", m_aware, "vona_gap_blind", m_blind, "PR-008:aware_vs_blind")
        compare(sigma, "vona_gap_aware", m_aware, "bpa_consensus", m_bpa, "PR-008:aware_vs_market")
        compare(sigma, "vona_gap_aware", m_aware, "vbd_current", m_current, "PR-008:aware_vs_plainbpa")
        for name in ("vona_gap_aware", "vona_gap_blind"):
            ptop4 = np.mean([vona_results[sigma][name][s].p_top4 for s in SEASONS])
            print(f"    p_top4[{name}, sigma={sigma}] = {ptop4:.3f}")

    # -------------------------------------------------- decision-divergence (paired at sim level)
    print()
    print("-" * 90)
    print("DECISION DIVERGENCE: vona_gap_aware vs vona_gap_blind, same opponent-noise draws")
    print("-" * 90)
    div_summary = {}
    for sigma in SIGMAS:
        for s in SEASONS:
            vbd_points = boards_vbd[s]["vbd_current"]
            strat_blind = rv.make_vona_strategy(vbd_points, aware=False, share=share)
            strat_aware = rv.make_vona_strategy(vbd_points, aware=True, share=share)
            board = boards_rank[s]["vbd_current"]
            pts_blind, pts_aware, diverged, illegal = rv.run_paired_strategies(
                data[s], strat_blind, strat_aware, board, sigma,
                seed_key="PR-008:paired", n_sims=args.sims,
            )
            rate = float(diverged.mean()) if len(diverged) else float("nan")
            margin = float((pts_aware - pts_blind).mean()) if len(pts_aware) else float("nan")
            div_summary[(sigma, s)] = (rate, margin, illegal, len(diverged))
            print(f"  sigma={sigma} season={s}: diverged {rate:.1%} of {len(diverged)} drafts "
                  f"(illegal={illegal}), paired points margin {margin:+.1f}")

    # ---------------------------------------------------------- record + BH correction
    if args.record:
        for tag, sigma, name_a, name_b, pt, lo, hi, p, margins in recorded:
            prereg.record_test_run(
                test_id=f"{tag}:sigma{sigma}",
                metric="paired_mean_roster_points_margin_sign_test",
                p_value=None if not np.isfinite(p) else p,
                effect_size=pt,
                seasons_used=SEASONS,
                notes=f"sims={args.sims} ci=[{lo:.1f},{hi:.1f}]",
            )
        ps = [r[7] for r in recorded if np.isfinite(r[7])]
        res = prereg.correct_against_full_log(ps, alpha=0.05)
        print()
        print(f"BENJAMINI-HOCHBERG across n_total={res.n_total_considered} ({res.note or 'this pass'})")
        print(f"  survived BH: {sum(res.rejected)} of {len(ps)}")
        for (tag, sigma, a, b, pt, lo, hi, p, _), adj, rej in zip(recorded, res.adjusted, res.rejected):
            print(f"    {tag:<28} sigma={sigma:>4} raw_p={p:.3f} adj_p={adj:.3f} survives={rej}")


if __name__ == "__main__":
    main()
