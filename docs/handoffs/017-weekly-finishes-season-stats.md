---
ID: 017
FROM: pm
TO: backend
STATUS: OPEN
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
