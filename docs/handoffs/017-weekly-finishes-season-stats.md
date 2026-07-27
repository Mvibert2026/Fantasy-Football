---
ID: 017
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: consistency view, player detail history
---

## Ask
Two related tables, both in the confirmed gap list:
1. **Weekly finishes by player** — `{season, week, positional_finish}`.
2. **Season-level stats** — `{season, games, TGT, REC, YDS, TD}` per player.

Export both. Bump the contract. Tell `frontend`.

## Why
Weekly finishes drive the consistency heat-map; season stats drive the player detail history section.
Both are currently null-stated in the UI, honestly but emptily.

**One hard constraint.** Target-derived stats — targets, air yards, anything built on them — are
unreliable for **2003–2008**: present in the data but effectively zero, measuring nothing. The export
must mark those seasons as unavailable rather than shipping zeros. A zero and a "not measured" are
different claims, and Principle #2 says never substitute one for the other.

## Done looks like
Both artifacts exported, 2003–08 explicitly marked unavailable for target-derived fields, tests
asserting that marking, contract bumped, `frontend` notified. Commit hash and test count.

---
### backend · 2026-07-26

Implemented, via thread 039's concrete spec. `src/export_history.py` (new module) exports
`data/export/weekly_finishes.json` and `data/export/season_stats.json`; 2003-2008 target-derived
data marked `target_data_unavailable: true` / `targets: null`, never zeroed, per this thread's
hard constraint — verified directly against `data/nfl.db` (league-wide `SUM(targets)` collapses
to single digits those six seasons vs 16,000+ adjacent). 13 tests in
`tests/test_export_history.py`, all passing. `CONTRACT_VERSION` bumped 1.8.0 -> 1.9.0. Full
detail and frontend handoff in thread 043. Closing this thread — 039 carries the implementation
detail forward and 043 is the live frontend-facing one.
