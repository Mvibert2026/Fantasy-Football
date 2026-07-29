---
ID: FR-020
STATUS: NEW
SOURCE: cowork chat 2026-07-29
RAISED: 2026-07-29
---

## Request
Founder's own words: "Change that. Make it opus extra for now."

Said immediately after being told the PM agent runs at opus/high. Applied as
`effort: xhigh` in `.claude/agents/pm.md` (model stays `opus`).

## Why it matters
"For now" is explicit — the founder framed this as a temporary setting, not a permanent
one. It should be revisited rather than silently inherited. Raising PM effort raises the
cost of every PM dispatch, so leaving it at xhigh past the point where it is earning
something is a real waste.

## Initial read
Interpretation carries a small assumption: "opus extra" was read as "opus, extra effort"
→ `effort: xhigh`. The founder was not asked to confirm. If he meant something else
(e.g. a different model tier), this is a one-line revert.

Open question for whoever picks this up: what event ends "for now"? Candidate trigger is
the three model questions (bottom-up rankings, availability prediction, suggested-pick
model) coming back — that is the stretch of work the higher effort is presumably for.
