---
ID: 070
FROM: pm
TO: data-ops, researcher
STATUS: OPEN
BLOCKS: T4 (suspensions/roster-status table stakes), E[games_played] per ADR-E Amendment E-A1
OPENED: 2026-07-27
---

## Ask

Founder directive, 2026-07-27: build a **recurring**, full-NFL injury and suspension feed — not a
one-off pull. Two halves, different mechanisms, do not conflate them.

**1. Injuries — automate it.** nflverse injury data (2009+, includes practice participation:
DNP/limited/full, game status) is already ingested historically (`src/ingest_reference.py`, the
`injuries` table — per `docs/CURRENT-STATE.md`, 2010-2024 with enforced `as_of_date`, 2009 mostly
undated at the source and dropped, 2025 has no `date_modified` column upstream yet). Turn this
into a **recurring pull** for the live 2026 season: same schema, same `as_of_date` discipline,
run on a schedule through the season.

**2. Suspensions — no reliable structured source exists.** Check thread 057 §4's answer first if
it has landed (`docs/handoffs/057-timeseries-data-audit.md` was still `OPEN` as of this thread —
do not re-research the same question twice). Founder's directive either way: do **not** build a
probability model for suspensions. Maintain a **hand-curated watchlist** (length, effective date,
appeal status, source, `current_as_of`) plus a **weekly researcher web sweep** to keep it current.
Known suspensions are a deterministic games-played deduction, enforced by a blocking test — not a
modelled estimate. Consistent with FR-007 (`docs/founder-requests.md`): table stakes are
unconditional, not traded against edge. Note appeal reductions specifically — an announced
suspension is frequently reduced on appeal, and a table capturing only the announcement
overstates the deduction.

## Cadence — state this explicitly, the founder asked for it by name

- **Injuries**: weekly during the season (in-season practice reports move status week to week).
  Whether to also add a daily pull in the 48 hours before each league's draft is data-ops's call
  — state whichever cadence actually gets implemented, don't leave it implicit.
- **Suspensions**: weekly researcher sweep, same cycle as the injury pull, so both land in the
  same `as_of_date` window. Pre-draft, off-season: the T4-interim curation
  (`docs/reviews/ACTION-PLAN-2026-08.md` Day 3 item 3.3, already specced) becomes the first
  watchlist row set; weekly sweeps from there.
- Both feed **E[games_played]** per `docs/adr-drafts/ADR-E-bottom-up-projection-framework.md`
  Amendment E-A1 (week-indexed, not a season scalar) — confirm the wiring shape with backend
  before building the ingest schema, so it lands in E-A1's shape the first time.

## Why

FR-007: table-stakes correctness is unconditional. This is T4/T6 from the pre-mortem
(`docs/reviews/fable-draft-day-premortem-2026-07-27.md`, failure #3 — High likelihood, Severe
damage: "a suspended/retired/IR player sits in the top 60 as a full-season starter"). A one-off
pull is exactly the "looks authoritative, silently stale" failure mode the founder has repeatedly
flagged as worse than an honest, visible gap.

## Done looks like

- A runnable, documented recurring injury-pull job writing to the existing `injuries` table with
  `as_of_date` discipline preserved for 2026, cadence stated in its own docstring or a runbook.
- A suspension watchlist table/fixture with `current_as_of`, populated from a first researcher
  sweep, with the sweep cadence documented (who/what re-runs it and how often).
- Both wired to feed E[games_played] per E-A1, or an explicit statement of what's blocking that
  wiring if it can't land this round.
- Thread 057 §4 checked first — do not re-litigate whether a structured suspension source exists
  if it already answered that.

---
### backend · 2026-07-27

Not resolving (not the `TO:` role) — flagging relevant work for whoever picks this up. This
session built the "first watchlist row set" this thread's cadence section anticipates:
`data/suspensions_2026.json` (`as_of_date: 2026-07-27`, `sources_checked` list, wired into the
live board via `export_contract.build_board_json`, ADR-053, thread 057 reply has full detail). It
is currently empty of entries — the research pass found nothing confirmable and fantasy-relevant
— so the "first row set" is an empty set, honestly, not a placeholder. Whoever builds the
recurring weekly sweep can treat this file as the target to append to; the wiring (`src/
suspensions.py` -> `build_board_json`) needs no further code changes to pick up new rows.
E[games_played]/E-A1 wiring was not touched this session — out of this round's narrower scope.
