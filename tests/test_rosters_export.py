"""Tests for rosters.json (thread 016): full league rosters export.

Two groups:
- In-memory synthetic-DB tests (fast, no `requires_db`): exercise the slot
  filling / needs arithmetic against a hand-built draft, independent of
  whatever real data happens to be on disk.
- Real-DB tests (`requires_db`): assert the CURRENT true state -- no real
  2026 draft is logged yet, so every roster must come back empty. This is the
  "empty-roster case" thread 016 asked to be covered.
"""

import sqlite3

import pytest

import export_contract as ec
import league_config as lc


def _yahoo_mock() -> lc.LeagueConfig:
    scoring = {
        "offense": {
            "passing_yards": {"per": 25, "bonuses": []},
            "passing_td": 4, "interception": -2,
            "rushing_yards": {"per": 10, "bonuses": []}, "rushing_td": 6,
            "receptions": 0,
            "receiving_yards": {"per": 10, "bonuses": []}, "receiving_td": 6,
            "return_td": 6, "two_point_conversion": 2, "fumbles_lost": -2,
            "offensive_fumble_return_td": 6,
        },
        "defense": {
            "sacks": 1, "interceptions": 2, "fumble_recoveries": 2, "touchdowns": 6,
            "safeties": 2, "blocked_kicks": 2, "return_tds": 6, "extra_point_returned": 2,
            "points_allowed": [(0, 10), (6, 7), (13, 4), (20, 1), (27, 0), (34, -1),
                                (float("inf"), -4)],
        },
    }
    return lc.LeagueConfig(
        league_id="test_yahoo_mock", name="Test Yahoo Mock", platform="yahoo", teams=4,
        scoring=scoring, starters={"QB": 1, "RB": 2, "WR": 2, "TE": 1},
        flex_slots=1, flex_eligible=("RB", "WR", "TE"), bench=2, ir=1, user_draft_slot=1,
    )


def _synthetic_conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        "CREATE TABLE mock_drafts (mock_id TEXT PRIMARY KEY, league_config_id TEXT, "
        "platform TEXT, drafted_at TEXT, source TEXT, is_mock INTEGER)"
    )
    c.execute(
        "CREATE TABLE mock_picks (mock_id TEXT, overall_pick INTEGER, round INTEGER, "
        "team_slot INTEGER, mfl_id TEXT, player_name_raw TEXT)"
    )
    c.execute(
        "CREATE TABLE rankings (source TEXT, season INTEGER, player_name TEXT, position TEXT)"
    )
    c.commit()
    return c


def _seed_real_draft(conn, league_id, season, picks):
    """picks: list of (overall_pick, round, team_slot, player_name, position)."""
    conn.execute(
        "INSERT INTO mock_drafts VALUES (?,?,?,?,?,?)",
        ("real_1", league_id, "manual", f"{season}-08-30", "test", 0),
    )
    for overall, rnd, slot, name, pos in picks:
        conn.execute(
            "INSERT INTO mock_picks VALUES (?,?,?,?,?,?)",
            ("real_1", overall, rnd, slot, None, name),
        )
        conn.execute(
            "INSERT INTO rankings VALUES (?,?,?,?)", ("fantasypros_ecr", season, name, pos)
        )
    conn.commit()


# -- synthetic-DB tests: slot-filling and needs arithmetic --------------------

def test_empty_roster_shape_and_needs_before_any_draft():
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    r = ec.build_rosters_json(conn, cfg)
    assert r["teams"] == 4
    assert r["draft_state"] == "not_started"
    assert r["picks_ingested"] == 0
    assert len(r["rosters"]) == 4
    for team in r["rosters"]:
        assert team["players"] == []
        assert team["needs"] == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "BENCH": 2, "IR": 1}
        assert team["roster_slots"]["ir"]["filled"] == 0
        assert team["roster_slots"]["ir"]["required"] == 1


def test_team_slots_are_unique_and_cover_all_teams():
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    r = ec.build_rosters_json(conn, cfg)
    slots = [t["team_slot"] for t in r["rosters"]]
    assert sorted(slots) == list(range(1, cfg.teams + 1))


def test_is_user_flag_matches_user_draft_slot():
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    r = ec.build_rosters_json(conn, cfg)
    user_teams = [t for t in r["rosters"] if t["is_user"]]
    assert len(user_teams) == 1
    assert user_teams[0]["team_slot"] == cfg.user_draft_slot


