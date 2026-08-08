# Launch prompts — the short thing you paste to start a session as a role

**Why this file exists.** The founder had a small prompt for launching a chat session as the PM
agent. It lived only in chat, and chat is discarded — so when he asked for it on 2026-08-07 it was
gone, and nobody could produce it. That is the exact failure `CLAUDE.md` warns about ("a request
that never reaches one of these files has, as far as this project is concerned, never been made"),
and the project fell into it anyway. It is written down here so it cannot happen twice.

**Keep these short.** `CLAUDE.md` loads automatically in Claude Code and already carries the
standing law, the read order, and the operating rules. A launch prompt only has to do two things:
name the role, and start the work. Anything longer is duplicated law that will drift out of sync
with `CLAUDE.md` and then quietly contradict it.

---

## PM — the founder's primary interface

```
You are pm. Read docs/CURRENT-STATE.md, docs/environment.md, docs/operating-model.md,
docs/founder-requests/INDEX.md and docs/handoffs/OPEN.md, in that order. Then tell me
what you think the single most important thing to work on is, and why — before doing it.
```

That is the whole prompt. The read order is `CLAUDE.md`'s, not a new invention, and the last
sentence is the part that earns its place: it forces the session to state a plan you can correct
before it spends anything, rather than after.

**Do not paste the role's job description.** It is already in `.claude/agents/pm.md`, which pins
`model: opus` and `effort: high`. Restating it in chat overrides nothing and desynchronises.

## Any other repo role

Same shape — swap the name. The agent definitions in `.claude/agents/` carry the tier:

```
You are <backend|data-ops|frontend|ranker|librarian|operator|verifier>. Read
docs/CURRENT-STATE.md, docs/environment.md and docs/operating-model.md, then open every
thread in docs/handoffs/OPEN.md where TO: includes your role. Work those and nothing else.
```

## Autonomous run — no human in the loop

Use the slash command instead of a prompt; it is `.claude/commands/inbox.md` and is written for
exactly this:

```
/inbox            # everything actionable, dispatched to the right specialist
/inbox backend    # one role only
```

## Strategist and researcher — chat, no repo

These two run outside Claude Code (`docs/operating-model.md`), so they cannot read any of the files
above. They need the question **and** its context pasted in full. Strategist deliberately has no
database access, so never ask it to check a number — ask it to specify how a number should be
checked.

## Design — Claude Design, no repo access

Paste `docs/design-brief.md` verbatim. Re-paste whenever the principles or tokens change; there is
no automatic sync and Design cannot see the repo.

---

**If you change how a session is launched, edit this file in the same breath.** It is one paragraph
of upkeep and the alternative is reconstructing it from memory again.
