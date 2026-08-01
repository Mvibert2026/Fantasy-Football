# 2026-08-01 — backend — batch C2: more factors, plus the RB high-carry breakpoint

**Dispatch**: run batch C2 against ranking v2 — Part A, more untested-for-v2 factors from the
ledger (prioritising data already in `nfl.db`, including newly-ingested `odds_snapshots`); Part B,
the threshold/breakpoint test class, never run before, with the founder's own RB high-carry-season
hypothesis (350/375/400 carries) as the worked example. Grading was explicitly suspended by the
dispatch: C1 found its registered inclusion rule hands a BH-robust WIN to seeded noise (false-
positive rate 9.6% of cells against a nominal 2.5%), and `strategist` is building the replacement.
This session was to build, run, and record — not grade, and not invent a substitute rule.

## Effort-tier note

This task designs a multi-arm statistical screen (control windows, coverage floors, a
non-linearity test, a placebo calibration instrument) against `CLAUDE.md` §6.3's overfitting
guardrails. Per the operating model, work touching a statistical constant or methodology design
should arrive dispatched to opus/high effort; this dispatch did not specify a tier explicitly and
ran at the default (sonnet/medium) available to this session. Two things mitigate the risk that
would normally justify escalating a tier gap: (1) grading was explicitly suspended by the dispatch
itself, so no INCLUDE/EXCLUDE call — the highest-stakes statistical judgment — was made this
session; (2) every design choice (control windows, factor scope exclusions, the single-spline-test
design for Part B, the coverage floor) follows an established pattern from C1/batch-7 rather than
inventing new methodology from scratch. Flagged here per the standing instruction rather than
stopping to ask for a re-run.

## What happened

1. **Environment**: worktree had no `data/nfl.db` (fresh worktree, per `docs/environment.md` §4) —
   copied from the main checkout. Worktree's branch (`worktree-agent-a1446683c76f72ee2`) had
   branched from `main` before C1's work landed; C1 lives on `claude/pm-agent-setup-gobxa0`, not yet
   merged to `main`. Merged that branch in (clean, no conflicts) to get `run_c1.py`/`factors_c1.py`
   and the C1 results doc to extend, per the dispatch's explicit instruction to extend rather than
   reinvent the harness.
2. **Registered before computing**: `docs/ranking/factor-campaign-manifest/batch-C2.md`, committed
   at `ee87b53`, m_b = 29. Manifest README updated, campaign Σm_b now 159 (recorded for a future
   regrade; not applied this batch since no BH is computed while grading is suspended).
3. **Built** `experiments/bottomup/v2/factors_c2.py` and `run_c2.py`, extending C1's pattern.
   Reused three of batch 7's existing gated feature blocks verbatim (`_yac`, `_rec_points_share`,
   `_late_season` — built for the old consensus-derived primary, never run against v2, and fair
   game per the ledger's Section 0 rule). Two new blocks: WOPR (reads an already-computed,
   already-dense `player_weekly_stats.wopr` column — no new source) and implied team total (the
   first read of `odds_snapshots` by any model in this project, joined by (season, week, team) to
   each player's own team so a mid-season trade is measured against the offence he was actually in).
   Part B's hinge-spline block needed **zero new data** — `carries_1` already exists in every v2
   feature frame from `pos_features.build_features`'s own lag-1 accumulator.
4. **Part B design decision, made before running anything**: the dispatch explicitly warned that
   sweeping candidate thresholds and reporting the best is how a multiple-comparisons finding gets
   manufactured, and preferred a single non-linearity test over a sweep. Implemented as one arm — a
   piecewise-linear (hinge) basis with the founder's own three values (350/375/400) used as fixed,
   pre-registered spline knots, never searched or compared against each other. m_b = 1 for Part B,
   not 3.
5. **Ran all 12 arm-runs, committing after each one** (per the dispatch's explicit instruction,
   given token-pool risk): F0, F0D (placebo at both controls), A1, A2/A2k, A3/A3k, A4/A4k, A5/A5k,
   B1. 29 of 29 registered cells landed. F0 at the 7-season control reproduced C1's own numbers
   byte-for-byte, the strongest available confirmation that the harness reuse (same generator, same
   salt, same control params) is correct.
6. **One anomaly investigated rather than left unexplained**: A4/A4k at TE produced bit-identical
   deltas despite adding different feature sets. A direct debug run (separate walk-forward fits,
   compared at the point-projection level) confirmed the two arms' predictions genuinely differ
   (up to 2.5 points/player-season); the graded TE population has 100% coverage on the coverage
   flag in every season, and the additional value columns apparently do not move rank order within
   that small population (n≈10-14) in any of 7 separate seasons. Recorded as an open, surprising-but-
   verified finding rather than assumed to be a bug or silently dropped.
7. **A5's own instrument caught a caution about itself**: A5 (implied team total) runs on `CTRL-D`,
   a 4-season control needed to match `odds_snapshots`' 2018 start. F0D (the placebo run fresh at
   that same control) won CI-level at 2 of 4 cells, against 0 of 4 at the 7-season control — an
   independent second measurement of C1's own "shorter windows are more miscalibrated" finding, and
   the reason A5's two apparent CI-WINs (QB value, RB coverage-control) are reported as
   indistinguishable from harness noise rather than as findings.
8. Wrote `docs/ranking/batch-C2-results.md` (conclusion-first, live-updated per the run log — each
   arm's commit hash is in the doc), extended `docs/factor-ledger.md` Section 0 with C2's
   dispositions (all `PENDING-RULE`), updated `docs/CURRENT-STATE.md` in place.

## What did not happen

- **No factor was graded INCLUDE or EXCLUDE.** Every cell carries a CI-level verdict (WIN/HARM/
  NULL, estimator-independent, safe for a mechanical future regrade) but the factor-level status is
  fixed at `PENDING-RULE` by construction (`run_c2.py`'s `factor_verdict()` always returns it,
  regardless of the CI numbers).
- **No new threshold or grading rule was invented** to fill the gap left by C1's broken WIN rule,
  per the explicit instruction not to.
- **The 2025 holdout was not opened.** Every arm asserts `n_preseason_proxy_reads == 0`.
- **No factor's design was tuned after seeing a result.** Registration was committed before any
  arm ran.

## Commits

Registration `ee87b53`; ledger row + manifest README `ee87b53`; harness + F0 `6dab690`; results doc
scaffold `a9dca42`; F0D `1e80cc8`; A1 `7cae66e`; A2/A2k `d213232`; A3/A3k `b3cb337`; A4/A4k
`1d48b22`; A5/A5k `c1b11f4`; B1 `06f04cb`. Write-back (this file, `CURRENT-STATE.md`,
`factor-ledger.md`, final `batch-C2-results.md`): pending, see the commit that follows this file in
git history.

## Handoffs touched

None opened or resolved this session — the blocking thread on C1's WIN rule
(`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`) already exists and
is `BLOCKED-ON-YOU` for `strategist`; this session adds a second data point (CTRL-D's placebo) to
the case for a control-window-aware replacement rule but does not reply into that thread, since no
new information changes who owns the next action.
