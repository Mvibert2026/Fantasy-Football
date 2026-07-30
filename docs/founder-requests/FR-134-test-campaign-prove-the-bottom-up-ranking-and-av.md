---
ID: FR-134
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: pm to scope, then parallel agents
---

## Request

Founder's own words:

> "we probably should work our way through all the testing for bottom up and availability, make sure
> the core of the product works I think we have a ton of ideas to test, let's run a bunch of agents
> together to test them (after we finish what was in flight)"

And, separately, on where the thinking should go:

> "Make sure someobdy with high thinknig looks at availability - ADP probably more important than
> consensus, we have lots of sources."

## What this is

A **campaign**, not a task: work the accumulated test ideas for the two subsystems that constitute the
product's core — the bottom-up ranking and the availability model — in parallel, and establish whether
the core actually works rather than whether it runs.

Explicitly sequenced by him **behind the in-flight frontend and design work.**

## Already underway

The second half is dispatched. **Strategist — Opus, xhigh, the highest thinking tier in the roster —
is working thread 119 right now**, on exactly the question he names: whether availability's opponent
model should draft from ADP rather than expert consensus, and whether sigma should be per-player
rather than one global guess. Its mandate is to *attack* the founder's position, not ratify it.

"We have lots of sources" is also already measured: `ffc_adp_snapshots` carries this league's exact
format (half-PPR, 10 teams), `adp_snapshots(mfl_proxy)` is a second independent ADP source, and both
were re-ingested 2026-07-30 and are current.

## Scoping needed before dispatch

The test ideas are spread across `docs/test-registry.md`, the FR backlog, and thread replies. Before
running "a bunch of agents together" they need to be collected into one list with, per item, what
would falsify it and which baseline it must beat — **§6.5's baseline rule applies to every one of
them: the headline result is the comparison, never the raw number.** Dispatching parallel agents at an
uncollected list produces parallel opinions, not evidence.

Statistical exposure is high here and named in CLAUDE.md §6.3: ~30 candidate factors at p<0.05 yields
~1.5 false positives by chance. A campaign that runs many tests at once is exactly the setup that
requires correction for multiple comparisons, and a holdout that is touched once.
