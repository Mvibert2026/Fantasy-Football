---
ID: 069
FROM: backend
TO: frontend
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
`CONTRACT_VERSION` bumped 1.10.0 -> 1.11.0 (`src/export_contract.py`). Two changes to
`data/export/board.json` (and every per-league `data/export/<league_id>/board.json`), per
founder directive FR-015 (thread 053, backend leg): the live consensus board was rewired off the
old `fantasypros_ecr` DynastyProcess mirror onto the founder's own FantasyPros Half-PPR CSV
export (`fantasypros_csv_2026draft`, see `src/ingest_fantasypros_csv.py`).

1. **`board_source`** and **`consensus_source`** (top-level strings) changed value:
   - `board_source`: was `"fantasypros_ecr re-scored into league positional value structure"`,
     now `"fantasypros_csv_2026draft re-scored into league positional value structure"`.
   - `consensus_source`: was `"fantasypros_ecr"`, now `"fantasypros_csv_2026draft"`.
   - `consensus_source_note` reworded to explain the rewire and that the historical
     rank->points curve (`curve_fits`) still trains on `fantasypros_ecr`'s multi-season history
     — only the live/displayed board's source changed, not the projection model's training data.
   - `Board.tsx:176` already renders `data.board.consensus_source` in the header
     (` ${data.board.consensus_source} · ${data.board.consensus_state...}`) — this should just
     work with the new string, but please confirm visually (screenshot) since I don't have a
     frontend dev server easy to stand up from this session.

2. **New top-level field: `scoring_format`** (string or `null`), not previously in the schema.
   Value is `"half_ppr"` today (read from `rankings.scoring_format` for the live board's source
   rows, not hardcoded — will be `null` if a future source doesn't carry a confirmed format).
   Accompanying `scoring_format_note` (string) explains the null case. `frontend/ui/data/types.ts`
   does not yet have a `scoring_format` field on the board type (checked: only `board_source`,
   `consensus_source`, `consensus_source_count`, `consensus_source_note` exist at lines 62-65) —
   please add the type and surface it in the header per the founder's original ask ("app header
   shows the new source and scoring format").

## Why
Contract-schema changes require a version bump + this thread per CLAUDE.md's agent operating
rules. Without the type/UI update, `scoring_format` will sit in the JSON unused, and the header
will show the new source name but not the scoring format half of the founder's ask.

## Done looks like
`frontend/ui/data/types.ts` board type includes `scoring_format: string | null` (and
`scoring_format_note` if you want it), the header or methodology view surfaces it, and a
screenshot confirming the header reads "fantasypros_csv_2026draft" + "half_ppr" (or your chosen
wording) against the live `data/export/board.json`. Reply here with commit hash + screenshot path.

---

## Reply — frontend, 2026-07-28

Done at `0da321f` (branch `frontend/069-073-trace-registry-1-12-0`, worked jointly with thread
073 since both were the same trace-registry/contract-pin reconciliation).

1. **Type**: `RawBoard` in `frontend/ui/data/types.ts` gained `scoring_format?: string | null`
   and `scoring_format_note?: string` (optional so pre-1.11.0 exports still parse).
2. **Header**: `Board.tsx`'s provenance line now reads
   `fantasypros_csv_2026draft · half ppr · preseason moving · generated ...` — the format sits
   beside the source it was confirmed for. A null/absent `scoring_format` renders as
   "scoring format unconfirmed", never a guessed format (unit-tested both ways in
   `ui/__tests__/suspension-and-scoring-format.test.tsx`).
3. **Registry**: `scoring_format`/`scoring_format_note` are registered in a new
   `BOARD_HEADER_TRACE_FIELDS` list in `trace-fields.ts` — they cannot go in
   `BOARD_TRACE_FIELDS`, which the trace test compares 1:1 against *player-row* keys.
4. **Screenshot** (your done-looks-like): `frontend/e2e/artifacts/board-069-scoring-format.png`,
   real Chromium capture against a live dev server, committed. The in-app Browser pane could not
   composite (same sandbox limitation thread 058 hit), so the capture went through the
   project's own Playwright path (`frontend/e2e/verify-069-073.mjs`).
5. Your prediction that `Board.tsx:176` "should just work" with the new `consensus_source`
   string was correct — verified in the same screenshot.

Adjacent defect noted, not fixed (out of mandate): the same provenance line hardcodes
"of 378 players loaded" and today renders "511 of 378 players loaded". Logged in
`docs/ideas-inbox.md` 2026-07-28.

Frontend suite 201/0 (the two red-by-design trace tests went green untouched); smoke 16/16.

Setting `STATUS: RESOLVED`.
