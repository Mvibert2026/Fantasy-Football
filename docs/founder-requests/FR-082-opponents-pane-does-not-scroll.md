---
ID: FR-082
STATUS: NEW
STATUS: SHIPPED
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Opponents pane does not scroll

Founder's own words:

> "Opponents doesn't scroll down"

## Why it matters

## Initial read
<Not the founder's own words -- PM's read on scope, constraints, sequencing.>

## Resolution (2026-07-30, frontend)

**Premise correction mid-task, from the coordinator:** the original brief said this was "one
component rendered twice" (`Opponents.tsx` wrapped as `AdaptedOpponentsPane` inside
`DraftRoom.tsx`) — true when FR-036 was written, no longer true. `LiveOpponents.tsx` (300 lines,
added for FR-032) is now a separate component that Draft mode actually renders
(`DraftRoom.tsx:1102`), not a wrapper around `Opponents.tsx`. Checked both surfaces independently
rather than assuming one fix covered both.

**Prep mode (`Opponents.tsx`, mounted via `App.tsx:207-210`): already scrolled correctly.**
`<div className="view" style={{flex:1, minHeight:0}}>` wraps it, and `.view` already carries
`overflow: auto` (`ui/styles/base.css`). Verified with a real scroll screenshot
(`frontend/e2e/artifacts/fr082-prep-opponents-scrolled.png`) — no code change needed here.

**Draft mode (`LiveOpponents.tsx`, mounted via `DraftRoom.tsx`'s `hubTab === 'opponents'`
branch): genuinely broken, matching the founder's report exactly.** Unlike the sibling
`hubTab === 'predictions'` branch right below it (which correctly wraps its content in
`flex:1, minHeight:0, overflowY:'auto'`), the opponents branch rendered `<LiveOpponents/>` with no
wrapping scroll container at all — its own root div carries padding but no `flex`/`overflow` of
its own, so it just grew to its natural height with nothing below able to scroll. Fixed by adding
the same wrapper pattern the predictions tab already uses. Verified with a real scroll screenshot
against a seeded 23-pick draft (10 team cards, two full rows):
`frontend/e2e/artifacts/fr082-draft-opponents-top.png` (rows 7-10 cut off at the fold) vs.
`fr082-draft-opponents-scrolled.png` (same state, scrolled — rows 7-10 now fully visible).

**Logged, not fixed here:** the two components have real feature divergence beyond this bug
(typed team-name override exists only in `Opponents.tsx`; behavioural-tendency fields only there
too) — `docs/handoffs/NEW-opponents-and-liveopponents-have-diverged.md` (pending PM's ID
allocation), per the coordinator's explicit instruction not to attempt a consolidation inside this
task.

`npx tsc -b --noEmit` clean. Test count/commit: see session report in `docs/status/`.
