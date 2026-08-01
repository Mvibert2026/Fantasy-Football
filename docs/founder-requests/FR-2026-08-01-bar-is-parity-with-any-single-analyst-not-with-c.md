---
ID: FR-2026-08-01-bar-is-parity-with-any-single-analyst-not-with-c
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Bar is parity with any single analyst, not with consensus; ingest Vegas lines and other unused public inputs

Founder's own words, chat 2026-08-01, on being shown v2's 2024 rank correlations against consensus
and the adjusted board:

> "Well we don't use Vegas lines and other things. There's room to improve. We should be able to get
> very close to consensus. They use public info. And each analyst included doesn't have the best
> rankings every year. We want to be on par with any single analyst."

## Why it matters

**This redefines the target, and to a materially easier and more appropriate one.** Consensus (ECR)
is an *average of many analysts*; averaging cancels individual error, which is why an aggregate
routinely outperforms most of its own members. "Beat ECR" and "match a good analyst" are different
difficulties. The founder has picked the one that matters for drafting a real team.

**We may already meet the new bar at two positions and cannot prove it.** On 2024, v2 sits at
**-0.031 vs consensus at WR** and **-0.022 at TE**. Individual analysts almost certainly scatter
around their own consensus by more than that, so v2 is plausibly already inside the analyst pack at
those positions. We cannot say so, because only the *aggregate* (`fantasypros_ecr`) was ever stored
-- there is no per-analyst distribution to place ourselves in.

**Measured gaps, same season:** QB -0.205, RB -0.071. QB remains the largest single weakness.

## Initial read

**Two work items, both data acquisition rather than modelling -- the cheap kind.**

1. **Per-analyst rankings.** Ingest individual expert boards (FantasyPros publishes them, plus
   accuracy history) so "on par with any single analyst" becomes a *measurable* claim with a
   distribution behind it, not an aspiration. This also gives the honest way to report v2: its
   percentile within the analyst field, per position, rather than a single delta against an
   aggregate that is structurally hard to beat. Verify licensing/terms before scraping (CLAUDE.md
   §5) -- free tier only, the founder has declined to pay.
2. **Vegas odds -- confirmed absent.** Checked 2026-08-01: **zero odds tables exist in
   `data/nfl.db`.** Win totals, implied team totals, spreads and player props have been listed as a
   source in CLAUDE.md §5 since the beginning and were never ingested. This is a genuine untouched
   public input, and it is plausibly one of the things feeding analyst opinion that we have no
   channel for.

**Caution against over-claiming the second one.** Vegas season win totals are a *team* signal; the
measured deficit in v2 is concentrated in the **projected-games** channel (Fable M2-1), not in team
context. Odds may well help, but they should be registered and tested as arms like anything else --
not adopted because the reasoning is appealing. Implied team totals and player props are the more
directly relevant slices; win totals are the weakest.

**Sequencing.** Both are `data-ops` work and neither blocks the other. Neither blocks the pending
strategist G2a ruling, which remains the single highest-value open decision. Note also that the
factor ledger (`docs/factor-ledger.md`) should gain rows for the odds-derived factors so they enter
the multiple-comparisons denominator when tested rather than after.
