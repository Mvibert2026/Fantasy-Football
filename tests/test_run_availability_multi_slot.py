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
import export_contract as ec
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


# --------------------------------------------------------------- #4 (regression)
def test_own_slot_numbers_unaffected_by_sweeping_other_slots(season_data):
    """REGRESSION TEST for a real bug caught before this shipped: the first
    version of sweep_slots added a slot-dependent seed offset to EVERY slot,
    including the founder's own -- so even though the founder's own slot
    still took the byte-identical engine=None code path, the RNG stream
    (and therefore the sampled probabilities) moved anyway, by 0.1-2.5
    percentage points across 671 of 1280 checked cells. The founder's own
    slot must produce IDENTICAL numbers whether it is swept alone or as part
    of the full 10-slot sweep."""
    cfg = lc.CURRENT_LEAGUE
    sources = av.default_ranking_sources(season_data)

    alone = ra.sweep_slots(cfg, season_data, sources, 30, 12345, [cfg.user_draft_slot])
    full = ra.sweep_slots(cfg, season_data, sources, 30, 12345, list(range(1, cfg.teams + 1)))

    alone_player_avail = alone[0]
    full_player_avail = full[0]
    own_picks = set(alone[3][cfg.user_draft_slot])

    checked = 0
    for sigma in ds.SIGMA_SWEEP:
        for i, picks in alone_player_avail[sigma].items():
            for pk, prob in picks.items():
                assert pk in own_picks
                assert full_player_avail[sigma][i][pk] == prob, (
                    f"sigma={sigma} player_idx={i} pick={pk}: sweeping other slots changed "
                    f"the founder's own slot's number ({full_player_avail[sigma][i][pk]} != {prob})"
                )
                checked += 1
    assert checked > 0


# --------------------------------------------------------------- #5 (regression)
def test_board_json_availability_embed_stays_own_slot_only(tmp_path):
    """REGRESSION TEST for a real bug caught before this shipped: multi-slot
    coverage in availability.json's by_player is exactly what FR-057 asked
    for, but board.json ALSO embeds `by_player[player]` per row
    (`export_contract.build_board_json`), and un-filtered that meant
    board.json inherited the full ~10x growth too -- measured 1,020,368 ->
    2,276,988 bytes for the primary league, more than doubling an artifact
    loaded on every page view. board.json's per-player `availability` field
    must stay restricted to cfg's OWN pick numbers, same as before 1.15.0 --
    only availability.json carries every slot's data.

    Uses a real DB connection (requires_db, like the rest of this file's
    board-building tests) so this exercises the actual `_own_picks` filter
    in `build_board_json`, not a mock of it.
    """
    conn = dbmod.connect()
    try:
        board = ec.build_board_json(conn, lc.CURRENT_LEAGUE)
    finally:
        conn.close()
    own_picks = set(str(p) for p in ds.user_pick_numbers())
    rows_with_data = [p for p in board["players"] if p["availability"]]
    assert rows_with_data, "expected at least one tracked player with availability data"
    for row in rows_with_data:
        extra = set(row["availability"]) - own_picks
        assert not extra, (
            f"{row['player']}'s board.json availability carries pick(s) {extra} outside "
            f"the founder's own slot -- multi-slot data leaked into board.json"
        )
