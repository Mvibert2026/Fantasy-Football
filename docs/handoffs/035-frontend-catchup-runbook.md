---
ID: 035
FROM: pm
TO: founder, frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 003, 027, 028, 029, 030, 031, and every future frontend thread
---

## The problem

Frontend is the bottleneck and it is not close. Design has delivered **seventeen specified states**
across three handoffs. Frontend has built **none** of them, has not run once this session, has never
answered thread 003, and has no recorded test count anywhere in this repository.

Worse, it structurally **cannot** participate in the operating model. Everything installed today —
`CLAUDE.md`, the six agents, the mailbox, `CURRENT-STATE.md`, the fidelity harness, the pinned design
reference — lives in *this* repository. The frontend code lives somewhere else entirely, on branch
`frontend-prep` at `7276a2d`. A Claude Code session is scoped to its directory, so a session opened in
the frontend working copy sees none of it, and a session opened here cannot touch frontend code.

So the queue of frontend threads is unreachable by the agent meant to work them.

## Step 1 — decide where frontend code lives. Founder decision.

**Recommended: move the frontend into this repository as a subdirectory** (`frontend/` or `ui/`).

Why:
- One mailbox. Frontend threads become reachable, and backend↔frontend handoffs stop needing a human.
- One `CURRENT-STATE.md`, so the frontend test count finally exists somewhere.
- The fidelity harness can reference `docs/design-reference/` by relative path instead of duplicating
  the pinned PNGs into a second repo where they will drift.
- Contract changes and their frontend consumers land in the same commit, which is the actual fix for
  "the export path changed and nobody told the frontend."

Cost: one merge, and history from `frontend-prep` either grafted or archived. Do this **after**
thread 013 resolves the tracked-database question — do not merge into a repository whose git state is
still unknown.

The alternative is copying `.claude/`, `CLAUDE.md`, and the mailbox into the frontend repo. That works
and is faster, but it creates two copies of the operating model, and the first time they diverge
nobody will notice. I would not.

## Step 2 — audit before building. Thread 031.

Once frontend is reachable, **031 runs first and alone.** Nobody knows what the running app actually
contains. Two screens were previously reported complete and were absent entirely. Building on top of
an unknown baseline repeats that.

The audit output — `docs/frontend-audit-2026-07.md`, one verdict per spec element — is what turns the
rest of this list into a real plan rather than a guess.

## Step 3 — build order, once the audit is in

1. **029** — frequency array on Board badges. Smallest, uses an existing component, and puts the
   product's signature honesty feature on the screen users actually live on.
2. **028** — Predictions tab. Not blocked by anything; the availability model already produces what it
   needs.
3. **027** — Opponents tab. Waits on thread 016's rosters export.
4. **030** — inline "why our rank differs". The most evidence-backed change in the queue.
5. **Settings editor** — six states, and it needs thread 026's stage names first.
6. **Mock Lab** — seven states, needs thread 025's backend.

Small and unblocked first, deliberately. Frontend needs demonstrated throughput before it takes on a
seven-state screen, and the project needs to see a screenshot that matches a design.

## Step 4 — stop the gap reopening

- **Every** frontend session ends with a screenshot. Not negotiable, and now the reason is empirical
  rather than theoretical.
- Wire the fidelity harness (thread 007) as soon as the audit lands. It is written and tested; it
  needs a running app to point at.
- Record the frontend test count in `CURRENT-STATE.md` at the first opportunity.

## Note on Design

Design is being paused after the consolidation task. It is producing roughly one full screen spec per
cycle and Frontend is consuming zero. Further specs would deepen a backlog that is already the
project's largest liability, and design drifts from reality the longer it sits unbuilt.

That pause is not a criticism of Design's output, which has been the strongest work in the project.
It is a queue problem.

## Done looks like

Founder answers step 1. Then frontend is reachable from a Claude Code session that can see the
mailbox, 031 has run, and `docs/frontend-audit-2026-07.md` exists with an honest verdict per element.
