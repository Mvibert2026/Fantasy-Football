---
ID: FR-119
STATUS: PARTIAL
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
---

## Request
Record product behaviour explanations; plan for an in-app product tour and tooltips

Founder's own words:

> "all of these nuances you share about how the product itself works need to be recorded, we'll likely
> need a prodcut tour on the front end at some point (don't build it now but plan for the need) they
> can also be tool tips or similar."

## Why it matters

Every explanation of *why the product behaves the way it does* — why DEF has no value number, why
availability is more trustworthy than projections, why the recommendation sometimes departs from raw
VBD, why an archetype chip is often blank — has so far existed only in chat. Chat is not stored
(FR-103, founder's decision) and is invisible to every other agent. Each of those explanations was
derived from a real decision or a real measurement, and re-deriving them costs a session apiece.

Two consequences if this is not recorded:

1. Agents answer the same "why does it do that" question differently across sessions, because each
   one reconstructs the reasoning from scratch.
2. When the product tour is eventually built, its content has to be written from nothing — at which
   point the honest, measured explanations get replaced by plausible-sounding marketing copy, which
   is exactly the failure mode §11 of `CLAUDE.md` prohibits.

## Initial read

**Two parts, deliberately separated by the founder himself.**

**Part 1 — record it. Done this session.** `docs/product-explanations.md` now carries 18 entries in
six sections (the never-fabricate rule; board and numbers; availability; recommendations and
strategy; the assistant; player card), each written in founder-facing language and each tagged with
the surface it would appear on (tour / tooltip / hover). It also carries a backlog of four
explanations that will be needed but cannot be written yet, because the underlying feature is
undecided (Insights tab scope, periodic-table cell semantics, news-feed inclusion rule, save-state).

**Part 2 — build the tour. Explicitly deferred by the founder: "don't build it now but plan for the
need."** Nothing dispatched. What "plan for the need" costs now is close to zero and is already
paid: the file is written in tour-ready form (one idea per entry, no statistics notation, surface
named), so the eventual build is a rendering job, not a writing job.

**Standing, not one-off.** This is the kind of request that recurs every session rather than
completing once. Treat it as an operating rule: when a PM or specialist session explains a product
behaviour to the founder in chat, that explanation gets appended to `docs/product-explanations.md`
before the session ends. Same discipline as `docs/strategic-insights.md`, different subject —
that file records what the research *measured*, this one records how the product *behaves*.

**Interaction with the design round.** Item 1 of `docs/design/PROMPT-2026-07-31-full.md` asks design
to build a hover-disclosure pattern for provenance and explanations. That pattern is the delivery
vehicle for most of the `Surface: hover` and `Surface: tooltip` entries here. Sequencing: design
answers item 1, then tooltip content comes from this file rather than being invented at build time.
The `Surface: tour` entries have no vehicle yet and stay parked until the founder asks for one.

**Not to be confused with `docs/assistant-context.md`.** That file is what the in-app assistant reads
at runtime to answer "why" questions — narrower, current-state-only, edited in place. This file is
the fuller human- and agent-facing reference. If they ever disagree, the assistant file is the one
that must be corrected, since it is the one a user sees answers from.
