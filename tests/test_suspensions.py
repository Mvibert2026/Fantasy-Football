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
