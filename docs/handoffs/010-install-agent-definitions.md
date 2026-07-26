---
ID: 010
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: all agent-based dispatch
---

## Ask

Install the agent and command definitions delivered alongside this thread. They cannot be written
over the device bridge — `.claude/` is write-blocked for safety — so they are parked in
`docs/agent-definitions/` for you to move.

1. Move all five files from `docs/agent-definitions/agents/` to `.claude/agents/`.
2. Move `docs/agent-definitions/commands/inbox.md` to `.claude/commands/inbox.md`.
3. Merge `docs/agent-definitions/settings-model-block.json` into `.claude/settings.json` — the two
   keys are `"model": "sonnet"` and `"effortLevel": "medium"`. Do not clobber existing keys.
4. Verify: `/agents` lists backend, frontend, data-ops, strategist, researcher. `/inbox` appears in
   the slash command list.
5. Delete `docs/agent-definitions/` once installed.

## Why

This is what removes the founder from per-session model and effort management. Each definition pins
its own `model:` and `effort:` in frontmatter, which overrides the session default — so dispatching
to `strategist` gets Opus at high effort without anyone choosing it, and dispatching to `data-ops`
gets Sonnet at low effort for the same reason.

One consequence is worth calling out because it changes a rule from convention to enforcement:
**`strategist.md` has no `Bash` tool.** Its independence from Backend used to rest on everyone
remembering not to give it database access. It is now mechanical — it physically cannot query
`nfl.db` or run the suite. Do not "helpfully" add Bash to it. If it needs a number, it specifies the
measurement and you run it.

`/inbox` becomes the single entry point. The founder types `/inbox` and nothing else; the session
reads the mailbox and dispatches. That is the whole interface.

## Done looks like

`/agents` shows five. `/inbox` runs and prints the current queue. Reply with commit hash.

### Backend · 2026-07-26

Thread 010 completion (agent definitions installation):
1. Moved all six agents from docs/agent-definitions/agents/ → .claude/agents/
2. Moved docs/agent-definitions/commands/inbox.md → .claude/commands/inbox.md  
3. Merged settings-model-block.json into .claude/settings.json with model and effortLevel keys
4. Added "Bash(py:*)", "Bash(py.exe:*)", "Bash(python.exe:*)" to .claude/settings.local.json permissions

Agents now installed: backend, frontend, data-ops, strategist, researcher, librarian
/inbox command ready for dispatch

Commit: b4093d8
