---
ID: FR-051
STATUS: NEW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Show value over the player expected at my next pick

Founder's own words:

> "I think we also already have value over the person expected to be there at my next pick - I'd like
> that to be shown, we may need some design input"

## Why it matters

**This is the number that actually answers the question a drafter is asking.** Not "how good is this
player" but "how much better is he than what I can still get next time round." VBD measures against
a season-long replacement level; this measures against *this draft, this slot, right now*. It is the
opportunity cost of the pick.

It is also the one figure in the app that no public ranking can produce, because it depends on the
founder's own slot, his league size and who has already gone. Consensus can never compute it. That
makes it the most defensible thing this product could put on screen.

## Initial read

Not the founder's own words — PM's read.

**The founder is right that the ingredients exist, and it is worth being precise about what is and
is not already there.**

- **Availability at the next pick: built and real.** `frontend/ui/data/liveAvailability.ts` computes
  survival probability to a given pick from the shipped sigma readings, and the scarcity panel
  already uses it to count players under 50% to reach the next pick.
- **VBD per player: built** (`board.json:players[].vbd`).
- **The subtraction itself: not built.** Nothing currently computes *value of this player minus
  expected value of the best player still available at my next pick.*

So it is one derived quantity away, and the derivation is where the care goes. "The player expected
to be there" is a distribution, not a single name. Options: expected value over the availability
distribution (most honest, hardest to read), the best player above a survival threshold (simple,
threshold is arbitrary and must be stated), or a range across the three sigma settings (matches what
the Predictions tab already does and the founder already likes).

**The uncertainty is the point, not a caveat.** The founder specifically praised the deviation
control in Predictions. This number inherits the same uncertainty, and it should be shown the same
way — as a range across sigma, never as a single confident figure.

**Design input requested by the founder** — carry that through. Whatever is chosen, the screen must
state which assumption produced the number.
