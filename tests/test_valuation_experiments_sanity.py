"""Sanity checks for `experiments/valuation/replacement_and_vona.py` (test-registry #35/#36),
written BEFORE the implementation per the project's non-negotiable rule and
`docs/statistical-guardrails.md` SS8. These check arithmetic invariants the pre-registration
(`docs/ranking/valuation-tests-35-36-precommit.md`) depends on -- not the substantive draft-sim
result, which lives in the results doc, not in this suite.

No `data/nfl.db` needed: every check here is either pure arithmetic on `draft_sim`'s own module
constants or exercises the module's helper functions directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "valuation"))

import draft_sim as ds  # noqa: E402


def _load_module():
    import replacement_and_vona as m  # noqa
    return m


# ------------------------------------------------------------------ Test 1 arithmetic
def test_flex_positions_sum_to_80_both_schemes():
    """RB20+WR30+TE10 mandated + 20 flex slots = 80, and that equals the CURRENT scheme's
    own RB30+WR40+TE10 total -- both schemes redistribute the SAME 80 picks, per the
    precommit doc's derivation. This is arithmetic on draft_sim's own constants, not a
    measurement, and must hold before any board is built."""
    mandated_flex_eligible = sum(
        ds.STARTERS[p] * ds.N_TEAMS for p in ("RB", "WR", "TE")
    )
    total_flex_picks = ds.FLEX_SLOTS * ds.N_TEAMS
    assert mandated_flex_eligible + total_flex_picks == 80

    from scoring import ReplacementLevels
    baselines = ReplacementLevels().baselines()
    assert baselines["RB"] + baselines["WR"] + baselines["TE"] == 80


def test_global_flex_baseline_index_is_80th_ie_index_79():
    m = _load_module()
    assert m.GLOBAL_FLEX_RANK == 80


def test_vbd_to_rank_board_is_a_valid_permutation():
    m = _load_module()
    vbd = np.array([3.0, -1.0, 5.0, 5.0, 0.0])
    board = m.vbd_to_rank_board(vbd)
    assert sorted(board.tolist()) == [1.0, 2.0, 3.0, 4.0, 5.0]
    # highest VBD gets rank 1 (lower rank = better, draft_sim._best_by convention)
    assert board[2] == 1.0 or board[3] == 1.0
    assert board[1] == 5.0  # the unique lowest VBD gets the worst rank


def test_build_vbd_board_current_matches_per_position_baselines():
    m = _load_module()
    # 2 QB, 3 RB (need baseline QB1 -> QB10 style, tiny toy roster so replacement = worst
    # player in each position group deterministically)
    ids = [f"p{i}" for i in range(6)]
    positions = np.array(
        [ds.POSITIONS.index(p) for p in ("QB", "QB", "RB", "RB", "RB", "WR")]
    )
    data = ds.SeasonData(
        season=2099, player_ids=ids, names=ids, positions=positions,
        consensus_rank=np.arange(1, 7, dtype=float),
        weekly_points=np.zeros((6, 1)), n_weeks=0,
    )
    prior_pts = {"p0": 10.0, "p1": 4.0, "p2": 20.0, "p3": 12.0, "p4": 6.0, "p5": 30.0}
    # tiny toy baselines: QB replacement = rank 2 (worst QB), RB = rank 3 (worst RB)
    vbd = m.build_vbd_board(data, prior_pts, mode="current",
                             baselines_override={"QB": 2, "RB": 3, "WR": 1, "TE": 1})
    assert vbd[data.player_ids.index("p0")] == pytest.approx(10.0 - 4.0)  # QB0 - replacement(QB1)
    assert vbd[data.player_ids.index("p1")] == pytest.approx(0.0)         # QB replacement itself
    assert vbd[data.player_ids.index("p2")] == pytest.approx(20.0 - 6.0)  # RB2 - replacement(RB4)


# ------------------------------------------------------------------ Test 2 arithmetic
def test_share_bar_offense_sums_to_one_and_excludes_def():
    m = _load_module()
    share = m.share_bar_offense()
    assert set(share) == {"QB", "RB", "WR", "TE"}
    assert sum(share.values()) == pytest.approx(1.0, abs=1e-9)
    # TARGET sums to 16 rounds; dropping DEF's 1.0 share leaves 15, which is exactly
    # N_ROUNDS-1 -- the number of rounds simulate_one actually drafts (final round is
    # reserved for DEF and never drafted in-sim). No hidden rescaling.
    assert ds.N_ROUNDS - 1 == 15


def test_user_pick_gaps_alternate_for_slot_3():
    """USER_SLOT=3, N_TEAMS=10 -- draft_sim.py's own docstring states picks 3,18,23,38,43,...
    Gaps (intervening opponent picks) must alternate long/short, ~3x apart, matching the
    registry's '#36 ... differs ~3x' framing and the precommit doc's derivation."""
    m = _load_module()
    picks, gaps = m.user_pick_gaps()
    assert picks[:5] == [3, 18, 23, 38, 43]
    assert gaps[:4] == [14, 4, 14, 4]
    assert gaps[0] / gaps[1] == pytest.approx(3.5)


def test_gap_blind_constant_is_one_round():
    m = _load_module()
    assert m.GAP_BLIND_CONST == ds.N_TEAMS - 1 == 9


def test_next_gap_picks_real_alternating_values_when_aware():
    m = _load_module()
    state_at_pick_3 = ds.DraftState(2099, 3, 0, [], {}, np.array([True]))
    state_at_pick_18 = ds.DraftState(2099, 18, 1, [], {}, np.array([True]))
    assert m._next_gap(state_at_pick_3, aware=True) == 14
    assert m._next_gap(state_at_pick_18, aware=True) == 4
    assert m._next_gap(state_at_pick_3, aware=False) == 9
    assert m._next_gap(state_at_pick_18, aware=False) == 9


# ------------------------------------------------------------------ shared: seeding + look-ahead
def test_stable_seed_is_deterministic_across_calls_and_not_hash_based():
    """statistical-guardrails SS11 rule 1: never derive a seed from builtin hash() -- it is
    salted per-process. crc32 must return the identical value called twice in this process."""
    m = _load_module()
    a = m.stable_seed("vbd_current", 2022, 10.0)
    b = m.stable_seed("vbd_current", 2022, 10.0)
    assert a == b
    assert isinstance(a, int)
    # different inputs must (almost always) differ
    c = m.stable_seed("vbd_global_flex", 2022, 10.0)
    assert a != c


def test_prior_season_points_uses_cutoff_enforced_store_not_a_raw_query():
    """Structural look-ahead guard: the function that builds each season's projection input
    must go through db.CutoffEnforcedStore (season S board may only see season S-1), never a
    raw SELECT against player_weekly_stats."""
    import inspect
    m = _load_module()
    src = inspect.getsource(m.prior_season_points)
    assert "CutoffEnforcedStore" in src
