# Fable mandate M2 — availability, the recommender, and whether this week's evidence holds

Written 2026-07-31 for a run at the start of the week beginning 2026-08-03.
**Supersedes `docs/fable-mandate-M-2026-07-29.md`**, which was written before anything in it was
measured and had accreted to 34 asks across three dates. Read that file only for its founder-framing
section, reproduced below.

---

## Rules

**Conclusion first.** Read the repo freely, run read-only queries, run existing tests.
**Modify nothing** except your own output document and a session-log entry.

**The sealed 2025 holdout does not open.** Founder's ruling, 2026-07-31, now `CLAUDE.md` §6.3: it is
gated on *you*. If your review concludes something warrants spending it, say so and stop — the
decision is the founder's. Every access is logged in `docs/preregistration/holdout_access_log.jsonl`.

**You have standing authority to block** (`CLAUDE.md` §8). Use it. Nothing in here has been through
adversarial review, and a week of work is queued behind you.

---

## The founder's framing — unchanged, and it outranks the rest of this file

> "If I don't have those three things in place, I don't want to use the tool for my real draft."

1. The best **bottom-up rankings**
2. The best **availability prediction**
3. The best **suggested-pick model** — his roster, opponents' rosters, availability, live

**These are this-season questions.** A previous PM framed them as off-season design work and was
overruled in his own words: *"NO, they are this season questions... just stop worrying about time
honestly."* Do not re-frame them.

**They are not a strict chain** (his correction, 2026-07-31). Availability predicts *drafter
behaviour*, so it runs on ADP and consensus — what drafters actually use — not on our board. The
recommender takes a ranking as a **parameter**, not a prerequisite. Only the recommender's *value*
term depends on ranking quality.

---

## What is different from the last mandate

The last one asked you to help *design* three models. Since then all three have been measured, so
**this one asks you to attack concrete claims with numbers attached.** The full evidence index is at
the end.

**Headline facts, all measured 2026-07-30/31:**

- A ranking version (`v1`) was assembled and tested end to end for the first time. **It loses to both
  crowds** — significantly to expert consensus at QB, RB and WR — while **beating prior-season points
  and a tier heuristic decisively at RB and WR.**
- **~90 registered factor tests across five batches. Zero edges.**
- **Consensus measured as a stable benchmark**: zero poor seasons at any position under either crowd.
- The shipped board's **within-position ordering is identical to consensus**; its whole deviation is
  cross-positional.

---

## Your primary targets — the founder's call, 2026-07-31

> "Maybe it's best use is availability and recommendations."

He is right, and the reason is that **rankings have been measured to death this week while these two
have barely been measured at all — and both are about to be built.** Adversarial review is worth most
before the build, not after.

### M2-1 · Availability

**What it does today.** `simulate_availability` runs a Monte Carlo where opponents draft to a ranking
perturbed by Gaussian noise. It uses **one global sigma for every player**, offered at 5/10/20, and
the code's own metadata admits it: *"a guess, not fitted to observed drafts."* It reads
`fantasypros_ecr` for **both** the opponent model **and the user's own best-available pick**
(`src/draft_sim.py:120`), and the two live ranking sources disagree on **73 of the top 80 players**.

**What was ruled and what was measured, and they point different ways:**

- Strategist ruled the central tendency should switch to **ADP on estimand grounds** — ADP measures
  the quantity in picks with an uncertainty; consensus measures opinion, ordinally, with none.
- **H1 measured NULL.** ADP is *not* more accurate at predicting realised pick order: it beat ECR in
  1 of 3 logged mocks, mean gap **−1.27 picks in ECR's favour.**
- **M0 failed.** FFC's `times_drafted` sums to **6.4%** of the player-slots its own API metadata
  implies (12,009 against 188,100), and Ja'Marr Chase's count *fell* while the total rose. The
  per-player dispersion half has no measured foundation.

**Attack:** is adopting a source on estimand grounds while the accuracy test says it is no better a
principled decision or a rationalised one? And is the founder's own decomposition — *ADP, then how the
draft has fallen, then opponents' needs* — the right factorisation, or does the closed-form result
(with ADP plus dispersion the unconditional marginal is nearly closed-form) mean the simulator is
mostly theatre outside live draft state?

### M2-2 · The recommender

**This is the weakest thing in the product and the founder has caught it failing twice by eye.**

The ordering function is `vbd + unfilled_need(+8) + tier1_te(+18) + early_qb_penalty(−25)`, and:

- **There is no availability term at all.** Not mis-signed — absent. Survival probability is computed
  *after* the order is fixed, purely to write display text.
- **All three constants are hardcoded and were never fitted to anything.** PR-007 predicted the −25
  should be deleted as redundant with VBD — and the measurement shows VBD does the **opposite** at the
  top of the position, *inflating* elite QBs by ~20 places. So the prediction rests on a false premise.
- **The board and the simulation contradict each other.** The board puts Josh Allen at overall **6** —
  round 1. `PR-003` measured early-QB as the **single most costly strategy tested**: negative in 12 of
  12 cells, point estimate −115.4 at σ=10, CI [−176.3, −54.4], simulated from **slot 3 of a 10-team
  snake — the founder's exact seat.** Nothing reconciles them.

**Attack:** specify what the ordering rule should be, and say whether the two measured findings can
both be right — or whether VBD and the draft simulation are answering different questions and one of
them is being read as something it is not.

