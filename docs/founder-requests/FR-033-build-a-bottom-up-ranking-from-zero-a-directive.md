---
ID: FR-033
STATUS: NEW
SOURCE: chat session 2026-07-29
RAISED: 2026-07-29
---

## Request
Build a bottom-up ranking from zero - a directive, not an open question

> "For bottoms up, I'm not asking if we should have a bottoms up ranking. I'm telling you to develop
> one. We have so many things to test to see if they are useful or not. I want to kind of start our
> own bottoms up ranking work from 0. As if we've hired somebody high level with fantasy football
> expertise. Only job."

Founder's own words, 2026-07-29.

## Why it matters

**This closes a framing the project kept reopening.** Every piece of work on bottom-up so far was
scoped as *should we*: timebox it, run one test, stop regardless, registered prediction STOP. That was
methodologically defensible and it was answering a question the founder had not asked.

He is not asking whether a bottom-up ranking is worth having. **He is saying build one, and expect to
test many things to find the few that work.** Those are different projects. The first produces a
verdict; the second produces a product.

**It is also the only route to a real edge.** The shipped board is consensus-derived at player level —
every player at the same positional consensus rank gets an identical projection, so it cannot
disagree about any individual player. Its only edge channel is positional revaluation, and Yahoo's
paid tool competes that away against anyone who pays. Bottom-up is the thing that can hold an opinion.

## Initial read
**A new agent, `ranker`, created 2026-07-29** — opus/xhigh, single-purpose, the fantasy football
expert whose only job is this.

**He asked whether to build a new agent, extend strategist, or add alongside it. A new one, and the
reason is structural:** strategist's entire value is that it does not build. If it designs the
rankings it cannot check them, which is the same principle that keeps Fable on a separate budget. So
three independent layers rather than two roles in one:

| Role | Job |
|---|---|
| `ranker` | Builds it. Owns features, projections, the factor registry. |
| `strategist` | Designs and reviews the methodology; registers every confirmatory test **before** it runs, with the stopping rule committed in advance. No database access, on purpose. |
| `fable` | Attacks the result afterwards, at max, weekly budget. |

`backend` owns the shipped pipeline — when the model is ready, that is a handoff, not a merge the
ranker performs.

**The constraint that shapes everything, and it should not be rediscovered:** usage features carry the
real signal and only exist from **2009**; targets are missing 2003–2008 entirely. Box-score features
go back to 1999 but that model is already at rough parity with prior-season rank. **The deep sample
supports only the weak features; the strong features have about thirteen seasons.**

**And a live defect it must not inherit:** the shipped rank curve pools all seasons flat, which is
how a quarterback premium that had collapsed to near zero still showed as a +20 signal. Nobody has
checked whether the same is happening at other positions. That is one of the first questions, not a
detail.
