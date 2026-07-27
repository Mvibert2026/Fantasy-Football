"""T4 (interim) -- known-suspension deduction, deterministic, no probability
model.

Per FR-007 ("table stakes are unconditional, not traded against edge") and
the founder's own instruction: NOT a probability model, a deterministic
games-played deduction from a hand-curated fixture
(tests/fixtures/suspensions_2026.json). The real automated feed is blocked on
thread 057 (data source still unresolved) -- this is the interim mechanism
that the real feed will plug into later without changing the board-flag
contract.

A suspended player's board row must carry (a) an explicit flag, and (b)
either a deterministic games-adjusted projection, or an explicit
"not adjusted" marker with a reason -- never silence.

Written before src/suspensions.py exists.
"""

import json
from pathlib import Path

import pytest

import suspensions as sus

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "suspensions_2026.json"
REAL_LIST = Path(__file__).resolve().parent.parent / "data" / "suspensions_2026.json"


@pytest.fixture
def known_suspensions():
    return sus.load_suspensions(FIXTURE)


class TestLoadSuspensions:
    def test_loads_the_fixture_by_gsis_id(self, known_suspensions):
        assert "00-9999901" in known_suspensions
        assert known_suspensions["00-9999901"]["games"] == 6
        assert known_suspensions["00-9999901"]["appeal_status"] == "upheld"


class TestGamesAdjustment:
    def test_upheld_suspension_deducts_games_deterministically(self):
        # 17-game season, 6 games missed -> plays 11/17 of the season.
        adjusted, reason = sus.adjust_for_suspension(
            projected_points=170.0, games_missed=6, appeal_status="upheld"
        )
        assert adjusted == pytest.approx(170.0 * (11 / 17))
        assert reason == "games_adjusted"

    def test_pending_appeal_is_flagged_but_not_adjusted(self):
        # Games could still change on appeal -- adjusting now would be
        # inventing a number; flag it and say explicitly why it isn't
        # adjusted rather than silently leaving it unflagged.
        adjusted, reason = sus.adjust_for_suspension(
            projected_points=170.0, games_missed=2, appeal_status="pending"
        )
        assert adjusted is None
        assert reason == "not_adjusted_pending_appeal"

    def test_zero_games_missed_is_a_no_op(self):
        adjusted, reason = sus.adjust_for_suspension(
            projected_points=170.0, games_missed=0, appeal_status="upheld"
        )
        assert adjusted == pytest.approx(170.0)
        assert reason == "games_adjusted"

    def test_games_missed_exceeding_season_floors_at_zero(self):
        adjusted, reason = sus.adjust_for_suspension(
            projected_points=170.0, games_missed=20, appeal_status="upheld"
        )
        assert adjusted == 0.0
        assert reason == "games_adjusted"


class TestApplyToBoardRows:
    def test_suspended_player_row_carries_flag_and_adjustment(self, known_suspensions):
        rows = [
            {"player": "Synthetic Test Player One", "player_id_gsis": "00-9999901",
             "projected_points": 170.0},
            {"player": "Untouched Player", "player_id_gsis": "00-1234567",
             "projected_points": 100.0},
        ]
        out = sus.apply_suspension_flags(rows, known_suspensions)
        suspended = next(r for r in out if r["player"] == "Synthetic Test Player One")
        untouched = next(r for r in out if r["player"] == "Untouched Player")

        assert suspended["suspension_flag"] is True
        assert suspended["suspension_games"] == 6
        assert suspended["projected_points_suspension_adjusted"] == pytest.approx(
            170.0 * (11 / 17)
        )
        assert suspended["suspension_adjustment_note"] == "games_adjusted"

        # Non-suspended rows must carry the SAME keys (never a shape that
        # only exists conditionally) with honest not-applicable values.
        assert untouched["suspension_flag"] is False
        assert untouched["suspension_games"] is None
        assert untouched["projected_points_suspension_adjusted"] is None
        assert untouched["suspension_adjustment_note"] == "not_suspended"

    def test_pending_appeal_row_flags_without_fabricating_an_adjustment(self, known_suspensions):
        rows = [
            {"player": "Synthetic Test Player Two", "player_id_gsis": "00-9999902",
             "projected_points": 80.0},
        ]
        out = sus.apply_suspension_flags(rows, known_suspensions)
        row = out[0]
        assert row["suspension_flag"] is True
        assert row["projected_points_suspension_adjusted"] is None
        assert row["suspension_adjustment_note"] == "not_adjusted_pending_appeal"


