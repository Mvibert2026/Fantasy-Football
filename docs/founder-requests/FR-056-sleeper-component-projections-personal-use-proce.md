---
ID: FR-056
STATUS: DONE
SOURCE: PM dispatch (data-ops session)
RAISED: 2026-07-29
---

## Request

Paraphrased from this session's dispatch text (not verbatim founder words — the founder's ruling
was relayed by the dispatching agent, not quoted directly to this session): "Ingest per-player
component projections for 2026. The founder has decided the licensing question: personal use,
proceed." This answers thread 091/092's item 1 escalation (`docs/research/component-projections-
and-fr-053-features-2026-07-29.md`) for the free Sleeper/Rotowire route specifically — component
projections may be captured and stored for this project's own local/personal use.

## Why it matters

FR-040 concluded custom scoring "cannot be computed in the browser" because `board.json` carries
no component stats. Sleeper's public endpoint (`api.sleeper.com/projections/nfl/2026`) publishes
per-player pass/rush/rec yards, TDs, attempts and fumbles, `company: rotowire`, free, robots.txt
fully open. The blocker was never data availability — it is that this project's site is public
and Sleeper's ToS §9.2 forbids redistribution. This ruling unblocks local ingestion without
resolving that public-site question (thread 092 item 2's escalation stays open).

## Initial read

Scoped narrowly: this ruling is about Sleeper/Rotowire component projections specifically,
**personal/local use only** — it does not touch board.json, does not touch the FantasyPros/FFC
public-hosting exposures thread 092 item 2 raised, and does not extend to any other projection
vendor. Built and committed this session: `src/ingest_sleeper_projections.py`, table
`sleeper_projections` (as_of_date-stamped per CLAUDE.md §4), CSV archive under
`data/projection-snapshots/`. Commit `fdd4685`. Reply appended to thread 092
(`docs/handoffs/092-...md`) rather than opening a new thread, since 092 already carries this exact
question as its item 1.
