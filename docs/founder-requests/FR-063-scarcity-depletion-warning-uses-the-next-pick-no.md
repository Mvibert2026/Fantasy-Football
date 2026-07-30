---
ID: FR-063
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session, screenshot
RAISED: 2026-07-30
---

## Request
Scarcity depletion warning uses the next pick, not the pick after — warns too late to act

Founder's own words, with a screenshot of the Scarcity tab mid-draft:

> "Shouldn't this be considering pick 23, since my next pick is 18, it's a warning now or you mis it?"

## What the screenshot shows

Header: `ON THE CLOCK #10 · team 10 · PICKS UNTIL YOU 8 · YOUR NEXT 18`. Roster: RB 1/2 filled
(Jahmyr Gibbs), everything else empty.

Scarcity panel, `vs. expected by pick 10`:

| | | |
|---|---|---|
| RB | 162/167 left | 1 ahead of pace · tier 1 gone · tier 2: 5 left · 1 <50% by 18 |
| WR | 202/206 left | 1 behind pace · **tier 1: 1 left** · 6 <50% by 18 |
| TE | 87/87 left | on pace · tier 1: 2 left · 1 <50% by 18 |
| QB | 50/50 left | — |

And the warning: *"All 1 remaining tier-1 WR sit under 50% to reach pick 18. If you want one, this
is the turn."*

## The defect

**The warning is computed against pick 18 — his next pick. It should be computed against pick 23 —
the pick after that.**

*"If you want one, this is the turn"* is only true if the player cannot survive to the turn **after
next**. Surviving to 18 is exactly what makes waiting safe: he picks at 18, so a player who reaches
18 is available to him. **The decision the warning is trying to inform is "take it now at 10, or wait
until 18"** — and that decision turns on whether the player is still there at 18, which is what the
panel already measures, not on whether he should panic at 10.

Read literally, the current warning fires when a player is *unlikely to reach the very pick the
founder is being told to act at.* It is either one turn early or measuring the wrong horizon,
depending on which reading of "this is the turn" was intended — and that ambiguity is itself the bug.

**`under50ByNext` and `depletionWarning` in `frontend/ui/data/scarcity.ts` both key off
`nextUserPick`.** The fix is not simply swapping to the following pick — the two numbers answer
different questions and the panel probably needs both:

- *"N players sit under 50% to reach your next pick (18)"* — the survival figure, useful as context.
- *"take now or wait"* — needs the pick **after** the next one, because that is the real alternative
  if he uses pick 18 on something else.

## Why it matters

This is the one derived urgency claim the product makes. It appeared in the same session as FR-045,
where the pace line was reporting an artifact as a market signal — same panel, same class of problem:
**a number that is arithmetically defensible and answers the wrong question.**

## Also in this screenshot, unrelated, for the same batch

A **dropdown colour defect** the founder flagged separately and asked to be logged rather than
discussed: the SLOT selector's open list renders near-white options on a near-white background —
only the highlighted row is legible. Applies to the native `<select>` popup in dark mode. Route to
`design` with the inert-controls and two-track work already delivered.

**Screenshot not saved.** It arrived inline and could not be written to disk; the description above
is the record.
