---
ID: 030
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Surface "why our rank differs from the market" **inline on the board row**, not only in the player
detail sheet. A compact affordance on the row itself — enough to see the reason without leaving the
board.

## Why — this is the most evidence-backed change in the queue

Two independent research passes converged on it. The competitive UX research identified it as the
product's single most trust-building feature. The Reddit voice-of-customer pass then strengthened
that, and specified the placement: the demand is not for fewer recommendations, nor for blind
deference to consensus, but for a recommendation that **shows its reasoning so the user can agree or
override**. The upvoted sentiment was explicitly about forming your own opinion.

The VOC finding included the placement argument directly: put it inline on the board row, not two
clicks deep in a modal. A trust feature that requires two clicks to reach does not build trust,
because most users never see it.

## Constraints
- Density is the product. This cannot cost rows per screen.
- Every reason shown must trace to a named backend field. No generated prose, no plausible-sounding
  explanation — the derivation already exists in the detail sheet, so this surfaces existing facts
  more prominently rather than producing new claims.
- Where no meaningful difference exists, show nothing. An empty affordance on every row is noise.

## Done looks like
Inline affordance on board rows, no loss of density, all content traceable to existing fields,
screenshot attached at the standard viewport. Commit hash and test count.
