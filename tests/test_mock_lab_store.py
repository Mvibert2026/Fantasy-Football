"""
Sanity checks for the Mock Lab live-logging store (thread 025), written
BEFORE src/mock_lab_store.py per CLAUDE.md's non-negotiable ordering.

Architecture under test is the thread 040 AMENDMENT model, not the original
thread 025 "immutable prediction" design: the pick log is the sole source of
truth, predictions are a derived pure function of board state, and undo
truncates-and-replays rather than voiding records. The one hard guard is
model-version pinning -- replay must refuse once the live model version has
moved past what a mock was created under.
"""
import sqlite3

import pytest

import mock_lab_store as mls


def _conn():
    conn = sqlite3.connect(":memory:")
    mls.ensure_tables(conn)
    return conn


BOARD = {
    "1001": 1,  # best player by consensus rank
    "1002": 2,
    "1003": 3,
    "1004": 4,
    "1005": 5,
    "1006": 6,
}


# --------------------------------------------------------------- create_mock

def test_create_mock_pins_model_version_and_seed():
    conn = _conn()
    row = mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    assert row["model_version"] == mls.MODEL_VERSION
    assert row["status"] == "open"
    assert isinstance(row["rng_seed"], int)


def test_create_mock_rejects_duplicate_id():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    with pytest.raises(mls.DuplicateMockError):
        mls.create_mock(conn, "m1", "primary", slot=5, teams=10)


def test_create_mock_rejects_slot_outside_teams():
    conn = _conn()
    with pytest.raises(mls.InvalidSlotError):
        mls.create_mock(conn, "m1", "primary", slot=11, teams=10)
    with pytest.raises(mls.InvalidSlotError):
        mls.create_mock(conn, "m2", "primary", slot=0, teams=10)


def test_create_mock_accepts_any_conforming_slot():
    """Thread 040 item 2: slot must not be hardcoded to the founder's own
    league slot -- any slot 1..teams is a valid mock."""
    conn = _conn()
    for slot in (1, 5, 10):
        mls.create_mock(conn, f"m-slot-{slot}", "primary", slot=slot, teams=10)


# --------------------------------------------------------------- append_pick

def test_append_pick_assigns_sequential_pick_numbers():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    p1 = mls.append_pick(conn, "m1", "1001")
    p2 = mls.append_pick(conn, "m1", "1002")
    assert (p1, p2) == (1, 2)


def test_append_pick_rejects_unknown_mock():
    conn = _conn()
    with pytest.raises(mls.MockNotFoundError):
        mls.append_pick(conn, "ghost", "1001")


def test_append_pick_rejects_duplicate_player_in_same_mock():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    with pytest.raises(mls.DuplicatePickError):
        mls.append_pick(conn, "m1", "1001")


def test_append_pick_rejects_when_closed():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.close_mock(conn, "m1")
    with pytest.raises(mls.MockClosedError):
        mls.append_pick(conn, "m1", "1002")


# --------------------------------------------------------------- undo / replay (thread 040 amendment)

def test_undo_truncates_the_log_not_voids_it():
    """Undo must delete rows, not mark them -- 'no voided records, no lost
    data, no undo count' per the 040 amendment."""
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.append_pick(conn, "m1", "1002")
    mls.append_pick(conn, "m1", "1003")
    mls.undo_to(conn, "m1", keep_through=1)
    picks = mls.list_picks(conn, "m1")
    assert [p["pick_no"] for p in picks] == [1]
    assert [p["mfl_id"] for p in picks] == ["1001"]


def test_undo_then_reentry_reuses_pick_numbers():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.append_pick(conn, "m1", "1002")  # misclick
    mls.undo_to(conn, "m1", keep_through=1)
    p = mls.append_pick(conn, "m1", "1003")  # corrected entry
    assert p == 2
    assert [x["mfl_id"] for x in mls.list_picks(conn, "m1")] == ["1001", "1003"]


