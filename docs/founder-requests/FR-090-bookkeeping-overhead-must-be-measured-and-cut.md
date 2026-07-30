---
ID: FR-090
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Bookkeeping overhead must be officially raised, measured, and investigated

Founder's own words, on being shown that bookkeeping consumed as much effort as frontend work:

> "What you flagged from a book keeping perspective needs to be officially raised and investigated"

## Why it matters

PM raised this as an aside in a cost report and then left it as an observation. The founder
correctly escalated it. An observation nobody owns is exactly the failure this ticket is about.

The measured facts that triggered it, all from 2026-07-30:

| Finding | Source |
|---|---|
| 2 of 9 agent dispatches (22%) were pure bookkeeping — equal to frontend | `docs/cost-log.md` |
| 24 of 38 older threads needed no action at all | `docs/handoffs-triage-2026-07-30.md` |
| 50 of 75 founder requests marked NEW; at least 5 confirmed already shipped | `docs/founder-requests/INDEX.md`, build-state audit |
| Numbering collided twice in one session (FR-072, thread 096) | This session |
| `tools/handoffs.py check` is RED and is a test nobody acts on | `tests/test_handoffs.py::test_mailbox_health` |

## Initial read

Not the founder's own words — PM's read.

**The hypothesis worth testing is structural, not behavioural.** FR-072 diagnosed thread hygiene as
four fixable mechanisms. That diagnosis may be treating symptoms. The deeper question:

**This project maintains at least nine parallel tracking surfaces** — `docs/handoffs/`,
`docs/founder-requests/`, `docs/status/`, `docs/decisions.md`, `docs/CURRENT-STATE.md`,
`docs/ideas-inbox.md`, `docs/deferred.md`, `docs/test-registry.md`, and two HTML dashboards. Each
must be manually reconciled against the others. Every one has drifted at least once. Two are already
frozen because they became untrustworthy (`docs/status.md`, `docs/founder-requests.md`).

For a **single-user, single-founder project**, that is a plausible over-engineering finding rather
than a discipline problem — and `CLAUDE.md` §8 makes flagging over-engineering an explicit mandate,
not an optional critique. Nine tracking surfaces for one user is the kind of thing that gets built
because each addition was individually justified.

**The investigation must be allowed to conclude "delete this."** An investigation that can only
recommend better upkeep of all nine surfaces has assumed its answer. For each surface the live
question is: who reads it, when, and what decision changes because of it? A surface with no reader
is overhead regardless of how well maintained it is.

**What must not be lost.** Some of this apparatus exists for real reasons that predate the mess:
inter-agent communication genuinely cannot rely on a human relay; founder requests genuinely vanish
if not written down; `CURRENT-STATE.md` genuinely stops agents trusting stale status logs. The
investigation has to separate load-bearing from ceremonial rather than treating volume as the
problem.

**Sequencing.** Ahead of FR-072's mechanical fixes, because if a surface is going to be deleted there
is no point building a `DONE-PENDING-CONFIRM` state for it first.
