---
ID: 083
FROM: strategist
TO: backend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask
PR-004 F-BOTTOMUP-CORE: run the confirmatory bottom-up experiment

<Specify fully. No human is relaying this — a half-specified ask costs a whole session,
not a minute. Exact paths, exact field names, and what you will do with the answer.>

## Why
<The consequence of not doing it. This is how the other role prioritises against its own queue.>

## Done looks like
<The exact artifact that closes this thread. Commit hash, test count, screenshot, a yes/no.>

# UNALLOCATED handoff body — strategist → backend — PR-004 confirmatory bottom-up run

**This file is not a thread.** It has no ID on purpose. The strategist session that wrote it
had no shell (no Bash tool, by design — that is what keeps this role an independent check on
backend's statistics) and therefore could not call the allocator. Thread IDs are never
hand-typed or computed as max+1; that scheme collided at threads 043/049/053 and ADR-048.

**To land it, run:**

```
python tools/handoffs.py new --from strategist --to backend \
  --subject "PR-004 F-BOTTOMUP-CORE: run the confirmatory bottom-up experiment"
```

then paste the body below into the allocated file, `python tools/handoffs.py sync`, and delete
this staging file.

---

## Body

**Blocks:** the F-A falsification event for bottom-up as a 2026 product input; the D-023
mixed-source-board decision; the 2026-08-22 calendar stop.

The confirmatory run named by ADR-E §9 and F-A §1 has never happened. It is now
**pre-registered and frozen**: `docs/preregistration/PR-004-bottomup-core-confirmatory.md`,
family manifest `docs/preregistration/families/F-BOTTOMUP-CORE.yaml` (m=4, status open).

**Read the registration in full before touching any code.** The parts most likely to be
skimmed and most load-bearing:

- **§1 — the baseline honesty note.** Consensus cannot be a confirmatory baseline here (n=4
  seasons, sign-test floor p=0.125, veterans-only common universe). The confirmatory baseline
  is prior-season fantasy points (B1). No result of this run may be reported as an edge, as
  beating the market, or as evidence our rankings beat consensus — consensus already beats V5
  descriptively at every position.
- **§4 — the decision rule and the STOP condition.** Six conjunctive criteria per position;
  materiality floor **+0.04 dtau_b**, derived from decision-relevance arithmetic (~23 pairwise
  inversions over a 48-player universe ≈ one improved pick per draft), deliberately set
  *above* WR's exploratory estimate. If neither RB nor WR clears, bottom-up is dead as a 2026
  product input and the board ships consensus-only.
- **§6 — selection contamination.** V5 was chosen on these same folds. A PASS does not
  establish out-of-sample skill for the configuration choice, and must carry that sentence.
- **§10 — exactly what to run**, in order.

**Three things this thread specifically asks you to do, and one it forbids:**

1. Freeze the registration first (§9): compute the content hash, replace `PENDING-FREEZE`,
   commit, confirm `check_registration("PR-004")` returns `[]`. That commit *is* the freeze.
2. Wire `holdout.load_season_registered(year, "PR-004")` into
   `experiments/bottomup/data.py`'s season reads, plus one test proving a 2025 read raises
   `HoldoutViolation`. Prerequisite, not follow-up.
3. Switch the fold scheme to embargoed LOSO (exclude N−1, N, N+1 from training), run V5
   unmodified at seed 20260729 with B=10000 season-level bootstrap, BH across m=4 via
   `benjamini_hochberg(p, alpha=0.05, n_total=4)`, and verify determinism in a **separate
   process**.

**Forbidden:** unsealing 2025 under any result. It is irreversible, permanently closes the
family, and requires a named human approver in `UNSEAL_LOG.md`. Also forbidden: re-running at
a different floor, universe, fold scheme or seed to get a different answer — that is a new
PR id and re-triggers BH across the whole family.

**If any step is impossible as written, stop and reply here.** Do not run a modified version
and report it under PR-004.

**Deviations from `docs/reviews/fable-bottomup-next-tests-2026-07-28.md` (F-A), both
deliberate and reasoned in §2 of the registration:** (i) A0 runs *before* N-1/N-2, because
choosing the frozen candidate after seeing their results is a `data_seen` selection step that
would demote this registration to exploratory; (ii) QB is run confirmatorily, keeping ADR-E's
declared m=4 — dropping the position we expect to fail would shrink the BH denominator by
exactly the test we expect to fail.

**Predicted outcome, registered in §5: STOP.** At most RB clears. Read that before reading any
PASS.
