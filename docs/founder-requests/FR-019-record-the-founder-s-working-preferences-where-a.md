---
ID: FR-019
STATUS: NEW
SOURCE: claude code session 2026-07-29
RAISED: 2026-07-29
---

## Request

Founder's own words:

> "my working preferences exist in my own notes but not where agents can read them"

Raised in response to a suggestion that nothing is currently recorded about *how the founder
wants agents to work* — only about the project itself. Founder endorsed acting on it.

## Why it matters

Agent-visible memory currently holds eight facts, all of them `project` type: interpreter
paths, hook behaviour, worktree gotchas, data-source state. Nothing describes how the founder
wants work done — how much autonomy to take, when to ask versus decide, expected verbosity,
review depth, or what "done" means for an unattended overnight run.

This is measurably expensive. Across 57 prior sessions, the single largest cause of a stopped
unattended run is an agent choosing to ask the founder a question (19 of 45 stops, 42% — see
FR-018 for the full breakdown). The founder's standing instruction in this session was
"decide and log", which is exactly the norm that would prevent most of those, and it exists
nowhere an agent can read.

Chat transcripts are invisible to every other agent and are discarded. A preference stated in
chat has, as far as this project is concerned, never been stated.

## Initial read

Scope is small and the value is immediate, but **the content has to come from the founder** —
this cannot be inferred from the repo without inventing preferences the founder never held,
which is worse than having none.

Suggested shape:

- A short `docs/working-preferences.md`, linked from CLAUDE.md §12 and added to the session-start
  reading list next to `docs/environment.md`.
- Written as decision rules, not adjectives. "Decide and log rather than ask, except when X"
  is actionable; "be autonomous" is not.
- Sourced by asking the founder a handful of specific questions rather than by drafting
  something for them to correct — the useful content is in their existing private notes.

Candidate questions to put to the founder:

1. When should an agent stop and ask, versus decide and log? What is the actual line?
2. What does "done" mean for an unattended run — committed and pushed, or staged for review?
3. How much narration do you want in a final report? (Observed preference: commit hash and test
   count, not prose — CLAUDE.md already says this for completion reporting; is it broader?)
4. When an agent disagrees with an instruction, do you want it flagged before acting, or acted
   on with the concern noted?
5. What should an agent never do without asking, regardless of how routine it looks?

Sequencing: worth doing before the next unattended overnight run, since that is where the
42%-of-stops cost is actually paid.

Related: FR-018 (the interruption measurement), `docs/environment.md`,
`docs/operating-model.md` (probable home if a separate file is not wanted).
