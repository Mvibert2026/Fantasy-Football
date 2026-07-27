---
ID: 027
FROM: pm
TO: frontend
STATUS: BLOCKED-EXTERNAL
OPENED: 2026-07-26
BLOCKED-BY: 016
---

## Ask
Build the Opponents tab in Draft mode, against the committed design at
`docs/design-reference/reference/02-draft-opponents.png` and the spec in
`docs/design-handoff/screens/02-draft-opponents.md`.

Wait for thread 016 to deliver the league rosters export. Building before that produces an empty
screen that looks finished.

## Why
This is the headline gap. It was previously reported as "folded into a single pane" and was in fact
absent entirely — no tabs, no fallback, nothing — while the whole test suite passed, because no test
asserted the screen existed.

## Hard requirements
- **What a team has** and **what a team still needs** are both mechanical arithmetic over roster
  slots. Show those.
- **Do not display or imply inferred strategy.** Guessing an opponent's latent draft plan from their
  opening picks was explicitly refused as methodologically indefensible with available data. Nothing
  on this screen may suggest the product knows what an opponent is *trying* to do.
- Seven of the nine other teams are known only by draft slot. Render that honestly rather than
  inventing labels.

## Done looks like
Tab renders with real data. A **screenshot** attached for the founder. A test asserting the tab
exists and is reachable — the missing-screen failure happened precisely because no such test existed.
Report as "built, pending screenshot verification," never as done. Commit hash and test count.

---
### frontend · 2026-07-27

Completed the card per this thread's "complete the card" scope (`frontend/ui/views/Opponents.tsx`,
its own tests only — did not touch `DraftRoom.tsx`/`Sidebar.tsx`/`PlayerDetail.tsx`/`lib/`, all
owned by concurrent sibling sessions this round). The screen was already largely built (roster slot
rows, STILL NEEDS chips, the starters/bench footer, real `rosters.json` wiring) from an earlier
session — this pass closed the remaining gaps:

1. **`next #N` in the card header** (was missing entirely). Pure snake-order arithmetic, no new
   backend field needed: `rosters.json:picks_ingested` + `league.json:teams`/`rounds` +
   `opponents.json:draft_slot_2026`, run through `pickNumbersForSlot` (`ui/data/draft.ts`, already
   exported and used by `DraftRoom.tsx`/`PlayerDetail.tsx` for the user's own next pick — imported
   read-only here, not duplicated or reimplemented). Three states per Principle #2: no
   `rosters.json` → no badge at all; `rosters.json` present but no picks left in this league's round
   count → `next —`; otherwise the real upcoming overall pick number. This is schedule math, not a
   strategy inference — it answers "whose turn is it," never "what will they do."
2. **Roster row order bug found and fixed while verifying against the spec**: the card anatomy
   (`docs/design-handoff/screens/02-draft-opponents.md`, confirmed against the reference screenshot)
   is `QB, RB, WR, TE, FLEX, DEF` — FLEX before DEF. The existing code rendered `QB, RB, WR, TE, DEF,
   FLEX`. Fixed; `STARTER_ORDER` now covers QB–TE only, DEF is placed after FLEX explicitly, and a
   new `CHIP_POSITIONS` constant keeps the STILL NEEDS chip set (QB/RB/WR/TE/DEF) from silently losing
   DEF when it moved out of the row-rendering list.
3. **No-inferred-strategy hard requirement re-checked, not re-decided**: `positional_tendencies`,
   `first_pick_by_position`, `consensus_tracking_behaviour` are already gated behind a real
   "NOT A MODEL INPUT" label and are null for all 9 real opponents today, so nothing renders there
   currently — left as-is, this thread's ask was completion, not re-litigating that gate.

**Tests**: `frontend/ui/__tests__/opponents.test.tsx` — 5 → 9 tests, all passing. Added: a screen-exists
heading assertion (the exact gap that let a prior "Opponents tab" ship as literally absent), a
real-data next-pick assertion (computed from the export via the same `pickNumbersForSlot` helper, not
a hand-picked literal), a forced "no picks left" → `next —` case, a `next` badge absent when
`rosters.json` is null, and a QB/RB/WR/TE/FLEX/DEF row-order assertion. Full frontend suite: **132
passed, 0 failed, 16 files** (`npx vitest run`, this session) — up from the 126/1-fail baseline noted
in `CURRENT-STATE.md`; the 1 pre-existing failure (`trace-fields.test.ts`, contract-version drift) is
gone too, but that fix belongs to whichever concurrent session touched `trace-fields.ts` this round,
not to this thread. `npx tsc --noEmit` clean for everything this thread touched (one unrelated error
in `Predictions.tsx`, a sibling session's concurrent WIP, not caused by or fixed by this thread).

**Screenshot: attempted, not obtained — reporting the gap rather than claiming one exists.** Started
the dev server on port 5175 as instructed (added a `frontend-opponents-b` entry to
`.claude/launch.json` for it, additive, did not touch the existing `prep`/`prep-verify` entries),
navigated to the Opponents tab, and confirmed via `read_page`/`get_page_text` that all of the above
renders correctly against the real 9-opponent, 10-team export (verified every card's `next #N`, row
order, needs chips, and footer counts by reading the live DOM text, not by inference). The pixel
`computer screenshot` / `zoom` calls themselves failed every attempt, on two separate tabs, with
"the Browser pane is not displayed, so the page is not compositing frames" — a session-level
limitation of this background dispatch, not a rendering problem in the app. No screenshot file exists;
none is claimed. Per operating-model.md's evidence bar ("a screenshot a human has looked at," not a
passing test suite), this thread is **not** being marked RESOLVED on that basis alone.

**Commit**: see final report to dispatcher for hash (created after this reply). Files touched:
`frontend/ui/views/Opponents.tsx`, `frontend/ui/__tests__/opponents.test.tsx`, `.claude/launch.json`
(additive entry only).

**STATUS left OPEN, not RESOLVED.** What remains: an actual screenshot image, a human (or a session
with working Browser-pane compositing) looking at it. Everything else in the "Done looks like" list —
real data, the test asserting the screen exists and is reachable, commit + test count — is done. The
dev server (port 5175) was left running for whoever picks this up to screenshot directly rather than
re-syncing exports and re-launching from scratch.

---
### pm · 2026-07-27

Reclassifying `OPEN` → `BLOCKED-EXTERNAL`. This is not silent and not stalled — everything in "Done
looks like" is met except the screenshot, and the blocker is a real external one: the Browser pane
this entire round shared one preview surface across 9 concurrent sessions and would not composite
frames for pixel capture (confirmed independently by me, not just this thread — same error on my
own attempt against this exact tab). DOM/text-level verification is real and was done thoroughly,
but is not the standard `operating-model.md` sets. Dev server still up on port 5175; this needs a
session with working screen compositing, not more engineering work.
