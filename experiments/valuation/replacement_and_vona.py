"""Test-registry #35 (global flex baseline) and #36 (VONA with pick-gap awareness).

Design is fixed in `docs/ranking/valuation-tests-35-36-precommit.md`, committed before this
module ran for real. Read that first; this implements it and adds nothing.

Uses `src/draft_sim.py` UNMODIFIED as the simulator -- both tests build alternative `board`
arrays / `Strategy` callables and drive them through the existing `run_strategy`/`simulate_one`/
`paired_season_bootstrap`/`sign_test`.

Player-level projections do not exist yet (ADR-017) -- every board here uses season S-1's
ACTUAL points, scored under this league's real rules, as the pre-season projection stand-in
(CLAUDE.md SS6.5 baseline #2), read through `db.CutoffEnforcedStore` so the look-ahead guard is
structurally exercised rather than bypassed.
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
import draft_sim as ds  # noqa: E402
import live_availability as la  # noqa: E402
from scoring import ReplacementLevels, score_offensive_game  # noqa: E402

TRAIN_SEASONS = (2021, 2022, 2023, 2024)  # 2025 is the sealed holdout -- not touched here
SIGMAS = (10.0, 20.0)
N_SIMS = 300

GLOBAL_FLEX_RANK = 80  # derived in the precommit doc: RB20+WR30+TE10 mandated + 20 flex slots
GAP_BLIND_CONST = float(ds.N_TEAMS - 1)  # naive "assume one round" approximation


# ============================================================================= shared utilities
def stable_seed(*parts) -> int:
    """crc32 of a stable string key. NEVER builtin hash() -- guardrails SS11 rule 1: hash() is
    salted per-process for str/bytes, so a seed derived from it silently changes every run while
    printing the same 'seed=' value (the exact bug ADR-025/ADR-028 both hit)."""
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return zlib.crc32(key)


def prior_season_points(conn, season: int) -> Dict[str, float]:
    """{player_id: season total points} for season-1, scored under this league's real rules,
    read through the structural cutoff guard (never a raw query against player_weekly_stats)."""
    store = db.CutoffEnforcedStore(conn, cutoff_season=season)
    pts: Dict[str, float] = {}
    for row in store.player_week_rows(seasons=[season - 1]):
        pid = row["player_id"]
        stats = {c: row[c] for c in db.SCORING_STAT_COLUMNS}
        pts[pid] = pts.get(pid, 0.0) + score_offensive_game(stats)
    return pts


def vbd_to_rank_board(vbd: np.ndarray) -> np.ndarray:
    """Descending VBD -> ascending rank (1=best), the convention draft_sim._best_by/strategy_bpa
    already use (argmin = pick). Ties broken by original index order (numpy argsort is stable)."""
    order = np.argsort(-vbd, kind="stable")
    rank = np.empty(len(vbd), dtype=float)
    rank[order] = np.arange(1, len(vbd) + 1, dtype=float)
    return rank


# ============================================================================= Test 1: #35
def build_vbd_board(
    data: "ds.SeasonData",
    prior_pts: Dict[str, float],
    mode: str,
    baselines_override: Optional[Dict[str, int]] = None,
) -> np.ndarray:
    """Returns raw VBD points (not rank) aligned to data.player_ids, under either the CURRENT
    per-position replacement scheme or the GLOBAL flex-eligible scheme. QB is identical in both
    (not flex-eligible in this league)."""
    n = len(data.player_ids)
    proj = np.array([prior_pts.get(pid, 0.0) for pid in data.player_ids])
    vbd = np.zeros(n)

    def repl_points(idx: np.ndarray, rank_1_indexed: int) -> float:
        if len(idx) == 0:
            return 0.0
        order = idx[np.argsort(-proj[idx], kind="stable")]
        i = min(rank_1_indexed - 1, len(order) - 1)
        return float(proj[order[i]])

    if mode == "current":
        baselines = baselines_override or ReplacementLevels().baselines()
        for p, pos in enumerate(ds.POSITIONS):
            idx = np.where(data.positions == p)[0]
            b = baselines.get(pos, len(idx))
            repl = repl_points(idx, b)
            vbd[idx] = proj[idx] - repl
    elif mode == "global_flex":
        baselines = baselines_override or ReplacementLevels().baselines()
        qb_idx = np.where(data.positions == ds.POSITIONS.index("QB"))[0]
        qb_repl = repl_points(qb_idx, baselines.get("QB", len(qb_idx)))
        vbd[qb_idx] = proj[qb_idx] - qb_repl

        flex_pos = [p for p in ("RB", "WR", "TE") if p in ds.POSITIONS]
        flex_idx = np.where(np.isin(data.positions, [ds.POSITIONS.index(p) for p in flex_pos]))[0]
        global_repl = repl_points(flex_idx, GLOBAL_FLEX_RANK)
        vbd[flex_idx] = proj[flex_idx] - global_repl
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return vbd


# ============================================================================= Test 2: #36
def user_pick_gaps() -> Tuple[List[int], List[int]]:
    """(picks, gaps) -- picks = user_pick_numbers(); gaps[i] = intervening opponent picks
    between picks[i] and picks[i+1] (deterministic snake arithmetic, no RNG)."""
    picks = ds.user_pick_numbers()
    gaps = [picks[i + 1] - picks[i] - 1 for i in range(len(picks) - 1)]
    gaps.append(gaps[-1] if gaps else int(GAP_BLIND_CONST))  # last pick has no "next"; unused
    return picks, gaps


_USER_PICKS, _GAPS = user_pick_gaps()
_PICK_INDEX = {p: i for i, p in enumerate(_USER_PICKS)}


def _next_gap(state: "ds.DraftState", aware: bool) -> float:
    if not aware:
        return GAP_BLIND_CONST
    idx = _PICK_INDEX.get(state.pick_number)
    if idx is None:
        return GAP_BLIND_CONST
    return float(_GAPS[idx])


def share_bar_offense() -> Dict[str, float]:
    """live_availability.TARGET's measured per-round position share, renormalised over
    QB/RB/WR/TE only. Dropping DEF's fixed 1.0 share leaves 15 = N_ROUNDS-1, the number of
    rounds simulate_one actually drafts (its final round is reserved for DEF and skipped
    entirely) -- so this is not a rescaling assumption, it is what the simulator itself does."""
    off = {p: la.TARGET[p] for p in ("QB", "RB", "WR", "TE")}
    total = sum(off.values())
    return {p: v / total for p, v in off.items()}


def make_vona_strategy(vbd_points: np.ndarray, aware: bool, share: Dict[str, float]) -> "ds.Strategy":
    def strat(state, available, data, board):
        legal = ds._legal_mask(state, data) & available
        cand_idx = np.where(legal)[0]
        if len(cand_idx) == 0:
            cand_idx = np.where(available)[0]
            if len(cand_idx) == 0:
                return int(np.argmax(available))
        gap = _next_gap(state, aware)

        pools: Dict[int, np.ndarray] = {}
        for p in range(len(ds.POSITIONS)):
            idx = np.where(available & (data.positions == p))[0]
            pools[p] = idx[np.argsort(-vbd_points[idx], kind="stable")] if len(idx) else idx

        best_i, best_score = cand_idx[0], -np.inf
        for ci in cand_idx:
            p = int(data.positions[ci])
            pos_name = ds.POSITIONS[p]
            pool_sorted = pools[p]
            cur_rank = int(np.where(pool_sorted == ci)[0][0])
            n_expected = gap * share.get(pos_name, 0.0)
            next_rank = cur_rank + n_expected
            lo = int(np.floor(next_rank))
            if lo >= len(pool_sorted) - 1:
                repl_vbd = 0.0  # replacement level, by construction of VBD
            else:
                frac = next_rank - lo
                v_lo = vbd_points[pool_sorted[lo]]
                v_hi = vbd_points[pool_sorted[lo + 1]]
                repl_vbd = v_lo + frac * (v_hi - v_lo)
            score = vbd_points[ci] - repl_vbd
            if score > best_score:
                best_score, best_i = score, ci
        return int(best_i)

    return strat


def run_paired_strategies(
    data: "ds.SeasonData",
    strat_a: "ds.Strategy", strat_b: "ds.Strategy",
    board: np.ndarray, sigma: float, seed_key: str, n_sims: int,
):
    """Runs strat_a and strat_b against IDENTICAL opponent-noise realisations (same seed feeds
    both calls' single `rng.normal` draw), so any outcome difference traces to the user's own
    pick, not re-randomised opponents. Returns per-sim point totals for both arms plus a
    pick-divergence flag."""
    pts_a, pts_b, diverged, illegal = [], [], [], 0
    for i in range(n_sims):
        seed = stable_seed(seed_key, data.season, sigma, i)
        rng_a = np.random.default_rng(seed)
        rng_b = np.random.default_rng(seed)
        mine_a, opps_a, legal_a = ds.simulate_one(data, strat_a, board, sigma, rng_a)
        mine_b, opps_b, legal_b = ds.simulate_one(data, strat_b, board, sigma, rng_b)
        if not (legal_a and legal_b):
            illegal += 1
            continue
        pts_a.append(ds.weekly_optimal_points(mine_a, data))
        pts_b.append(ds.weekly_optimal_points(mine_b, data))
        diverged.append(mine_a != mine_b)
    return np.array(pts_a), np.array(pts_b), np.array(diverged), illegal
