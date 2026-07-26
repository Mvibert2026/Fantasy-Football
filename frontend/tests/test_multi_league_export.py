import json

import pytest

import export_contract as ec
import export_static as es
import league_config as lc


def _yahoo_mock() -> lc.LeagueConfig:
    scoring = {
        "offense": {
            "passing_yards": {"per": 25, "bonuses": []},
            "passing_td": 4,
            "interception": -2,
            "rushing_yards": {"per": 10, "bonuses": []},
            "rushing_td": 6,
            "receptions": 0,
            "receiving_yards": {"per": 10, "bonuses": []},
            "receiving_td": 6,
            "return_td": 6,
            "two_point_conversion": 2,
            "fumbles_lost": -2,
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
        league_id="test_yahoo_mock",
        name="Test Yahoo Mock",
        platform="yahoo",
        teams=12,
        scoring=scoring,
        starters={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1},
        flex_slots=1,
        flex_eligible=("RB", "WR", "TE"),
        bench=6,
        ir=0,
        user_draft_slot=6,
    )


def test_export_dir_for_primary_is_unprefixed():
    assert ec.export_dir_for(lc.PRIMARY_LEAGUE_ID) == ec.EXPORT_DIR


def test_export_dir_for_other_league_is_prefixed():
    d = ec.export_dir_for("some_other_league")
    assert d == ec.EXPORT_DIR / "some_other_league"


@pytest.mark.requires_db
class TestBoardJsonGeneralizes:
    def test_board_json_league_id_field(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            board = ec.build_board_json(conn, _yahoo_mock())
        finally:
            conn.close()
        assert board["league_id"] == "test_yahoo_mock"

    def test_board_json_excludes_k_and_def_from_replacement_levels(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            board = ec.build_board_json(conn, _yahoo_mock())
        finally:
            conn.close()
        assert "K" not in board["replacement_levels_used"]
        assert "DEF" not in board["replacement_levels_used"]
        assert set(board["unsupported_positions"]) == {"K", "DEF"}
        assert board["def_supported"] is False

    def test_board_json_flex_split_flagged_unmeasured(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            board = ec.build_board_json(conn, _yahoo_mock())
        finally:
            conn.close()
        assert board["replacement_levels_flex_split_measured"] is False
        assert board["replacement_levels_flex_split_note"] is not None

    def test_board_json_is_strict_json(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            board = ec.build_board_json(conn, _yahoo_mock())
        finally:
            conn.close()
        raw = json.dumps(board, default=str, allow_nan=False)

        def strict(c):
            raise ValueError(c)

        json.loads(raw, parse_constant=strict)  # must not raise


def test_league_json_reflects_the_config_not_the_primary_defaults():
    league = ec.build_league_json(_yahoo_mock())
    assert league["teams"] == 12
    assert league["rounds"] == 15
    assert league["user_draft_slot"] == 6
    assert league["roster"]["kicker"] is True
    assert league["roster"]["starters"]["K"] == 1
    assert set(league["positions_without_replacement_levels"]) == {"K", "DEF"}
    assert league["scoring"]["offense"]["receptions"] == 0


def test_league_json_primary_unaffected_by_new_positions_field():
    league = ec.build_league_json(lc.CURRENT_LEAGUE)
    assert league["positions_without_replacement_levels"] == ["DEF"]
    assert league["def_supported"] if "def_supported" in league else True  # not a board.json field
    assert league["roster"]["kicker"] is False


def test_opponents_json_generic_for_new_league():
    opp = es.build_opponents(_yahoo_mock())
    assert len(opp["opponents"]) == 11  # 12 teams - 1 (the user)
    assert all(p["team_name"] is None for p in opp["opponents"])
    assert all("NOT SUPPLIED" in p["data_status"] for p in opp["opponents"])


def test_opponents_json_primary_still_has_known_managers():
    opp = es.build_opponents(lc.CURRENT_LEAGUE)
    named = [p for p in opp["opponents"] if p["team_name"] is not None]
    assert {p["team_name"] for p in named} == {"Shit Leopards", "Cucked Commish"}


def test_nulls_json_not_run_for_new_league():
    findings = es.build_nulls(_yahoo_mock())
    assert len(findings) == len(es._NULLS_BASE)
    for f in findings:
        assert f["result"] == "NOT_YET_RUN_FOR_THIS_LEAGUE"
        assert "id" in f and "claim_tested" in f  # identity/method preserved


def test_nulls_json_primary_has_real_results():
    findings = es.build_nulls(lc.CURRENT_LEAGUE)
    assert findings == es._NULLS_BASE
    assert all(f["result"] != "NOT_YET_RUN_FOR_THIS_LEAGUE" for f in findings)


def test_glossary_primary_unchanged():
    g = es.build_glossary(lc.CURRENT_LEAGUE)
    assert g == es._GLOSSARY_BASE


def test_glossary_new_league_cites_its_own_numbers():
    g = es.build_glossary(_yahoo_mock())
    text = g["replacement level"]["long_explanation"]
    assert "12 teams" in text
    assert "QB12" in text
    # must NOT silently claim the primary league's specific levels
    assert "RB30, WR40, TE10, QB10" not in text
