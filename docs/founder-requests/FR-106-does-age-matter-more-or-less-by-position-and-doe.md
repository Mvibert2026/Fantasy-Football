---
ID: FR-106
STATUS: NEW
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Does age matter more or less by position, and is there a curve where it inverts?

Founder's own words:

> "does age matter more or less for different positons?  is there a curve where it inverts?"

## Why it matters / PM's read

Two questions, and the second is the sharper one.

**What exists:** `docs/analysis/adp-vs-production-2026-07-30.md` §Tier 2 tested **age × position** and
found the direction robust but the magnitude noisy — young WR/TE (≤23) beat ADP by ~35 VBD
pts/season, **MARGINAL**, with **LOW** confidence specifically for QB age effects (n too small, sign
unstable). So age-by-position has been touched; the *shape* of the curve has not.

**What has not been done: the aging curve itself.** Every existing test treats age as a bucket
(≤23 vs. rest) or a linear term. The founder is asking about **curvature** — whether the
age-to-value relationship peaks and turns over, and whether that turning point differs by position.
That is a different model, and it is the one that would actually inform a draft.

**Why the inversion point matters more than the slope:** if RB value turns over at 26 and WR at 28,
that is directly actionable at the draft in a way "young players are slightly better" is not.

**Traps that make this harder than it looks:**

- **Survivorship dominates aging curves.** Players who are still in the league at 32 are, by
  selection, the good ones. A naive age curve measures who survived, not how players decline. The
  ranker already measured a version of this: players seen ≥5 seasons score roughly **2× the PPG** of
  those seen ≤2. Any age curve must handle this or it will show players *improving* with age.
- **Age is confounded with the availability question in FR-104**, which is running now. If the young
  advantage turns out to be a games-played effect, the aging "curve" may largely be a durability
  curve.
- Per-position cells get small fast, especially at QB where the existing age result was already LOW
  confidence.

**Sequence after FR-104**, which may partly answer it.
