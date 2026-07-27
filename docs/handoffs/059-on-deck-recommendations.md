---
ID: 059
FROM: pm
TO: backend, frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: FR-006 (draft chatbot), calm-preparation use case
DEPENDS ON: 045 (simulation lookahead), 028 (Predictions tab), 049 (reasoned recommendation)
---

## Founder request

> "Some of the 'on the clock' information and potential recommendations and considerations at my pick
> would be nice instead of only on my pick. I'd like to be able to review those recommendations ahead
> of time under less pressure."

Recorded as **FR-008**. The general principle, which should shape decisions beyond this thread:
**the founder wants to do his thinking in the fourteen picks before his turn, not in the ninety
seconds of it.** Any feature that moves cognitive load out of the clock window is worth more than its
face value.

## The reframe that makes this buildable

A recommendation for pick 38, viewed at pick 24, **cannot be the same object as a recommendation at
pick 38.** Thirteen players will come off the board first and the model does not know which. Showing
the current recommendation early would be showing a confident answer to a question that has not been
asked yet — the exact failure mode this project exists to avoid.

**The correct object is conditional.** The engine already computes survival probabilities; a pre-pick
view is those probabilities turned into a small decision tree:

> *"Bowers reaches you 46% of the time. If he does, he is the pick. If he doesn't (54%), it comes
> down to Kittle or waiting on TE entirely — and if you wait, tier 2 is empty by your following
> pick."*

That is reviewable calmly, it is honest about what is unknown, and it is more useful than a single
name would be, because it is what the founder would actually be reasoning about.

## Build

### Backend — forward simulation

- **Monte Carlo, not enumeration.** Sample forward from the current board through the hazard model to
  the founder's next pick, many times. Enumerating branches thirteen picks out is combinatorially
  hopeless; sampling is tractable and gives honest frequencies for free.
- Output per candidate: **P(available at my next pick)**, and the joint structure that matters —
  which players tend to be available *together*, since "one of these three will be there" is a much
  stronger statement than three independent probabilities and is the thing a human cannot compute.
- Report **tier-level and position-level survival**, not only player-level. Far from the pick, that is
  the only thing with enough signal to say.
- **Use the real hazard model.** The Mock Lab currently runs a model-free baseline (known gap from
  thread 025) — that must not silently power this surface. If the real model cannot be wired to an
  arbitrary future pick yet, **this thread is blocked on that**, and blocked is the correct outcome to
  report. Do not substitute the placeholder.
- **Cost and cadence.** The board changes on every opponent pick. Decide whether to recompute per
  pick or on demand, and state the reasoning. If it is not recomputed continuously, **the staleness
  must be visible** — the view carries an as-of pick number, and a view computed at pick 24 and read
  at pick 30 must say so rather than look current.

### Frontend — the on-deck surface

Lives in the **Predictions tab** (thread 028, not yet built) — coordinate rather than building a
second home for it.

**Degrade gracefully with distance from the pick.** This is the core design rule:

| Distance | What is honest to show |
|---|---|
| Far (10+ picks) | Position and tier level only. *"Tier 1 TE will likely be gone; tier 2 has 4."* Player-level branches at this range are noise dressed as advice. |
| Middle (4–9) | Named candidates with survival probabilities; the top two or three branches. |
| Near (1–3) | Full conditional tree, plus the specific trade-off — the sentence from thread 049. |

- **Branches should cover roughly 80% of probability mass in two or three arms**, with the residual
  stated explicitly rather than hidden. *"Other outcomes: 15%"* is a required element, not a footnote.
- **Honest nulls apply in full.** A branch the model cannot compute renders as `not yet` or `—`. A
  confident-looking tree built on missing inputs is worse than an empty panel, and this surface is
  the most tempting place in the product to fake it.
- **Traceability footer** naming the fields feeding the tree, consistent with the pattern in thread
  058 Section F.
- The founder should be able to **open this at any point during the draft**, not only when it
  refreshes itself. Reviewing calmly is the entire point.

## Why this is worth prioritising above its apparent size

1. It is the natural home for **FR-006**, the draft-time strategy chatbot. A conversation about
   *"what happens if I wait a round?"* requires exactly this object to exist. Build this first and the
   chatbot becomes a view over it rather than a model inventing rationales — which is the failure mode
   FR-006 was recorded to prevent.
2. It converts the survival model from **a number into a plan**, which is the difference between a
   statistic and a product.
3. It is the strongest argument the product has against consensus tools, and it is only possible
   because the engine computes distributions rather than rankings.

## Done looks like

Backend: a forward-simulation endpoint returning per-candidate and per-tier survival to a specified
future pick, with joint availability structure, an as-of marker, and an explicit refusal when the
real hazard model cannot serve the request.

