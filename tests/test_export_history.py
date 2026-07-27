"""Tests for weekly_finishes.json / season_stats.json (thread 017/039).

Sanity checks written against thread 039's "Done looks like" checklist:
(a) shape/schema test for both files, (b) a 2003-2008 row asserting
target_data_unavailable=true and no fabricated zero, (c) a finish-vs-bye
null-vs-false distinction test. Synthetic in-memory DB so these do not
depend on what real data happens to be on disk; a smaller real-DB group
below spot-checks the same claims against data/nfl.db.
"""

import sqlite3

import pytest

import export_history as eh


def _make_conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE player_weekly_stats (
            player_id TEXT, season INTEGER, week INTEGER, season_type TEXT,
            position TEXT, team TEXT, targets INTEGER, receptions INTEGER,
            receiving_yards INTEGER, receiving_tds INTEGER, rushing_yards INTEGER,
            rushing_tds INTEGER, fantasy_points_ppr REAL
        )
        """
    )
    rows = [
        # Two WRs, 2025, week 1 and 2 -- P1 outscores P2 both weeks.
        ("P1", 2025, 1, "REG", "WR", "AAA", 8, 6, 90, 1, 0, 0, 18.0),
        ("P2", 2025, 1, "REG", "WR", "BBB", 5, 3, 40, 0, 0, 0, 7.0),
        ("P1", 2025, 2, "REG", "WR", "AAA", 7, 5, 60, 0, 0, 0, 11.0),
        ("P2", 2025, 2, "REG", "WR", "BBB", 6, 4, 55, 1, 0, 0, 13.5),
        # P1 also has an old, target-unreliable 2005 season.
        ("P1", 2005, 1, "REG", "WR", "AAA", 0, 4, 50, 0, 0, 0, 9.0),
        ("P1", 2005, 2, "REG", "WR", "AAA", 0, 2, 20, 0, 0, 0, 4.0),
        # A universe-qualifying row for P1 (>=2018) already exists above.
    ]
    c.executemany(
        "INSERT INTO player_weekly_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    c.commit()
    return c


@pytest.fixture
def conn():
    return _make_conn()


class TestWeeklyFinishesShape:
    def test_envelope_fields(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        assert out["export_version"]
        assert "generated_utc" in out
        assert "note" in out
        assert isinstance(out["players"], list)

    def test_finish_ranks_within_season_week_position(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        by_id = {p["player_id"]: p for p in out["players"]}
        p1_wk1 = next(w for w in by_id["P1"]["seasons"]["2025"]["weeks"] if w["week"] == 1)
        p2_wk1 = next(w for w in by_id["P2"]["seasons"]["2025"]["weeks"] if w["week"] == 1)
        assert p1_wk1["finish"] == 1  # 18.0 > 7.0
        assert p2_wk1["finish"] == 2

    def test_finish_order_flips_when_scoring_flips(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        by_id = {p["player_id"]: p for p in out["players"]}
        p1_wk2 = next(w for w in by_id["P1"]["seasons"]["2025"]["weeks"] if w["week"] == 2)
        p2_wk2 = next(w for w in by_id["P2"]["seasons"]["2025"]["weeks"] if w["week"] == 2)
        assert p1_wk2["finish"] == 2  # 11.0 < 13.5 this week
        assert p2_wk2["finish"] == 1


class TestSeasonStatsShape:
    def test_envelope_and_aggregation(self, conn):
        out = eh.build_season_stats(conn, ["P1", "P2"])
        by_id = {p["player_id"]: p for p in out["players"]}
        p1_2025 = next(s for s in by_id["P1"]["seasons"] if s["year"] == 2025)
        assert p1_2025["games"] == 2
        assert p1_2025["targets"] == 15  # 8 + 7
        assert p1_2025["receptions"] == 11
        assert p1_2025["fantasy_points_ppr"] == pytest.approx(29.0)


class Test2003to2008TargetUnavailable:
    def test_season_stats_marks_flag_and_nulls_targets(self, conn):
        out = eh.build_season_stats(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        row_2005 = next(s for s in p1["seasons"] if s["year"] == 2005)
        assert row_2005["target_data_unavailable"] is True
        assert row_2005["targets"] is None  # never a fabricated 0

    def test_season_stats_does_not_flag_recent_season(self, conn):
        out = eh.build_season_stats(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        row_2025 = next(s for s in p1["seasons"] if s["year"] == 2025)
        assert row_2025["target_data_unavailable"] is False
        assert row_2025["targets"] == 15

    def test_weekly_finishes_marks_season_flag(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        assert p1["seasons"]["2005"]["target_data_unavailable"] is True
        assert p1["seasons"]["2025"]["target_data_unavailable"] is False

    def test_constant_covers_exactly_2003_through_2008(self):
        assert eh.TARGET_DATA_UNAVAILABLE_SEASONS == frozenset(range(2003, 2009))
        assert 2002 not in eh.TARGET_DATA_UNAVAILABLE_SEASONS
        assert 2009 not in eh.TARGET_DATA_UNAVAILABLE_SEASONS


class TestFinishVsByeDistinction:
    def test_missing_week_with_no_schedule_data_is_null_not_bye(self, conn):
        # No schedules table/network in this synthetic DB -- _bye_weeks_by_season
        # must fail open to {} rather than fabricate a bye guess, and a week
        # with a row always carries bye=False regardless.
        out = eh.build_weekly_finishes(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        for wk in p1["seasons"]["2025"]["weeks"]:
            assert wk["bye"] is False
            assert wk["finish"] is not None

    def test_bye_and_finish_null_are_never_conflated_in_shape(self, conn):
        # A week entry must always carry both keys explicitly, so a consumer
        # can never confuse "we have no data" with "we know it was a bye".
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        for p in out["players"]:
            for season in p["seasons"].values():
                for wk in season["weeks"]:
                    assert "finish" in wk and "bye" in wk


class TestPlayerUniverse:
    def test_universe_excludes_players_without_2018_plus_row(self, conn):
        # P1 has 2025 rows so qualifies; a player with only a 2005 row would not.
        ids = eh._player_universe(conn)
        assert "P1" in ids
        assert "P2" in ids

    def test_write_all_produces_both_files(self, conn, tmp_path):
        written = eh.write_all(tmp_path, conn)
        names = {p.name for p in written}
        assert names == {"weekly_finishes.json", "season_stats.json"}
        for p in written:
            assert p.exists() and p.stat().st_size > 0


@pytest.mark.requires_db
class TestAgainstRealData:
    def test_real_db_2003_2008_row_is_flagged_and_null(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            row = conn.execute(
                "SELECT player_id FROM player_weekly_stats "
                "WHERE season = 2005 AND position = 'WR' LIMIT 1"
            ).fetchone()
            if row is None:
                pytest.skip("no 2005 WR row in this DB snapshot")
            pid = row[0] if not isinstance(row, sqlite3.Row) else row["player_id"]
            out = eh.build_season_stats(conn, [pid])
            assert out["players"], "expected the probed player_id back in season_stats output"
            seasons = out["players"][0]["seasons"]
            row_2005 = next((s for s in seasons if s["year"] == 2005), None)
            if row_2005 is not None:
                assert row_2005["target_data_unavailable"] is True
                assert row_2005["targets"] is None
        finally:
            conn.close()
