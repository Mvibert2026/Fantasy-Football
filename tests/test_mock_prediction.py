"""Sanity checks for mock_prediction.py, written before wiring it into
ingest_mock_drafts.py (ADR-054)."""

import sqlite3

import mock_lab_store as mls
import mock_prediction as mp


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE rankings (source TEXT, season INTEGER, player_id TEXT, "
        "adp_rank INTEGER, as_of_date TEXT)"
    )
    conn.execute(
        "CREATE TABLE player_ids (mfl_id TEXT, source TEXT, source_id TEXT, "
        "confidence TEXT, method TEXT, resolved_at TEXT)"
    )
    return conn


def _seed_rankings(conn, source, season, as_of_date, rows):
    """rows: [(gsis_id, mfl_id, adp_rank), ...] -- also seeds the gsis->mfl
    identity mapping `identity.resolve` reads."""
    for gsis_id, mfl_id, adp_rank in rows:
        conn.execute(
            "INSERT INTO rankings (source, season, player_id, adp_rank, as_of_date) "
            "VALUES (?,?,?,?,?)",
            (source, season, gsis_id, adp_rank, as_of_date),
        )
        conn.execute(
            "INSERT INTO player_ids (mfl_id, source, source_id, confidence, method, resolved_at) "
            "VALUES (?, 'gsis', ?, 'high', 'test', '2026-01-01')",
            (mfl_id, gsis_id),
        )


class TestHistoricalBoardRanksAsOf:
    def test_finds_snapshot_on_or_before_cutoff(self):
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-08-29", [
            ("g1", "m1", 1), ("g2", "m2", 2),
        ])
        source, snap, ranks = mp.historical_board_ranks_as_of(conn, 2025, "2025-08-30")
        assert source == "fantasypros_ecr"
        assert snap == "2025-08-29"
        assert ranks == {"m1": 1, "m2": 2}

    def test_never_uses_a_snapshot_dated_after_cutoff(self):
        """The core look-ahead-bias guard: a snapshot dated AFTER drafted_at
        must never be selected, even if it is the only one in the DB."""
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-09-15", [
            ("g1", "m1", 1),
        ])
        source, snap, ranks = mp.historical_board_ranks_as_of(conn, 2025, "2025-08-30")
        assert snap is None
        assert ranks == {}

    def test_none_when_no_snapshot_exists_at_all(self):
        conn = _conn()
        source, snap, ranks = mp.historical_board_ranks_as_of(conn, 2025, "2025-08-30")
        assert source is None
        assert snap is None
        assert ranks == {}

    def test_falls_back_to_training_source_when_primary_source_absent(self):
        """2026-only SOURCE has no season=2025 rows; TRAINING_SOURCE
        (fantasypros_ecr) does -- the real 2025 draft's actual situation."""
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-08-29", [("g1", "m1", 1)])
        source, snap, ranks = mp.historical_board_ranks_as_of(conn, 2025, "2025-08-30")
        assert source == "fantasypros_ecr"

    def test_unmapped_gsis_id_is_dropped_not_guessed(self):
        conn = _conn()
        conn.execute(
            "INSERT INTO rankings (source, season, player_id, adp_rank, as_of_date) "
            "VALUES ('fantasypros_ecr', 2025, 'g_unknown', 1, '2025-08-29')"
        )
        source, snap, ranks = mp.historical_board_ranks_as_of(conn, 2025, "2025-08-30")
        # snapshot date is found, but the unmapped row contributes nothing
        assert snap == "2025-08-29"
        assert ranks == {}


class TestComputePickPredictions:
    def test_reuses_mock_lab_store_baseline_formula_exactly(self):
        """Must not fork the D-3 formula -- same MODEL_VERSION, same output
        as calling mock_lab_store.predict_next_pick directly."""
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-08-29", [
            ("g1", "m1", 1), ("g2", "m2", 2), ("g3", "m3", 3),
        ])
        _, _, preds = mp.compute_pick_predictions(conn, ["m2", "m1"], 2025, "2025-08-30")
        expected_first = mls.predict_next_pick({"m1": 1, "m2": 2, "m3": 3})
        assert preds[0]["predicted_top"] == expected_first.predicted_top
        assert preds[0]["predicted_p"] == expected_first.predicted_p
        assert preds[0]["model_version"] == mls.MODEL_VERSION

    def test_board_shrinks_as_picks_are_replayed(self):
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-08-29", [
            ("g1", "m1", 1), ("g2", "m2", 2),
        ])
        _, _, preds = mp.compute_pick_predictions(conn, ["m1", "m2"], 2025, "2025-08-30")
        # at pick 2, m1 is already drafted and must not appear as a candidate
        assert preds[1]["predicted_top"] == "m2"

    def test_returns_all_none_when_no_snapshot_available(self):
        conn = _conn()
        _, snap, preds = mp.compute_pick_predictions(conn, ["m1", "m2"], 2025, "2025-08-30")
        assert snap is None
        assert preds == [None, None]

    def test_returns_all_none_when_any_pick_unresolved(self):
        """An unresolved (quarantined) pick breaks pool bookkeeping for every
        pick after it -- refuse the whole replay rather than silently
        mis-track who's still available."""
        conn = _conn()
        _seed_rankings(conn, "fantasypros_ecr", 2025, "2025-08-29", [
            ("g1", "m1", 1), ("g2", "m2", 2),
        ])
        _, snap, preds = mp.compute_pick_predictions(conn, ["m1", None, "m2"], 2025, "2025-08-30")
        assert snap == "2025-08-29"  # snapshot was found...
        assert preds == [None, None, None]  # ...but replay still refused
