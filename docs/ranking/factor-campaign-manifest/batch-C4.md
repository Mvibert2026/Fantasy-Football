# Batch C4 — registration (tier-2, ADR-070 instrument)

**Registered by `ranker`, 2026-08-04, before any C4 arm is graded.** Candidate definitions:
`backend`, `docs/ranking/batch-C4-candidates.md` + `experiments/bottomup/v2/factors_c4.py`
(2026-08-04, written against the real merged interface). Arm wiring:
`experiments/bottomup/v2/factors_c4_adapter.py`. Interface smoke before this commit: C4M/RB and
the AB1 shakeout — arm set, positions, windows fixed in the adapter before the smoke; nothing
changed after seeing output; no cell graded, no ensemble built.

Binding: ADR-070 in full; ADR-069 (no consensus/ADP/market feature anywhere).

## Arms

| arm | factor | positions | family (window) | columns |
|---|---|---|---|---|
| C4I | target-share stability (persistence, not level) | WR TE | T2A | `tshare_stability_prior`, `tshare_stability_known` |
| C4J | team pace (plays/game) | QB RB WR TE | T2P (ff 2012, targets 2014–2024) | `pace_prior_w`, `pace_known` |
| C4K | contract-year status | QB RB WR TE | T2P | `is_contract_year`, `contract_years_left`, `contract_known` |
| C4L | prior-season coaching disruption (lag-1 HC change) | QB RB WR TE | T2A | `hc_disruption_prior1`, `hc_disruption_known` |
| C4M | O-line YBC/carry | RB | **T2D (ff 2018, targets 2021–2024, S_pos = 4 — labelled)** | `ol_ybc_prior_w`, `ol_ybc_known` |
| C4N | two-WR personnel rate | RB WR TE | **T2C (ff 2017, targets 2019–2024, S_pos = 6)** | `two_wr_rate_prior_w`, `two_wr_known` |
| F0C4 | **placebo** (salt `C4-placebo`) | QB RB WR TE | T2A | `placebo_noise_c4` |

k-controls C4Ik…C4Nk inherit their treatment's family/positions (C1 Amendment 1 discipline; not in
m_b; ensembles run lazily for WIN candidates at p_two ≤ 0.10).

**Carried-forward caveats from backend's definitions, binding on the reader of any C4K result:**
`CONTRACTS_FIRST = 2011` is a density judgment, not a measured breakpoint; the 62% contract-year
smoke rate is flagged and must be re-checked on the graded population before the indicator is
trusted at face value (coverage is reported per cell; the 0.80 floor gates as NO DATA where thin).
C4K's `year_signed ≤ target_season` read is the batch's one same-calendar-year read — a
March–August signing predates Week 1; the source gate still bounds at the sealed holdout.

## Endpoint, statistics, m_b

Identical to batch C3: per-season Spearman on `m_panel_ppr12` board veterans vs matched control at
an identical §4.8 key (raise-enforced), §4.7 snap, tier-3 co-report, Besag–Clifford h = 20,
**L = 7,999** (p-floor 2.5 × 10⁻⁴ — raised from 5,999 because registered M now exceeds 300), BH at
cumulative campaign M, VOID rule as C1 Amendment 1.

**`m_b = 22`** (treatment cells 18 + placebo 4). Cumulative campaign M at grading: 259 + 25 (C3)
+ 22 (C4) + 27 (AB1) = **333**, plus any late-arrival batch registered before it computes.

## Registered predictions (against the standing calibration prior)

1. F0C4: 0 INCLUDE / 0 EXCLUDE, ≤1 HYPOTHESIS. A placebo INCLUDE re-opens ADR-070.
2. C4J (pace) and C4N (personnel) are the likeliest to show anything — both are environment
   channels the specs currently lack entirely; still ≤ even odds either reaches INCLUDE.
3. C4K NULL or VOID — the 62% base-rate anomaly suggests the indicator is diluted by backup-tier
   one-year deals, exactly the population the board excludes.
4. C4M at S_pos = 4 cannot reach BH robustness unless the effect is enormous; expected NULL
   (calibrated) with a wide quoted band — an honest "insufficient span," not evidence of absence.

## Standing constraints

Holdout 2025 sealed; targets ≤ 2024; no week-1-of-target-season roster reads; one arm one change;
placebo carried; seeds sha256.
