# Founder request protocol — how the backlog gets recorded now

This directory replaces new writes to `docs/founder-requests.md` (frozen 2026-07-28, existing
FR-001..FR-017 kept there as archive). That file was a single append-only log every session wrote
new entries to *and* later sessions edited in place to flip an existing entry's `Status:` —
concurrent edits to one blob, the same conflict shape as `docs/CURRENT-STATE.md`, not the pure
append shape `docs/status.md` had. So this follows `docs/handoffs/` instead: one file per request,
numbered, individually addressable — because FR numbers are referenced by number elsewhere in the
repo (ADRs, handoff threads, reviews), unlike a session-log entry nothing else points at.

---

## The rules

**1. Capture every founder request, still.** Nothing about *when* to record a request changed —
just *where*. If the founder expresses a want, a constraint, a preference, or a "wouldn't it be
good if" in any session, it gets an entry before that session ends.

**2. Nobody types the ID.** Same reasoning as `docs/handoffs/README.md` — hand-computed and even
counter-based numbering collided repeatedly in this project (threads 043/049/053, ADR-048, and
more found 2026-07-30 — see `docs/known-id-collisions.md`, ADR-064). To open a request:

```
python tools/founder_requests.py new --raised-by "cowork chat" --subject "Research/comparison section for prep mode"
```

This writes `NEW-<slug>.md` with no `ID:` field, then runs `sync`, which allocates the real
`FR-YYYY-MM-DD-slug` filename immediately — no shared counter, so no cross-worktree race is
possible (ADR-064). Requests opened before 2026-07-30 keep their `FR-NNN` numbers unchanged.

**3. Status changes are edits to the request's own file, not a shared log.** Change the `STATUS:`
line in `FR-NNN-slug.md` directly — `NEW` → `SCOPING` → `SPECCED` → `IN PROGRESS` →
`SHIPPED`/`DECLINED`/`DEFERRED`, matching the vocabulary the archive used. Append reasoning under
a `## Resolution` or `## Update (date)` heading in the same file rather than deleting what was
there before — a request the founder made and the team decided against is worth keeping, same
rule the archive followed.

**4. Regenerate the index after any change.**

```
python tools/founder_requests.py sync
```

Rebuilds `docs/founder-requests/INDEX.md`, grouped by status, from every `FR-*.md` file in this
directory. Never hand-edit `INDEX.md` — fix the request's own file and re-sync.

---

## Filename format

**`FR-YYYY-MM-DD-slug.md` (ADR-064, 2026-07-30 onward)**, allocated by `sync` — never hand-typed.
No shared counter: allocation is a pure function of (today's date, this request's own slug),
claimed atomically, so two worktrees can't race the same "next number." Same-day-same-slug within
one working tree gets a deterministic `-2`/`-3` suffix.

Requests opened before 2026-07-30 keep their old `FR-NNN-slug.md` filenames forever — **never
renamed** (`FR-018` through the last one allocated under the old scheme; archive `FR-001..FR-017`
tops out at `FR-017`, with a pre-existing duplicate `FR-015` heading, left as-is since this
directory doesn't rewrite the archive). Both filename shapes load and resolve identically.
