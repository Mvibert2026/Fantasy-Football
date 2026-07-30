"""Discipline tests for factor batch 2 (vacated opportunity on real rosters,
and preseason coordinator identity).

These pin the guardrails, not the model quality:
  - the sealed holdout is unreachable through both new panel accessors,
  - both season-N reads log under the SAME `proxy` audit tag batch 1 already
    asserts on, so an arm that did not declare them is still provably clean,
  - batch 1's feature frame reproduces BIT-FOR-BIT under the extended builder,
  - the roster status taxonomy classifies every code present in the data,
  - the player-level "opportunity ahead of me" feature is actually player-level
    (two players on one club differ) and is monotone in the right direction.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.bottomup.components import pos_data as D  # noqa: E402
from experiments.bottomup.components.pos_eval import universe_for  # noqa: E402
from experiments.bottomup.factors.factor_features import (  # noqa: E402
    build_factor_features,
)
from experiments.bottomup.factors.factor_features2 import (  # noqa: E402
    _ahead_of_me, build_factor2_features,
)

DB_PATH = ROOT / "data" / "nfl.db"
needs_db = pytest.mark.skipif(not DB_PATH.exists(), reason="nfl.db not available")


@pytest.fixture(scope="module")
def panel():
    return D.build_panel(DB_PATH)


@needs_db
def test_holdout_sealed_for_both_new_accessors(panel):
    with pytest.raises(D.HoldoutViolation):
        panel.preseason_roster(D.HOLDOUT_SEASON)
    with pytest.raises(D.HoldoutViolation):
        panel.preseason_coordinators(D.HOLDOUT_SEASON)


@needs_db
def test_new_reads_log_under_the_proxy_tag(panel):
    """The audit assertion batch 1 already runs (`n_preseason_proxy_reads == 0`)
    must keep catching these. If either read logged under `feature` instead, an
    undeclared arm could touch season-N data and the audit would pass."""
    panel.reset_audit()
    panel.preseason_roster(2020)
    panel.preseason_coordinators(2020)
    a = panel.audit(2021)
    assert a["n_preseason_proxy_reads"] == 2
    assert a["max_feature_cutoff"] == -1


@needs_db
def test_batch1_features_reproduce_bit_for_bit(panel):
    """`build_factor2_features(use_batch2=False)` must be the batch-1 frame
    exactly -- otherwise batch 2 silently invalidates batch 1's table."""
    for season in (2016, 2022):
        u = universe_for(panel, season, "RB")
        a = build_factor_features(panel, u, season, use_proxy=False)
        b = build_factor2_features(panel, u, season, use_proxy=False,
                                   use_batch2=False)
        pd.testing.assert_frame_equal(a, b)


@needs_db
def test_every_roster_status_code_is_classified(panel):
    """A status code nobody has classified would silently fall to
    'not under contract', i.e. would be read as a departure."""
    unk = D.unknown_status_codes(panel._roster)
    assert unk.empty, f"unclassified roster status codes: {unk.to_dict()}"


@needs_db
def test_under_contract_and_available_are_nested(panel):
    r = panel._roster
    assert (r.loc[r["available"] == 1, "under_contract"] == 1).all()


def test_ahead_of_me_is_player_level_and_ordered():
    """Two players on the same club must be able to get different values, and a
    player with more prior volume must see no MORE vacated opportunity above him
    than a team-mate with less."""
    prev = pd.DataFrame({
        "player_id": ["a", "b", "c"],
        "team": ["X", "X", "X"],
        "targets": [100.0, 60.0, 20.0],
        "carries": [0.0, 0.0, 0.0],
    })
    tt = pd.DataFrame({"team": ["X"], "team_targets": [200.0],
                       "team_carries": [100.0]})
    # 'a' (the 100-target player) departs
    stays = np.array([False, True, True])
    s = _ahead_of_me(prev, tt, stays, "targets", "team_targets")
    assert s["a"] == pytest.approx(0.0)          # nobody above the top player
    assert s["b"] == pytest.approx(0.5)          # a's 100 of the club's 200
    assert s["c"] == pytest.approx(0.5)
    assert s["b"] >= s["a"]

    # nobody departs -> nothing opened for anyone
    s2 = _ahead_of_me(prev, tt, np.array([True, True, True]), "targets",
                      "team_targets")
    assert set(np.round(s2.to_numpy(), 9)) == {0.0}


def test_ahead_of_me_ties_get_the_same_value():
    prev = pd.DataFrame({
        "player_id": ["top", "t1", "t2"],
        "team": ["X", "X", "X"],
        "targets": [80.0, 40.0, 40.0],
        "carries": [0.0, 0.0, 0.0],
    })
    tt = pd.DataFrame({"team": ["X"], "team_targets": [160.0],
                       "team_carries": [1.0]})
    s = _ahead_of_me(prev, tt, np.array([False, True, True]), "targets",
                     "team_targets")
    assert s["t1"] == pytest.approx(s["t2"])


@needs_db
def test_batch2_block_produces_the_declared_columns(panel):
    u = universe_for(panel, 2022, "RB")
    f = build_factor2_features(panel, u, 2022, use_batch2=True)
    for c in ("vac2_tshare", "vac2_cshare", "vac3_tshare", "vac3_cshare",
              "vac_ahead_t", "vac_ahead_c", "moved_club", "move_known",
              "new_oc", "oc_known", "vac_club_known"):
        assert c in f.columns, c
        assert np.isfinite(f[c].to_numpy(dtype=float)).all(), f"{c} has non-finite"
    # departure share can never exceed absence share: leaving the club implies
    # being unavailable for it
    assert (f["vac2_tshare"] <= f["vac3_tshare"] + 1e-9).all()
    assert (f["vac2_cshare"] <= f["vac3_cshare"] + 1e-9).all()


@needs_db
def test_new_oc_is_zero_wherever_it_is_unknown(panel):
    """`new_oc=1` with `oc_known=0` would be a claim about a club we have no
    coordinator record for -- exactly the false-reason failure the insight rule
    in the pre-commitment exists to prevent."""
    for season in (2016, 2020, 2024):
        u = universe_for(panel, season, "WR")
        f = build_factor2_features(panel, u, season, use_batch2=True)
        assert not ((f["oc_known"] == 0) & (f["new_oc"] != 0)).any()
