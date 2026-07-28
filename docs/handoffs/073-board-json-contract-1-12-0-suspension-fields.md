---
ID: 073
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
`CONTRACT_VERSION` in `src/export_contract.py` bumped 1.11.0 -> 1.12.0 (ADR-053). Every player
row in `board.json` (`data/export/**/board.json`, all league configs) now carries four new keys,
unconditionally on every row (never conditionally present):
- `suspension_flag` (bool)
- `suspension_games` (int or null)
- `projected_points_suspension_adjusted` (float or null -- null when `suspension_flag` is false,
  OR when true but the appeal is still pending, i.e. `suspension_adjustment_note ==
  "not_adjusted_pending_appeal"`)
- `suspension_adjustment_note` (string: `"not_suspended"` / `"games_adjusted"` /
  `"not_adjusted_pending_appeal"`)

Mechanism: `src/suspensions.py` (deterministic games-played deduction, NOT a probability model),
driven by a real, hand-curated, dated list at `data/suspensions_2026.json`. That list is
CURRENTLY EMPTY (verified via exhaustive WebSearch, as_of_date 2026-07-27 -- see that file's
`_comment` and ADR-053 in `docs/decisions.md` for the full research trail), so today every board
row reads `suspension_flag: false`. This is expected, not a bug -- it will start populating the
moment a real skill-position (QB/RB/WR/TE) suspension is confirmed and added to that file.

Same trace-field-registry gap pattern as threads 066/069 (roster_status/scoring_format): your
`ui/__tests__/trace-fields.test.ts`'s `TRACE_CONTRACT` will need these four fields added when you
next touch it, the same way it's currently red for not knowing about 1.10.0/1.11.0's fields.

## Why
Contract-version drift between `src/export_contract.py` and the frontend's own field registry is
exactly the gap threads 066/069 already flagged unresolved (frontend's version banner correctly
shows this drift; `TRACE_CONTRACT` still pinned at 1.9.0 as of this session). Not acting on it
doesn't break anything today (fields are additive, and every current value is the "not suspended"
default), but it's one more version behind for whoever eventually reconciles 066/069/073 together.

## Done looks like
`TRACE_CONTRACT` (or equivalent field registry) updated to acknowledge contract 1.12.0 and the
four new fields, OR an explicit reply here saying it's being bundled into the 066/069 reconciliation
pass instead of done standalone. Either is fine -- silence is not.
