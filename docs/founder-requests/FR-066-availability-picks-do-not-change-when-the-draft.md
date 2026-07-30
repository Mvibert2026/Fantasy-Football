---
ID: FR-066
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Availability picks do not change when the draft slot changes

Founder's own words:

> "When slot selection happens on the availability, it doesn't change the picks shown"

## This is the known gap, now confirmed on the live site

**Diagnosed 2026-07-29 and recorded in FR-057** — the founder has now hit it himself, which upgrades
it from a predicted consequence to an observed defect.

`data/export/availability.json`'s `by_player` is keyed by **one slot's pick numbers** — `3, 18, 23,
38, 43, 58` for the slot the export was generated at. Change the slot to 5 and the picks become `5,
16, 25, 36, 45, 56`; **none of those keys exist**, so the screen keeps showing the original slot's
picks rather than recomputing.

The selector moves everything else — board, round grid, Predictions, the draft room — because those
derive from `league.json:pick_sequence`. Availability alone cannot, because its numbers come from a
Monte Carlo simulation run in Python against a single slot.

## Status: the fix was started and then paused, by the founder

FR-057 part 1 (export every slot) ran for hours on 3,000 simulations per slot without finishing and
was **stopped at his instruction** to conserve tokens. Nothing is lost; there are simply no results.

**That pause changed the recommendation.** If a full sweep takes hours it must re-run whenever the
board changes, which is often. Browser-side recomputation — his stated preference all along — costs
once and then covers any slot, any team count, any roster shape. `client_simulation_parameters` is
already in the export and nothing consumes it.

**So: resume FR-057, and consider doing part 2 first.** That is the opposite of the original order
and it is what the measured cost argues for.

**Until then the screen should say so.** Showing another slot's picks without a word is the failure
this project treats as worst — a number that is confidently wrong. An honest "availability is
computed for slot N and has not been recomputed for your selection" is correct today and cheap.
