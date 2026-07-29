---
ID: FR-043
STATUS: IN PROGRESS
PRIORITY: MEDIUM
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Update — 2026-07-29, librarian

Audit delivered: `docs/audit-2026-07-29-built-and-unused.md`. Covers all five requested areas
(orphan modules, backend-with-no-UI, unused ingested data, phantom-cited documents, unread export
fields), plus the item-1-crossed-with-backlog check the coordinator prioritised. Two live documents
corrected in place this session (`docs/operating-model.md`, `docs/design-handoff/HANDOFF-NOTES.md`
— both cited the missing "Competitive UX + platform + Reddit research" artifact thread 086 also
found). One contradiction escalated rather than resolved unilaterally: `docs/handoffs/
087-fr-043-audit-claude-md-ss5-staleness-built-but-u.md`, to `pm`, on `CLAUDE.md` §5's stale
coaching/route-data claims. Remains `IN PROGRESS` (not `SHIPPED`) until thread 087 closes.

## Request
Audit for capability already built and sitting unused

Founder's own words:

> "Probably should see if anything else is built sitting around we can use."

Raised immediately after being told the custom-league backend already existed and nobody had
mentioned it.

## Why it matters

The trigger was `src/league_builder.py` — a complete API for creating and exporting an arbitrary
league, present in the repo, with no consumer and no mention in any planning document. It was found
by accident while scoping FR-040. Had it not been found, the project would likely have specced and
built a second one.

There is prior evidence this is a pattern rather than a one-off:

- **Mock Lab** has a backend store and no interface at all (`docs/design-briefing-2026-07-29.md` §2).
- **The Draft screen was assumed absent from the standalone build** until someone checked and found
  it worked.
- **Two of three "missing" datasets turned out to already be free in nflverse** — `load_schedules()`
  carries coaches 1999-2026 and `load_participation()` carries route data 2016-2025 — after coaching
  history and route participation had both been recorded as unbuilt data gaps in `CLAUDE.md` §5.
- **The competitive UX research** commissioned 2026-07-29 found a prior completed pass logged in
  `docs/operating-model.md` whose artifact is not in the repository. Six live documents cite its
  conclusions. That is the inverse failure — a document believed to exist that does not — and it
  belongs in the same audit.
- **Of 23 nflverse loaders, 10 are used.**

So the project has lost track in both directions: capability that exists and is not known about, and
capability believed to exist that does not.

## Initial read

Not the founder's own words — PM's read.

**Scope it as an inventory, not a cleanup.** The deliverable is a list with a disposition per item —
*use it, finish it, delete it, or leave it* — not a refactor. An audit that turns into a tidy-up
consumes the budget and produces no decision.

Cover at minimum:

1. **Python modules in `src/` with no caller.** `league_builder.py` is one. Find the rest.
2. **Backend capability with no UI.** Mock Lab is the known case; there are probably others.
3. **Data already ingested and unused** — the 13 unused nflverse loaders, plus anything sitting in
   `data/nfl.db` that nothing reads.
4. **Documents cited but absent.** The inverse case. Cheap to check and it corrects live docs.
5. **Exports generated and never read.** `board.json` fields nothing renders; artifacts written for
   leagues where no screen consumes them.

**The output that matters is item 1 crossed with what is currently queued** — anything on the
backlog that a built module already does. That is the finding that saves real time, and it is the
reason the founder raised it.

Suitable for `librarian`: repo-wide, evidence-based, no building. Not urgent, but it should run
before the next round of build planning rather than after.
