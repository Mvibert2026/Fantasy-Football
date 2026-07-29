---
ID: FR-021
STATUS: NEW
SOURCE: cowork chat 2026-07-29
RAISED: 2026-07-29
---

## Request
Founder's own words: "I read the terms we are good to go. No blockers."

Said in direct response to the PM raising Fantasy Football Calculator (FFC) as one of two
items needing a founder decision — specifically: get a real answer on FFC's terms of use, or
accept the conservative-default block permanently and calibrate availability only from the
founder's own mock drafts.

Read as: the founder has personally reviewed FFC's terms, found nothing prohibiting our use,
and is clearing the block.

## Why it matters
This is the gating decision for pick-level draft data, which is the gating input for
availability calibration — and availability ("will he last until my next pick") is the actual
product. Today those numbers are calibrated on zero real drafts.

It also answers handoff thread 078, which has been OPEN to PM since 2026-07-27 waiting on
exactly this call. Thread 078 established that MFL cannot substitute: its `draftResults`
export is league-scoped and there is no population-level pick-by-pick endpoint, so FFC was
the remaining path.

## Initial read
**Provenance matters here and should not be flattened.** The prior block was recorded in
`docs/research/source-audit-2026-07.md` as *ToS unretrievable → conservative default* — the
terms could not be fetched programmatically, so policy blocked the source rather than guess.
The block is now lifted on the founder's personal review, not on a retrieved and archived
terms document. Those are different evidentiary states, and a later agent must not read this
as "terms machine-verified and archived."

Recommended alongside the build, not before it:
- Capture what the founder actually read — URL, date, ideally an archived copy — into
  `docs/research/source-audit-2026-07.md`, replacing the "unretrievable" line in place so the
  finding and its reversal live together.
- Thread 078 drew a distinction between a *one-time historical pull* and a *recurring
  systematic capture*. The founder's clearance did not name a scope. Worth confirming which
  he means before standing up anything scheduled.
- Ordinary scraping hygiene applies regardless of terms: rate limiting, honest user agent, no
  evasion of blocks.
