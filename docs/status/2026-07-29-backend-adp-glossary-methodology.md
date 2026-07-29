# 2026-07-29 — backend — ADP glossary/methodology gap

**Dispatch:** PM finding. Contract 1.14.0 (thread 082) shipped real ADP fields to the board,
draft screen, and player profile, but the term was defined nowhere: `glossary.json` carried 13
terms and none was ADP; `Methodology.tsx` had five sections and none mentioned it.

## What shipped

1. **`ADP` glossary term** (`src/export_static.py::_GLOSSARY_BASE`). States the caveats up
   front: MFL proxy population (not this league's), captured full-PPR against this half-PPR
   league, thin sample, ~230-player coverage ceiling, and that it is display-only. Folded
   `adp_min_pick`/`adp_max_pick`/`adp_selected_pct` into this one entry rather than four separate
   terms — same pattern the existing `confidence interval` term uses for `ci_low`/`ci_high`.
2. **Methodology section** (`frontend/ui/views/Methodology.tsx`). Renders `board.json`'s real
   `adp_source_note`/`adp_match_rate_note` verbatim, states explicitly which fields ADP does
   *not* feed (`projected_points`, `vbd`, tiers, availability, recommendations).
3. **`frontend/ui/data/glossaryCategories.ts`** maps `ADP` to the `draft` (Draft mechanics)
   category — previously declared but empty — with `field: 'board.json:players[].adp'`.
4. **Regenerated all 27 `glossary.json` files** (primary + 26 saved league configs under
   `data/leagues/`) via `export_static.write_static_artifacts`, which needs no `.db` connection.
5. **Corrected two now-stale claims** found next to the new text: the `consensus rank` glossary
   entry and `board.json`'s `consensus_source_note` (`export_contract.py`) both said "no ADP
   source is legally obtainable (ADR-018)" — false since ADR-035's real MFL proxy. Fixed both to
   point at the real (thin) ADP instead of denying it exists.
6. **Fixed two files with literal leftover git-conflict markers** (`docs/decisions.md` around
   ADR-057/058; `docs/handoffs/082-...md` around its two frontend replies) — mechanical, marker
   lines only, no content change, both sides already sequential/non-overlapping. Did **not**
   touch the actual ADR-054/055 duplicate-header collision, which is ADR-056's already-made,
   deliberately-left decision.

Full reasoning, including why each judgement call was made without escalating, is in
`docs/decisions.md` ADR-060 and `docs/ideas-inbox.md`'s 2026-07-29 backend entry.

## Explicit answer to the dispatch's central question

**ADP is display-only.** It does not feed `projected_points`, VBD, tier, availability, or any
recommendation. Evidence: `_load_adp_snapshot()`'s own docstring in `export_contract.py` ("for
DISPLAY only -- does NOT feed the model"); ADR-035's status note that
`availability.load_mfl_adp_source()` "exists, is tested, and is NOT wired into the shipped
default"; thread 082's frontend reply confirming `AdpCell`/`AdpBlock`/`DraftRoomAdpCell` read
`row.adp`/`row.adpSource` exclusively, never merged into `consensus_rank` or its delta. This
session did not rewire any of that — the new Methodology section states the existing fact, it
does not create it.

## Contract

**No version bump.** Every field used (`adp`, `adp_source_note`, `adp_match_rate_note`, etc.)
already existed at contract 1.14.0 from thread 082. `CONTRACT_VERSION` in
`src/export_contract.py` untouched.

## Known limitation, not fixed this session

`data/export/board.json`'s `consensus_source_note` field (the shipped artifact, not the Python
source) still contains the old ADR-018 text. Regenerating it needs a live `nfl.db`; this
session's `scripts/rebuild_database.py` run got through steps 1-3 and failed at step 4
(`ingest_rankings.py`, `github.com/dynastyprocess/*` returns 403 in this kind of session) — a
documented, pre-existing, session-local restriction (`docs/can-we-rebuild-the-database.md`),
reported rather than re-solved per that doc's own instruction. The source fix will take effect
automatically the next time `board.json` is rebuilt with a working database.

## Evidence

- Backend: `python3 -m pytest tests/ -q` (no `nfl.db` in this container) — **688 passed, 29
  failed, 9 errors, 3 skipped**. Every failure/error is the missing-DB condition or the
  pre-existing `test_mailbox_health` ADR-054/055 collision (ADR-056, unrelated to this work,
  same before and after). Glossary-adjacent suites that don't need a live board build
  (`test_multi_league_export.py`'s pure-function tests, `test_export_contract.py`,
  `test_export_directory_contract.py`, `test_league_builder.py`) run clean.
- Frontend: `npm test` — **203 passed, 0 failed, 22 files**. `tsc -b --noEmit` clean.
- Screenshots (Playwright, `frontend/e2e/verify-adp-glossary-methodology.mjs` plus a follow-up
  scroll/expand pass), looked at directly: `adp-glossary-2026-07-29.png`,
  `adp-glossary-expanded-2026-07-29.png`, `adp-methodology-2026-07-29.png`,
  `adp-methodology-scrolled-2026-07-29.png` in `frontend/e2e/artifacts/`. Confirmed: ADP renders
  under "Draft mechanics" in the Glossary and expands to the real MFL text; the new Methodology
  section renders the real `adp_source_note` (147 of 225 `mfl_proxy` rows resolved, snapshot
  2026-07-29) beneath the "does not feed" language.
- All 27 `data/export/*/glossary.json` files (primary root + 26 sub-league dirs) confirmed via
  script to contain the `ADP` term.

## Files touched

- `src/export_static.py` — ADP term, `consensus rank` fix
- `src/export_contract.py` — `consensus_source_note` fix (comment + string), no version bump
- `frontend/ui/views/Methodology.tsx` — new ADP section
- `frontend/ui/data/glossaryCategories.ts` — `ADP` -> `draft` category mapping
- `data/export/**/glossary.json`, `nulls.json`, `opponents.json` — regenerated (content diff
  limited to the new ADP term plus timestamps)
- `docs/decisions.md` — ADR-060, plus conflict-marker cleanup around ADR-057/058
- `docs/handoffs/082-adp-fields-on-board-json-contract-1-14-0.md` — conflict-marker cleanup
- `docs/ideas-inbox.md` — session entry
- `docs/CURRENT-STATE.md` — in-place update
- `frontend/e2e/verify-adp-glossary-methodology.mjs` (new) — screenshot verification script
