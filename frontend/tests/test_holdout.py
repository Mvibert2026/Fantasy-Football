import json

import pytest

import holdout


@pytest.fixture
def lock(tmp_path):
    return holdout.HoldoutLock(season=2025, log_path=tmp_path / "access.jsonl")


def test_reading_the_holdout_raises_by_default(lock):
    with pytest.raises(holdout.HoldoutViolation, match="LOCKED HOLDOUT"):
        lock.guard([2023, 2024, 2025], purpose="factor sweep")


def test_non_holdout_seasons_pass_through_untouched(lock):
    assert lock.guard([2022, 2023, 2024], purpose="factor sweep") == [2022, 2023, 2024]


def test_denied_access_is_logged(lock):
    with pytest.raises(holdout.HoldoutViolation):
        lock.guard([2025], purpose="sneaky peek")
    entries = lock.access_log()
    assert entries[-1]["event"] == "DENIED"
    assert entries[-1]["reason"] == "sneaky peek"
    assert "timestamp_utc" in entries[-1]


def test_final_evaluation_permits_and_logs_the_read(lock):
    with lock.final_evaluation(reason="PR-001 one-time final evaluation"):
        assert lock.guard([2025], purpose="final") == [2025]
    events = [e["event"] for e in lock.access_log()]
    assert "FINAL_EVALUATION_OPENED" in events
    assert "ALLOWED" in events
    assert "FINAL_EVALUATION_CLOSED" in events


def test_lock_re_engages_after_the_final_evaluation_context_exits(lock):
    with lock.final_evaluation(reason="one-time"):
        lock.guard([2025], purpose="final")
    with pytest.raises(holdout.HoldoutViolation):
        lock.guard([2025], purpose="afterwards")


def test_final_evaluation_requires_a_reason(lock):
    with pytest.raises(ValueError):
        with lock.final_evaluation(reason="  "):
            pass


def test_release_for_final_fit_is_logged_separately_from_evaluation(lock):
    """The audit trail must distinguish 'we measured on the holdout' from
    'we trained the shipped model on everything'."""
    with lock.release_for_final_fit(reason="production refit for 2026 board"):
        lock.guard([2025], purpose="refit")
    events = [e["event"] for e in lock.access_log()]
    assert "FINAL_FIT_OPENED" in events
    assert "FINAL_EVALUATION_OPENED" not in events


def test_lock_is_restored_even_if_the_body_raises(lock):
    with pytest.raises(RuntimeError):
        with lock.final_evaluation(reason="will fail"):
            raise RuntimeError("boom")
    with pytest.raises(holdout.HoldoutViolation):
        lock.guard([2025], purpose="after failure")


def test_is_locked_reflects_context(lock):
    assert lock.is_locked(2025) is True
    assert lock.is_locked(2024) is False
    with lock.final_evaluation(reason="checking"):
        assert lock.is_locked(2025) is False


def test_development_seasons_excludes_the_holdout(lock):
    assert 2025 not in lock.development_seasons()
    assert lock.development_seasons([2021, 2022, 2025]) == [2021, 2022]


def test_walk_forward_splits_always_train_on_the_past():
    splits = holdout.walk_forward_splits()
    assert splits, "expected at least one split"
    for train, test in splits:
        assert all(s < test for s in train), "a split trained on the future"


def test_walk_forward_splits_exclude_the_holdout():
    for train, test in holdout.walk_forward_splits():
        assert test != holdout.HOLDOUT_SEASON
        assert holdout.HOLDOUT_SEASON not in train


def test_walk_forward_splits_grow_the_training_window():
    splits = holdout.walk_forward_splits()
    sizes = [len(train) for train, _ in splits]
    assert sizes == sorted(sizes)


def test_holdout_season_is_2025_and_documented():
    """Changing this invalidates every prior holdout claim; the test exists so
    that a change is deliberate and shows up in review."""
    assert holdout.HOLDOUT_SEASON == 2025
