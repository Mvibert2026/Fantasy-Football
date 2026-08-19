# 2026-08-19 — PM: two bugs were eating the campaign, not a compute shortage

## The premise that was wrong

The working theory for days was that the ADR-070 inclusion campaign was compute-starved, and
the response escalated accordingly: parallelise, move to GitHub Actions, and finally rent a
32-vCPU box. The founder's read — *"It's insane we've made so little progress"* — was correct
about the symptom and the diagnosis was wrong about the cause.

Two defects were destroying essentially all of it. Neither is about compute, and the rented
box would have hit both at $0.96/hr.

## Bug 1 — `KeyError: 'T2P'`, five consecutive runs

Control-factor families are registered as an import side effect, and they are shared across
batches: `T2P` is defined in `factors_c3_adapter.py` and used by C4. Running a single batch in
isolation therefore left `ens.TIER2` half-built, and every matrix job died on it.

This had been "fixed" once already, and the fix was wrong — it imported a module list derived
from the wrong source. Verified properly this time, end to end rather than at import level:

```
TIER2 keys: ['T2A','T2B','T2C','T2D','T2I','T2P','T2Q']
T2P present: True          C4 arms: 13
```

Timeline worth recording, because it explains a confusing log: the fix landed at 03:56 and the
last crash was committed at **03:30**. Every traceback in `sweep_C4.log` predates the fix. The
fix had never been exercised in CI when it looked like it was still failing.

## Bug 2 — the push loop could not survive its own concurrency

This is the expensive one. Four matrix jobs finish within seconds of each other and all push to
one branch. The retry was `git pull --rebase && git push`, five times.

That cannot work. A conflict on a binary draws archive **stops the rebase and leaves the
repository in a rebase**, so every later attempt failed on "cannot pull during a rebase"
regardless of contention having cleared. One conflict poisoned all five retries and the job
exited having computed for hours and saved nothing.

The evidence had been visible for days and was misread as "only C4 is running": every run
committed exactly one batch and the campaign report. Only one job ever won the race. Six lost
their compute, every run, silently.

`tools/sweep070_push.py` aborts the rebase and reconciles by union instead. The union is exact
rather than a heuristic, which is the only reason this is safe: draws are pure functions of
`(cell, k)` and append-only, so *longer wins* IS the union for a cell, and the archive is a pure
function of the live draws. So `take their archives -> restore (only ever lengthens) ->
re-archive` provably yields both sides' compute. Cell rows are unioned on their natural key
instead, being rows rather than sequences.

Deliberately **not** a force push: that would "resolve" the conflict by deleting the other
worker's hours of work, which is the exact failure being fixed.

The reconcile runs `git reset --hard`, so it refuses outright when anything outside the results
tree is dirty. Tested against a synthetic two-worker repo — union of draws, survival of each
worker's exclusive cells, union of the shared control shard, and the refusal
(`tests/test_sweep070_push_reconcile.py`, 2 passed).

## The rented box

The founder rented `cpu3c-32-64` and could not reach a shell on it: *"I don't see 'start web
Terminal'... I'm going to turn off the pod and do this tomorrow."* The pod billed while nothing
ran. Captured as FR-2026-08-19: **any rent-a-box plan must be startable from a web console**,
because a plan whose first step is "open a terminal" is not one the founder can execute.

`docs/rented-box-runbook.md` now records the no-terminal path (env var + container start
command, both deploy-form fields) and the billing trap that **Stop does not end the bill —
Terminate does**. Nothing on the box is worth keeping; the setup script rebuilds the database
from public sources in ~3 minutes.

The honest conclusion, though, is that the box was the wrong instrument for this problem. A
faster machine fails faster. Actions is free and uncapped on a public repo.

## Verified working, locally

A 15-minute local run of AB1 after the fix completed **5 cells cleanly** — `ABAGE` at all four
positions and `ABEVID` at QB, all `stopped (h_reached)` in 21–51s each. Cells reached and
banked, no crash. That is the first end-to-end evidence the pipeline works post-fix.

**Do not read those five as results yet.** They are 5 of 27 in one batch, ungraded, and grading
applies BH at campaign M. `p_two=1` on an ablation arm is suggestive that the ablated term is
doing nothing, and that is precisely the AB1 question — but 5 uncorrected cells is a look, not
a verdict.

## State

| | |
|---|---|
| Batches graded | 1 of 8 (D1A1) |
| Pool factors graded | 0 of 75 |
| Archived cells | 23 → 32 |
| Known-untestable | C4K (contract-year status), all four positions |

**C4K trips the look-ahead guard** at every position — it reads season-N data to build a
season-N feature. The guard was not touched and must not be. This is a real methodology
decision for strategist/fable (a properly-dated preseason proxy, or disposition as untestable),
and it belongs in the founder's "untestable, and why" column rather than being worked around.
Its sibling C4J shares the same family window and does not trip it.

## For the next session

The four-number deliverable is still unanswered — factors tested, factors passed, passes per
position, untestable with reasons. Nothing above changes that; it changes whether the machine
that would answer it is running. Two runs were queued under the old workflow and one was
dispatched under the fixed one.
