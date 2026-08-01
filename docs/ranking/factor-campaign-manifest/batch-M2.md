# Batch M2 — Fable adversarial-review diagnostics on ranking v1

**Registered by `fable`, 2026-08-01, before any number was computed.** Mandate:
`docs/fable-mandate-M2-2026-08-01.md` (founder's ruling 2026-08-01: fable may compute and build,
same guardrails). Full pre-registration text: `docs/fable/M2-findings.md`, log entry
"Pre-registration of M2-1 diagnostics".

## m_b = 8

All eight are cells of one diagnostic — **D2, the disagreement-conditional win rate** on the
frozen, committed v1 panel (`experiments/bottomup/results/ranking_v1_v1_players.csv`, 2018–2024,
2025 untouched, no refit, no selection):

| # | cell |
|---|---|
| 1–4 | panel M (market ADP) × QB / RB / WR / TE — pooled veteran-pair win rate vs 0.50 |
| 5–8 | panel E (expert ECR) × QB / RB / WR / TE — pooled veteran-pair win rate vs 0.50 |

Decision rule: NULL unless the 4,000-rep season-block bootstrap 95% CI excludes 0.50 (seed
20260801). BH correction at the campaign denominator, per this manifest's README — these 8 join
Σ_b m_b.

D0 (reproduction of published v1 numbers) and D1 (availability-channel decomposition) are
**verification and estimation respectively — no hypothesis grade, 0 tests contributed.**
Descriptive conviction strata under D2 are labelled descriptive and are not graded.

## Amendment 1, 2026-08-01 — registered after D0–D2 were read, before any v2 number was computed

D1/D2 located v1's deficit in the games channel (oracle-games flips every cell; the oracle is an
upper bound sharing a factor with the outcome and is not a target). One reachable arm follows and
is registered **before being run**:

**D3 — candidate `v2-flatgames`: m_b += 8 (total m_b = 16).** Identical to v1 except veterans are
ordered by projected **per-game** points (`proj_points / max(proj_games, 1)`) — i.e. the games
projection is removed entirely, no foresight substituted. Rookies stay pinned. Graded per cell
(panel × position, 8 cells): paired season-block bootstrap (4,000 reps, seed 20260801) on
**Δρ(v2 − crowd) − Δρ(v1 − crowd)**; a cell is a WIN only if the 95% CI excludes 0 on the
positive side, HARM if on the negative side, else NULL.

**Adoption rule, fixed now:** recommend v2-flatgames to `ranker` only if ≥ 2 cells are WIN and 0
cells are HARM. Otherwise the recommendation is "repair the games channel" with no shipped
variant. **Registered prediction:** partial recovery of the expert-panel deficit at QB and RB
(where D1b concentrates the excess in missed-time players); WR/TE market cells expected NULL.
A 0.5-shrink games variant will be reported as descriptive sensitivity only and is **not** a
candidate (two candidates would be selection).

## Outcomes, recorded 2026-08-01 after the runs (no grade changes to any other batch)

**D2 (8 cells):** three significant LOSSES for v1's disagreements vs expert ECR — QB 0.342, RB
0.360, WR 0.412, all p=0.0003 (bootstrap floor), surviving BH at any campaign denominator; five
NULL (all market cells + E-TE). **D3 (8 cells):** M-RB WIN (+0.036, p=0.049), E-QB and E-RB HARM
(−0.033 p=0.0003, −0.043 p=0.010), five NULL → the pre-registered adoption rule (≥2 WIN, 0 HARM)
**fails; v2-flatgames is not adopted.** Reproduction scripts committed:
`experiments/bottomup/fable_m2_diagnostics.py`, `experiments/bottomup/fable_m2_v2.py`. Full
write-up: `docs/fable/M2-findings.md`.
