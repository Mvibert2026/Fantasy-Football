"""Factor batch 7 — guardrail tests for the RB usage/efficiency feature blocks.

Same shape as `test_factor_batch2_features.py` and `test_factor_batch3_features.py`:
these do not check that a factor WORKS, they check that the machinery cannot
quietly stop being what the pre-commitment says it is.

The one that matters is `test_no_season_n_read_anywhere`. Batch 7's whole claim
to a clean look-ahead audit is that not one of its six blocks reads season N —
unlike batches 1 and 2, whose vacancy and coordinator blocks did. That is
asserted here rather than believed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experiments.bottomup.components.pos_data import (
    HOLDOUT_SEASON, HoldoutViolation, build_panel, universe_for,
)
from experiments.bottomup.components.pos_features import build_features
from experiments.bottomup.factors import factor_features7 as F7

ALL_BLOCKS = tuple(F7._BLOCKS)


@pytest.fixture(scope="module")
def panel():
    return build_panel()


@pytest.fixture(scope="module")
def src():
    return F7.sources()


# ----------------------------------------------------------------- the holdout
def test_no_source_contains_the_sealed_holdout(src):
    for name in ("rz", "i5", "yac", "snaps", "half"):
        df = getattr(src, name)
        assert len(df), f"batch-7 source {name} is empty"
        assert int(df["season"].max()) < HOLDOUT_SEASON, name


@pytest.mark.parametrize("accessor", ["rz_before", "i5_before", "yac_before",
                                      "snaps_before", "half_before"])
def test_every_accessor_refuses_the_holdout(src, panel, accessor):
    with pytest.raises(HoldoutViolation):
        getattr(src, accessor)(HOLDOUT_SEASON, panel)


@pytest.mark.parametrize("accessor", ["rz_before", "i5_before", "yac_before",
                                      "snaps_before", "half_before"])
def test_every_accessor_honours_its_cutoff(src, panel, accessor):
    out = getattr(src, accessor)(2018, panel)
    if len(out):
        assert int(out["season"].max()) <= 2018


# ------------------------------------------------------------- the look-ahead
@pytest.mark.parametrize("target", [2018, 2021, 2024])
def test_no_season_n_read_anywhere(panel, src, target):
    """THE ASSERTION BATCH 7'S AUDIT RESTS ON. Every block, every season."""
    panel.reset_audit()
    u = universe_for(panel, target, "RB")
    F7.build_factor7_features(panel, u, target, blocks=ALL_BLOCKS, position="RB")
    a = panel.audit(target)
    assert a["n_preseason_proxy_reads"] == 0
    assert a["max_feature_cutoff"] < target
    assert a["max_outcome_season"] < target
    assert a["n_outcome_reads_at_target"] == 0


def test_primary_is_exactly_build_features(panel):
    """`blocks=()` must be `pos_features.build_features` and nothing else, or the
    batch-7 primary is not the primary every other batch used."""
    u = universe_for(panel, 2021, "RB")
    a = F7.build_factor7_features(panel, u, 2021, blocks=())
    b = build_features(panel, u, 2021)
    assert list(a.columns) == list(b.columns)
    pd.testing.assert_frame_equal(a, b)


def test_a_block_adds_only_its_own_columns(panel):
    u = universe_for(panel, 2021, "RB")
    base = set(F7.build_factor7_features(panel, u, 2021, blocks=()).columns)
    only_i5 = set(F7.build_factor7_features(panel, u, 2021, blocks=("i5",),
                                            position="RB").columns)
    assert only_i5 - base == {"i5_conv_w", "i5_conv_placebo_w", "i5_known"}


# --------------------------------------------------- the coverage-flag finding
def test_rzsnap_known_is_a_time_dummy_among_veterans(panel):
    """Locked as a regression test so the batch-7 result §1(2) cannot be
    quietly re-derived. `participation` starts 2016 and the training window
    starts 2012, so among VETERANS the flag is a pre-2017/post-2017 indicator —
    which is why it beat both treatments it was registered to control."""
    def vet_known(target):
        u = universe_for(panel, target, "RB")
        f = F7.build_factor7_features(panel, u, target, blocks=("rz",),
                                      position="RB")
        return float(f.loc[f["entry"] == "veteran", "rzsnap_known"].mean())

    assert vet_known(2014) == 0.0
    assert vet_known(2016) == 0.0
    assert vet_known(2019) == 1.0
    assert vet_known(2024) == 1.0


def test_i5_and_yac_flags_are_not_time_dummies(panel):
    """The contrast that makes the finding a finding: `pbp` (2009) and weekly
    YAC (2006) both cover the whole training window, so their coverage flags
    vary by PLAYER and not by era."""
    for target in (2014, 2024):
        u = universe_for(panel, target, "RB")
        f = F7.build_factor7_features(panel, u, target, blocks=("i5", "yac"),
                                      position="RB")
        vet = f[f["entry"] == "veteran"]
        for col in ("i5_known", "yac_known"):
            assert 0.5 < float(vet[col].mean()) < 1.0, (target, col)


# ------------------------------------------------- the rate-covariate hook
def test_rate_covariate_hook_is_not_a_no_op(panel):
    """MECHANICS ONLY, and deliberately not a claim about any factor. Two of
    batch 7's arms insert through `RateCovariateRB` rather than through
    `volume_cols`; if that path silently did nothing, those arms would be
    non-tests reported as nulls. Fed a covariate that MUST matter — the shrunk
    rate's own lagged inputs — the hook has to move the projection."""
    from experiments.bottomup.factors.run_factors7 import RateCovariateRB
    from experiments.bottomup.components.pos_features import outcome_components

    fs, os_ = [], []
    for s in range(2012, 2020):
        u = universe_for(panel, s, "RB")
        fs.append(F7.build_factor7_features(panel, u, s, blocks=("yac",),
                                            position="RB"))
        os_.append(outcome_components(panel, u, s))
    tf, to = pd.concat(fs, ignore_index=True), pd.concat(os_, ignore_index=True)

    plain = RateCovariateRB(position="RB", avail_arm="A").fit(tf, to)
    hooked = RateCovariateRB(position="RB", avail_arm="A",
                             rate_cov=("ypr", "ypr_num")).fit(tf, to)
    assert hooked.cov_n > 0, "the covariate was never fitted"
    assert abs(hooked.cov_beta) > 0, "the covariate slope is exactly zero"

    u = universe_for(panel, 2020, "RB")
    f = F7.build_factor7_features(panel, u, 2020, blocks=("yac",), position="RB")
    a = plain.predict(f)["proj_rec_yards"].to_numpy(dtype=float)
    b = hooked.predict(f)["proj_rec_yards"].to_numpy(dtype=float)
    assert not np.allclose(a, b), "the hook did not reach the projection"
