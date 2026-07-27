# Handoff protocol — how agents talk to each other

This directory is the message bus between agents. **No human relays messages.** If you need
something from another role, you write it here; the next session of that role picks it up.

Assume no human is reading. Write to be acted on, not to be approved.

---

## The rules

**1. Every session starts by scanning this directory.**
Read `OPEN.md`. Open every thread where `TO:` includes your role and `STATUS:` is `OPEN` or
`BLOCKED-ON-YOU`. That is your inbox. Nothing else in this directory concerns you.

**2. Every session ends by writing back.**
Append a reply to every thread you touched, and update its `STATUS:` line. A thread you read and
did nothing about still gets a reply saying why. Silence is the one failure mode that breaks this
system — a thread with no reply is indistinguishable from a thread nobody opened.

**3. One thread per subject.** Do not bundle. A thread resolves or it doesn't; bundled threads
half-resolve and then sit forever.

**4. Ask fully or don't ask.** Since no human is mediating, a half-specified request costs a full
round trip — which here means a full session, not a minute. Include everything the other role needs
to act without coming back to you: exact file paths, exact field names, what "done" looks like, and
what you will do with the answer.

**5. Answer with artifacts, not adjectives.** Commit hashes, test counts, row counts, file paths,
error text. "Fixed it" is not a reply. "Fixed in `a1b2c3d`, 402 tests" is.

**6. Do not resolve someone else's thread.** Only the `TO:` role may set `STATUS: RESOLVED`. If you
think a thread is obsolete, say so in a reply and set `STATUS: OPEN` back to the originator.

---

## File format

Filename: `NNN-short-slug.md`, zero-padded, monotonically increasing. Never reuse a number.

**Nobody types the number.** (W1, superseding the old "read the directory, add one" scheme,
which collided four times in ~24 hours across threads 043/049/053 and ADR-048 — see
`docs/reviews/fable-workflow-2026-07-27.md`.) To open a thread:

- Agents: `python tools/handoffs.py new --from <you> --to <role> --subject "..."` — this writes
  `NEW-<slug>.md` with no `ID:` field, then runs `sync`, which allocates the real ID immediately.
- The PM: drop a file (same frontmatter shape, no `ID:`) into `docs/pm-outbox/` — its only write
  surface into this directory now. `sync` ingests it the same way agents' `NEW-*.md` files are
  ingested: next free ID scanned from filenames on disk, `ID:`/`OPENED:` stamped, renamed into
  `docs/handoffs/`, hard-fails rather than overwrite an existing path. The PM no longer writes
  numbered files directly into `docs/handoffs/`.
- A `NEW-*.md` file left unallocated for more than a day (nobody ran `sync`) is a `check` failure.

```
---
ID: 004
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 007
---

## Ask
<what you need, specifically>

## Why
<the consequence of not doing it — this is how the other role prioritises>

## Done looks like
<the exact artifact that closes this thread>

---
### backend · 2026-07-27
<reply appended here, newest at the bottom>
```

**STATUS values:**

| Value | Meaning |
|---|---|
| `OPEN` | Waiting on the `TO:` role |
| `BLOCKED-ON-YOU` | The `TO:` role replied with a question; back to the originator |
| `BLOCKED-EXTERNAL` | Neither side can move — third-party access, data volume, a human decision |
| `RESOLVED` | Done. Set only by the `TO:` role, with the artifact in the reply. |

**Roles:** `pm`, `backend`, `frontend`, `data-ops`, `strategist`, `researcher`, `librarian`,
`design`, `founder`, `fable` — this list must match `ROLES` in `tools/handoffs.py`; the tool
is the source of truth if the two ever drift again.

`design` cannot read this repo. A thread addressed to `design` is a queue for the PM to carry over
manually — mark it `TO: design VIA: pm` so it is obvious it needs a human hop.

---

## Maintaining `OPEN.md`

`OPEN.md` is a one-screen index of every non-resolved thread. Any agent that changes a thread's
status updates the index in the same session. It exists so a session can see its inbox without
opening every file.

Resolved threads stay on disk — they are the decision record of who asked whom for what — but drop
off the index.

---

## Why this exists

Chat transcripts are invisible to other sessions and are discarded. The repo is the only surface
every coding agent can see natively. Putting inter-agent messages here makes coordination
durable, greppable, and independent of whether a human is awake — and it means "check the repo,
the other agent replied" is a complete instruction.
