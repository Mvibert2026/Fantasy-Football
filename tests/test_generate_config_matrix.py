import pytest

import generate_config_matrix as gcm
import league_config as lc


def test_build_configs_returns_24_valid_configs():
    configs = gcm.build_configs()
    assert len(configs) == 24
    ids = {c.league_id for c in configs}
    assert len(ids) == 24  # all unique
    for cfg in configs:
        cfg.validate()  # raises on any invalid config


def test_team_counts_and_scoring_variants_are_fully_crossed():
    configs = gcm.build_configs()
    seen = {(c.platform, c.teams, round(c.scoring["offense"]["receptions"], 2)) for c in configs}
    expected = {
        (platform, teams, ppr)
        for platform in ("espn", "yahoo")
        for teams in gcm.TEAM_COUNTS
        for ppr in gcm.SCORING_VARIANTS.values()
    }
    assert seen == expected


def test_yahoo_flex_excludes_te_espn_flex_includes_te():
    configs = {c.league_id: c for c in gcm.build_configs()}
    yahoo = configs["yahoo_10_half"]
    espn = configs["espn_10_half"]
    assert "TE" not in yahoo.flex_eligible
    assert "RB" in yahoo.flex_eligible and "WR" in yahoo.flex_eligible
    assert "TE" in espn.flex_eligible


def test_scoring_variants_only_change_receptions():
    standard = gcm.scoring_variant(0.0)
    full = gcm.scoring_variant(1.0)
    assert standard["offense"]["receptions"] == 0.0
    assert full["offense"]["receptions"] == 1.0
    # Everything else must be untouched.
    for key in standard["offense"]:
        if key == "receptions":
            continue
        assert standard["offense"][key] == full["offense"][key]
    assert standard["defense"] == full["defense"]


def test_scoring_variants_use_standard_ruleset_not_westwood():
    """FR-042: presets must NOT carry Westwood's custom ruleset (scoring.LEAGUE)
    -- no stacking yardage bonuses, and the offense values match the founder's
    explicit 'standard' definition, not scoring.LEAGUE's."""
    from scoring import LEAGUE as WESTWOOD

    variant = gcm.scoring_variant(0.5)
    assert variant["offense"]["passing_yards"]["bonuses"] == []
    assert variant["offense"]["rushing_yards"]["bonuses"] == []
    assert variant["offense"]["receiving_yards"]["bonuses"] == []
    assert WESTWOOD["offense"]["passing_yards"]["bonuses"] != []  # sanity: Westwood still has them
    assert variant["offense"] != WESTWOOD["offense"]
    assert variant is not WESTWOOD  # not even the same object


def test_espn_and_yahoo_roster_shapes_roster_a_kicker_and_no_replacement_level_exists_for_it():
    """K has no scoring engine (same as DEF) -- both platforms roster one, so
    both must show up in unsupported_positions once exported."""
    configs = {c.league_id: c for c in gcm.build_configs()}
    for league_id in ("espn_10_half", "yahoo_10_half"):
        assert configs[league_id].starters.get("K") == 1


@pytest.mark.requires_db
def test_one_config_exports_board_and_league_json_without_crashing():
    """Smoke-tests the full write_all pipeline for ONE synthetic config
    (not all 24 -- that's what generate_all()/the committed script output
    covers) against the real DB."""
    import json

    import db as dbmod
    import export_contract as ec

    configs = {c.league_id: c for c in gcm.build_configs()}
    cfg = configs["espn_12_full"]
    conn = dbmod.connect()
    try:
        board = ec.build_board_json(conn, cfg)
        league = ec.build_league_json(cfg)
    finally:
        conn.close()

    assert board["league_id"] == "espn_12_full"
    assert len(board["players"]) > 0
    assert league["teams"] == 12
    assert set(league["positions_without_replacement_levels"]) >= {"DEF", "K"}
    json.dumps(board, allow_nan=False)
    json.dumps(league, allow_nan=False)
