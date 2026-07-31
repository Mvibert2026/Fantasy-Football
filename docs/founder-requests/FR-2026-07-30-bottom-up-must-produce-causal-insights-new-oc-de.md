---
ID: FR-2026-07-30-bottom-up-causal-insights
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — the product payoff of question 1
NEEDS: ranker, data-ops
---

## Request

> "Plus with full bottoms up our insights can be fairly deep. So and so has a new OC and we expect
> routes run to increase.
>
> Or the starter from last year left. Etc.
> I don't need to hear the issues. Solve them. Others do."

## What he is naming

**The product payoff of a bottom-up model, not another factor request.** A model built from player
inputs can *explain itself in football language*; a model built from consensus rank cannot say
anything except "consensus likes him." His two examples are the shape of the output he wants:

- *"New OC, so we expect routes run to increase"* — coordinator change → scheme → opportunity
- *"The starter from last year left"* — departed teammate → vacated opportunity

Both are **causal, prospective, and specific to a player**. Neither is expressible from a rank.

## The two factors these map to, and both are unblocking now

| His example | Registry | Was blocked by | Status now |
|---|---|---|---|
| New OC → routes up | **#29 Coordinator continuity**, High edge | PFR HTTP 403; `coach_id` has nothing behind it | A coordinator table was ingested 2026-07-30. `coach_id` is already a first-class schema dimension (`CLAUDE.md` §4) |
| Starter left → opportunity vacated | **#28 Vacated targets & carries**, High edge | No pre-season roster table; ran on a Week-1 depth-chart proxy and was HARMFUL at RB — with harm concentrated in exactly the bucket the proxy contaminates | `load_rosters_weekly()` is being ingested now — the function the registry row names as the fix |

**#28's earlier harmful result is a proxy artifact, not a verdict on the factor.** The registry row
says so itself. It has never been tested with real pre-season rosters.

## The standing instruction attached

> "I don't need to hear the issues. Solve them. Others do."

Recorded as a working-style directive: **report outcomes, not obstacles.** Obstacles go in threads for
the agent that owns them, not into founder-facing summaries. An issue worth raising to him is one
that needs his decision — everything else is work.
