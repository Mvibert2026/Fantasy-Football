import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(autouse=True, scope="session")
def _isolate_holdout_audit_log(tmp_path_factory):
    """Point the holdout audit log at a temp file for the whole test session.

    docs/preregistration/holdout_access_log.jsonl is tracked in git as evidence
    of when the locked season was actually read. Letting the test suite append
    to it on every run would bury the handful of real accesses under hundreds of
    synthetic ones and destroy the audit trail's value.
    """
    import holdout

    original = holdout.DEFAULT_LOCK.log_path
    holdout.DEFAULT_LOCK.log_path = tmp_path_factory.mktemp("holdout") / "access.jsonl"
    yield
    holdout.DEFAULT_LOCK.log_path = original


@pytest.fixture(scope="session", autouse=True)
def _cache_expensive_archetype_computation():
    """Thread 022: test_archetypes.py::TestAgainstRealData and
    test_player_descriptions.py::TestAgainstRealData/TestExport each call
    archetypes.compute_player_season_inputs(conn, 2025) fresh -- 15-60s of raw
    SQL aggregation over player_weekly_stats/snap_counts, uncached, 7+ times
    across the two files (directly, or transitively via assign_for_season ->
    generate_all_descriptions -> export_player_descriptions_json). That one
    function is the entire cost; every other DB-backed test in these two files
    runs in milliseconds once its result is available.

    Memoized here, not in src/, so production code is untouched -- this is a
    test-session-only cache, keyed on the exact arguments, of a function whose
    result is already documented as deterministic for a given DB snapshot
    (test_description_is_deterministic_across_calls,
    test_export_is_deterministic_modulo_timestamps). Every test still calls
    the real function and gets the real result; it is just computed once
    instead of once per test. No coverage is removed -- same call sites, same
    assertions, same code paths exercised.
    """
    import archetypes as arch

    original = arch.compute_player_season_inputs
    cache: dict = {}

    def cached(conn, data_season, positions=("RB", "WR", "TE")):
        key = (data_season, positions)
        if key not in cache:
            cache[key] = original(conn, data_season, positions)
        return cache[key]

    arch.compute_player_season_inputs = cached
    yield
    arch.compute_player_season_inputs = original
