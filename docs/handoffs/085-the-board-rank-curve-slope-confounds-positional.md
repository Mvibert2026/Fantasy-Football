---
ID: 085
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask

Two things, in order.

**1. Rule on a diagnosis that contradicts a recommendation already in the repo.**

`docs/ideas-inbox.md:229` (backend, ADR-057) records: the QB rank->points slope ran
-67, -73, -59, -45, **-4** across 2021-2025, calls it "a monotone collapse", attributes the
shipped board's QB premium to flat pooling over it, and asks for a **recency-weighting
experiment**. My agent brief repeats this as a live defect to fix.

Measured this session, exploratory, look-ahead-clean, 2025 never read
(`docs/ranking/bottom-up-research-pass-1.md` §4.2):

- `make_board.fit_rank_curves` fits `points ~ a + b*ln(consensus positional rank)`. That single
  regression confounds **two** quantities: the *shape of the positional value distribution*,
  and *how well consensus orders that position that year*.
- Fit instead on **realised** positional finish rank (available 1999-2024, no consensus needed):
  the QB value curve did **not** collapse. Era means: 1999-2007 **-57.7**, 2008-2015 **-59.0**,
  2016-2020 **-56.8**, 2021-2024 **-72.9**. QB top-3 VBD over a QB10 replacement is at an era
  **high** (102.2 vs a long-run 79-90).
- Over the four overlapping seasons the two fits move in **opposite directions** at QB:
  consensus-fit slope -66.6 / -72.6 / -58.6 / -45.0 against realised-fit slope
  -72.8 / -83.2 / -60.1 / -75.6.
- The consensus fit's R^2 is 0.15-0.41 (this is the documented `curve_caveat` "R^2 0.16-0.27").
  The realised fit's R^2 is **0.91-0.98**. The log-rank functional form is not the problem;
  the noise in consensus rank is.
- Within-position consensus ordering skill at QB declined over the same window
  (tau_b consensus-vs-finish: 0.484, 0.305, 0.263, 0.263). TE shows the same pattern
  (0.305, 0.263, 0.326, 0.200) and its fitted consensus slope flattened the same way
  (-42.7, -40.7, -26.4, -25.4) against a flat realised slope. **RB and WR do not.**

So the fitted-slope movement is at least partly, and possibly mostly, *declining consensus
informativeness at QB and TE*, not a change in positional value. If that is right, then
**recency-weighting the pooled consensus curve makes the board track market noise faster**,
which is the opposite of the intent.

I am not ruling on this — that is your call, not mine, and I am aware I am arguing against a
finding produced by another agent. Note the one caveat that cuts against me: fitting points on
*realised* finish rank is an order-statistic fit, so it is mechanically steeper than any fit on
an imperfect ordering. The ratio being < 1 is guaranteed. What is **not** guaranteed, and is
the load-bearing evidence, is that the two series move in opposite directions at QB while the
realised value spread reaches an era high.

**2. Register the next experiment, or tell me it is the wrong one.**

Proposed, and deliberately not run: **decompose the board's rank curve into
(i) a value-spread curve fitted on realised positional finish over many seasons and
(ii) a consensus-rank -> finish-rank mapping fitted on the four usable consensus seasons**,
then compare the resulting board against the current single-regression board. Decision rule,
stopping condition and the recency-weighting question all belong in your registration, not
mine. Everything in this session is exploratory and I make no claim it survives.

## Why

The QB premium on the live board is the most visible ranking output the founder sees, and the
currently-recorded explanation for it points at a fix I believe would make it worse. If
recency weighting gets built on the existing diagnosis, it gets built against the wrong
mechanism and the failure will not be obvious — the board will still produce a number.

## Done looks like

(a) A ruling on the diagnosis: confounded as described, or not, with reasoning. If confounded,
`docs/ideas-inbox.md:229` and ADR-057 need correcting and that is a librarian/backend follow-up
I will not do unilaterally. (b) Either a pre-registration for the decomposition experiment with
its stopping condition committed in advance, or a statement that a different experiment should
come first. I will not run a confirmatory test on any of this without one.
