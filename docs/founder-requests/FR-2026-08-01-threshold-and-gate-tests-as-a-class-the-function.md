---
ID: FR-2026-07-31-threshold-tests-as-a-class
STATUS: NEW — registered, deliberately not started
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGH — a whole class of test, not a single factor
NEEDS: strategist (design the class), then ranker
---

## Request

> "Put notes in the record to look into more threshold tests. Don't do any now. Just add it to the
> list."

**Nothing was started. This is a placeholder with enough detail that whoever picks it up does not
have to reconstruct the reasoning.**

## Why this is a class and not a backlog item

**Every one of the ~90 registered factor tests used a single global linear weight.** Batches 2, 3, 5,
6 and 7 all fitted one coefficient per factor across all players, via `np.linalg.lstsq`, with no
regularisation beyond one empirical-Bayes shrinkage constant.

That means the honest statement of every null on file is:

> *No single global linear weight on this factor improves the ordering.*

It is **not** *"this factor carries no signal."* A factor that is null as a weight can be real as a
threshold, and the campaign would never have seen it. **The functional form has never been varied —
only the factors.**

This matters more than one more factor would, because if gates work where weights do not, that is a
finding about **model shape**. It would apply to everything already tested, not just to the next thing.

## The candidates already on file, in the order they arrived

| # | Candidate | Where it came from |
|---|---|---|
| 1 | **QB rushing attempts ≥ 55** | `FR-2026-07-31-league-winner-anatomy`. Converges with the analyst sweep's independent finding that QB rushing is the strongest single QB predictor (0.576). Batch 3 tested it as a **weight** and it earned its place; the gate is a different test |
| 2 | **RB carries ≥ 350 / 375 / 400 the prior season** | The founder's own, `FR-2026-07-30-rb-workload-hangover`. **Counted and mostly undefined:** ≥350 is 26 player-seasons since 1999 and **two** in the harness window; ≥400 is **zero**. Batch 4 is registered and deliberately unrun for that reason |
| 3 | **Team passing volume ≥ ~225 YPG** | Analyst sweep N29. On teams at 200–224 passing YPG, **3 of 108 WRs (3%)** finished top-12; even at a 24%+ target share, **3 of 23**. The only other gate in the registry, also untested |
| 4 | **Targets per route run ≥ 20%** | Analyst sweep N3. **92% of top-24 WR finishers since 2006** cleared it |
| 5 | **Snap share ≥ 60% persistence** | Analyst sweep N18. Tested as a weight in batch 7 and came back a **RESTATEMENT at R² = 0.90** — the gate version is untested and is a different question |

## Design cautions, so the class is not run badly

- **A threshold is a free parameter, and testing several is testing several times.** Three cut-points
  is three tests, and the campaign correction is at campaign level (`CLAUDE.md` §6.3). Pre-commit one
  primary cut with the others as secondary, or fit a continuous form with the cut as a robustness
  check — decided **before** seeing which cut works.
- **Count the support first.** Candidate 2 is the cautionary case: two of the founder's three
  thresholds turned out to be *undefined* rather than underpowered, and only counting revealed it.
  **Count n on each side of every cut before designing anything.**
- **A gate found by scanning cut-points is a curve-fit.** If the threshold is chosen by looking, the
  result is a hypothesis, not a finding — the same standing rule that keeps the lagged-YPC result
  unshipped.
- **Interactions are the adjacent untested form** and should probably be scoped alongside: nothing has
  tested a factor that helps for a subset and hurts elsewhere, which nets to zero and reports as null
  under a single global weight.
