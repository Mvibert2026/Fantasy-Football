---
ID: 087
FROM: librarian
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask
FR-043 audit: CLAUDE.md SS5 staleness + built-but-unwired pattern (Mock Lab / narrate / ADR-C)

Full audit: `docs/audit-2026-07-29-built-and-unused.md`. Two things need a PM/founder call, not a
librarian one:

1. **`CLAUDE.md` §5's coaching-data and route-data rows are stale.** They say coaching data is
   "Not in nflverse" and route data "not directly in nflverse — needs NGS or a documented proxy
   calculation," with no acknowledgment of `docs/research/nflverse-unused-data-audit-2026-07-29.md`
   (same repo, same day): `load_schedules()`'s `home_coach`/`away_coach` columns partially close
   the coaching gap (head-coach identity only, not coordinator/play-caller — that distinction
   matters, `src/ingest_play_callers.py` still correctly stays parked), and `load_participation()`'s
   `route` column (2016-2025) is a real, documented route-participation proxy that closes part of
   the route gap. Neither is ingested yet — the audit measured them without writing to
   `data/nfl.db`. A `CLAUDE.md` edit is a spec change (`CLAUDE.md`'s own operating rules: "a
   decision that would change CLAUDE.md goes to PM/founder"), so I flagged it in the audit file
   rather than editing it myself.
2. **Three built-but-structurally-disconnected backend capabilities now exist**: the Mock Lab
   live-logging store (`src/mock_lab_store.py`, known, tracked), `src/narrate.py`'s deterministic
   Facts layer (zero callers anywhere — not imported, no CLI entrypoint, no artifact written; the
   deliberately-deferred LLM prose layer above it is the reason, per its own docstring), and the
   ADR-C pre-registration convention (`src/preregistration.py`/`src/holdout.py`, "not yet enforced
   at any entrypoint" per thread 020). None of these has cost anything yet, unlike
   `src/league_builder.py` (the FR-043 trigger, which nearly caused duplicate build work). Naming
   the recurrence in case it's worth a standing check later — not requesting one be built now, per
   thread 062's own bar ("name a failure that has actually occurred").

## Why
If §5 stays as written, the next session scoping a coaching or route-data feature will read
"not in nflverse" as settled fact and re-derive (or worse, re-propose buying) something that is
already free and partially measured. That is the exact FR-043 failure mode, just aimed at CLAUDE.md
instead of `src/`.

## Done looks like
A PM/founder decision on whether to amend `CLAUDE.md` §5 (and if so, the amended text), recorded as
an ADR per the project's own rule that a CLAUDE.md change needs one. No action required on item 2 —
informational, close whenever read.
