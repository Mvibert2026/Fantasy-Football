# Batch CT1 — registration (tier-2, ADR-070): the 40 within-cluster contrasts

**Registered by `ranker`, 2026-08-04, before any CT1 arm is graded.** The founder's observation
that collinearity is itself predictive, made testable: screen 2 constructed a percentile-rank gap
`pr(A) − pr(B)` for every within-position pair with |ρ| ≥ 0.6, and those 40 constructs (78
position-cells — the arm set and cells were **fixed by the screen**, not chosen here) now face the
confirmatory instrument. Code: `experiments/bottomup/v2/factors_c5_ct1.py` (`CT_REGISTRY`, read
from `standalone_screen2_contrasts.csv`).

**Construction** replicates the screen exactly: components built by the SAME gated block functions
the batches use (19 components spanning C1/C2/C3/C4/C5 blocks and base-frame columns),
percentile-ranked within the frame (one season per frame ⇒ within-season), gap = pr(A) − pr(B),
`ct_known` = both components known. One arm = one contrast = one (gap, known) block appended to the
veteran volume specs. **Window per contrast = the later of its two components' families**
(realised spread: T2A 3, T2P 23, T2I 2, T2B 7, T2C 4, T2D 2), matched control at the identical
§4.8 key, raise-enforced.

**Labelling caveat, stated up front:** the harness block constructions carry the batches' own lag
conventions (recency-weighted where the source batch is), which can differ in detail from the
screen's standalone values. The registered object is the **construct** (the rank gap between the
two named signals), not the screen's exact scalar.

**Placebo:** F0CT = `pr(noise₁) − pr(noise₂)` (salts `CT-placebo-0/1`), T2A, 4 cells — the placebo
is shaped like the treatment (a rank-gap column), not a raw noise column.

**`m_b = 82`** (78 contrast cells + 4 placebo). Cumulative campaign M with C3+C4+AB1+C5+CT1
registered: 259 + 25 + 22 + 27 + 27 + 82 = **442**. **L raised to 8,999** (p-floor 2.22 × 10⁻⁴ <
q/M at M ≤ 450); the ADR's rule that resolution is bought with draws, priced and accepted.

**Registered predictions** (calibration prior applied): F0CT 0 INCLUDE / 0 EXCLUDE, ≤1 HYPOTHESIS;
most contrasts NULL — the screen's strong TE depth-rank-vs-usage family
(`CT_depth_end_rank_minus_*` at TE) is the likeliest INCLUDE candidate but TE's S_pos = 7 makes
consistency hard to reach, so HYPOTHESIS is the modal good outcome there; the QB
`depth_first_share`-vs-`inj_unexp_missed_share` contrast (screen ρ 0.71) is the single likeliest
BH-robust cell.

Standing constraints: holdout sealed; targets ≤ 2024; no proxy reads; one arm one change; seeds
sha256.
