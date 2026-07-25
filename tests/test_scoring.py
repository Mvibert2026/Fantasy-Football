import pytest

from scoring import ReplacementLevels, compute_vbd, score_defense_game, score_offensive_game


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
    levels = ReplacementLevels()
    baselines = levels.baselines()
    assert baselines == {"QB": 10, "RB": 28, "WR": 41, "TE": 11}


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
