---
ID: FR-073
STATUS: DONE
SOURCE: backend session 2026-07-30, ADP vs production dispatch
RAISED: 2026-07-30
---

## Request
Founder's own words: "so now we can also look at ADP vs Production and try to establish patterns."
Dispatched and completed this session as the ADP-vs-production structural-mispricing analysis
(`docs/analysis/adp-vs-production-2026-07-30.md`). Logged here per the standing rule that every
founder want gets its own file even when a dispatch already covers it, so status is trackable
independent of the dispatch that carried it out.

## Why it matters
Directly informs the ranker's factor-testing pass — a real, era-stable (though only partially
holdout-confirmed) candidate mispricing was found: early-round RB overpriced relative to
same-round peers at other positions, and young WR/TE (age <=23) underpriced. See the writeup for
full results, confidence labels, and the honest null results (games missed, team change,
volume-vs-efficiency split all failed to show a reliable pattern).

## Initial read
Real, actionable follow-up work surfaced during this analysis, not requested by the founder in so
many words but a direct consequence of what was found: (1) this project has no real 10-team
historical ADP source anywhere -- only 12-team FFC mock-draft ADP was usable, which is a genuine
gap if the founder wants this analysis validated against the league's actual market; (2)
`play_callers` (coach/coordinator identity) is not populated in this environment's `nfl.db`, so the
"new coordinator" factor the founder's own schema design (`coach_id` as first-class) anticipated
could not be tested -- only a narrower "team changed" proxy was, and it found nothing. Both are
scoping questions for PM/founder, not decided here.

## Status update, 2026-07-30 (backend)
Marking DONE for the analysis itself -- see `docs/analysis/adp-vs-production-2026-07-30.md`.
Methodology review handed to strategist via thread 096
(`docs/handoffs/096-adp-vs-production-methodology-review.md`) before anything here should reach
the ranking model.
