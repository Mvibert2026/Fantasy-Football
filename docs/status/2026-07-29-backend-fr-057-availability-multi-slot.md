# 2026-07-29 — backend — fr-057-availability-multi-slot

Dispatched to execute FR-057 part 1: the draft-slot selector (FR-034) already changes the pick
sequence everywhere in the app, but `data/export/availability.json`'s `by_player`/`by_tier` were
keyed by the founder's own slot's pick numbers only, computed by a single Monte Carlo run in
`run_availability.py`. Switching the selector to any other slot found no matching keys — numbers
went absent, not wrong. Part 2 (browser-side recomputation, the founder's stated preference) was
explicitly out of scope, per the dispatch.

## What shipped

- `src/run_availability.py`: sweeps every slot 1..`teams` (was one), merges into the EXISTING
  `by_player`/`by_tier` shape. No new nesting level: for a fixed team/round count, a pick number
  belongs to exactly one slot, so the merge is a disjoint union — proved structurally
  (`tests/test_run_availability_multi_slot.py`) before the merge code was written, per the
  project's sanity-check-first rule.
- `src/export_contract.py`: `CONTRACT_VERSION` 1.14.0 → 1.15.0. New `metadata.multi_slot_coverage`
  and `metadata.picks_by_slot` (canonical pick sequence per slot — one source of truth instead of
  a second, independently-written snake-order implementation on the frontend that could drift).
- `docs/data-contract.md` documents the new fields and states the measured payload/runtime numbers
  plainly, including the recommendation these numbers support.
- Handoff thread 093 opened to `frontend` with the exact field-level contract and the required
  change (read `picks_by_slot[str(slot)]` instead of assuming the founder's own).
- ADR-061 in `docs/decisions.md` — full writeup, measured numbers, both bugs below.

## Two real regressions caught before this shipped, not after

Both were found by diffing actual output against the pre-session committed artifacts — not by
review — and both are now regression-tested so they can't silently recur:

1. **The founder's own slot's numbers moved.** The first version of the sweep added a
   slot-dependent RNG seed offset to every slot, including the founder's own — so even though that
   slot kept the exact pre-existing algorithm path (`engine=None` for the primary league), the
   different seed changed the sampled noise draws. 671 of 1280 checked cells at the founder's own
   pick numbers differed from the pre-session committed `availability.json` by 0.1–2.5 percentage
   points. Fixed: the seed offset is now `0` specifically for `cfg.user_draft_slot`, non-zero only
   for the nine new slots. `test_own_slot_numbers_unaffected_by_sweeping_other_slots`.
2. **`board.json` inherited the multi-slot growth by accident.** It embeds
   `by_player[player]` per row too (a separate consumer of the same CSV, `build_board_json`), and
   left un-filtered that meant `board.json` — loaded on every page view, not just an
   availability-specific screen — grew from 1,020,368 to 2,276,988 bytes (2.2x) for a feature
   FR-057 never asked it to carry. Fixed: `build_board_json` now filters its `by_player` read down
   to `cfg`'s own pick numbers only, the exact slice it carried before 1.15.0.
   `test_board_json_availability_embed_stays_own_slot_only`.

Refactored the sweep out of `run_availability.py`'s `main()` into a standalone `sweep_slots()`
function specifically so both bugs above could be regression-tested directly instead of only
through a full CLI run (which takes ~10.5 minutes and can't run per-test).

## Measured, not assumed (the task's explicit ask)

| | Before (1 slot) | After (10 slots, primary league) |
|---|---|---|
| `availability.json` | 161,100 bytes | 1,554,817 bytes (**9.65x**) |
| Sweep runtime (3000 sims × 3 sigmas) | ~45-60s (prior doc estimate, 1 slot) | **628.8s (~10.5 min) measured directly, ~63s/slot average** |
| `board.json` | 1,020,368 bytes | unchanged (bug #2 above, caught and fixed) |

**Recommendation, stated plainly per the dispatch's instruction:** ~10.5 minutes and a 9.65x
`availability.json` (to 1.55 MB) is workable as a one-time floor for one 10-team league. It does
NOT extend cheaply — a 14-team league scales roughly linearly with team count at the measured
~63s/slot rate, and sweeping all 27 league exports (25 of which have no Monte Carlo data at all
today, per ADR-047's pre-existing cost scope) would be on the order of hours. This is exactly what
client-side recomputation (FR-057 part 2) sidesteps — it computes one slot's answer on demand
instead of precomputing all of them, and its inputs (`client_simulation_parameters`) already ship,
predating this session.

## Scope decisions logged, not escalated (`docs/ideas-inbox.md`)

1. No `by_slot` nesting needed — pick number alone disambiguates, kept the contract change
   additive.
2. Only the primary league (Westwood, real founder data) got a real sweep. The 24 preset configs
   and `ethans_expert_league` have never had a real Monte Carlo run at all (ADR-047, unrelated to
   this session) — the code path works for any league the moment one IS run.
   `yahoo_standard_mock`'s existing single-slot CSV (a labelled test fixture, not a founder league)
   was left un-swept for the same reason.
3. The founder's own slot stays on its exact pre-existing code path rather than unifying every
   slot onto `ds.DraftEngine` — a scratchpad comparison found the two paths diverge by up to ~0.02
   absolute probability at late picks even though they should be numerically identical (not
   root-caused, logged, does not affect the founder's own slot).

## Also fixed as a side effect

`board.json`'s `consensus_source_note` field still carried ADR-060's stale "no ADP source
(ADR-018)" text as of that session's own "known limitation, not fixed here" note — that session's
worktree had no working `nfl.db`. This session's worktree did, so regenerating `board.json` here
picked up the already-corrected source text with no code change needed. Confirmed by reading the
regenerated file directly.

## Evidence

- `python3 -m pytest tests/test_run_availability_multi_slot.py -q` — 9 passed.
- `data/nfl.db` copied into the worktree from the shared checkout per `docs/environment.md` §4
  (worktrees don't inherit it; a fresh `sqlite3.connect` would otherwise create a silent empty
  stub).
- Full sweep run twice: once with the seed bug present (caught by diffing, not committed as data),
  once after the fix (committed). `export_strategies.py` also re-run (13-minute regeneration) so
  its `contract_version` stamp matches 1.15.0 — `test_strategies_json_contract_version_matches_export_contract`
  otherwise fails unconditionally (a real inconsistency with the OTHER contract-version test's
  comment claiming strategies.json is allowed to lag; not resolved here, just worked around by
  regenerating rather than leaving a known-red test).

Commit hashes and final test count: see the session's final report / next `git log`.
