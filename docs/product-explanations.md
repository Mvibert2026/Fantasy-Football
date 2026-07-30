# Product explanations — the "why does it do that" file

**Purpose.** Every nuance about how this product behaves that has so far only been explained in chat.
Chat is discarded; these are not.

**Founder's instruction, 2026-07-30:**

> "all of these nuances you share about how the product itself works need to be recorded, we'll likely
> need a prodcut tour on the front end at some point (don't build it now but plan for the need) they
> can also be tool tips or similar."

**So this file has two jobs.** Right now it is the reference for anyone — human or agent — who needs
to explain a behaviour without re-deriving it. Later it is the **source content for an in-app product
tour and tooltips.** Written in founder-facing language for that reason: no jargon, no statistics
notation, one idea per entry.

**Not to be confused with:**

- `docs/assistant-context.md` — what the in-app assistant reads to answer "why" questions. Narrower,
  and edited in place when superseded.
- `docs/strategic-insights.md` — what the research measured. This file explains the *product*; that
  one records *findings*.

**Rule:** each entry names where it would surface. An entry with no surface is a note, not a tooltip.

---

## A. The rule underneath everything

### A1. The app never makes a number up
**Surface: tour, opening card.**
Where a value is missing, the app says so in place, and says why — rather than showing a plausible
default. This is why you see "not computed" text where other tools would show a confident figure. It
is deliberate: a number that looks computed and isn't is worse than a visible gap, because you would
act on it during a draft.

### A2. Every number traces back to where it came from
**Surface: hover, on any figure.**
Each displayed value knows which backend field produced it. That trace currently renders as visible
text (`board.json:players[].vbd` and similar) — which is being moved behind a hover, not deleted. The
rule stays; only the audience changes.

### A3. A control that can't do anything isn't shown as a control
**Surface: tour.**
Buttons that do nothing were removed rather than greyed out. If a capability isn't built, the app says
so in plain text instead of offering a dead affordance.

---

## B. The board and the numbers on it

### B1. Why our own rankings aren't shown yet
**Surface: tour; Board empty-state.**
The bottom-up model does not yet beat consensus at any position, so showing it would give you a
worse board with more confidence. It gets shown when it earns it, not before.

### B2. What VBD means here
**Surface: tooltip on the VBD column; glossary.**
Points above what a freely-available replacement player at the same position would score. It is what
makes players at *different* positions comparable — a running back and a receiver can't be compared on
raw points, but they can be compared on how far above their own position's replacement level they sit.

### B3. Why VBD is about to show two numbers
**Surface: tooltip on the VBD column, once shipped.**
"Value at his position" and "value against what else you could do with that roster spot" are different
questions. A tight end can look strong on the first and weak on the second, because only one tight end
starts and a flex spot is usually better spent elsewhere. Both get shown, labelled, never blended.

### B4. Where replacement levels come from
**Surface: tooltip; glossary.**
RB30 / WR40 / TE10 / QB10 — derived from this league's ten teams and its actual starting lineup, not
from the twelve-team convention public boards assume. Public boards are solving a different league's
maths.

### B5. Why DEF has no value number, permanently
**Surface: tooltip on any DEF row.**
No defensive scoring data is ingested, so there is nothing to measure a replacement level against.
Publishing a DEF rank would invite a value calculation whose other half doesn't exist. It is a
decision, not an oversight, and it won't change without new data.

### B6. Every player at the same positional rank gets the same projection
**Surface: tour; player card.**
The board has no opinion about whether a specific player is better than his consensus rank suggests.
It has an opinion about what a given *rank* is worth under this league's rules. This is why the app
will not answer "do you like this player more than the experts do" — that data doesn't exist here.

---

## C. Availability — the most trustworthy thing in the app

### C1. Why availability is more reliable than projections
**Surface: tour; Availability screen header.**
It depends only on how a draft room behaves, not on predicting football. It doesn't need to know who
will be good — only who tends to get picked when. That makes it the strongest output the project has.

### C2. Pre-draft numbers versus live numbers
**Surface: tooltip on availability figures.**
Before the draft, availability is an average across every possible draft — planning numbers. Once
picks start, it recomputes against what has actually happened. Don't read the pre-draft figure as live
odds.

### C3. Why availability changes when you change your draft slot
**Surface: tooltip near the slot selector.**
Availability is about *your* picks. Change the slot and your pick numbers change, so the question
"who survives until my next turn" has a different answer. The app recomputes rather than showing you
another slot's numbers.

### C4. Why "behind pace" sometimes disappears
**Surface: tooltip in the Scarcity tab.**
Auto-fill inserts honest placeholders rather than inventing who was taken. That makes pace
uncomputable — not zero, uncomputable — so the app withholds it and says why instead of showing a
number built from two different populations.

---

## D. Recommendations and strategy

### D1. Why the recommendation sometimes isn't the highest VBD player
**Surface: tooltip in the Recommend tab.**
Because who is likely to survive until your next pick matters as much as who is best now. If the
better player is very likely to still be there and the second-best is not, taking the second-best is
correct. The panel explains this whenever it departs from raw value.

### D2. Choosing a strategy is a preference, not an edge
**Surface: strategy selector, permanent note.**
Zero RB was simulated against plain value-based drafting and the difference was indistinguishable from
zero. The selector changes how recommendations are ordered because you may want it to — it does not
claim to win you more games. That is stated on screen every time it fires.

### D3. Late rounds are a volume game
**Surface: tour; Recommend tab, later rounds.**
Roughly one in four picks from round ten onward returns a startable player — a rate that held on a
held-back test season. Across six late picks that's about one and a half hits with no skill at all. So
taking enough shots and cutting fast beats agonising over any single one.

---

## E. The assistant

### E1. What it can and can't see
**Surface: assistant panel, first-run note.**
It sees what your screen shows: current pick, roster needs, the live recommendation and its reason,
scarcity, and what's likely available at your next pick. It does not silently reach for anything
beyond that, and it won't invent a figure that isn't in front of it.

### E2. Conversation history is context, not evidence
**Surface: assistant panel.**
It remembers the last several turns so follow-ups make sense. It will not treat something said earlier
in the conversation as a fact about football.

### E3. Nothing you ask is stored
**Surface: assistant panel, privacy note.**
Questions go from your browser to the model and back. Nothing is logged, saved, or committed —
a deliberate decision, made knowing it costs us the ability to improve the assistant from real usage.

---

## F. Player card

### F1. Why an archetype is often missing or vague
**Surface: hover on the archetype chip.**
The current labels are weak: one label covers roughly two thirds of running backs, and about a third
of players match no label at all. The chip shows what exists and admits when nothing does, rather
than forcing every player into a bucket. The taxonomy is being rebuilt.

### F2. Why some players have no projected points
**Surface: tooltip where a projection is absent.**
Players outside the depth the projection curve was fitted on carry no honest confidence range, so no
point estimate is shown. The curve explains only 16–27% of what a player actually scores, so treat any
single projection as noisy and prefer the range.

---

## Backlog — explanations that will be needed but aren't written yet

- What the Insights tab shows, once its scope is decided.
- The periodic-table grid: what a cell encodes and why position colours are used the way they are.
- The news feed: what makes an item appear.
- Save-state and league sharing, if Yahoo access stays closed.
