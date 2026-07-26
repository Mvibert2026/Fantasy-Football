---
ID: 012
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

You are the coordinating session for Sprint 1. **Assume no human is available for the entire run.**
Do not stop to ask a question — record it and continue. Work the queue in this order:

**Phase 1 — bootstrap (serial, do these yourself, do not delegate).** Threads 008 then 010.
Installs CLAUDE.md rules, six agent definitions, the `/inbox` command, and the mailbox health test.
Verify with `/agents` and `python tools/handoffs.py check` before continuing. If phase 1 fails,
stop and report — everything downstream assumes it.

**Phase 2 — parallel, max three at a time.** Dispatch via the Task tool to the named subagent; do
not do their work yourself. Each carries its own pinned model and effort — do not override.

- `backend` → 001 (adopt CURRENT-STATE, demote status.md, fix the 1.6.0 stamp)
- `backend` → 002 (per-pick draft state — the highest-value item in this sprint)
- `librarian` → 011 (locate FRONTEND-SPEC.md and the reference prototype)
- `strategist` → 004 (three statistical specs)
- `researcher` → 009 (source audit for FR-001)

**Phase 3 — only if phase 2 leaves capacity.** `frontend` → 003, then 007 if 011 succeeded.

## Handling the things that need a human

Several threads need the founder and he is away. Do not block on any of them.

- **011** — search the filesystem broadly before concluding absent: sibling directories, other
  branches, `git log --diff-filter=D --name-only` for a deleted copy, and any `.html` over 20KB.
  If genuinely not found, set `STATUS: BLOCKED-ON-YOU`, say exactly where you looked, and move on.
- **007** — blocked by 011. If 011 fails, build the harness anyway against a placeholder reference so
  the scaffolding exists; mark it clearly as unpinned.
- **005** (FantasyPros CSVs) and mock collection — founder-only. Skip entirely.

## Rules for an unattended run

- **Never mark UI work resolved.** "Built, pending screenshot verification" is the terminal state
  without a human. This rule exists because a green suite has already coexisted with a missing screen.
- **Do not reverse a deferral.** The injury/LLM-renderer deferral and the closed alpha track were
  deliberate decisions with reasoning in the code. Encountering them is not permission to revisit.
- **Do not invent a constant.** If a value is needed and unmeasured, leave it unmeasured and say so.
- Anything the founder said that isn't captured → append to `docs/founder-requests.md`.
- If a subagent fails or runs out, record it in its thread and continue. One failure does not end
  the sprint.

## Done looks like

`python tools/handoffs.py sync && python tools/handoffs.py check` both clean. `CURRENT-STATE.md`
reflects reality. Every thread touched has a reply. Final report: threads resolved with commit
hashes and test counts, threads still open and what each waits on, and a short list of what needs
the founder.
