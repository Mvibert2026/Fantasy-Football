---
ID: FR-041
STATUS: NEW
PRIORITY: MEDIUM-LOW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Prose, design and relevance review of Strategy guide, Methodology and Glossary

Founder's own words:

> "What about the prose and design of those three screens. Relevance etc. they need a review. But
> that can be mid priority to low."

Raised directly after being told all three were written 2026-07-26 and untouched since.

## Why it matters

These are the three screens that explain the product to its user. If the board is wrong the founder
can see it; if the explanation of the board is wrong or stale he cannot, and it will quietly teach
him to trust the wrong things. That is the same failure class as a present-but-inert control, one
level up.

Priority is the founder's own: **mid to low.** Not before the draft-critical work.

## Initial read

Not the founder's own words — PM's read. Four things measured 2026-07-29 that the review should
start from rather than rediscover.

**1. The Strategy guide is empty in 26 of 27 leagues.** Only the primary league export carries
`strategies.json`. Every other league renders *"Not available for this league. Strategy simulations
have not been run for it yet."* Honest, but it means the screen exists for exactly one league and the
founder has at least three.

**2. Non-primary leagues are missing four artifacts, not one.** Primary carries 11 export files;
each of the 26 sub-league directories carries 7. Absent from all of them:
`strategies.json`, `player_descriptions.json`, `season_stats.json`, `weekly_finishes.json`. So
switching league degrades more than the Strategy guide — this should be scoped as a whole rather
than screen by screen.

**3. The Glossary is thinner than the app it explains.** 13 terms. ADP is being added separately
(dispatched 2026-07-29), but the review should ask what *else* the board shows and the glossary does
not define — `structural_adjustment`, `evaluative_adjustment`, `ci_applies_to`, `roster_status`,
`suspension_flag` and the tier labels are all on screen now.

**4. Methodology's most valuable section is its least prominent.** *"Tested and found nothing"* —
publishing what was tried and did not hold up — is the part of this product that would most earn a
stranger's trust, and it sits fourth of five under a heading that reads like an appendix. That is a
design judgement, which is why this is a design review and not a copy-edit.

**Sequencing note:** do not start this until the ADP glossary/methodology work lands. Reviewing
prose that is mid-change wastes the review.

**Ownership:** the *relevance* half (what should be on these screens at all, what the null and empty
states should say, what deserves prominence) is `design`. The *accuracy* half (does the prose still
describe what the code does) needs someone with repo access — `librarian` or `backend`. Do not
collapse them into one pass; they fail differently.
