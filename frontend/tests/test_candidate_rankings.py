import pytest

import candidate_rankings as cr


def test_vbd_baseline_ranking_orders_by_descending_value():
    values = {"A": 10.0, "B": 30.0, "C": 20.0}
    ranking = cr.vbd_baseline_ranking(values)
    assert ranking == {"B": 1, "C": 2, "A": 3}


def test_hero_rb_boosts_only_top_n_rbs_and_leaves_others_untouched():
    values = {"RB1": 100.0, "RB2": 90.0, "RB3": 10.0, "WR1": 95.0}
    positions = {"RB1": "RB", "RB2": "RB", "RB3": "RB", "WR1": "WR"}
    ranking, boosted = cr.hero_rb_ranking(values, positions, top_n=2, bonus=0.30)
    assert set(boosted) == {"RB1", "RB2"}
    # RB1: 100*1.3=130, RB2: 90*1.3=117, WR1: 95 (untouched), RB3: 10 (untouched, not in top_n)
    assert ranking == {"RB1": 1, "RB2": 2, "WR1": 3, "RB3": 4}


def test_hero_rb_boost_can_change_overall_order_relative_to_other_positions():
    # WR1 (95) would beat RB2 (90) unboosted, but RB2*1.3=117 > 95 after boost.
    values = {"RB2": 90.0, "WR1": 95.0}
    positions = {"RB2": "RB", "WR1": "WR"}
    ranking, _ = cr.hero_rb_ranking(values, positions, top_n=24, bonus=0.30)
    assert ranking["RB2"] < ranking["WR1"]  # RB2 now ranks ahead


def test_rerank_with_forced_positions_places_forced_players_exactly():
    base = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
    forced = {"E": 1, "C": 5}
    result = cr._rerank_with_forced_positions(base, forced)
    assert result["E"] == 1
    assert result["C"] == 5
    # remaining players (A, B, D) keep relative order from base, filling ranks 2,3,4
    remaining_order = sorted((pid for pid in result if pid not in forced), key=lambda pid: result[pid])
    assert remaining_order == ["A", "B", "D"]


def test_rerank_with_forced_positions_rejects_duplicate_target_ranks():
    base = {"A": 1, "B": 2}
    with pytest.raises(ValueError):
        cr._rerank_with_forced_positions(base, {"A": 1, "B": 1})


def test_elite_te_ranking_forces_named_players_to_target_ranks():
    base = {"TE1": 5, "TE2": 6, "TE3": 7, "RB1": 1, "WR1": 2, "WR2": 3, "WR3": 4}
    positions = {"TE1": "TE", "TE2": "TE", "TE3": "TE", "RB1": "RB", "WR1": "WR", "WR2": "WR", "WR3": "WR"}
    result = cr.elite_te_ranking(base, ["TE1", "TE2"], [1, 2], positions, bottom_n=1)
    assert result["TE1"] == 1
    assert result["TE2"] == 2


def test_elite_te_ranking_demotes_best_non_elite_tes_to_the_bottom():
    n = 10
    base = {f"P{i}": i for i in range(1, n + 1)}  # P1..P10, rank == number
    positions = {f"P{i}": ("TE" if i in (3, 4, 5) else "WR") for i in range(1, n + 1)}
    # elite = P1, P2 (currently WR-ranked slots, doesn't matter for this synthetic test);
    # non-elite TEs are P3, P4, P5 -- best-ranked of those (by base rank) is P3.
    result = cr.elite_te_ranking(base, ["P1"], [1], positions, bottom_n=2)
    # best 2 non-elite TEs (P3, P4) should be pushed to the worst 2 overall ranks (9, 10)
    assert result["P3"] in (9, 10)
    assert result["P4"] in (9, 10)
    # P5 (worst-ranked non-elite TE) wasn't targeted for demotion, so it must NOT land in the
    # demoted band -- it just shifts up to fill the gap left by P3/P4 moving out (5 -> 3, since
    # two players ahead of it in the base order were removed from the "remaining" sequence).
    assert result["P5"] not in (9, 10)
    assert result["P5"] == 3


def test_elite_te_ranking_preserves_relative_order_of_untouched_positions():
    base = {"TE1": 3, "TE2": 4, "RB1": 1, "WR1": 2}
    positions = {"TE1": "TE", "TE2": "TE", "RB1": "RB", "WR1": "WR"}
    result = cr.elite_te_ranking(base, ["TE1"], [1], positions, bottom_n=1)
    assert set(result.keys()) == set(base.keys())
    # RB1 and WR1 were never forced or TE-demoted; their relative order to each
    # other must be unchanged even though their absolute rank numbers can shift
    # to make room for the forced TE1.
    assert result["RB1"] < result["WR1"]
