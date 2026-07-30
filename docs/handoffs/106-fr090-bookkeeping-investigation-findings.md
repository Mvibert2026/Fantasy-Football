---
ID: 106
FROM: librarian
TO: pm
STATUS: OPEN
SUBJECT: FR-090 bookkeeping investigation delivered — two action items and one escalation
OPENED: 2026-07-30
---

## What this is

FR-090 ("bookkeeping overhead must be officially raised, measured, and investigated") is answered in
full at `docs/bookkeeping-investigation-2026-07-30.md`. Summary for triage, not a substitute for
reading it — every claim there carries a `file:line`.

## Headline

Seven of nine tracking surfaces are load-bearing by direct evidence (named reader, named decision,
or a documented incident showing what breaks without them). Two are not:

1. **`docs/roles-workflow-map.html`** — no instruction in `CLAUDE.md`, `.claude/agents/*.md`, or
   `docs/pm/*.md` points at it. One commit total, never touched since creation. **Recommend DELETE.**
2. **`docs/dashboard.html`** — generator-backed (`tools/dashboard.py`), so cheap to maintain, but
   stale by construction between runs (verified this session: it claims "50 open, 41 resolved,"
   `OPEN.md` currently says "55 open, 44 resolved" — one day stale) and no agent instruction treats
   it as a decision input, only a founder browse view. `docs/pm/ROLE.md:97` already states `OPEN.md`
   is "the standing recommendation" over it. **Recommend wiring its regeneration into the existing
   `pm/CLOSEOUT.md:85` step; if that discipline doesn't hold, delete it.**

Total evidenced upkeep: 375 commits across the nine live surfaces, 81% of which sit in the four
surfaces with the strongest reader/decision evidence (`handoffs/`, `founder-requests/`, `status/`,
`CURRENT-STATE.md`) — high churn there is not itself evidence of ceremony.

## The real cost is not surface count — it's the allocator

`tools/handoffs.py check` is red right now (re-verified live this session): thread `093` claimed by
3 files, `094` by 2, ADR-054/055 each with 2 conflicting headers. `docs/founder-requests/INDEX.md`
carries the same failure one layer up — **FR-072 is two unrelated tickets sharing one ID** (thread
hygiene vs. bottom-up model scope), because two branches diverged before either could see the other's
allocation.

This is a *different* failure mode from the 093/094 race (simultaneous allocation) — it only needs
branch divergence before a commit, not simultaneity, and a wider merge-base search doesn't fix it
because the other branch's ref genuinely isn't reachable yet. **The investigation's read: the mutable
central registry is the defect, not agent discipline or search radius.** Two structural alternatives
are named (content-addressed IDs; branch-scoped namespacing collapsed at merge) but the choice is
explicitly not mine to make — this is the same root-cause class as thread 076 (still `OPEN`, still
addressed to `pm`), and this document should be read alongside it rather than instead of it.

One data point worth carrying into that decision: `docs/ideas-inbox.md` has zero collisions across
43 commits because it was built with **no identifiers at all** ("safety by construction"). That's a
working precedent for whatever fix gets picked for the numbered surfaces.

## What I did not do

Did not touch `frontend/`. Did not attempt to deduplicate FR-029/030/072 or renumber 093/094/ADR-
054/055 by hand — per this project's own standing rule, that is the allocator's job or a deliberate
single renumbering, never a hand guess. Did not pick between the two structural ID-allocation fixes.

Full detail, table, and evidence: `docs/bookkeeping-investigation-2026-07-30.md`.
