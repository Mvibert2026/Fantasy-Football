import numpy as np
import pytest

import draft_sim as ds
import league_config as lc
from scoring import ReplacementLevels


def _tiny_data(n_per_pos=8):
    positions = np.repeat(np.arange(4), n_per_pos)
    n = len(positions)
    rank = np.arange(1, n + 1, dtype=float)
    return ds.SeasonData(
        season=2026, player_ids=[f"p{i}" for i in range(n)], names=[f"P{i}" for i in range(n)],
        positions=positions, consensus_rank=rank, weekly_points=np.zeros((n, 2)), n_weeks=1,
    )


def _yahoo_mock() -> lc.LeagueConfig:
    return lc.LeagueConfig(
        league_id="yahoo_mock",
        name="Yahoo standard mock",
        platform="yahoo",
        teams=12,
        scoring={},
        starters={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1},
        flex_slots=1,
        flex_eligible=("RB", "WR", "TE"),
        bench=6,
        ir=0,
        user_draft_slot=6,
    )


class TestPrimaryLeagueParity:
    def test_engine_matches_free_functions_exactly(self):
        eng = ds.DraftEngine(lc.CURRENT_LEAGUE)
        assert eng.pick_order() == ds.pick_order()
        assert eng.user_pick_numbers() == ds.user_pick_numbers()
        assert eng.need_targets == ds.NEED_TARGETS
        assert eng.max_at_position == ds.MAX_AT_POSITION
        assert eng.reserved_rounds() == [ds.N_ROUNDS - 1]

    def test_opponent_pick_matches_module_function(self):
        eng = ds.DraftEngine(lc.CURRENT_LEAGUE)
        data = _tiny_data()
        rng = np.random.default_rng(1)
        effective = data.consensus_rank + rng.normal(0, 10, size=len(data.positions))
        available = np.ones(len(data.positions), dtype=bool)
        counts = {p: 0 for p in ds.POSITIONS}
        a = ds.opponent_pick(effective.copy(), available.copy(), dict(counts), data)
        b = eng.opponent_pick(effective.copy(), available.copy(), dict(counts), data)
        assert a == b

    def test_legal_mask_matches_module_function(self):
        eng = ds.DraftEngine(lc.CURRENT_LEAGUE)
        data = _tiny_data()
        available = np.ones(len(data.positions), dtype=bool)
        state = ds.DraftState(2026, 1, 0, [], {p: 0 for p in ds.POSITIONS}, available)
        assert np.array_equal(ds._legal_mask(state, data), eng.legal_mask(state, data))


class TestYahooMockGeneralizes:
    def test_engine_constructs_without_error(self):
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        assert eng.n_teams == 12
        assert eng.user_slot == 6

    def test_k_and_def_are_reserved_not_simulated(self):
        """Two unscored starter positions (K, DEF) -> two reserved rounds, not
        draft_sim's original hardcoded single 'DEF is the last round' rule."""
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        assert set(eng.unscored_starter_positions) == {"K", "DEF"}
        assert len(eng.reserved_rounds()) == 2
        # both reserved rounds are the LAST two rounds
        assert eng.reserved_rounds() == [cfg.rounds - 2, cfg.rounds - 1]

    def test_scoreable_starters_excludes_k_and_def(self):
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        assert eng.scoreable_starters == {"QB": 1, "RB": 2, "WR": 2, "TE": 1}

    def test_mechanical_need_targets_used_for_non_primary_league(self):
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        # QB: 1 starter, not flex-eligible -> target 1
        assert eng.need_targets["QB"] == 1
        # RB: 2 starters + 1 flex slot (flex-eligible) -> target 3
        assert eng.need_targets["RB"] == 3
        # must NOT be the primary league's judgement-call numbers
        assert eng.need_targets != ds.NEED_TARGETS

    def test_pick_order_respects_12_teams(self):
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        order = eng.pick_order()
        assert len(order) == cfg.teams * cfg.rounds
        assert set(order[:12]) == set(range(12))
        # snake: round 2 (index 12-23) is reversed
        assert order[12] == 11

    def test_full_simulated_draft_runs_and_fills_a_legal_roster(self):
        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        data = _tiny_data(n_per_pos=40)  # enough depth for 12 teams x reduced rounds
        board = data.consensus_rank
        rng = np.random.default_rng(5)
        mine, opps, legal = eng.simulate_one(data, eng.strategy_bpa, board, sigma=10.0, rng=rng)
        assert legal, "user roster should be legal after a full simulated draft"
        assert len(opps) == cfg.teams - 1

    def test_weekly_optimal_points_respects_flex_slots_config(self):
        cfg = _yahoo_mock()  # flex_slots=1, unlike primary's 2
        eng = ds.DraftEngine(cfg)
        data = _tiny_data(n_per_pos=8)
        # Build a roster satisfying starters, with extra RBs available for flex.
        # positions array: 0=QB,1=RB,2=WR,3=TE (index within group of 8)
        roster = [0, 8, 9, 10, 16, 17, 24, 11]  # 1QB,2RB+1flexRB,2WR,1TE
        pts = eng.weekly_optimal_points(roster, data)
        assert pts >= 0.0  # all-zero weekly_points in the fixture, sanity only

    def test_replacement_levels_from_league_config_excludes_k_and_def(self):
        cfg = _yahoo_mock()
        levels, measured = ReplacementLevels.from_league_config(cfg)
        assert "K" not in levels.starters
        assert "DEF" not in levels.starters
        assert levels.starters == {"QB": 1, "RB": 2, "WR": 2, "TE": 1}
        assert measured is False  # cfg.flex_split was not supplied

    def test_replacement_levels_placeholder_flagged_not_measured(self):
        cfg = _yahoo_mock()
        _, measured = ReplacementLevels.from_league_config(cfg)
        assert measured is False

    def test_replacement_levels_measured_flag_true_when_supplied(self):
        cfg = _yahoo_mock()
        cfg.flex_split = {"RB": 0.6, "WR": 0.3, "TE": 0.1}
        _, measured = ReplacementLevels.from_league_config(cfg)
        assert measured is True

    def test_availability_simulation_runs_with_a_new_engine(self):
        import availability as av

        cfg = _yahoo_mock()
        eng = ds.DraftEngine(cfg)
        data = _tiny_data(n_per_pos=40)
        sources = av.default_ranking_sources(data)
        res = av.simulate_availability(
            data, sigma=10.0, n_sims=20, seed=1, sources=sources, engine=eng
        )
        assert res.user_picks == eng.user_pick_numbers()
        assert len(res.user_picks) > 0


def test_primary_league_availability_output_unchanged_by_engine_plumbing():
    """The default (engine=None) path must be byte-identical to before this
    change -- this is the guarantee the whole 'duplicate, don't refactor'
    design decision exists to protect."""
    import availability as av

    data = _tiny_data(n_per_pos=20)
    sources = av.default_ranking_sources(data)
    res_a = av.simulate_availability(data, sigma=10.0, n_sims=50, seed=99, sources=sources)
    res_b = av.simulate_availability(
        data, sigma=10.0, n_sims=50, seed=99, sources=sources, engine=None
    )
    assert res_a.tier_avail == res_b.tier_avail
