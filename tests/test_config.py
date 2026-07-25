import pytest

from config import ProjectConfig, SeasonWeighting


def test_uniform_weights_are_equal():
    w = SeasonWeighting(scheme="uniform").weights([2021, 2022, 2023], reference_season=2024)
    assert set(w) == {2021, 2022, 2023}
    assert all(v == pytest.approx(1 / 3) for v in w.values())


def test_weights_sum_to_one():
    w = SeasonWeighting(scheme="exponential", half_life_seasons=2.0).weights(
        [2019, 2020, 2021, 2022, 2023], reference_season=2024
    )
    assert sum(w.values()) == pytest.approx(1.0)


def test_exponential_halves_at_half_life():
    sw = SeasonWeighting(scheme="exponential", half_life_seasons=2.0)
    # raw weight at age 2 should be half the weight at age 0
    assert sw._raw_weight(2022, 2024) == pytest.approx(0.5)
    assert sw._raw_weight(2024, 2024) == pytest.approx(1.0)
    assert sw._raw_weight(2020, 2024) == pytest.approx(0.25)


def test_recent_seasons_weigh_more_than_older_ones():
    w = SeasonWeighting(scheme="exponential", half_life_seasons=3.0).weights(
        [2020, 2021, 2022, 2023], reference_season=2024
    )
    assert w[2023] > w[2022] > w[2021] > w[2020]


def test_max_lookback_drops_seasons_beyond_cap():
    w = SeasonWeighting(scheme="exponential", max_lookback=3).weights(
        [2018, 2019, 2020, 2021, 2022, 2023], reference_season=2024
    )
    # max_lookback=3 means the 3 most recent prior seasons: ages 1,2,3
    assert set(w) == {2021, 2022, 2023}


def test_weights_rejects_the_reference_season_itself():
    """Weighting the season being predicted is look-ahead, not a weighting choice."""
    sw = SeasonWeighting()
    with pytest.raises(ValueError, match="at or after reference_season"):
        sw.weights([2022, 2023, 2024], reference_season=2024)


def test_linear_scheme_requires_max_lookback():
    with pytest.raises(ValueError):
        SeasonWeighting(scheme="linear").weights([2022], reference_season=2024)


def test_linear_tapers_to_zero():
    sw = SeasonWeighting(scheme="linear", max_lookback=4)
    assert sw._raw_weight(2023, 2024) == pytest.approx(0.75)
    assert sw._raw_weight(2021, 2024) == pytest.approx(0.25)


def test_future_season_is_rejected_as_lookahead():
    """A ranking input may never be weighted on a season after the one it predicts."""
    sw = SeasonWeighting()
    with pytest.raises(ValueError, match="at or after reference_season"):
        sw.weights([2025], reference_season=2024)


def test_invalid_half_life_rejected():
    with pytest.raises(ValueError):
        SeasonWeighting(half_life_seasons=0)


def test_config_describe_is_flat_and_carries_seed():
    d = ProjectConfig().describe()
    assert d["random_seed"] == 20260725
    assert "season_weighting.scheme" in d
