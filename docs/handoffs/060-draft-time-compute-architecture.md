---
ID: 060
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: 059 (on-deck recommendations), 045 (lookahead), draft-day viability of everything computed live
---

## Founder question

> "How will the app do this thinking during the draft? Continually run projections, how fast, at
> who's guidance and request?"

This has never been decided. Threads 045 and 059 both assume live computation without specifying when
it runs, what triggers it, or what happens when it does not finish. Decide it here, before either is
built on an unstated assumption.

## The insight that should shape the design

**The scarce resource is not compute. It is freshness.**

In a ten-team league with a ninety-second clock, the gap between the founder's pick 24 and his pick 38
is roughly **twenty minutes of wall clock**. That is an enormous compute budget by any standard. The
problem is that every opponent pick invalidates part of the state, so the question is not "can we
afford to compute this" but **"what is still true when the founder looks at it."**

Design for staleness, not for speed.

## Proposed tiering — challenge it if you disagree

Four tiers by cost, each with a latency target and a defined degradation.

| Tier | Work | Target | On each pick |
|---|---|---|---|
| **0** | Board bookkeeping — remove player, update roster counts, position remaining, tier depletion, pace | **<50 ms** | Always, synchronously. Never allowed to be stale. |
| **1** | Hazard weights and survival probabilities to the founder's next pick | **<1 s** | Always. O(n) over ~350 players; vectorise it. |
| **2** | Forward Monte Carlo for the on-deck branch tree (thread 059) | **seconds** | On each pick if it fits the interval; otherwise on demand. |
| **3** | Full-draft roster-value simulation per candidate (059 addendum) | **tens of seconds** | Background, speculative, frequently stale — and that is acceptable *if visible*. |

**Tier 0 and 1 must never show a stale number.** They are cheap enough that there is no excuse.
Tiers 2 and 3 may be stale, and must say so.

## Speculative precomputation — the idea worth building

The model already knows which players are most likely to go next. **Precompute tier 2 and 3 results
for the top few likely branches before those picks happen.** When the pick lands, the common case is
a cache hit rather than a recompute, and the founder's on-deck view updates instantly.

Cover enough branches to capture the bulk of the probability mass; fall back to live recompute on a
miss. This converts most of the draft into precomputed work done during idle time — which is exactly
the resource the draft provides in abundance and which the current design wastes entirely.

Report the hit rate. If it is low, the branching is wider than assumed and that is worth knowing.

## Triggers — the "at whose request" half of the question

Three, and they should not be conflated:

1. **Automatic, on each observed pick.** Tiers 0 and 1 unconditionally. Tier 2 if it fits.
2. **On demand**, when the founder opens the on-deck or Predictions surface. He must be able to force
   a refresh and see when the last one completed. FR-008 is about reviewing calmly — that means
   pulling, not waiting to be pushed.
3. **Speculative**, in the background, per the section above.

**No recompute is ever triggered by the founder being on the clock.** If the only fresh numbers arrive
when his turn starts, the entire premise of FR-008 fails. Everything he needs at his pick should have
been computed during the thirteen picks before it.

## Non-negotiables

- **No part-applied recomputes.** Existing architectural principle. A recompute lands whole or not at
  all; the founder never sees a half-updated board. Confirm this is actually enforced in code rather
  than observed by convention — I suspect the latter.
- **Every derived surface carries an as-of pick number.** A tier-3 result computed at pick 24 and read
  at pick 30 must say "as of pick 24," not look current.
- **Degrade downward, never sideways.** If tier 2 cannot finish, show tier 1 with an honest marker.
  Never show an older tier-2 result styled as if it were current.
- **The real hazard model or nothing.** The Mock Lab's model-free baseline (thread 025) must not leak
  into live draft surfaces. If the real model cannot serve a request, refuse it visibly.

## What to report back

1. **Measured timings** for each tier against a realistic board — ~350 players, a ten-team league, a
   mid-draft state. Not estimates. If tier 1 cannot hit one second, say so now rather than on draft
   day; vectorising the hazard computation is likely the difference between tens of seconds and
   fractions of one, and it is worth doing before anything else here.
2. **The speculative cache hit rate** across a simulated draft.
3. **A recommendation on tier 3's cadence** — whether per-pick background recomputation is worth the
   cost, or whether it should be on-demand only.
