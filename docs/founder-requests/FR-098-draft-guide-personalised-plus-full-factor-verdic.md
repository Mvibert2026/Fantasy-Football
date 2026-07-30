---
ID: FR-098
STATUS: NEW
PRIORITY: MEDIUM (deliverable) / HIGH (the ledger feeding it)
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
A personalised Draft Guide, plus a full factor list showing which ones earned their place

Founder's own words:

> "I'd like for you to record these strategic insights, at some point, I'll ask you to produce a
> Draft Guide for me outlining all of the research and trends and giving me advice in a very
> personalized and digestible manor."

> "Including a list of every factor we checked, along with indicating the ones worth while that made
> the formula/algorithm for our proprietary rankings."

## Why it matters

Two separable things, and the first is urgent even though the second is not.

**1. The ledger (started immediately).** Findings are arriving faster than they are being
consolidated, across `docs/ranking/`, `docs/analysis/`, and individual agent reports. Reconstructing
them later means re-reading a dozen documents and re-deriving which figures were superseded — the
exact failure mode that froze `docs/status.md`. `docs/strategic-insights.md` was created this session
as the durable home, with fixed confidence grades and a rule that superseded rows are edited in place
rather than appended to.

**2. The guide (on request).** Assembled *from* the ledger when the founder asks. Not written yet.

## The gap the second half of the request exposes

**`docs/test-registry.md` tracks build status, not outcomes.** Its status key is `PORT` / `SPEC` /
`NEW` / `BLOCKED` — what we intend to test and whether code exists. There is **no column recording
what a factor was measured to be worth, or whether it earned a place in the ranking formula.**

So the founder's second ask cannot currently be answered from any single document. The verdict
information exists, scattered across analysis write-ups, and nothing joins it to the factor list.

**Required: a verdict column on the registry**, with values that mean something decision-relevant:

| Verdict | Meaning |
|---|---|
| `IN FORMULA` | Measured, earned its place against a holdout, currently used |
| `SURVIVES` | Measured and holds, not yet wired into the model |
| `MARGINAL` | Clears zero but an interval endpoint is near it — a hypothesis, not a finding |
| `NULL` | Measured, no effect |
| `BLOCKED` | Cannot be measured; name the missing data |
| `UNTESTED` | No measurement exists |

The distinction between `IN FORMULA` and `SURVIVES` is the one the founder actually asked for —
"the ones worthwhile that made the formula" is a narrower set than "the ones that worked."

## Initial read

Not the founder's own words — PM's read.

**Tone is a hard requirement, not a preference.** "Very personalized and digestible" means written
for the founder — a non-developer preparing for a specific 10-team half-PPR league with stacking
bonuses and a 4-team playoff — not a research summary with the jargon left in. Effect sizes belong in
points and roster decisions, not correlation coefficients.

**And it must stay honest under that tone.** The current honest state is that we do not beat consensus
at any position, most tested factors are null, and two of the most interesting findings are MARGINAL.
A digestible guide that quietly rounded those up to advice would be the most damaging document this
project could produce, because it would be read on draft day and acted on. §6 of the ledger records
that constraint for whoever writes it.

**Sequencing.** The ledger is maintained continuously from now. The guide is written on request, and
is worth more the later it is written — several open tests (variance term, strategy simulation,
positional volatility, bust screen) could each change what it says.
