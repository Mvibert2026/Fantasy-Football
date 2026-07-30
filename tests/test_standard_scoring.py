"""
Sanity checks for the standard-scoring ruleset (FR-042), written before the
callers that consume it (generate_config_matrix.py, league_builder.py) were
changed to use it, per CLAUDE.md's non-negotiable ordering.

The capability under test: a "standard scoring" ruleset that is genuinely
independent from Westwood's `scoring.LEAGUE` -- distinct object, no yardage
bonuses, and matches the founder's own explicit definition in FR-042 for the
categories he named.
"""

from __future__ import annotations

import standard_scoring as ss
from scoring import LEAGUE as WESTWOOD


def test_standard_league_is_not_westwood():
    assert ss.STANDARD_LEAGUE is not WESTWOOD
    assert ss.STANDARD_LEAGUE["offense"] != WESTWOOD["offense"]


def test_standard_league_has_no_yardage_bonuses():
    off = ss.STANDARD_LEAGUE["offense"]
    assert off["passing_yards"]["bonuses"] == []
    assert off["rushing_yards"]["bonuses"] == []
    assert off["receiving_yards"]["bonuses"] == []


def test_standard_league_matches_founders_named_categories():
    """FR-042 verbatim: 'passing 25 yd/pt, 4 pt passing TD, -2 INT, 10 yd/pt
    rushing and receiving, 6 pt TD, -2 fumble lost'."""
    off = ss.STANDARD_LEAGUE["offense"]
    assert off["passing_yards"]["per"] == 25
    assert off["passing_td"] == 4
    assert off["interception"] == -2
    assert off["rushing_yards"]["per"] == 10
    assert off["rushing_td"] == 6
    assert off["receiving_yards"]["per"] == 10
    assert off["receiving_td"] == 6
    assert off["fumbles_lost"] == -2


def test_standard_league_defense_differs_from_westwood_points_allowed():
    """Regression guard: defense must be a real, distinct ruleset, not a
    silent copy of Westwood's (the exact bug this file exists to fix)."""
    assert ss.STANDARD_LEAGUE["defense"] != WESTWOOD["defense"]


def test_standard_scoring_variant_sets_receptions_only():
    zero = ss.standard_scoring_variant(0.0)
    half = ss.standard_scoring_variant(0.5)
    full = ss.standard_scoring_variant(1.0)
    assert zero["offense"]["receptions"] == 0.0
    assert half["offense"]["receptions"] == 0.5
    assert full["offense"]["receptions"] == 1.0
    for key in zero["offense"]:
        if key == "receptions":
            continue
        assert zero["offense"][key] == full["offense"][key]


def test_standard_scoring_variant_does_not_mutate_shared_constant():
    before = dict(ss.STANDARD_LEAGUE["offense"])
    ss.standard_scoring_variant(1.0)
    assert ss.STANDARD_LEAGUE["offense"]["receptions"] == before["receptions"]


def test_scoring_ruleset_note_flags_defense_as_unverified():
    assert "UNVERIFIED" in ss.SCORING_RULESET_NOTE
    assert "FR-042" in ss.SCORING_RULESET_NOTE
