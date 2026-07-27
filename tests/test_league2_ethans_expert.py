"""League 2 ("Ethan's Expert League", Yahoo 834236) real-config confirmation.

Handoff 067 (data-ops piece). Confirms league_builder.create_league() /
export_league() build a correct, non-primary board for this founder's actual
second league, per the same generic-league pattern already proven in
tests/test_multi_league_export.py (thread 040). This is a confirmation test
of existing machinery against real settings, not new statistical work --
ReplacementLevels.from_league_config() and the K/DEF filter (ADR-039) were
already built and tested; nothing here re-derives them.

user_draft_slot=1 below is an EXPLICIT PLACEHOLDER -- the founder has not
supplied their actual draft slot in this league. Flagged here and in the
067 handoff reply, never presented as a real value (CLAUDE.md: never
fabricate a value to fill a gap).

teams=10 below is a FOUNDER OVERRIDE, not a screenshot value. The Yahoo
league-settings screenshot said "Max Teams: 12" and that transcription was
correct -- see the 067 handoff, pm reply 2026-07-27: "Ethan's expert league
may likely only end up being 10 people, treat it as a 10 person league
unless otherwise directed." Do not "fix" this back to 12 by re-reading the
screenshot; 12 is the platform's configured slot count, 10 is the founder's
directive on how many real participants to build for. See also
scripts/rebuild_ethans_expert_league.py.

Consensus-pull format-awareness (handoff 067 item 1/2) is NOT covered by
this test. See the 067 reply: the only working ingestion path
(ingest_rankings.py, DynastyProcess mirror) is already format-agnostic
(no scoring parameter at all) and is shared, unmodified, by every league
including the primary one -- there is no second, HALF-preset-specific
pull to build or test yet. The FantasyPros live API that *would* support
`scoring=HALF` remains capped at 10 players/response even filtered by
position (re-confirmed live this session), which is far below what any
league's replacement-level cutoff needs, so no new pull was built on top
of it.
"""

from __future__ import annotations

import json

import pytest

import league_builder as lb
import league_config as lc

LEAGUE2_KWARGS = dict(
    name="Ethan's Expert League (Yahoo 834236)",
    # teams=10, NOT 12 -- founder override, see module docstring.
    teams=10,
    starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DEF": 1},
    flex_slots=1,
    flex_eligible=("RB", "WR", "TE"),
    bench=5,
    ir=1,
    user_draft_slot=1,  # PLACEHOLDER -- see module docstring
    platform="yahoo",
    draft_type="snake",
    ppr=0.5,
    scoring_overrides={
        "interception": -1,
        "passing_yards": {"per": 25, "bonuses": []},
        "rushing_yards": {"per": 10, "bonuses": []},
        "receiving_yards": {"per": 10, "bonuses": []},
    },
    playoff_teams=4,
    playoff_weeks=(16, 17),
)


def _cfg(tmp_path, league_id="ethans_expert_league_test"):
    return lb.create_league(directory=tmp_path, league_id=league_id, **LEAGUE2_KWARGS)


def test_league2_config_matches_transcribed_settings(tmp_path):
    cfg = _cfg(tmp_path)
    assert cfg.teams == 10  # founder override, not the screenshot's 12 -- see module docstring
    assert cfg.flex_slots == 1
    assert cfg.starters == {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DEF": 1}
    assert cfg.scoring["offense"]["interception"] == -1
    assert cfg.scoring["offense"]["passing_yards"]["bonuses"] == []
    assert cfg.scoring["offense"]["rushing_yards"]["bonuses"] == []
    assert cfg.scoring["offense"]["receiving_yards"]["bonuses"] == []
    assert cfg.scoring["offense"]["receptions"] == 0.5
    # flex_split intentionally unmeasured for a new league (ADR-029 scope).
    assert cfg.flex_split is None


@pytest.mark.requires_db
class TestLeague2BoardJson:
    """One board build (~15s, same class-scoped-fixture pattern as
    test_multi_league_export.py) shared across assertions."""

    @pytest.fixture(scope="class")
    def board(self, tmp_path_factory):
        import db as dbmod
        import export_contract as ec

        tmp_dir = tmp_path_factory.mktemp("league2cfg")
        cfg = lb.create_league(directory=tmp_dir, league_id="ethans_expert_league_probe", **LEAGUE2_KWARGS)
        conn = dbmod.connect()
        try:
            yield ec.build_board_json(conn, cfg)
        finally:
            conn.close()

    def test_league_id(self, board):
        assert board["league_id"] == "ethans_expert_league_probe"

    def test_replacement_levels_differ_from_primary(self, board):
        # Primary league (10-team, 2 flex): RB30/WR40/TE10/QB10. League 2 is
        # also 10 teams (founder override, not the screenshot's 12) but with
        # only 1 flex slot and a K starter -- its levels must not silently
        # equal the primary's despite the same team count.
        levels = board["replacement_levels_used"]
        assert levels != {"RB": 30, "WR": 40, "TE": 10, "QB": 10}
        assert levels == {"QB": 10, "RB": 25, "WR": 35, "TE": 10}

    def test_k_and_def_excluded_from_replacement_levels(self, board):
        assert "K" not in board["replacement_levels_used"]
        assert "DEF" not in board["replacement_levels_used"]
        assert set(board["unsupported_positions"]) == {"K", "DEF"}
        assert board["def_supported"] is False

    def test_flex_split_flagged_unmeasured(self, board):
        assert board["replacement_levels_flex_split_measured"] is False
        assert board["replacement_levels_flex_split_note"] is not None

    def test_board_is_strict_json(self, board):
        raw = json.dumps(board, default=str, allow_nan=False)

        def strict(c):
            raise ValueError(c)

        json.loads(raw, parse_constant=strict)  # must not raise