def test_starters_fill_before_flex_and_flex_fills_before_bench():
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    ec.SEASON, saved = 2099, ec.SEASON
    try:
        _seed_real_draft(conn, cfg.league_id, ec.SEASON, [
            (1, 1, 1, "RB One", "RB"),
            (2, 1, 2, "QB Other", "QB"),
            (9, 2, 1, "RB Two", "RB"),   # 2nd RB -> fills RB starter slot
            (17, 3, 1, "RB Three", "RB"),  # 3rd RB -> flex (RB is flex-eligible)
            (25, 4, 1, "RB Four", "RB"),   # 4th RB -> bench (starters+flex full)
        ])
        r = ec.build_rosters_json(conn, cfg)
    finally:
        ec.SEASON = saved
    team1 = next(t for t in r["rosters"] if t["team_slot"] == 1)
    assert team1["roster_slots"]["starters"]["RB"]["filled"] == 2
    assert [p["player"] for p in team1["roster_slots"]["starters"]["RB"]["players"]] == \
        ["RB One", "RB Two"]
    assert team1["roster_slots"]["flex"]["filled"] == 1
    assert team1["roster_slots"]["flex"]["players"][0]["player"] == "RB Three"
    assert team1["roster_slots"]["bench"]["filled"] == 1
    assert team1["roster_slots"]["bench"]["players"][0]["player"] == "RB Four"
    assert team1["needs"]["RB"] == 0
    assert team1["needs"]["FLEX"] == 0
    assert team1["needs"]["BENCH"] == 1  # bench=2, 1 filled


def test_unresolved_position_flagged_not_guessed():
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    ec.SEASON, saved = 2099, ec.SEASON
    try:
        conn.execute(
            "INSERT INTO mock_drafts VALUES (?,?,?,?,?,?)",
            ("real_1", cfg.league_id, "manual", "2099-08-30", "test", 0),
        )
        conn.execute(
            "INSERT INTO mock_picks VALUES (?,?,?,?,?,?)",
            ("real_1", 1, 1, 1, None, "Mystery Player"),
        )
        conn.commit()
        r = ec.build_rosters_json(conn, cfg)
    finally:
        ec.SEASON = saved
    assert r["unresolved_position_count"] == 1
    team1 = next(t for t in r["rosters"] if t["team_slot"] == 1)
    pick = team1["players"][0]
    assert pick["position"] is None
    assert pick["position_resolved"] is False
    # An unresolved-position pick must not silently land in a starter slot.
    assert all(len(v["players"]) == 0 for v in team1["roster_slots"]["starters"].values())
    assert team1["roster_slots"]["bench"]["filled"] == 1


def test_never_infers_a_team_need_beyond_slot_arithmetic():
    """Design constraint from thread 016: no field on this artifact may claim
    to know what a team is LIKELY to draft, only what it structurally needs."""
    conn = _synthetic_conn()
    cfg = _yahoo_mock()
    r = ec.build_rosters_json(conn, cfg)
    for team in r["rosters"]:
        assert "predicted" not in str(team).lower()
        assert "likely" not in str(team).lower()
        assert "strategy" not in str(team).lower()
    assert "does not model, guess, or rank" in r["inference_scope_note"]


def test_contract_version_bumped():
    # 1.10.0 (this session, T6): board.json rows gained roster_status.
    assert ec.CONTRACT_VERSION == "1.10.0"


# -- real-DB test: today's actual state must be the empty case ---------------

@pytest.mark.requires_db
def test_primary_league_rosters_are_empty_before_the_real_2026_draft():
    import db as dbmod

    conn = dbmod.connect()
    try:
        r = ec.build_rosters_json(conn, lc.CURRENT_LEAGUE)
    finally:
        conn.close()
    assert r["draft_state"] == "not_started"
    assert r["picks_ingested"] == 0
    assert len(r["rosters"]) == lc.CURRENT_LEAGUE.teams
    assert all(t["players"] == [] for t in r["rosters"])


@pytest.mark.requires_db
def test_rosters_json_is_strict_json():
    import json

    import db as dbmod

    conn = dbmod.connect()
    try:
        r = ec.build_rosters_json(conn, lc.CURRENT_LEAGUE)
    finally:
        conn.close()
    raw = json.dumps(r, default=str, allow_nan=False)

    def strict(c):
        raise ValueError(c)

    json.loads(raw, parse_constant=strict)
