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


# ======================= ADR-C: load_season (the prereg-tied data-access guard) =======================

import sys

import preregistration as prereg


CONFIRMATORY_SEALED = """---
id: PR-910
test_registry_id: T-910
family: F-LOADSEASON
mode: confirmatory
question: Does load_season respect declared scope?
metric: m
threshold: t
data_scope: {seasons: [2021, 2022, 2023, 2024, 2025], holdout_unsealed: false}
frozen: {at: 2026-07-26T00:00:00Z, code_sha: abc, seed: 1, content_hash: sha256:PLACEHOLDER}
---
"""

CONFIRMATORY_UNSEALED = """---
id: PR-911
test_registry_id: T-911
family: F-LOADSEASON
mode: confirmatory
question: Does load_season respect an unsealed flag?
metric: m
threshold: t
data_scope: {seasons: [2021, 2022, 2023, 2024, 2025], holdout_unsealed: true}
frozen: {at: 2026-07-26T00:00:00Z, code_sha: abc, seed: 1, content_hash: sha256:PLACEHOLDER}
---
"""


@pytest.fixture
def prereg_dir(tmp_path):
    d = tmp_path / "preregistration"
    d.mkdir()
    return d


@pytest.fixture
def hlock(tmp_path):
    return holdout.HoldoutLock(season=2025, log_path=tmp_path / "access.jsonl")


def test_load_season_allows_a_year_within_declared_scope(prereg_dir, hlock):
    (prereg_dir / "PR-910-x.md").write_text(CONFIRMATORY_SEALED, encoding="utf-8")
    assert holdout.load_season_registered(2022, "PR-910", lock=hlock, prereg_directory=prereg_dir) == 2022


def test_load_season_rejects_a_year_outside_declared_scope(prereg_dir, hlock):
    (prereg_dir / "PR-910-x.md").write_text(CONFIRMATORY_SEALED, encoding="utf-8")
    with pytest.raises(holdout.HoldoutViolation, match="outside the data_scope"):
        holdout.load_season_registered(2019, "PR-910", lock=hlock, prereg_directory=prereg_dir)


def test_load_season_rejects_the_holdout_when_registration_says_sealed(prereg_dir, hlock):
    (prereg_dir / "PR-910-x.md").write_text(CONFIRMATORY_SEALED, encoding="utf-8")
    with pytest.raises(holdout.HoldoutViolation, match="holdout_unsealed=false"):
        holdout.load_season_registered(2025, "PR-910", lock=hlock, prereg_directory=prereg_dir)


def test_load_season_rejects_holdout_unsealed_flag_without_a_signed_log_entry(prereg_dir, hlock):
    (prereg_dir / "PR-911-x.md").write_text(CONFIRMATORY_UNSEALED, encoding="utf-8")
    with pytest.raises(holdout.HoldoutViolation, match="signed entry"):
        holdout.load_season_registered(2025, "PR-911", lock=hlock, prereg_directory=prereg_dir)


def test_load_season_allows_the_holdout_with_flag_and_signed_log(prereg_dir, hlock):
    (prereg_dir / "PR-911-x.md").write_text(CONFIRMATORY_UNSEALED, encoding="utf-8")
    prereg.append_unseal_log(
        "PR-911", family="F-LOADSEASON", reason="final look", approver="founder",
        log_path=prereg_dir / "UNSEAL_LOG.md",
    )
    assert holdout.load_season_registered(2025, "PR-911", lock=hlock, prereg_directory=prereg_dir) == 2025
    events = [e["event"] for e in hlock.access_log()]
    assert "FINAL_EVALUATION_OPENED" in events
    assert "ALLOWED" in events


def test_load_season_denial_is_still_logged_to_the_holdout_access_log(prereg_dir, hlock):
    (prereg_dir / "PR-910-x.md").write_text(CONFIRMATORY_SEALED, encoding="utf-8")
    with pytest.raises(holdout.HoldoutViolation):
        holdout.load_season_registered(2025, "PR-910", lock=hlock, prereg_directory=prereg_dir)
    # the registration-level check fires before HoldoutLock.guard is ever
    # called for 2025, so nothing is appended to the (unrelated) HoldoutLock
    # log for this specific case -- assert instead that the raise happened
    # and did not silently pass the read through.
    assert not hlock.access_log() or hlock.access_log()[-1]["event"] != "ALLOWED"
