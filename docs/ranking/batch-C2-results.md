# Batch C2 results — more factors, plus the RB high-carry breakpoint, against v2

**Conclusion first. Live document, updated as each arm completes — not written at the end.**

> ## GRADING IS SUSPENDED. This batch builds, runs, and records — it does not include or exclude
> ## anything.
>
> C1 found that its registered inclusion rule hands a BH-robust `INCLUDE` to seeded noise that
> provably cannot carry signal (false-positive rate measured at 9.6% of cells against a nominal
> 2.5%). `strategist` owns the replacement rule
> (`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`, BLOCKED-ON-YOU).
> Every cell below carries a CI-level verdict (WIN/HARM/NULL, estimator-independent) and a
> comparison against this batch's own placebo, but the factor-level status is fixed at
> **`PENDING-RULE`** for all of them. Re-grading once the replacement rule lands needs no refit —
> `python3 -m experiments.bottomup.v2.run_c2 --regrade`.

Registration: `docs/ranking/factor-campaign-manifest/batch-C2.md`, committed at `ee87b53` before
any arm was fitted. m_b = 29 (20 Part A + 1 Part B + 8 placebo). Control: v2 games arm G0, pinned
(unchanged from C1).

---

## NEXT STEP

*Rewritten on every update. Written for a successor with none of this context.*

**All arms complete as of this write-up** (see the run log below). Nothing is outstanding except
what other roles own:

1. **`strategist` ruling on C1's WIN criterion** — same blocking thread as C1. No factor in this
   batch may be graded INCLUDE/EXCLUDE until it lands. This batch's NULLs (where CI-level NULL) do
   not depend on the rule; a CI-level WIN does, and is reported as PENDING-RULE, not as a finding.
2. **To re-grade after the rule change, with no refits:**
   ```
   python3 -m experiments.bottomup.v2.run_c2 --regrade
   ```
3. **State on disk after every arm:** `experiments/bottomup/results/factor_c2_cells.csv` (per
   position-season) and `factor_c2_contrasts.csv` (CI-graded, placebo-compared, BH not computed).

---

## Run log

| arm | status | commit |
|---|---|---|
| F0 (placebo, CTRL-A2) | done — reproduces C1's CTRL-A numbers byte-for-byte | `6dab690` |

*(rows appended as each arm completes)*

---

## Results table

<!--C2-TABLE-START-->
*(filled in as arms complete — see `experiments/bottomup/results/factor_c2_contrasts.csv` for the
authoritative, machine-generated numbers)*
<!--C2-TABLE-END-->
