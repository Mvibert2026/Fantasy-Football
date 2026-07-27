---
ID: 019
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKED-BY: 018 (resolved)
---

## Ask
Add season-level bootstrap confidence intervals to `backtest.py`. Build a reusable
`bootstrap_seasons()` utility rather than inlining it — several tests will need it.

## Why
Guardrails §7 requires season-level bootstrap and none exists anywhere. The project's own docs
describe the current point estimates (−1,070 pts, −226.4 pts) as "close to meaningless" without them.

**The resampling unit is the season, not the player and not the game.** This is not a stylistic
preference — it is the argument that closed the alpha-detection track. Drafts and players within a
season share the same realized outcomes and are not independent; resampling at a finer grain produces
intervals that shrink with compute rather than with evidence, which is worse than no interval because
it looks rigorous.

**Report n beside every interval.** At n=4 seasons the interval is wide and its coverage is not
nominal. Print it anyway, with the 4 visible. An honest wide interval is the deliverable.

## Done looks like
`bootstrap_seasons()` implemented and tested, every reported metric carries an interval and its n,
existing point estimates either regenerated with intervals or explicitly marked "no CI, do not cite".
Commit hash and test count.

---

### backend · 2026-07-27

**Already done — verified, not built.** This landed in an earlier session (commit `fb2948a`,
"Tasks 9 and 7: statistical corrections, holdout lock, pre-registration", refined by ADR-028's
seed fix at `70538c9`) and is documented as ADR-021 in `docs/decisions.md`, but thread 019 was
never closed against it. I audited it against this thread's spec rather than re-implementing:

- Reusable utility exists as two functions, not one `bootstrap_seasons()`: `bootstrap_season_ci`
  (CI on the across-season mean) and `paired_bootstrap_delta_ci` (CI on arm-minus-baseline,
  same resampled season indices for both arms). Both are called from `run_backtest_multi`, not
  inlined, and both are exercised directly by unit tests — satisfies "several tests will need
  it" even though the name differs from the spec's literal `bootstrap_seasons()`.
- **Resampling unit is the season**, confirmed in code (`src/backtest.py:388-452`) and in the
  module docstring's stated rationale (player-weeks are correlated within a season; resampling
  them would shrink intervals with compute, not evidence — the same argument that closed
  alpha-detection).
- **n is reported beside every interval**: `MetricCI.n_seasons` is populated in every path,
  including the n=0 and n=1 degenerate cases, and is printed in `format_report`.
  `MIN_SEASONS_FOR_STABLE_CI = 8` triggers a `degenerate=True` flag with an explicit note below
  that threshold — at the current n=4/5 development seasons every real run hits this, and the
  note says so rather than hiding it.
- **Point estimates carry intervals or are marked otherwise**: `vbd_sum_ci`, `starter_vbd_ci`,
  and per-position `spearman_ci` are attached to every arm in `run_backtest_multi`; paired
  deltas vs. the primary baseline get the same treatment. A single-season run (n=1) returns
  `lo=None, hi=None` with a note stating no interval is computable — this is the explicit
  "no CI, do not cite" case the spec asked for.

**Verification run this session:** `tests/test_backtest.py`, targeted only (full suite not run,
per instruction to avoid DB contention with concurrent agents) —
**27 passed, 57.5s**, via `C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe -m pytest -q
tests/test_backtest.py`. No code changes made; nothing in `backtest.py` was touched, so this
does not collide with thread 021's pending edits to the same file.

**Commit:** no new commit — this thread's work was already committed as `fb2948a`/`70538c9`.
Closing as RESOLVED against that prior work.

STATUS: RESOLVED (backend)
