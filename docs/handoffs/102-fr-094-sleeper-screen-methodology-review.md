---
ID: 102
FROM: backend
TO: strategist
STATUS: OPEN
BLOCKS:
OPENED: 2026-07-30
---

## Ask
Methodology review of `docs/analysis/sleeper-screen-2026-07-30.md` (FR-094, "can we predict
late-round sleepers"), script `analysis/sleeper_screen.py`, raw output
`data/qa/sleeper-screen-2026-07-30.json`. This was a Sonnet/default-tier session doing
statistical-methodology work that `docs/operating-model.md` says belongs at Opus/high-effort —
flagged rather than stopping to ask, per this session's own operating rules. Please re-derive or
spot-check the key numbers, not just read the prose.

Specifically:
1. **Step 1 base rate** — round-10+ (12-team FFC ADP, rank ≥109) universe, `actual_vbd > 0` as
   the hit definition (this league's own ADR-029 replacement levels). Train (2018–2023) 24.1%
   [19.1%, 30.0%] Wilson, holdout (2024) 24.5% [14.6%, 38.1%]. Check the cutoff-round
   justification (§1.2 of the doc — round 10+ chosen because round-9+ is already shown to carry
   a strong positive residual in the sibling ADP-vs-production analysis) holds up, and that the
   train/holdout stability isn't an artifact of the (thin, documented) universe sizes — 2022 in
   particular has only 9 qualifying train rows.
2. **Step 2 features** — three pre-registered (AGE_YOUNG, EFFICIENT_LOW_VOLUME, RISING_SHARE),
   season-clustered permutation test, BH-corrected across the three. None reach significance
   (raw p 0.209 / 0.643 / 0.266). Check the permutation/clustering implementation
   (`permutation_test_binary` in the script) is sound, and that the RISING_SHARE holdout
   inversion (0/6 hits vs. 24.5% base) is being read correctly as disconfirmation rather than
   just "not yet proven."
3. **Whether AGE_YOUNG is worth carrying forward as a hypothesis** — it's the one feature whose
   direction held in holdout (37.5% vs 24.5% base, n=8) and is independently evidenced at
   MODERATE-HIGH confidence on the full board in the sibling ADP-vs-production analysis. The
   doc's verdict is "underpowered, not disproven, worth a pre-registered re-test once more FFC
   ADP history accrues." Sanity-check that framing isn't post-hoc rationalization of a
   non-significant result (guardrails §3.4's specific warning).

## Why
Nothing here should reach a ranking-model change or a shipped UI flag without a second read —
this is exactly the kind of small-n, multiple-feature screen `docs/statistical-guardrails.md` §0
calls close to worst-case for spurious findings, and the doc's own verdict is that nothing
tested this pass should ship. Confirming (or correcting) that verdict is the point of this
thread, not rubber-stamping it.

## Done looks like
A reply here stating agreement/disagreement with the doc's verdict, any errors found in the
permutation test or Wilson interval implementation, and an explicit call on whether AGE_YOUNG is
worth a follow-up pre-registered pass once more FFC ADP seasons are backfilled.
