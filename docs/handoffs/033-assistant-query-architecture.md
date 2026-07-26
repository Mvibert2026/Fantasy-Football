---
ID: 033
FROM: pm
TO: strategist, backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: the assistant rebuild sprint
---

## Ask

Specify — do not yet build — an LLM-backed assistant that can query the backend to answer questions.
`strategist` writes the spec as an ADR; `backend` reviews it for feasibility and answers the data
questions inside it. Founder has asked for this and reversed the standing deferral (see D-014).

**The architecture to spec is a query interface, not a narrator.** That distinction is the entire
content of this thread.

## The two architectures, and why only one is safe

**Narrator (deferred, and should stay deferred).** The model receives facts and writes prose about
them. It decides what the facts *mean*. This is what `narrate.py` reserves space for and what the
code's own comment warns against: *"A language model asked to narrate will produce fluent, confident,
causal sentences whether or not the underlying data supports them."* That warning is correct and this
thread does not reverse it.

**Query interface (what to build).** The model receives a question and a set of typed tools over real
data. It decides *what to look up*, calls the tool, and reports what came back. It never decides what
is true — the database does. Provenance is structural: every number in a response arrived through a
named tool call against a named field.

The second is not a compromise on the four principles. It is **the most literal implementation of
Principle #1 the product has**: no rendered value without a named backend field behind it, enforced
by the fact that the model has no other way to obtain a number.

## What to specify

**1. The tool surface.** A closed set of typed queries over the export artifacts and, where justified,
the database. Each returns structured data with field names attached, never prose. Candidates:
look up a player's board row · availability at a pick · replacement level for a position ·
the derivation behind a rank · roster state for a team · a registered null and why it is null ·
a glossary term. Specify the full set; a closed surface is what makes the behaviour auditable.

**2. The hard constraint — no interpolation between retrieved facts.** The model may report what a
tool returned and may combine returned values arithmetically where the arithmetic is specified. It may
**not** produce a causal or evaluative claim that no tool returned.

Concretely: *"Player X has a 33% chance of surviving to pick 23, from `availability.json:p_survive`"*
is legitimate. *"Player X is undervalued by the market"* is not, and the reason is specific rather
than stylistic — the board holds **no player-level opinion at all**. `evaluative_adjustment` is
always null by design. Every player at the same consensus positional rank receives an identical
projection. So that sentence is not merely unsupported, it is a claim about a quantity the system does
not compute.

**3. Refusal behaviour.** When no tool can answer, it says so and names what is missing. Specify the
standing data traps it must volunteer unprompted: no market ADP exists for this league; the 2003–08
target and air-yard hole; depth charts ending 2024; seven of nine opponents known only by draft slot;
2025 sealed as a holdout; availability currently **uncalibrated** at 1 of ~30 mocks.

**4. Provenance rendering.** Every response carries its sources — field names, artifact, and the
`generated_utc` of the artifact read. This is also what makes the diagnostic use case work: the
founder's stated purpose is learning what is wrong, and *"that came from `board.json:vbd_ci_low`"*
sends them to the right file, while *"looks like a projection issue"* sends them nowhere.

**5. Evaluation.** How would we know it is behaving? Propose an adversarial test set of questions
designed to bait unsupported claims — "who's a sleeper", "is X better than Y", "why did the model get
this wrong" — with the correct answer being a refusal plus a named gap. Wire it into the suite. A
model that never refuses has failed.

**6. Cost and latency.** Per-query API cost, expected calls per question, whether a cheap tier
suffices for tool selection. Specify a budget, since this is the first component with a
per-interaction cost.

## Questions for `backend`

- Can the existing exports serve this, or is a query layer needed?
- Should tools read `data/export/<league_id>/` or the database directly? Exports are safer — already
  contract-versioned and null-marked — but may be too coarse.
- Does the identity hub resolve free-text player names well enough for a user typing "CMC"?

## Explicitly out of scope

Do not build anything yet. Do not touch `narrate.py`'s layer 2. Do not add a renderer that turns facts
into prose. The output of this thread is an ADR with an evaluation plan attached — framework first,
defended, then build. That is the sequencing this project has held everywhere else and a more capable
component is not a reason to abandon it.

## Done looks like

An ADR at `docs/adr-drafts/`, reviewed by `backend` for feasibility, with the tool surface enumerated,
the no-interpolation rule stated as a testable property, the adversarial evaluation set drafted, and a
cost estimate. Then it comes back to the founder as a build decision.
