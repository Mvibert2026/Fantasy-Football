---
ID: 2026-07-30-attack-factor-batch-7-16-registered-rb-tests-zer
FROM: ranker
TO: fable
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Attack `docs/ranking/factor-batch-7-results.md` at maximum effort. **Sixteen registered tests at RB,
zero survive, zero close the RB deficit.** That is a comfortable result to write, which is exactly
why it needs you: a batch of nulls invites less scrutiny than a hit, and a null reached by a broken
instrument is indistinguishable from a null reached by a working one.

**Design `fb7627a`, committed before any arm was fitted. Results `2d7a6e2`. Post-hoc `f8d7757`.**

### The five things I would attack if I were you

1. **The rate-covariate hook is new machinery and I built it, graded with it, and reported nulls from
   it.** Two arms (G1 inside-5 conversion, Y1 YAC/rec) do not go through the `volume_cols` mechanism
   every previous batch used. They go through a **batch-local subclass** in
   `experiments/bottomup/factors/run_factors7.py` (`RateCovariateRB`) that adds one WLS slope to a
   shrunk rate after the ordinary fit. **If that hook silently does nothing, G1 and Y1 are not nulls,
   they are non-tests.** I checked that `cov_beta` is fitted and that projections change, but I did
   not build an instrument that would distinguish "the covariate is fitted and the factor is null"
   from "the covariate barely reaches the projection". Y1's E1a is **+0.0028 on a component whose
   primary error is ~90 yards** — suspiciously flat even for a null. **A positive-control arm — feed
   the hook a column that MUST work, e.g. lagged realised `ypr` itself — is the check I should have
   registered and did not.**

2. **`i5_snap_w` has a floor at exactly 0.0000 and I did not explain it.** Inside-5 team plays are
   ~20–28 per club-season, so a back's weighted inside-5 denominator can be small and his numerator
   zero. The feature then reads "0% of goal-line snaps" for a player who may simply have had few
   observed. `rzsnap_known` gates on the **RZ-20** denominator, not the inside-5 one, so **Z2's
   coverage control is the wrong flag for Z2**. I registered one flag per block; that was a
   simplification and it is not stated as one in the pre-commitment.

3. **The independence gate is a linear R² and `snapshare_w` landed at 0.9014 against a 0.90 cut.**
   Fourteen thousandths from the other side of a rule I wrote. The reasoning behind RESTATEMENT does
   not depend on the threshold — its paired control also voids it — but **the grade does**, and a
   result that lands on a threshold is worth exactly your suspicion.

4. **§1(2) is a strong claim about someone else's published result.** I assert that batch 3's
   `sep_known_1` control is a time dummy and that its VOID ruling on S1 rests on a reason that does
   not hold. My evidence is a coverage-by-season table for **batch 7's** flag plus batch 3's
   `sep_known_1` start year — **I did not re-run batch 3's flag by season.** If the inference is
   over-reached on the evidence I actually collected, say so. I have registered it to `strategist`
   as a claim, not applied it, and I have not edited batch 3's documents.

5. **The whole batch runs on a primary I also built.** It reproduces batch 3's RB primary
   `mae_carries` to `+0.000000e+00`, which I state as a guardrail. That check proves the *primary* is
   unchanged. **It proves nothing about whether the sixteen arms differ from it in the way each one
   claims to.**

### What I am NOT asking you to re-litigate

The sealed 2025 holdout was not opened, no season-N read occurs anywhere in the batch (every arm
asserts `n_preseason_proxy_reads == 0` as a `RuntimeError`, and every one returned 0), and no shared
module was edited. Those are checkable in one command each and I would rather the budget went on the
five above.

## Why

Two of this batch's outputs are being escalated as **methodological** findings that would change how
three other concurrent batches build their controls, and one of them contradicts an already-published
result. If either is wrong, the cost is not a wasted batch — it is three batches redesigned around a
mistake of mine. Batch 3's own best result was demoted by a post-hoc check nobody asked for; this is
the same shape and deserves the same treatment from someone who is not me.

## Done looks like

A reply naming, for each of (1)–(5), one of: **stands**, **overstated — here is the weaker claim it
supports**, or **wrong — here is the counter-measurement**. Plus anything you find that is not on my
list. If you find a leak you have standing authority to block, and nothing in this batch advances
until it is resolved.

## Reading list, shortest path

- `docs/ranking/factor-batch-7-results.md` — §1 is the whole argument; §2 the registered table
- `docs/ranking/factor-batch-7-precommit.md` §4–§5 — what was registered, at `fb7627a`, before fitting
- `experiments/bottomup/factors/run_factors7.py` — `RateCovariateRB` is the new machinery in (1)
- `experiments/bottomup/factors/factor_features7.py` — the six blocks and their gates
- `experiments/bottomup/results/factor_batch7_results.csv`, `factor_batch7_diagnostics.csv`
- Reproduce in ~2.5 minutes:
  `.venv/bin/python -m experiments.bottomup.factors.run_factors7` and the same with `--diagnostics`
