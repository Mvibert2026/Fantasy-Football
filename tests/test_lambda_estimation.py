import math

import numpy as np

import lambda_estimation as le
import live_availability as la


def test_target_sums_to_roster_size():
    assert abs(sum(la.TARGET.values()) - 16.0) < 1e-9


def test_share_bar_sums_to_one():
    assert abs(sum(la.SHARE_BAR.values()) - 1.0) < 1e-9


def test_a_teams_first_pick_has_all_zero_x_vector():
    """No picks made yet => share_t == share_bar for every position =>
    log(1) == 0. This is the 'the formula does not pretend to know things
    early that it cannot know' property, checked directly."""
    picks = [
        {"overall_pick": 1, "team_slot": 1, "position": "WR"},
        {"overall_pick": 2, "team_slot": 2, "position": "RB"},
    ]
    teams, x_rows, y_idx = le.build_regression_rows(picks)
    assert np.allclose(x_rows[0], 0.0)
    assert np.allclose(x_rows[1], 0.0)


def test_saturated_position_produces_negative_x_next_pick():
    """A team that just took a QB should show a NEGATIVE log-share-ratio for
    QB on its next pick (need suppressed toward the eps floor) -- the same
    near-hard-cap behaviour SS2 measures from the 2025 composition table."""
    picks = [
        {"overall_pick": 1, "team_slot": 1, "position": "QB"},
        {"overall_pick": 2, "team_slot": 1, "position": "WR"},
    ]
    teams, x_rows, y_idx = le.build_regression_rows(picks)
    qb_i = la.POSITIONS.index("QB")
    assert x_rows[1][qb_i] < 0.0


def test_conditional_logit_recovers_known_beta_on_synthetic_data():
    """Sanity-checks the MLE machinery in isolation: generate choices FROM the
    model's own functional form with a known true beta, and verify the fit
    recovers it. This is what check #1's spirit demands of the regression
    tool itself, separate from any real-data question."""
    rng = np.random.default_rng(20260726)
    true_beta = 0.8
    k = len(la.POSITIONS)
    n = 4000
    x_rows = [rng.normal(0.0, 1.0, size=k) for _ in range(n)]
    y_idx = []
    for x in x_rows:
        z = true_beta * x
        p = np.exp(z - z.max())
        p /= p.sum()
        y_idx.append(int(rng.choice(k, p=p)))
    teams = [i % 10 for i in range(n)]  # 10 synthetic clusters, like the real draft

    fit = le.fit_conditional_logit(x_rows, y_idx, teams)
    assert fit["converged"]
    assert abs(fit["lambda_hat"] - true_beta) < 0.1
    assert fit["se_clustered"] > 0
    assert fit["n_obs"] == n
    assert fit["n_teams"] == 10


def test_conditional_logit_beta_zero_when_choices_are_uniform_random():
    """If position choice is independent of the need covariate entirely
    (uniform random pick among alternatives), the fitted beta should be near
    zero -- confirms the estimator does not manufacture a spurious effect."""
    rng = np.random.default_rng(20260727)
    k = len(la.POSITIONS)
    n = 3000
    x_rows = [rng.normal(0.0, 1.0, size=k) for _ in range(n)]
    y_idx = [int(rng.integers(0, k)) for _ in range(n)]
    teams = [i % 10 for i in range(n)]

    fit = le.fit_conditional_logit(x_rows, y_idx, teams)
    assert fit["converged"]
    assert abs(fit["lambda_hat"]) < 0.15


def test_real_2025_draft_log_exists_and_has_160_picks():
    picks = le.load_picks()
    assert len(picks) == 160
    positions = {p["position"] for p in picks}
    assert positions == set(la.POSITIONS)
    teams = {p["team_slot"] for p in picks}
    assert teams == set(range(1, 11))


def test_estimate_lambda_from_real_2025_draft_runs_and_is_finite():
    report = le.estimate_lambda_from_2025_draft()
    assert report["n_obs"] == 160
    assert report["n_teams"] == 10
    assert report["converged"]
    assert math.isfinite(report["lambda_hat"])
    assert math.isfinite(report["se_clustered"])
    # Sign check only -- SS5(a) explicitly warns against over-reading a
    # 10-cluster, one-season estimate's precision. Direction (need suppresses
    # further drafting of a saturated position) is the load-bearing claim.
    assert report["lambda_hat"] > 0
