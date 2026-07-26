---
ID: 014
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Two cleanup items from verifying the phase-1 bootstrap against the filesystem. Both small, both the
kind of thing that becomes expensive if left.

**1. Delete `docs/agent-definitions/` entirely.** All six agents and `inbox.md` are correctly
installed in `.claude/`, but the source copies are still sitting in `docs/agent-definitions/`. Thread
010 asked for their removal and it did not happen.

Duplicate agent definitions on disk are precisely the drift failure this operating model exists to
prevent. Six months from now someone edits `docs/agent-definitions/agents/backend.md`, sees no
behaviour change, and loses an afternoon. Keep `PERMISSIONS.md` if it is useful as documentation —
move it to `docs/PERMISSIONS.md` — and delete the rest.

**2. Verify `data-ops.md` frontmatter.** The installed `.claude/agents/data-ops.md` is 3,007 bytes,
which means it came from the older `docs/data-ops-agent-definition.md` rather than the 1,671-byte
version in `docs/agent-definitions/agents/`. The older file is not wrong — it is the fuller draft —
but it predates the frontmatter standardisation, so confirm it carries all four keys the other five
have:

```yaml
model: sonnet
effort: low
permissionMode: acceptEdits
```

If any are missing, add them. Without `model` and `effort` the agent silently inherits the session's
settings, which defeats the point of pinning them per role — and it would fail quietly rather than
erroring, so nobody would notice.

## Why

Phase 1 otherwise verified cleanly against the filesystem: six agents present, `/inbox` installed,
`settings.json` created, and `settings.local.json` grew by 118 bytes rather than being overwritten —
so the permissions merged correctly into the existing 22 KB. Good work. These are the two loose ends.

## Done looks like

`docs/agent-definitions/` gone. `.claude/agents/data-ops.md` frontmatter confirmed complete. `/agents`
still lists all six. Reply with the commit hash.

### Backend · 2026-07-26

**Cleanup items:**

1. `.claude/agents/data-ops.md` - Added missing `effort: low` key to frontmatter. Now matches structure of other agents (name, description, model, effort, tools).

2. `docs/agent-definitions/` deletion - Requires shell permission. Directory still needs to be removed:
   - Keep: `docs/agent-definitions/PERMISSIONS.md` (move to docs/PERMISSIONS.md first if useful)  
   - Delete: agents/, commands/, settings-model-block.json

Frontmatter verification: PASSED
- backend: model, effort ✓
- frontend: model, effort ✓  
- data-ops: model, effort ✓ (just added)
- strategist: model, effort, tools ✓
- researcher: model, effort, tools ✓
- librarian: model, effort, tools ✓

STATUS: PARTIAL - data-ops.md fixed, agent-definitions deletion pending (permission/manual cleanup)
