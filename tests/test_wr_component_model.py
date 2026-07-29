"""Guardrail tests for the WR component model (FR-054).

These test the things that, if broken, would make every number the model
produces confidently wrong: the look-ahead gate, the survivorship rule, and the
claim that a component projection can be re-scored under a different ruleset.

They deliberately do NOT test accuracy. Accuracy is measured by the walk-forward
in `experiments/bottomup/components/run_wr.py` and judged by `strategist`, not
asserted here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments.bottomup.components import wr_data as W
from experiments.bottomup.components.wr_model import (
    HALF_PPR, ShrunkRate, WRComponentModel, binom_glm, score_components,
)

DB = Path(__file__).resolve().parents[1] / "data" / "nfl.db"
needs_db = pytest.mark.skipif(not DB.exists(), reason="data/nfl.db not built")


# --------------------------------------------------------------- pure logic
def test_binom_glm_recovers_a_known_rate():
    """A flat logistic with no slope must return the pooled log-odds."""
    n = 400
    x = np.column_stack([np.ones(n), np.zeros(n)])
    trials = np.full(n, 16.0)
    succ = np.full(n, 4.0)          # true p = 0.25
    beta = binom_glm(x, succ, trials)
    p = 1.0 / (1.0 + np.exp(-beta[0]))
    assert abs(p - 0.25) < 0.01


def test_binom_glm_survives_a_rare_event():
    """The 200-yard threshold separates; a plain IRLS diverges here."""
    rng = np.random.default_rng(0)
    n = 500
    ypg = rng.uniform(5, 100, n)
    x = np.column_stack([np.ones(n), np.log1p(ypg)])
    trials = np.full(n, 15.0)
    succ = (ypg > 95).astype(float)   # a handful of events, perfectly separated
    beta = binom_glm(x, succ, trials)
    assert np.isfinite(beta).all()


def test_shrunk_rate_pulls_small_samples_harder():
    sr = ShrunkRate("cr", "num", "den", prior=0.60, k=50.0, slope=1.0, intercept=0.0)
    f = pd.DataFrame({"num": [8.0, 240.0], "den": [10.0, 300.0]})   # both 80%
    out = sr.raw(f)
    assert out[0] < out[1], "the 10-target player must be pulled further to the prior"
    assert abs(out[0] - 0.60) < abs(out[1] - 0.60)


def test_score_components_re_scores_under_a_different_ruleset():
    """The reason components exist: one projection, any league."""
    comp = pd.DataFrame({
        "proj_receptions": [80.0], "proj_rec_yards": [1100.0],
        "proj_rec_tds": [7.0], "proj_rush_yards": [20.0], "proj_rush_tds": [0.0],
        "proj_fumbles_lost": [1.0], "proj_games": [16.0],
        "p_100yd_game": [0.30], "p_150yd_game": [0.08], "p_200yd_game": [0.01],
    })
    half = score_components(comp, HALF_PPR)[0]

    full_ppr_no_bonus = dict(HALF_PPR, per_reception=1.0, rec_yard_bonuses=())
    full = score_components(comp, full_ppr_no_bonus)[0]

    # +0.5/reception on 80 catches = +40; minus the whole bonus block
    bonus = 16.0 * (1.0 * 0.30 + 1.5 * 0.08 + 2.0 * 0.01)
    assert full == pytest.approx(half + 40.0 - bonus, abs=1e-6)


def test_score_components_refuses_an_unmodelled_threshold():
    comp = pd.DataFrame({
        "proj_receptions": [1.0], "proj_rec_yards": [1.0], "proj_rec_tds": [0.0],
        "proj_rush_yards": [0.0], "proj_rush_tds": [0.0], "proj_fumbles_lost": [0.0],
        "proj_games": [1.0], "p_100yd_game": [0.1],
    })
    weird = dict(HALF_PPR, rec_yard_bonuses=((125, 1.0),))
    with pytest.raises(KeyError):
        score_components(comp, weird)


# --------------------------------------------------------- look-ahead gates
@needs_db
def test_panel_refuses_the_sealed_holdout():
    panel = W.build_panel(DB)
    with pytest.raises(W.HoldoutViolation):
        panel.before(W.HOLDOUT_SEASON)
    with pytest.raises(W.HoldoutViolation):
        panel.outcomes(W.HOLDOUT_SEASON)


@needs_db
def test_no_holdout_row_is_ever_loaded():
    panel = W.build_panel(DB)
    assert panel.before(2024)["season"].max() < W.HOLDOUT_SEASON
    assert max(panel.seasons) < W.HOLDOUT_SEASON


@needs_db
def test_before_gate_is_exclusive_of_later_seasons():
    panel = W.build_panel(DB)
    for cutoff in (2015, 2020, 2023):
        assert panel.before(cutoff)["season"].max() <= cutoff


@needs_db
def test_feature_build_touches_no_target_season_row():
    """The audit log is the enforcement; this asserts it actually fires."""
    from experiments.bottomup.components.wr_features import build_features
    panel = W.build_panel(DB)
    panel.reset_audit()
    target = 2021
    u = W.universe_for(panel, target)
    build_features(panel, u, target)
    a = panel.audit(target)
    assert a["max_feature_cutoff"] < target
    assert a["n_outcome_reads_at_target"] == 0


# ------------------------------------------------------------ survivorship
@needs_db
def test_universe_retains_players_who_scored_nothing():
    """If this ever returns zero busts, the universe has been rebuilt from
    production and every downstream number is inflated."""
    panel = W.build_panel(DB)
    for target in (2016, 2020, 2024):
        u = W.universe_for(panel, target)
        act = W.actual_points(panel, u, target)
        zero = (act["games"] == 0).sum()
        assert zero >= 20, f"{target}: only {zero} zero-game players -- suspicious"
        assert zero / len(act) > 0.10


@needs_db
def test_universe_is_computable_before_the_season():
    """Universe membership must not change when later seasons are added."""
    panel = W.build_panel(DB)
    u = W.universe_for(panel, 2019)
    hist = panel.before(2018)
    known = set(hist["player_id"]) | set(
        panel.draft.loc[panel.draft["draft_season"] <= 2019, "player_id"].dropna())
    assert set(u["player_id"]) <= known


@needs_db
def test_rookies_are_labelled_by_prior_history_not_by_admission_rule():
    panel = W.build_panel(DB)
    u = W.universe_for(panel, 2022)
    hist = set(panel.before(2021)["player_id"])
    for _, row in u.iterrows():
        expected = "veteran" if row["player_id"] in hist else "rookie"
        assert row["entry"] == expected


# --------------------------------------------------------------- ADP gating
@needs_db
def test_adp_snapshot_is_strictly_pre_kickoff():
    from experiments.bottomup.components import adp_baseline as A
    ks = A.kickoff_dates(DB)
    for season in A.adp_seasons():
        board = A.load_adp(season, db_path=DB)      # raises if any row is late
        assert len(board) > 20
        assert (board["season"] == season).all()
        assert season in ks


@needs_db
def test_adp_ids_resolve_to_the_stats_key():
    from experiments.bottomup.components import adp_baseline as A
    board = A.load_adp(2022, db_path=DB)
    assert board["unmatched"].mean() < 0.05
