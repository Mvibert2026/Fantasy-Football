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
