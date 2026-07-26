# ADR-B — Per-position rank correlation aggregation

**Path:** `docs/adr/ADR-B-rank-correlation-aggregation.md`
**Status:** Proposed
**Date:** 2026-07-26
**Owner:** Strategist (spec) / Backend (execution)
**Test-registry family:** `F-RANKCORR`

## Context

`backtest.py::_rank_correlation()` currently correlates **all positions pooled**, violating the within-position guardrail. Pooling across positions is not a mild approximation — it manufactures correlation from between-position mean differences. QBs score more than TEs in almost any season; a model that knows only "QBs beat TEs" and orders players randomly *within* every position will still post a healthy pooled correlation. The pooled number cannot go to zero even for a model with no within-position skill, which is the only skill that matters at a draft where you pick one position at a time.

Fixing the pooling exposes a design fork. Positions differ by roughly 4× in usable pool size (WR ~40–80 vs TE/QB ~10–20) and differ substantially in outcome variance. Any single figure must weight them, and the weighting is a free parameter — the exact shape of researcher degrees of freedom that lets a mediocre result be presented as a good one. But a single number is what gets quoted, and refusing to produce one guarantees somebody computes their own.

## Decision

**Report per position, separately. No aggregate correlation.**

Where a single headline figure is unavoidable, the *only* permitted substitute is the **minimum across positions, always printed with its position label and n** — e.g. `worst position: TE, τ_b = 0.21 (n=20)`. This is a selection, not an aggregate: it cannot be inflated by pool size, cannot be gamed by reweighting, and moves in the direction of the model's actual weakest claim. It is never to be called "the rank correlation."

### What the other choice would hide

A position-weighted single figure hides four things, in descending order of how badly:

1. **Sign disagreement.** A model can be genuinely good at WR and *anti-correlated* at QB and still show a comfortable positive aggregate. The aggregate would be reported, the QB rankings would ship, and the failure would only surface as user distrust.
2. **Pool-size domination.** Any weighting proportional to n gives WR (~40–80) four times the influence of TE (~10–20). The headline becomes "how good are we at WR," relabelled.
3. **Which positions the estimate is even informative about.** Kendall τ_b at n=20 has an approximate SE of 0.162, so a 95% interval spans ±0.32. TE and QB coefficients below roughly |0.32| are indistinguishable from noise in a single season. Folding them into an aggregate launders that uninformativeness into apparent precision.
4. **The weighting choice itself.** Equal-weight, n-weight, roster-slot-weight, and draft-capital-weight all defensible, all different answers. Whichever is chosen after seeing results is the result.

The cost of the chosen option is real and should be stated: four numbers are harder to communicate than one, and different readers will pick different ones to quote. The min-with-label rule is the mitigation.

## Exact computation

**Coefficient: Kendall's τ_b (primary).** Chosen over Spearman for three reasons: τ_b has an explicit tie correction in the denominator (ties are common on both sides here); it is the concordant-minus-discordant *pair probability*, which is directly interpretable as "how often does the model order two players correctly"; and Spearman squares rank differences, so at n=10–20 a single top-ranked bust dominates the coefficient. Spearman ρ is computed and reported as a fixed secondary. **Disagreement between them never licenses switching the primary** — if they diverge by more than 0.15 at any position, that position is flagged `unstable` and gets the tier-only treatment (below).

**Ties.** Use τ_b's tie correction; do not break ties. Specifically: identical model projections must **not** be disambiguated by player ID, alphabetical order, or load order — that fabricates ordering the model does not assert and inflates τ. Exact realized-point ties (possible in 0.5 PPR) are kept as ties.

**Population: prospective, by predicted rank.** The set for each position is the players the model ranked in its **pre-season, pre-week-1 frozen** within-position top-K. Selecting on realized rank would introduce look-ahead selection.

**Depth cutoff K, per position, frozen here:**

| position | primary K (2× replacement) | secondary K (at replacement) |
|---|---|---|
| RB | 60 | 30 |
| WR | 80 | 40 |
| TE | 20 | 10 |
| QB | 20 | 10 |
| DEF | 20 | 10 |

Primary is 2× replacement because the ranking's job extends past replacement into bench and flex, and because at replacement TE/QB give n=10, where τ_b's SE is ~0.24 (±0.47 at 95%) — a number too wide to support any decision. `2×` is chosen a priori as the smallest round multiple that reaches minimum viable n; it is not to be tuned. Both K values are pre-registered, so reporting only the flattering one is detectable.

**Realized side.** Within-position rank by **season total** 0.5-PPR points (not per-game). Total is what draft capital buys. Games missed count as scored zeros.

**Explicitly forbidden: any minimum-games-played filter.** "Min 8 games" is the canonical survivorship filter in this domain and it inflates correlation by deleting exactly the outcomes the model failed to anticipate. Any such filter appearing in `backtest.py` is a bug, not a modelling choice.

