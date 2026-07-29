---
ID: FR-030
STATUS: NEW
SOURCE: chat session 2026-07-29
RAISED: 2026-07-29
---

## Request
Run the rankings validation at maximum effort across several agents - the ultimate test

> "at some point we may want to run a few of the agents on table really high to lock in our rankings
> work at some point. Like the ultimate test. That's the core of the product so probable the most
> important thing for effort."

Founder's own words, 2026-07-29.

## Why it matters

**Rankings are the product.** Availability, the draft board and the pick recommendation all sit on
top of whether the ranking is good. It is the one place where a cheap answer costs the season rather
than a retry.

## Initial read
**Agreed. The sequencing matters more than the setting.**

**Not yet — there is nothing to validate.** The bottom-up model has not been built. The registrations
exist (PR-004, PR-005, thread 083); the model does not.

**The order:** build → run the registered test at maximum, with its decision rule already committed →
**then** Fable attacks the result at `max` before anyone believes it.

**Do not collapse the run and the review.** The agent producing a result must not be the one deciding
it survived — the reason Fable sits on a separate budget and the strategist has no database access.

Fable runs end-of-week only, so this has to be scheduled around that rather than fired when the model
happens to finish.

**The setting to use is `Ultracode`, not `Max` — and the difference matters here.** The effort scale
is `Low · Medium · High (default) · Extra · Max · Ultracode`. Max is one agent thinking as hard as it
can. **Ultracode is Claude planning and running a whole multi-agent workflow** — fan-out, independent
verification, synthesis.

For this specific job that is the correct shape. The question is not "can one agent think hard about
whether the rankings are good"; it is "does the result survive several independent attacks." A
registered confirmatory test with a pre-committed decision rule, verified adversarially, is a
workflow — not a single deep think.

**It is a session-level setting the founder turns on**, not something the PM assigns per agent, and
its own warning says it uses limits faster. That is the correct trade for the one test that decides
the product, and waste on anything else. **Do not spend it before the model exists.**
