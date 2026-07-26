---
ID: 011
FROM: pm
TO: founder, frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 007
---

## Ask

Find and commit two artifacts that the project treats as authoritative but that do not exist in this
repository:

1. **`FRONTEND-SPEC.md`** — the ~38,000-character implementation spec. Commit to `docs/FRONTEND-SPEC.md`.
2. **`Draft_Assistant_reference.dc.html`** — the reference prototype from Claude Design. Commit to
   `docs/design-reference/`, split per screen if it is a single file containing several.

Likely locations, in order: the frontend working copy (uncommitted or on a branch), a Claude Design
project export, or a chat attachment in a prior session. If it exists only in a chat, download it now
— chat attachments are not durable storage.

## Why

This was raised by `librarian` reading the repo, and it is a real hole rather than a bookkeeping one.

The project's own operating model names `FRONTEND-SPEC.md` as the source of truth for the port, and
`docs/design-fidelity.md` specifies that the fidelity harness diffs the running app against a
**pinned** reference committed to the repo. Neither is possible right now: thread 007 cannot be built
without the prototype, and Frontend has been porting against a document that no session other than
its own can read.

This is also the concrete form of the design gap. Design produces the spec, it lands somewhere
outside version control, and every other agent is blind to it. Committing it does not fix the
handoff, but it does mean the spec stops being a single point of failure living in one session's
context.

One thing to check while retrieving it: whether the spec still matches what Design currently shows.
If the spec predates recent design changes, commit it anyway with a dated note — a pinned stale
reference is still far better than no reference, because at least drift becomes measurable.

## Done looks like

Both files committed. Reply with paths and the spec's character count so we can confirm it is the
full document and not a truncated copy. Then 007 unblocks.
