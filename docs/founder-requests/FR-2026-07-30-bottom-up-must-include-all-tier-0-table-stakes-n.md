---
ID: FR-2026-07-30-bottom-up-must-include-table-stakes
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — question 1, his stated first priority
NEEDS: ranker
---

## Request

> "Our bottoms up needs to include all the table stakes. There are probably quite a few."

## He is right, and the count is worse than "quite a few"

`docs/test-registry.md` Tier 0 lists **twelve** table-stakes factors. **Not one is implemented.**
Every row reads `SPEC`, `NEW`, or `BLOCKED`:

| # | Factor | Status |
|---|---|---|
| 1 | Multi-source ADP | SPEC |
| 2 | Consensus projections | BLOCKED — needs component-level projections |
| 3 | Positional tiers | SPEC |
| 4 | Bye weeks | SPEC |
| 5 | Depth chart / role | SPEC |
| 6 | Injury designations & status | SPEC |
| 7 | Age | SPEC |
| 8 | Prior-year target / touch share | SPEC |
| 9 | Snap share | SPEC |
| 10 | Red-zone / goal-line usage | SPEC |
| 11 | Vegas win totals & implied team totals | NEW |
| 12 | Season-long strength of schedule | SPEC — measured **~zero** edge |

## This explains today's headline finding

Ranker measured that the shipped board's within-position ordering is **identical to consensus** at all
four positions, and that its whole deviation is cross-positional.

**That is the direct consequence of having zero table stakes wired in.** A board with no age, no snap
share, no target share, no depth-chart role and no red-zone usage has nothing with which to disagree
with consensus about *a player*. It can only re-weight *positions*. The two findings are the same
finding seen from opposite ends, and the founder arrived at it from the product side.

## The distinction that unblocks this without inflating false positives

**Table stakes have a different evidence bar from edge factors, and conflating the two is what has
kept all twelve at SPEC.**

- **§6.3's multiplicity exposure is about edge claims** — "does factor X beat the baseline" tested
  across ~30 candidates. That is where false positives live.
- **Table stakes do not need to win that test to be included.** Nobody needs a holdout to establish
  that snap share and depth-chart role carry information about opportunity. They are the floor every
  credible model already stands on. Requiring each to prove incremental edge before inclusion is
  applying the wrong bar, and it is why a model that is supposed to be bottom-up currently contains
  none of them.

So: **include the table stakes on construction grounds, and spend the multiplicity budget on Tier 1
and 2, where the edge claims actually are.** That is not a relaxation of the guardrails; it is
applying them where they bite.

Two Tier 0 rows already carry measured results that must survive this: #12 strength of schedule is
**~zero edge**, and #2 is genuinely blocked on component projections. Include is not the same as
weight — a table stake with no measured effect can be present and carry zero.
