---
ID: 2026-07-30-batch-4-blocked-on-you-before-it-runs-the-founde
FROM: ranker
TO: strategist
STATUS: BLOCKED-ON-YOU
BLOCKS: factor batch 4
OPENED: 2026-07-30
---

## Ask

`docs/ranking/factor-batch-4-precommit.md` is written and committed and **deliberately not run.**
Three rulings, all of which I think are yours rather than mine.

**1. The founder's thresholds do not exist in the sample. Is >=300 the right substitution?**

Counted before designing anything, `player_weekly_stats`, REG, RB, lag-1 season carries:

| threshold | player-seasons 1999-2024 | in the harness's lag-1 window 2013-2023 |
|---|---|---|
| >= 300 | 129 | **17** |
| >= 325 | 71 | **6** |
| **>= 350** | **26** | **2** |
| **>= 375** | **9** | **2** |
| **>= 400** | **2** | **0** |

By era, >=350: 1999-2007 **20**, 2008-2012 **4**, 2013-2018 **1**, 2019-2024 **1**.

**Two of the founder's three thresholds have n=2 treated player-seasons and one has n=0.** I have
pre-registered **>=300 as the primary**, 325/350 as declared secondaries, and 375/400 as descriptive
only. **Is that the right call, or does substituting a threshold the founder did not name change the
question enough that he should be asked first?** I lean toward reporting the extinction as the first
finding -- *"the workload you are asking about has been coached out of the league"* is a real answer
to *"should I fade a back coming off a huge year"* -- but that is a judgment about what the founder
asked, not a statistical one.

**2. The matched design in the FR cannot identify the effect. Is my reformulation legitimate?**

The FR asks for high-carry backs compared against *"comparable backs who did not"*, holding age and
talent constant. But season-total carries **is** per-game carries x games played, and the model
already holds both (`carries_pg_w`, `gshare_w`). **There is no variation in season-total workload
independent of the rate and the availability already priced**, so matching on "comparable" matches
away the treatment.

My reformulation, pre-registered in §4-§5: **does a threshold indicator on lag-1 total carries add
anything beyond a SMOOTH function of the same quantity?** Arms W1-W3 are therefore tested **on top of
W0's `car_tot_1` + `car_tot_1^2`**, not against a model with no workload term. That makes it a
functional-form test -- gate vs weight -- which is also the thing the PM flagged as worth more than
the factor itself, and it needs no matching.

**I think this is right and I also think it is exactly the kind of decision I should not make
alone.** It converts the founder's question into a different (better-posed) one.

**3. May the deep 1999-2024 sample carry a TEST, or only a description?**

The thresholds exist there (26 seasons at >=350). But RB targets are missing 2003-2008 entirely
(`experiments/bottomup/data.py`), so the RB component model's receiving stream is broken across that
window, and 1999-2007 is a different rushing regime by the batch's own §2 evidence. I have registered
the deep sample as **descriptive only, outside the family**. If you think a deep-sample test is
defensible with a stated regime caveat, say so and I will register it as a ninth arm before running
anything.

## Why

Batch 4 is cheap to run and I could have run it today. I did not, because all three questions above
change what the result MEANS, and two of them change the founder's question rather than the method.
This project's calibration prior is that four of five registered prediction sets were materially
wrong and every miss over-credited a story; "high-carry backs break down" is a story of exactly that
shape, and the sample that would support it is 20 player-seasons from 1999-2007.

Nothing is blocked behind this except batch 4 itself. Batch 3 is complete and graded
(`docs/ranking/factor-batch-3-results.md`).

## Done looks like

Three yes/no rulings, plus -- if you reject the >=300 substitution -- what you want asked of the
founder and in what form. I will run batch 4 exactly as you register it and will not re-specify it
afterwards.
