---
ID: FR-058
STATUS: SHIPPED
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
The recommendation must explain itself whenever it departs from VBD or the selected strategy

Founder's own words:

> "Also if the recommendation strays from vbd or any selected strategy, then the panel needs to
> provide an explanation"

## Why it matters

**The recommendation currently disagrees with VBD silently, and it does so on four numbers nobody
measured.** `frontend/ui/data/recommendation.ts`:

```
score = vbd
      + 8   if the position is still unfilled
      + 18  if the player is a tier-1 TE
      - 25  if QB and round < 6
```

So the top recommendation is routinely *not* the highest-VBD player available, and nothing on screen
says why. The module's own docstring calls it *"a stopgap, not a validated model… it has not been
backtested the way the rankings themselves have."* **The founder is being shown an unexplained
override of the one number the board is actually built on.**

This is the same defect class as everything else caught today — a screen presenting a derived value
without its basis. It is worse here because it is the screen used under a clock.

## Initial read

Not the founder's own words — PM's read.

**The requirement is precise and it is a rule, not a feature: any departure from the VBD ordering
must carry its reason.** The panel already knows the reason — each adjustment is a named term. It
simply throws it away and renders the total.

What it should show, when and only when the ordering changes:

- **Which term moved the player**, in plain words — *"ahead of higher-VBD players because you have no
  tight end and this is the last tier-1"*, not `+18 tier-1 TE`.
- **What it displaced.** The founder cannot judge an override without knowing what he is giving up.
- **The size of the gap.** Overriding a 2-point VBD difference is not the same claim as overriding
  a 30-point one, and the second deserves more scepticism, not less.
- **When nothing moved, say nothing.** A permanent explanation panel becomes wallpaper.

**Two things this must not become.**

1. **Not a justification generator.** The explanation states which rule fired and what it cost. It
   does not argue that the pick is good. Those four constants are unvalidated; prose that makes them
   sound reasoned would launder a guess into a finding.
2. **The honest version says so.** Any explanation that cites the tier-1 TE bonus or the early-QB
   penalty is citing a hand-picked number. The panel should be able to say that — *"this rule has not
   been backtested"* — because it is true and because the founder has consistently asked to see what
   a number is made of.

**"Or any selected strategy"** points at something that does not exist yet: there is no strategy
selector in the app. `strategies.json` holds simulated strategies (hero-RB, zero-RB and others) and
the Strategy Guide displays them, but nothing lets the founder *choose* one and have the
recommendation follow it. **That is a second, larger request inside this one** — treat it as
dependent work, not part of the same build, and note that the strategy guide is empty in 26 of 27
leagues (see `CURRENT-STATE.md` item 5).

**Sequencing:** the explanation for VBD departures is small and should ship with the next draft-screen
pass, alongside FR-050 (VBD in the list) and FR-055 (column headers) — all three are the same screen
and the same complaint, which is that the numbers do not explain themselves. Strategy selection is a
separate build.

**This also strengthens the case for fixing the constants** (already flagged for adversarial review).
Once the panel has to say *why* it overrode VBD, "because of a number someone picked" becomes visible
to the founder every time it happens.

## Resolution (2026-07-29, frontend)

**Shipped: the VBD-departure explanation.** Out of scope, per this file's own read and this
session's task boundary: "or any selected strategy" — no strategy selector exists to depart from,
so nothing was built there; still open, dependent work.

`ui/data/recommendation.ts` gained `recommendationTerms()` (the three reachable constants — DEF's
`-40` was never reachable, board.json carries no DEF rows, ADR-039 — each paired with the plain-word
reason it fired, e.g. `"you have no tight end yet"`, `"this is the last tier-1 tight end left on the
board"`, `"it is a quarterback being taken before round 6"`) and `findVbdOverride(top, available,
round, unfilledPositions)`, which compares the recommendation's #1 pick against the single
highest-VBD player still available on the *whole* board (not just the six-deep shortlist already
shown) and returns `null` whenever they already agree — satisfying "when nothing moved, say
nothing" exactly, not just usually. `recommendationScore` itself is unchanged arithmetic, now built
from the same term list so the score and its own explanation can never drift apart.

`DraftRoom.tsx`'s RECOMMENDED card gained a "WHY NOT HIGHEST VBD" panel, rendered only when
`findVbdOverride` returns non-null, showing: the displaced player by name and position, the exact
VBD gap (`vbdLeader.vbd - top.vbd`, e.g. "7 more VBD (113.7 vs 106.8)"), and every firing term in
plain words with its signed point value — each one tagged, every time, "an unbacktested stopgap
constant, not a finding" (item 2's literal ask). Nothing in the panel argues the pick is good
(item 1) — it states which rule fired and what it cost, full stop.

Verified against a real, reproducible scenario (not a synthetic fixture): with the board's real top
five VBD players drafted off, the user's next real turn recommends Jaxon Smith-Njigba (WR) over
Josh Allen (QB, 7 more VBD) because the unfilled-WR bonus (+8) and the early-QB penalty (-25, round
2 < 6) combine to flip the order — the panel names Josh Allen, the 7-point gap, and both terms.
A second scenario (the user's actual first real pick, only the board's top two players gone)
confirms the negative case: the recommendation's #1 pick *is* the VBD leader there, and no panel
renders. Screenshots: `frontend/e2e/artifacts/fr058-vbd-override-explanation.png` and
`frontend/e2e/artifacts/fr058-no-override-when-order-agrees.png`; script:
`frontend/e2e/verify-fr050-055-058.mjs`. Unit tests: `ui/__tests__/recommendation.test.ts` (12
tests covering `recommendationTerms` reasons and `findVbdOverride`'s null/non-null cases, the
displaced player, the exact VBD gap, and both `appliesTo` sides).
