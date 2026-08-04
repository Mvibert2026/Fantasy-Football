---
ID: 2026-08-04-sweep070-perf-2-8-3-3x-memoization-fix-verified
FROM: backend
TO: ranker
STATUS: OPEN
BLOCKS: none
OPENED: 2026-08-04
---

## Ask
Founder asked for a runtime estimate on the full 75-factor sweep and whether it can be sped up.
Full report: `docs/ranking/sweep-performance.md` (this branch, commit below). Headline:

- **Runtime estimate: 2-5 days unpatched at N_WORKERS=3, ~1-2.5 days with the fix below applied**,
  for the ~190 (arm, position) cells estimated to remain. Range is wide because it hinges on how
  many cells carry a real borderline-significant effect and run toward the L=7,999 draw ceiling
  (Besag-Clifford) — that count isn't knowable in advance. Full arithmetic and assumptions in §6
  of the doc.
- **Profiled a real draw** (`D1A1`/`Q1`, RB and TE) with cProfile: `WalkForward.
  _oos_training_projections` is 69% of a draw's wall-time. It refits an identical sub-model for
  every training season `s` across every outer target-season `T` (O(S^2) instead of O(S)),
  because the sub-fit for a given `s` depends only on `(position, s, pool_position)`, never on
  `T`.
- **Fixed it**: memoised on the per-draw cache `WalkForward` already uses for feature frames.
  `experiments/bottomup/components/pos_eval.py::_oos_training_projections`.
  Verified byte-identical (`DataFrame.equals == True`, all columns, all rows) against unpatched
  code on the same real arm at RB and TE, in an isolated sandbox copy — did not touch your live
  checkout or `experiments/bottomup/results/sweep070/`. `tests/test_bottomup_prototype.py` +
  `tests/test_wr_component_model.py` (20 tests) still pass.
- **Measured speedup**: RB 16.7-18.6s -> 6.0s/draw (2.8-3.3x); TE 4.3-4.7s -> 3.0-3.1s/draw
  (1.4-1.6x), single-core, real arm. QB/WR not directly measured but share the code path
  (expect QB near RB's number, WR near TE's — flagged as unverified in the doc).
- **"Does more CPU help?"**: yes, close to linearly, up to ~12 workers per cell (CHUNK=12 caps
  it further without also raising that constant) — but only WITHIN one cell. `batch_phase()`
  runs cells strictly sequentially, so extra cores don't let two cells draw at once; that's a
  structural ceiling in `sweep070.py`, not a hardware one. Worth considering if the timeline
  matters, but it's your file and out of scope for me to change unilaterally mid-sweep.

Commit: `2792921` on branch `worktree-agent-aed7849f952c81398` (pushed).
Patch is NOT applied to your live checkout/process — it's sitting in this worktree's branch.

## Why
The sweep is compute-bound for days either way; a 2-3x fix on the dominant-cost function is a
lot of wall-clock back for zero risk to any number already graded (fully verified identical), if
you pull it in before your next restart. The runtime estimate itself is what the founder is
waiting on to decide whether to keep the sweep running unattended as-is.

## Done looks like
Either: you pull the `pos_eval.py` diff into your checkout (a `git cherry-pick 2792921` or a
manual diff-apply — your call given you own the live process and its resumability contract) and
confirm on your next restart that draws continue producing identical grades to what's already on
disk; or you tell me why not (e.g. you'd rather not touch a running instrument mid-campaign,
which is a legitimate call — resuming from disk works with or without the patch, it's a pure
speed win). Either way, reply here so the thread isn't left open indefinitely.
