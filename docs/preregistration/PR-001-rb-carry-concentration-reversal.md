---
id: PR-001
title: RB carry concentration reversed after 2019, contradicting committee-backfield consensus
hypothesis: Since 2020 the share of RB carries going to workhorse backs has been rising,
  reversing a two-decade decline. If real and persistent, elite RB workload is becoming
  more concentrated and therefore more valuable than a committee-era prior implies, and
  prior-year carry share should carry positive incremental information about RB fantasy
  outcomes above consensus rank in the post-2019 regime specifically.
metric: Incremental adjusted R-squared and the coefficient on prior-year RB carry-share,
  conditional on a flexible function of consensus positional rank, in a model predicting
  actual season fantasy points for RBs. Coefficient reported separately for the pre-2020
  and post-2019 regimes. Standard errors clustered by player.
confirmation_threshold: CONFIRMED requires ALL of - (a) the post-2019 coefficient on
  carry-share is positive and its BH-adjusted p-value is at or below 0.05 after correction
  across the full run log; (b) incremental adjusted R-squared over the consensus-only model
  is at least 0.01; (c) the sign is stable across both bootstrap tails, i.e. the 95%
  season-level bootstrap CI on the coefficient excludes zero. Anything less is reported as
  NOT CONFIRMED. A pre-2020 coefficient that is equal or larger falsifies the regime claim
  even if the pooled coefficient is significant.
status: FROZEN-FOR-FUTURE
frozen_date: 2026-07-25
frozen_reason: The ALPHA track is structurally closed for 2026 (ADR-026). This test measures a
  factor coefficient CONDITIONAL ON CONSENSUS, so it is bounded by consensus coverage - 4
  development seasons, where the exact sign test floors at p=0.125 before any multiple-
  comparisons correction. It cannot reach significance regardless of whether the effect is
  real. NOT pending, NOT abandoned: the hypothesis stands and the pre-registration is intact.
  Reopens when development coverage reaches n>=6 seasons (floor 0.031), on current trajectory
  2028. Do not run it before then and do not treat a null from it as evidence against the
  hypothesis.
source_finding: src/regimes.py structural break analysis, 2026-07-25
regime_context: Break detected after 2019 (sup-F=9.12, bootstrap p=0.0430). Pre-break
  regime 1999-2019 slope -0.00686/season (p<0.001, DECLINING); post-break regime 2020-2025
  slope +0.01402/season (p=0.019, RISING).
data_availability: rb_carry_top30_share is derived from `carries`, which is populated for
  the full 1999-2025 window (docs/data-availability.md §2). Unlike target-derived metrics
  it is NOT affected by the 2003-2008 receiver-attribution gap. Effective sample for the
  alpha track is nonetheless bounded to 2021-2025 by consensus coverage, of which 2025 is
  the locked holdout, leaving 2022-2024 for development (the board arm needs a prior
  consensus season, so 2021 is unusable).
---

## Why this is worth testing

The structural break analysis in `src/regimes.py` found that `rb_carry_top30_share`
declined steadily from 1999 to 2019 and then **reversed direction**, rising since 2020.
The received wisdom that running back usage has become irreducibly committee-based
describes the pre-2019 regime, not the current one.

If the reversal is real, it is the kind of thing that produces alpha: a widely-held prior
that stopped being true recently enough that consensus may not have fully repriced it.

## Why it might be nothing

Stated in advance so it cannot be explained away later:

1. **n = 6 seasons in the post-break regime.** The break itself was detected on 27 annual
   observations, which `regimes.py` explicitly flags as low power. p=0.043 is not far from
   the threshold and would not survive a stringent correction on its own.
2. **The reversal may be a COVID-era artifact.** The post-break regime starts in 2020.
   Roster volatility, missed games, and scheduling disruption in 2020-2021 could produce
   apparent concentration without a scheme change.
3. **Consensus may already price it.** Analysts read the same box scores. Rising carry
   concentration is observable to everyone, so the market may have adjusted before we
   measured it. This is precisely the PRICED_IN case, and it is the most likely outcome.
4. **Concentration at the league level need not imply predictability at the player level.**
   Knowing the top 30 backs take a larger share says nothing about *which* backs they are.

## Pre-committed interpretation

- If **CONFIRMED** under the threshold above → label CANDIDATE_ALPHA and report the effect
  size in points, not just significance.
- If the coefficient is significant **pooled** but not in the post-2019 regime specifically
  → the regime claim is falsified; report as PRICED_IN or ACCURACY_ONLY as applicable, and
  do not describe the pooled result as supporting this hypothesis.
- If **NOT CONFIRMED** → record it in the run log and move on. Do not re-specify the metric
  and re-run. Any re-specification requires a new pre-registration with a new id, and both
  count toward the multiple-comparisons total.
