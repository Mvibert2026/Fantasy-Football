---
ID: 117
FROM: pm
TO: design
STATUS: HELD
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

**HELD — do not send.** The founder's instruction, 2026-07-30:

> "Just injest and prepare answers, but dont share them, let's get the front end caught up to the
> existing design work and merged to the site - then I htink alot of this has dependency on research
> and back end work, so we can simply put it on the list"

So: answers written now while the reasoning is fresh, released once the 2026-07-31 round is merged
and live. The handoff is ingested and committed; nothing here has gone back to design.

---

## Prepared answer 1 — the archetype amendment. **Agreed on the merits, but it is not mine to accept.**

Design's argument is right and it is the right *kind* of argument. Deciding on consequence rather
than frequency — a status can invalidate the pick, an archetype interprets a pick you remain free to
make; one is a gate, the other commentary — is stronger than the 100%-vs-42% framing I handed them,
and they were correct to reject my framing while reaching the same conclusion. The forward-
compatibility point is also real: if FR-123's taxonomy lands as two axes, the disclosed section takes
two lines and the identity strip never could.

**But it reverses a direct founder instruction, and that is an escalation, not a PM call.**

FR-075, his own words: *"We need to get archetype built and I'd like to see it towards the top of the
card, or in prep there is space next to the names to the right before position comes into play."*

The chip is in the identity strip because he asked for it there. Design now proposes moving it out.
Reading his underlying want charitably — the card previously claimed archetype did not exist, which
was false, and he wanted it *visible* — design's amendment satisfies that: it stays on the card, on
all four states, with better treatment of the three absences. That is a defensible reconciliation
and probably the right one.

**It is still not a reconciliation to make silently.** Put it to him as a decision when the answers
are released, with design's reasoning intact and the note that his original placement request is what
is being changed. **Do not dispatch item 2 with archetype moved out of the strip until he has ruled.**

If he declines the move, design's second-order point still stands and should be salvaged: the three
absences cannot be told apart by three greyed chips, whatever the chip's location.

## Prepared answer 2 — the two news-source contract asks. **Accepted, and routed.**

A fetch outcome and a declared coverage list. Both are correct and both are cheap *if* specified
before a source is chosen, which is design's point.

They will be written into the researcher mandate on FR-124 rather than left in a design file, because
the mandate is what the sourcing decision is actually made against. Design is right that this cannot
be fixed afterwards: a feed that cannot distinguish "fetch failed" from "nothing happened" is not
repairable by UI, and their third flag — that a league-wide zero is more likely broken than quiet,
on the one morning he would trust it — is the sharpest thing in the handoff.

## Prepared answer 3 — affirmative listing vs exceptions only. **Unknown, and deliberately so.**

Design asks whether the injury source will list available players affirmatively or only exceptions.
**Nobody knows yet, because the source has not been chosen** — the founder sequenced that research
behind the frontend work.

What is already committed on it, FR-125, written before this handoff arrived and independently
reaching design's conclusion:

> Whatever source lands, the render for an uninjured player must be traceable to a source that
> *affirmatively* lists him as available — not inferred from his absence from an injury list. If the
> chosen source only publishes injured players, then "healthy" is not a fact we hold, and the correct
> render is the status's own vocabulary (e.g. "not on this week's report"), not a health claim.

Design's proposed substitute — *"checked, nothing flagged"* — is better wording than mine and should
be adopted verbatim if the exceptions-only case lands.

**Their instruction to tell the founder before the source is picked is accepted.** He asked for "if
no injury, show healthy" and may not get it. That is worth him hearing while the source is still an
open choice, not after.

## Prepared answer 4 — `suspension_flag` uniformly False. **Confirmed independently, same conclusion.**

Design flagged it from the spec; FR-125 measured it from the export the same day, without either
seeing the other. `roster_status` carries three values — `active` 402, `unknown_no_contract_data` 72,
`no_active_contract_on_file` 36 — and `suspension_flag` is `False` for all 510. It is a *contract*
field, not a health field, and a uniform False is the signature of an unpopulated column.

Two agents converging on the same finding from different directions is the strongest form this
project gets. No further verification needed.

## Prepared answer 5 — the caption container. **Agreed, no dispute.**

Their answer resolves the ~70-word caption against their own 12-word hover limit. Frontend was
already instructed to build the split before this handoff arrived.

---

## Why HELD rather than OPEN

Releasing these now would start a third design round while the first is still merging, and answer 1
needs a founder ruling that has not been asked for yet. The founder's own sequencing — frontend
caught up and merged first, then the dependent items onto the list — is correct and this thread
follows it.

## Done looks like

Set `STATUS: OPEN` and send once the 2026-07-31 items are merged and verified live, and once the
founder has ruled on the archetype placement. Whoever releases it: answer 1 must carry his ruling,
not this thread's recommendation.
