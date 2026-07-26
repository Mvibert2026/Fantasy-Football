---
ID: 016
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: the Opponents tab
---

## Ask
Build the full league rosters export: all 10 teams' complete rosters including bench and IR, not just
the drafted board. Add it to the export set with a contract version bump, and open a thread to
`frontend` announcing the new artifact and its shape.

## Why
It is the first item in the confirmed backend gap list and the hard blocker on the Opponents tab.
Frontend has been asked to build that tab; without this it can only render an empty screen, which is
worse than not building it — it looks finished and says nothing.

Note the design constraint: the Opponents view distinguishes what a team *has* from what a team still
*needs*, and the need side is mechanical arithmetic over roster slots. The inferential side — guessing
an opponent's latent strategy — was explicitly refused as indefensible. Export the observable facts
only.

## Done looks like
New artifact in `data/export/<league_id>/`, contract version bumped, tests covering shape and the
empty-roster case, thread opened to `frontend`. Reply with commit hash and test count.

---
### backend · 2026-07-26

Built. `rosters.json` in `data/export/<league_id>/` (unprefixed `data/export/rosters.json` for the
primary league, same convention as board/availability/league). `CONTRACT_VERSION` bumped 1.7.0 ->
1.8.0 in `src/export_contract.py`; all six other artifacts regenerated at the new version so nothing
on disk claims a stale version.

`build_rosters_json()` in `src/export_contract.py` builds all `teams` rosters (starters/flex/bench/IR)
mechanically from real (`is_mock=0`) draft picks logged for the *current* season only -- see
`_real_draft_picks`'s docstring for why that season scoping structurally excludes the 2025 real draft
already on file (2025 is the locked holdout; this query can't return it even by accident). `needs` is
pure `required - filled` arithmetic per slot, nothing inferential -- no field predicts what a team is
likely to draft next, per the design constraint in this thread's Ask.

Right now, correctly, `data/export/rosters.json` shows `draft_state: "not_started"`, every team's
`players` empty, every `needs` at full requirement -- no real 2026 draft is logged yet. That is the
empty-roster case, and it's exercised directly by
`test_rosters_export.py::test_empty_roster_shape_and_needs_before_any_draft` plus the requires_db
`test_primary_league_rosters_are_empty_before_the_real_2026_draft`. Slot-filling/needs arithmetic
(starters before flex before bench, unresolved-position picks never silently guessed into a starter
slot) is covered against a synthetic in-memory DB in the same file, independent of what's on disk.

Thread opened to frontend: `docs/handoffs/038-rosters-json-artifact.md` (note: 037 was already taken
by a concurrently-opened thread when I went to write this -- used 038 instead, see that thread's own
note).

Commit: `<see closing commit below>`. Tests: `tests/test_rosters_export.py` adds 9 (7 fast synthetic +
2 requires_db), full suite otherwise unchanged in coverage.

STATUS: RESOLVED
