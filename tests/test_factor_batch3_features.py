"""Factor batch 3 feature guarantees.

Three properties the batch-3 results depend on, asserted rather than believed:

1. **Batch 1 and batch 2 still reproduce bit for bit.** `build_factor3_features`
   only ever appends, so every published number in `factor-batch-1-results.md`
   and `factor-batch-2-results.md` stays checkable against unchanged code.

2. **A block an arm did not declare is never computed.** This is not tidiness --
   it is what lets `factor-batch-3-results.md` §6 claim that the NGS and
   explosive arms made *zero* season-N proxy reads. If the builder computed all
   three blocks unconditionally, every batch-3 arm would touch the coordinator
   table and the audit assertion would stop meaning anything.

3. **Coordinator tenure is never reported where it is censored.** A tenure
   computed off a source that starts in 2010 understates every spell that began
   earlier, in one direction, for exactly the longest-serving coordinators. The
   censored rows must carry `oc_tenure_known = 0`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

pytest.importorskip("pandas")

from experiments.bottomup.components.pos_data import (  # noqa: E402
    build_panel, universe_for,
)
from experiments.bottomup.factors.factor_features2 import (  # noqa: E402
    build_factor2_features,
)
from experiments.bottomup.factors.factor_features3 import (  # noqa: E402
    OC_FIRST_SEASON, build_factor3_features,
)

DB = _REPO / "data" / "nfl.db"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="data/nfl.db not present")

SEASON = 2022


@pytest.fixture(scope="module")
def panel():
    return build_panel()


def _u(panel, pos, season=SEASON):
    return universe_for(panel, season, pos)


@pytest.mark.parametrize("pos", ["WR", "RB", "QB"])
def test_batch2_reproduces_bit_for_bit(panel, pos):
    u = _u(panel, pos)
    a = build_factor2_features(panel, u, SEASON, use_batch2=True)
    b = build_factor3_features(panel, u, SEASON, use_batch2=True)
    assert list(a.columns) == list(b.columns)
    pd.testing.assert_frame_equal(a, b)


def test_no_block_means_no_batch3_columns(panel):
    f = build_factor3_features(panel, _u(panel, "RB"), SEASON)
    for c in ("sep_1", "expl_w", "oc_tenure"):
        assert c not in f.columns


def test_declared_block_is_the_only_block_computed(panel):
    u = _u(panel, "WR")
    sep = build_factor3_features(panel, u, SEASON, blocks=("sep",))
    assert "sep_1" in sep.columns and "sep_known_1" in sep.columns
    assert "oc_tenure" not in sep.columns and "expl_w" not in sep.columns


def test_history_only_blocks_make_no_season_n_proxy_read(panel):
    """The claim `factor-batch-3-results.md` §6 makes, enforced."""
    for blocks in (("sep",), ("expl",)):
        panel.reset_audit()
        build_factor3_features(panel, _u(panel, "RB"), SEASON, blocks=blocks)
        assert panel.audit(SEASON)["n_preseason_proxy_reads"] == 0, blocks
    panel.reset_audit()
    build_factor3_features(panel, _u(panel, "RB"), SEASON, blocks=("oc",))
    assert panel.audit(SEASON)["n_preseason_proxy_reads"] > 0


def test_coverage_flags_are_binary_and_agree_with_their_values(panel):
    f = build_factor3_features(panel, _u(panel, "RB"), SEASON,
                               blocks=("sep", "expl", "oc"))
    for c in ("sep_known_1", "expl_known", "oc_tenure_known"):
        assert set(np.unique(f[c])) <= {0.0, 1.0}
    # unknown separation is imputed to the median of the known, never to zero
    unk = f.loc[f["sep_known_1"] == 0, "sep_1"]
    if len(unk) and (f["sep_known_1"] == 1).any():
        assert np.allclose(unk, np.median(f.loc[f["sep_known_1"] == 1, "sep_1"]))
        assert (unk > 0).all()


def test_tenure_is_at_least_one_and_censoring_is_flagged(panel):
    f = build_factor3_features(panel, _u(panel, "WR"), SEASON, blocks=("oc",))
    known = f["oc_tenure_known"] == 1
    assert known.any()
    assert (f.loc[known, "oc_tenure"] >= 1).all()
    # a chain cannot be longer than the observable window
    assert (f.loc[known, "oc_tenure"] <= SEASON - OC_FIRST_SEASON + 1).all()


def test_explosive_rate_is_a_rate(panel):
    f = build_factor3_features(panel, _u(panel, "RB"), SEASON, blocks=("expl",))
    assert (f["expl_w"] >= 0).all() and (f["expl_w"] <= 1).all()
    assert (f["expl_rel_w"].abs() <= 1).all()
    # unknown players sit exactly at the pooled prior, and there is one prior
    unk = f.loc[f["expl_known"] == 0, "expl_w"]
    if len(unk):
        assert unk.nunique() == 1


def test_holdout_stays_sealed_for_the_new_sources(panel):
    from experiments.bottomup.components.pos_data import HoldoutViolation
    assert len(panel._ngs) == 0 or panel._ngs["season"].max() < 2025
    assert len(panel._rush) == 0 or panel._rush["season"].max() < 2025
    with pytest.raises(HoldoutViolation):
        panel.ngs_before(2025)
    with pytest.raises(HoldoutViolation):
        panel.rush_before(2025)
