"""
ADR-046: strategy_balanced's flat -8.0 'unfilled starter' nudge was replaced
with live_availability.n_need()'s continuous, share-based N_t(p). These tests
cover the replacement's actual behaviour change, not live_availability.py's
own math (see test_live_availability.py for that).
"""

import numpy as np

import draft_sim as ds
import live_availability as la


def _tied_qb_rb_board():
    """2 players, one QB one RB, EXACT tied board rank -- any choice between
    them is then decided purely by the need adjustment."""
    positions = np.array([ds.POSITIONS.index("QB"), ds.POSITIONS.index("RB")])
    board = np.array([5.0, 5.0])
    data = ds.SeasonData(
        season=2026,
        player_ids=["p_qb", "p_rb"],
        names=["QB1", "RB1"],
        positions=positions,
        consensus_rank=board.copy(),
        weekly_points=np.zeros((2, 2)),
        n_weeks=1,
    )
    available = np.ones(2, dtype=bool)
    return data, board, available


def test_strategy_balanced_prefers_rb_when_qb_is_in_surplus():
    data, board, available = _tied_qb_rb_board()
    state = ds.DraftState(
        season=2026, pick_number=10, round_number=3, my_roster=[],
        my_counts={"QB": 3, "RB": 0, "WR": 0, "TE": 0}, taken=available,
    )
    choice = ds.strategy_balanced(state, available, data, board)
    assert data.positions[choice] == ds.POSITIONS.index("RB")


def test_strategy_balanced_prefers_qb_when_rb_is_in_surplus():
    data, board, available = _tied_qb_rb_board()
    state = ds.DraftState(
        season=2026, pick_number=10, round_number=3, my_roster=[],
        my_counts={"QB": 0, "RB": 3, "WR": 0, "TE": 0}, taken=available,
    )
    choice = ds.strategy_balanced(state, available, data, board)
    assert data.positions[choice] == ds.POSITIONS.index("QB")


def test_strategy_balanced_is_neutral_with_a_fresh_roster():
    """With no picks made yet, N_t(p) == 1.0 for every position (share_t ==
    share_bar), so the adjustment is exactly zero and the tie is broken by
    raw board order alone (argmin's first-index tie-break -> QB, index 0)."""
    data, board, available = _tied_qb_rb_board()
    state = ds.DraftState(
        season=2026, pick_number=1, round_number=0, my_roster=[],
        my_counts={"QB": 0, "RB": 0, "WR": 0, "TE": 0}, taken=available,
    )
    n_by_pos = la.n_need(state.my_counts, lam=la.DEFAULT_LAMBDA)
    assert all(abs(n - 1.0) < 1e-9 for n in n_by_pos.values())
    choice = ds.strategy_balanced(state, available, data, board)
    assert data.positions[choice] == ds.POSITIONS.index("QB")


def test_need_adjustment_scale_is_a_named_flagged_constant():
    assert ds.NEED_ADJUSTMENT_SCALE == 10.0
