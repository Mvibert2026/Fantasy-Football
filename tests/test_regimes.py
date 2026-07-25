import numpy as np
import pytest

import regimes


def _seasons(n, start=1999):
    return list(range(start, start + n))


def test_chow_f_is_large_at_a_true_break():
    x = np.arange(20, dtype=float)
    y = np.concatenate([np.zeros(10), np.full(10, 10.0)])
    at_break = regimes.chow_f(x, y, 10)
    off_break = regimes.chow_f(x, y, 5)
    assert at_break > off_break


def test_sup_wald_locates_a_clean_level_shift():
    rng = np.random.default_rng(0)
    x = np.arange(24, dtype=float)
    y = np.concatenate([np.zeros(12), np.full(12, 8.0)]) + rng.normal(0, 0.2, 24)
    k, f = regimes.sup_wald(x, y)
    assert k == 12
    assert f > 50


def test_detect_breaks_finds_a_strong_synthetic_break():
    rng = np.random.default_rng(1)
    n = 24
    ss = _seasons(n)
    vals = list(np.concatenate([np.zeros(12), np.full(12, 8.0)]) + rng.normal(0, 0.2, n))
    breaks = regimes.detect_breaks(ss, vals, seed=7, n_bootstrap=200)
    assert len(breaks) >= 1
    # break is reported as the LAST season of the earlier regime
    assert breaks[0].season == ss[11]


def test_detect_breaks_returns_nothing_on_a_smooth_trend():
    """A clean linear trend with light noise has no structural break."""
    rng = np.random.default_rng(2)
    n = 27
    ss = _seasons(n)
    vals = list(np.arange(n) * 0.5 + rng.normal(0, 0.3, n))
    breaks = regimes.detect_breaks(ss, vals, seed=11, n_bootstrap=300)
    assert breaks == []


def test_slope_is_per_season_not_per_row_when_seasons_have_gaps():
    """The 2003-2008 exclusion must not compress the time axis: a series that
    skips seasons has to report slope per SEASON, not per observation."""
    seasons = np.array([2000, 2001, 2002, 2010, 2011, 2012], dtype=float)
    values = seasons * 2.0  # exact slope of 2.0 per season
    slope, _ = regimes._slope_with_p(seasons, values)
    assert slope == pytest.approx(2.0)
    # a row-index regressor would have produced a much steeper slope
    idx_slope, _ = regimes._slope_with_p(np.arange(6, dtype=float), values)
    assert idx_slope > 3.0


def test_analyze_metric_excludes_missing_seasons_and_flags_the_gap():
    seasons = _seasons(21, start=1999)
    seasons = [s for s in range(1999, 2026) if s not in range(2003, 2009)]
    values = [1.0 + 0.01 * (s - 1999) for s in seasons]
    res = regimes.analyze_metric("gappy", seasons, values, seed=3, n_bootstrap=100)
    assert res.has_season_gaps is True
    assert 2005 not in res.seasons
    assert len(res.seasons) == 21


def test_analyze_metric_drops_none_values():
    seasons = _seasons(12)
    values = [1.0, None, 2.0, 3.0, None, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    res = regimes.analyze_metric("sparse", seasons, values, seed=3, n_bootstrap=50)
    assert len(res.seasons) == 10
    assert None not in res.values


def test_trend_classification_thresholds():
    assert regimes._classify_trend(0.5, 0.01) == "rising"
    assert regimes._classify_trend(-0.5, 0.01) == "declining"
    assert regimes._classify_trend(0.5, 0.90) == "plateaued"


def test_recent_trends_capture_a_reversal_the_full_fit_misses():
    """A series that rises for 20 seasons then falls for 6 should fit RISING
    overall but report a DECLINING recent window -- this is the cycle-position
    question the whole-regime slope cannot answer."""
    seasons = np.array(_seasons(26), dtype=float)
    values = np.concatenate([np.arange(20) * 1.0, 20 - np.arange(1, 7) * 2.0])
    full_slope, full_p = regimes._slope_with_p(seasons, values)
    trends = regimes._recent_trends(seasons, values)
    assert regimes._classify_trend(full_slope, full_p) == "rising"
    assert trends[5].trend == "declining"


def test_era_similarity_excludes_adjacent_seasons():
    seasons = _seasons(20)
    # metric identical in 1999 and 2018, noisy elsewhere
    data = {"m": [0.0 if s in (1999, 2018) else float(i) for i, s in enumerate(seasons)]}
    best, usable, ranked = regimes.most_similar_prior_season(
        seasons, data, target_season=2018, min_gap=5
    )
    assert usable == ["m"]
    assert best == 1999
    assert all(s <= 2018 - 5 for s, _ in ranked)


def test_era_similarity_ignores_metrics_with_missing_values():
    seasons = _seasons(12)
    data = {
        "complete": [float(i) for i in range(12)],
        "incomplete": [None] * 12,
    }
    _, usable, _ = regimes.most_similar_prior_season(seasons, data, target_season=2010, min_gap=5)
    assert usable == ["complete"]


def test_bootstrap_p_value_is_reproducible_under_a_fixed_seed():
    rng = np.random.default_rng(5)
    x = np.arange(24, dtype=float)
    y = np.arange(24) * 0.3 + rng.normal(0, 1.0, 24)
    _, f = regimes.sup_wald(x, y)
    p1 = regimes._bootstrap_p_value(x, y, f, seed=99, n_bootstrap=200)
    p2 = regimes._bootstrap_p_value(x, y, f, seed=99, n_bootstrap=200)
    assert p1 == p2
