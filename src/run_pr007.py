"""Runner for PR-007 (F-RECOMMENDATION-CONSTANTS): does frontend/ui/data/
recommendation.ts's `+8 unfilled-need / +18 tier-1-TE / -25 early-QB` beat
plain VBD, and does each constant earn its place?

Executes exactly the frozen registration at
docs/preregistration/PR-007-recommendation-constants-ablation.md. Every
design choice here is pinned there; where the registration names a formula,
this file ports it mechanically (see its §1 table). Run twice in separate
processes and diff the JSON output for the §7/(g) determinism check --
this script does not do that itself.

Usage:
    .venv/bin/python src/run_pr007.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db as dbmod
import draft_sim as ds
import holdout as holdout_mod
import make_board as mb
import preregistration as prereg

PREREG_ID = "PR-007"
SEASONS = [2022, 2023, 2024]
SIGMAS = list(ds.SIGMA_SWEEP)  # (5.0, 10.0, 20.0)
N_SIMS = 1000
SEED_BASE = 20260729
TE_K = 2  # census check 1: live board.json has exactly 2 TE tier==1 rows
          # (Brock Bowers pos-rank 1, Trey McBride pos-rank 2); 1b confirms
          # this equals the top-K TEs by consensus positional rank exactly.
MC_SE_EXTENSION_TRIGGER = 3.0
EXTENDED_SIMS = 3000
DIAG_SIMS = 200  # pick-flip diagnostic: descriptive only, no CI, reduced n

QB_IDX = ds.POSITIONS.index("QB")
TE_IDX = ds.POSITIONS.index("TE")


def seed_for(sigma: float, season_index: int) -> int:
    return SEED_BASE + int(sigma * 1000) + season_index * 97


# --------------------------------------------------------------- board build


def vbd_score_for_season(conn, season: int):
    data = ds.load_season(conn, season)
    board, curves = mb.build_board(conn, season, source=mb.TRAINING_SOURCE, n_bootstrap=0)
    training_seasons = mb.resolve_training_seasons(conn, season)
    assert max(training_seasons) < season, (
        f"LOOK-AHEAD: season {season} curve trained on {training_seasons}"
    )
    print(f"  season {season}: rank curves trained on seasons {training_seasons} "
          f"(max={max(training_seasons)} < {season}: OK)")

    vbd_by_pid: Dict[str, float] = {r.player_id: r.vbd for r in board if r.player_id}
    vbd = np.empty(len(data.player_ids))
    n_missing = 0
    for i, pid in enumerate(data.player_ids):
        v = vbd_by_pid.get(pid)
        if v is None:
            n_missing += 1
            vbd[i] = np.nan
        else:
            vbd[i] = v
    join_frac = n_missing / len(data.player_ids)
    if n_missing:
        vmin = float(np.nanmin(vbd))
        vbd[np.isnan(vbd)] = vmin - 1e-6

    n_zero = int(np.sum(data.weekly_points.sum(axis=1) == 0.0))
    return -vbd, vbd, data, join_frac, len(data.player_ids), n_zero


def te_tier1_mask(data, k: int = TE_K) -> np.ndarray:
    idx = np.where(data.positions == TE_IDX)[0]
    order = idx[np.argsort(data.consensus_rank[idx])]
    mask = np.zeros(len(data.positions), dtype=bool)
    mask[order[:k]] = True
    return mask


def te_window_mask(data, lo: int = 7, hi: int = 10) -> np.ndarray:
    idx = np.where(data.positions == TE_IDX)[0]
    order = idx[np.argsort(data.consensus_rank[idx])]
    mask = np.zeros(len(data.positions), dtype=bool)
    sel = order[lo - 1:hi]
    mask[sel] = True
    return mask


# --------------------------------------------------------------- arms


def make_arm_strategy(te1_mask: np.ndarray, need: bool, te: bool, qb: bool):
    """No RNG use anywhere (§7 requirement 1)."""

    def strat(state, available, data, board):
        adj = board.copy()
        if need:
            for pos_name, cnt in ds.STARTERS.items():
                if state.my_counts.get(pos_name, 0) < cnt:
                    p = ds.POSITIONS.index(pos_name)
                    adj[data.positions == p] -= 8.0
        if te:
            adj[te1_mask] -= 18.0
        if qb:
            if state.round_number <= 4:  # round < 6, 1-indexed -> round_number <= 4, 0-indexed
                adj[data.positions == QB_IDX] += 25.0
        return ds._best_by(adj, available, ds._legal_mask(state, data))

    return strat


def make_te_window_strategy(te_window: np.ndarray):
    def strat(state, available, data, board):
        adj = board.copy()
        adj[te_window] -= 18.0
        return ds._best_by(adj, available, ds._legal_mask(state, data))
    return strat


ARM_DEFS = {
    "vbd_plain": dict(need=False, te=False, qb=False),
    "vbd_all4": dict(need=True, te=True, qb=True),
    "vbd_loo_need": dict(need=False, te=True, qb=True),
    "vbd_loo_te": dict(need=True, te=False, qb=True),
    "vbd_loo_qb": dict(need=True, te=True, qb=False),
    "vbd_only_need": dict(need=True, te=False, qb=False),
    "vbd_only_te": dict(need=False, te=True, qb=False),
    "vbd_only_qb": dict(need=False, te=False, qb=True),
}
CONFIRMATORY_ARMS = list(ARM_DEFS.keys())
COMPARISONS = {
    "FULL-PLAIN": ("vbd_all4", "vbd_plain"),
    "need": ("vbd_all4", "vbd_loo_need"),
    "te": ("vbd_all4", "vbd_loo_te"),
    "qb": ("vbd_all4", "vbd_loo_qb"),
}
ONLY_COMPARISONS = {  # criterion (d): ONLY(c) - PLAIN, sign only
    "need": ("vbd_only_need", "vbd_plain"),
    "te": ("vbd_only_te", "vbd_plain"),
    "qb": ("vbd_only_qb", "vbd_plain"),
}


# --------------------------------------------------------------- CRN identity


def effective_rank_bytes(data, sigma: float, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    n = len(data.player_ids)
    effective_rank = data.consensus_rank + rng.normal(0.0, sigma, size=n)
    return effective_rank.tobytes()


# --------------------------------------------------------------- pick-flip diagnostic


def pick_flip_diag(data, board_score, board_vbd, arm_defs, te1_mask, sigma, seed, n_sims):
    """Descriptive only. Runs vbd_plain's own drafts; at every USER pick state
    visited, evaluates what each named arm's decision function WOULD choose in
    that exact state (same available mask, same counts, same board) -- no
    extra RNG draws, no CI. Returns {arm: (flip_rate, mean_vbd_surrendered)}."""
    rng = np.random.default_rng(seed)
    plain_strat = make_arm_strategy(te1_mask, **arm_defs["vbd_plain"])
    arm_strats = {name: make_arm_strategy(te1_mask, **arm_defs[name])
                  for name in arm_defs if name != "vbd_plain"}
    flips = {name: 0 for name in arm_strats}
    surrendered = {name: [] for name in arm_strats}
    total_picks = 0

    n = len(data.player_ids)
    order = ds.pick_order()
    me = ds.USER_SLOT - 1
    for _ in range(n_sims):
        effective_rank = data.consensus_rank + rng.normal(0.0, sigma, size=n)
        available = np.ones(n, dtype=bool)
        rosters = [[] for _ in range(ds.N_TEAMS)]
        counts = [{p: 0 for p in ds.POSITIONS} for _ in range(ds.N_TEAMS)]
        for pick_i, team in enumerate(order):
            rnd = pick_i // ds.N_TEAMS
            if rnd == ds.N_ROUNDS - 1:
                continue
            if team == me:
                state = ds.DraftState(data.season, pick_i + 1, rnd, rosters[me], counts[me], available)
                plain_choice = plain_strat(state, available, data, board_score)
                total_picks += 1
                for name, strat in arm_strats.items():
                    arm_choice = strat(state, available, data, board_score)
                    if arm_choice != plain_choice:
                        flips[name] += 1
                        surrendered[name].append(board_vbd[plain_choice] - board_vbd[arm_choice])
                choice = plain_choice
            else:
                choice = ds.opponent_pick(effective_rank, available, counts[team], data)
            if not np.isfinite(choice) or not available[choice]:
                continue
            available[choice] = False
            rosters[team].append(int(choice))
            counts[team][ds.POSITIONS[data.positions[choice]]] += 1

    out = {}
    for name in arm_strats:
        rate = flips[name] / total_picks if total_picks else float("nan")
        surr = float(np.mean(surrendered[name])) if surrendered[name] else 0.0
        out[name] = (rate, surr, flips[name], total_picks)
    return out


# --------------------------------------------------------------- sigma=0 diagnostic


def sigma0_diag(data, board_score, arm_defs, te1_mask):
    """Deterministic, one draft per arm, no CI: does the constant change ANY
    pick at all in a modal noiseless room (§7)."""
    out = {}
    plain_strat = make_arm_strategy(te1_mask, **arm_defs["vbd_plain"])
    plain_res = ds.run_strategy(data, "vbd_plain", plain_strat, board_score, 1, 0.0, SEED_BASE)
    for name, defs in arm_defs.items():
        strat = make_arm_strategy(te1_mask, **defs)
        res = ds.run_strategy(data, name, strat, board_score, 1, 0.0, SEED_BASE)
        out[name] = res.mean_points
    return out, plain_res.mean_points


# --------------------------------------------------------------- main


def run() -> dict:
    print(f"=== PR-007 :: {PREREG_ID} ===")
    reg = prereg.require_confirmatory(PREREG_ID)
    print(f"registration OK, effective_mode={reg.effective_mode}")
    violations = prereg.check_registration(PREREG_ID)
    if violations:
        raise SystemExit(f"REGISTRATION INTEGRITY FAILURE: {violations}")
    print("content hash verified against frozen registration.")

    conn = dbmod.connect()

    print("\n--- Census ---")
    census: dict = {}
    for s in SEASONS:
        year = holdout_mod.load_season_registered(s, PREREG_ID)
        assert year == s

    per_season = {}
    for s in SEASONS:
        score, vbd, data, join_frac, n_players, n_zero = vbd_score_for_season(conn, s)
        per_season[s] = dict(score=score, vbd=vbd, data=data, join_frac=join_frac,
                              n_players=n_players, n_zero=n_zero)
        print(f"  {s}: n_players={n_players} join_missing_frac={join_frac:.4f} "
              f"n_zero_scorers={n_zero}")
        if join_frac > 0.05:
            raise SystemExit(f"STOP condition 3: {s} join-missing fraction {join_frac:.3f} > 5%")
        if n_zero == 0:
            print(f"  WARNING (guardrails §2): {s} has zero zero-scorers -- survivorship check")

    te1_masks = {s: te_tier1_mask(per_season[s]["data"]) for s in SEASONS}
    te_window_masks = {s: te_window_mask(per_season[s]["data"]) for s in SEASONS}
    for s in SEASONS:
        k_fired = int(te1_masks[s].sum())
        print(f"  {s}: TE tier-1 surrogate fires on {k_fired} players (K={TE_K})")
        if k_fired == 0:
            raise SystemExit("STOP condition 2: TE tier-1 surrogate empty")

    census["K"] = TE_K
    census["season_join_frac"] = {s: per_season[s]["join_frac"] for s in SEASONS}
    census["season_zero_scorers"] = {s: per_season[s]["n_zero"] for s in SEASONS}
    census["season_n_players"] = {s: per_season[s]["n_players"] for s in SEASONS}

    # ---------------------------------------------------- monte carlo SE pre-check
    print("\n--- Monte Carlo SE pre-check (sigma=10, FULL-PLAIN, before any margin) ---")
    n_sims = N_SIMS
    mc_ses = {}
    for si, s in enumerate(SEASONS):
        d = per_season[s]["data"]
        te1 = te1_masks[s]
        seed = seed_for(10.0, si)
        full_res = ds.run_strategy(d, "vbd_all4", make_arm_strategy(te1, **ARM_DEFS["vbd_all4"]),
                                    per_season[s]["score"], N_SIMS, 10.0, seed)
        plain_res = ds.run_strategy(d, "vbd_plain", make_arm_strategy(te1, **ARM_DEFS["vbd_plain"]),
                                     per_season[s]["score"], N_SIMS, 10.0, seed)
        m = min(len(full_res.user_points), len(plain_res.user_points))
        diff = np.array(full_res.user_points[:m]) - np.array(plain_res.user_points[:m])
        se = float(np.std(diff, ddof=1) / np.sqrt(m)) if m > 1 else float("nan")
        mc_ses[s] = se
        print(f"  {s}: FULL-PLAIN paired MC SE at sigma=10 = {se:.3f} (n={m})")
    if any(v > MC_SE_EXTENSION_TRIGGER for v in mc_ses.values()):
        n_sims = EXTENDED_SIMS
        print(f"  >>> MC SE exceeded {MC_SE_EXTENSION_TRIGGER}; re-running ENTIRE grid at "
              f"{EXTENDED_SIMS} sims.")
    else:
        print(f"  All under {MC_SE_EXTENSION_TRIGGER} points; keeping {N_SIMS} sims/cell.")

    # ---------------------------------------------------------- main grid
    print(f"\n--- Main grid: {len(SEASONS)} seasons x {len(SIGMAS)} sigmas, {n_sims} sims/cell ---")
    all_arms = CONFIRMATORY_ARMS + ["vbd_te_window", "vbd_need_continuous"] + list(
        ["bpa_consensus", "balanced"])
    results: Dict[str, Dict[int, Dict[float, dict]]] = {a: {s: {} for s in SEASONS} for a in all_arms}
    crn_ok = True

    for si, s in enumerate(SEASONS):
        d = per_season[s]["data"]
        board_score = per_season[s]["score"]
        te1 = te1_masks[s]
        tew = te_window_masks[s]
        consensus_board = d.consensus_rank

        for sigma in SIGMAS:
            seed = seed_for(sigma, si)
            cell_crcs = []

            for arm in CONFIRMATORY_ARMS:
                strat = make_arm_strategy(te1, **ARM_DEFS[arm])
                res = ds.run_strategy(d, arm, strat, board_score, n_sims, sigma, seed)
                results[arm][s][sigma] = dict(mean=res.mean_points, sd=res.sd_points,
                                               p_top4=res.p_top4, n=len(res.user_points),
                                               illegal=res.illegal_rosters,
                                               user_points=res.user_points)
                cell_crcs.append((arm, zlib.crc32(effective_rank_bytes(d, sigma, seed))))

            te_window_strat = make_te_window_strategy(tew)
            res = ds.run_strategy(d, "vbd_te_window", te_window_strat, board_score, n_sims, sigma, seed)
            results["vbd_te_window"][s][sigma] = dict(mean=res.mean_points, sd=res.sd_points,
                                                        p_top4=res.p_top4, n=len(res.user_points),
                                                        illegal=res.illegal_rosters)
            cell_crcs.append(("vbd_te_window", zlib.crc32(effective_rank_bytes(d, sigma, seed))))

            res = ds.run_strategy(d, "vbd_need_continuous", ds.strategy_balanced, board_score,
                                   n_sims, sigma, seed)
            results["vbd_need_continuous"][s][sigma] = dict(mean=res.mean_points, sd=res.sd_points,
                                                              p_top4=res.p_top4, n=len(res.user_points),
                                                              illegal=res.illegal_rosters)
            cell_crcs.append(("vbd_need_continuous", zlib.crc32(effective_rank_bytes(d, sigma, seed))))

            for arm in ["bpa_consensus", "balanced"]:
                res = ds.run_strategy(d, arm, ds.STRATEGIES[arm], consensus_board, n_sims, sigma, seed)
                results[arm][s][sigma] = dict(mean=res.mean_points, sd=res.sd_points,
                                               p_top4=res.p_top4, n=len(res.user_points),
                                               illegal=res.illegal_rosters)
                cell_crcs.append((arm, zlib.crc32(effective_rank_bytes(d, sigma, seed))))

            crcs = {c for _, c in cell_crcs}
            ok = len(crcs) == 1
            crn_ok = crn_ok and ok
            print(f"  season={s} sigma={sigma}: {len(cell_crcs)} arms, CRN identity: "
                  f"{'OK' if ok else 'MISMATCH ' + str(cell_crcs)}")
            if not ok:
                raise SystemExit(f"CRN IDENTITY ASSERTION FAILED season={s} sigma={sigma}: "
                                  f"{cell_crcs} -- run is VOID per §7.")

    # ---------------------------------------------------------- bootstrap + sign test
    print("\n--- Bootstrap CI (sigma=10) + sign tests, per comparison ---")
    stats = {}
    for name, (a_hi, a_lo) in COMPARISONS.items():
        arm_pts = {s: results[a_hi][s][10.0]["mean"] for s in SEASONS}
        base_pts = {s: results[a_lo][s][10.0]["mean"] for s in SEASONS}
        point, lo, hi, margins = ds.paired_season_bootstrap(arm_pts, base_pts, seed=SEED_BASE)
        k, n, p, minp = ds.sign_test(margins)
        # 9-cell sign table across the sigma sweep
        cell_signs = {}
        for sigma in SIGMAS:
            for s in SEASONS:
                m = results[a_hi][s][sigma]["mean"] - results[a_lo][s][sigma]["mean"]
                cell_signs[f"{s}@{sigma}"] = m
        stats[name] = dict(point=point, ci_lo=lo, ci_hi=hi, per_season_margin=
                            {s: arm_pts[s] - base_pts[s] for s in SEASONS},
                            sign_k=k, sign_n=n, sign_p=p, sign_minp=minp, cells=cell_signs)
        print(f"  {name}: FULL-{'PLAIN' if name=='FULL-PLAIN' else 'LOO('+name+')'} "
              f"mean={point:+.2f} CI95=[{lo:+.2f},{hi:+.2f}] sign={k}/{n} p={p}")

    # criterion (d): ONLY(c)-PLAIN sign agreement at sigma=10
    for name, (a_hi, a_lo) in ONLY_COMPARISONS.items():
        arm_pts = {s: results[a_hi][s][10.0]["mean"] for s in SEASONS}
        base_pts = {s: results[a_lo][s][10.0]["mean"] for s in SEASONS}
        only_margin = float(np.mean([arm_pts[s] - base_pts[s] for s in SEASONS]))
        stats[name]["only_margin_sigma10"] = only_margin
        stats[name]["sign_agree_only"] = (np.sign(only_margin) == np.sign(stats[name]["point"])) \
            if stats[name]["point"] == stats[name]["point"] else False

    # criterion (e): delta P(top4) sign agreement at sigma=10
    for name, (a_hi, a_lo) in COMPARISONS.items():
        d_top4 = results[a_hi][SEASONS[-1]][10.0]["p_top4"]  # placeholder overwritten below
    for name, (a_hi, a_lo) in COMPARISONS.items():
        deltas = [results[a_hi][s][10.0]["p_top4"] - results[a_lo][s][10.0]["p_top4"] for s in SEASONS]
        mean_delta_top4 = float(np.mean(deltas))
        stats[name]["delta_p_top4"] = mean_delta_top4
        stats[name]["sign_agree_top4"] = (np.sign(mean_delta_top4) == np.sign(stats[name]["point"])) \
            if stats[name]["point"] == stats[name]["point"] else False

    # criterion (f): regime gate, per-season margin at sigma=10 not strictly
    # decreasing across 2022->2023->2024 with 2024 below +20
    for name in ("need", "te", "qb"):
        margins = [stats[name]["per_season_margin"][s] for s in SEASONS]
        strictly_decreasing = margins[0] > margins[1] > margins[2]
        below_floor_2024 = margins[2] < 20.0
        regime_dependent = strictly_decreasing and below_floor_2024
        stats[name]["regime_margins"] = margins
        stats[name]["regime_dependent"] = regime_dependent
        stats[name]["criterion_f_pass"] = not regime_dependent

    # ---------------------------------------------------------- QB rank-curve slope
    print("\n--- QB rank-curve slope per season (§8.2 required reporting) ---")
    qb_slopes = {}
    for s in SEASONS:
        _, curves = mb.build_board(conn, s, source=mb.TRAINING_SOURCE, n_bootstrap=0)
        qb_slopes[s] = curves["QB"].slope_log_rank if "QB" in curves else None
        print(f"  {s}: QB slope_log_rank={qb_slopes[s]}")

    # ---------------------------------------------------------- pick-flip diagnostic (sigma=10)
    print("\n--- Pick-flip diagnostic (descriptive, sigma=10, reduced n={}) ---".format(DIAG_SIMS))
    flip_diag = {}
    for si, s in enumerate(SEASONS):
        d = per_season[s]["data"]
        te1 = te1_masks[s]
        seed = seed_for(10.0, si) + 999999  # distinct stream from main grid, diagnostic only
        out = pick_flip_diag(d, per_season[s]["score"], per_season[s]["vbd"], ARM_DEFS, te1,
                              10.0, seed, DIAG_SIMS)
        flip_diag[s] = out
        for name, (rate, surr, flips, total) in out.items():
            print(f"  {s} {name}: flip_rate={rate:.4f} ({flips}/{total}) mean_vbd_surrendered={surr:.2f}")

    # ---------------------------------------------------------- sigma=0 diagnostic
    print("\n--- Sigma=0 deterministic diagnostic ---")
    sigma0 = {}
    for s in SEASONS:
        d = per_season[s]["data"]
        te1 = te1_masks[s]
        out, plain_mean = sigma0_diag(d, per_season[s]["score"], ARM_DEFS, te1)
        sigma0[s] = dict(arms=out, plain=plain_mean)
        for name, val in out.items():
            flips = "differs" if abs(val - plain_mean) > 1e-9 else "same"
            print(f"  {s} {name}: pts={val:.2f} vs plain={plain_mean:.2f} ({flips})")

    # ---------------------------------------------------------- pack output
    out_results = {}
    for arm in results:
        out_results[arm] = {}
        for s in results[arm]:
            out_results[arm][str(s)] = {}
            for sigma in results[arm][s]:
                cell = dict(results[arm][s][sigma])
                cell.pop("user_points", None)
                out_results[arm][str(s)][str(sigma)] = cell

    output = dict(
        n_sims=n_sims,
        census=census,
        mc_ses=mc_ses,
        results=out_results,
        stats=stats,
        qb_slopes={str(k): v for k, v in qb_slopes.items()},
        flip_diag={str(s): {a: list(v) for a, v in flip_diag[s].items()} for s in flip_diag},
        sigma0={str(s): dict(arms=sigma0[s]["arms"], plain=sigma0[s]["plain"]) for s in sigma0},
        crn_ok=crn_ok,
    )
    return output


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("/tmp/pr007_out.json"))
    args = ap.parse_args()
    out = run()
    args.out.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n=== Written to {args.out} ===")
