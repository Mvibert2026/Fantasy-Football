# PM operating discipline

**Written 2026-07-27**, prompted by a founder challenge that was correct:

> "Who is looking out for this stuff? Just general program and project stuff — should be you thinking
> about this and solving for it before I do."

He was right. In this session the founder personally caught: backlog rot, the absence of a
contradiction check, a suggester regression that had been marked resolved, and a large draft-board
gap against the design. Every one of those is a PM responsibility and every one reached him first.

This document diagnoses why and specifies the mechanisms. It is deliberately structural — the
project's own standard is that guardrails beat habits, and "the PM will be more vigilant" is a habit.

---

## Why it happened — five distinct causes, not one

**1 · The PM cannot see the running application.** Every UI defect in this project's history has
originated from a founder screenshot. This is a structural blindness rather than an attention failure,
and it means that on anything visual, **the founder is currently the sensor.** That is the single
biggest cause and the one most worth fixing.

**2 · "Resolved" means an agent said so.** Thread 051 was closed. The behaviour it was closed against
still fails. There is no acceptance step between an agent's self-report and a thread being marked
done, so a confident agent and a working feature are indistinguishable in the mailbox.

**3 · The PM never audits its own output.** Threads 044 and 059 duplicated each other within an hour,
written by me, with no pass where I re-read new threads against existing ones before dispatch.

**4 · Nothing runs when the founder is silent.** The PM is reactive by construction — it responds to
messages. There is no loop that asks "what is rotting?" in the absence of a prompt. Sixty-two threads
accumulated before anyone looked at the pile, and the person who looked was the founder.

**5 · The PM is the least-checked component in the system.** It writes the threads, sequences the
rounds, decides what is verified, and authors the documents asserting that the system works. Every
other role has someone reading its output. This one does not.

---

## Mechanisms

### M1 · Founder-reported defect register — the important one

A tracked table of every defect the founder reports personally: what it was, the round it was
reported, the round it was verified fixed, and **whether it had been reported before.**

This exists to make one specific thing mechanically visible: **the founder catching the same problem
twice.** That is a process failure, not a bug, and it currently leaves no trace anywhere. The
suggester is the live example — reported, closed, still broken, reported again, and nothing in the
system registered that as significant.

Two derived numbers, reported at every sprint closeout:

- **Repeat rate** — defects reported more than once. Target zero; any non-zero value is a failure of
  M2 below.
- **Detection source split** — defects found by the founder versus found by the project. If the
  founder's share is not falling over time, FR-002 is not being served regardless of what else
  improves.

### M2 · Acceptance evidence, distinct from agent self-report

A thread affecting observable behaviour cannot be marked `RESOLVED` on an agent's word alone. It
requires one of:

- A test asserting the specific behaviour, enumerated trigger by trigger where relevant — the pattern
  now specified in thread 063.
- A screenshot of the changed surface.
- An explicit, recorded statement that neither was possible, with the reason.

**The third option is acceptable and the current silence is not.** "Screenshots failed in the sandbox"
is a legitimate outcome that leaves a trace; a thread quietly closing with no evidence is not.

### M3 · Pre-dispatch check by the PM

Before any round is dispatched, the PM re-reads every newly written thread against the open set and
the recently closed set. Mechanical support arrives with the checks specified in thread 062 —
file-boundary overlap, contradiction heuristics, re-request of resolved work — but the discipline does
not wait on the tooling.

This is a five-minute pass that would have caught 044/059, and 054/055/057.

### M4 · Fix the sensor — the highest-value item here

While the PM cannot see the app, the founder will keep finding UI defects first, and no amount of
process fixes that. Priorities, in order:

1. **A cheap, repeatable screenshot protocol at the end of every frontend round** — not requested
   ad hoc when something looks wrong, but standing. Thread 007's fidelity harness is the existing
   vehicle; it has never been made routine.
2. **Agent-run visual verification** where the sandbox permits it, with failure reported explicitly
   rather than silently skipped.
3. **A fidelity comparison against the design reference**, so drift is detected by diff rather than by
   the founder noticing that a screen looks worse than the mock.

Until at least the first exists, the PM should say so plainly when reporting on frontend work rather
than describing unverified changes in the language of completion.

### M5 · Standing PM self-audit at every sprint boundary

Not prompted. At each boundary, the PM answers in writing:

- What did the founder catch that the project should have?
- What is stale, contradictory, or superseded?
- Which threads are older than two rounds and why?
- What did I assert last round that turned out to be wrong?

Short, written, and appended to the sprint record. The value is the fourth question.

### M6 · The PM gets reviewed

Already specified — the Fable mandate § 2.2 asks directly whether the PM is adding value or ceremony,
and instructs that the PM's own documents be treated as advocacy. **That section stays in every future
Fable mandate**, and this document is explicitly in scope for it.

---

## What this does not fix

The PM remains reactive between sprints. A genuinely proactive PM would notice problems mid-round
without being prompted, and nothing above achieves that — M5 fires at boundaries, not continuously.

Stating it rather than implying the problem is solved. If the founder keeps finding things between
boundaries, the honest answer will be that the cadence is too coarse, and the fix will be a shorter
one rather than a promise.