4. **Whether "no part-applied recomputes" is actually enforced**, with evidence.

## Done looks like

`docs/adr/` entry recording the decided architecture, measured timings, and the degradation rules.
Implementation of tiers 0 and 1 to their latency targets. Tier 2 and 3 cadence decided and
documented, even if their contents are built later under 059.

**File boundary:** `src/`, `docs/adr/`. Do not touch `frontend/` — thread 059 owns the surface, this
thread owns what feeds it. Agree the contract with 059 before either lands.

---

## REVISION · Every pick recomputes — unconditionally

Founder correction:

> "Really every pick should be a recomputation, some people take longer or shorter."

**This supersedes the "if it fits the interval" language in the tier table above.** My version assumed
a comfortable and roughly constant gap between picks. That assumption is wrong, and it is wrong in
both directions at once: a manager who autopicks gives you two seconds, and a manager agonising gives
you two minutes. **You cannot schedule against a budget you do not know.**

The correct design is: **every observed pick triggers a full recompute of every tier, always.** What
varies is not *whether* the work starts but *how precise it gets before the next pick arrives.*

### The four properties this requires

**1 · Preemptible.** If pick 25 lands while the pick-24 recompute is still running, **kill it and
start again from the pick-25 state.** Do not let it finish. Do not queue.

Queuing is the catastrophic failure mode here: with fast picks you fall progressively further behind,
and the display drifts from slightly stale to badly stale while continuing to look normal. A recompute
for a board state that no longer exists has zero value and negative cost.

**2 · Cancellation is free, and here is why.** A recompute is a **pure function of board state** —
this is already established, it is the same property that makes undo-as-replay correct in the
event-sourced Mock Lab design. Nothing accumulates across recomputes, so there is no partial state to
unwind and no cleanup to get wrong. Killing a running recompute costs exactly the work already done
and nothing else. **Verify this property actually holds in the code** rather than assuming it; if any
tier carries state between runs, that is a defect and it should be reported as one.

**3 · Anytime, not all-or-nothing.** Monte Carlo is naturally an anytime algorithm and should be built
as one. Run samples until interrupted, then report **with the interval you actually earned.** Five
hundred samples produces a wider interval than ten thousand; that is not a failure, it is an honest
result at lower precision.

This is strictly better than the degradation rule I wrote above. "Could not finish, showing tier 1"
throws away real work. "Here is the answer, with a wider interval because three managers autopicked in
a row" keeps it and tells the truth about it.

**Consequence for the UI:** the as-of marker carries **precision as well as recency** — as of pick 30,
N samples, interval ±x. Precision is data, not an implementation detail, and thread 059's surfaces
should show it.

**4 · Coalesce bursts.** The founder's point cuts both ways. Slow picks hand you budget; **fast picks
arrive in clumps.** If five autopicks land in three seconds, do not start and kill five recomputes —
debounce briefly and recompute **once** from the latest state.

A whole round can pass in seconds when a league is full of autodrafters. Design for that case
explicitly and test it: replay a draft log at high speed and confirm the system stays current rather
than thrashing.

### Revised tier behaviour

| Tier | On every pick |
|---|---|
| **0** — bookkeeping | Runs to completion. Cheap enough that it always finishes; no excuse for staleness. |
| **1** — survival to next pick | Runs to completion. Vectorise until this is true. If it cannot finish inside the fastest realistic pick interval, that is a defect to fix, not a case to degrade. |
| **2** — branch tree MC | Starts unconditionally, anytime, preempted by the next pick, reports at achieved precision. |
| **3** — full-draft roster value MC | Same, at lower priority. Frequently coarse. Says so. |

### Speculative precomputation matters more now, not less

If picks can arrive in two seconds, precomputing the likely branches **before** they happen is the only
mechanism that delivers a fresh answer at high precision. On a cache hit the recompute is already done
and tiers 2 and 3 are instantly current at full sample count.

Prioritise the speculative cache accordingly — under variable pick timing it moves from an
optimisation to the primary path.

### Added to what to report back

5. **Behaviour under a fast-draft replay.** Replay a real draft log at high speed, including a burst
   of consecutive autopicks. Confirm: no queue growth, no thrash, no stale display, and correct
   coalescing. Report the achieved sample counts across the draft — the distribution of those counts
   is the honest measure of whether this design works.
