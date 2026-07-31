---
ID: FR-2026-07-30-coordinator-continuity-tenure-and-qb
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — corrects a factor that was just graded NULL on the wrong specification
NEEDS: ranker
---

## Request

> "What about OC and coach continuity instead of new? By position. Probably impacts qb more."

## Both halves are right, and the second is a straight gap

**1 — The factor was tested as a binary, but the registry row is named for a duration.**

Registry **#29 is literally "Coordinator continuity"**. What batch 2 measured was arm `C1 new
offensive coordinator (PLAYER)` — a **binary**: did the OC change, yes or no. Continuity is a
different object: *how long has this coordinator been here*. A third-year system and a first-year
system are both "not new", and the binary cannot tell them apart.

So the NULL on file is a NULL on the specification, not on the founder's hypothesis. Same class of
error as registry #13, which measured target-share *stability* and is routinely misread as a verdict
on target share.

**2 — QB was never tested. At all.**

Batch 2's coordinator arms cover exactly three positions:

| Position | Arm | Result |
|---|---|---|
| WR | C1 new OC (player) | d = +0.1274, NULL |
| TE | C1 new OC (player) | d = +0.1513, NULL |
| RB | C1 new OC (player) | d = +0.1470, NULL |
| **QB** | **— none —** | **never run** |

The founder's stated hypothesis — that this matters most at QB — is **untested**, at the one position
absent from the run. He identified the gap from the outside.

## Why QB is the plausible place for it, stated as a prior not a finding

- The QB is the only position whose production is a direct function of the play-caller's system: cadence,
  protection scheme, read progression, pass rate.
- Researcher's sweep found the registry contains **zero QB-specific factors**, and that the strongest
  published QB predictor is rushing attempts — a *scheme* variable. That is convergent, which is
  exactly when to be careful, not confident.

**Prior stated before measurement:** if continuity has an effect anywhere, QB is where it should be
largest. If it is null at QB too, the factor is dead on both specifications and should be recorded as
such rather than re-specified a third time.

## Constraint carried forward

Batch 2's own finding applies here: `new_oc` is true for **46–48% of every ADP board**. Any continuity
variable will be similarly dense, so an effect must be real before anything renders on screen — the
insight sentence was refused for exactly that reason.
