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

**7. Pull before starting work, push at close.** The repo now has a remote (`origin`); this
directory only works as a message bus if every session sees the latest threads before acting and
leaves its own writes visible to the next one.

**8. A pull conflict is not yours to resolve alone.** Stop and escalate — the same rule as a
contradiction between docs. Do not merge, rebase over, or discard either side's changes on your
own authority.

---

## File format

**Filename: `YYYY-MM-DD-short-slug.md` (W3, ADR-064, 2026-07-30).** Older threads keep their
original `NNN-short-slug.md` filenames and `ID:` fields forever — **never renamed, never
renumbered**, because they're cited by number throughout the repo (prose, commits, `CLAUDE.md`,
other threads). Both shapes load, sort, and resolve identically; `tools/handoffs.py`'s `inbox`/
`sync`/`check` handle either transparently, so `docs/handoffs/119-*.md` still works exactly as
before.

**Why the scheme changed.** The old `NNN` counter (`max(existing) + 1`, later widened to scan every
git ref — still just narrowing the race, not closing it) let two worktrees each compute a
locally-valid "next free" number in the same window. Because the two colliding files had
*different filenames*, git merged them cleanly with no conflict — the collision was silent, only
found by someone reading the `ID:` field later. It collided six times on 2026-07-30 alone
(threads 043/049/053, ADR-048, and several more found retroactively — see
`docs/known-id-collisions.md`). Full reasoning: ADR-064, `docs/decisions.md`.

**Nobody types the date or the slug's disambiguation.** To open a thread:

- Agents: `python tools/handoffs.py new --from <you> --to <role> --subject "..."` — this writes
  `NEW-<slug>.md` with no `ID:` field, then runs `sync`, which allocates
  `docs/handoffs/{today}-{slug}.md` (or `-2`/`-3`/... if this same working tree already has a
  thread with that exact date+slug) via an atomic filesystem claim — no counter, no git scan.
- The PM: drop a file (same frontmatter shape, no `ID:`) into `docs/pm-outbox/` — its only write
  surface into this directory now. `sync` ingests it the same way, into `docs/handoffs/`.
- Two *separate* worktrees independently choosing the identical subject on the identical day is
  the one case a single tree can't locally disambiguate — it surfaces as an ordinary git same-path
  merge conflict at merge time (loud, blocks the merge) rather than the old scheme's silent
  duplicate `ID:`.
- A `NEW-*.md` file left unallocated for more than a day (nobody ran `sync`) is a `check` failure.

**ADR numbers are unaffected by this change** — `tools/handoffs.py adr next` keeps its existing
counter-plus-ref-scan design; ADR-064 did not touch it (a much smaller, less concurrent space).

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

**`design` CAN read this repo but CANNOT write to it** (corrected 2026-07-29 — this line said design
could not read at all, which stopped being true on 2026-07-27 and cost real relaying before anyone
noticed). So a thread addressed to `design` needs no hop to be *read*: design opens it directly.
What still needs a hop is the return leg — every design output arrives as a file for the PM or
`frontend` to commit, because design cannot land anything itself. Keep `VIA: pm` only where the
thread expects something committed back.
`design` has read access to this repo and no write access (`docs/design-protocol.md` §1 — corrected
here 2026-07-29; this file previously said design could not read the repo at all, which had been
false for two days and cost the founder repeated hand-relaying of files). Mark a thread to design
`TO: design VIA: pm` only for the **landing** hop — design produces files but cannot commit them.
Do not paste file contents into a thread for design to read; name the path and the ref.

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
