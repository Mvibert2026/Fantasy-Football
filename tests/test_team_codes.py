"""T9 -- team-code crosswalk.

FantasyPros spells the Jaguars/Rams as JAC/LAR; nflverse (schedules,
player_weekly_stats, etc.) spells them JAX/LA. That single mismatch stripped
bye weeks from 22 players (all Rams, all Jaguars) on the live board --
test_floor_checks.py::test_t3_every_board_player_has_a_bye_week is the
regression pin for the downstream symptom. This file pins the crosswalk
itself: every code variant this project's own tables actually contain must
resolve to a canonical franchise, and the mapping must be a durable table,
not two special-cased strings.

Written before src/team_codes.py exists (sanity-checks-before-implementation).
"""

import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "nfl.db"

import team_codes as tc


def test_current_era_codes_map_to_themselves():
    # The 32 modern nflverse codes are already canonical -- mapping one to
    # itself must be a no-op, not a KeyError.
    for code in tc.CANONICAL_TEAMS:
        assert tc.to_canonical(code) == code


def test_known_era_and_source_variants_resolve():
    cases = {
        "JAC": "JAX",   # FantasyPros Jaguars
        "LAR": "LA",    # FantasyPros Rams
        "OAK": "LV",    # Raiders, pre-2020
        "SD": "LAC",    # Chargers, pre-2017
        "STL": "LA",    # Rams, 1995-2015
        "RAI": "LV",    # PFR-style Raiders
        "RAM": "LA",    # PFR-style Rams
        "SDG": "LAC",   # PFR-style Chargers
        "GNB": "GB",
        "KAN": "KC",
        "NWE": "NE",
        "NOR": "NO",
        "SFO": "SF",
        "TAM": "TB",
        "PHO": "ARI",   # Phoenix Cardinals, pre-1994
        "LVR": "LV",
        "GBP": "GB",
        "KCC": "KC",
        "NEP": "NE",
        "NOS": "NO",
        "TBB": "TB",
    }
    for variant, canonical in cases.items():
        assert tc.to_canonical(variant) == canonical, variant


def test_free_agent_and_unknown_are_not_silently_mapped():
    # 'FA' is not a franchise -- must resolve to None, never to a guessed team.
    assert tc.to_canonical("FA") is None
    assert tc.to_canonical(None) is None
    assert tc.to_canonical("") is None


def test_unrecognized_code_raises_rather_than_guesses():
    with pytest.raises(KeyError):
        tc.to_canonical("ZZZ")


@pytest.mark.skipif(not DB_PATH.exists(), reason="nfl.db not available")
def test_every_distinct_team_code_in_every_table_resolves():
    """Positive-coverage sweep: every team code actually present anywhere in
    the DB's team-bearing columns must resolve to a canonical franchise (or
    to None for the known non-franchise sentinels). A code this doesn't know
    about is a silent-corruption risk identical to T3's bye-week bug."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    tabs_cols = [
        ("rankings", "team"),
        ("player_weekly_stats", "team"),
        ("player_weekly_stats", "opponent_team"),
        ("snap_counts", "team"),
        ("draft_picks", "team"),
        ("depth_charts_snapshots", "team"),
        ("depth_charts_snapshots", "depth_team"),
        ("injuries", "team"),
        ("adp_snapshots", "team"),
    ]
    try:
        unresolved = []
        for table, col in tabs_cols:
            rows = conn.execute(f"SELECT DISTINCT {col} FROM {table}").fetchall()
            for (code,) in rows:
                if code is None:
                    continue
                try:
                    tc.to_canonical(code)
                except KeyError:
                    unresolved.append((table, col, code))
    finally:
        conn.close()
    assert not unresolved, (
        f"Team codes with no crosswalk entry: {unresolved}. Add them to "
        f"src/team_codes.py's mapping rather than special-casing the caller."
    )
