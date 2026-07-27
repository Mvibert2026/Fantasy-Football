import json
import os

import pytest

from scoring import LEAGUE, ReplacementLevels, compute_vbd, score_defense_game, score_offensive_game

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
LIVE_FIXTURE_PATH = os.path.join(FIXTURES_DIR, "league_scoring_live.json")


@pytest.mark.parametrize(
    "label,stats,expected",
    [
        (
            "QB line",
            {
                "passing_yards": 320,
                "passing_tds": 2,
                "interceptions": 1,
                "rushing_yards": 30,
                "rushing_tds": 1,
            },
            28.8,
        ),
        (
            "RB line",
            {"rushing_yards": 105, "rushing_tds": 1, "receptions": 4, "receiving_yards": 35},
            23.0,
        ),
        (
            "WR 200-yd game (all three receiving bonuses stack)",
            {"receiving_yards": 200, "receiving_tds": 2, "receptions": 10},
            41.5,
        ),
        (
            "QB 410-yd game (all three passing bonuses stack)",
            {"passing_yards": 410, "passing_tds": 3},
            32.9,
        ),
        (
            "Nets to exactly zero by arithmetic (not by clamping)",
            {"rushing_yards": 40, "fumbles_lost": 2},
            0.0,
        ),
    ],
)
def test_offensive_scoring_cases(label, stats, expected):
    assert score_offensive_game(stats) == pytest.approx(expected), label


def test_negative_scores_are_not_clamped_to_zero():
    """Yahoo permits negative player scores. A floor would silently inflate
    poor performances and bias season totals upward."""
    # 10 rush yards (1.0) + 3 fumbles lost (-6.0) = -5.0
    assert score_offensive_game({"rushing_yards": 10, "fumbles_lost": 3}) == pytest.approx(-5.0)
    # the minimal negative case: no production, one fumble lost
    assert score_offensive_game({"rushing_yards": 0, "fumbles_lost": 1}) == pytest.approx(-2.0)
    # negative QB line: 30 pass yds (1.2) - 2 INT (4.0) = -2.8
    assert score_offensive_game({"passing_yards": 30, "interceptions": 2}) == pytest.approx(-2.8)


def test_missing_keys_default_to_zero():
    assert score_offensive_game({}) == 0.0


def test_single_yardage_bonus_threshold_not_all_stack():
    # 120 receiving yards clears only the 100 threshold, not 150/200.
    stats = {"receiving_yards": 120}
    # 120/10 = 12.0 + 1.0 bonus
    assert score_offensive_game(stats) == pytest.approx(13.0)


def test_defense_shutout():
    stats = {"sacks": 4, "interceptions": 2, "touchdowns": 1, "points_allowed": 0}
    assert score_defense_game(stats) == pytest.approx(24.0)


def test_defense_points_allowed_tiers_are_exclusive():
    # Exactly 7 allowed should get the (7, 7) tier, not (0, 10).
    assert score_defense_game({"points_allowed": 7}) == pytest.approx(7.0)
    assert score_defense_game({"points_allowed": 8}) == pytest.approx(4.0)


def test_defense_blowup_loss():
    assert score_defense_game({"sacks": 1, "points_allowed": 38}) == pytest.approx(-3.0)


def test_replacement_levels_match_spec():
    """RB30/WR40/TE10/QB10 as of 2026-07-25, from the MEASURED flex split
    (was RB28/WR41/TE11 under the assumed 0.40/0.55/0.05).

    Pinned because a change here silently re-values every player on the board.
    The measurement's own window-sensitivity is +/-1 rank, so this is not a
    precise constant -- it is the midpoint, adopted for consistency with
    measurement rather than as a claimed improvement."""
    levels = ReplacementLevels()
    baselines = levels.baselines()
    assert baselines == {"QB": 10, "RB": 30, "WR": 40, "TE": 10}


def test_te_wins_no_flex_slots():
    """The one robust result of the flex measurement: TE won a flex slot in 2 of
    26 seasons. Its share rounds to zero in every window tested, so the TE
    replacement level equals its mandated count."""
    levels = ReplacementLevels()
    assert levels.flex_split["TE"] == 0.0
    assert levels.baselines()["TE"] == levels.teams * levels.starters["TE"]


