---
ID: FR-2026-07-31-availability-and-qb-tilt
STATUS: NEW
SOURCE: PM session 2026-07-31, founder chat — spotted by eye from the rankings chart
RAISED: 2026-07-31
PRIORITY: HIGH — the second is a direct conflict with a measured finding
NEEDS: ranker (1), strategist (2)
---

## Request

> "From looking at the rankings I can tell you our rankings has an issue with injuries. Not sure if
> that's from the data or an assumption in the model.
>
> Second - why is our adjusted consensus ranking quarterbacks so high?"

**Both confirmed by measurement within minutes of him asking. He found both by eye, from a chart, in
under a minute.**

## 1 — Availability. An assumption in the model, not the data

Measured on v1's own 2024 output, `ranking_v1_v1_players.csv`:

| Prior-season games | n | Mean prior | Mean projected games |
|---|---|---|---|
| ≤ 8 (mean 2.2) | 277 | 2.2 | **5.9** |
| ≥ 16 (mean 16.5) | 134 | 16.5 | **12.7** |

**The games projection shrinks brutally toward the middle in both directions.** A player who was
essentially absent last season is projected for nearly six games; an iron-man who played 16+ is
projected to **miss more than four**. The model barely distinguishes the chronically unavailable from
the durable.

**The consequence is visible in the board's own largest disagreements.** v1's biggest positive moves
against consensus are Taysom Hill (+194), DeAndre Hopkins (+157), Elijah Moore (+160), Kareem Hunt
(+142), DeMario Douglas (+170) — a list dominated by small-sample, aging, or backup-usage players.
A high per-game rate from a handful of games, multiplied by an over-generous games projection,
produces exactly this.

**Three things make this a systemic failure rather than one bad parameter:**

1. The games projection is over-shrunk in both tails (above).
2. **Injury designations were measured NULL at ranking level** — the one feature built to address this
   does nothing (batch 2, arms D/E).
3. **The backtest could not have caught it.** Until today's fix, a drafted player who never took a
   snap scored as *replacement level* rather than a disaster — so the harness systematically
   under-penalised exactly this error. The defect and the symptom are the same story.

## 2 — The QB tilt, and it contradicts this project's own strongest strategy finding

**It is not a blanket tilt.** Across the top 150 the mean QB shift is **−2.1 places** — the board
ranks most quarterbacks *later*. The tilt is concentrated violently at the top:

| Player | Consensus | Market ADP | **Adjusted board** |
|---|---|---|---|
| Josh Allen | 27 | 27 | **6** |
| Lamar Jackson | 34 | 54 | **13** |
| Drake Maye | 41 | 50 | **22** |
| Joe Burrow | 46 | 52 | **31** |

That is the mechanism working as designed: with a QB10 replacement level in a 10-team 1-QB league,
the surplus over replacement for the top few quarterbacks is enormous, then collapses.

**But it puts Josh Allen at overall 6 — round 1.**

`docs/preregistration/PR-003` measured that **reaching for a quarterback in the first three rounds was
the single most costly strategy tested**: negative in **12 of 12** cells, point estimate −115.4 at
σ=10, CI [−176.3, −54.4], simulated from **slot 3 of a 10-team snake — the founder's exact seat**.

So the board's largest proprietary claim and the project's strongest measured strategy finding
**point in opposite directions**, and nothing in the system reconciles them. This is the consistency
failure the founder named on 2026-07-30 — *"if we say don't take a qb early then suggest one in second
round it doesn't make sense"* — appearing again at the board level rather than the recommender level.

**It also inverts a prediction on file.** PR-007 §8.2 predicted the recommender's −25 early-QB penalty
should be **deleted as redundant**, on the reasoning that VBD against a QB10 baseline already
suppresses QB value. The measurement says VBD does the **opposite** at the top of the position: it
*inflates* elite quarterbacks by roughly 20 places. Any deletion decided on that reasoning would be
decided on a false premise.

## What is needed

Neither is a fix to make quietly. **1** is a modelling decision about how games-played should be
projected and whether per-game rates from tiny samples should be trusted at all. **2** is a
methodology question — which of two measured things is right, or whether both are right and the
board's VBD is answering a different question from the draft simulation.
