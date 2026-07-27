"""T9 -- canonical NFL team-code crosswalk.

Different sources in this project spell the same franchise differently:
FantasyPros (`rankings.team`) uses JAC/LAR; nflverse (schedules,
player_weekly_stats, snap_counts, injuries, depth charts) uses JAX/LA/OAK/SD/
STL depending on era; draft_picks and adp_snapshots carry PFR-style codes
(GNB, KAN, LVR, NWE, NOR, SDG, SFO, TAM, PHO, GBP, KCC, NEP, NOS, TBB, RAI,
RAM). None of that is season-ambiguous -- each historical code names exactly
one franchise across the league's history -- so a flat lookup table is
sufficient; there is no need to thread `season` through this module.

This existed as two special-cased team strings (JAC/LAR) nowhere in the
codebase before T9 -- this table is the fix: one durable mapping, used
everywhere a team code needs to be compared or joined across sources.

Canonical form: the current (2026) nflverse code, since that's what
`nflreadpy.load_schedules` returns and byes are joined against it.
"""

from __future__ import annotations

from typing import Dict, Optional

# The 32 current-era nflverse team codes. Canonicalizing to one of these
# is a no-op.
CANONICAL_TEAMS = frozenset({
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN",
    "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
})

# Sentinel codes that are known and legitimate but are NOT a franchise --
# resolving these to None is deliberate, not a gap. ('FA' = free agent /
# no current team, seen in rankings.team.)
_NON_FRANCHISE = frozenset({"FA"})

# variant code -> canonical franchise code. Every entry here is a code this
# project's own tables have actually been observed to carry (test_team_codes
# .py's DB sweep is the enforcement mechanism for "actually observed" --
# extend this table, don't special-case the caller, if a new variant shows
# up).
_VARIANT_TO_CANONICAL: Dict[str, str] = {
    # Jaguars -- FantasyPros / old nflverse spelling
    "JAC": "JAX",
    # Rams -- FantasyPros spelling, and both historical relocations
    "LAR": "LA",
    "STL": "LA",     # St. Louis Rams, 1995-2015
    "RAM": "LA",     # PFR-style
    # Raiders -- both historical relocations
    "OAK": "LV",      # Oakland, pre-2020
    "RAI": "LV",      # PFR-style
    "LVR": "LV",
    # Chargers -- pre-2017 relocation
    "SD": "LAC",
    "SDG": "LAC",     # PFR-style
    # Cardinals -- pre-1994 Phoenix name
    "PHO": "ARI",
    # PFR-style / adp_snapshots-style 3-letter codes for teams whose
    # canonical code is otherwise unambiguous
    "GNB": "GB",
    "GBP": "GB",
    "KAN": "KC",
    "KCC": "KC",
    "NWE": "NE",
    "NEP": "NE",
    "NOR": "NO",
    "NOS": "NO",
    "SFO": "SF",
    "TAM": "TB",
    "TBB": "TB",
}


def to_canonical(code: Optional[str]) -> Optional[str]:
    """Resolve any known team-code variant to its current-era canonical
    franchise code. Returns None for the known non-franchise sentinels
    (empty/None/'FA'). Raises KeyError for a code this table has never seen
    -- an unrecognized code is a data-quality event to investigate, not
    something to guess at silently."""
    if not code:
        return None
    if code in _NON_FRANCHISE:
        return None
    if code in CANONICAL_TEAMS:
        return code
    if code in _VARIANT_TO_CANONICAL:
        return _VARIANT_TO_CANONICAL[code]
    raise KeyError(f"unrecognized team code: {code!r} -- add it to team_codes.py, do not guess")
