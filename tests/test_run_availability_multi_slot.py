"""
FR-057 part 1: availability must recompute for any draft slot, floor version
(run the existing simulation for every slot, not the browser recompute --
that is part 2 and explicitly out of scope here).

WRITTEN BEFORE the run_availability.py sweep it checks, per the project's
sanity-check-first rule. The multi-slot merge in run_availability.py relies
on one structural claim: for a fixed team count and round count, a pick
number belongs to exactly one draft slot, so sweeping every slot 1..teams
and merging player_avail/tier_avail/best_avail_dist into one combined
per-sigma structure can never have two slots write the same (subject, pick)
cell. Every test here either proves that claim directly or checks a
consequence of it. If the merge ever DOES collide, these are the tests that
should catch it before it reaches by_player/by_tier silently overwriting
data no one asked to overwrite.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import availability as av
import db as dbmod
import draft_sim as ds
import league_config as lc
import run_availability as ra


@pytest.fixture(scope="module")
def season_data():
    conn = dbmod.connect()
    try:
        return ds.load_season(conn, ra.SEASON)
    finally:
        conn.close()


# --------------------------------------------------------------- #1 (critical)
def test_no_two_slots_share_a_tracked_pick_number(season_data):
    """THE structural claim the whole merge depends on: sweep every slot of
    the primary league and confirm the union of tracked pick numbers is a
    disjoint partition, not an overlapping set. A cheap n_sims is fine here
    -- this checks WHICH keys get written, not the values in them."""
    cfg = lc.CURRENT_LEAGUE
    sources = av.default_ranking_sources(season_data)
    seen: set[int] = set()
    for slot in range(1, cfg.teams + 1):
        engine = ra._engine_for_slot(cfg, slot)
        r = av.simulate_availability(season_data, 10.0, 20, 1, sources=sources, engine=engine)
        tracked_picks = {p for picks in r.player_avail.values() for p in picks}
        overlap = tracked_picks & seen
        assert not overlap, f"slot {slot} re-tracked pick(s) {overlap} another slot already owns"
        seen |= tracked_picks


def test_full_sweep_covers_every_overall_pick_number(season_data):
    """Union across all slots must reach every overall pick number 1..teams*
    rounds. Reserved-round (DEF) picks are still KEYS in the result (unchanged
    pre-existing single-slot behavior -- avail_counts is seeded with every
    user pick before the sim loop runs) but their VALUE is always 0.0, since
    that round is skipped for every team, not just the user -- checked
    separately below rather than folded into this coverage count."""
    cfg = lc.CURRENT_LEAGUE
    sources = av.default_ranking_sources(season_data)
    all_picks: set[int] = set()
    for slot in range(1, cfg.teams + 1):
        engine = ra._engine_for_slot(cfg, slot)
        r = av.simulate_availability(season_data, 10.0, 20, 1, sources=sources, engine=engine)
        all_picks |= {p for picks in r.player_avail.values() for p in picks}
    assert all_picks == set(range(1, cfg.teams * cfg.rounds + 1))


def test_reserved_def_round_picks_are_always_zero(season_data):
    """The final round (DEF, ADR-039) is skipped for every team in every
    slot's simulation -- its pick numbers are present as keys (see test
    above) but never incremented, in every slot, not only the founder's."""
    cfg = lc.CURRENT_LEAGUE
    sources = av.default_ranking_sources(season_data)
    reserved_round = cfg.rounds - 1  # 0-indexed, matches draft_sim reserved_rounds()
    reserved_picks = {
        reserved_round * cfg.teams + i + 1 for i in range(cfg.teams)
    }
    for slot in range(1, cfg.teams + 1):
        engine = ra._engine_for_slot(cfg, slot)
        r = av.simulate_availability(season_data, 10.0, 20, 1, sources=sources, engine=engine)
        for i, picks in r.player_avail.items():
            for pk in reserved_picks & set(picks):
                assert picks[pk] == 0.0, f"slot {slot} pick {pk} (reserved round) should be 0.0"


# --------------------------------------------------------------- #2
def test_own_slot_uses_legacy_engine_none_path_for_primary():
    """The founder's own slot must keep engine=None for the primary league --
    the whole point is that this change cannot move a number he has already
    seen. Any other slot must use a real DraftEngine."""
    cfg = lc.CURRENT_LEAGUE
    assert ra._engine_for_slot(cfg, cfg.user_draft_slot) is None
    other_slot = 1 if cfg.user_draft_slot != 1 else 2
    other = ra._engine_for_slot(cfg, other_slot)
    assert isinstance(other, ds.DraftEngine)
    assert other.user_slot == other_slot


def test_merge_helpers_are_pure_union_not_overwrite():
    """Unit-level check of the three merge helpers directly, independent of
    the simulator: disjoint inputs must produce their union; the helpers
    must never require identical keys to combine cleanly."""
    dst = {1: {3: 0.5}}
    ra._merge_player(dst, {1: {18: 0.4}, 2: {3: 0.9}})
    assert dst == {1: {3: 0.5, 18: 0.4}, 2: {3: 0.9}}

    tdst = {"RB": {"T1": {3: 0.9}}}
    ra._merge_tier(tdst, {"RB": {"T1": {18: 0.8}}, "WR": {"T2": {3: 0.7}}})
    assert tdst == {"RB": {"T1": {3: 0.9, 18: 0.8}}, "WR": {"T2": {3: 0.7}}}

    bdst = {"RB": {3: [1, 2]}}
    ra._merge_best(bdst, {"RB": {18: [3, 4]}})
    assert bdst == {"RB": {3: [1, 2], 18: [3, 4]}}


# --------------------------------------------------------------- #3
def test_picks_by_slot_partition_matches_pick_order(season_data):
    """_all_slot_pick_numbers (export_contract.py) must produce, for each
    slot, exactly the pick numbers that slot's own DraftEngine reports --
    the single source of truth the frontend is told to trust (FR-057's
    'two implementations must agree' -- this keeps there being only one)."""
    import export_contract as ec

    cfg = lc.CURRENT_LEAGUE
    by_slot = ec._all_slot_pick_numbers(cfg)
    assert set(by_slot) == {str(s) for s in range(1, cfg.teams + 1)}
    all_picks = [p for picks in by_slot.values() for p in picks]
    assert len(all_picks) == len(set(all_picks)), "a pick number appears under two slots"

    # cross-check against run_availability's own engine construction
    for slot in range(1, cfg.teams + 1):
        engine = ra._engine_for_slot(cfg, slot)
        expected = ds.user_pick_numbers() if engine is None else engine.user_pick_numbers()
        assert by_slot[str(slot)] == expected


def test_picks_by_slot_sums_to_rounds_per_slot():
    import export_contract as ec

    cfg = lc.CURRENT_LEAGUE
    by_slot = ec._all_slot_pick_numbers(cfg)
    for slot_str, picks in by_slot.items():
        assert len(picks) == cfg.rounds, f"slot {slot_str} should own exactly cfg.rounds picks"