**Players outside the fitted curve — two distinct cases, handled differently:**
- **Ranked, no realized production** (never played, retired, injured out, cut): realized total = 0, **retained** in the sample. Zero is the correct fantasy outcome, and removing these players is the same survivorship error as a games filter.
- **Realized production, not ranked in top-K** (undrafted breakouts): cannot enter a paired correlation — there is no prediction to pair. They are **excluded from τ_b** and reported as a mandatory adjacent line, never omitted: `misses: k of the top-K realized <POS> were outside our ranked set (list)`. This is the coverage-disclosure pattern already established in the product ("3 of 10 starters have no projection — this total covers 7 of them"). Without it, the metric's blind spot *is* the model's worst failure mode.

**Uncertainty.**
- Within a single season: τ_b with a 10,000-draw seeded permutation reference distribution (seed recorded). The analytic large-sample SE is reported but flagged approximate at n ≤ 20.
- Across seasons: **season-level bootstrap only**, per the standing guardrail. With 4 usable seasons this interval is wide and its coverage is not nominal; it is reported anyway, with n=4 printed beside it, because an honest wide interval is the point.
- A within-season **player-level** bootstrap may be reported to characterize sampling variability of τ over players in *that* season. It must be labelled as such and must never be presented as a claim about future-season skill. Those are different estimands and conflating them is how a 4-season problem gets dressed up as a 200-player problem.

**Reference baseline.** Compute τ_b identically for consensus ADP vs realized, same K, same season. Our ranking's claim is `τ_ours − τ_consensus`, per position, per season. With 4 seasons, report the 4 paired differences as raw numbers with no p-value. **Pre-committed: no directional claim about beating consensus is published from n=4 seasons** — the same floor as ADR-A applies (min sign-test p = 0.0625 at n=4, before multiplicity across 5 positions).

## Pre-committed decision rule

Bands and their actions, fixed before any number is computed. Each band maps to a **product decision**, not an adjective — that is the device that prevents post-hoc rationalization, because the number now costs something.

| τ_b (primary K, median across available seasons) | Verdict | Action in the product |
|---|---|---|
| < 0.10 | no ordering skill | Suppress the numeric rank for that position. Show tiers only, unordered within tier. |
| 0.10 – 0.25 | weak | Show tiers with ordering inside tier, no global rank number. |
| 0.25 – 0.40 | moderate | Show rank, with the position's τ_b and n printed in the methodology surface and reachable from the column header. |
| > 0.40 | strong for this domain | Show rank normally. |

Additional pre-commitments:
- **Instability override.** If the secondary-K coefficient differs from the primary by more than 0.15, or τ_b and ρ differ by more than 0.15, the position is `unstable` regardless of band and drops to the tier-only treatment. Rationale: a coefficient that moves that much under a pre-registered depth change is not measuring a stable property.
- **Uninformative override.** If the position's 95% permutation interval contains 0, the band is reported but the action is the *lower* adjacent band. At n=20 (TE, QB, DEF) this will frequently bind. That is the correct outcome — those positions' rankings are not currently supported by evidence at the depth we can measure.
- **No aggregate may be computed, stored, or logged**, including in intermediate artifacts. Fields that do not exist cannot be quoted. `_rank_correlation()` returns a per-position mapping; a scalar return type is a lint failure.

## Consequences

- `_rank_correlation()` is rewritten to return `{position: {tau_b, spearman, n, k_primary, k_secondary, permutation_ci, misses}}`. Existing pooled figures in any doc are retracted, not adjusted.
- Several positions — TE, QB, DEF near-certainly — will land in tier-only treatment. This is a visible product downgrade and should be framed to users as such, via the existing "read the bars, not the order" idiom.
- Existing point estimates (−1,070 pts, −226.4 pts) remain uninterpretable until season-level CIs land; this ADR does not fix those, and they should carry an explicit "no CI, do not cite" marker until they do.
- Four-to-five numbers instead of one. Accepted cost.

## What would falsify this

- **Falsifies the no-aggregate decision:** a weighting scheme derived from something external and non-negotiable — e.g. weights fixed by actual draft capital spent per position in the 10-team/0.5-PPR/no-K format, published and frozen before any correlation is computed. That removes the free-parameter objection. It does not remove objections 1 and 3 (sign disagreement, uninformative small-n positions), so it would need to be an addition alongside per-position reporting, never a replacement.
- **Falsifies τ_b as primary:** pool sizes grow such that all positions clear n ≈ 50 (a deeper consensus source, or expanded K justified by a change in roster format), at which point Spearman's small-sample fragility stops binding and the choice becomes cosmetic.
- **Falsifies the depth cutoff:** replacement levels are revised. K is defined *relative* to replacement, so it should follow automatically — if it does not, the cutoff has been hardcoded and that is a bug.
- **Falsifies the band table:** a validated user study showing that tier-only presentation harms decision quality more than a weakly-supported rank helps. Absent that evidence, the conservative mapping stands.