def test_no_undo_count_is_tracked():
    """The 040 amendment explicitly retracts the undo-count/voided-cost
    design. There must be no such column or bookkeeping."""
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.undo_to(conn, "m1", keep_through=0)
    row = mls.get_mock(conn, "m1")
    assert "undo_count" not in row


def test_undo_requires_reopen_if_closed():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.close_mock(conn, "m1")
    with pytest.raises(mls.MockClosedError):
        mls.undo_to(conn, "m1", keep_through=0)
    mls.reopen_mock(conn, "m1")
    mls.undo_to(conn, "m1", keep_through=0)  # now fine
    assert mls.list_picks(conn, "m1") == []


# --------------------------------------------------------------- predictions (derived, not stored)

def test_predict_next_pick_favours_highest_board_rank_when_undrafted():
    result = mls.predict_next_pick({"1002": 2, "1003": 3, "1004": 4})
    assert result.predicted_top == "1002"
    assert 0.0 < result.predicted_p <= 1.0
    assert result.predicted_top5[0] == "1002"


def test_predict_next_pick_probabilities_sum_to_one():
    result = mls.predict_next_pick(BOARD)
    assert result.all_probs["1001"] == pytest.approx(max(result.all_probs.values()))
    assert sum(result.all_probs.values()) == pytest.approx(1.0, abs=1e-9)


def test_replay_predictions_excludes_already_drafted_players():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.append_pick(conn, "m1", "1002")
    replay = mls.replay_predictions(conn, "m1", BOARD)
    # prediction for pick 2 must not have offered pick 1's player as a candidate
    assert "1001" not in replay[1].prediction.all_probs


def test_replay_refuses_when_model_version_has_moved(monkeypatch):
    """The one guard the 040 amendment actually requires: replay under a
    newer model than the one pinned at creation is refused outright."""
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    monkeypatch.setattr(mls, "MODEL_VERSION", "some_future_model_v2")
    with pytest.raises(mls.ModelVersionMismatch):
        mls.replay_predictions(conn, "m1", BOARD)


def test_replay_permitted_when_model_version_unchanged():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    replay = mls.replay_predictions(conn, "m1", BOARD)
    assert len(replay) == 1


# --------------------------------------------------------------- scoring

def test_brier_score_is_zero_for_perfect_prediction():
    """Construct a degenerate board where at the moment of each pick only
    one undrafted candidate exists -- predicted_p is forced to exactly 1
    and the actual pick matches it, so Brier must be exactly 0."""
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    score = mls.brier_score(conn, "m1", {"1001": 1})
    assert score == pytest.approx(0.0, abs=1e-9)


def test_brier_score_bounded_zero_to_one():
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    for pid in ("1004", "1002", "1006", "1001"):  # scrambled vs. board rank
        mls.append_pick(conn, "m1", pid)
    score = mls.brier_score(conn, "m1", BOARD)
    assert 0.0 <= score <= 1.0


def test_calibration_buckets_counts_all_picks_and_skips_mismatched_versions(monkeypatch):
    conn = _conn()
    mls.create_mock(conn, "m1", "primary", slot=3, teams=10)
    mls.append_pick(conn, "m1", "1001")
    mls.append_pick(conn, "m1", "1002")
    mls.create_mock(conn, "m2", "primary", slot=5, teams=10)
    mls.append_pick(conn, "m2", "1003")

    result = mls.calibration_buckets(conn, ["m1", "m2"], {"m1": BOARD, "m2": BOARD})
    assert result["n_scored"] == 3
    assert result["n_skipped_version_mismatch"] == 0

    # now move the goalposts and re-pin only m2's stored version to something else
    conn.execute("UPDATE mocklab_drafts SET model_version=? WHERE mock_id=?",
                 ("stale_v0", "m2"))
    result2 = mls.calibration_buckets(conn, ["m1", "m2"], {"m1": BOARD, "m2": BOARD})
    assert result2["n_scored"] == 2
    assert result2["n_skipped_version_mismatch"] == 1
