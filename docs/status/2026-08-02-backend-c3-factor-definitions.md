# 2026-08-02 — backend — C3 factor definitions

**Dispatch:** write factor *definitions* (not run/fit/grade) for untested candidates in
`docs/factor-ledger.md`, against the `experiments/bottomup/v2/factors_c1.py`/`factors_c2.py`
harness interface, prioritising `odds_snapshots`, `injuries`+practice participation,
`depth_charts_weekly`, `combine`, `pbp`, `ff_opportunity`, `snap_counts` in that order.

**Blocking dependency found and worked around, not stopped on.** `factors_c1.py`/`factors_c2.py`
(and `docs/ranking/batch-C1-results.md`/`batch-C2-results.md`) do not exist anywhere in this repo —
checked `find` over the repo, `git ls-tree -r origin/main` after `git fetch`, and a doc grep for the
capital-C naming. Most likely a concurrent `ranker` worktree building the v2 rewrite (ADR-069) that
has not merged; worktrees are isolated so this session cannot see it. Built instead against the
closest verified-real interface, `experiments/bottomup/components/pos_data.py`'s `SeasonPanel`/
`feature_gate`/holdout-gate machinery (used by all of batches 1-7), structured like
`factor_features7.py`'s `Batch7Sources` pack. Flagged in a new handoff thread to `ranker`
(`docs/handoffs/2026-08-02-c3-factor-definitions-written-but-v2-factors-c1.md`) for reconciliation
once the real files land.

**Scope deviation from the dispatch's own priority order, also flagged, not resolved unilaterally.**
`odds_snapshots` was priority #1 in the dispatch, but `docs/factor-ledger.md` T0-11/N12 (Vegas
spread/total/implied total) are dispositioned `blocked` for data availability (no odds table at the
time) plus a substantive oracle-ceiling finding (≤+0.055 τ_b). The dispatch also says "do not
resurrect data-availability exclusions." `odds_snapshots` now exists (2018-2024), so the
data-availability half is stale, but the oracle-ceiling half is not obviously a consensus-derived-
frame artifact either. No odds factor was defined. Same for T1-22 (PROE, blocked for "no PBP table,"
also now stale but not resurrected) — used N20 (neutral-situation pass rate, `untested` not
`blocked`) instead, from `pbp`.

**Delivered:**
- `experiments/bottomup/v2/factors_c3.py` (761 lines) — six factors:
  - **C** injury report-week burden (`injuries`, 2010+, target seasons 2011+)
  - **D** practice-participation severity (`injuries`, 2010+, target seasons 2011+)
  - **E** end-of-prior-season depth-chart ordinal rank (`depth_charts_weekly`, 2001+, target
    seasons 2002+; explicitly NOT week-1-of-target-season, per strategist's look-ahead ruling)
  - **F** combine athletic-testing z-composite (`combine`, 2000-2026; the rookie-relevant factor
    named in the dispatch — `combine` was confirmed read by no projection model)
  - **G** neutral-situation team pass rate (`pbp`, 2009+, target seasons 2010+; ledger N20)
  - **H** efficiency-over-expected rate (`ff_opportunity`, 2006+, target seasons 2007+;
    opportunity-normalized, distinguished from the already-built xFP volume diff)
  - All six have `*_known` companions and a stated mechanism, per the dispatch's mandatory
    requirements. All six loaders + `attach_*` functions smoke-tested against the real
    `data/nfl.db` (copied into this worktree per `docs/environment.md` §4) — run end to end,
    produce plausible values. Not a unit-test file; not a fit; no predictive claim made.
- `docs/ranking/batch-C3-candidates.md` — mechanism/source/span/control per factor, plus the
  odds/PROE scope-deviation writeup and the NEXT STEP block.
- Handoff thread `2026-08-02-c3-factor-definitions-written-but-v2-factors-c1` opened to `ranker`.
- `docs/CURRENT-STATE.md` updated in place (new paragraph ahead of the batch-7 entry).

**Not done, by design (per dispatch):** no factor registered into
`docs/ranking/factor-campaign-manifest/`; nothing run, fit, or graded; `factors_c1.py`/`factors_c2.py`
not touched (do not exist); the campaign manifest not touched.

**Commits:**
- `db16a06` — C3 part 1/2 (factors C, D)
- `278d9f9` — C3 part 2/2 (factors E, F, G, H)
- (this commit) — docs, CURRENT-STATE, status log, handoff thread

**Test suite:** `tests/test_holdout_audit.py` — 1 pre-existing failure
(`test_no_new_direct_sqlite_connections_in_src`, unrelated to this session — flags
`src/ingest_combine.py` and eight other pre-existing ingestion files not on the allowlist, none of
which this session touched), 3 passed. Full `tests/` run in progress at session-end; not touched by
this batch (no code under `src/` or `tests/` was changed).
