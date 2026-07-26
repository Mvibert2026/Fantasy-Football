---
ID: 028
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Build the Predictions tab in Draft mode, against
`docs/design-reference/reference/03-draft-predictions.png` and
`docs/design-handoff/screens/03-draft-predictions.md`.

## Why
The second of the two screens that were reported complete and did not exist. Unlike Opponents, this
one is not blocked — the availability model already produces what it needs, so it can be built now.

This is also the screen that most directly shows the product's differentiator. Availability
probability with a stated number is the thing no competitor ships; this is where it lives.

## Hard requirements
- Probabilities must render with their honest uncertainty treatment, not as bare point estimates.
- Where a probability is not computed for a player, show the explicit null. Not `0%` — those are
  different claims, and confusing them here would undercut the exact feature the screen exists for.
- The current availability figures are **unvalidated** — 1 of ~30 mocks logged. Nothing in this
  screen may imply the numbers are calibrated. If the design does not already carry that caveat,
  flag it rather than inventing wording.

## Done looks like
Tab renders with real data, nulls render as nulls, a screenshot attached, and a test asserting the
tab exists. "Built, pending screenshot verification." Commit hash and test count.
