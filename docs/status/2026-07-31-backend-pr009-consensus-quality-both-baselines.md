# 2026-07-31 — backend — PR-009 consensus quality, season by season, both baselines

Dispatch: run strategist's pre-registered design
(`docs/preregistration/PR-DRAFT-consensus-quality-by-season.md`, allocated `PR-009`) against BOTH
required baselines per the founder's ruling folded into `CLAUDE.md` §6.5 today (market ADP +
expert consensus/FantasyPros ECR), per `docs/handoffs/2026-07-31-consensus-quality-season-by-season-
plus-the-comp.md` item 1 and `docs/founder-requests/FR-2026-07-31-ruling-measure-against-both-market-adp-and-exper.md`.

## What was run

New `experiments/bottomup/components/consensus_quality.py`. Reuses `pos_data.build_panel`/
`universe_for`, `pos_features.build_features`/`outcome_components` unmodified (so B2/B3 cannot
drift from the already-published walk-forward numbers), adds:

- `market_pass_players` / `ecr_pass_players`: per (2013-2024, position), the frozen pre-season
  universe merged with that crowd's board (FFC ADP or `rankings` `fantasypros_ecr`).
- `season_cell`: rho of the crowd vs realised points, rho of B2 (prior points) and B3 (weighted
  PPG x games share), on the covered subset, plus B4 context (top-12 vs 13-24 realised points).
- `null_band`: player-level bootstrap (4,000 reps) of the season's own rho, giving a sampling-noise
  half-width. Decision rule (PR-009 SS5): POOR iff rho_crowd < rho_B3 AND the gap exceeds that band.
- `prediction_test` (SS6): S1 rookie share of ADP/ECR top-36, S2 FFC's own std_dev (ADP only), S3
  prior season's own gap, each tested via Mann-Whitney AUC (season-level bootstrap CI) against the
  POOR label. Simplification stated in the code: each signal is a raw pre-existing value (nothing
  fit), so "walk-forward" AUC reduces to computing AUC directly over labelled seasons without
  leakage.
- `spread_ci`: season-level bootstrap of the SS5 outcome-(i) spread clause.

Seed `20260731` throughout (guardrails SS11 — never builtin `hash()`; the one place a small
deterministic seed offset was needed, `hash_free_index`, is an explicit dict lookup, not `hash()`).

## Coverage found, reported before any rho was read (PR-009 SS9)

- **Market ADP (half-PPR 12-team)**: `data/adp-snapshots-ffc/` has **zero** half-PPR-12team files
  for 2013-2017 — only the non-PPR/PPR 12-team archives reach back that far. So despite the PR's
  nominal 2013-2024 window, the market pass is structurally **2018-2024, 7 seasons**. Confirmed via
  `ls` before writing any code that depended on it.
- **Expert ECR**: `rankings` where `source='fantasypros_ecr'` has exactly one pre-Week-1-dated
  snapshot per season, 2021-2025. 2025 excluded both by the sealed holdout and by the source itself
  (`load_ecr` refuses `season >= HOLDOUT_SEASON` before querying). Usable: **2021-2024, 4 seasons**.
- ECR is a **standard/non-PPR proxy**, not this league's half-PPR — `src/ingest_rankings.py`'s own
  docstring says `scoring_format` is NULL on every row (DynastyProcess mirror has no PPR variant of
  `redraft-overall`). Same caveat class as the market pass's 12-team-for-10-team substitution.

## Reproducibility check before trusting anything

Before writing the ECR pass, reran `run_position.py RB` (the committed pass) and diff'd its output
CSV against the repo's committed `rb_components_metrics.csv` — byte-identical on every `rho_*`
column (only new `adpsub_mae_*` columns from a later factor batch differ, additive). Then, once
`consensus_quality.py`'s own market-ADP pass was written independently (not copy-pasted from
`pos_eval`, reusing only its unmodified building blocks), its RB output matched the committed CSV
to the same precision — two independent code paths, same numbers.

## Result

Zero POOR seasons at every position under both crowds (0/7 market-ADP cells, 0/4 ECR cells).
STRONG clears at 1/7-3/7 positions (market ADP) and 1/4-4/4 (ECR). **Outcome (i)** (consensus
stable) is what the data supports — directly contradicting strategist's own pre-registered
prediction of outcome (iii), written in advance specifically so it could be checked against the
number. The spread sub-clause of outcome (i) is mixed (passes at RB/WR for market ADP, RB/WR/TE
for ECR; fails at QB/TE for market ADP and narrowly at QB for ECR — driven by small `n_covered`,
not an established quality swing). SS6's prediction test could not discriminate anything: with zero
POOR seasons, there is no positive class, so every AUC cell is `NaN` by construction. Outcome (ii)
is therefore structurally unreachable this run, not disproven.

## One data fix, additive

`experiments/bottomup/components/adp_baseline.py::load_adp` was dropping FFC's own `std_dev`
column at its final column-select (needed for SS6's S2 signal). Retained now; purely additive
(other callers unaffected — verified `tests/test_wr_component_model.py` 14/14 still green, and all
existing `adp.load_adp(...)` call sites elsewhere in `experiments/bottomup/factors/*` destructure by
name, not by position).

## What was not done

Item 2 of the same thread (component-MAE-to-rank derivation) — out of this session's dispatch,
left `STATUS: OPEN` on the thread. `docs/ranking/component-model-*` files untouched.

## Files

- `docs/preregistration/PR-009-consensus-quality-by-season.md` (allocated, was `PR-DRAFT-*`)
- `experiments/bottomup/components/consensus_quality.py` (new)
- `experiments/bottomup/components/adp_baseline.py` (std_dev retained, additive)
- `experiments/bottomup/results/pr009_consensus_quality.csv`,
  `pr009_outcome_summary.csv`, `pr009_prediction_test.csv` (new)
- `docs/preregistration/test_run_log.jsonl` (56 PR-009 rows, one clean run after removing a
  duplicated debug pass)
- `docs/CURRENT-STATE.md` (new "Last verified 2026-07-31" entry)
- `docs/handoffs/2026-07-31-consensus-quality-season-by-season-plus-the-comp.md` (reply appended,
  `### backend · 2026-07-31`, STATUS left OPEN — item 2 outstanding)

## Note on shared session

A coordinator commit (`ed8d269`, then `e29e955`) landed this session's `consensus_quality.py` and
`adp_baseline.py` changes alongside a parallel, independent `ranker` session's own
`ecr_baseline.py`/`ranking_v1.py` work in the same commits. Verified via `git diff HEAD -- <files>`
that every file this session wrote landed byte-identical — nothing to reconcile. The two ECR-facing
efforts (this thread's per-season level report vs. `ranking_v1`'s own baseline harness) are
flagged as not reconciled against each other, not assumed consistent.
