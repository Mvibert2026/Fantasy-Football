"""Run the strategy comparison and emit data/export/strategies.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import db as dbmod
import draft_sim as ds
from draft_sim import stable_offset
import holdout as holdout_mod
from config import DEFAULT_CONFIG
from export_contract import CONTRACT_VERSION, EXPORT_DIR

BASELINE = "bpa_consensus"
DEV_SEASONS = [2021, 2022, 2023, 2024]


def verdict(point: float, lo: float, hi: float, k: int, n: int, p: float, floor: float) -> str:
    if not np.isfinite(lo):
        return "Not enough seasons to say anything."
    same_dir = k == n or k == 0
    direction = "better" if point > 0 else "worse"
    if same_dir and abs(point) > 20:
        return (
            f"Consistently {direction} than best-available in all {n} seasons, by about "
            f"{abs(point):.0f} points. That cannot be called statistically significant — with "
            f"only {n} seasons the strongest possible result is p={floor:.3f} — but the "
            f"direction never wavers and the gap is large."
        )
    if p <= 0.30 and abs(point) > 20:
        return (
            f"Leans {direction} by about {abs(point):.0f} points ({k} of {n} seasons), but not "
            f"reliably. Treat as a hint, not a plan."
        )
    return (
        f"No real difference from just taking the best player available. The margin is "
        f"{point:+.0f} points and it swings both ways across seasons ({k} of {n} positive)."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=int, default=600)
    ap.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    ap.add_argument("--out", type=Path, default=EXPORT_DIR / "strategies.json")
    args = ap.parse_args()

    holdout_mod.DEFAULT_LOCK.guard(DEV_SEASONS, purpose="strategies.json export")
    conn = dbmod.connect()
    try:
        data = {s: ds.load_season(conn, s) for s in DEV_SEASONS}
    finally:
        conn.close()

    results = {}
    for sigma in ds.SIGMA_SWEEP:
        results[sigma] = {}
        for name, strat in ds.STRATEGIES.items():
            results[sigma][name] = {}
            for si, season in enumerate(DEV_SEASONS):
                d = data[season]
                seed = args.seed + int(sigma * 1000) + si * 97 + stable_offset(name)
                results[sigma][name][season] = ds.run_strategy(
                    d, name, strat, d.consensus_rank.copy(), args.sims, sigma, seed
                )

    _, _, _, floor = ds.sign_test(np.array([1.0] * len(DEV_SEASONS)))
    out = {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": BASELINE,
        "seasons": DEV_SEASONS,
        "simulations_per_cell": args.sims,
        "seed": args.seed,
        "sigma_values": list(ds.SIGMA_SWEEP),
        "power_floor": {
            "n_seasons": len(DEV_SEASONS),
            "smallest_attainable_two_sided_p": floor,
            "plain_english": (
                f"With only {len(DEV_SEASONS)} seasons of data, the best a perfect result could "
                f"score is p={floor:.3f}. The usual bar is 0.05. So nothing here can be called "
                "statistically significant, no matter how many drafts we simulate — that is a "
                "limit of the data, not of the method."
            ),
        },
        "lineup_assumption": (
            "Lineups are set with perfect hindsight each week. This flatters deep rosters and "
            "is corrected by the realistic-lineup arm (Block 3), not yet included here."
        ),
        "strategies": [],
    }

    for name in ds.STRATEGIES:
        per_sigma = []
        for sigma in ds.SIGMA_SWEEP:
            arm = results[sigma][name]
            base = results[sigma][BASELINE]
            means = {s: arm[s].mean_points for s in DEV_SEASONS}
            bmeans = {s: base[s].mean_points for s in DEV_SEASONS}
            pt, lo, hi, margins = ds.paired_season_bootstrap(means, bmeans, seed=args.seed)
            k, n, p, _ = ds.sign_test(margins)
            per_sigma.append({
                "sigma": sigma,
                "mean_roster_points": round(float(np.mean(list(means.values()))), 1),
                "p_top4": round(float(np.mean([arm[s].p_top4 for s in DEV_SEASONS])), 3),
                "margin_vs_baseline": None if name == BASELINE else round(pt, 1),
                "ci_low": None if name == BASELINE or not np.isfinite(lo) else round(lo, 1),
                "ci_high": None if name == BASELINE or not np.isfinite(hi) else round(hi, 1),
                "seasons_positive": None if name == BASELINE else k,
                "sign_test_p": None if name == BASELINE else round(p, 4),
                "per_season_margin": None if name == BASELINE else {
                    str(s): round(means[s] - bmeans[s], 1) for s in DEV_SEASONS
                },
                "simulation_se": round(float(np.mean([
                    arm[s].sd_points / np.sqrt(max(1, len(arm[s].user_points)))
                    for s in DEV_SEASONS
                ])), 2),
            })
        default = next(x for x in per_sigma if x["sigma"] == ds.DEFAULT_SIGMA)
        out["strategies"].append({
            "name": name,
            "is_baseline": name == BASELINE,
            "by_sigma": per_sigma,
            "verdict": "This is the baseline everything else is compared against."
            if name == BASELINE else verdict(
                default["margin_vs_baseline"], default["ci_low"], default["ci_high"],
                default["seasons_positive"], len(DEV_SEASONS), default["sign_test_p"], floor,
            ),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"wrote {args.out}")
    for s in out["strategies"]:
        d = next(x for x in s["by_sigma"] if x["sigma"] == ds.DEFAULT_SIGMA)
        print(f"  {s['name']:<18} margin={d['margin_vs_baseline']}  {s['verdict'][:60]}")


if __name__ == "__main__":
    main()
