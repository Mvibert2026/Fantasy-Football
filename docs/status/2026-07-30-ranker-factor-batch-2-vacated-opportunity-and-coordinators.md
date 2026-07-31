# 2026-07-30 — ranker — factor batch 2: vacated opportunity on real rosters, coordinator continuity

**Task.** Build the two factors behind the founder's own two examples of what a bottom-up ranking
should be able to *say* — "so and so has a new OC" (registry #29) and "the starter from last year
left" (registry #28) — and decide whether either earns the right to render an insight sentence.

Main checkout, branch `claude/pm-agent-setup-gobxa0`, no worktree.

---

## What happened, in order

**1. Found the coordinator table missing.** `play_callers` is not in `data/nfl.db`. The 607 rows
data-ops ingested at 04:29 (`6ba3887`) are gone, along with the `data/raw/wikipedia/` cache, because
`play_callers` is not in `scripts/rebuild_database.py` and the DB was rebuilt at 19:39. Reported to
data-ops as a rebuild-path defect, not a one-off.

**2. Established that end-of-season staff cannot answer #29, and that the obvious fix fails.**
Thread `101` had left backend a choice between restricting to teams with no in-season change, or
reconstructing start-of-season staff from Wikipedia revision history. Option (b) works but **not the
way that thread describes it**: re-running the `{{NFL final staff}}` parser on pre-Week-1 article
revisions returns **0 of 32** team-seasons, because "final staff" is a static block editors
substitute in *after* the season. What the in-season article carries is a `==Staff==` section
transcluding the club's **live** navbox. So the preseason name needs **two** revision-dated reads per
club-season. Built as `experiments/bottomup/factors/coord_preseason.py` → `play_callers_preseason`,
2012–2024, all 32 clubs, 803 OC+DC rows. `redirects=1` turned out to be required, not cosmetic —
without it 28 team-seasons came back empty for exactly four renamed franchises, a non-random hole.

**3. Measured the batch-1 contamination before writing the design.** Depth chart vs. `rosters_weekly`
on prior-season producers (≥50 carries or ≥50 targets, 2014–2024, n=2,166): the depth chart calls
**91 (4.2%) departed while the roster still has them under contract**, 40 of them on reserve/injured.
That is the leak channel `factor-batch-1-results.md` §4 hypothesised, counted rather than argued.

**4. Pre-registered, then corrected the registration twice — both times before fitting.**
`docs/ranking/factor-batch-2-precommit.md`, content committed `851a6bb` at 20:00:54 before any arm
was fitted. Amendment A: V4 was ambiguous for a player who moved clubs. Amendment B, the important
one: **I had made the ADP-board metric the FDR family and stated it at 11 seasons; it is 7**, because
the consensus board only exists 2018–2024. A 15-arm BH family on 7 seasons returns all-NULL
regardless of the truth. Moved the family back to the full-universe endpoint (also keeping batch-1
comparability) and demoted the board metric to a required direction check, with a new grade
**BOARD-NEUTRAL** naming batch 1 §1(3)'s failure mode in advance.

**5. Ran the campaign once. 15 arms, BH q=0.10, holdout untouched.**

---

## Results

**#28's harm was a proxy artifact — and the factor is still NULL.** Both halves are true.

| | V1 depth chart (batch 1) | V2 real rosters | V2 − V1, paired |
|---|---|---|---|
| RB `carries` | +0.2031 HARMFUL | **−0.0123 NULL** | **−0.2154 [−0.3003, −0.1384], p = 0.0006** |
| TE `targets` | +0.0448 HARMFUL | +0.0153 NULL | −0.0295, p = 0.056 |
| WR `targets` | +0.0818 NULL | +0.0284 NULL | −0.0534, p = 0.362 |

V1 reproduces batch 1 to four decimals. In the high-measured-vacancy bucket the RB harm goes
**+0.770 → +0.064**, confirming the mechanism batch 1 predicted. Two further constructions (absence
share; the first genuinely *player-level* vacancy feature, opportunity vacated **above** a player)
are also NULL. Nine cells, zero wins.

**#29 is ungated and NULL.** `oc_known` is 0.995/0.992/0.997 on the ADP board — far above the 0.80
gate committed in advance, so this is a real test, not a data failure. WR −0.006 (p=0.71), TE −0.003
(p=0.87), RB +0.093 (p=0.29), board metric positive at all three. Not underpowered: the OC changes
for **46–48% of board player-seasons**.

**The `coach_id` join works.** 53 of 126 named OCs (42.1%) appear for 2+ clubs, covering 243 of 400
club-seasons, **zero** same-season name collisions. But only **17.9%** of OC changes bring in someone
who was an OC elsewhere last year — that bounds any future tendency-following signal (#30) at one
change in six, before anyone spends on it.

**My own escape hatch fired on my own arm, and it was right to.** M1 ("this player moved clubs")
cleared BH at all three positions with the largest effects in either batch (WR −2.40%, TE −1.73%,
RB −1.91%; two SURVIVES). WR's −2.40% breached the 2%-of-primary-error trigger I registered as a
suspected-leak threshold. Decomposition: **95–97% of the effect is `move_known`** ("he is on some
club's Week-1 roster"), and `moved_club` — the variable the arm is named after — does nothing
anywhere (p = 0.28 / 0.62 / 0.12). I introduced this by adding `move_known` as a companion flag by
analogy with batch 1's `vac_team_known`, which was computed but never entered a model. Registered
grades stand as recorded with the correction attached; how to record them is a `strategist` ruling,
escalated, not mine. **Excluding that arm the batch is 12 NULL-or-worse out of 12.**

---

## The deliverable the founder actually asked for

**Nothing in batch 2 earns the right to render an insight sentence, and that is the answer.**

`new_oc` is true for **46–48% of every ADP board** (187/391 WR, 167/357 RB, 49/106 TE). A "new OC,
expect more" line would have attached a **NULL** mechanism to half of every draft board — the same
failure the recommendation card was caught committing, at ten times the surface area. Directional
wording ("routes up") was never licensed either: nothing here measures routes and route
participation is not in `nfl.db` at all.

---

## Threads opened, both OPEN

| to | subject |
|---|---|
| `strategist` | register the design; three rulings escalated — how to record a confounded pre-registered arm, whether `move_known` (worth 1.6–2.3% of component MAE, larger than anything either batch produced) belongs to the availability sub-model, and whether the 2% trigger is calibrated |
| `data-ops` | `play_callers` is empty and the rebuild path is why; thread `101`'s option (b) answered with the two-read finding; keep the two coordinator tables separate |

## Evidence

Commits `70bc893`, `fe3b66a`, `5d3e95e`, `df50e3b`, `da10906`, `dbc52a5`, plus this session's
registry/ADR update. **ADR-067.** 12 tests pass (10 new), including bit-for-bit reproduction of batch
1's feature frame under the extended builder. **Sealed 2025 holdout not opened; no holdout spend
requested.**

Artifacts: `docs/ranking/factor-batch-2-precommit.md`, `docs/ranking/factor-batch-2-results.md`,
`experiments/bottomup/results/factor_batch2_results.csv`, `_m1_decomposition.txt`,
`_diagnostics.txt`, `_coach_join.txt`.

Six untested candidates appended to `docs/ideas-inbox.md`, including the one that most plausibly
explains every null vacancy arm this project has run: **it counts who LEFT a club and has never once
counted who ARRIVED.**
