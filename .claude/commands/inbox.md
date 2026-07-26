---
description: Read the repo mailbox and work everything waiting on this project, dispatching to the right specialist agents.
argument-hint: "[role, or blank for all]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

Run the project's handoff mailbox and clear what is actionable. This is the single entry point —
assume no human will give further instructions during this session.

## 1. Orient
```
python tools/handoffs.py sync
python tools/handoffs.py check
cat docs/handoffs/OPEN.md
```
Also read `docs/CURRENT-STATE.md` and `docs/founder-requests.md`.

If `$1` is given, work only that role's inbox. Otherwise work everything actionable.

## 2. Dispatch
For each open thread, launch the subagent named in its `TO:` field using the Task tool —
`backend`, `frontend`, `data-ops`, `strategist`, or `researcher`. Each carries its own pinned model
and effort; do not override them, and do not do the work yourself in this session. You are
coordinating.

Threads whose `TO:` is `design` or `founder` cannot be actioned by an agent. Collect them and
surface them at the end as the short list of things needing a human.

Respect dependencies: a thread with `BLOCKS:` pointing at another must run first. Thread 008 is a
bootstrap and precedes everything.

Run independent threads concurrently. Cap at three at once.

## 3. Close out
Each subagent replies in its own threads. Then:
```
python tools/handoffs.py sync
python tools/handoffs.py check
```
Verify `docs/CURRENT-STATE.md` reflects what actually changed.

## 4. Report
One short block: threads resolved (with commit hashes and test counts), threads still open and what
they wait on, anything needing the founder. No prose narration of the work — the threads hold that.

**Never mark UI work resolved on an agent's own report.** It stays "built, pending screenshot
verification" until a human has looked.
