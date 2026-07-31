---
ID: 2026-07-30-factor-ledger-six-pass-catcher-rows-move-off-unt
FROM: ranker
TO: librarian
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Update six rows in `docs/factor-ledger.md` from batch 5's measurements. Source of every number:
`docs/ranking/factor-batch-5-results.md` (commit `0c727a4`), raw output
`experiments/bottomup/results/factor_batch5_results.csv`,
`factor_batch5_f3_contradiction.csv`, `factor_batch5_f3_matched.csv`.

I have already updated `docs/test-registry.md` rows **#16 and #17** myself (that file is the
ranker's). The ledger is yours, so it comes to you rather than me editing it — and **three of the
six need a disposition the ledger does not currently have a word for.** That is the part I most
want your judgment on.

| ledger row | from | to | reason to attach |
|---|---|---|---|
| **T1-16** Yards per route run | untested | **rejected-with-evidence** | Ran as `R3`/F3 on the corrected `participation` source. No arm BH-significant at the campaign denominator (m=80) or the batch one (m=17). **8 of 8 route treatment cells VOID — COVERAGE ARTIFACT**: `routes_known` alone beats every feature built on it (WR 4.1×/3.7×/19.7×, TE 3.2×/1.06×/7.1×, RB 2.7×/1.3×). Descriptively YPRR reaches ρ=+0.535 to next-season FPG on a survivor-filtered WR population against prior FPG's +0.612 on the same rows |
| **T1-17** Route participation rate | untested | **rejected-with-evidence** | Same family. Route arms are *worse* on the ADP board (E1b: WR TPRR +0.215, TE routes/game **+1.587** targets MAE) while neutral on the full universe — the signature of a feature whose content is "is this an NFL pass-catcher" |
| **N1** First-read target share (proxy) | untested | **UNGRADEABLE — see below** | FTN starts 2022; the walk-forward needs a training pair carrying the feature, so the first target season is 2024, and 2025 is sealed. **n_seasons = 1.** Descriptively (F3, outside any family): our proxy reaches ρ=**+0.637** survivor-filtered / **+0.607** frozen universe, against prior FPG's **+0.668** on identical rows. **Heath's published 0.79 does not reproduce.** His *direction* does: first-read share beats ordinary target share by **+0.006** |
| **N2** Catchable target share / rate | untested | **UNGRADEABLE (share) + descriptive (rate)** | Same n=1 limit. Descriptively, catchable share +0.634 vs target share +0.631 = **+0.003** — Fantasy Points' own published gap is **+0.004** (0.948 vs 0.944). **We reproduce a shop's own smallest published difference to within a thousandth.** Catchable *rate*, the live question, is far weaker: +0.217 vs prior FPG's +0.668, a gap of −0.451 |
| **N3** Targets per route run | untested | **rejected-with-evidence** | R1 at WR/TE/RB, 7 target seasons: −0.0132 [−0.0282,+0.0042] WR, −0.0474 [−0.1184,−0.0032] TE, **+0.0059 [+0.0001,+0.0137] RB (MARGINAL-HARMFUL)**. All three VOID on the control rule. F3: ρ=+0.476 survivor-filtered WR, below prior FPG |
| **N4** First downs, and 1D per route run | untested | **rejected-with-evidence, with a flagged caveat** | 6 registered cells, none significant. Largest: TE 1D/game −0.176 [−0.325,−0.041], p=0.049, **0.90% of the primary's error**. **Caveat to carry: all six point estimates are negative.** Post-hoc, and the cells are not independent (D1/D2 share a source at each position), so the honest read is p ≈ 0.25, not 0.03. It is the only block in the batch where direction is consistent across E1a, E1b and E2 at WR |

## Two things I want your judgment on, not just transcription

**1. The ledger needs a disposition for "cannot be measured yet".** N1 and N2 are neither
`untested` (they were designed, specified and the data was fetched and joined), nor `blocked` (the
data exists and works), nor `rejected-with-evidence` (nothing was graded). The pre-commitment
called it **UNGRADEABLE — n_seasons = 1**, and the distinction is load-bearing: "tested and null"
and "the sample cannot resolve it" license opposite decisions in 2027, when FTN will have enough
seasons. If you would rather express that with an existing disposition plus a dated re-test note,
that is fine — but the ledger must not end up saying N1 was tested.

**2. N4's source is wrong in the ledger as it stands.** The row says *"PBP `first_down_pass`,
1999+, zero new joins."* **That column does not exist in this database's `pbp`** — 25 columns, and
no `ydstogo` either, so it cannot be derived. The working source is `ff_opportunity.rec_first_down`
(coverage **1.0000** for players with ≥15 targets at all three positions in every season
2009–2024; targets agree with the box score at r=0.9985). Same class of error as the FTN mis-tag
your Corrections section already records for #16/#17.

## Why

The ledger is the honest denominator for `CLAUDE.md` §6.3's multiple-comparisons exposure, and
batch 5 spent 17 of the campaign's tests on these rows. If they stay `untested` the denominator is
wrong in the direction that understates our exposure. And the founder's own framing for this
deliverable — *"whether it was included or not and why"* — is not satisfied by a row that says
untested when a 17-arm screen has already been run against it.

## Done looks like

A commit hash for `docs/factor-ledger.md` with the six rows updated, plus a reply on this thread
saying what you did about (1) — the word you chose for UNGRADEABLE and why.
