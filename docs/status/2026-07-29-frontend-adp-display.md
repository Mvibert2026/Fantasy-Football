# 2026-07-29 — frontend — ADP display on board, draft room, player detail

**Role:** frontend · **Type:** UI wiring against an already-landed export contract bump
**Thread:** 082 (backend -> frontend, FR-024) · **Contract:** 1.13.0 -> 1.14.0

## Task

Founder asked (2026-07-29, recorded as FR-024): "ADP should be shown on both the prep and draft
screens as well as player profile." Backend's half landed same day (thread 082, commit `3690217`/
`c6b45be`, contract bump to 1.14.0): `board.json` player rows gained `adp`/`adp_min_pick`/
`adp_max_pick`/`adp_selected_pct`/`adp_source`; the board top level gained `adp_source`/
`adp_as_of_date`/`adp_match_rate_note`/`adp_source_note`. Nothing rendered any of it. This session
closes the frontend half.

## Premise check

Read `CLAUDE.md`, `docs/CURRENT-STATE.md`, `docs/operating-model.md`, `docs/design-fidelity.md`,
thread 082, `docs/founder-requests/FR-024-*.md`, and `docs/backlog-triage-2026-07-29.md` before
acting. All consistent, no contradiction found. `data/export/board.json` and
`frontend/public/data/board.json` were both already at `contract_version: 1.14.0`, byte-identical,
already synced — confirmed measured, 144/510 rows carry a real `adp` value, 366 null, matching
backend's reported count.

## What was built

- `frontend/ui/data/types.ts` — `RawBoardPlayer` gains 5 optional ADP fields; `RawBoard` gains 4
  optional top-level ADP fields. Optional so a pre-1.14.0 export still parses.
- `frontend/ui/data/board.ts` — `BoardRow` gains `adp`/`adpMinPick`/`adpMaxPick`/`adpSelectedPct`
  as `Cell<number>` (through `fromNullable`, honest-null convention, authored reason citing MFL's
  ~top-230 coverage limit) and `adpSource` as a plain string travelling alongside them.
- `frontend/ui/data/contract.ts` — `EXPECTED_CONTRACT` 1.13.0 -> 1.14.0.
- `frontend/ui/data/trace-fields.ts` — `TRACE_CONTRACT` 1.13.0 -> 1.14.0, new 1.14.0 changelog
  entry (records the delta-column decision below), all 5 player-row ADP fields registered in
  `BOARD_TRACE_FIELDS` (required — the registry is compared 1:1 against exported player-row keys
  by `trace-fields.test.ts`), all 4 top-level fields registered in `BOARD_HEADER_TRACE_FIELDS`.
