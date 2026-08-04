# backend, 2026-08-04 — ADR-070 sweep070 performance pass

Dispatch: founder asked directly for a runtime estimate on the full 75-factor sweep and whether
it can be made faster (compute vs. a smarter method). Full report: `docs/ranking/
sweep-performance.md`.

## What was done

1. Read `experiments/bottomup/v2/sweep070.py`, `adr070.py`, `ensemble070.py`, `grade070.py`, and
   `docs/ranking/adr070-tier2-execution.md` to understand the actual phase structure, the
   Besag-Clifford stopping rule (h=20 exceedances or L=7,999 draws), and that `M_CAMPAIGN` growth
   is already handled by a pre-registered fixed `L_DRAWS=7999` ceiling valid to M≤400 (campaign is
   at M=333) — the dispatch's "L grows with M" caution is correct in general but already resolved
   by design here, worth noting so nobody re-derives it as a live problem.
2. Counted registered arms/cells directly (`ensemble070.ARMS070`): C1 12 arms/38 cells, C2 12/29,
   D1A1 5/20, VERIFY 3/12 — 99 cells currently coded; C3/C4/AB1 flag-driven, not yet imported.
3. Profiled a real draw (`D1A1`/`Q1`, RB and TE, not a synthetic case) with `cProfile` against the
   real database: `WalkForward._oos_training_projections` is 69% of a draw's cost.
4. Found the mechanism: that method refits an identical sub-model per training season `s` inside
   every outer target-season `T`'s calibration loop — O(S²) instead of O(S), because the sub-fit
   for a given `s` depends only on `(position, s, pool_position)`, never on `T`.
5. Fixed it by memoising on the WalkForward instance's existing per-draw cache
   (`experiments/bottomup/components/pos_eval.py::_oos_training_projections`).
6. **Verified byte-identical**, not just "looks right": built an isolated sandbox copy of the full
   `experiments/` tree (symlinked to the real `data/nfl.db`, no writes), ran the same real arm
   unpatched vs. patched at RB (1,556 rows × 82 cols) and TE (1,040 × 78) — `DataFrame.equals ==
   True` both times, zero differing cells. Ran `tests/test_bottomup_prototype.py` +
   `tests/test_wr_component_model.py` (20 tests) against the patched file — all pass.
7. Measured speedup: RB 16.7-18.6s → 6.0s/draw (2.8-3.3×); TE 4.3-4.7s → 3.0-3.1s/draw (1.4-1.6×),
   single-core.
8. Wrote the runtime estimate: **2-5 days unpatched at N_WORKERS=3, ~1-2.5 days patched**, for
   ~190 remaining (arm, position) cells — stated as a range because the dominant unknown (how many
   cells carry a real borderline effect and run the sequential test out to L=7,999) can't be known
   in advance; the arithmetic and every assumption behind it are in the doc, not just the
   conclusion.
9. Answered "does more CPU help": yes, close to linearly, but only *within* one cell
   (`pool.imap` over `CHUNK=12` draws) — `batch_phase()` runs cells strictly sequentially, so more
   cores don't let two cells draw at once. That cross-cell serialization, not core count, is the
   real ceiling; changing it is a `sweep070.py` edit, `ranker`'s file, flagged not made.
10. Committed the fix + report (`2792921`), pushed, opened handoff thread
    `2026-08-04-sweep070-perf-2-8-3-3x-memoization-fix-verified` to `ranker` (owns the live
    checkout/process; the patch is not applied there yet — it needs a deliberate pull-in, which is
    `ranker`'s call given they own the running instrument's resumability contract).

## What was explicitly not done (out of scope per dispatch)

- No change to the estimator, draw count, stopping rule, BH correction, or any statistical
  constant — `strategist`'s territory.
- No change to which factors run or how many — founder's call.
- No edit to `experiments/bottomup/results/sweep070/` or the live `sweep070.py` process.
- Did not vectorise `ols()`/`binom_glm()` — measured at ~20% of a draw combined, smaller win than
  the fix made, and swapping `lstsq` for a normal-equations solve risks diverging on
  near-rank-deficient inputs (`binom_glm`'s ridge exists precisely to guard against that), i.e.
  exactly the "speed that changes a number" the dispatch warned against without a much larger
  verification effort than this session's budget allowed.
- Did not directly profile QB/WR (time-boxed); flagged as unverified-but-expected-similar in the
  report rather than silently assumed.

## Evidence

- Commit `2792921`, branch `worktree-agent-aed7849f952c81398` (pushed to origin).
- `docs/ranking/sweep-performance.md` — full arithmetic, profiling output, identity-verification
  transcript, and the "more cores" analysis.
- `docs/handoffs/2026-08-04-sweep070-perf-2-8-3-3x-memoization-fix-verified.md` — thread to
  `ranker`.
- `docs/CURRENT-STATE.md` — summary paragraph added in place near the top status block.
- Test count: 20/20 pass (`tests/test_bottomup_prototype.py`, `tests/test_wr_component_model.py`)
  against the patched file, in this worktree.

## Founder-request capture

Not applicable — the founder's ask ("figure out if there is a faster method of testing, or do you
need CPU power") was the dispatch itself, already tracked; nothing new was expressed to log to
`docs/founder-requests/`.
