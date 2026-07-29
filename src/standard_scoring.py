"""
Standard scoring ruleset (FR-042) -- the "everything except Westwood" track.

WHY THIS FILE EXISTS. `scoring.LEAGUE` is Westwood's ruleset: half-PPR with
stacking yardage bonuses (+1/+1.5/+2 at 100/150/200 rushing and receiving,
300/350/400 passing), verified against the live platform 2026-07-27
(ADR-052). Until 2026-07-29, `generate_config_matrix.py`'s 24 presets AND
`league_builder.py`'s custom-league builder both started from
`copy.deepcopy(scoring.LEAGUE)` and only swapped the reception value -- so
every preset and every founder-created league silently inherited Westwood's
bonuses, TD values, and defensive scoring while being labeled a generic ESPN/
Yahoo default or a from-scratch custom league. A preset called "ESPN-default,
12 teams, half scoring" was Westwood with a different name. Founder's ruling
(FR-042, 2026-07-29): only Westwood carries the custom ruleset. Every other
league -- preset or founder-created -- gets a genuinely standard ruleset,
varying only PPR.

WHAT "STANDARD" MEANS HERE, AND THE CONFIDENCE LEVEL OF EACH PART.

Offense -- SOURCED to the founder's own words in FR-042: "passing 25 yd/pt,
4 pt passing TD, -2 INT, 10 yd/pt rushing and receiving, 6 pt TD, -2 fumble
lost, no yardage bonuses, receptions varying 0 / 0.5 / 1.0." That is exactly
what OFFENSE below encodes. This is a founder decision, not a researched
platform default -- it does not claim to match any specific platform's
confirmed settings, and should not be described as "ESPN's confirmed
defaults" the way the old file wrongly did (that claim contradicted the same
file's own admission, twelve lines later, that the ESPN fetch was blocked by
bot detection and never verified -- see generate_config_matrix.py's prior
docstring, now corrected).

return_td / two_point_conversion / offensive_fumble_return_td -- NOT
mentioned in the founder's ruling (which named the seven core offensive
categories only). Kept at the same values Westwood uses (return_td=6,
two_point_conversion=2, offensive_fumble_return_td=6) because these are near-
universal across mainstream platforms and are not the kind of "bonus
structure" the founder was distinguishing Westwood by -- Westwood's
distinguishing feature is the stacking yardage bonus, not these flat, rare-
event values. Flagged here as a judgment call, not a verified fact.

Defense -- NOT addressed by the founder's ruling at all, and NOT verified
against any platform. Reusing Westwood's defense dict here would quietly
reintroduce the exact bug this file exists to fix (an unlabeled Westwood
value presented as "standard"), so it is instead a conventional, widely-seen
default (flat per-event scoring + a coarse points-allowed ladder), explicitly
labeled UNVERIFIED below and in every export's `scoring_ruleset_note`
(export_contract.build_league_json). It is a reasonable placeholder, not a
platform-confirmed number -- do not upgrade its confidence level without an
actual source.
"""

from __future__ import annotations

import copy

# Offense -- founder-specified in FR-042, verbatim. No yardage bonuses is the
# core distinction from Westwood's scoring.LEAGUE.
STANDARD_LEAGUE = {
    "offense": {
        "passing_yards": {"per": 25, "bonuses": []},
        "passing_td": 4,
        "interception": -2,
        "rushing_yards": {"per": 10, "bonuses": []},
        "rushing_td": 6,
        "receptions": 0.5,  # overridden per-config; see standard_scoring_variant()
        "receiving_yards": {"per": 10, "bonuses": []},
        "receiving_td": 6,
        # Not named in FR-042; kept at the near-universal flat value rather
        # than guessed at differently. See module docstring.
        "return_td": 6,
        "two_point_conversion": 2,
        "fumbles_lost": -2,
        "offensive_fumble_return_td": 6,
    },
    # UNVERIFIED against any real platform -- a conventional placeholder, not
    # a confirmed default. See module docstring's "Defense" paragraph.
    "defense": {
        "sacks": 1,
        "interceptions": 2,
        "fumble_recoveries": 2,
        "touchdowns": 6,
        "safeties": 2,
        "blocked_kicks": 2,
        "return_tds": 6,
        "extra_point_returned": 2,
        "points_allowed": [
            (0, 5),
            (6, 4),
            (13, 3),
            (20, 1),
            (27, 0),
            (34, -1),
            (float("inf"), -4),
        ],
    },
}

SCORING_RULESET_NOTE = (
    "STANDARD ruleset (FR-042), not Westwood's. Offense (passing/rushing/receiving yardage "
    "rates, TD values, INT, fumbles lost) is the founder's own explicit specification: no "
    "stacking yardage bonuses, receptions varying 0/0.5/1.0 across presets. Return-TD, "
    "two-point, and offensive-fumble-return-TD values are not part of that specification and "
    "are carried over at conventional flat values as a judgment call, not a platform fact. "
    "Defense scoring is UNVERIFIED against any real platform -- a conventional placeholder, "
    "not a confirmed default -- kept deliberately distinct from Westwood's defensive scoring "
    "so this ruleset does not silently reintroduce the bug it exists to fix. Only the primary "
    "(Westwood) league uses scoring.LEAGUE, the verified custom ruleset (ADR-052)."
)


def standard_scoring_variant(ppr: float) -> dict:
    """Deep copy of STANDARD_LEAGUE with `receptions` set to `ppr`. Never
    mutates the shared module constant."""
    cfg = copy.deepcopy(STANDARD_LEAGUE)
    cfg["offense"]["receptions"] = ppr
    return cfg
