"""
Sanity checks for the provider adapter interface (providers/base.py),
written before the Yahoo/ESPN adapters that implement it.

These check the shape of the seam CLAUDE.md SS4 asks for -- a generic
interface adding a platform means implementing it, not threading
platform-specific code through the app -- independent of whether any real
network call ever succeeds.
"""

from __future__ import annotations

import pytest

from providers.base import (
    Bonus,
    DraftPick,
    DraftResult,
    LeagueProvider,
    LeagueSettings,
    ProviderUnavailable,
    RosterPositionSpec,
    StatModifier,
)


def test_provider_unavailable_is_an_exception():
    with pytest.raises(ProviderUnavailable):
        raise ProviderUnavailable("no credentials configured")


def test_league_provider_cannot_be_instantiated_directly():
    # It's an ABC with abstract methods -- a "provider" that doesn't
    # implement get_league_settings/get_draft_results must fail loudly at
    # class-definition/instantiation time, not silently no-op at call time.
    with pytest.raises(TypeError):
        LeagueProvider()  # type: ignore[abstract]


def test_incomplete_subclass_still_cannot_be_instantiated():
    class HalfProvider(LeagueProvider):
        platform = "half"

        def get_league_settings(self, league_key):
            return None

        # get_draft_results deliberately not implemented

    with pytest.raises(TypeError):
        HalfProvider()  # type: ignore[abstract]


def test_bonus_shape_matches_yfpy_documented_class():
    # Verified field names, docs/research/...-2026-07-30.md SS3.1: yfpy's
    # Bonus class carries exactly `points` and `target`.
    b = Bonus(points=1.5, target=150)
    assert b.points == 1.5
    assert b.target == 150


def test_league_settings_always_carries_raw_and_warnings():
    settings = LeagueSettings(
        league_key="461.l.1",
        name="Test League",
        platform="yahoo",
        max_teams=10,
        scoring_type="head",
        num_playoff_teams=4,
        playoff_start_week=16,
        uses_playoff_reseeding=False,
        roster_positions=[RosterPositionSpec("QB", 1, True, False)],
        stat_modifiers=[StatModifier(4, "Passing Yards", 0.04)],
    )
    # Defaults must exist and be mutable-empty, not None -- callers iterate
    # these unconditionally (scripts/yahoo_pull_league_settings.py does).
    assert settings.raw == {}
    assert settings.parse_warnings == []


def test_draft_result_live_estimate_flag_is_explicit():
    live = DraftResult(picks=[], is_live_estimate=True, caveat="single-source, unverified")
    final = DraftResult(picks=[], is_live_estimate=False)
    assert live.is_live_estimate is True
    assert live.caveat is not None
    assert final.is_live_estimate is False
    assert final.caveat is None


def test_draft_pick_cost_defaults_to_none_for_snake_drafts():
    pick = DraftPick(pick=1, round=1, team_key="461.l.1.t.1", player_key="461.p.1")
    assert pick.cost is None
