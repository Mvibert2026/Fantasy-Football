---
ID: FR-039
STATUS: NEW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
ROUTED-TO: ranker
---

## Request
Late-round TE is the draft-strategy expression of the unpriced-TE finding

Founder's own words:

> "The tight end finding is interesting and for draft strategy. If we aren't taking tight end or QB
> early, then finding a tight end at late round ADP who is underrated is a good edge. Like Kraft
> last year."

## Why it matters

This is the founder converting a measurement into a decision rule, and it is the right instinct.

The ranker's first bottom-up pass (`docs/ranking/bottom-up-research-pass-1.md`) measured, per
position, how much of a player's season is stable quality that consensus does **not** already price:

| Position | Stable quality consensus does not price |
|---|---|
| TE | **33.6%** |
| RB | 15.1% |
| WR | 15.1% |
| QB | 6.3% |

Tight end is roughly three times the opportunity of anywhere else on the field, confirmed three
independent ways. That is a measurement. **The founder's addition is where in the draft it can
actually be spent** — and that is the part the research pass did not answer.

His reasoning: if the roster plan does not commit an early pick to TE or QB, then the TE mispricing
is only realisable in the late rounds, because that is where the picks are. An edge that exists only
at TE1 prices is not an edge this roster construction can use.

## Initial read

Not the founder's own words — PM's read.

**This is a directive to the ranker, not an open question.** It narrows phase 2 from "TE is
mispriced" to a testable claim with a decision attached.

Three things have to be established, and none of them is established yet:

1. **Where in the ADP distribution the TE mispricing actually sits.** 33.6% is a pooled figure
   across all tight ends. If the unpriced share is concentrated in the top 5 TEs, the founder's
   strategy does not capture it and the finding argues the opposite way — take a TE early. If it is
   flat or back-loaded, he is right. **This is the question, and it is directly measurable.**
2. **Whether late-round TE hits are forecastable in advance**, or only identifiable afterwards.
   A position can be mispriced and still be unforecastable — the pass already found availability is
   near-unforecastable (r = 0.09–0.18) despite mattering enormously. If the late TE hit rate is
   coin-flip, the correct advice is "take more late TE shots", not "take the right one".
3. **The Kraft example must be tested, not assumed.** It is one player, named from memory, and the
   project's own calibration prior is that four of five registered predictions here were wrong and
   *every miss over-credited a situation story*. A single vivid case is the most reliable way to be
   wrong. Check whether the pattern it represents holds across seasons before any of it reaches a
   ranking.

Sequencing: this is the natural second phase of the ranker's work and it is more concrete than what
was queued (a TE arm on `snap_counts`). It should absorb that rather than run beside it.

Ownership: `ranker` measures. `strategist` registers any confirmatory test before it runs. Nothing
from this reaches the board until that loop closes — the ranker does not grade its own homework.
