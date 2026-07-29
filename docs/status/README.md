# Session log protocol — how session narratives get recorded

This directory replaces `docs/status.md` (frozen 2026-07-29). The old file was one append-only
log every session wrote to; under parallel worktrees that made it the most common source of merge
conflicts in the project (see `docs/reviews/fable-workflow-2026-07-27.md`, work order W3). This
directory removes the contention by giving each session its own file.

---

## The rules

**1. One file per session.** At the end of a session that did anything worth recording, write
`docs/status/YYYY-MM-DD-role-slug.md` — your own new file, never an edit to someone else's.
Two sessions on the same day and role just get two files; there is no collision to avoid.

**2. Write freely.** Same content that used to go in a `status.md` entry: what happened, what
changed, what's still open. No required frontmatter — this is narrative, not a machine-parsed
thread. A one-line `# YYYY-MM-DD — role — short description` heading at the top makes the
generated index more useful, but isn't enforced.

**3. Never edit a previous session's file.** If something you wrote turns out to be wrong, say so
in your own session's file — don't rewrite history. This is a log, not a wiki.

**4. Regenerate the index after writing.** Run:

```
python tools/status_log.py sync
```

This rebuilds `docs/status/INDEX.md` — the full combined narrative, oldest first, generated fresh
from every file in this directory. `INDEX.md` is never hand-edited; if it looks wrong, the fix is
in the session file it was generated from, followed by another `sync`.

**5. Read `docs/CURRENT-STATE.md` for current state, not this directory.** This log (like the
frozen `status.md` before it) is forensic narrative — what happened, in order. It is not the
canonical answer to "where is the project right now." Same hazard `CURRENT-STATE.md` already
documents for the old file.

---

## Scaffolding a new session file

```
python tools/status_log.py new --role backend --slug short-slug
```

Writes `docs/status/YYYY-MM-DD-backend-short-slug.md` (today's date) with a heading stub, and
prints the path. Optional convenience — a plain `Write` to a correctly-named file works too.

---

## Filename format

`YYYY-MM-DD-role-slug.md` — date first so directory listings sort chronologically without help.
`role` is any of the roles in `docs/handoffs/README.md` (or `pm`/`founder` for non-agent
sessions). `slug` is a short kebab-case description, same style as handoff thread slugs.
