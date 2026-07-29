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
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

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


@pytest.mark.requires_db
class TestBoardBuildActuallyRefuses:
    """Integration coverage for the real gap the unit tests above don't
    close: freshness.py's pure functions are well tested in isolation, but
    nothing previously proved that `export_contract.build_board_json` --
    the actual live board-build entrypoint every league config funnels
    through via `write_all` -- calls them and really refuses. This exercises
    the real `data/nfl.db` `rankings` table (not an in-memory fixture) and a
    real LeagueConfig, forcing staleness by pushing `freshness_today` far
    enough forward that today's real as_of_date reads as stale, then
    confirms the raise. This is the check the fable pre-mortem finding #2
    asked for: not just "the function exists" but "the builder actually
    stops."
    """

    def _real_conn(self):
        import db as dbmod

        return dbmod.connect()

    def test_build_board_json_raises_on_stale_snapshot_primary_league(self):
        import export_contract as ec
        import league_config as lc

        conn = self._real_conn()
        try:
            real_age = fr.snapshot_age_days(
                conn, ec.SEASON, make_board_source(), today=date.today()
            )
            assert real_age is not None, (
                "no rankings rows on file for the primary source/season -- "
                "cannot exercise the stale path meaningfully"
            )
            far_future = date.today() + timedelta(
                days=lc.CURRENT_LEAGUE.freshness_max_age_days + real_age + 30
            )
            with pytest.raises(fr.StaleSnapshotError):
                ec.build_board_json(
                    conn, lc.CURRENT_LEAGUE, freshness_today=far_future
                )
        finally:
            conn.close()

    def test_build_board_json_does_not_raise_when_fresh_today(self):
        import export_contract as ec
        import league_config as lc

        conn = self._real_conn()
        try:
            # Sanity check the inverse: calling with the real "today" (the
            # snapshot really is fresh per CURRENT-STATE.md's dateline) must
            # NOT raise -- otherwise the test above would be trivially true
            # for the wrong reason (e.g. a bug that always raises).
            ec.build_board_json(conn, lc.CURRENT_LEAGUE, freshness_today=None)
        finally:
            conn.close()

    def test_board_json_carries_the_freshness_result_it_computes(self):
        """Thread 074: build_board_json computed a FreshnessResult on every
        call (via fr.require_fresh) and printed it to the console, but never
        attached it to the dict it returns -- so board.json shipped with
        generated_utc (file-write time) only, and no way to see the actual
        rankings snapshot's age. Pins the fields onto the returned dict and
        checks they agree with the FreshnessResult computed independently
        via fr.check_freshness for the same inputs."""
        import export_contract as ec
        import league_config as lc

        conn = self._real_conn()
        try:
            board = ec.build_board_json(conn, lc.CURRENT_LEAGUE, freshness_today=None)
            expected = fr.check_freshness(
                conn, ec.SEASON, make_board_source(),
                lc.CURRENT_LEAGUE.freshness_max_age_days, today=None,
            )
            assert board["snapshot_as_of_date"] == expected["as_of_date"]
            assert board["snapshot_age_days"] == expected["age_days"]
            assert board["snapshot_max_age_days"] == expected["max_age_days"]
            assert board["snapshot_stale"] == expected["stale"]
            assert board["snapshot_stale"] is False, (
                "snapshot is expected to be fresh at build time per "
                "CURRENT-STATE.md's dateline -- if this flips to True the "
                "snapshot needs re-pulling, not this test relaxed"
            )
            assert isinstance(board["snapshot_freshness_note"], str)
            assert "generated_utc" in board["snapshot_freshness_note"], (
                "the note must call out the distinction from generated_utc, "
                "not just restate the field names"
            )
        finally:
            conn.close()


def make_board_source():
    import make_board

    return make_board.SOURCE
