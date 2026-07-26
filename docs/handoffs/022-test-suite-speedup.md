---
ID: 022
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Cut the test suite runtime. It has gone from ~1.3 minutes to ~5.7 minutes, and the cause is recorded:
DB-backed `archetypes` and `player_descriptions` tests running 15–60 seconds each, uncached.

Add session-scoped fixtures or a cached test database so the expensive setup happens once rather than
per test. Do not reduce coverage to buy speed.

## Why
A slow suite gets run less often, and a suite that is run less often stops being a safety net. At
5.7 minutes it is still tolerable; the trajectory is the problem, and every new DB-backed test makes
it worse. Cheapest possible moment to fix it is now.

There is a second-order cost specific to this project: every agent session that runs the suite pays
that wall-clock time, and long-running commands are where sessions get interrupted or time out.

## Done looks like
Suite under 2 minutes with the same test count and no coverage lost. Report before and after timings.
Commit hash and test count.