Frontend: the on-deck surface in the Predictions tab, distance-aware, with residual mass stated,
honest nulls, and a traceability footer.

Report the recompute cost. If it is expensive enough to affect the draft-room experience, say so and
propose the cadence rather than deciding silently.

**File boundary:** backend takes `src/`; frontend takes `frontend/`. Coordinate on the contract before
either starts — this is one of the few threads where the two halves must agree on a shape first.

---

## ADDENDUM · Roster-aware reasoning — "why I may want to consider them"

Founder clarification:

> "Showing who you think will be available and why I may want to consider them. Remember our dynamic
> recommendations should be looking at my team and doing math to understand how I should continue to
> put my team together, like bye weeks."

This absorbs the intent of thread 044 into this surface. Coordinate; do not build two roster-aware
recommenders.

### The core quantity is marginal, not absolute

A player's value to *this* roster is not his projection. It is **what he adds over the best
alternative already available to this roster at the slot he would occupy** — flex eligibility
included, since a fourth good running back on a roster starting two plus a flex is worth much less
than his projection suggests.

**Specify marginal value explicitly, and never display raw projection as if it were the reason to
draft someone.** The "why consider them" string the founder is asking for is the decomposition of
that marginal number: what slot he fills, what he displaces, and what it is worth.

### Bench value is option value, not points value

A bench player scores nothing unless a starter is unavailable or underperforming. Valuing bench picks
at their raw projection is the most common error in this class of tool. Their real contribution is
**insurance** — the value of having a competent replacement available when a starter is out — which
is a function of the starter's fragility, the position's weekly variance, and how thin the waiver
wire is in this league size.

This connects directly to the injury and suspension work in `docs/fable-mandate-2026-07-27.md`
Addendum 2. A handcuff behind a fragile starter is worth more than the same player behind a durable
one, and that is computable rather than a matter of taste.

### Bye weeks — build it, and expect the honest answer to be "smaller than people think"

Compute it properly rather than displaying a warning icon:

**Cost of a bye collision = (projection of the starter you lose that week) − (best replacement
actually available to you that week).**

That framing makes the real structure obvious, and it is not what most tools imply:

- **A bye at a deep position is nearly free.** If you roster six wide receivers, two sharing a bye
  costs approximately nothing — you start someone else.
- **A bye at a thin position is the real cost.** Your only tight end on bye means starting a
  streamed replacement, and the gap is large.
- **The cost is concentrated, not distributed.** It is not "a bad week," it is one specific week where
  one specific slot is worse.

**State the expected magnitude honestly, and quantify it before the UI implies anything.** My strong
prior — register it and test it — is that **drafting a materially worse player to avoid a bye
collision is almost always wrong**, and that the correct output is a *note about a future roster
management cost*, not a downgrade to the player's value. If the computed magnitude contradicts that,
say so; that would be a genuine finding.

The one case that likely does justify a real adjustment is a **collision at a position where you will
roster only one or two**, since there the replacement is a waiver-wire body rather than a bench
starter.

### "How should I continue to put my team together" — the multi-pick question

This is the deepest part of the request and the most valuable. He is not asking who to take; he is
asking what shape his roster is heading toward and whether this pick serves it.

**The forward simulation specified above already provides the machinery.** Extend it: for each
candidate available now, simulate the *remainder of the draft* — opponents via the hazard model, the
founder's own future picks under a stated policy — and report the **distribution of final roster
value** under each immediate choice.

That answers "how should I continue to put my team together" with arithmetic instead of heuristics,
and it is the object the FR-006 chatbot needs to answer *"what happens if I wait a round?"*

**Three honesty requirements, non-negotiable:**

1. **State the self-policy assumption.** Simulating your own future picks requires assuming how you
   will behave — following the recommender, taking best available, or filling needs. The result
   depends on it. Name the assumption on the surface; do not bury it.
2. **Model error compounds with depth.** Each simulated round stacks hazard-model error on top of
   projection error. End-of-draft roster value estimates will have wide intervals. **Show the
   intervals.** A point estimate of final roster value would be the most overconfident number in the
   product.
3. **Report the comparison, not the winner.** The useful output is *"these three candidates produce
   statistically indistinguishable rosters; this fourth one is meaningfully worse"* — which is an
   honest reading of a wide interval and is more decision-relevant than a ranked list that implies
   precision the simulation does not have.

### What the founder should see

For each likely-available candidate, a short reason built only from computed quantities:

> *"Fills your empty TE. Worth +18 over your next-best tight end. Tier 2 is empty after him. Bye 10
> collides with Chase — one week, and you have bench depth at WR."*

Every clause traceable to a field. **No clause generated by a model that did not compute it** — this
is the FR-006 hallucinated-rationale risk arriving early, on a surface that is being built now.
