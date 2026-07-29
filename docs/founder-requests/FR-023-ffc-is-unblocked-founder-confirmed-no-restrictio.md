---
ID: FR-023
STATUS: NEW
SOURCE: claude code session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
FFC is unblocked - founder confirmed no restrictions, use as needed

> "I asked, we hve no blocks from FFC, we can use as needed"

Founder's own words, 2026-07-29. He contacted Fantasy Football Calculator directly and reports no
restrictions on use.

## Why it matters

FFC was recorded as **blocked** across this project, and the block was load-bearing. Its terms could
not be retrieved, so the conservative default applied and no scraping was permitted. That decision
is cited in `docs/research/source-audit-2026-07.md` and in threads 055, 057, 062, 064 and 078, and
it is why an agent once correctly refused a PM instruction to scrape it.

Everything those threads were waiting on is now actionable:

- **FFC ADP history back to 2007.** Real archival history, unlike MFL, whose endpoint serves a
  rolling accumulated aggregate stamped with today's date — re-pulling a past season from MFL and
  treating it as a preseason board is look-ahead bias, which is why the daily snapshots exist at all.
- **Pick-level ADP velocity** (thread 078). MFL genuinely cannot supply this: `TYPE=draftResults`
  requires a league ID this project does not hold, and there is no platform-wide per-pick export.
  FFC was the only remaining route, so this went from blocked to merely unbuilt.
- Any ADP-vs-value work, and availability-model calibration inputs that need real historical draft
  behaviour rather than a single season.

## Initial read

**This is broader than the earlier authorisation and supersedes it.** D-021 had permitted a *one-time
historical pull* via the HTML endpoints. "Use as needed" covers recurring use, which D-021 explicitly
did not — thread 078 turned on exactly that distinction.

Recorded in `docs/pm/MEMORY.md` §4 under source constraints. The old entry is kept in edited form
rather than deleted, because it explains why an agent refused an FFC instruction in the past — that
refusal was correct at the time and should not read as a malfunction to a future session.

**Conditions that still hold and were not lifted:**

- Scoped to **private use by one person**. Void if the product ever reaches a second human, alongside
  D-020 and D-021.
- **Rate-limit and cache anyway.** Permission is not licence to hammer a small hobby endpoint; the
  same courtesy the MFL ingester already applies (descriptive User-Agent, one request per day,
  backoff on 429) should apply here.
- Pull once per season-format and cache the result, rather than re-fetching.

**Not yet scoped or built, and deliberately not dispatched in the session that recorded this** — the
week's capacity was committed to finishing the move off the founder's machine. The natural owner is
data-ops. Sequencing note: the *shape* of what to collect should follow the availability review
(M-2), which is the thing that would consume it, rather than collecting first and deciding later.
