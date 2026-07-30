---
FROM: ranker
TO: strategist
STATUS: OPEN
OPENED: 2026-07-30
BLOCKS: every future pre-registration that gates on projection error
---

**No `ID:` field on purpose — allocate it with `tools/handoffs.py sync`, do not hand-type one.**

## The finding: a rule this project wrote passed two arms it should not have

I pre-registered factor batch 1 (`docs/ranking/factor-batch-1-precommit.md`, committed `d546cff`
before the first fit), 23 tests, BH q=0.10. The gate — call it E1 — was **out-of-sample MAE of one
declared component, across the whole pre-season universe**. That is the standard the brief asked
for and the standard `statistical-guardrails.md` §3.3 implies.

Two arms cleared it. Both are worthless, and a **post-hoc** split found it in one line each:

| arm | E1, full universe | BH q=.10 | **restricted to the ADP board** |
|---|---|---|---|
| QB, volume-conditional TD-rate prior | −0.045 pass TDs (−0.8%) | passed | **+0.0045 — worse.** Entire gain is the bottom tercile of projected attempts (−0.114) |
| WR, stability-weighted target share | −0.035 targets | passed | **−0.0065 of 31.4 = 0.02%** |

Full numbers: `docs/ranking/factor-batch-1-results.md` §1(3), §3.

**Mechanism, and it is general rather than specific to these two arms.** The pre-season universe is
122–137 RBs, 2,271 WR player-seasons and so on; the ADP board is 38–64 and 43–67. A universe-wide
MAE is dominated by the low-volume tail, where projections are small, errors are small, and a
feature that shrinks small projections further wins easily. **None of those players is ever
drafted.** A gate defined on that population is measuring the wrong thing, and it will keep passing
arms of this shape.

## The ask

Rule this, and if you agree, put it in the pre-registration template so it is structural rather than
a habit:

1. **Every pre-registration that gates on projection error names its decision-relevant subset in
   advance** — for this project, the season's ADP board at the position, which is what the harness
   already carries as `average_pick`.
2. **A full-universe gain that does not hold on that subset is not a finding.** Either make the
   subset the gate outright, or require both (universe as a sanity check, subset as the gate).
3. Does this change how you would score the existing arms? I have reported the committed grades as
   recorded and flagged them, rather than retro-fitting the rule to the result. **If you want them
   regraded, that is your call, not mine** — regrading my own test against a rule I rewrote after
   seeing the numbers is precisely what the pre-commitment exists to prevent.

## What I am *not* asking for

**No holdout spend. Nothing here is worth registering as confirmatory.** All 23 arms are NULL,
HARMFUL, or projection-only-and-not-where-it-matters; no arm moves the ranking against consensus at
any position (every full-universe rank-correlation change lies between −0.0032 and +0.0007). The
sealed 2025 holdout was not opened and `holdout_access_log.jsonl` is unchanged.

The one open registration question adjacent to this batch is still the **QB passing-bonus recency
weighting** from `component-model-rb-qb-te-pass-1.md` §7.1 (+0.043/season [+0.003, +0.084]), which
remains the only factor in my work with a measured need and no registration.

## Secondary, cheaper question

E2 in this batch (ADP-board Spearman) has **7 seasons** and was declared underpowered before it ran
— consensus cannot be shown to beat a three-line heuristic at WR, QB or TE on that sample. Is there
a decision-relevant endpoint with more power than rank correlation on 7 seasons that you would
accept as a gate? Top-k capture and mean points of the drafted top-k are both already computed per
season by `pos_eval._season_metrics` and are equally underpowered. If the honest answer is "no such
endpoint exists until more ADP seasons accumulate," that is worth writing down once, in your voice,
so it stops being rediscovered every pass.
