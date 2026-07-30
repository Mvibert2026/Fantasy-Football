# 2026-07-30 — backend — backtest VBD-deficit fix (ADR-066)

Dispatched directly (not via inbox) to fix a backtest evaluation defect strategist found while
ruling on the primary evaluation metric
(`docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md` §4.1): `src/backtest.py`'s
`_vbd_sum_for_ranking`/`top_k_starter_vbd` scored a ranked player with a resolved position but zero
weekly stat rows (retired, cut, season-ending preseason injury, suspended for the year) at exactly
`0.0` VBD — replacement level — for the starting slot he consumed. His true contribution is
`0 - replacement_points[pos]`, since he consumed a slot and produced nothing. `0.0` is a materially
better outcome ("as good as the waiver wire") than what actually happened, so the harness
systematically under-penalised rankings that promote injury/roster-risk players.

## What changed

`src/backtest.py`:
- `_vbd_lookup` now returns `(vbd, replacement_points)` — the second element is the per-position
  POINT value at the replacement baseline, computed with the same index arithmetic
  `scoring.compute_vbd` uses internally (duplicated locally; `compute_vbd` doesn't expose it). This
  is an evaluation-harness-only addition — `scoring.py` and all ranking logic are untouched.
- New `_slot_value(pid, pos, vbd, replacement_points)` helper: returns the real `vbd[pid]` if the
  player has one, else `-replacement_points.get(pos, 0.0)`.
- `_vbd_sum_for_ranking` and `top_k_starter_vbd` both route slot contributions through
  `_slot_value` instead of `vbd.get(pid, 0.0)`.
- `compute_season_metrics` threads `replacement_points` through to both.

Regression tests written first (confirmed failing against pre-fix code before the fix landed):
`tests/test_backtest.py::test_never_played_player_scores_the_replacement_deficit_not_zero_vbd`,
`::test_never_played_player_in_starter_vbd_also_scores_the_deficit`.

Commit `b567586`.

## Re-run of ADR-025

Recomputed the published board-vs-consensus `starter_vbd` figures (+176.0/-34.7/+113.4/+83.8,
2022-2025 holdout) under the fix, against the current `data/nfl.db` snapshot. Result: the fix
changes **none** of them — delta exactly `0.0` in all four seasons, both arms, confirmed by diffing
pre-fix and post-fix code against identical DB state and ranking objects. No board- or
raw-consensus-ranked player filling a top-15 starting slot in 2022-2025 had a completely empty
season, so `_slot_value`'s new branch is never exercised for this specific comparison.

Separately — and reproduced with the *unmodified* pre-fix code, so not caused by this fix — the
numbers no longer exactly match the originally published values (now 174.6/-27.68/94.1/79.54).
This is `nfl.db` re-ingestion drift since 2026-07-25 (the DB is gitignored and rebuilt repeatedly
across sessions). ADR-025's qualitative conclusion (3/4 seasons positive, board advantage not
statistically established at n=3/4) is unaffected either way.

## Blast radius

The defect is real regardless of ADR-025 being unaffected — found a live instance on
`bpa_prior_season_points` (the weak, backward-looking, injury-blind baseline arm), which moved on
`vbd_sum` (the deeper per-position metric, not `starter_vbd`) by **-114.7 in 2022** and
**-139.1 in the 2025 holdout** — one never-played player per season, now correctly scored as a
deficit.

`docs/test-registry.md` #44-46's "-1,070 pts" BPA-vs-FantasyPros headline uses the same defective
path (`src/candidate_rankings.py` + `_vbd_sum_for_ranking`) on the sealed 2025 season. **Not
re-run**: no committed script reproduces the original run, and `docs/strategic-insights.md` §1
already marks this exact figure "Discarded as superseded ... do not cite" for unrelated
methodological reasons. Flagged as additionally contaminated on top of already being deprecated.
Escalated to `strategist`/`pm` rather than deciding unilaterally, since it touches the sealed
holdout and ADR-026 (alpha-track closure) cites the same evidence pattern — handoff thread
`docs/handoffs/2026-07-30-backtest-vbd-deficit-fix-landed-adr-025-confirme.md`.

`docs/adr-drafts/ADR-DRAFT-oracle-ladder-disposition.md`'s planned durability test was already
blocked on this exact precondition by name; now unblocked (never ran, no re-run needed).

Full before/after table and reasoning: `docs/decisions.md` ADR-066.

## Holdout access

Recomputing ADR-025 under the fix reads the sealed 2025 season again. Per strategist's own ruling,
this is a recomputation of an already-spent access (2025 was unsealed for this exact decomposition
on 2026-07-25), not a fresh spend — logged as such. Eight new `FINAL_EVALUATION_OPENED` entries in
`docs/preregistration/holdout_access_log.jsonl` (some from re-verifying after a concurrent commit
reshuffle required repeating the diff against the correct pre-fix parent), all reviewed and added
to `tests/test_holdout_audit.py::REVIEWED_TIMESTAMPS` with ADR-066 as the justification, per that
test's own required procedure.

## A found-but-not-caused-by-me issue

`docs/CURRENT-STATE.md` contained live, unresolved git merge-conflict markers spanning two
frontend session narratives, left by a coordinator merge commit that resolved the code conflict but
not the doc. Per the operating rules (merge conflicts are escalated, never resolved unilaterally),
inserted this session's own "Last verified" entry above the conflict without touching it, and
logged the conflict itself to `docs/ideas-inbox.md` item 6 for `pm`/`verifier`.

## Shared-session note

Concurrent agents in this shared container committed on top of this session's work twice
(`b567586`'s fix commit is intact in history; the ADR-066/blast-radius/holdout-review edits landed
inside a coordinator commit `df50e3b` and a merge `17d41a3`). Verified via `git diff HEAD -- <files>`
that what landed is byte-identical to what this session wrote in every case — nothing lost, nothing
to reconcile.

## Evidence

- Commit `b567586`: the fix + regression tests, confirmed failing pre-fix.
- `docs/decisions.md` ADR-066: full before/after table, blast radius, holdout-access reasoning.
- `docs/handoffs/2026-07-30-backtest-vbd-deficit-fix-landed-adr-025-confirme.md`: escalation to
  strategist/pm for the #44-46 item.
- `docs/ideas-inbox.md` item 6: the CURRENT-STATE.md merge-conflict escalation.
- Tests: `tests/test_backtest.py` 33/33 passing (2 new). `tests/test_holdout_audit.py` 3/4 passing
  (the one failure, `test_no_new_direct_sqlite_connections_in_src`, is pre-existing and unrelated —
  new ingestion scripts from concurrent sessions, verified via `git log` that this backend session
  did not author them).
