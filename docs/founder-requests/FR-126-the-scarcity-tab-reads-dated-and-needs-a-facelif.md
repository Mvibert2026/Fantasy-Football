---
ID: FR-126
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat with screenshot
RAISED: 2026-07-30
NEEDS: design
---

## Request

Founder's own words, with a screenshot of the Scarcity tab mid-draft at pick 11:

> "for design, this seems a little old and due for a facelift/modernization"

## Why it matters

He asked for a facelift. **The screenshot shows a measurement problem underneath the styling one**,
and design should have it before treating this as visual work.

### The bars are structurally incapable of showing scarcity

Read off his own screenshot at pick 11:

| Position | Bar | Fill |
|---|---|---|
| WR | 201 / 206 left | 97.6% |
| RB | 162 / 167 left | 97.0% |
| TE | 87 / 87 left | 100% |
| QB | 50 / 50 left | 100% |

Four bars, all essentially full, all the same length. **The bar carries no signal at the moment he is
looking at it**, and it is the loudest element on the panel.

That is not a rendering accident — it is the denominator. `frontend/ui/data/scarcity.ts:112` sets
`total: atPos.length`, the count of every player at that position on the 510-row board: 206 WR, 167
RB, 87 TE, 50 QB. Ten picks into a draft, `remaining/total` is ~97–100% for every position and always
will be. The bar only starts to move in rounds nobody worries about scarcity in.

### The right denominator is already computed, on the same object, and unused

Line 122 of the same file:

    startablePool: (startersByPosition[pos] ?? 0) * teams,

Against this league — 10 teams, 1 QB / 2 RB / 3 WR / 1 TE / 2 FLEX — that is 30 WR, 20 RB, 10 TE,
10 QB. **Those denominators would move.** At pick 11 with tier 1 WR gone, a bar drawn against a
30-player startable pool says something; a bar drawn against 206 cannot.

This is the same shape of defect as the `PROJ (CI)` bug the founder caught the same day: the correct
field exists, is populated, and the UI renders a different one.

### The code already knows the raw count is the wrong signal

`scarcity.ts:163-165`, written by whoever built the tier line:

> "tier 1 gone · tier 2: 1 left" — **what actually determines whether the user must act, as opposed
> to a raw remaining count.**

So the panel's own author identified the decision-relevant number, put it in the smallest type on the
row, and left the raw count driving the full-width bar above it. The hierarchy is inverted against a
judgement the project already made.

## Initial read

**Design item, and the brief should lead with the measurement, not the styling.** Otherwise a facelift
produces a prettier bar that still cannot move.

Four things worth naming in the design prompt:

1. **The denominator question is design's to decide**, because it is really "what is this panel
   *for*." Startable pool, tier depletion, or availability-by-next-pick are three different panels
   wearing one layout. `startablePool` exists either way.
2. **The tier line is doing the real work and is styled as a footnote.** It is the line that says
   whether he must act now.
3. **Semantic colour is being spent on non-semantic content.** In the screenshot, `1 behind pace`,
   `1 ahead of pace` and `tier 1 gone` all render in the same warning orange — including *ahead of
   pace*, which is good news. `POSITION-COLOUR-RESOLUTION.md` already banned semantic accents from
   the grid; the same reasoning applies here.
4. **`5 <50% by 18` is unreadable as written** and is one of the most decision-relevant facts on the
   panel — five players he might want will probably be gone by his next pick.

**What must not be lost in a redesign.** `dataAvailable` is a real gate: DEF has no board data at all,
and the file's own comment says conflating "we tracked it, nothing gone, exactly on pace" with "we
have never tracked this position" is exactly the failure to avoid. Same for `paceSuppressedReason` —
pace goes uncomputable when auto-fill placeholders are present, and the panel currently withholds it
and says why. Both are the never-fabricate rule in working form and survive any facelift.

**Sequencing:** behind the 2026-07-31 items in build. Goes into the next design prompt with the
measurement attached.
