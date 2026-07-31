---
ID: FR-2026-07-31-separate-edge-from-absolute-quality
STATUS: NEW
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGHEST — a methodology correction affecting how every result so far is read
NEEDS: strategist, then a measurement
---

## Request

> "Are we making sure to separate edge over consensus and having the best rankings we can have?
> These analysts all aren't better than consensus. Certainly not every year."

## He is right, and the harness half-agrees with him already

**Two different questions have been reported as one.**

1. **Absolute quality** — are our rankings the best we can make them? Measured by `E1a`, component
   projection MAE against the incumbent.
2. **Edge over consensus** — do they beat the market? Measured by `E1b` (board error) and `E2`
   (board rank correlation).

The grading vocabulary **does** separate them — `PROJECTION-ONLY` exists precisely for "improves the
projection, does not improve the board", and several arms across batches 3, 6 and 7 earned it. But
every founder-facing summary has led with *"nothing survives"*, which is the **edge** verdict, and
that has buried the absolute-quality result underneath it.

**Concrete cases already on file where the distinction changes the reading:**

| Arm | E1a (absolute) | Board | Reported as |
|---|---|---|---|
| ANY/A at QB | −1.43, −1.26% | −3.06 board error, but E2 negative | "PROJECTION-ONLY" — buried |
| Passer rating at QB | −0.96 | −3.45 board error, E2 excludes zero on the wrong side | same |
| Lagged YPC → RB volume | **−1.88%** | E1b −0.72 | post-hoc, unshipped |
| Explosive rush rate | −1.51% | E1b −0.03 | PROJECTION-ONLY |

**These are real improvements to the rankings.** Graded against §6.5's baseline rule they are
failures, because that rule makes the comparison the headline. Both readings are correct; only one
has been reported.

## The second half of his point, which is the deeper one

> "These analysts all aren't better than consensus. Certainly not every year."

**This is the wisdom-of-crowds result, and it is the strongest argument against treating
"beat consensus" as the only bar.** Consensus *is* the aggregate of the analysts. Individual
analysts do not reliably beat their own average — that is what makes an average worth taking.

Today's own measurement is consistent with it: prior points-per-game replicated at **ρ = +0.668** and
was the **ceiling** — all ten alternative predictors, including every published analyst metric tested,
came in below it (batch 5).

So **"no edge over consensus" is the expected outcome, not a failure signal.** Reporting it as a
failure, session after session, misrepresents what was learned.

## The measurement nobody has run

**How good is consensus, year by year — and how much does that vary?**

Every result so far compares to consensus as though it were a fixed bar. The founder's
"certainly not every year" says it is not. If consensus is strong on average but poor in identifiable
seasons, then:

- "Beat consensus every year" is the wrong bar, and no factor will ever clear it
- "Be robust in the years consensus is wrong" is a different, achievable, and more valuable goal
- A proprietary source's job may not be to beat consensus but to be **independently wrong in
  different places** — which is what makes a second opinion worth having, and what
  `CLAUDE.md` §4's never-blend rule preserves

## What to do

Route to `strategist` before any further factor testing is graded, because it changes what the grades
mean. Then measure consensus's own year-to-year variance against realised outcomes.
