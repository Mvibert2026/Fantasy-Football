# 2026-07-29 — backend — why QBs rank high in a 4-pt-passing-TD league

**Task.** The founder challenged the shipped 2026 board: it moves Josh Allen +20 (to overall #6)
and Lamar Jackson +19 against consensus, in a league that pays only 4 points per passing TD.
Investigated as a suspected defect first, per CLAUDE.md §8.

**Outcome: explained, not a bug — but the edge does not survive its own error bars.** Full
reasoning and every figure in **ADR-057** (`docs/decisions.md`).

## What I was asked to test, and what happened to it

The launching brief named the stacking passing-yardage bonuses as the leading mechanism and told
me to attack it hardest. **It is refuted.** Turning every yardage bonus off moves Allen zero board
ranks; passing bonuses are 2.1% of QB1's value over replacement. The brief's second premise — "if
disabling rushing/receiving bonuses also moves quarterbacks, that is a bug" — is **also wrong**,
and I did not treat it as a bug: VBD is a cross-position comparison, so changing the RB curve
necessarily reorders QBs, and elite QBs rush enough to hit rushing thresholds themselves. Both
predictions were stated confidently and both were incorrect; recording that here because the
project's stated failure mode is confident stories that fit the numbers.

The brief's leading *defect* hypothesis — a threshold bonus computed off a season total rather
than per game — is also disproved, at the engine level and against real 2024 QB seasons.

## What actually explains it

1. **VBD cancels the curve intercept exactly** (`VBD = b·(ln rank − ln base)`). Level intuitions
   about scoring rules — including "4 points per passing TD is stingy" — transfer to this board
   only through the *slope*. This is why the question felt unanswerable.
2. **The founder's intuition is correct and the board already obeys it.** At 6 pts/passing TD
   Allen would be #4; at 2 pts he'd be #8. The stingy setting is already pushing QBs down.
3. **56.5% of the elite-QB edge is rushing**, scored at RB rates and untouched by passing
   stinginess. Exact decomposition, licensed by the linearity of OLS in the outcome vector.

## The finding that matters more than the answer

The QB slope **collapsed monotonically** across the training window: −67, −73, −59, −45, **−4**
for 2021–2025. `fit_rank_curves()` pools all five seasons with **equal weight**, so the shipped QB
premium is an average over a regime that was disappearing. 2025 is verified complete (18 weeks,
18,521 rows), so this is not truncation. Meanwhile Allen's bootstrap CI is **[57.0, 155.2]**,
overlapping 29 of the top 40 players. The board's own uncertainty machinery already said the +20
was not actionable; the point estimate was being read without its interval.

Secondary: the log-linear estimator is misspecified **asymmetrically across positions** (RB/WR
concave in log-rank, QB not) — an ordering risk, since the board ranks positions against each
other.

**Deliberately not fixed.** Recency weighting and the estimator form are methodology changes
requiring the Statistician + Red-team gate, not a backend patch. Both are test-pinned and logged
in `docs/ideas-inbox.md`.

## Environment notes

- `scripts/rebuild_database.py` failed at **step 4/8** (`ingest_rankings.py`): the DynastyProcess
  mirror on github.com 403s through the agent proxy. This is documented in that script as an
  expected, reportable Claude-session-only block that must **not** be patched around. I did not
  patch it. I restored the `rankings` table from the **committed byte-exact dump**
  `data/rankings-history/rankings_2021_2025.csv` via a session-local helper in `experiments/` —
  a committed-artifact restore, not a source swap, and nothing in the pipeline calls it.
- Consequently steps 6–8 never ran, so `players_canonical`, `adp_snapshots` and `play_callers` do
  not exist in this container's DB. **18 test failures + 9 errors are entirely from those missing
  tables** (`sqlite3.OperationalError: no such table: adp_snapshots`), plus the pre-existing
  `test_handoffs.py::test_mailbox_health` documented in ADR-056. `git status` confirms **zero
  files changed under `src/`** this session, so none of them can be mine.
- The brief said the rebuild takes ~64s and succeeds. It does not in this worktree.

## Inbox

23 open threads addressed to `backend`, all from `pm` and all unrelated to this task. Not worked —
this session was scoped to the QB question only. No thread statuses changed.

## Evidence

- `tests/test_qb_board_delta.py` — **9 tests, all passing** (6 pure, 3 `requires_db`). Written
  before the diagnostics they license, per the standing rule.
- `experiments/qb_board_delta_diagnostic.py`, `experiments/qb_board_delta_uncertainty.py` —
  reproducible.
- Full suite: **673 passed, 18 failed, 9 errors** — all failures environmental as above.
