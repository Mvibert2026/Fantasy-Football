"""
Sanity checks for real league creation (thread 040 item 1), written BEFORE
league_builder.py per CLAUDE.md's non-negotiable ordering.

The capability under test: a founder-facing "create a league" entrypoint --
name, team count, roster shape, scoring rules, draft slot -- distinct from
picking one of the 24 pre-generated configs or hand-constructing a
LeagueConfig in Python. The core risk this thread called out is that
replacement levels might get reused across leagues instead of recomputed
per format; several tests below exist specifically to catch that.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import league_builder as lb
import league_config as lc


# ------------------------------------------------------------ slug/id tests
def test_slugify_basic():
    assert lb.slugify("My Dynasty League!") == "my_dynasty_league"


def test_slugify_collapses_whitespace_and_punctuation():
    assert lb.slugify("  Bob's   2nd League -- 2026  ") == "bobs_2nd_league_2026"


def test_unique_league_id_no_collision(tmp_path):
    assert lb.unique_league_id("Fresh League", directory=tmp_path) == "fresh_league"


def test_unique_league_id_collision_gets_suffixed(tmp_path):
    (tmp_path / "taken_name.json").write_text("{}", encoding="utf-8")
    assert lb.unique_league_id("Taken Name", directory=tmp_path) == "taken_name_2"


def test_unique_league_id_rejects_reserved_primary(tmp_path):
    with pytest.raises(ValueError):
        lb.unique_league_id("primary", directory=tmp_path)


# ------------------------------------------------------------ scoring build
def test_build_scoring_applies_ppr():
    scoring = lb.build_scoring(ppr=1.0)
    assert scoring["offense"]["receptions"] == 1.0


def test_build_scoring_default_matches_league_ppr_default():
    scoring = lb.build_scoring(ppr=0.5)
    assert scoring["offense"]["receptions"] == 0.5
    # Everything else rides on this project's existing ruleset (ADR-047
    # precedent) unless explicitly overridden.
    assert scoring["offense"]["passing_td"] == 4


def test_build_scoring_overrides_are_shallow_merged_into_offense():
    scoring = lb.build_scoring(ppr=0.5, scoring_overrides={"passing_td": 6, "interception": -1})
    assert scoring["offense"]["passing_td"] == 6
    assert scoring["offense"]["interception"] == -1
    # Untouched fields survive.
    assert scoring["offense"]["rushing_td"] == 6


def test_build_scoring_does_not_mutate_shared_league_constant():
    from scoring import LEAGUE

    before = LEAGUE["offense"]["passing_td"]
    lb.build_scoring(ppr=0.5, scoring_overrides={"passing_td": 999})
    assert LEAGUE["offense"]["passing_td"] == before


# ------------------------------------------------------------ create_league
def _basic_kwargs(**overrides):
    kwargs = dict(
        name="Test League Creation",
        teams=12,
        starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1},
        flex_slots=1,
        flex_eligible=("RB", "WR", "TE"),
        bench=6,
        ir=1,
        user_draft_slot=5,
        ppr=1.0,
    )
    kwargs.update(overrides)
    return kwargs


def test_create_league_returns_valid_league_config(tmp_path):
    cfg = lb.create_league(directory=tmp_path, **_basic_kwargs())
    assert isinstance(cfg, lc.LeagueConfig)
    assert cfg.teams == 12
    assert cfg.user_draft_slot == 5
    assert cfg.scoring["offense"]["receptions"] == 1.0


def test_create_league_saves_and_is_loadable(tmp_path):
    import json

    cfg = lb.create_league(directory=tmp_path, **_basic_kwargs())
    reloaded = lc.LeagueConfig.load(cfg.league_id, directory=tmp_path)
    # Round-trip through JSON: tuples (e.g. yardage-bonus pairs) come back as
    # lists, which is JSON's own limitation, not a bug in save/load -- compare
    # via a JSON round-trip on both sides instead of raw dataclass equality.
    assert json.loads(json.dumps(reloaded.to_dict())) == json.loads(json.dumps(cfg.to_dict()))


def test_create_league_id_derived_from_name(tmp_path):
    cfg = lb.create_league(directory=tmp_path, **_basic_kwargs())
    assert cfg.league_id == "test_league_creation"


def test_create_league_explicit_id_honored(tmp_path):
    cfg = lb.create_league(directory=tmp_path, **_basic_kwargs(league_id="custom_id"))
    assert cfg.league_id == "custom_id"


def test_create_league_rejects_reserved_primary_id(tmp_path):
    with pytest.raises(ValueError):
        lb.create_league(directory=tmp_path, **_basic_kwargs(league_id=lc.PRIMARY_LEAGUE_ID))


def test_create_league_invalid_draft_slot_raises(tmp_path):
    with pytest.raises(ValueError):
        lb.create_league(directory=tmp_path, **_basic_kwargs(user_draft_slot=99))


def test_create_league_invalid_flex_eligible_raises(tmp_path):
    with pytest.raises(ValueError):
        lb.create_league(
            directory=tmp_path,
            **_basic_kwargs(flex_eligible=("RB", "WR", "K")),  # K not a starter
        )


def test_create_league_no_flex_split_supplied_by_default(tmp_path):
    # A brand-new league's flex split has not been measured -- create_league
    # must NOT silently borrow the primary league's measured split into the
    # saved config; from_league_config()'s explicit-placeholder path is what
    # should surface it later, not a value baked in at creation.
    cfg = lb.create_league(directory=tmp_path, **_basic_kwargs())
    assert cfg.flex_split is None


# ------------------------------------------------------------ per-format replacement levels
# The thread's actual concern: does a second league with different format get
# its OWN replacement levels, or the founder's league's numbers reused?

def test_replacement_levels_differ_by_format():
    from scoring import ReplacementLevels

    primary_levels, primary_measured = ReplacementLevels.from_league_config(lc.CURRENT_LEAGUE)
    assert primary_levels.baselines() == {"QB": 10, "RB": 30, "WR": 40, "TE": 10}

    other = lc.LeagueConfig(
        league_id="format_probe",
        name="Format probe",
        platform="other",
        teams=14,
        scoring=lb.build_scoring(ppr=1.0),
        starters={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "DEF": 1},
        flex_slots=2,
        flex_eligible=("RB", "WR", "TE"),
        bench=7,
        ir=1,
        user_draft_slot=1,
    )
    other_levels, other_measured = ReplacementLevels.from_league_config(other)
    other_baselines = other_levels.baselines()

    assert other_baselines != primary_levels.baselines()
    # 14 teams, 1 QB starter, no flex QB eligibility -> QB14, not QB10.
    assert other_baselines["QB"] == 14
    # A brand-new format's flex split is an unmeasured placeholder, and that
    # must be visible, not silently presented as this league's own number.
    assert other_measured is False
    assert primary_measured is True


@pytest.mark.requires_db
def test_create_and_export_league_board_uses_its_own_replacement_levels(tmp_path):
    import db as dbmod

    cfg = lb.create_league(
        directory=tmp_path,
        name="Export Probe League",
        teams=14,
        starters={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "DEF": 1},
        flex_slots=2,
        flex_eligible=("RB", "WR", "TE"),
        bench=7,
        ir=1,
        user_draft_slot=1,
        ppr=1.0,
    )
    out_dir = tmp_path / "export"
    conn = dbmod.connect()
    try:
        written = lb.export_league(cfg, out_dir, conn)
    finally:
        conn.close()

    names = {p.name for p in written}
    assert {"board.json", "league.json", "availability.json", "rosters.json"} <= names

    import json

    board = json.loads((out_dir / "board.json").read_text(encoding="utf-8"))
    league = json.loads((out_dir / "league.json").read_text(encoding="utf-8"))

    assert league["teams"] == 14
    # Must NOT be the primary league's RB30/WR40/TE10/QB10.
    assert board["replacement_levels_used"] != {"QB": 10, "RB": 30, "WR": 40, "TE": 10}
    assert board["league_id"] == cfg.league_id
