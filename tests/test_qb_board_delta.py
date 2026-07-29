"""Sanity checks for the "why are QBs high in a 4-pt-passing-TD league" question
(thread: backend-qb-delta, 2026-07-29).

These are written BEFORE the diagnostic that uses them, per CLAUDE.md agent rules.
They pin the three structural facts the explanation rests on:

  1. Board VBD is INVARIANT to the curve intercept. VBD = b*(ln rank - ln base),
     so any scoring change that shifts a whole position by a constant moves the
     board not at all. This is why "4 vs 6 points per passing TD" cannot be
     reasoned about as a level effect.
  2. Yardage bonuses are applied PER GAME, not to season totals. A threshold
     bonus computed off a season total would inflate elite QBs enormously.
  3. The OLS log-rank slope is LINEAR in the outcome vector, so the slope --
     and therefore VBD -- decomposes EXACTLY (not approximately) across
     additive scoring components.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from make_board import RankCurve, _fit_one  # noqa: E402
from scoring import score_offensive_game  # noqa: E402


# --------------------------------------------------------------- 1. intercept
def test_vbd_is_invariant_to_curve_intercept():
    """VBD = predict(rank) - predict(base) cancels the intercept exactly.

    Consequence: a scoring rule that adds a CONSTANT to every player at a
    position cannot change that position's board placement at all.
    """
    base_rank = 10
    for shift in (0.0, 50.0, -120.0, 1e4):
        c = RankCurve("QB", intercept=300.0 + shift, slope_log_rank=-40.0,
                      r_squared=0.2, residual_sd=50.0, n_obs=100, max_rank_fitted=20)
        for rank in (1, 5, 10, 20):
            vbd = c.predict(rank) - c.predict(base_rank)
            expected = -40.0 * (np.log(rank) - np.log(base_rank))
            assert vbd == pytest.approx(expected, abs=1e-9)


def test_constant_shift_in_points_does_not_change_fitted_slope():
    """Adding a constant to every observation moves the intercept only."""
    pairs = [(r, 300.0 - 40.0 * np.log(r) + (r % 3) * 7) for r in range(1, 21)]
    base = _fit_one("QB", pairs)
    shifted = _fit_one("QB", [(r, y + 137.0) for r, y in pairs])
    assert shifted.slope_log_rank == pytest.approx(base.slope_log_rank, abs=1e-9)
    assert shifted.intercept == pytest.approx(base.intercept + 137.0, abs=1e-6)


# ------------------------------------------------------------- 2. per-game
def test_yardage_bonus_is_per_game_not_per_season():
    """17 games of 250 passing yards = 4250 season yards but ZERO bonuses.

    If the engine ever scored off a season total it would award all three
    passing bonuses here. This is the load-bearing check on the leading
    defect hypothesis.
    """
    per_game = {"passing_yards": 250}
    got = sum(score_offensive_game(per_game) for _ in range(17))
    # 250/25 = 10.0 per game, no bonus (250 < 300)
    assert got == pytest.approx(170.0, abs=1e-9)

    # The season-total mistake would have produced this instead:
    season_total_mistake = score_offensive_game({"passing_yards": 4250})
    assert season_total_mistake == pytest.approx(170.0 + 1.0 + 1.5 + 2.0, abs=1e-9)
    assert got != pytest.approx(season_total_mistake)


def test_passing_bonuses_stack_at_thresholds():
    """CLAUDE.md §7: bonuses stack, verified against the live Yahoo platform."""
    base = score_offensive_game({"passing_yards": 299})
    assert base == pytest.approx(299 / 25, abs=1e-9)
    assert score_offensive_game({"passing_yards": 300}) == pytest.approx(300 / 25 + 1.0)
    assert score_offensive_game({"passing_yards": 350}) == pytest.approx(350 / 25 + 1.0 + 1.5)
    assert score_offensive_game({"passing_yards": 400}) == pytest.approx(
        400 / 25 + 1.0 + 1.5 + 2.0
    )


def test_passing_td_is_four_points():
    """The league's stingy setting -- pinned so a silent change is caught."""
    assert score_offensive_game({"passing_tds": 1}) == pytest.approx(4.0)
    assert score_offensive_game({"rushing_tds": 1}) == pytest.approx(6.0)
    assert score_offensive_game({"receiving_tds": 1}) == pytest.approx(6.0)


# --------------------------------------------------------- 3. decomposition
def _pooled(conn, pos):
    import db as dbmod
    import make_board as mb

    train = mb.resolve_training_seasons(conn, 2026)
    obs = mb.collect_observations(conn, train)
    return [p for s in train for p in obs[s].get(pos, [])], train


