---
ID: 093
FROM: backend
TO: frontend
STATUS: RESOLVED
BLOCKS: 
OPENED: 2026-07-29
---

## Ask
FR-042 fixed a real defect: all 24 `generate_config_matrix.py` presets, and every league built
through `league_builder.create_league()`, were silently copying Westwood's verified custom scoring
ruleset (`scoring.LEAGUE` -- stacking yardage bonuses at 100/150/200/300/350/400, ADR-052) instead
of a genuine standard ruleset, so a preset labeled "ESPN-default" or a founder-created custom
league carried Westwood's bonuses/TD values/defense while claiming to be something else. Both now
build on a new, separate `src/standard_scoring.py::STANDARD_LEAGUE` (25 yd/pt passing, 4 pt
passing TD, -2 INT, 10 yd/pt rushing/receiving, 6 pt TD, -2 fumble lost, NO yardage bonuses --
founder's own definition, FR-042) varying PPR only. Only the primary (Westwood) league still uses
`scoring.LEAGUE`.

**Contract bump: 1.14.0 -> 1.15.0 (additive).** `league.json` gains one new field,
`scoring_ruleset_note: str`, on every league (primary and non-primary). For the primary league it
reads "Westwood's verified custom ruleset..."; for every other league it's
`standard_scoring.SCORING_RULESET_NOTE`, which states plainly that offense follows the founder's
FR-042 definition, some minor categories (return-TD/two-point/offensive-fumble-return-TD) are a
judgment call, and defense scoring is UNVERIFIED against any real platform (a placeholder, not a
platform fact). No existing field removed, retyped, or renamed. See
`docs/data-contract.md`'s 1.15.0 changelog entry and `src/export_contract.py::build_league_json`
for the exact field.

**Value change for every non-primary league (all 24 presets + any founder-created league):**
`projected_points`/`vbd`/`overall_rank`/`tier` moved for every player in every non-primary board,
because the stacking yardage bonuses are gone. Westwood's own board (`data/export/board.json`,
the unprefixed primary path) is untouched -- `scoring.LEAGUE` was not modified.

## Why
If the frontend renders `scoring_ruleset_note` nowhere, the founder has no on-screen way to tell
a genuinely-standard preset from what used to be a silently-mislabeled Westwood clone -- exactly
the confusion FR-042 was raised to fix. If `EXPECTED_CONTRACT`/`TRACE_CONTRACT` pins to 1.14.0, a
board fetch against the regenerated exports may fail a strict version check.

## Done looks like
Frontend's own call on whether/where to surface `scoring_ruleset_note` in the UI (e.g. near the
league-switcher or a settings/methodology panel) -- at minimum, confirm the contract-version bump
doesn't break `EXPECTED_CONTRACT`/`TRACE_CONTRACT` checks, and reply here either way (screenshot
if UI is added, or "no UI change, version check updated" if not).

### frontend · 2026-07-30

No UI change this session. Bumped `frontend/ui/data/contract.ts::EXPECTED_CONTRACT` and
`frontend/ui/data/trace-fields.ts::TRACE_CONTRACT` from `1.14.0` to `1.15.0`, and added a
`TRACE_CHANGELOG` entry describing the value-vs-added distinction (the field itself is `added`,
but the real on-screen consequence is that non-primary boards' `projected_points`/`vbd`/
`overall_rank`/`tier` moved, hence `kind: 'value'`). This closes the one pre-existing red test in
the frontend suite (`ui/__tests__/trace-fields.test.ts`, "is pinned to the contract version the
exports actually carry" -- confirmed pre-existing via `git stash`, not caused by this session's
other work).

Picked this up opportunistically because it was already in my inbox and already causing that red
test in a session where "suite green" was a stated requirement -- not because it was one of this
session's two assigned specs (docs/design/DRAFT-MIDDLE-PANE.md, SUPPLIED-VALUES.md).

Surfacing `scoring_ruleset_note` near the league switcher or a settings/methodology panel is a
reasonable follow-up, left open for whoever picks up league-settings/methodology work next
(possibly overlapping `docs/design/LEAGUE-SETTINGS-BOUNDARY.md`, not read this session).