- `frontend/ui/views/Board.tsx` — new `ADP (MFL)` column between CONS and Δ, sortable
  (`SortKey` gains `'adp'`). Header label is the glance-level "not your league's ADP" signal (per
  the founder's explicit requirement); `AdpCell` shows the value with a tooltip carrying source,
  pick range, and selected%; absent renders through the same em-dash convention as every other
  column on this table. Column header itself carries a title with the full `adp_source_note` +
  `adp_as_of_date`, reachable without depending on any row having data.
- `frontend/ui/views/DraftRoom.tsx` — compact `DraftRoomAdpCell` (value + "MFL" superscript, or
  em-dash) inserted between team and the existing delta-vs-consensus cell in the board list.
- `frontend/ui/components/PlayerDetail.tsx` — new `AdpBlock` section below "WHY OUR RANK DIFFERS
  FROM THE MARKET": value, pick range, selected%, and `board.adp_source_note` rendered verbatim
  (the one place on any of the three screens the full caveat is always visible, not gated behind
  hover) plus `adp_as_of_date`. Null case shows the row's own absent-cell reason, distinct wording
  from the projection/availability null states elsewhere in the same sheet.
- `frontend/e2e/cloud-adp-screenshot.mjs` — new screenshot script following the cloud recipe in
  `docs/frontend-cloud-runbook.md` (explicit `executablePath` against the pre-installed Chromium
  1194 binary; never `playwright install`).

## Judgement call: no second delta column

Thread 082 and FR-024 both explicitly left this to frontend ("the board already shows a delta
against consensus, and two adjacent delta columns measuring different things would confuse more
than they reveal... left to frontend, which can see the layout").

**Decision: do not add a delta column comparing our rank to ADP.** Reasons:

1. The board already renders one delta (`delta_vs_consensus`, our rank vs. FantasyPros expert
   consensus). A second delta beside it (our rank vs. MFL-proxy ADP) is a different comparison but
   would sit in the same visual slot doing the same visual job — a reader skimming Δ columns has no
   cheap way to remember which delta means what without re-reading a header each time.
2. No backend field computes "our rank minus ADP." Adding that column would mean computing it
   client-side from two independently-sourced numbers, which is closer to inventing a value than
   displaying one — thin justification against Principle #1 (every rendered number traces to a
   named backend field).
3. The raw ADP value placed beside CONS lets a reader compare three sourced numbers (consensus
   rank, ADP, our rank) directly, which is the information FR-024 actually asked for, without
   introducing an unsourced fourth number.

Recorded in `trace-fields.ts`'s 1.14.0 changelog entry and in the thread 082 reply so the reasoning
is visible from both places a future session would look.

## Evidence

`npm test`: **202 passed, 0 failed, 22 test files** (`frontend/`). `npx tsc -b --noEmit`: clean.
`npm run smoke` (against a live dev server, contract 1.14.0 confirmed via `curl`): **18/19 passed**
— the one failure (`no console errors during the loop`) is the pre-existing missing-
`ANTHROPIC_API_KEY` reasoning-proxy network error already documented in
`docs/frontend-cloud-runbook.md` as unrelated to any data screen; unchanged by this session.

Six screenshots, looked at directly (not just captured), in `frontend/e2e/artifacts/`:

- `adp-board-2026-07-29.png` — Board table, top 16 rows, ADP (MFL) column populated (Bijan
  Robinson 3.3, Ja'Marr Chase 2.9, ...).
- `adp-board-null-row-2026-07-29.png` — scrolled to rank 33 (Jeremiyah Love), ADP column shows
  "—" distinct from populated neighbors above and below.
- `adp-draft-room-2026-07-29.png` — Draft Room board list, compact ADP figures with "MFL"
  superscript beside the existing delta column.
- `adp-draft-room-null-row-2026-07-29.png` — same list scrolled to Jeremiyah Love, "—" with no
  MFL tag, delta and availability columns unaffected.
- `adp-player-detail-present.png` — Bijan Robinson detail sheet, MARKET ADP block: 3.3 avg pick,
  range 1–7, taken in 16% of sampled drafts, full caveat paragraph visible.
- `adp-player-detail-null.png` — Jeremiyah Love detail sheet, MARKET ADP block: "No MFL ADP data
  for this player -- MyFantasyLeague's public sample only covers roughly the top ~230 players in a
  10-team pull... Not a zero, not a rank -- not computed."

## Coordinator commit note

Most of this session's edits (`board.ts`, `contract.ts`, `trace-fields.ts`, `types.ts`,
`Board.tsx`, plus `DraftRoom.tsx`/`PlayerDetail.tsx`) appear in commits `b6d5a0d` and `75bf095`,
authored by the coordinator mid-session ("wip: ADP display, in flight" / "Also carries in-flight
ADP display work from the frontend chain"), not by a competing agent. Verified via `git diff HEAD
-- <files>` before concluding anything: empty diff both times, byte-for-byte the session's own
work. No reconciliation needed, work continued.

## Boundary

Touched only `frontend/**`, this status file, and thread 082. Did not touch `src/`, `tests/`
outside frontend, `.claude/`, `docs/pm/`, `docs/CURRENT-STATE.md`, `wrangler.jsonc`, `.github/`.

## Result

Commit (this session's remaining diff — screenshots + screenshot script): see `git log` after
`tools/handoffs.py sync`. Test count: 202 frontend unit tests passing, 0 failed, 22 files.
