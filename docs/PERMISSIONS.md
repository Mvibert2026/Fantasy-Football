# Stop the approval prompts — two changes

You said you always approve. That is exactly why this is worth configuring properly rather than
turning approvals off wholesale: a prompt you reflexively click through provides no safety, so the
honest move is to pre-approve the safe majority and keep a genuine prompt on the handful of commands
that can actually destroy work.

## Change 1 — add `permissionMode: acceptEdits` to every agent definition

Add this single line to the YAML frontmatter of all six files in `.claude/agents/`
(`backend.md`, `frontend.md`, `data-ops.md`, `strategist.md`, `researcher.md`, `librarian.md`):

```yaml
permissionMode: acceptEdits
```

Place it anywhere among the other frontmatter keys, e.g.:

```yaml
---
name: backend
description: ...
model: sonnet
effort: low
permissionMode: acceptEdits
---
```

This stops file edits and writes from prompting inside subagent runs — the overwhelming majority of
the interruptions during an unattended sprint.

## Change 2 — merge the permissions block into `.claude/settings.local.json`

Merge the `permissions` object from `settings-model-block.json` into your existing
`.claude/settings.local.json`. **Merge, do not overwrite** — that file is ~22 KB and already holds
accumulated rules you want to keep. If both files have a `permissions.allow` array, concatenate them
and drop duplicates.

## What is pre-approved, and what still asks

**Allowed without prompting:** all file reads, writes, and edits · `git status/diff/log/add/commit/
show/branch/stash` · `python`, `pytest`, `sqlite3` · `ls`, `head`, `tail`, `wc`, `mkdir`, `mv`, `cp`
· `npm test`, `npm run`, `npx playwright` · web fetch and search.

**Still prompts, deliberately:** `rm` · `git reset` · `git checkout` · `git restore` · `git clean` ·
`git push` · `pip install` · `npm install`.

Every command on that second list either destroys uncommitted work or changes your environment.
Your repository has **no remote configured**, so a bad `git reset --hard` or `git clean -fd` is
unrecoverable — there is no origin to re-clone from. Those five git commands are the entire reason
to keep any prompt at all.

## What I did not recommend

`--dangerously-skip-permissions` (sometimes called YOLO mode) turns off every check including the
destructive ones. With no git remote as a backstop, an agent that misreads a situation and runs
`git clean -fd` takes your uncommitted work with it and nothing gets it back. The two changes above
remove essentially all the friction you are actually experiencing while leaving that one guardrail
standing.

## Worth doing separately

Get a remote. Not for agent coordination — that problem is solved by the repo and the device bridge
— but as a backstop. A private GitHub repo is free and, once one exists, the calculus above changes
and a broader auto-approve becomes defensible. Right now a single `nfl.db` is 853 MB and the entire
project exists on exactly one disk.
