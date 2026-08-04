# ADR-070 sweep — runtime estimate, profiling, and a verified speedup

**backend, 2026-08-04.** Dispatch: estimate wall-clock for the full 75-factor queue, find out
where the time goes, optimise only where provably identity-preserving. Not in scope: touching
`experiments/bottomup/results/sweep070/` or the live sweep process (`ranker`'s), changing the
statistics, dropping factors.

---

## NEXT STEP

*Rewritten on every update. Being cut off is the expected case.*

1. **The fix below (`pos_eval.py::_oos_training_projections` memoisation) is committed in this
   worktree but NOT applied to the live sweep.** `ranker` owns `experiments/bottomup/results/
   sweep070/` and the running process; this patch needs `ranker` (or whoever restarts the
   detached sweep) to pull it in before the next restart. It is safe to apply mid-campaign: it
   changes nothing about what gets computed, only how many times, and identity was verified
   against the code as currently deployed (see §3).
2. Opened no thread yet — flagging this in the session reply is the handoff; if `ranker`'s next
   restart doesn't pick this commit up, open `docs/handoffs/` thread `backend → ranker` pointing
   here.
3. Not yet done, worth someone's five minutes: apply the same profiling pass to a C1/C2 arm (this
   report profiles D1A1/Q1 only) to confirm the speedup generalises — expected to, since the
   `_oos_training_projections` code path is shared by every arm regardless of batch, but not
   directly measured here.

---

## Headline: the runtime estimate

**Unpatched, at the current `N_WORKERS = 3`: roughly 2–5 days of wall-clock for what's left of
the 75-factor queue. With the fix in §3 applied: roughly 1–2.5 days.** This is a *range*, not a
point estimate, and the width is real — it depends on a fraction of the queue that cannot be
known until the arms are actually drawn (see "why the range is wide" below). If the founder is
expecting single-digit hours, that expectation should be revised now, not discovered three days
into a run.

**The arithmetic, shown, not just the conclusion:**

- **Cells to run.** Currently registered in `ensemble070.ARMS070`: C1 (12 arms / 38
  arm×position cells), C2 (12 / 29), D1A1 (5 / 20), VERIFY (3 / 12) — 32 arms, 99 cells, measured
  directly by importing the module and counting (`ARMS070` dict). C3/C4/AB1 are flag-driven and
  not yet imported; their registered test counts (`m_b` = 25, 22, 27 in `grade070.M_EXTRA_
  REGISTERED`) imply roughly another 74 factor-tests, but arm-to-position ratio for those isn't
  measurable until their adapters land. Using the observed ratio across what IS registered (87
  cells / 29 arms ≈ 3.0 positions/arm) and the founder's stated "75 factors," the full campaign
  is **on the order of 220–230 (arm, position) cells total**, of which 32 (VERIFY + D1A1
  observed) are done or in flight per `state.json` (`phases_done: ["VERIFY"]`,
  `observed_D1A1` timing present). Call it **~190 cells remaining.**
