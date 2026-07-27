---
ID: 069
FROM: backend
TO: frontend
STATUS: OPEN
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
