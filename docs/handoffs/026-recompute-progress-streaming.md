---
ID: 026
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: Settings editor build
---

## Ask
Implement recompute job progress streaming: a stage name plus percent complete, emitted during a
scoring recompute, rather than only a final callback. This is item 4 in the confirmed backend gap
list.

Answer thread 015 question 1 first — the real stage names — then build to those. Design assumed five
named stages; if the pipeline genuinely has three or seven, the design changes rather than the
pipeline being bent to fit.

Also from thread 015: the job must be **league-scoped, not session-scoped**. A session-scoped job
vanishes when the tab closes, which silently breaks multi-device use and makes the
"finished-but-unapplied" state impossible to implement.

## Why
A ~60-second wait with a bare progress bar reads as a hang. Design's Settings spec is built entirely
around named stages, and without them the interaction degrades to a percentage with no meaning — the
user cannot tell a slow recompute from a dead one.

This also underpins the `04-ready-to-apply` state Design added: a job whose result outlives the
request is only possible if the job belongs to the league.

## Done looks like
Streaming endpoint emitting real stage names, league-scoped job lifecycle, a documented retention
window for a computed-but-unapplied result, and a `superseded` response for the restart case. Reply
in thread 015 with the actual stage names so they reach Design. Commit hash and test count.
