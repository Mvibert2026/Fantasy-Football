import pytest

import league_config as lc


def _minimal_kwargs(**overrides):
    kwargs = dict(
        league_id="test_league",
        name="Test League",
        platform="other",
        teams=10,
        scoring={},
        starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1},
        flex_slots=2,
        flex_eligible=("RB", "WR", "TE"),
        bench=6,
        ir=1,
        user_draft_slot=3,
    )
    kwargs.update(overrides)
    return kwargs


def test_current_league_matches_todays_hardcoded_constants():
    cfg = lc.CURRENT_LEAGUE
    assert cfg.teams == 10
    assert cfg.user_draft_slot == 3
    assert cfg.rounds == 16
    assert cfg.starters["DEF"] == 1
    assert cfg.flex_split == {"RB": 0.52, "WR": 0.48, "TE": 0.00}


def test_rounds_derived_correctly_excludes_ir():
    """Regression: an earlier draft of this formula included `ir` in the
    rounds calculation and produced 17 instead of 16 for the primary league.
    IR is a bonus roster slot, not a drafted round."""
    cfg = lc.LeagueConfig(**_minimal_kwargs(starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1}))
    assert cfg.rounds == 16  # 8 starters + 2 flex + 6 bench, ir excluded
    assert cfg.drafted_rounds() == 16


def test_explicit_rounds_mismatch_raises():
    with pytest.raises(ValueError, match="rounds"):
        lc.LeagueConfig(**_minimal_kwargs(rounds=99))


def test_invalid_user_draft_slot_raises():
    with pytest.raises(ValueError, match="user_draft_slot"):
        lc.LeagueConfig(**_minimal_kwargs(user_draft_slot=11))


def test_invalid_platform_raises():
    with pytest.raises(ValueError, match="platform"):
        lc.LeagueConfig(**_minimal_kwargs(platform="madden"))


def test_flex_eligible_position_not_in_starters_raises():
    with pytest.raises(ValueError, match="flex_eligible"):
        lc.LeagueConfig(**_minimal_kwargs(flex_eligible=("RB", "WR", "K")))


def test_unknown_starter_position_raises():
    with pytest.raises(ValueError, match="unknown position"):
        lc.LeagueConfig(**_minimal_kwargs(starters={"QB": 1, "ZZ": 1}))


def test_flex_split_position_not_flex_eligible_raises():
    with pytest.raises(ValueError, match="flex_split"):
        lc.LeagueConfig(**_minimal_kwargs(flex_split={"TE": 0.5, "K": 0.5}))


def test_round_trip_to_dict_from_dict():
    cfg = lc.CURRENT_LEAGUE
    restored = lc.LeagueConfig.from_dict(cfg.to_dict())
    assert restored == cfg


def test_save_and_load_round_trip(tmp_path):
    cfg = lc.LeagueConfig(**_minimal_kwargs())
    cfg.save(directory=tmp_path)
    loaded = lc.LeagueConfig.load("test_league", directory=tmp_path)
    assert loaded == cfg


def test_load_missing_league_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        lc.LeagueConfig.load("does_not_exist", directory=tmp_path)


def test_is_primary_flag():
    assert lc.CURRENT_LEAGUE.is_primary
    other = lc.LeagueConfig(**_minimal_kwargs())
    assert not other.is_primary
