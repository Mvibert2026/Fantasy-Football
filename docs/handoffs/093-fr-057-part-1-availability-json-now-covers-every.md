---
ID: 093
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask
FR-057 part 1: the draft-slot selector (FR-034) already changes the pick sequence everywhere in
the app -- board, round grid, Predictions, draft room -- but `data/export/availability.json`'s
`by_player`/`by_tier` used to have rows for only ONE slot's pick numbers (the founder's own,
`metadata.user_draft_slot`). Switch the selector to any other slot and those keys didn't exist --
numbers went absent, not wrong. `CONTRACT_VERSION` is now `1.15.0` (was 1.14.0).

**The shape did NOT change.** `by_player`/`by_tier` are still `{player_or_pos: {pick_number:
{sigma_5, sigma_10, sigma_20}}}` exactly as before -- nothing to re-parse. What changed: those
dicts now have rows for every slot's pick numbers, not just one, because `run_availability.py`
runs the simulation once per slot (1..`league.json:teams`) and merges the results (safe: an
overall pick number belongs to exactly one slot, proven in
`tests/test_run_availability_multi_slot.py`, so it's a disjoint union, never an overwrite).

**Two new fields in `availability.json.metadata`:**
- `multi_slot_coverage: true` -- a flag you can check to confirm you're reading a 1.15.0+ export.
- `picks_by_slot`: `{"1": [pick,...], "2": [...], ..., "<teams>": [...]}` -- the canonical pick
  sequence for EVERY slot, computed by the same `pick_order()`/`DraftEngine` code the backend
  already uses, not re-derived. **Use this instead of re-implementing snake-order arithmetic
  client-side** -- FR-057's own text calls out "two implementations must agree" as the risk to
  avoid, and this closes that risk by giving you one source of truth instead of two that could
  drift apart.

**What you need to do:** wherever the app currently reads `by_player[player][pick]`/
`by_tier[pos][tier][pick]` using the founder's own slot's pick numbers, when the user has the
slot selector set to slot N, look up `picks_by_slot[String(N)]` for that slot's pick sequence and
read those pick numbers out of the existing `by_player`/`by_tier` instead. `metadata.
user_draft_slot`/`user_picks` are UNCHANGED (still the founder's configured slot) -- nothing that
reads them today needs to change.

Full field-level docs: `docs/data-contract.md` under `## availability.json` -> "Multi-slot
coverage (contract 1.15.0, FR-057 part 1)".

**Not included, do not build against it:** true client-side recomputation conditioned on picks
actually made mid-draft (FR-057 part 2, the founder's stated preference, explicitly a separate
larger build). `client_simulation_parameters` (unchanged, predates this thread) already carries
what a client-side simulator would need for that -- this thread is the floor, not the ceiling.

**Known, measured deviation, not expected to be visible in the UI but worth knowing about:** every
slot except the founder's own (which stays on the exact pre-existing code path) uses a generalized
draft engine that a scratchpad comparison found differs from the original by up to ~0.02 absolute
probability at late picks for the SAME slot -- not yet root-caused (`docs/ideas-inbox.md`,
2026-07-29 backend entry). The founder's own slot's numbers are unchanged from before this
session.

## Why
Without this, the slot selector he can already click today produces a screen with blank/absent
availability numbers for any slot but the one hardcoded picks he started with -- a selector that
changes labels but not answers, which is the exact defect FR-057 was opened to describe. This
closes that for the primary league (Westwood, the only league with real availability data
generated so far -- see the ADR for why the other 26 leagues stay out of scope here).

## Done looks like
`src/run_availability.py` and `src/export_contract.py::build_availability_json` regenerate
`data/export/availability.json` with `contract_version: "1.15.0"`, `metadata.multi_slot_coverage:
true`, and `metadata.picks_by_slot` populated for all 10 primary-league slots. Committed:
`src/run_availability.py`, `src/export_contract.py`, `tests/test_run_availability_multi_slot.py`,
`docs/data-contract.md`, `data/availability_2026.csv`, `data/export/availability.json`, and every
other regenerated primary-league artifact whose `contract_version` field the test suite checks
(`board.json`, `league.json`, `glossary.json`, `nulls.json`, `opponents.json`). See ADR-061 for
the full writeup and measured payload/runtime numbers. Reply here once the frontend side reads
`picks_by_slot` for the non-default-slot case -- a screenshot of the selector set to a slot other
than the founder's own showing real (non-blank) availability numbers is the acceptance evidence,
same standard as any other UI claim.
