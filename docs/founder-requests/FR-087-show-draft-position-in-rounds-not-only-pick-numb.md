---
ID: FR-087
STATUS: NEW
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Think in rounds, not only pick numbers

Founder's own words:

> "It's also helpful to think in rounds"

## Why it matters

## Initial read
<Not the founder's own words -- PM's read on scope, constraints, sequencing.>

## Resolution (2026-07-30, frontend)

Added `pickWithinRound` and `roundPickLabel` (`frontend/ui/data/draft.ts`) beside the existing
`roundOfPick` — pure display formatters (`"R3.03"`) derived from the same snake arithmetic already
in that file, deriving round count from `teams` at each call site, never hardcoded to 10 or 12 as
instructed. Display only: every caller's own overall-pick-number computation is unchanged, only a
label is appended alongside it.

Threaded into every place this app shows a bare overall pick number:
- Draft room: ON THE CLOCK and YOUR NEXT badges, the LIKELY BEST AVAILABLE / LIKELY THERE AT
  reference-point headers.
- Prep and Draft opponents cards (`Opponents.tsx`, `LiveOpponents.tsx`): the "next #N" badge on
  every team card.
- Player detail sheet: the AVAILABILITY AT YOUR PICKS pick label and the five-pick availability
  strip below it.
- Predictions: the "Live availability at pick N" header.

Not touched: `RoundGrid.tsx`'s per-cell pick numbers — that grid is already organized round-by-round
(one grid row per round), so the round is already communicated structurally; adding a redundant
label to every cell would be exactly the density/whitespace violation Principle #4 forbids without
adding real information.

Screenshot: `frontend/e2e/artifacts/fr087-clock-badges.png` (ON THE CLOCK / YOUR NEXT with round
labels); round labels also visible in `fr082-prep-opponents-top.png` and
`fr082-draft-opponents-top.png`'s "next #N (R#.##)" badges, and in
`fr083-player-card-westwood-adp-block.png`'s "at pick 3 (R1.03)" line.

`npx tsc -b --noEmit` clean. Test count/commit: see session report in `docs/status/`.
