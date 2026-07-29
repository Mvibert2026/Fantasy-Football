---
ID: FR-039
STATUS: ANSWERED
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

---

### ranker · 2026-07-29

Measured. Full pass: `docs/ranking/bottom-up-research-pass-2.md`. Code:
`experiments/bottomup/pass2_te_adp.py`. **Exploratory — nothing registered, nothing shipped.**
The one confirmatory test worth running is an *ask* in thread **087** to `strategist` with its
stopping condition committed in advance, and it has not been run.

**The three questions, answered in order.**

**1. Where the mispricing sits: the founder's strategy is not supported.** The unpriced *error* is
flat across the TE draft range — residual RMSE 45.9 / 51.0 / 45.7 / 43.5 / 41.0 / 43.4 from TE1-3
down to TE25-40, where RB falls 104.7 → 61.2 over the same span. That flatness is real and new. But
error is not opportunity. Top-6 TE hit rate is steeply front-loaded with no late bump: **TE1-3
66.7% [39.1, 86.2] · TE4-6 41.7% [19.3, 68.0] · TE7-10 25.0% [10.2, 49.5] · TE11-16 4.2% [0.7,
20.2] · TE17-24 9.4% [3.2, 24.2] · TE25-40 3.1% [0.9, 10.7]**.

And the measurement that settles it: of the 24 top-6 TE seasons in 2021-2024, seven came from
pre-draft TE11+, and **only two of those seven were inside the 150 picks of a 10-team, 15-round
draft** — one, after correcting for the measured ECR→ADP shift. Schultz (ECR 265), Hill (346), Jonnu
Smith (204), LaPorta (161), Engram (158) were **waiver-wire adds, not late-round picks.** In the band
that genuinely is the last four rounds, ECR 111-150, 2 of 27 TEs finished top-6 — **7.4% [2.1,
23.4]** — and the two were a 32-year-old Gronkowski and David Njoku at TE10.

**The half of the instinct that survives, and it is the useful half.** This does *not* argue "take a
TE early". It argues for **TE7-10, overall ECR 75-113, rounds 8-11**. At that cost a tight end's mean
realised VBD is **−12.2, identical to a wide receiver's −12.2** at the same pick (RB −22.7, QB
−56.3) — the pick is free relative to its alternative — and it buys a 25% top-6 shot. **One such
pick (25.0%) beats three darts at ECR 111-150 (20.6%) and costs two fewer picks.**

**2. Forecastable? Essentially not — and "take more shots" does not rescue it.** Base rate per late
shot (TE11-40): top-6 **5.0% [2.3, 10.5]**, top-10 15.0% [9.7, 22.5]. Of eleven pre-draft-knowable
signals, only two have intervals excluding a coin flip, and **both are the market restated** —
consensus rank itself (AUC **0.649 [0.56, 0.74]**) and the panel's most optimistic expert (**0.692
[0.61, 0.78]**). Expert disagreement, my one cheap novel idea, is dead (0.487 / 0.500 / 0.432).
Prior points-per-game runs *backwards* (0.362). The queued snap-share TE arm is absorbed here and is
not supported at TE11+ (0.630 [0.36, 0.89]). A composite I built after seeing the components scored
0.752 and is **not** reported as a finding — that is what an overfit looks like.

So the answer is a third one, neither "take the right one" nor "take more": **take one, earlier, in
the window where it is free.**

**3. Kraft: the pattern does not recur, and the example is misremembered.** Going into 2025 Tucker
Kraft was **consensus TE11 at overall ECR 105**, coming off a **TE9 finish in 2024** (138.3 pts, 17
games). Adjusted for the measured TE ECR→ADP shift, his real cost was around pick 117 — round 12. He
was a mid-round tight end off a top-ten season sitting one slot outside the starter tier, **not a
late-round unknown**; the market had repriced him a full year before the season being remembered.
Correctly priced, the example supports the mid-round window above, not the late-round strategy drawn
from it. **No 2025 outcome was read** — those are pre-draft rows, and thread 087 asks strategist to
confirm that is clean.

Tested rather than assumed, 2021-2024, "Kraft type" defined entirely pre-draft (TE11+, ≤3rd NFL
season, NFL-drafted): top-6 rate **1.9% [0.5, 6.6]** against **2.5% [1.1, 5.8]** for other late tight
ends. No advantage — marginally worse.

**What binds this, and it is now the priority.** There is **no ADP history in the database at all** —
only FantasyPros ECR, 2021-2025, four usable seasons, 24 top-6 TE outcomes in total. Every
"late-round" claim above uses ECR rank as a draft-cost proxy, calibrated on the single season where
both exist (2026: TE median ADP − ECR **+12**, IQR [+4, +16], n=18). Thread **055** (FFC half-PPR
ADP history, 2018-2024) is already open to `data-ops` and would take this from 4 seasons to 7 *and*
replace the proxy with a real draft position. It is the single thing that would most change
confidence in this answer.

**Escalated rather than celebrated:** TE1-3 produced exactly two top-6 tight ends in each of the
four seasons (2, 2, 2, 2) — a 3.9% coincidence under its own base rate. I do not believe it is
leakage, but the regularity must not be read as precision.

**Status → ANSWERED (exploratory).** Nothing reaches the board until thread 087 closes.
