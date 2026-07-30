---
ID: FR-2026-07-30-recommendation-logic-is-inverted
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat, live Draft-mode screenshot
RAISED: 2026-07-30
PRIORITY: HIGHEST — this is question 3 of the founder's bar, observed failing
NEEDS: ranker + strategist
---

## Request

Founder's own words, looking at Draft mode on the clock at pick 18:

> "recommendations don't make a ton of sense... Josh Allen at pick 18 doesn't make sense almsot
> ever, and the logic is backwards, you'd take the player with less chance of being there if you
> wait, not more"

## He is right, and the tool states the inverted rule in its own words

The recommendation card and the assistant both give the *same* reason, and it is backwards.

Assistant, verbatim from the screen:

> "The tool's top pick right now is Josh Allen because only two tier-1 quarterbacks are left on the
> board and he's just 71% likely to still be available at your next pick (23) — versus Trey McBride
> at only 25% for that same next slot."

Card, verbatim:

> "Only 2 tier-1 QB left on the board, and only 71% likely to survive to your pick"

**Allen 71% to survive; McBride 25% to survive. The tool recommends Allen.** That is precisely
inverted. A player who will still be there when you pick again is one you can *wait* on; the scarce
one is the one you must take now. Taking the survivor and losing the non-survivor is the strictly
dominated branch whenever you want both.

The correct comparison is not "who is less likely to last" in isolation either — it is
value-now-plus-expected-best-later under each branch. But whatever the full rule, **the sign on the
survival term is wrong**, and the founder identified that from the product's own explanation.

## Three further defects visible in the same screenshot

**1 — The tool contradicts its own tested finding, and says so on screen.** The assistant's second
paragraph:

> "reaching for a quarterback in the first three rounds was the single most costly strategy tested
> in simulation, negative in all 12 scenarios run, with the worst case losing 115.4 points... Pick
> 18 falls in that early window the test covered, so that finding cuts against the live
> recommendation you're looking at."

So the recommender is making the single most costly move this project has measured, and the
assistant is correctly flagging it. That is the assistant working and the recommender not.

**2 — A garbled, self-contradicting sentence shipped to the founder.** Verbatim:

> "McBride still shows more value over replacement (49) than Allen does not, actually Allen's is
> higher (114)"

That is a model mid-correcting itself in production text.

**3 — Two different availability numbers for the same player on one screen.** The board's `AVAIL`
column reads Allen **79%**, McBride **40%**. The card and assistant say **71%** and **25%**. These
may be different picks (18 vs 23) and therefore both correct — but nothing on screen says so, and if
they are the same quantity, one is wrong.

## Why this outranks nearly everything

This is **question 3 of the founder's three model questions** — the suggested-pick model — observed
failing in the surface he would use on 7 September. The bar is his own: *"If I don't have those
three things in place, I don't want to use the tool for my real draft."*

It is also the question PM already recorded as the weakest of the three (FR-136), and whose `need`
parameter is an open decision PM must not frame, having authored the claim.

---

## Strategist ruling — 2026-07-30

**The rule:** `docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md`.
**The registration:** `docs/ranking/suggested-pick-rule-precommit.md`.
**The diagnosis it is built on:** `docs/handoffs/2026-07-30-pick-18-recommendation-defect-traced-reproduced.md`
(ranker's, independently corroborated) and its `### strategist · 2026-07-30` reply.

| Founder's item | Ruling |
|---|---|
| "the logic is backwards" | **Right about the sign, wrong about the replacement.** The correct rule is $\arg\max_X q_X g_X$ — (probability he is **gone** by your next pick) × (how much better he is than what you would take instead). His shorthand is $q$ alone, which drafts a 1%-survival replacement-level player ahead of a 60%-survival star. Refused in writing (ADR §3.4, §7 D-7). |
| Is it a sign error? | **No — structural.** `recommendation.ts:64-72`/`:82-97` take `(row, round, unfilledPositions)`. No `Dataset`, no `LeagueConfig`, no pick log. Availability is unreachable from the ordering function; there is no coefficient to invert. A "sign fix" would add availability as an additive VBD-points term, which is the wrong object. |
| Item 1 — contradicts the early-QB finding | **Neither ignoring it nor encoding it.** It carries an unfitted `−25` proxy that fires and loses by 21.70. The finding is narrower than the assistant said in five ways, and the assistant **inverted the uncertainty**: −115.4 is the point estimate at σ=10, not the worst case (CI [−176.3, −54.4]). No conversion exists between season roster points and a per-pick VBD addend, so no magnitude could have been "correct." |
| Item 2 — the garbled sentence | Model output from the reasoning lane, not a template. Its most likely cause is `DraftRoom.tsx:1005`'s false causal claim being handed to the model alongside contradicting VBD numbers. Fixing the string removes the cause. |
| Item 3 — two availability numbers | **Different picks, both correct, neither labelled.** Verified from `data/export/availability.json`: board `AVAIL` 79%/40% is the σ=10 marginal at **pick 18**; card 71%/25% is live-adjusted at **pick 23** (baselines 63%/22.5%). Worse: on the clock, `AVAIL` is the probability of an event you can see already happened. Disposition in ADR §6. |

**Three fixes need no measurement and ship now** (staged to `frontend`): the false causal sentence
at `DraftRoom.tsx:1005`, the unconditional "only" at `:961`, and the board `AVAIL` target pick at
`:1915`. **The ordering change does not ship until measured** — thread 111 measured the rule's
nearest relative at −106 to −126 roster points, and the argument that that arm was mis-specified is
an explanation, not evidence.