---

## Secondary — the campaign's own integrity

Only if the primary targets do not consume the session. **Ranked by how much a false positive here
would cost.**

### M2-3 · Did the campaign-level correction actually happen?

Five factor batches ran **concurrently** on 2026-07-30/31, each instructed to register into one shared
manifest (`docs/ranking/factor-campaign-manifest/`) rather than correct within itself. **Verify it.**
If each corrected locally, every individual correction is defensible and the campaign is not — ~25
arms in flight and a false positive arriving exactly on schedule while looking real.

Known wobble: batch 6 built a *second* manifest and graded at m=47 before finding batch 5's and
re-grading at 80. It caught itself. **Check whether anything else did not.**

### M2-4 · Are the nulls findings, or symptoms?

~90 tests, zero edges, is what an honest campaign looks like. It is **also** what an underpowered
harness looks like. `src/backtest.py` had a defect found the same week that scored a drafted player
who never took a snap as **replacement level** rather than a disaster — systematically
under-penalising injury risk, the channel the oracle work calls largest.

Related and unresolved: **three separate coverage-flag artifacts with three different explanations**,
the last contradicting the first. Batch 5 concluded "coverage artifact"; batch 7 found a flag whose
source starts inside the training window is really a **time dummy**; batch 5's flag is the same source
and geometry. That is registered as a claim and **no batch-5 document was edited.** Rule on it.

### M2-5 · The suspiciously clean result

**Zero poor consensus seasons, at any position, under either crowd.** It contradicted the strategist's
own pre-registered prediction of the opposite — which is evidence of honest process, and also exactly
what a mis-specified decision rule produces. The two crowds were measured on **different windows**:
market ADP 2018–2024 (7 seasons), expert consensus 2021–2024 (4). Not comparable head to head, and
reported that way.

---

## What PM believes, so you can attack it rather than inherit it

**Each of these is mine. Several are convenient. One I have already been wrong about twice.**

1. **"The external factor well is dry."** 90 tests, zero edges, and every published factor is by
   construction inside consensus because consensus is made of the people who published it. This is
   *very* convenient for a PM whose campaign produced nothing. It is also unfalsifiable in the
   direction that ends the project — strategist named this **"the efficient-market lullaby"** and said
   it is currently indistinguishable from *"we have not built a model yet."*
2. **"Parity before edge."** The founder's framing, 2026-07-31: v1 loses to consensus because
   consensus *knows things v1 was never told*, not because it has a subtle edge — and the pattern (beats
   naive baselines, loses to the informed one) fits. **Attack whether that is the real explanation or a
   comfortable one**, because it converts a week of nulls into "we were measuring the wrong thing,"
   which is the most flattering possible reading.
3. **"The tests measured our model, not consensus."** Strategist established that `E1b`/`E2` compare an
   arm against the batch's own primary model; consensus never appears. I had told the founder the
   opposite. **Check whether the corrected reading is now being over-applied.**
4. **Things I stated to the founder that review overturned within a day:** the 12-of-12 zeros as proof
   the metric was blind (one algebraic identity printed twelve times); four arms reported as
   consensus-suppressed improvements when two were measured degradations; Fable as free capacity,
   twice. **Assume more of what I have said is wrong and find it.**

---

## Deliverable

One document. Conclusion first. For each finding: what is claimed, what the evidence actually
supports, and what would falsify your objection.

**Say plainly which of the founder's three questions is not reachable by 7 September** — that is
different from being hard, and the last mandate asked for the same distinction. He has 38 days and
would rather be told now.

---

## The audit trail — every artifact, so you do not have to go looking

| Artifact | What it is |
|---|---|
| `docs/factor-ledger.md` | Every factor considered with disposition and reason — 95 rows. **The multiple-comparisons denominator, written down** |
| `docs/preregistration/*.md` | 9 pre-registrations, thresholds fixed before measurement |
| `docs/ranking/factor-batch-{2,3,5,6,7}-precommit.md` / `-results.md` | Per-batch, dated, amendments dated separately |
| `docs/ranking/factor-campaign-manifest/` | Sharded campaign manifest — where the campaign `M` lives |
| `docs/preregistration/test_run_log.jsonl` | Which registered tests actually ran — 63 entries |
| `docs/preregistration/holdout_access_log.jsonl` | **Every touch of the sealed 2025 season** — 19 entries |
| `docs/ranking/ranking-v1-{precommit,results}.md` | The first assembled ranking version and its four-baseline test |
| `docs/ranking/fr136-q1-bottom-up-assessment.md` | Where question 1 stands, measured |
| `docs/adr-drafts/ADR-DRAFT-edge-vs-absolute-quality.md` | Strategist's four rulings on what the metrics measure |
| `docs/research/analyst-factor-sweep-2026-07-30.md` | 11 shops, 34 candidate factors, provenance-tagged |
| `experiments/bottomup/results/*.csv` | Raw per-arm output — 29 files |
| `experiments/bottomup/**/run_*.py`, `head_to_head.py` | Reproduction scripts — re-run any result rather than trusting a write-up |

**Known-unresolved, so you do not spend time rediscovering it:** `PR-` ids still have no allocator
after three sessions raised it, so a pre-registration's identity is mutable. The metric rename
strategist ordered (`E1a→C1` etc.) has not been applied anywhere. Threads 109–111 carry literal
merge-conflict markers from an old ID collision.
