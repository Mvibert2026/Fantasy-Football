# PM outbox

This directory is the PM's **only** write surface for new mailbox threads. Per
`docs/reviews/fable-workflow-2026-07-27.md` work order W1: the PM no longer writes numbered
files directly into `docs/handoffs/` — that direct-write path is what let a bridge write
silently destroy an agent's thread on an ID collision (thread 053; see
`docs/handoffs/RECONCILIATION-2026-07.md`).

Drop a thread file here with the normal frontmatter (`FROM`, `TO`, `STATUS`, `BLOCKS`) but
**no `ID:` field** — you cannot collide on a number you never typed. Name the file anything
descriptive; the name becomes the slug.

`python tools/handoffs.py sync` ingests every file here on each run: allocates the next free
ID by scanning `docs/handoffs/` filenames, stamps `ID:` and `OPENED:`, renames it to
`docs/handoffs/NNN-<slug>.md`, and removes it from this directory. It hard-fails rather than
overwrite an existing path.

This directory should be empty between sync runs, except immediately after the PM drops
something new.
