---
ID: FR-2026-08-01-consensus-may-be-draft-oriented-not-points-order
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Consensus may be draft-oriented not points-ordered: explains why our VBD-adjusted board loses to raw consensus

Founder's own words, chat 2026-08-01, immediately after establishing the three-layer architecture
(rankings / board / strategy) now in `CLAUDE.md` 6.6:

> "I suspect consensus rankings may be draft oriented not just a rank order of projected points for
> the season (though I'm sure that's a starting point for the draft boards)."

## Why it matters

**It supplies a mechanism for a measured anomaly PM reported without one.** On the three seasons
where both exist, the shipped **consensus-adjusted board scores rho 0.649 against raw consensus's
0.743** -- worse in 3 of 3 seasons. PM reported this as "a systematic defect in the shipped product"
and could not say why.

**If ECR is draft-oriented, the mechanism is double-counting.** Experts ranking players *for a draft*
have already priced positional scarcity, roster construction, bye weeks and risk. Our board then
applies **VBD on top of that** -- adjusting for scarcity a second time. Over-adjustment would
degrade the ordering, which is exactly what is measured.

**A second measurement corroborates it and was previously unexplained.** Consensus and
consensus-adjusted are **identical within position** and differ *only* cross-positionally. The
cross-positional axis is precisely where double-counted scarcity would show up, and nowhere else.

## Initial read

**This is a hypothesis with a clean test, not a conclusion.** Two ways to check it, both cheap:

1. **Compare ECR against a pure projected-points ordering** from a public projection source for the
   same season. If ECR systematically deviates from points-order in the direction of positional
   scarcity -- QBs and TEs pushed down relative to their raw point totals -- it is draft-oriented.
   If it tracks points-order closely, it is not, and the double-counting story is wrong.
2. **Check whether the adjusted board's loss concentrates at the positions VBD moves most.** The
   double-counting account predicts the damage is concentrated in QB (the position VBD inflates most,
   ~20 places at the top per PR-007 work), not spread evenly.

**Consequence if true, and it is significant.** The `expert_adjusted` board -- the shipped default,
one of ADR-068's four selectable sources -- is applying a correction its input already contains.
**The fix would be to stop adjusting a draft-oriented source, not to adjust it better.** That is a
one-line change to the default, gated on the test above.

**Consequence for v2, which is the more important half.** v2 is built from projected stat lines, so
it produces a genuine *points-ordered* ranking with no draft reasoning in it. Under ADR-069 that is
correct and intended -- and it means **v2 is the layer-1 object and ECR is closer to a layer-2
object.** Comparing them on pooled cross-positional rank correlation compares different kinds of
thing, which is the error `CLAUDE.md` 6.6 now names. **Within-position comparison is the valid one**,
and it is the one where v2 is closest (WR -0.031, TE -0.022 on 2024).

**Does not reopen ADR-069.** Consensus remains neither an input nor a development signal. This is
about correctly *interpreting the baseline*, not about steering toward it.
