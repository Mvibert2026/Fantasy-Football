---
ID: FR-2026-08-01-dynamic-data-derived-pick-penalty-vona-to-replac
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Dynamic data-derived pick penalty (VONA) to replace the hardcoded -25/+8/+18 constants

Founder's own words, chat 2026-08-01:

> "We need to try to come up with a dynamic points penalty. Not hard codes. And even better if based
> in real data."

## Why it matters

The recommender orders picks as `vbd + unfilled_need(+8) + tier1_te(+18) + early_qb_penalty(-25)`.
**All three constants are hardcoded, were never fitted to anything, and the module's own docstring
calls itself a stopgap.** The founder has caught the recommender failing by eye twice.

The `-25` in particular is a hand patch over a **category error**: presenting a season-value order
(VBD, a *stock*) as a pick order (a *policy*). See `CLAUDE.md` 6.6's four-deliverable table and
`docs/fable/M2-findings.md` M2-3.

## Initial read

**The dynamic replacement already has a name and a spec: value over next available (VONA).**

`score = VBD(player) - E[best same-position VBD surviving to your next pick]`

with the expectation taken from the calibrated availability model. This satisfies both halves of the
request exactly:

- **Not hardcoded.** It is computed per player, per slot, per board state, and it changes as the
  draft unfolds.
- **Based in real data.** The survival probabilities come from measured ADP dispersion, not from a
  chosen number.

**Why it reproduces the -25 without anyone choosing -25.** An elite QB has high VBD, but the expected
best QB still available at your next pick is *also* high -- the QB premium collapsed from -67 to -4 --
so the net is small and he falls. An elite RB's replacement curve falls off a cliff, so his net is
large and he rises. **The term stops being a QB penalty and becomes a general opportunity-cost term
that merely bites hardest where the replacement curve is flattest.**

**The hard prerequisite, and the reason this is not dispatched yet.** `PR-008` already measured a
naive VONA variant **losing to plain VBD by roughly -106 to -126 roster points**, because the
scarcity input beneath it was crude. **Opportunity-cost logic is only as good as the survival model
under it.** Built on a guessed sigma, it is worse than the constant it replaces. This is also why the
founder's own build order -- availability before recommender -- is correct.

**Sequencing, in order, none of it optional:**

1. **PR-007** (running as of 2026-08-01) -- do the three constants earn their place at all? Measured
   in roster points against actual outcomes, leave-one-out, powered to delete. Registration is frozen.
2. **Calibrate the availability model** against the logged mock drafts (measurement M3, unrun). The
   current simulator uses **one global sigma for every player**, offered at 5/10/20, and its own
   metadata admits it is *"a guess, not fitted to observed drafts."*
3. **Then VONA**, registered and simulated before shipping -- because PR-008 is a live warning, not a
   hypothetical.

**Founder's own refinement, same conversation, and it tells us where the value is:** conditioning on
opponents' rosters "changes that a little. More in later rounds." Fable measured that with ADP plus
per-player dispersion the *unconditional* marginal is nearly closed-form -- so simulation buys little
early, when the room is taking best-available, and progressively more late, when picks are
need-driven. **Testable prediction: simulation value is near zero in round 1 and rises monotonically.**
If it holds, it says where to spend effort and it justifies simulating at all.
