---
ID: FR-060
STATUS: NEW
PRIORITY: HIGH
ROUTED-TO: ranker
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
ADP versus production — find where the market is systematically wrong

Founder's own words:

> "so now we can also look at ADP vs Production and try to establish patterns"

## Why it matters

**This is the measurement the whole edge claim rests on, and until tonight it could not be made.**

Passes 1 and 2 asked what consensus fails to price — but using **expert consensus rank as a proxy for
draft cost**, because no ADP history existed. Those are different quantities: measured 12 places
apart for tight ends (median ADP − ECR **+12**, IQR [+4, +16]). Every "late round" claim in pass 2
carries that proxy error, and the ranker flagged it as the binding constraint on its own findings.

That constraint is gone. `ffc_half_ppr_12team` covers **2018-2024** in this league's format;
`ffc_non_ppr_12team` covers **2013-2024**. So the question can now be asked properly: **given where a
player was actually drafted, what did they return?**

## Initial read

Not the founder's own words — PM's read.

**This is not a separate track from the bottom-up model — it is the map that tells the model where to
aim.** Where the market is systematically wrong is exactly where a bottom-up projection can win.
Where it is right, no model beats it and effort spent there is wasted. Sequenced accordingly: the
bottom-up pass is running now, and this should inform its second iteration rather than compete with
it for the same agent.

**What "patterns" should mean here, concretely:**

- **By draft position band.** Is surplus concentrated early, late, or in a middle window? Pass 2
  found exactly one such window for TE (rounds 8-11); the same question is unanswered for RB, WR, QB.
- **By position, per band.** The pooled answer hides the useful one.
- **By season.** A pattern present in 2018 and absent since is a regime change, not an edge —
  and this project has already been caught pooling a collapsing quarterback market flat.
- **Bust rate and hit rate separately, not just the mean.** A band whose average is fine because two
  hits offset eight misses is a different proposition from one that is uniformly adequate, and the
  founder drafts one roster, not a distribution.
- **Where variance is priced wrong**, not just level. This league pays for ceiling through stacking
  bonuses; a market that prices expected points correctly can still misprice ceiling.

**The traps, all of which this project has hit before:**

1. **Survivorship.** The universe for each season must be everyone drafted at that ADP, including
   those who returned nothing. Building it from players who scored deletes every bust and manufactures
   surplus everywhere.
2. **The market moved.** ADP in 2013 is not the same object as ADP in 2024 — different platforms,
   different roster conventions, different pass rates. Test whether older seasons help or hurt before
   pooling them (`CLAUDE.md` §6.4).
3. **Format mismatch.** The half-PPR series is 12-team; this league is 10-team. Note it, do not
   silently treat them as the same.
4. **Multiple comparisons.** Bands × positions × seasons is a large grid, and something will look
   significant. Register the confirmatory version with `strategist` before running it — a pattern
   found by sweeping is a hypothesis, not a finding.

**The honest prior:** the strongest patterns will most likely be things the market already knows and
prices — the point of the analysis is to find the residual after that, not to rediscover that early
picks outperform late ones.
