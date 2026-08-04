# 2026-08-01 — ranker — batch D1 (v2 player availability) and M-4 (the season span)

Branch `claude/pm-agent-setup-gobxa0`. Two pieces of work: the founder's standing instruction to
build v2's player-availability model from the injury, practice and depth-chart data already in the
database, and — mid-session, on the founder's push-back — the season-span question, which was made
the priority above finishing the availability arms.

## What was built

**Batch D1**, registered at `95e2bc9` before any arm was fitted (m_b = 88; campaign Σ m_b resolved
to 247 by pm after C2 registered concurrently). Eleven arms, two matched controls, two graded
endpoints each. Code: `experiments/bottomup/v2/availability_{data,features,model}.py`, `run_d1.py`,
`reversion_buckets.py`. Results: `docs/ranking/batch-D1-results.md`.

**M-4 season span**: `experiments/bottomup/v2/span_curve.py`, `docs/ranking/season-span-M4.md`,
`experiments/bottomup/results/span_feasibility.csv` and `span_curve_cells.csv`.

## What was found

**No arm adopted, and the placebo is the reason.** The estimator-form change (binomial GLM for the
incumbent clipped OLS) buys +0.067 games-ordering over naive persistence at RB; the seeded-noise
placebo buys +0.070 on the identical contrast. Only A3 (roster status) clears its own window's
placebo bar, at RB only, at n = 5.

**The resolved-vs-ongoing instrument is real in the raw data** and explains fable's G1/G1a failure:
among players who missed ≥40% of N−1, on reserve at season end predicts 5.96 games next year against
4.14, and 26.7% against 13.7% reaching 12+ games. G1's box-score timing signal separates 4.56 against
4.19 — nothing. Being on IR at year end is *good* news relative to being cut, which is the reverse of
the intuitive reading and is why a box-score-only arm could never have found it.

**The MAE loss to naive persistence is a population mismatch.** The games model is unbiased on the
population it is fitted on (−0.14 games) and −2.41 on the board population it is used on. At matched
projected games and matched prior availability, board players play 13.77 and non-board players 9.61,
separated by prior-season points. The games model has no quality or role term; availability is partly
job security. Designed as Amendment 1 and deliberately not run, because it was found in this batch's
own output.

**On a continuous residual endpoint the arms work and the registered endpoint cannot see it.** In the
discovery pass's own buckets, G0 carries +0.315 / −0.271 SD, the form change alone moves it 0.011 SD,
and A5 moves it 0.101 SD on n = 2,000 player-seasons. Post-hoc, outside m_b, promotes nothing — but
it is the strongest methodology finding of the session and went to `strategist` as a ruling request.

**The season span can be 21, not 7.** Core stat lines run 1999–2025 with no gaps. The binding
constraint is the ADP archive that defines the evaluation universe: 7 seasons at exact format, 12
with a membership-only format caveat, 21 with no ADP at all. Two real gaps named: targets are zero
for 2003–2008 and air yards do not exist before 2009, so the extension is currently a QB/RB
extension. **Nothing adopted** — `FIRST_FEATURE_SEASON` untouched, every span passed per-run.

**Rookies are already fitted separately**, verified in `pos_model.py` rather than assumed: disjoint
fit populations, separate regressions on separate feature lists, `np.where` at every prediction site.
The live weakness is that `ROOKIE_COLS = ["log_draft_pick", "age"]` is the entire rookie model.

## Mistakes and corrections made in-session

- First span run crashed on `first_feature_season = 2018` (no training pair exists for target 2018).
  Clamped `first_target` per span and re-ran; the clamp is documented in code so a shortened span
  reports its own `n_seasons` rather than borrowing the baseline's.
- Wrote artifacts as parquet before checking; no engine installed. Switched to `csv.gz`.
- A concurrent merge left conflict markers in the shared campaign manifest README and in
  `docs/status/INDEX.md`. Resolved by keeping both batches' rows and regenerating the index; pm
  subsequently recorded the Σ m_b reconciliation at 247.

## What was checked because another agent flagged it

`depth_charts_weekly.pos_rank` / `.pos_slot` are unpopulated. **No batch D1 code reads either field**
(`grep` over `experiments/bottomup/v2/` is empty) and the inherited loader keys on `depth_team`.
Nothing in this session is that artifact.

## Threads opened

- `data-ops` — `2026-08-01-player-weekly-stats-targets-are-zero-for-2003-20`
- `strategist` — `2026-08-01-three-rulings-needed-the-endpoint-is-the-bottlen`