- **Per-cell draw count is NOT fixed and NOT small — this is the part likely to surprise.** The
  Besag–Clifford sequential test (`adr070.bc_sequential_p`) stops a cell at whichever comes
  first: 20 exceedances (`H_EXCEED`) or **7,999 draws** (`grade070.L_DRAWS`, a ceiling
  pre-registered to stay valid up to campaign M ≤ 400 — the campaign is at M = 333 now, so this
  ceiling does **not** grow further this campaign; the dispatch's warning that L grows with M is
  correct in general but the codebase already fixed L once, in advance, rather than
  recomputing it live). Concretely:
  - A **null arm** (no real effect) hits 20 exceedances fast, because roughly half of null draws
    "exceed" a near-zero observed delta by chance — `docs/ranking/adr070-tier2-execution.md` §D10
    already measured this at **~120 draws for a typical null cell**, and that estimate matches
    the shape of the VERIFY calibration data.
  - An arm with a **real, borderline-significant effect** is the expensive case: real signal
    means null draws rarely exceed it, so exceedances accumulate slowly, and the cell can run all
    the way to **L = 7,999 draws** before the sequential test resolves at all — this is the
    tail that dominates wall-clock, not the typical cell.
  - Historically on this project only a handful of factors per batch have turned out to be real
    (the factor ledger's 92 rows are overwhelmingly NULL/EXCLUDE), so most of the ~190 remaining
    cells should be cheap. But "a handful" per batch, applied to ~190 cells, is still plausibly
    10–25 cells that go the distance to (or near) 7,999 draws, and **that's what the width of the
    range above is pricing in** — I do not know that count in advance and neither does anyone
    else; it is discovered by running the test, which is the entire point of it.
- **Per-draw cost, measured, not assumed** — see §2 for the profiling and §3 for the two
  numbers (unpatched vs. patched) that feed the estimate above:

  | | unpatched, single-core | patched, single-core | speedup |
  |---|---|---|---|
  | RB (deep window, S≈9–12) | 16.7–18.6 s/draw | 6.0 s/draw | **2.8–3.3×** |
  | TE (shallow window, S≈7–11) | 4.3–4.7 s/draw | 3.0–3.1 s/draw | **1.4–1.6×** |

  These are real (arm, position) draws — `D1A1`/`Q1`, not a synthetic case — measured by running
  the actual `ensemble070.run_players` end to end against the real database. With `N_WORKERS = 3`
  the wall-clock per draw is roughly this divided by 3 (measured parallel efficiency is close to
  linear — see the VERIFY numbers in `state.json`, where `CPU-time ≈ 3 × wall-time` per position
  to within ~10%).

**Putting it together:** ~190 cells × (weighted-average draws/cell, dominated by the unknown
"how many go to 7,999" fraction) × (per-draw wall-time at 3 workers) lands at 2–5 days unpatched,
1–2.5 days patched, for a 10–25-cell tail assumption. If the tail turns out to be larger (a bad
batch with many borderline arms) or smaller (a clean batch, mostly obvious NULLs), the true
number moves within — plausibly outside — that range in either direction. **This is not a
number to promise a deadline against; it is a number to decide, with, whether to keep running
unattended ("tests are compute, not tokens," per `sweep070.py`'s own docstring) or to intervene.**

---

## §1. What was measured, and where it came from

- `experiments/bottomup/results/sweep070/state.json` (read-only, `ranker`'s live sweep, not
  touched): VERIFY phase timings, 4 positions × 200 fixed draws each — QB 122.9 s, RB 821.5 s,
  WR 286.3 s, TE 193.2 s wall, all under `N_WORKERS = 3`. That's **1,423.9 s (23.7 min) for 800
  draws total**, matching the dispatch's "24 minutes for 4 cells."
- Environment: 4 CPU cores, load average 4.4–4.7 measured twice during this session (getting
  *more* saturated, not less, while this report was being written) — confirms the "already
  saturated" framing in the dispatch. `nproc` = 4, 7 sweep processes were already running when
  this session started.
- A fresh, direct profile of a real (non-placebo) arm, `D1A1`/`Q1` at RB and TE, run single-core
  (no pool) against the real database, both before and after the fix in §3 — see below.

---

## §2. Where the time actually goes (measured with `cProfile`)

One permutation draw, `D1A1`/`Q1`/RB, k=1, unpatched, single-core, 23.9 s total, 22.6M function
calls:

```
ncalls  cumtime  function
     1    23.91  WalkForward.run()
    12    16.54  WalkForward._oos_training_projections   <- 69% of the draw
   198    12.94  RBComponentModel.fit
   198    12.55  BaseComponentModel.fit
    34     4.31  build_features_v2 (feature construction)
  1260     2.69  binom_glm (IRLS bonus-threshold fit)
  2376     1.92  np.linalg.lstsq (OLS volume/rate fits)
```

**`_oos_training_projections` is the dominant cost, at 69% of the draw**, exactly matching the
dispatch's hypothesis that the loop re-fits a model in a Python loop. It is called once per
target season (12 calls for RB's S≈12-season window) and, per its own docstring, exists only to
generate expanding-window out-of-sample projections to calibrate the bonus curves — it is not
the primary model fit, it's an auxiliary calibration step, and it is where 198 of the run's
~210 total model fits happen (12 primary fits + ~186 calibration sub-fits).

Neither `lstsq` nor `binom_glm` (the two "is this just an unbatched matrix op" suspects) is
individually the bottleneck — together they're under 20% of the draw. **The dispatch's "closed
form for permuted refits" instinct was right in spirit but aimed at the wrong layer**: the
expensive part isn't that OLS is being redone unnecessarily inside one fit, it's that an entire
*model* (which happens to contain several OLS/IRLS fits) is being refit unnecessarily across
outer loop iterations. See §3.

---

## §3. The fix — provably identity-preserving, measured 1.4–3.3×

**The bug (not a bug in correctness, a bug in the loop structure):**
`WalkForward.run()` calls `_oos_training_projections(tf, to, pool)` once per outer target season
`T`, where `tf, to` are truncated at `T-1`. Inside, the method loops over every training season
`s < T` and fits a fresh model on `{data with season < s}` to project season `s`. But that
sub-fit's result **depends only on `(position, s, whether a rate-pool is attached)` — never on
`T`.** Consecutive target seasons' `oos` loops overlap almost completely: scoring `T=2016` refits
the identical sub-models for every `s` already fit while scoring `T=2015`. This is `O(S²)`
sub-fits where `O(S)` distinct ones exist.

**The fix** (`experiments/bottomup/components/pos_eval.py::_oos_training_projections`):
memoise each `s`'s sub-fit result on `self._cache` — the same dict `WalkForward` already uses to
cache season-level feature frames, reset fresh for every `WalkForward` instance (i.e. every
draw, so no cross-draw contamination is possible). No change to what is computed, no change to
any tolerance, seed, or draw order — only the redundant recomputation is removed.

```python
key = ("_oos", self.position, int(s), self.pool_position)
hit = self._cache.get(key)
if hit is None:
    ...  # exactly the original fit + predict
    self._cache[key] = hit
```

**Verified byte-identical**, not just "looks the same": ran the real `D1A1`/`Q1` arm at RB (k=0
and k=1) through an unpatched sandbox copy and a patched sandbox copy of the full `experiments/`
tree — same database, same code elsewhere, only this one function's internals different — and
diffed all 82 numeric output columns for all 1,556 player-season rows:

```
shapes: (1556, 82) (1556, 82)
cells differing: 0
a.equals(b): True
```

Same check repeated at TE (which exercises the `pool_position` borrowing path RB doesn't use):
1,040 rows, 78 columns, `a.equals(b) == True`.

**Also ran the pos_eval-adjacent test suites** (`tests/test_bottomup_prototype.py`,
`tests/test_wr_component_model.py`, 20 tests) against the patched file — all pass.

**Measured speedup, same real arm, single-core:**

- RB: 16.7–18.6 s → 6.0 s per draw (**2.8–3.3×**). RB has the deepest window (`first_feature_
  season = 2002`, up to 12 target seasons), so it has the most quadratic redundancy to remove —
  consistent with the mechanism.
- TE: 4.3–4.7 s → 3.0–3.1 s per draw (**1.4–1.6×**). Shallower window (`S ≈ 7–11`), so less
  `O(S²)` overhang, smaller but still real win.
- QB and WR were not directly profiled this session (time-boxed); given they share the exact
  same code path, expect QB (deep window, like RB) to land nearer the RB speedup and WR (shallow,
  like TE) nearer the TE speedup, but this is not measured and should be confirmed before citing
  a number for those two positions specifically.

**Where this patch lives right now:** committed in this worktree
(`experiments/bottomup/components/pos_eval.py`), **not yet applied to the live sweep**
(`ranker` owns that checkout and process — see NEXT STEP). It is safe to hot-apply: the running
sweep resumes from disk state regardless of code changes between restarts (`sweep070.py`'s own
resumability design), and this patch changes no seed, no draw order, no tolerance — a restart
after pulling it in will continue producing the identical numbers, just faster.

---

## §4. What was NOT changed, and why

- **`ols()` / `binom_glm()` internals** — considered and measured (§2: ~20% of a draw combined),
  but not vectorised across the many small independent fits within one model, for two reasons:
  (a) it's a smaller win than the `_oos_training_projections` fix and would cost more engineering
  time to get provably identical (small-matrix `lstsq` vs. normal-equations `solve` can diverge
  on near-rank-deficient inputs, which `binom_glm`'s ridge specifically guards against — swapping
  the linear-algebra routine is exactly the kind of "speed that changes a number" the dispatch
  warned against, and verifying it stays identical across every rank-deficient corner case in the
  real data would cost real time); (b) it wasn't the dominant cost once `_oos_training_
  projections`'s redundancy is removed.
- **Draw count, stopping rule, `N_WORKERS`, `CHUNK`, the estimator, the correction** — explicitly
  out of scope per the dispatch; untouched.
- **`sweep070.py` itself and anything under `experiments/bottomup/results/sweep070/`** — owned by
  `ranker`, live, not touched.

---

## §5. Does more CPU help?

**Yes, close to linearly, up to a real structural ceiling — and that ceiling, not core count, is
the more interesting finding.**

- **Within one cell, draws are embarrassingly parallel.** `sweep070.py`'s `run_ensemble` submits
  draws in chunks of 12 (`CHUNK = 12`) to a `multiprocessing.Pool(N_WORKERS)`, and each draw is
  fully independent (different seed, no shared mutable state across processes — the panel is
  shared copy-on-write, read-only). The VERIFY timings are consistent with close-to-linear
  scaling: CPU-time ≈ 3 × wall-time per position, to within ~10%, at `N_WORKERS = 3`. Going to,
  say, 15 workers on a 16-core box should buy close to a 5× reduction in per-cell wall-clock, up
  to the `CHUNK = 12` ceiling — **workers beyond 12 buy nothing extra per round without also
  raising `CHUNK`**, since only 12 draws are in flight at once between sequential
  Besag–Clifford stopping checks.
- **Across cells, there is no parallelism at all — this is the real ceiling, not the core
  count.** `batch_phase()` in `sweep070.py` loops over arms and positions and calls
  `run_ensemble` **one cell at a time**; the next cell's draws don't start until the current
  cell's sequential test has resolved (h reached or L exhausted). A 4-core box and a 64-core box
  behave identically here: at any instant, only one cell is being drawn, using at most
  `min(N_WORKERS, CHUNK)` cores. **More cores speed up each cell in turn; they do not let two
  cells run at once.** The bigger lever — restructuring `batch_phase` to run several cells'
  pools concurrently — is a real option but is a change to `sweep070.py`, which is `ranker`'s
  live file and out of scope for this dispatch; flagging it here as the structural finding rather
  than making the change.
- **On this specific box right now: more cores is not a live option anyway.** 4 cores, load
  average 4.4–4.7 measured twice during this session, 7 sweep processes already running — the
  box is already oversubscribed relative to its own core count, which is *also* why the
  measured wall-clock per draw (e.g., RB at `N_WORKERS = 3` implying ~12.3 s CPU/draw from
  VERIFY) runs a bit worse than the raw per-draw CPU cost alone would predict: contention from
  whatever else is running eats into the "close to linear" scaling claimed above. **A machine
  with cores actually free for this workload — not just more cores nominally — is what would
  show the full benefit.**

**Bottom line for the founder's question:** yes to CPU, with two caveats — (1) it only helps
up to ~12 workers per cell without also touching `CHUNK`, a code constant, and (2) it does
nothing for cross-cell throughput without a structural change to the driver, which is a real
option worth `ranker`/`strategist` considering if the campaign timeline matters, but is not
something to do unilaterally mid-sweep.

---

## §6. Assumptions, stated plainly

- The 190-remaining-cells figure blends measured counts (32 done, ~29 arms/87 cells currently
  registered) with the founder's stated "75 factors" and an observed ~3 positions/arm ratio; it
  is an estimate, not a count, for the batches not yet coded (C3/C4/AB1).
- The draws-per-cell range leans on `docs/ranking/adr070-tier2-execution.md`'s own "~120 draws
  for a typical null cell" figure and this project's historical hit rate (factor ledger:
  overwhelmingly NULL) to guess a 10–25-cell tail that runs toward L = 7,999. That guess is the
  single largest source of uncertainty in the headline range and cannot be tightened without
  either running more of the queue or asking `strategist`/`ranker` for their own prior on the
  batch's expected hit rate.
- Per-draw costs for QB and WR are extrapolated from the shared code path, not directly measured
  this session — flagged above, not hidden.
