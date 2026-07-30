---
ID: FR-102
STATUS: NEW
PRIORITY: MEDIUM-HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Should a positional run flip to negative momentum once value piles up elsewhere?

Founder's own words:

> "at some point should a positional run go negative momentum because so much value is elsewhere?"

## Why it matters

A run does **two things at once**, and the app currently models one of them explicitly:

1. **The run position depletes**, so the player available at your next pick there is much worse than
   expected. That is urgency to take one now.
2. **Every other position does not deplete**, so good players there are still falling. That is value
   accumulating elsewhere — the founder's point.

`src/live_availability.py:305` already computes `R(p) = 1 + delta * z(p)`, where `z(p)` is the
standardised excess of observed over expected picks at that position across a rolling window,
clipped at ±`RUN_CLIP`. **`z` is symmetric by construction**: a run at RB pushes `z(RB)` positive
*and* `z(WR)` negative in the same calculation. So the model already knows that a run at one position
means survivors at the others.

## The real question, restated

The founder is not asking for a new signal. He is asking whether the **recommendation** flips —
whether there is a point at which the accumulated value elsewhere outweighs the scarcity urgency at
the run position.

**It should flip, and it should flip on its own.** Scarcity only matters if the player is worth
having: once a position is picked over, the marginal player there has low value-over-replacement, and
no availability multiplier should make a low-value player the right pick. If value and availability
are combined multiplicatively, the crossover is automatic and needs no "negative momentum" rule at
all.

**So the test is not "should we build this" — it is "does the existing recommendation already do it,
and if not, why not."** If a special-case rule turns out to be needed, that is evidence the two
inputs are being combined wrongly, not evidence that a run rule was missing.

## Initial read — where it could plausibly be broken

Not the founder's own words — PM's read. Three candidates, in order of suspicion:

1. **The unvalidated recommendation constants.** `frontend/ui/data/recommendation.ts` carries flat
   additive adjustments — roughly `vbd + 8 (unfilled slot) + 18 (tier-1 TE) − 25 (QB before round 6)`.
   Flat additive terms do not scale with how depleted a position is, so they can hold a
   recommendation on a run position past the point where the value has gone. **PR-007 registered a
   test of these constants against plain VBD and it has never been run.** This is the most likely
   culprit and the cheapest thing to check.
2. **`delta` and `RUN_CLIP` calibration.** If the run multiplier is clipped tightly, the availability
   signal may be too weak to move the recommendation either way, making the crossover invisible
   rather than absent.
3. **Whether the recommendation consumes availability at all**, or only reports it alongside. If they
   are computed and displayed independently, no crossover can occur by construction.

## What a good answer looks like

Not a yes/no. A **crossover point**: at what degree of positional run does the recommended pick move
off the run position, expressed in something the founder can act on — e.g. "after N consecutive RBs
inside a window, the recommendation should and does switch to the best WR." Then whether the app
actually does that today.

If the crossover exists and is correctly placed, the answer is "already handled, here is where."
If it never crosses over, that is a live bug in the recommendation and the most draft-relevant one
found so far.
