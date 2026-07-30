# 2026-07-30 — ranker — factor batch 1 (registry #19, #20, #28, #13)

Worktree `agent-a6dad8fc40be4a3b3`. Commits `d546cff` (pre-commitment, before any fit), `HEAD`.
Suite: **878 passed, 8 failed** — all eight verified pre-existing by running the same set against a
stashed tree (identical 8 failures, 75 passed). None is in code touched this session.

## What was asked

Run the highest-value untested **projection** factors from `docs/test-registry.md`, four of them, in
priority order, with a pre-registration committed first and a multiple-comparisons correction across
the batch. Stay out of VBD baseline and VONA work.

## What was done

| path | what |
|---|---|
| `docs/ranking/factor-batch-1-precommit.md` | design — factors, arms, endpoints, m=23, BH q=0.10, grading — committed `d546cff` **before the first fit** |
| `experiments/bottomup/factors/factor_features.py` | three new lagged feature blocks: team volume, vacated opportunity (PROXY), target-share stability |
| `experiments/bottomup/factors/run_factors.py` | the 23 registered arms + the #13 descriptive persistence measurement |
| `experiments/bottomup/factors/diagnostics.py` | post-hoc splits: reproduction check, effect size in absolute terms, volume terciles, ADP-board restriction |
| `docs/ranking/factor-batch-1-results.md` | results |
| `experiments/bottomup/results/factor_batch1_*.csv` | per-arm numbers |

Harness changes, all additive and all default-off: `SeasonPanel.week1_roster()` with its own audit
tag; `WalkForward.feature_fn` and `allow_preseason_proxy`; `ShrunkRate.volume_prior`;
`BaseComponentModel.volume_cols` / `rate_overrides`. **The primary is bit-identical under the old and
new feature builders across 30–34 metric columns at all four positions**, so
`component-model-rb-qb-te-pass-1.md` still reproduces.

## Result

**23 tests, zero wins.** 10 NULL, 7 HARMFUL, 2 projection-only, 2 nominal survivors — and both
survivors are undone by a post-hoc check showing their gain sits among undrafted players. No arm
moves the ranking against consensus anywhere. Sealed 2025 holdout not opened.

The four keepers are in `docs/ranking/factor-batch-1-results.md` §1 and are summarised in
`docs/strategic-insights.md` §3, §4 and §5b. The one that changes what gets built next: **registry
#19's premise is wrong in its strong form** — discarding a player's own TD rate for the pooled
positional mean is worse at all four positions, so TD rate is signal and the existing shrinkage
already extracts it.

## Handoffs opened (no IDs allocated — use `tools/handoffs.py sync`)

- `docs/handoffs/NEW-rosters-weekly-blocks-vacated-opportunity.md` → `data-ops`
- `docs/handoffs/NEW-preregistration-gates-need-a-decision-subset.md` → `strategist`

## Not done, deliberately

`docs/CURRENT-STATE.md` untouched — another agent is working board/valuation math concurrently and
its machine-measured rows come from `tools/state.py --apply`. `docs/dashboard.html` and
`docs/roles-workflow-map.html` are point-in-time snapshots and are **stale** with respect to the
test-registry verdict column added this session.
