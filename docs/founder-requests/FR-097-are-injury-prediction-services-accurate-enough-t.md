---
ID: FR-097
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Are injury-prediction services accurate enough to be worth buying?

Founder's own words:

> "how accurate are the injury sites at predicting injuries, is that worthwhile?"

## Why it matters

It is a buy decision, raised while scoping the bust screen (FR-096), where injury is one of the two
nulls any bust model must beat. If a paid service genuinely predicts injury, it feeds the bust flag,
the availability model, and the projection's games-played component. If it does not, we should stop
treating "we could buy injury data" as a live option and close it.

## What our own pipeline already says — partial answer, already measured

`docs/analysis/adp-vs-production-2026-07-30.md:199` tested **prior-season games missed** as a
predictor of ADP residual:

> Not significant. Sign order is not even monotonic, and both extreme buckets flip sign between eras
> (era A: 0-games +1.1 / 4+-games +1.5; era B: 0-games −16.8 / 4+-games −3.0). No evidence the market
> over- or under-discounts games missed, in either direction.

Prior injury history is the primary input to essentially every injury-risk product. In our data it
carries **no exploitable signal about who beats or misses their ADP**, and the effect does not even
order sensibly.

**The important distinction, which this result does not settle:** "the market misprices injury
history" and "injury history predicts injury" are different claims. The null above is on the first.
The market could be pricing a real effect correctly — in which case injury data is accurate and
still worth nothing to a drafter, because the edge is already in the price. For a *drafting*
decision both roads lead to the same place; for the *projection's* games-played component they do
not, and that distinction should survive into the answer.

## Initial read — the test that makes this answerable

Not the founder's own words — PM's read.

**"How accurate are they" is the wrong question as posed, because almost nothing published is
falsifiable.** Injury-risk content is typically framed as tiers or narrative ("elevated risk"),
issued without a dated, checkable prediction, and reviewed after the fact against outcomes everyone
already knows. The answerable questions are:

1. **Does the service publish dated, specific predictions before the season, in a form that can be
   scored?** If not, its accuracy is unmeasurable by anyone including its publisher, and that alone
   is close to a decision.
2. **Has anyone independently scored it against a base rate?** "70% of our high-risk players got
   injured" is meaningless without knowing what share of *all* players got injured. If the base rate
   is 60%, that is noise.
3. **Does it beat prior-season games missed?** That is the free baseline, and our data says it is
   worth approximately nothing. A paid product must clear the free one.

## Also worth settling in the same pass

`nfl.db.injuries` (79,816 rows) is read by no model, and `ranker` measured why: it captures 26–35%
of short absences but only 2.5–4.8% of absences of nine games or more, because season-ending IR
removes a player from the weekly report. **The absences that destroy a season are the ones it cannot
see.** If an external source covers precisely that gap — season-ending injuries, dated, before the
fact — it is worth substantially more than a generic risk score. That is the specific thing to look
for.