class TestRealSuspensionList:
    """T4 -- distinct from the synthetic-fixture tests above. This is the
    real, WebSearch-verified, hand-curated list at data/suspensions_2026.json
    that the live board actually reads (export_contract.SUSPENSIONS_PATH),
    NOT the synthetic tests/fixtures/suspensions_2026.json used to unit-test
    the mechanism above. Real, distinct from synthetic -- do not merge these
    test classes or delete either fixture."""

    def test_real_list_loads_and_is_dated(self):
        raw = json.loads(REAL_LIST.read_text(encoding="utf-8"))
        assert raw["season"] == 2026
        assert raw["as_of_date"]  # must be recorded, never blank
        assert "sources_checked" in raw and len(raw["sources_checked"]) > 0

    def test_real_list_currently_has_no_confirmed_skill_position_entries(self):
        # As of this session's research pass (2026-07-27), exhaustive
        # WebSearch/WebFetch turned up no real, currently-pending (not
        # already served), skill-position (QB/RB/WR/TE) 2026 suspension --
        # the one confirmed real 2026 suspension found (Charles Snowden, DE)
        # has no fantasy-board consequence since this league has no
        # individual defensive-player scoring (ADR-039). An empty list here
        # is the honest, verified state, not an oversight -- see the file's
        # own _comment for the full research trail. This test pins that
        # state so a future session doesn't mistake "empty" for "unwired."
        known = sus.load_suspensions(REAL_LIST)
        assert known == {}

    def test_real_list_wired_into_live_board_is_a_correct_no_op(self):
        # End-to-end: applying today's real (currently empty) list to real
        # board-shaped rows must leave every row flagged not-suspended --
        # proving the wiring runs (not just that the mechanism CAN run, per
        # the synthetic-fixture tests above) without inventing a false
        # positive.
        known = sus.load_suspensions(REAL_LIST)
        rows = [
            {"player": "Aaron Rodgers", "player_id_gsis": "00-0023459",
             "projected_points": 250.0},
        ]
        out = sus.apply_suspension_flags(rows, known)
        assert out[0]["suspension_flag"] is False
        assert out[0]["suspension_adjustment_note"] == "not_suspended"


@pytest.mark.requires_db
class TestRealListWiredIntoBuildBoardJson:
    """Confirms export_contract.build_board_json (the actual live
    board-build entrypoint, called via write_all for every league config)
    calls the suspensions mechanism at all -- not just that the mechanism
    exists in isolation. Uses the real data/nfl.db and the real (currently
    empty) suspensions list, plus a temp fixture with a fabricated-for-test
    gsis_id matched against a real board row to prove the flag actually
    propagates through the full pipeline into board.json's player rows.
    """

    def test_board_rows_carry_suspension_keys_unconditionally(self, tmp_path):
        import sqlite3

        import db as dbmod
        import export_contract as ec
        import league_config as lc

        conn = dbmod.connect()
        try:
            board = ec.build_board_json(conn, lc.CURRENT_LEAGUE)
        finally:
            conn.close()
        assert len(board["players"]) > 0
        for row in board["players"]:
            # Every row, suspended or not, carries the same keys (never a
            # conditional shape) -- same convention apply_suspension_flags
            # itself is tested against above.
            assert "suspension_flag" in row
            assert "suspension_games" in row
            assert "projected_points_suspension_adjusted" in row
            assert "suspension_adjustment_note" in row

    def test_a_real_board_player_flagged_via_temp_fixture_propagates_through(
        self, tmp_path
    ):
        import db as dbmod
        import export_contract as ec
        import make_board
        import league_config as lc

        conn = dbmod.connect()
        try:
            row = conn.execute(
                "SELECT player_id FROM rankings WHERE source=? AND season=? "
                "AND player_id IS NOT NULL LIMIT 1",
                (make_board.SOURCE, 2026),
            ).fetchone()
            assert row is not None, "need at least one real ranked player to test against"
            gsis_id = row["player_id"]

            temp_fixture = tmp_path / "suspensions_test.json"
            temp_fixture.write_text(json.dumps({
                "season": 2026,
                "as_of_date": "2026-07-27",
                "sources_checked": ["test-only temp fixture, not a real claim"],
                "suspensions": [
                    {
                        "player_name": "temp-fixture-test-row",
                        "gsis_id": gsis_id,
                        "games": 4,
                        "appeal_status": "upheld",
                        "as_of_date": "2026-07-27",
                    }
                ],
            }), encoding="utf-8")

            board = ec.build_board_json(
                conn, lc.CURRENT_LEAGUE, suspensions_path=temp_fixture
            )
        finally:
            conn.close()

        flagged = [p for p in board["players"] if p["player_id_gsis"] == gsis_id]
        assert flagged, "the test player must appear on the board to prove anything"
        assert flagged[0]["suspension_flag"] is True
        assert flagged[0]["suspension_games"] == 4
        assert flagged[0]["suspension_adjustment_note"] == "games_adjusted"
