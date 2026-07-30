---
ID: FR-051
STATUS: SHIPPED
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Show value over the player expected at my next pick

Founder's own words:

> "I think we also already have value over the person expected to be there at my next pick - I'd like
> that to be shown, we may need some design input"

## Why it matters

**This is the number that actually answers the question a drafter is asking.** Not "how good is this
player" but "how much better is he than what I can still get next time round." VBD measures against
a season-long replacement level; this measures against *this draft, this slot, right now*. It is the
opportunity cost of the pick.

It is also the one figure in the app that no public ranking can produce, because it depends on the
founder's own slot, his league size and who has already gone. Consensus can never compute it. That
makes it the most defensible thing this product could put on screen.

## Initial read

Not the founder's own words — PM's read.

**Corrected 2026-07-29, same day, by the founder.** The PM first specced this as a subtraction —
this player's VBD minus the expected value of the best player still available next turn — and shipped
a long argument about how to compute the difference. That was over-built. His correction, verbatim:

> "Not subtracting one from the other, just another data point I can use while drafting and maybe we
> put into our suggestion algorithm"

**So: show the reference point, do not do the arithmetic for him.** What is wanted on screen is *who,
and how good, is likely to still be there at my next pick.* He does the comparison himself, in his
head, against whoever he is considering. A single derived "advantage" number hides the inputs; two
plain numbers side by side do not, and he has said repeatedly that he wants to see what a figure is
made of.

**What exists, measured:**

- **Survival probability to a named pick: built and real.** `frontend/ui/data/liveAvailability.ts`
  computes it from the shipped sigma readings, and the scarcity panel already counts players under
  50% to reach the next user pick. So "who is likely to be there" is already computable today.
- **VBD per player: built** (`board.json:players[].vbd`), and already a sortable column in Prep
  (`Board.tsx:99`) though not yet in the draft room (FR-050).

So the display is close to free. The open questions are presentational: best available at next pick
overall, or one per position? A name, a value, or both?

**The uncertainty travels with it.** The founder specifically praised the deviation control in
Predictions. This figure depends on the same assumption about how closely opponents follow
consensus, and should be shown the same way — as a range across the sigma settings, never a single
confident number. FR-047 (deviation widening later in the draft) changes this figure directly.

**"Maybe we put into our suggestion algorithm" — noted, and it is the more consequential half.**
The current recommendation runs on four hand-picked constants that have never been backtested
(`frontend/ui/data/recommendation.ts`). Adding a genuinely measured input to it is an improvement in
principle and a model change in practice: **it must be registered with `strategist` before it ships**,
not tuned until the output looks sensible. Display first, model second.

## Resolution (2026-07-30, frontend)

Built per `docs/design/DRAFT-MIDDLE-PANE.md` §1.2, "show the reference point, do not do the
arithmetic" — no subtraction, two plain figures side by side (CONSIDERING / LIKELY THERE AT
&lt;pick&gt;), each with a real name, position and VBD. Renders only in the base on-the-clock "this
pick" state (see the code comment on `referencePoint` in `DraftRoom.tsx` for why it isn't
generalised into the look-ahead branch — a deliberate scope limit, not an oversight).

**One divergence from the mock, disclosed rather than silently matched:** the design mock's
illustrative "VBD 54.1 · 48.9–58.2 across σ" range appears to be placeholder numbers — VBD is a
static per-player `board.json` field, not sigma-dependent, so a real sigma-swept VBD range isn't a
computation this data supports. Built instead as a **survival-probability range** (sigma 5/10/20
spread) for the same selected player, reusing the exact idiom `Predictions.tsx`'s own `RangeCell`
already ships (`ReferenceSurvivalRange` in `DraftRoom.tsx`). Real, sourced, traceable — the
uncertainty travels with the figure, per the ticket's own instruction, just expressed on the
quantity this build can actually measure.

**"Likely there" selection rule:** the highest-VBD available player (excluding the one already
being considered) with at least 50% live-adjusted odds of surviving to the pick in question —
`findLikelyThereCandidate`, matching `scarcity.ts`'s own `under50ByNext` convention. Null (an honest
"no available player has even odds") when nothing clears that bar, never a forced pick at whatever
odds happen to be highest.

**Display only, not fed into the recommendation** — the ticket's own instruction, unbuilt
deliberately; would need `strategist` registration first.

Tests: `frontend/ui/__tests__/draft-room-middle-pane-tabs.test.tsx`. Screenshot:
`frontend/e2e/artifacts/middle-pane-1-recommend-this-pick.png`.
