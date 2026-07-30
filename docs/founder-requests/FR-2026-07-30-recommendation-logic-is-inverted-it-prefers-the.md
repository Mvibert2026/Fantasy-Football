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
