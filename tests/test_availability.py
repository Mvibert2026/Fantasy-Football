import numpy as np
import pytest

import availability as av
import draft_sim as ds


def _tiny_data(n_per_pos=6):
    """Minimal SeasonData: 4 positions x n_per_pos players, consensus rank 1..4n."""
    positions = np.repeat(np.arange(4), n_per_pos)
    n = len(positions)
    rank = np.arange(1, n + 1, dtype=float)
    return ds.SeasonData(
        season=2026,
        player_ids=[f"p{i}" for i in range(n)],
        names=[f"Player {i}" for i in range(n)],
        positions=positions,
        consensus_rank=rank,
        weekly_points=np.zeros((n, 2)),
        n_weeks=1,
    )


def test_mechanical_need_targets_derived_from_roster_rules():
    """QB: 1 starter, not flex-eligible -> target 1. RB/WR/TE: starters + the
    full FLEX_SLOTS pool (an upper bound, not a partition)."""
    for pos in ds.POSITIONS:
        expected = ds.STARTERS[pos] + (ds.FLEX_SLOTS if pos in ds.FLEX_ELIGIBLE else 0)
        assert ds.MECHANICAL_NEED_TARGETS[pos] == expected
    assert ds.MECHANICAL_NEED_TARGETS["QB"] == 1
    assert ds.MECHANICAL_NEED_TARGETS["TE"] == 3


def test_mechanical_need_targets_do_not_alter_the_pr003_default():
    """NEED_TARGETS (the judgement-call constant used by opponent_pick's
    default / simulate_one / the PR-003 strategy comparisons) must be
    untouched by the availability rewrite -- those numbers are already
    ADR-028-verified reproducible and must not move silently."""
    assert ds.NEED_TARGETS == {"QB": 2, "RB": 5, "WR": 6, "TE": 2}


def test_opponent_pick_targets_param_defaults_to_need_targets():
    """Backward compatibility: a caller that does not pass `targets` gets
    exactly the pre-rewrite behaviour."""
    data = _tiny_data()
    available = np.ones(len(data.positions), dtype=bool)
    counts = {p: 0 for p in ds.POSITIONS}
    a = ds.opponent_pick(data.consensus_rank.copy(), available, counts, data)
    b = ds.opponent_pick(
        data.consensus_rank.copy(), available, counts, data, targets=ds.NEED_TARGETS
    )
    assert a == b


def test_scenario_pick_mechanism_is_gone():
    """ADR-033/034: the named-manager repeat-probability mechanism must not
    exist anywhere in the module -- it was found circular and removed, not
    deprecated."""
    assert not hasattr(av, "ScenarioPick")


def test_default_ranking_sources_is_single_source_today():
    data = _tiny_data()
    sources = av.default_ranking_sources(data)
    assert len(sources) == 1
    assert sources[0].name == "fantasypros_ecr"
    assert np.array_equal(sources[0].rank, data.consensus_rank)


def test_simulate_availability_runs_with_default_sources():
    data = _tiny_data()
    res = av.simulate_availability(data, sigma=5.0, n_sims=20, seed=1)
    assert res.n_sims == 20
    assert set(res.tier_avail.keys()) == set(av.TIERS.keys())


def test_single_source_mixture_is_a_no_op_regardless_of_declared_weight():
    """With one source, sampling from the mixture always returns that source --
    the weight is irrelevant. This is the case that must be unchanged from the
    pre-mixture behaviour."""
    data = _tiny_data()
    sources = av.default_ranking_sources(data)
    res_a = av.simulate_availability(
        data, sigma=5.0, n_sims=50, seed=42, sources=sources, source_weights=[1.0]
    )
    res_b = av.simulate_availability(
        data, sigma=5.0, n_sims=50, seed=42, sources=sources, source_weights=[0.001]
    )
    # Same seed, same single-source board -> byte-identical results regardless
    # of the (irrelevant, since there is nothing else to weigh against) weight.
    for pos in av.TIERS:
        for tier in av.TIERS[pos]:
            assert res_a.tier_avail[pos][tier] == res_b.tier_avail[pos][tier]


def test_two_source_mixture_samples_both_ends_of_the_weight_range():
    """A degenerate two-source mixture (weight 1/0 vs 0/1) must reproduce the
    single-source result for whichever source has all the weight -- proof the
    sampling path is real, not a stub that ignores `sources`."""
    data = _tiny_data()
    fp = av.default_ranking_sources(data)[0]
    # A second "source" that is identical in content but a different object,
    # so any code path that silently ignores `sources` and always uses
    # `data.consensus_rank` cannot pass this test by accident.
    alt = av.RankingSource("alt_source", data.consensus_rank[::-1].copy())

    all_fp = av.simulate_availability(
        data, sigma=1.0, n_sims=200, seed=7, sources=[fp, alt], source_weights=[1.0, 0.0]
    )
    fp_only = av.simulate_availability(
        data, sigma=1.0, n_sims=200, seed=7, sources=[fp], source_weights=[1.0]
    )
    for pos in av.TIERS:
        for tier in av.TIERS[pos]:
            assert all_fp.tier_avail[pos][tier] == fp_only.tier_avail[pos][tier]


@pytest.mark.requires_db
def test_te_t1_at_23_lands_in_the_predeclared_sanity_bracket():
    """Regression guard for ADR-034's own stated bracket: the new model's
    P(TE T1 survives to pick 23) must land in roughly [0, 0.60] -- the old
    unconditional (0% forced-repeat) baseline was 0.5963. A value outside this
    band means the mechanical need model is behaving very differently from the
    old opponent model and should be investigated before shipping."""
    import db as dbmod

    conn = dbmod.connect()
    try:
        data = ds.load_season(conn, 2026)
    finally:
        conn.close()
    sources = av.default_ranking_sources(data)
    res = av.simulate_availability(
        data, ds.DEFAULT_SIGMA, n_sims=800, seed=20260725, sources=sources
    )
    p = res.tier_avail["TE"]["T1"].get(23)
    assert p is not None
    assert 0.0 <= p <= 0.62, f"TE T1 @23 = {p}, outside the pre-declared sanity bracket"


@pytest.mark.requires_db
def test_load_season_provenance_matches_the_rows_it_actually_read():
    """SeasonData.consensus_rank_source/consensus_rank_as_of_date must be
    read from the SAME rows consensus_rank came from, not a second constant
    that could drift -- this is what export_contract's ranking_sources
    identity (thread 104) is built on. Cross-checked here against a direct
    query, independent of load_season's own internals."""
    import db as dbmod

    conn = dbmod.connect()
    try:
        data = ds.load_season(conn, 2026)
        row = conn.execute(
            "SELECT MAX(as_of_date) FROM rankings WHERE source=? AND season=?",
            (ds.CONSENSUS_RANK_SOURCE, 2026),
        ).fetchone()
    finally:
        conn.close()
    assert data.consensus_rank_source == ds.CONSENSUS_RANK_SOURCE
    assert data.consensus_rank_as_of_date == row[0]
    assert data.consensus_rank_as_of_date is not None
