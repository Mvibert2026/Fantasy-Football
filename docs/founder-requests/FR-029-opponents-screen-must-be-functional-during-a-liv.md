---
ID: FR-029
STATUS: IN PROGRESS
SOURCE: frontend session, dispatched as "FR-032" in the task brief
RAISED: 2026-07-29
---

## Request

Founder's own words, quoted in this session's dispatch brief: **"For opponents we will need to
fix that.. make it functional for the user."**

**Numbering note:** the dispatch that opened this session referred to this request as "FR-032"
throughout. Running `tools/founder_requests.py new` in this worktree allocated **FR-029** instead
(this worktree's `docs/founder-requests/` only had FR-018..FR-028 on disk; `check` reports no
cross-branch collision as of this session). Recorded here rather than silently renumbered, in case
"FR-032" already exists as a real, merged file in a sibling worktree/branch not visible here —
whoever reconciles branches should treat FR-029 and any real FR-032 covering this same request as
the same item, not two.

## Why it matters

A prior session mounted `Opponents.tsx` into the Draft-mode hub tab and found it reads roster/
next-pick data only from backend `rosters.json` -- real, non-mock completed-draft data. During a
live draft that file reflects nothing (no real 2026 draft has been logged to it), so the tab was a
permanently-empty placeholder exactly when the founder needs it most: knowing what an opponent
already has and still needs while a live draft is running.

## Initial read

Not the founder's own words -- this session's scope call: build a *separate* live-draft view
(`LiveOpponents.tsx`) rather than reusing the Prep-mode `Opponents.tsx` screen, because the two
have genuinely different data sources (backend `rosters.json` vs. this session's local pick log)
that must never silently blend into one number. Mechanical arithmetic only -- roster fill, unfilled
slots, next-pick number -- reusing the existing `buildRosterSlots` roster-need arithmetic
(originally in `DraftRoom.tsx`, extracted to `ui/data/rosterSlots.ts` so both the user's own MY
ROSTER panel and this new per-opponent view share one implementation). No inferred strategy,
tendencies, or predicted next pick anywhere on this screen.

## Update, 2026-07-29 (same session)

Built: `frontend/ui/views/LiveOpponents.tsx`, mounted at `DraftRoom.tsx`'s Opponents hub tab in
place of the old "not wired into Draft mode yet" placeholder. Every team's roster/needs/next-pick
is computed from `DraftState.picks` (this session's local pick log), never from `rosters.json`.
Empty state (zero picks entered) renders one honest sentence, not a ten-team empty grid. 4 new
tests (`ui/__tests__/live-opponents.test.tsx`) plus one updated existing test
(`draft-room-recommendation.test.tsx`), full suite 209/209 passing, `tsc -b --noEmit` clean.
Screenshots taken and looked at (`frontend/e2e/artifacts/live-opponents-empty-2026-07-29.png`,
`live-opponents-populated-2026-07-29.png`) -- see the frontend session log
(`docs/status/2026-07-29-frontend-opponents-live.md`) for what they show. Left `IN PROGRESS`, not
`SHIPPED`, pending founder review of the screenshots per this project's own evidence standard (a
screenshot a human has looked at, not an agent's own report).
