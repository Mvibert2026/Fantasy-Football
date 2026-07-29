---
ID: FR-058
STATUS: NEW
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
