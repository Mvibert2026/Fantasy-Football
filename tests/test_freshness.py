"""T5 -- snapshot freshness tripwire.

Pre-mortem finding #2 (fable-draft-day-premortem-2026-07-27.md): the board is
built from whatever `rankings.as_of_date` happens to be, and nothing records
or bounds how old that snapshot is. A July ECR pull silently backs an August
draft. This pins the fix: a function that measures snapshot age from
`rankings.as_of_date` and a board-build gate that REFUSES (raises) once the
snapshot exceeds a configurable max age, plus a non-raising `check()` that
always reports the age so it can be surfaced even when still fresh.

Written before src/freshness.py exists.
"""

import sqlite3
from datetime import date

import pytest

import freshness as fr


def _conn_with_rankings(as_of_dates):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE rankings (source TEXT, season INTEGER, player_id TEXT, "
        "player_name TEXT, as_of_date TEXT)"
    )
    for i, d in enumerate(as_of_dates):
        conn.execute(
            "INSERT INTO rankings VALUES (?,?,?,?,?)",
            ("fantasypros_ecr", 2026, f"p{i}", f"Player {i}", d),
        )
    conn.commit()
    return conn


class TestSnapshotAgeDays:
    def test_age_measured_from_most_recent_as_of_date(self):
        conn = _conn_with_rankings(["2026-07-20", "2026-07-24"])
        age = fr.snapshot_age_days(
            conn, season=2026, source="fantasypros_ecr", today=date(2026, 7, 27)
        )
        assert age == 3  # from the MOST RECENT as_of_date, not the oldest

    def test_returns_none_when_no_rows(self):
        conn = _conn_with_rankings([])
        age = fr.snapshot_age_days(
            conn, season=2026, source="fantasypros_ecr", today=date(2026, 7, 27)
        )
        assert age is None

    def test_zero_age_same_day(self):
        conn = _conn_with_rankings(["2026-07-27"])
        age = fr.snapshot_age_days(
            conn, season=2026, source="fantasypros_ecr", today=date(2026, 7, 27)
        )
        assert age == 0


class TestCheckFreshness:
    def test_under_threshold_is_not_stale_but_still_reported(self):
        conn = _conn_with_rankings(["2026-07-26"])
        result = fr.check_freshness(
            conn, season=2026, source="fantasypros_ecr", max_age_days=3,
            today=date(2026, 7, 27),
        )
        assert result["age_days"] == 1
        assert result["stale"] is False
        assert result["max_age_days"] == 3
        assert result["as_of_date"] == "2026-07-26"

    def test_exactly_at_threshold_is_not_stale(self):
        conn = _conn_with_rankings(["2026-07-24"])
        result = fr.check_freshness(
            conn, season=2026, source="fantasypros_ecr", max_age_days=3,
            today=date(2026, 7, 27),
        )
        assert result["age_days"] == 3
        assert result["stale"] is False

    def test_over_threshold_is_stale(self):
        conn = _conn_with_rankings(["2026-07-20"])
        result = fr.check_freshness(
            conn, season=2026, source="fantasypros_ecr", max_age_days=3,
            today=date(2026, 7, 27),
        )
        assert result["age_days"] == 7
        assert result["stale"] is True

    def test_missing_snapshot_reports_none_age_and_is_stale(self):
        # No rows at all -- honest "we don't know", but treated as stale
        # (refuse to build silently on a total absence of a snapshot date).
        conn = _conn_with_rankings([])
        result = fr.check_freshness(
            conn, season=2026, source="fantasypros_ecr", max_age_days=3,
            today=date(2026, 7, 27),
        )
        assert result["age_days"] is None
        assert result["stale"] is True


class TestRequireFresh:
    def test_raises_when_stale(self):
        conn = _conn_with_rankings(["2026-07-01"])
        with pytest.raises(fr.StaleSnapshotError):
            fr.require_fresh(
                conn, season=2026, source="fantasypros_ecr", max_age_days=3,
                today=date(2026, 7, 27),
            )

    def test_does_not_raise_when_fresh(self):
        conn = _conn_with_rankings(["2026-07-27"])
        # Should not raise.
        fr.require_fresh(
            conn, season=2026, source="fantasypros_ecr", max_age_days=3,
            today=date(2026, 7, 27),
        )

    def test_error_message_states_age_and_threshold(self):
        conn = _conn_with_rankings(["2026-07-01"])
        with pytest.raises(fr.StaleSnapshotError) as exc_info:
            fr.require_fresh(
                conn, season=2026, source="fantasypros_ecr", max_age_days=3,
                today=date(2026, 7, 27),
            )
        msg = str(exc_info.value)
        assert "26" in msg  # age in days
        assert "3" in msg  # threshold
