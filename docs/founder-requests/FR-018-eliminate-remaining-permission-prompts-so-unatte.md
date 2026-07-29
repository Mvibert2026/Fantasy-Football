---
ID: FR-018
STATUS: NEW
SOURCE: chat session 2026-07-29
RAISED: 2026-07-29
---

## Request
Eliminate remaining permission prompts so unattended runs can proceed without a human

## Why it matters

Every stop in an unattended run costs the whole run, not the one command — the session waits
for an approval that never comes until the founder next looks at it.

## Initial read

**The premise needs adjusting before this gets worked.** Permission prompts are not the main
thing stopping unattended runs.

Measured 2026-07-29 across all 57 prior session transcripts in
`~/.claude/projects/C--Users-matth-Documents-Personal-Fantasy-Football/`, classifying only
structured transcript events (an earlier regex pass over raw text gave 173 and was inflated by
documentation and hook source code that merely *quote* these strings — that number should not
be used):

| Interruption type | Count | Share |
|---|---|---|
| Agent stopped to ask the founder (`AskUserQuestion`) | 19 | 42% |
| Founder manually interrupted the run | 9 | 20% |
| Founder denied a tool call | 6 | 13% |
| Hook blocked chaining (`;` `&&` `\|\|` newline) | 6 | 13% |
| Hook blocked a destructive pattern | 5 | 11% |
| **Total** | **45** | |

Mean 0.8 per session. The two hook rows are still slightly overstated: reading
`.claude/hooks/block_dangerous.py` puts its own message strings into the transcript.

**Consequence for this request:** the largest single cause is agents *choosing* to ask (42%),
and the second is the founder stepping in (20%). Together that is 62%, and no permission or
hook change touches either. Actual permission denials are 6 of 45.

This does not make the request wrong — 11 hook stops are real and worth removing — but the
title's framing would send someone to `permissions.allow`, which is already fully wildcarded
(`Bash(*)`, `PowerShell(*)`; see `docs/environment.md` §2) and therefore cannot be the cause.

Suggested rescope, in value order:

1. **Reduce agents asking.** 42% of all stops. Needs a norm about when an agent should decide
   and log rather than ask — the founder's own standing instruction this session was
   "decide and log," which suggests the norm exists but is not written down anywhere an agent
   reads. Candidate home: `docs/operating-model.md`.
2. **Fix the hook's semicolon false positive.** 6 stops. The hook's scan is textual, so it
   rejects semicolons that are legitimate PowerShell syntax (hashtable calculated properties,
   statements inside script blocks) while correctly allowing semicolons inside quoted strings.
   Founder acknowledged this on 2026-07-29 as self-inflicted. A syntactic check, or narrowing
   to top-level separators, removes these without weakening the gate. Detail and a measured
   truth table in `docs/environment.md` §2b.
3. Leave `permissions.allow` alone. Adding entries removes zero prompts.

Related: `docs/environment.md` (written 2026-07-29 so subagents stop rediscovering all of this).