@pytest.mark.requires_db
def test_yardage_bonuses_are_immaterial_to_the_board():
    """MEASURED 2026-07-29: turning every yardage bonus OFF moves Josh Allen
    zero board ranks. The bonuses contribute ~2% of QB1's value-over-
    replacement. This pins the refutation of the "stacking passing bonuses are
    why QBs rank high" hypothesis, so a future change that makes bonuses
    load-bearing shows up as a test failure rather than as a story.
    """
    import copy
    import db as dbmod
    import make_board as mb
    from scoring import LEAGUE

    if not dbmod.DB_PATH.exists():
        pytest.skip("nfl.db not available")
    conn = dbmod.connect(dbmod.DB_PATH)
    try:
        nobonus = copy.deepcopy(LEAGUE)
        for k in ("passing_yards", "rushing_yards", "receiving_yards"):
            nobonus["offense"][k]["bonuses"] = []

        full, _ = mb.build_board(conn, 2026, n_bootstrap=0)
        off, _ = mb.build_board(conn, 2026, n_bootstrap=0, scoring_cfg=nobonus)

        def rank_of(board, name):
            return next(r.overall_rank for r in board if name in r.player)

        assert rank_of(full, "Allen") == rank_of(off, "Allen")
        # and the QB VBD barely moves
        vf = next(r.vbd for r in full if "Allen" in r.player)
        vo = next(r.vbd for r in off if "Allen" in r.player)
        assert abs(vf - vo) / vf < 0.05
    finally:
        conn.close()


@pytest.mark.requires_db
def test_qb_curve_slope_collapsed_in_2025():
    """MEASURED 2026-07-29: the QB rank->points slope is NOT stable across the
    five training seasons. It runs roughly -67, -73, -59, -45, -4 for
    2021..2025 -- a monotone collapse, with 2025 essentially flat.

    The board pools all five seasons with EQUAL weight, so the shipped QB
    result is an average over a regime that was disappearing. This test exists
    so that fact cannot quietly stop being true (or quietly stay true) without
    someone noticing. CLAUDE.md §6.4 non-stationarity.
    """
    import db as dbmod
    import make_board as mb

    if not dbmod.DB_PATH.exists():
        pytest.skip("nfl.db not available")
    conn = dbmod.connect(dbmod.DB_PATH)
    try:
        train = mb.resolve_training_seasons(conn, 2026)
        obs = mb.collect_observations(conn, train)
        slopes = {
            s: mb._fit_one("QB", obs[s]["QB"]).slope_log_rank for s in train
        }
        assert slopes[2025] > -20, f"expected a near-flat 2025 QB slope, got {slopes}"
        assert slopes[2021] < -50 and slopes[2022] < -50, slopes
        # the most recent season is the flattest of the five
        assert slopes[2025] == max(slopes.values()), slopes
    finally:
        conn.close()


@pytest.mark.requires_db
def test_rank_points_curve_is_misspecified_for_rb_and_wr():
    """MEASURED 2026-07-29: RB and WR points are CONCAVE in log(rank) -- the
    slope fitted on ranks 21-45 (RB) / 21-60 (WR) is roughly twice as steep as
    the slope fitted on ranks 1-20. A single log-linear fit therefore
    overstates the top-of-board gap for those positions.

    QB does not show this (ranks 1-10 vs 11-20 are comparable), so the
    misspecification is asymmetric ACROSS positions, which matters because the
    board ranks positions against each other. Recorded as a known open issue,
    not fixed here -- changing the estimator is a methodology decision that
    needs the Statistician/Red-team gate (CLAUDE.md §8).
    """
    import db as dbmod
    import make_board as mb

    if not dbmod.DB_PATH.exists():
        pytest.skip("nfl.db not available")
    conn = dbmod.connect(dbmod.DB_PATH)
    try:
        train = mb.resolve_training_seasons(conn, 2026)
        obs = mb.collect_observations(conn, train)

        def slope(pos, lo, hi):
            pairs = [p for s in train for p in obs[s].get(pos, []) if lo <= p[0] <= hi]
            return mb._fit_one(pos, pairs).slope_log_rank

        assert slope("RB", 21, 45) < 1.8 * slope("RB", 1, 20)
        assert slope("WR", 21, 60) < 1.8 * slope("WR", 1, 20)
        # QB is comparable across its two halves -- no such asymmetry
        assert abs(slope("QB", 11, 20) / slope("QB", 1, 10)) < 1.3
    finally:
        conn.close()


def test_slope_decomposes_exactly_across_additive_components():
    """OLS slope is a fixed linear functional of y for fixed x, so if
    y = y_a + y_b then slope(y) = slope(y_a) + slope(y_b) EXACTLY.

    This is what licenses attributing shares of QB VBD to passing yards,
    passing TDs, bonuses and rushing separately without approximation.
    """
    rng = np.random.default_rng(7)
    ranks = list(range(1, 21))
    ya = {r: 300.0 - 40.0 * np.log(r) + rng.normal(0, 20) for r in ranks}
    yb = {r: 80.0 - 9.0 * np.log(r) + rng.normal(0, 5) for r in ranks}

    fa = _fit_one("QB", [(r, ya[r]) for r in ranks])
    fb = _fit_one("QB", [(r, yb[r]) for r in ranks])
    fboth = _fit_one("QB", [(r, ya[r] + yb[r]) for r in ranks])

    assert fboth.slope_log_rank == pytest.approx(
        fa.slope_log_rank + fb.slope_log_rank, abs=1e-9
    )
    assert fboth.intercept == pytest.approx(fa.intercept + fb.intercept, abs=1e-9)