def test_replacement_levels_are_tunable():
    custom = ReplacementLevels(teams=12, flex_split={"RB": 0.5, "WR": 0.5, "TE": 0.0})
    baselines = custom.baselines()
    assert baselines["QB"] == 12  # 12 teams * 1 starter, no flex share for QB
    total_flex = custom.teams * custom.flex_slots  # 12 * 2 = 24
    expected_rb = custom.teams * custom.starters["RB"] + round(total_flex * 0.5)
    assert baselines["RB"] == expected_rb


def test_compute_vbd_uses_nth_ranked_player_as_replacement():
    levels = ReplacementLevels(teams=1, starters={"WR": 1}, flex_slots=0, flex_split={})
    # replacement baseline for WR = rank 1 (only starter slot) -> 2nd-best player's points
    season_points = {"WR": [("A", 30.0), ("B", 20.0), ("C", 10.0)]}
    vbd = compute_vbd(season_points, levels)
    # baseline = WR1 = 1 starter -> index 0 -> replacement = best player's own points (30)
    assert vbd["A"] == pytest.approx(0.0)
    assert vbd["B"] == pytest.approx(-10.0)
    assert vbd["C"] == pytest.approx(-20.0)


def test_compute_vbd_handles_position_with_fewer_players_than_baseline():
    levels = ReplacementLevels()  # TE baseline = 11
    season_points = {"TE": [("OnlyTE", 50.0)]}
    vbd = compute_vbd(season_points, levels)
    assert vbd["OnlyTE"] == pytest.approx(0.0)  # replacement = itself, no crash


# --------------------------------------------------------------------------
# T2 / ADR-050: live-league verification fixture (docs/screenshots, 2026-07-27)
# --------------------------------------------------------------------------
#
# These tests were written to check `scoring.LEAGUE` against the fixture
# BEFORE loosening or otherwise touching scoring.py, per this project's
# sanity-check-before-implementation rule. `scoring.py` is not expected to
# change as a result -- the founder's own verification is that its `>=` loop
# is already correct; this is confirmation, not a fix.


def _load_live_fixture():
    with open(LIVE_FIXTURE_PATH) as f:
        return json.load(f)


def test_live_fixture_offense_matches_scoring_league():
    """Field-by-field: the live-verified Yahoo scoring table (Westwood,
    primary league, verified 2026-07-27) must match scoring.LEAGUE['offense']
    exactly. A mismatch here means either the fixture was mistranscribed or
    scoring.py has drifted from the real league settings."""
    fixture = _load_live_fixture()
    live_offense = fixture["offense"]
    code_offense = LEAGUE["offense"]

    assert set(live_offense.keys()) == set(code_offense.keys())

    for key, live_val in live_offense.items():
        code_val = code_offense[key]
        if isinstance(live_val, dict):
            assert live_val["per"] == code_val["per"], key
            # bonuses transcribed as JSON lists of [threshold, bonus]; code
            # stores them as a list of tuples -- compare as tuples.
            assert [tuple(b) for b in live_val["bonuses"]] == code_val["bonuses"], key
        else:
            assert live_val == code_val, key


def test_live_fixture_metadata_sanity():
    """Non-scoring facts captured alongside the scoring table this session
    (T2/FR-012/FR-013): team count and roster shape for the primary league."""
    fixture = _load_live_fixture()
    meta = fixture["_meta"]
    assert meta["teams"] == 10
    assert meta["league_name"] == "Westwood"
    assert meta["platform"] == "Yahoo"
    assert meta["roster_positions"]["FLEX_WRT"] == 2
    # Matches league_config.py's playoff_weeks=(16,17) -- confirmed against
    # the live screenshot this session, not a discrepancy (see ADR-050).
    assert meta["playoffs"]["weeks"] == [16, 17]


def test_yardage_bonuses_stack_all_applicable_thresholds():
    """The behavior this whole fixture exists to verify: a player crossing
    MULTIPLE yardage bonus thresholds gets ALL of them added, not just the
    highest one. 425 rushing yards clears the 100/150/200 thresholds, so the
    expected score includes all three bonuses (1.0 + 1.5 + 2.0), on top of
    425/10 = 42.5 yardage points. If scoring.py ever changed to an
    if/elif-highest-only shape, this test would catch it even though the
    existing >= loop (scoring.py, the per-threshold loops in
    score_offensive_game) already does this correctly."""
    stats = {"rushing_yards": 425}
    # 425/10 = 42.5, + 1.0 (100) + 1.5 (150) + 2.0 (200) = 47.0
    assert score_offensive_game(stats) == pytest.approx(47.0)
