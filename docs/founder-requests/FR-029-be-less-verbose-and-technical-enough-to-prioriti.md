---
ID: FR-029
STATUS: NEW
SOURCE: chat session 2026-07-29
RAISED: 2026-07-29
---

## Request
Be less verbose and technical - enough to prioritise, then confirmation it is fixed

> "generally be less verbose and technical with issues really I need to understand just to help
> prioritize and, then that it's fixed."

Founder's own words, 2026-07-29.

## Why it matters

He is the CEO, not an engineer. What he needs from a problem report is **how bad, how urgent, and
what it blocks** — enough to decide where it sits in the queue. Then, later, that it is done.
Everything between those two points is the PM's job to hold, not his to read.

This has been asked for repeatedly in different words — "I'm the CEO, not in the code", "be brief",
"English, not identifiers" — and the PM keeps drifting back into explaining mechanism. Explaining
*why* a thing broke is usually the PM reassuring itself, not informing him.

## Initial read
**The rule: two sentences for a problem, one line when it's fixed.**

- **Reporting a problem:** what it stops him doing, and how urgent. Not the cause, not the file, not
  the mechanism. If he asks why, then explain.
- **Reporting a fix:** that it's fixed, and anything he should now do differently. Nothing else.
- **Keep the depth in the repo**, where the agents read it — session logs, ADRs, the triage docs.
  Nothing is lost by leaving it out of chat; it is lost by never writing it down.

**The exception, and it is narrow:** when he is being asked to make a decision, he needs the trade-off
in full. Brevity is about *reports*, not about *decisions*. A one-line summary of a choice that
costs money, publishes data, or closes off an option is under-informing him, not respecting his time.

Also applies to length generally, not just problem reports. Recorded in `docs/pm/CHARTER.md`.
