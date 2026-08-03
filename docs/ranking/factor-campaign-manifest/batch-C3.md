# Batch C3 — registration (tier-2, ADR-070 instrument)

**Registered by `ranker`, 2026-08-03, before any C3 arm is graded.** Candidate definitions:
`backend`, `docs/ranking/batch-C3-candidates.md` + `experiments/bottomup/v2/factors_c3.py`
(2026-08-02). Reconciliation to the real v2 arm interface:
`experiments/bottomup/v2/factors_c3_adapter.py` — backend wrote against a reconstructed interface
from a worktree that predated `factors_c1.py`/`factors_c2.py`; the adapter maps its `attach_*`
builders into the C1/C2 block convention without rewriting its loaders.

**Honesty note on ordering.** An interface smoke (C3H/TE, C3G/QB, F0C3/QB observed runs plus one
permutation draw) executed before this file was committed, to verify the adapter plumbing. The arm
set, positions, windows and endpoint below were fixed in the adapter **before** that smoke ran, and
nothing was changed after seeing its output. No cell had been graded, no ensemble built, no verdict
computed.

Binding: ADR-070 in full (permutation ensembles §4.1, Besag–Clifford §4.3, verdicts §4.4 incl.
CONSISTENCY §4.4a and the RE-SPECIFY/EXCLUDE split §4.4b, BH at cumulative campaign M §4.5,
provenance keys §4.8). ADR-069: no consensus/ADP/market column is a feature or ordering input
anywhere in this batch.

## Arms

| arm | factor | positions | family (window) | columns | control |
|---|---|---|---|---|---|
| C3C | injury report-week burden | QB RB WR TE | T2I (ff 2013, targets 2015–2024) | `injury_burden_prior_w`, `injury_known` | C3Ck |
| C3D | practice-participation severity | QB RB WR TE | T2I | `practice_severity_prior_w`, `practice_known` | C3Dk |
| C3E | end-of-prior-season depth-chart rank | RB WR TE | T2A (ff 2002/2012, targets 2013/2014–2024) | `depth_end_rank_prior1`, `depth_end_known` | C3Ek |
| C3F | combine athletic composite (veteran spec only) | RB WR TE | T2A | `combine_z`, `combine_known` | C3Fk |
| C3G | neutral-situation team pass rate | QB RB WR TE | T2P (ff 2012, targets 2014–2024) | `neutral_pass_rate_prior_w`, `neutral_pass_known` | C3Gk |
| C3H | efficiency-over-expected rate | RB WR TE | T2P | `yoe_rate_prior_w`, `yoe_known` | C3Hk |
| F0C3 | **placebo** (seeded N(0,1), salt `C3-placebo`) | QB RB WR TE | T2A | `placebo_noise_c3` | — |

Position restrictions, with reasons stated now: **C3E/C3F/C3H exclude QB** — QB1 designation is
near-redundant with attempts volume already in the spec; the QB modelling channel was closed after
six failed configurations; and `ff_opportunity` efficiency at QB re-enters that channel. **C3C/C3D
run at T2I** (ff 2013) rather than the deep window: injuries coverage starts 2010, and nine
known-zero training years at QB/RB is the coverage-flag time-dummy geometry batch 7's D2 measured —
a clean matched window is cheaper than arguing with the artifact afterwards. **C3G/C3H at T2P**
(ff 2012) for the same reason (pbp 2009+, ff_opportunity usable span).

**Not in this batch:** odds factors (T0-11/N12 tension backend flagged — strategist's call, not
resurrected here); snap share (already C1's F1); draft capital (already a built feature).

## Endpoint, universe, statistics

Per-season Spearman `rho(proj_points, points)` on **`m_panel_ppr12`** board veterans, arm minus its
matched control at an **identical** §4.8 key (enforced by raise), §4.7 derived snap,
`rho_points_fullvet` co-reported on every cell. Besag–Clifford h = 20, L = 5,999
(p-floor 3.33 × 10⁻⁴), BH at cumulative campaign M. VOID rule: a treatment WIN is void where its
paired k-arm has p_win ≤ 0.05 (loose bar to void, BH bar to claim); k-arm ensembles run lazily for
WIN candidates (treatment p_two ≤ 0.10).

**Known population fact, measured 2026-08-03 before any grading:** the ppr12 archive is shallow
before ~2017 (TE has ≥10 board veterans only from 2018; RB from 2016; QB from 2015; WR from 2014),
so realised `S_pos` at the ≥10-player floor is QB 10 / RB 9 / WR 11 / **TE 7**. Cells below the
floor do not exist; `S_pos` is published per cell. This is reported to `strategist` as a finding
about the tier ruling (TE gains nothing from tier 2), not silently absorbed.

## Multiplicity

`m_b = 25` (treatment cells 21 + placebo cells 4; k-controls excluded, the C1 convention).
Campaign M at C3 grading: **259 + 25 = 284** (130 through C1 + 29 C2 + 88 D1 + 12 D1-A1 — C2's
registered 29 restored to the denominator; discrepancy flagged to strategist in the M-1..M-6 thread
reply). L = 5,999 covers M ≤ 300.

## Registered predictions (priced against the standing calibration prior)

1. F0C3: 0 INCLUDE / 0 EXCLUDE, ≤1 HYPOTHESIS across its 4 cells. **A placebo INCLUDE re-opens
   ADR-070**, as F0 re-opened its predecessor.
2. Most treatment cells NULL (calibrated). The likeliest non-null: C3E (depth-end rank) at RB — a
   genuine role snapshot lag features dilute — and C3C at RB/WR in the HARM direction if injury
   burden proxies age/wear already carried by `age`/`gshare` (mis-specification, would be
   RE-SPECIFY material, not EXCLUDE).
3. C3F (combine, veteran spec) NULL everywhere — athletic ceiling is priced into veteran volume
   history by year 3.
4. No cell at TE reaches INCLUDE at S_pos = 7 (§4.4a's consistency q95 saturates) — the same
   structural limit ADR-070 predicted for QB at S = 7.

## Standing constraints

Holdout 2025 sealed (panel gates); targets end 2024; no week-1-of-target-season roster reads
(`allow_preseason_proxy=False` on every run, asserted); one arm one change; seeds sha256, recorded.
