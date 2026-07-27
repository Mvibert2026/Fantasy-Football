"""Sanity tests for the bottom-up prototype (experiments/bottomup).

These pin the discipline claims, not model quality:
- the holdout (2025) is structurally unreachable,
- feature reads at/after the target season raise,
- the frozen universe uses only prior-season information,
- metric edge cases behave.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.bottomup import data as bdata  # noqa: E402
from experiments.bottomup import metrics as bmetrics  # noqa: E402

DB = ROOT.parent.parent.parent / "data" / "nfl.db"
# In the fable-ext worktree, the shared DB lives in the master working tree.
# Resolve it explicitly; skip cleanly when unavailable (CI without data).
_CANDIDATES = [
    DB,
    Path(r"C:\Users\matth\Documents\Personal\Fantasy Football\data\nfl.db"),
]
DB_PATH = next((p for p in _CANDIDATES if p.exists()), None)

needs_db = pytest.mark.skipif(DB_PATH is None, reason="nfl.db not available")


@needs_db
def test_holdout_sealed_for_evaluation():
    store = bdata.SeasonStore(DB_PATH)
    with pytest.raises(bdata.HoldoutViolation):
        store.actuals(2025)
    with pytest.raises(bdata.HoldoutViolation):
        store.player_seasons(2025)


@needs_db
def test_cutoff_refuses_target_season_features():
    store = bdata.SeasonStore(DB_PATH)
    with pytest.raises(bdata.CutoffViolation):
        store.player_seasons(2020, for_target=2020)
    with pytest.raises(bdata.CutoffViolation):
        store.player_seasons(2021, for_target=2020)


@needs_db
def test_frozen_universe_is_prior_season_only():
    store = bdata.SeasonStore(DB_PATH)
    universe = bdata.frozen_universe(store, 2020)
    # depths respected
    for pos, depth in bdata.UNIVERSE_DEPTH.items():
        assert len(universe[pos]) <= depth
    # every member has a 2019 season on record (i.e., no target-season info)
    prior = store.player_seasons(2019, for_target=2020)
    for pos, pids in universe.items():
        for pid in pids:
            assert pid in prior


@needs_db
def test_store_is_read_only():
    store = bdata.SeasonStore(DB_PATH)
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):
        store.conn.execute("CREATE TABLE _fable_should_fail (x int)")


def test_metric_edge_cases():
    # tau on too-few players is nan, not a crash
    assert bmetrics.tau_b({}, {}, []) != bmetrics.tau_b({}, {}, [])  # nan
    pt, lo, hi = bmetrics.season_bootstrap_ci([])
    assert pt != pt  # nan
    mean, lo, hi, frac = bmetrics.paired_delta_ci([1.0, 2.0], [0.5, 1.5])
    assert abs(mean - 0.5) < 1e-9
    assert frac == 1.0


def test_replacement_depths_match_repo_constants():
    assert bmetrics.REPLACEMENT_K == {"QB": 10, "RB": 30, "WR": 40, "TE": 10}
