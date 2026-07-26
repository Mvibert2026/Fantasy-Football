---
ID: 001
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Three small changes, all in `docs/`:

1. **Adopt `docs/CURRENT-STATE.md` as canonical.** It already exists and is populated as of
   `3ea391b`. Verify its figures against the working tree and correct anything I got wrong — I read
   the repo through a file bridge, not a live shell, so I could not run the suite myself.
2. **Demote `docs/status.md`.** Add a header at the very top:
   `> HISTORICAL LOG — do not read for current state. See docs/CURRENT-STATE.md.`
   Do not restructure or delete its content; the history is worth keeping.
3. **Fix the contract stamp in `docs/assistant-context.md`.** Line reads
   `Contract version referenced below: **1.6.0**`. Actual is **1.7.0**. Check whether anything else
   in that file went stale with the 1.7.0 bump while you are in there.

## Why

`status.md` is 52 KB and carries three separate "current state" headers reading 139, 191, and 202
tests, plus roughly fifteen internal contradictions — contract 1.6.0 is never introduced anywhere,
Task B appears as "deferred", "not started", and "already built" in three places, and ADR-035 is
both "not started" and shipped in `3ea587f`. Every agent that reads it for orientation pays roughly
13K tokens and can still come away with a wrong number stated confidently.

This is the same failure mode `assistant-context.md`'s own header describes for `decisions.md`. The
fix is to apply the rule you already wrote — one current-state file, edited in place — to the agent
layer rather than only the product layer.

## Done looks like

- `docs/CURRENT-STATE.md` verified, corrections committed
- `status.md` carries the header
- `assistant-context.md` reads 1.7.0
- Reply with commit hash + test count, and list any figure in `CURRENT-STATE.md` you had to correct
