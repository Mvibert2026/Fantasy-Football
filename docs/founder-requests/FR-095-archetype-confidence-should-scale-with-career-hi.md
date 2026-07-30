---
ID: FR-095
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Archetype confidence should scale with how much career history a player has

Founder's own words:

> "we have multiple seasons of history for most players - the longer, the more confident we can be
> in archetype"

## Why it matters

Correct, and it is the missing piece in `docs/ranking/archetypes-proposal.md`. That proposal defines
`UNCLASSIFIED` as a binary state — a player either meets criteria or does not. The founder is
pointing out that classification is not binary, it is **graded by sample size**. A rookie with eight
games and a six-year veteran with ninety should not carry the same confidence in the same label,
even when both technically clear the same threshold.

Practically this means archetype assignment needs shrinkage toward the positional prior, with the
shrinkage weight driven by games observed — the same empirical-Bayes machinery the component model
already uses (`experiments/bottomup/components/`, single constant fitted on training seasons only).

## Initial read — the trap in the premise

Not the founder's own words — PM's read. **The premise is right but incomplete, and the incomplete
half could do damage if it is implemented naively.**

More history increases confidence about a **stable property**. It can actively mislead about a
**situational** one. A back who was a committee player for three seasons and has just become the
lead back has a long, consistent, and now-wrong history. Weighting that history more heavily because
there is more of it would encode exactly the stale role the founder is trying to draft ahead of.
This is `CLAUDE.md` §6.4 (non-stationarity) at the player level rather than the league level.

**The resolution is to split the archetype dimensions by what kind of thing they measure:**

| Dimension type | Examples | How history should be used |
|---|---|---|
| **Stable trait** — properties of the player | aDOT band, catch rate, YAC tendency, rushing share for QBs, athletic profile | Career history is strong evidence. Pool across seasons, shrink by total games. The founder's rule applies directly. |
| **Situational role** — properties of the job | snap share, target share, committee vs. lead back, in-line vs. slot, handcuff status | Career history is **weak** evidence and can be actively wrong. Weight recent seasons heavily; a depth-chart or coaching change should reset rather than dilute. |

This distinction is not currently in the proposal, and it changes the shape of the system: confidence
in a stable-trait dimension should rise with career length, while confidence in a situational
dimension should be dominated by recency and by whether the situation just changed.

**It also connects to FR-094 (sleepers).** A breakout is by definition a *situational* change. A
sleeper screen that leaned on career averages would systematically miss exactly the players it
exists to find — which is why that work was already scoped to within-season trend rather than season
averages. The two requests are the same insight seen from opposite ends.

## Open question for whoever implements

Is career length itself confounded with quality? Players survive in the league partly by being good,
so a long history is not a neutral sample — it is a survivor's sample. Long-career players may look
more classifiable partly because marginal players were cut before accumulating history. Worth
measuring rather than assuming it away.
