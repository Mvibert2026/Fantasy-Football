---
ID: FR-059
STATUS: NEW
PRIORITY: HIGH
ROUTED-TO: strategist, ranker
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Test the recommendation's four constants against plain VBD — they are arbitrary

Founder's own words:

> "Those seem like random adjustments.
> And odd given our research suggested vbd.
> The chatbot should be able to discuss the pick.
> We need to test those adjustments."

## Why it matters

**He is right on the facts and the framing.** `frontend/ui/data/recommendation.ts` adds four
hand-picked numbers on top of VBD — `+8` unfilled position, `+18` tier-1 TE, `−25` QB before round 6,
and a DEF term that is unreachable. **None was fitted to anything.** The module's own docstring calls
itself *"a stopgap, not a validated model… it has not been backtested the way the rankings themselves
have."*

**The contradiction he spotted is the important part.** VBD is the researched quantity — it is what
the board is built on and what the ranking work measures against. These constants override it, and
they were chosen so the panel would sort sensibly. So the one screen used under a clock is the one
place where measured work is overridden by guesses.

Two of the four also sit awkwardly against today's findings: the `+18` tier-1 TE bump points at the
top of the position, while pass 2 found the free window is TE7-10 (rounds 8-11); and the `−25` early
QB penalty is a flat constant in a market whose QB premium collapsed from −67 to −4 across 2021-2025.

## Initial read

Not the founder's own words — PM's read.

**"Test them" is answerable with tools that already exist, and that is the point.** `src/draft_sim.py`
simulates full drafts with opponents and scores the resulting rosters — it was built precisely to
price opportunity cost under contention, which is the question here. So the test is:

**Does the recommendation with these four constants produce better rosters than plain VBD?**

Arms worth running, at minimum: plain VBD · VBD + all four · each constant ablated one at a time
(that is what isolates which term, if any, earns its place) · and the existing strategy baselines
already in the simulator.

**This is registered before it is run.** `strategist` designs it and commits the stopping condition
in advance; `ranker` may execute; neither grades its own homework. The decision rule must be written
down first — otherwise "the constants look fine" becomes the finding by default.

**Expect them to lose, and plan for that.** The likely outcome is that some or all fail to beat plain
VBD on a holdout. **If so, delete them.** A simpler model that matches a tuned one is the better
model, and this project's own guardrails say every added parameter must earn its place against a
holdout, not against training fit.

**Note the sample constraint honestly:** the simulator's opponent noise is itself unfitted
(`draft_sim.py:17-27`), so results across a sigma sweep are the finding, not results at one setting.

## Interaction with FR-058, in flight now

FR-058 (the panel explains itself when it overrides VBD) is being built as this is written. **They do
not conflict — they compound.** The panel makes every override visible to the founder in the moment;
this decides whether the override should exist at all. If the constants are deleted, the panel
correctly falls silent, which is the honest end state.

## The chatbot half

> "The chatbot should be able to discuss the pick."

Currently it cannot: the assistant retrieves through seven regex templates (FR-048) and the
recommendation is not among them. **Discussing a pick means the recommendation's own breakdown —
which terms fired, what was displaced, by how much — has to be retrievable context.** That is the
same structured-explanation object FR-058 is building for the panel. Build it once, render it twice:
on screen and to the assistant.

**Dependency: this is worth doing only after this ticket resolves.** An assistant fluently explaining
four untested constants would be the most persuasive way yet to launder a guess.
