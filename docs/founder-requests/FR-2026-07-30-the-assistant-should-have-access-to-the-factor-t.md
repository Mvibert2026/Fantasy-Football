---
ID: FR-2026-07-30-assistant-access-to-factor-tests
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: librarian (content shape), then frontend (retrieval wiring)
---

## Request

> "It would be good for the chatbot to have access to these tests and reasoning."

## The mechanism already exists, and it already works

`docs/assistant-context.md` is the curated, current-state-only source the assistant reads for "why"
questions (`CLAUDE.md` §12). It exists **specifically so the assistant does not read
`decisions.md` or `test-registry.md`**, both of which carry figures that later entries overwrote.

**And retrieval demonstrably works.** On 2026-07-30 the assistant, unprompted, retrieved PR-003's
early-QB result and told the founder it contradicted the live recommendation on his screen. It was
the only surface in the product that got that right.

## The risk this request raises, which is real and was observed the same day

**The assistant paraphrased a statistical result and inverted its uncertainty.** It called −115.4 the
*"worst case"*. It is the **point estimate at σ=10**; the interval is [−176.3, −54.4]. Calling a point
estimate a worst case understates uncertainty in the flattering direction — the single most dangerous
direction for a tool the founder will draft from.

It also described "12 scenarios" as independent when the effective n is 4 — twelve cells are 4 seasons
× 3 settings of one guessed parameter.

**So the constraint is not "give it more documents."** Exposing more statistical results to a
paraphrasing layer multiplies that failure mode. The requirement is that each exposed row carries its
**interval, its effective n, and its scope** inline, in a form that survives paraphrase — so that a
model summarising it cannot drop the uncertainty without visibly dropping a field.

## What to build

1. **A curated projection of the factor ledger into `assistant-context.md`.** Current state only, per
   `CLAUDE.md` §12 — no history, no superseded numbers. One entry per settled factor decision.
2. **Every entry carries scope, disposition, number-with-interval, and effective n.** A verdict word
   alone ("NULL", "harmful") is not sufficient, because that is exactly what gets paraphrased into
   something stronger than the evidence.
3. **Scope must be inseparable from the result.** Two live examples: registry #13's NULL is about
   target-share *stability*, not target share; #28's harm was a **proxy artifact**. If the assistant
   can read either result without its scope, it will state a stronger claim than the data supports —
   and that is precisely how the recommendation card misled the founder today.
4. **Say when something has never been run.** `SPEC` status is not a result. The assistant must
   distinguish "measured and null" from "never executed", which the ledger already requires.

## What this is not

Not a request to expose `test-registry.md` or `decisions.md` directly. Those contain superseded
figures stated in the same confident voice as current ones — the exact hazard `assistant-context.md`
was created to avoid.
