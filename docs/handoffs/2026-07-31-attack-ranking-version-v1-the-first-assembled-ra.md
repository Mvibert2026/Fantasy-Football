---
ID: 2026-07-31-attack-ranking-version-v1-the-first-assembled-ra
FROM: ranker
TO: fable
STATUS: OPEN
BLOCKS: the 2025 holdout (CLAUDE.md 6.3: does not open until fable has run); any decision to invest further in bottom-up before 7 September
OPENED: 2026-07-31
---

## Ask

**Attack ranking version v1 at maximum effort.** It is the first ranking version this project has
ever assembled or tested, and `CLAUDE.md` §6.3 as ruled today makes your run the named precondition
for unlocking the 2025 holdout. Nothing about v1 has been checked by anyone other than me.

Artifacts, in the order I would read them:

| what | where |
|---|---|
| pre-commitment, committed **before** the runner existed | `docs/ranking/ranking-v1-precommit.md` (commit `5ffbbef`) |
| config blob, sha256 `ab15cb93467b4f3f…` | `experiments/bottomup/ranking_versions/v1.json` |
| results | `docs/ranking/ranking-v1-results.md` |
| runner | `experiments/bottomup/ranking_v1.py` |
| post-hoc sensitivities | `experiments/bottomup/ranking_v1_sensitivity.py` |
| new baseline loader (§6.5 baseline #2 had never had one) | `experiments/bottomup/components/ecr_baseline.py` |
| the one change to the audited harness | `experiments/bottomup/components/pos_eval.py` — `extra_universe_fn`, default `None` |
| raw per-season output | `experiments/bottomup/results/ranking_v1_*.csv` |

**The headline is a loss, so the usual "too good to be true" heuristic points the wrong way here.**
v1 beats the two trivial §6.5 baselines decisively at RB and WR and **beats neither crowd at any
position**. The failure mode to hunt is therefore the inverse of the usual one: **a null or a loss
manufactured by a defect.** One already happened in this pass (§9 of the results doc) and I caught it
only because the NaNs were total.

### Five specific attacks I want, in priority order

**1. The §3.2 margins over B3/B4 are partly borrowed, and I have not quantified how much.**
This is the weakest number in the document and I am naming it first on purpose. v1 pins rookies to
their consensus slot (10–18% of rows depending on position and panel). B3 (prior-season points) and
B4 (tier heuristic) have *no* rookie information — a rookie's `pts_1` is 0, so both baselines dump
every rookie at the bottom. **So part of v1's advantage over B3/B4 is consensus information injected
through the rookie channel, not model skill.** The clean test: re-run §3.2 with rookie rows dropped
from the universe, or with B3/B4 given the same consensus pin. I did not run it. If it eats the RB
and WR margins, §3.2 is wrong as written.

**2. Is `extra_universe_fn` bit-for-bit inert when unused?** I added one optional field to
`pos_eval.WalkForward` so the ECR board could define an evaluation universe without duplicating the
audited harness. It defaults to `None` and I believe it reproduces batches 1–7 exactly (17 tests pass,
4 skipped). **Verify that rather than believe it.** If it is not inert, every batch-1-to-7 number is
in question, not just v1's.

**3. The look-ahead surfaces, of which there are three new ones.** (a) `ecr_baseline.load_ecr`
re-asserts each row's `as_of_date` is strictly before that season's measured Week 1 kickoff, and
serves only `is_preseason_final = 1` — check the kickoff source (`snap_counts.pfr_game_id`) actually
covers 2018–2024 and that the fallback (`Sep 1`) can only reject, never admit. (b) The rank-space
rookie assembly reads `entry`, which comes from `universe_for` — confirm `entry` cannot be
contaminated by target-season data. (c) `extra_universe_fn` returns ECR board membership for the
target season; board membership is a pre-kickoff fact, but I am asserting that, not proving it.

**4. Survivorship.** Universes are frozen pre-season from board membership; 73 zero-game
player-seasons retained in the market panel and 182 in the expert panel, all at 0 points, no games
filter. But the expert panel's universe is the *intersection* of the ECR board and what
`universe_for` admits — **if `universe_for` drops anyone the ECR board lists, the expert panel is
quietly survivor-filtered and every panel-E number moves.** I did not measure the drop rate. Please
do.

**5. The depth-matched sensitivity (§5) is the most attackable thing in the document.** It is
post-hoc, it is labelled post-hoc, and it flips WR from a significant loss to parity. I argue it is
*closer* to strategist's `C2` endpoint than the pre-registered full-board panel. **That is exactly
the argument a motivated analyst makes.** Strategist has it as an open question
(`2026-07-31-ranking-version-v1-tested-end-to-end-review-the`); an independent attack on it is worth
more than my defence of it.

### Also fair game

- The pre-commitment predicted QB and TE would trip the power rule in panel M. TE did, QB did not,
  and QB then turned out to be the one cell where the pre-registered MDE proxy is wrong by 2×. I
  report this in §4 rather than switching measures — check that I have not switched measures anywhere
  else.
- Bootstrap p-values at **n = 4 seasons** (panel E) produce `p = 0.0002`. That is the percentile
  bootstrap's floor behaviour on four highly-consistent paired differences, not strong evidence in
  the usual sense. I flagged the season count everywhere but did not down-weight the p-values.
- `fantasypros_ecr` has `scoring_format = NULL` on all 2,948 rows. The format those ranks were
  produced under is unrecorded, and the whole expert-crowd panel rests on it.

## Why

`CLAUDE.md` §6.3 now names your run as the gate on the 2025 holdout, and the holdout is spendable
once. Review overturned three things today that would otherwise have been carried into a holdout
test. v1 is the first artifact in this campaign shaped like the thing the founder actually asked
for, with 38 days left, and a decision to keep investing in bottom-up or to stop will be made off
this document. **If it is wrong, it is worth more to know now than in September.**

Your mandate explicitly covers over-engineering as a finding. v1 is ~500 lines of new code producing
a result that says "do not ship this." If that judgement is right, say so; if the whole exercise was
avoidable, that is also a finding.

## Done looks like

A reply on this thread stating, per claim: sustained / overturned / unresolved. Specifically —
(1) does the rookie-pin channel account for the §3.2 margins; (2) is `extra_universe_fn` provably
inert; (3) do the three new look-ahead surfaces hold; (4) the ECR-board drop rate through
`universe_for` and whether panel E is survivor-filtered; (5) admissible or rescue on §5. Plus
anything I did not think to ask about — that is the part I cannot specify.
