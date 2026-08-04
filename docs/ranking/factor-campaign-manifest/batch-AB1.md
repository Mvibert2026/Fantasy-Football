# Batch AB1 — incumbent ablations (no grandfather clause)

**Registered by `ranker`, 2026-08-04, before any AB1 arm is graded.** Founder's ruling
(FR-2026-08-04-v3-build-strategy…): incumbents get no grandfather clause; in the incremental frame
the correct arm for an incumbent is an **ablation**. Code:
`experiments/bottomup/v2/ablations_ab1.py`; the spec lists are read from the instantiated shipped
models at import, never hand-typed.

## What is actually in the model — measured, and it corrects the dispatch's list

The running veteran volume specs carry exactly seven channels: the volume level (each spec's own
lag), share (`tshare_w`/`cshare_w`), games share (`gshare_w`), `evidence`, age (`age`+`age2`),
prior points/game (`ppg_w`), `experience`. **Four "predictive incumbents" named in the dispatch are
NOT in the running model and have no ablation:**

| named incumbent | where it actually is | its test |
|---|---|---|
| depth chart / role | `AVAIL_E` only — an arm that never shipped | additive: C3E (registered, queued) |
| injury designations | `AVAIL_B` only — never shipped | additive: C3C/C3D (registered, queued) |
| air yards / aDOT | accumulated by the feature builder, consumed by **no spec** | additive: C1 F4, C2 A1 (WOPR) — both re-running at tier 2 |
| draft capital | rookie path only (`ROOKIE_COLS`); graded endpoint is board **veterans** | rookie-side registration (`season-span-M4.md` §4, not yet run) |

Reporting any of those four as "incumbent tested by ablation" would be false; the final report
carries this table instead.

## Arms

Observed run = incumbent volume specs with the channel removed from **every** spec of the position;
null draw k = **full incumbent specs with the channel's rows jointly permuted within season**
(ensemble070 `perm_ablate` — under H0 the removal differs from control only by the variance cost of
a noise block, which is what the permuted block is). Both difference against the unmodified
control. Availability specs untouched — that channel has its own campaign (B1/D1/D1-A1).

| arm | channel removed | positions |
|---|---|---|
| ABAGE | `age`, `age2` | QB RB WR TE |
| ABSHARE | `tshare_w`, `cshare_w` | RB WR TE |
| ABGSH | `gshare_w` (volume specs only) | QB RB WR TE |
| ABPPG | `ppg_w` | QB RB WR TE |
| ABEVID | `evidence` | QB RB WR TE |
| ABEXP | `experience` | QB RB WR TE |
| F0AB | **placebo** (additive noise, salt `AB-placebo`) | QB RB WR TE |

All at T2A (base features have no source constraint). The volume **level** channel is deliberately
not ablated: removing a spec's own lag of its target variable is not an incumbent audit, it is
deleting the model.

## Verdict translation — fixed now, before any result exists

The §4.4 taxonomy is written for additions; for a removal arm it reads inverted, and the
translation is fixed here so it cannot be chosen after seeing results:

| §4.4 verdict on the removal | reading for the incumbent |
|---|---|
| BH-robust HARM + CONSISTENT | **VALIDATED** — the channel carries ordering signal |
| BH-robust WIN + CONSISTENT | **REMOVAL CANDIDATE** — the channel costs ordering; escalate to strategist before touching the spec |
| NULL (calibrated) | **NOT EVIDENCED at this power** — a parsimony question for strategist, never an automatic removal |
| FRAGILE / HYPOTHESIS | as the taxonomy says: nothing |

## Endpoint, statistics, m_b

As C3/C4: `rho_points` on `m_panel_ppr12`, matched keys raise-enforced, Besag–Clifford h = 20,
L = 7,999, BH at cumulative campaign M (333 with C3+C4+AB1 registered). **`m_b = 27`** (23
treatment cells + 4 placebo).

## Registered predictions

1. F0AB: 0 INCLUDE / 0 EXCLUDE, ≤1 HYPOTHESIS.
2. ABSHARE and ABGSH are the likeliest VALIDATED (HARM on removal) — share and availability history
   are the model's core opinion carriers.
3. ABEXP and ABEVID are the likeliest REMOVAL CANDIDATES or NULLs — both are near-collinear with
   age and the volume level.
4. At least three of the six channels come back NOT EVIDENCED at TE (S_pos 7, small boards) —
   which is a statement about power, not about the channels.

## Standing constraints

Holdout sealed; targets ≤ 2024; no proxy reads; one arm = one channel; placebo carried; seeds
sha256; nothing enters or leaves the shipped spec without a strategist ruling on the graded output.
