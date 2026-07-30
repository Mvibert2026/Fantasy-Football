"""
Tests for providers/mapping.py's raw-JSON -> dataclass extraction, run
entirely against the constructed fixtures in tests/fixtures/yahoo/ (see
their `_fixture_note` fields -- never a live Yahoo response, per this
build's constraint). These exercise the parser's actual behavior; a
credential-gated smoke test can't substitute for this because the parser's
correctness does not depend on having one (that is the whole point of the
walk-and-match extraction strategy -- see mapping.py's module docstring).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import providers.mapping as mapping

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "yahoo"


@pytest.fixture
def settings_raw():
    return json.loads((FIXTURES / "league_settings_response.json").read_text())


@pytest.fixture
def draft_raw():
    return json.loads((FIXTURES / "draft_results_response.json").read_text())


class TestParseLeagueSettings:
    def test_scalar_fields_extracted(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="461.l.154693")
        assert s.league_key == "461.l.154693"
        assert s.name == "Westwood"
        assert s.max_teams == 10
        assert s.num_playoff_teams == 4
        assert s.playoff_start_week == 16
        assert s.uses_playoff_reseeding is False

    def test_roster_positions_extracted_with_counts(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        by_pos = {rp.position: rp for rp in s.roster_positions}
        assert by_pos["QB"].count == 1
        assert by_pos["WR"].count == 3
        assert by_pos["RB"].count == 2
        assert by_pos["W/R/T"].count == 2
        assert by_pos["BN"].count == 6
        assert by_pos["BN"].is_bench is True
        assert by_pos["QB"].is_bench is False

    def test_stat_modifiers_extracted(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        by_id = {sm.stat_id: sm for sm in s.stat_modifiers}
        assert by_id[11].value == 0.5  # receptions
        assert by_id[5].value == 4.0  # passing TD
        assert by_id[6].value == -2.0  # interception

    def test_bonuses_extracted_with_points_and_target(self, settings_raw):
        # This is the load-bearing case for FR-062's biggest payoff claim:
        # Westwood's stacking yardage bonuses readable from Yahoo's own
        # shape (research doc SS0 item 4).
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        rushing = next(sm for sm in s.stat_modifiers if sm.stat_id == 9)
        assert len(rushing.bonuses) == 3
        targets = sorted(b.target for b in rushing.bonuses)
        assert targets == [100.0, 150.0, 200.0]
        by_target = {b.target: b.points for b in rushing.bonuses}
        assert by_target[100.0] == 1.0
        assert by_target[150.0] == 1.5
        assert by_target[200.0] == 2.0

    def test_receiving_bonuses_also_extracted(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        receiving = next(sm for sm in s.stat_modifiers if sm.stat_id == 12)
        assert len(receiving.bonuses) == 3

    def test_raw_always_preserved_for_audit(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        assert s.raw == settings_raw

    def test_missing_field_produces_warning_not_crash(self):
        # Deliberately malformed / incomplete payload -- the parser must
        # degrade gracefully (module docstring), never raise.
        s = mapping.parse_league_settings({"fantasy_content": {}}, league_key="x")
        assert s.max_teams == 0
        assert s.roster_positions == []
        assert any("max_teams" in w for w in s.parse_warnings)
        assert any("roster_positions" in w for w in s.parse_warnings)

    def test_unparseable_scalar_records_warning_and_default(self):
        raw = {"name": "Westwood", "max_teams": "not-a-number"}
        s = mapping.parse_league_settings(raw, league_key="x")
        assert s.max_teams == 0
        assert any("max_teams" in w and "could not coerce" in w for w in s.parse_warnings)


class TestParseDraftResults:
    def test_picks_extracted(self, draft_raw):
        result = mapping.parse_draft_results(draft_raw)
        assert len(result.picks) == 3
        first = result.picks[0]
        assert first.pick == 1
        assert first.round == 1
        assert first.team_key == "461.l.154693.t.1"
        assert first.player_key == "461.p.1"

    def test_final_draft_has_no_live_caveat(self, draft_raw):
        result = mapping.parse_draft_results(draft_raw, is_live_estimate=False)
        assert result.is_live_estimate is False
        assert result.caveat is None

    def test_live_draft_carries_explicit_caveat(self, draft_raw):
        result = mapping.parse_draft_results(draft_raw, is_live_estimate=True)
        assert result.is_live_estimate is True
        assert result.caveat is not None
        assert "single" in result.caveat.lower() or "undated" in result.caveat.lower()

    def test_empty_draft_returns_empty_list_not_error(self):
        result = mapping.parse_draft_results({"fantasy_content": {}})
        assert result.picks == []


class TestDiffAgainstClaudeMd:
    def test_matching_settings_produce_no_diff(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        diffs = mapping.diff_against_claude_md_westwood(s)
        assert diffs == []

    def test_mismatched_team_count_is_flagged(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        s = s.__class__(**{**s.__dict__, "max_teams": 12})
        diffs = mapping.diff_against_claude_md_westwood(s)
        assert any("max_teams" in d for d in diffs)

    def test_reseeding_true_is_flagged(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        s = s.__class__(**{**s.__dict__, "uses_playoff_reseeding": True})
        diffs = mapping.diff_against_claude_md_westwood(s)
        assert any("reseeding" in d for d in diffs)

    def test_no_bonuses_at_all_is_flagged(self, settings_raw):
        s = mapping.parse_league_settings(settings_raw, league_key="x")
        stripped = [
            sm.__class__(stat_id=sm.stat_id, name=sm.name, value=sm.value, bonuses=[])
            for sm in s.stat_modifiers
        ]
        s = s.__class__(**{**s.__dict__, "stat_modifiers": stripped})
        diffs = mapping.diff_against_claude_md_westwood(s)
        assert any("Bonus" in d for d in diffs)
