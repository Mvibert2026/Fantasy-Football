---
FROM: design
TO: pm, research
STATUS: OPEN
DATE: 2026-08-01
COVERS: the news feed — empty states only, as instructed. No content rules, no populated layout.
---

# The news feed — six empty states, no populated one

The brief says an empty panel from failed ingestion must not look like an empty panel from a quiet
news day. **There are not two of those cases — there are six**, and four of them currently have
nowhere to render, which is how this ships wrong.

| | Cause | What the panel says | Why it is not the one above |
|---|---|---|---|
| 1 | **not built** | "News is not built yet. No source is wired." | Today's state. Says nothing about whether news exists — only that the app cannot see any. |
| 2 | **fetch failed** | "Couldn't reach the source. Last successful check: yesterday 18:40." | The app tried and failed. Loud, and carries the last time it worked so he can judge the gap. |
| 3 | **stale** | "Last checked 2 days ago. Items below may be out of date." | Items exist but the window lapsed. Renders content and stamps it — not empty, but not current. |
| 4 | **global zero** | "Source reachable, 0 items in the last 24 hours. A global zero is unusual — worth checking the source." | Technically empty, statistically suspicious. |
| 5 | **per-player zero** | "No news for him in the last 7 days." | Ordinary, reads calmly. Names its window, so it is a claim about a period rather than all history. |
| 6 | **not covered** | "This source doesn't cover him." | Partial coverage is not silence. |

## State 4 is the one that will mislead him on draft morning

A **global** feed reporting zero items is far more likely to be a broken source than a genuinely
silent news day across a whole league. **So a global zero is never rendered as calm.** It states the
count, the time it was checked, and that a global zero is unusual — because "no news" on the morning
of a draft is precisely when he would most trust the app and be most wrong to.

A **per-player** zero is ordinary and reads calmly. Same emptiness, different prior, different copy —
and the panel has to know which one it is.

## Two contract asks, without which four of the six are unrenderable

These are asks on whoever specifies the source, not design decisions — but they must be in the
contract from the start, because **a feed that returns only a list cannot distinguish four of these
six states no matter how it is drawn.**

1. **The feed must return a fetch outcome, not just a list.** Reachability, the time of the attempt,
   the time of the last success, and an item count. An empty array cannot say why it is empty.
2. **The feed must declare its coverage** — which players or teams it claims to cover — so state 6 is
   distinguishable from state 5. Without it, silence about a player is ambiguous between "nothing
   happened" and "never looked."
