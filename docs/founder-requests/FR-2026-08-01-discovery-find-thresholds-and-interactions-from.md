---
ID: FR-2026-07-31-reverse-discovery
STATUS: NEW — registered, not started
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGH — changes how the whole campaign generates hypotheses
NEEDS: strategist (the search/test split), then ranker
---

## Request

> "Is there any way to identify them without having to come up with the idea to test it? Like a
> reverse identification via trend analysis somehow."

**Yes. And he has already done it by hand — twice, today, successfully.**

Looking at the 2026 board he identified an availability problem from Burrow and Lamb, and a QB tilt
from Allen and Jackson. Both were confirmed by measurement within minutes. **That is exactly reverse
identification: read the errors, infer the missing mechanism.** The ask is to systematise what his eye
did.

## Why this matters more than another factor

Every hypothesis in the campaign so far came from a person or a publication. That bounds the search to
what somebody already thought of — and the analyst sweep established the ceiling on that route:
**the published literature is the crowd that makes consensus**, so factors sourced from it are priced
in by construction. 90 tests, zero edges.

**Discovery from residuals is not bounded that way.** It can only find what is actually in *our*
errors, which is the one place consensus cannot have already looked.

## The methods, cheapest first

**1 — Residual analysis. Cheap, interpretable, no ML, and it is what the founder did by eye.**
Take v1's per-player error against realised finish and ask what the large-error players have in
common: position, age, prior-season games, draft round, target share, team change. A cluster is a
missing mechanism. **This needs no new data and no new modelling** — the residuals already exist in
`experiments/bottomup/results/`.

**2 — Breakpoint detection on a single variable.** Segmented regression or a one-variable tree finds
where a relationship changes slope. This is the direct answer to "where is the threshold" for any
factor already in the model, rather than guessing 350 / 375 / 400.

**3 — Tree-based discovery.** A decision tree split *is* a threshold; a tree with depth > 1 *is* an
interaction. Gradient boosting plus partial-dependence plots would surface both classes automatically
across every feature at once.

`CLAUDE.md` §6.3 says start with weighted/regression approaches, **not ML**, and escalate "only if
backtesting demonstrates the simple model is leaving real signal on the table." Whether ~90 linear
nulls constitute that demonstration, or its opposite, is a real question and **strategist's to answer,
not PM's.** Note the guardrail's own next line: *"We should use machine learning" is not a finding.*
Trees here would be a **search device**, not a shipped model — that distinction is what keeps it
inside the rule.

## The thing that makes or breaks it

**A searched threshold is not a tested threshold.** A tree examining 30 features at ~200 candidate
splits each performs roughly 6,000 implicit comparisons. The p-value of "the best split found" is not
the p-value of a pre-specified split, and treating it as one is the most efficient way to manufacture
a false finding this project could adopt.

**So discovery and confirmation must be separated structurally, not by intention:**

1. **Search** on training seasons only — output is a *candidate list*, never a finding.
2. **Pre-register** each candidate with its threshold fixed, into the campaign manifest, counting
   against the campaign `M`.
3. **Confirm** on seasons the search never saw.
4. The sealed 2025 holdout is the final arbiter and is **gated on fable** (`CLAUDE.md` §6.3).

This project already has all four pieces — the ledger is the denominator, `docs/preregistration/`
exists, the campaign manifest is sharded, and the holdout is logged. **Nothing new is needed except
the discipline of not reporting a searched result as a measured one.**

## Where to start, when this is picked up

**v1's residuals.** It is the only model here that disagrees with consensus at the player level, it
loses at three of four positions, and *why* it loses has never been examined. The founder found two
mechanisms in that output by eye; a systematic pass over the same residuals is the highest-value
version of this idea and needs no new data at all.
