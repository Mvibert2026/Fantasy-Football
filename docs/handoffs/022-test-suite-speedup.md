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

---
### backend · 2026-07-26

Fixed. Two changes, both test-only -- no `src/` code touched, no coverage removed:

1. **`tests/conftest.py`**: session-scoped autouse fixture memoizes
   `archetypes.compute_player_season_inputs(conn, data_season)`, the single expensive SQL
   aggregation (player_weekly_stats/snap_counts join, ~35-40s uncached) that
   `test_archetypes.py::TestAgainstRealData` and `test_player_descriptions.py::TestAgainstRealData` /
   `TestExport` each recompute fresh, directly or transitively through `assign_for_season` /
   `generate_all_descriptions`. Keyed on `(data_season, positions)`, cleared at session end. Every
   test still calls the real function through the real call path and gets the real (deterministic,
   per the project's own regeneratability tests) result -- just computed once instead of ~7 times.

2. **`tests/test_multi_league_export.py::TestBoardJsonGeneralizes`**: same pattern, smaller win --
   4 tests each rebuilt a fresh ~2000-bootstrap `build_board_json(conn, _yahoo_mock())` (~7-10s each).
   Replaced with a single `scope="class"` fixture the 4 tests now share.

**Before:** ~5.7 min per the thread (confirmed independently: an unmodified run of
`test_archetypes.py` alone took 119s, almost entirely 3 x ~40s real-data calls).
**After:** full suite **107s (1:47)**, `--durations` confirms the former worst offender
(`test_assign_for_season_runs_and_produces_a_mix_of_archetypes`) dropped to 26.85s (one real
computation, the other two real-data tests in the same class now near-instant).

**Test count:** 423 collected, 422 passed, same as before this change -- no test removed, none
skipped, none newly parametrized-away. One pre-existing failure, **unrelated to this thread**:
`tests/test_handoffs.py::test_mailbox_health` fails on a duplicate thread ID (036, two files) and an
unaddressed thread (031-ADDENDUM) that both predate this session. Not touched here -- see the reply on
thread 016 and the mailbox-hygiene note below; whoever owns those two 036 threads needs to re-file one
of them.

Commit: `<see closing commit>`. Suite: 423 collected / 422 passed / 107s.

STATUS: RESOLVED
