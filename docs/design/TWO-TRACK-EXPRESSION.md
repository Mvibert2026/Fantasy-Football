---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 4 (briefing §12)
DATE: 2026-07-29
COVERS: FR-042, FR-027 — 26 of 27 leagues
---

# How a screen says "this league is the generic track"

The current empty state is *"Not available for this league"*, and the briefing's criticism of it is
exactly right: it does not say whether it ever will be. One string is doing the work of three
different claims.

## Split it into three

| State | What it means | Voice |
|---|---|---|
| **primary** | Westwood. Full custom ruleset verified against the live platform, nine named opponents, modelled tendencies. | — |
| **generic** | Standard scoring, varying PPR only. Opponents are not modelled **and will not be** — that is what the track is. | Indicative. Confident. |
| **not yet** | Reserved for data that genuinely could arrive: a prior-season draft board for this league would populate opponent profiles. **Names the missing input.** | Expectant. |

## Put the track on the league selector

The thinning should be **expected before it is encountered**, not discovered four screens in. The
selector carries the track as a property of the league:

    * WESTWOOD        · primary track · full ruleset · 9 opponents modelled
    o ETHAN'S EXPE... · generic track · standard scoring · opponents not modelled

## Why this stops it reading as broken

**"By design" and "not yet" are different sentences.** A generic-track league has no opponent model
because that is what the track *is*, and a screen saying so confidently is a screen working
correctly. The softer, expectant wording is reserved for the case where data could actually arrive.
Using one string for both is what makes a correct screen look like a failed one.

Four screens thin out on league switch (non-primary leagues carry 7 export files against primary's
11). With the track on the selector, all four thin out *as advertised*.
