# Frontend — Opponents live in Draft mode + Refresh data removal — 2026-07-29

**Scope given:** `frontend/**` only. Not `src/`, not `docs/CURRENT-STATE.md`, not `.github/`.
Dispatched as FR-032 (see numbering note below); a second ask was relayed mid-session by the
coordinator (remove the Refresh data button on the hosted site).

## What the founder asked for

> "For opponents we will need to fix that.. make it functional for the user."

A prior session (same day) had mounted `Opponents.tsx` into the Draft-mode hub tab and found the
real limit: it reads roster/next-pick data only from backend `rosters.json`, which is real,
non-mock completed-draft data. During a live draft that file reflects nothing (no real 2026 draft
has been logged there), so the tab rendered as a placeholder. This session's job was to make the
tab actually useful mid-draft.

## Numbering note

The dispatch referred to this request as "FR-032" throughout. `tools/founder_requests.py new` in
this worktree allocated **FR-029** (this worktree's `docs/founder-requests/` only went up to
FR-028; `check` reports no cross-branch collision). Filed under FR-029, with the FR-032 label
preserved in its `SOURCE:` field in case a real FR-032 already exists in a branch this worktree
doesn't see — flagged for whoever reconciles branches, not resolved unilaterally here.

## What was built

**Found the existing roster-need arithmetic rather than writing a second one**, per the task's own
instruction: `buildRosterSlots` in `frontend/ui/views/DraftRoom.tsx` (previously private to that
file, used only to build the user's own MY ROSTER panel from `userPicks` -- a filter of
`draft.picks` by the user's own `teamSlot`). The function itself was already slot-agnostic; it has
never looked at which team's picks it's handed. Extracted verbatim, no logic change, to
`frontend/ui/data/rosterSlots.ts` so a second caller could use the identical arithmetic per team
instead of re-deriving it. `DraftRoom.tsx` now imports it from there; its own MY ROSTER panel is
unchanged in behavior.

**New component: `frontend/ui/views/LiveOpponents.tsx`.** Mounted at `DraftRoom.tsx`'s Opponents
hub tab in place of the old "Opponents is not wired into Draft mode yet" placeholder. For each of
the league's real team slots (`league.json:teams`), it filters `DraftState.picks` (this session's
local, in-browser pick log -- the same object `DraftRoom.tsx`'s own MY ROSTER already reads) by
`teamSlot`, runs `buildRosterSlots`, and renders:

- Real drafted players by roster slot (QB/RB/WR/TE/FLEX/DEF), matching the Prep-mode Opponents
  card's visual language (bordered team cards, colored position rows, "empty" in dim italic).
- **STILL NEEDS** chips: real `required - filled` per starter position -- QB/RB/WR/TE/DEF, no
  fabricated urgency ranking, no predicted next pick.
- **next #N**: real snake-order arithmetic (`nextPickForSlot`, already existing in `ui/data/
  draft.ts`, imported not reimplemented) -- the same helper that already computes the user's own
  next pick.
- **ON THE CLOCK**: which team slot is currently up, from `teamSlotAtPick(currentOverallPick(...))`
  -- also already-existing arithmetic, not new.
- **(you)**: the user's own slot, from `league.json:user_draft_slot`.

**Boundaries honored, not just stated:**

- **No inferred strategy anywhere on this screen.** `opponents.json`'s `positional_tendencies` /
  `first_pick_by_position` / `consensus_tracking_behaviour` fields are not read by this component
  at all -- there is no code path that could render them here, not just an unused prop. Verified by
  a test asserting those strings and "NOT A MODEL INPUT" never appear on this tab
  (`ui/__tests__/live-opponents.test.tsx`, "STILL NEEDS reflects real unfilled starter counts, not
  a fabricated tendency").
- **The two data sources never merge.** This component imports nothing from `rosters.json` --
  only `opponents.json`'s static `team_name` field (an identity label, not a roster number) is
  read, the same field the Prep-mode screen already uses for the same purpose. The empty-state
  text and the populated-state banner both name `rosters.json` explicitly, by contrast, so the
  distinction is visible on screen, not just true in the code.
- **Empty state reads as "nothing happened," not as a finding.** Before any pick is entered,
  `LiveOpponents` renders one sentence ("No picks yet. Mark picks on the Board tab...") and zero
  team cards -- not a ten-team grid where every team needs every position, which would look like a
  discovered fact rather than the absence of one. Confirmed live and by test.

**Doc comments updated in place**, not left describing stale behavior: `DraftRoom.tsx`'s own
module doc previously said Opponents/Predictions were "not yet folded into this pane"; corrected
to say Opponents is now wired in via `LiveOpponents.tsx` and explain why it isn't a reuse of the
Prep-mode screen.

## Mid-session addition: remove the Refresh data button

Coordinator relayed, mid-task: **"We also can remove that refresh data button at the top."**
Reasoning given: `/__refresh` is dev-server-only Vite middleware
(`server/refresh.ts`'s `configureServer` hook never attaches under `vite build`), and the
founder's daily use has moved to the hosted static site, where the button can only ever fail.

Verified directly rather than taking the reasoning on faith: built the app (`npm run build`),
served the real production output with `vite preview`, and confirmed by screenshot that
`/__refresh` genuinely does not exist there -- this is a compile-time absence (no route registered
at all), not a flaky-network question, so the fix uses a compile-time signal
(`import.meta.env.DEV`), not a runtime probe.

`RefreshData.tsx` gained a `refreshAvailable` prop, defaulting to `import.meta.env.DEV`. The
button renders only when true. **The freshness line is unconditional either way** -- per the
coordinator's explicit hard requirement, hiding the button must never also hide the fact it
existed to report (`generated_utc` + the snapshot-freshness fields, contract 1.13.0). Confirmed by
screenshot: production build shows `exported <timestamp> · snapshot fresh (...)` with no button;
dev server shows the same text plus the button.

## Evidence

Screenshots taken and looked at (not merely captured) -- `frontend/e2e/artifacts/`:

- **`live-opponents-empty-2026-07-29.png`** -- Draft mode, Opponents tab, zero picks entered.
  Shows exactly one sentence: "No picks yet. Mark picks on the Board tab and each team's roster
  will fill in here as the draft happens. This view is built from picks entered in this session
  (this browser's local draft log), separate from and never merged with backend `rosters.json`
  -- the Prep-mode Opponents screen's data source, which reflects only real, completed drafts on
  file." No team cards, no STILL NEEDS chips, nothing that could be mistaken for a finding.
- **`live-opponents-populated-2026-07-29.png`** -- same tab after seeding 6 real picks across 6
  different team slots (real board players: Bijan Robinson -> slot 1 "Cucked Commish", Ja'Marr
  Chase -> slot 2 "Shit Leopards", Josh Allen -> slot 3, the user's own slot, labelled "(you)",
  Puka Nacua -> slot 4, Jonathan Taylor -> slot 5, Amon-Ra St. Brown -> slot 6). Each card shows
  only its own player, correct STILL NEEDS chips (e.g. slot 1's RB row went from "×2" to "×1"
  after Bijan Robinson filled one of two RB starter slots), and real per-team next-pick numbers
  that check out against the league's real 10-team snake order (slot 1's "next #20" and slot 2's
  "next #19" both match round-2 snake reversal by hand calculation). Slot 7, on the clock at
  overall pick 7, is the only card marked "ON THE CLOCK." Slots 8-10 (not yet reached) show fully
  empty, honest zero state -- real per-team absence, not the global "nothing happened yet" state
  from the empty screenshot above.
- **`topbar-dev-2026-07-29.png`** -- dev server (`npm run dev`): "Refresh data" button present,
  next to the freshness text.
- **`topbar-prod-2026-07-29.png`** -- real production build (`npm run build` + `vite preview`):
  button gone; freshness text (`exported 2026-07-29T16:39:37... · snapshot fresh (2d old, max
  3...)`) still fully present, unchanged from the dev screenshot's text.

**Degrades sensibly with zero picks entered:** confirmed above (the empty-state screenshot) and by
an explicit test asserting no `live-opponent-slot-*` test id and no "STILL NEEDS" text render
before any pick exists.

## Tests

- `frontend/ui/__tests__/live-opponents.test.tsx` (new, 4 tests): empty state; each team's card
  shows only its own picks; STILL NEEDS arithmetic + no inferred-strategy text; on-the-clock badge
  + real next-pick numbers.
- `frontend/ui/__tests__/draft-room-recommendation.test.tsx` (1 assertion updated to match the new
  empty-state text instead of the retired placeholder text).
- `frontend/ui/__tests__/refresh.test.tsx` (2 new tests): button hidden + freshness text intact
  when `refreshAvailable={false}`; button shown when `refreshAvailable={true}`.

**Full suite: 209 passed, 0 failed, 23 test files** (`npm test`, this worktree, 2026-07-29).
`npx tsc -b --noEmit`: clean.

**Fidelity harness:** `docs/design-fidelity.md` names `tools/fidelity.py`; the actual file lives at
`docs/design-reference/fidelity.py` (a known, already-tracked relocation gap -- see
`docs/backlog-triage-2026-07-29.md` thread 037 items 3-4, not something to fix unilaterally in this
session). Its `screens.json` maps `opponents` to route `/draft/opponents`, but this app has no
router at all (`grep` for `react-router`/`BrowserRouter` in `ui/`/`server/` returns nothing) --
navigation is in-memory tab state, not URLs. Running the harness as-is would not measure this
change meaningfully (it would `goto` a path this SPA doesn't route on). Not run this session;
flagged rather than silently skipped or forced to a misleading result.

## Founder requests logged

- **FR-029** (`docs/founder-requests/FR-029-...md`) -- this Opponents-live request. `SOURCE:` notes
  the dispatch called it "FR-032."
- **FR-030** (`docs/founder-requests/FR-030-...md`) -- the Refresh data button removal, relayed
  by the coordinator mid-session.

Both left `STATUS: IN PROGRESS`, not `SHIPPED` -- this session's own report is not the evidence bar
per `docs/operating-model.md`; founder review of the attached screenshots is.

## Files touched

- `frontend/ui/data/rosterSlots.ts` (new -- extracted from `DraftRoom.tsx`)
- `frontend/ui/views/LiveOpponents.tsx` (new)
- `frontend/ui/views/DraftRoom.tsx` (import shared roster-slot module; mount `LiveOpponents`;
  doc comment corrected)
- `frontend/ui/components/RefreshData.tsx` (`refreshAvailable` prop, default from
  `import.meta.env.DEV`)
- `frontend/ui/__tests__/live-opponents.test.tsx` (new)
- `frontend/ui/__tests__/draft-room-recommendation.test.tsx` (assertion updated)
- `frontend/ui/__tests__/refresh.test.tsx` (2 new tests)
- `frontend/e2e/live-opponents-shot.mjs`, `frontend/e2e/topbar-prod-shot.mjs` (new capture
  scripts, tracked per the existing `e2e/` convention)
- `frontend/e2e/artifacts/live-opponents-empty-2026-07-29.png`,
  `live-opponents-populated-2026-07-29.png`, `topbar-dev-2026-07-29.png`,
  `topbar-prod-2026-07-29.png` (new, tracked)
- `docs/founder-requests/FR-029-...md`, `FR-030-...md` (new), `docs/founder-requests/INDEX.md`
  (regenerated)

## Not done / explicitly out of scope this session

- Thread 027 (Prep-mode Opponents screenshot) was not touched -- different screen
  (`Opponents.tsx`, backend-`rosters.json`-backed), not modified by this session's work.
- The `fidelity.py` relocation (backlog thread 037 items 3-4) was not fixed here.
- `docs/CURRENT-STATE.md` was intentionally not edited -- out of this dispatch's stated boundary.
