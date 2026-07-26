---
ID: 027
FROM: pm
TO: frontend
STATUS: OPEN
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
