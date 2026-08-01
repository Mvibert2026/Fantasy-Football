---
ID: FR-2026-08-01-respectability-check-large-unexplained-deviation
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Respectability check: large unexplained deviations from consensus are a red flag to investigate, not a penalty to minimize

Founder's own words, chat 2026-08-01, clarifying the analyst-parity bar he had set earlier the same
day:

> "Don't take that bar literally. But we need to be respectable. If we have too many major
> differences from consensus it's probably a red flag."

## Why it matters

**It softens the "on par with any single analyst" bar and adds a sanity constraint that ADR-069, read
literally, does not provide.** ADR-069 removed consensus from the development loop entirely. Read
carelessly, that licenses a board that disagrees with the entire market and calls it independence.
The founder is closing that gap.

**Recorded in `CLAUDE.md` §2a** so the next agent reading ADR-069 does not conclude consensus is to
be ignored outright.

## Initial read

**The distinction is load-bearing and must survive restatement, because collapsing it in either
direction breaks something:**

- **Never a penalty to minimize.** Scoring the model on closeness to consensus rebuilds a
  consensus-derived board by the back door -- and takes scoring portability down with it, since a
  board pulled toward a generic 12-team full-PPR consensus cannot respond to this league's half-PPR
  and stacking bonuses. That is precisely the failure ADR-069 exists to prevent.
- **Always a flag to investigate.** A board that disagrees violently and cannot state *why* has a
  bug. The deliverable is an **explained-deviation report**, not a deviation budget.

**This method already has a 2-for-2 record on this project, both found by the founder by eye:**

| Disagreement | Verdict |
|---|---|
| Taysom Hill -- ours 25, consensus 171 (146 places) | Real defect, games channel |
| Joe Burrow -- ours QB26, consensus ~QB4 | Real defect, games channel |

Neither was a real disagreement about football. Both were the projected-games defect surfacing.
That is strong evidence the diagnostic works *and* a hint about where to point it first: **rank
deviations by size, and expect the games channel to dominate the tail.**

**Implementation sketch (not built, not dispatched).** A report that, per position: counts
deviations above a threshold, ranks the largest, and requires a stated reason per entry. Cheap. The
natural consumer is the board export and the draft-room UI -- the founder has twice done this
manually by scrolling a list, which is the strongest possible argument for surfacing it.

**Open question for whoever builds it:** the threshold. "Major difference" is undefined and should
not be guessed -- calibrate it against the observed analyst-to-analyst spread now that 66 individual
expert boards exist for 2026 (`rankings`, `source` = `fantasypros_expert_<id>`). A deviation that is
ordinary *between analysts* is not a red flag; one that exceeds the whole analyst range is. That
also makes this the first genuinely useful application of the per-analyst data, which cannot serve
its original purpose (accuracy comparison) until a season with per-analyst boards has been played.
