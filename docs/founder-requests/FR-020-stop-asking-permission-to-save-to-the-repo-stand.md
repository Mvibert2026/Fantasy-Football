---
ID: FR-020
STATUS: NEW
SOURCE: claude code session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Stop asking permission to save to the repo - standing authorisation

> "You still keep asking if claude can save things in the repo, yes always, stop asking me
> permission for things"

Founder's own words, 2026-07-29.

## Why it matters

Every ask is an interruption, and the founder's standing complaint is that he is kept at the
keyboard by things that do not need him. This one is worse than an ordinary interruption because
the answer is always the same — asking has no information content, it only costs his attention.

It also compounds with the measured interruption data in FR-018: agents *choosing* to stop and ask
was 42% of all stops across 57 sessions, the single largest category, more than permission denials
and hook blocks combined. Permission machinery has now been stripped (see `docs/decisions.md`,
2026-07-29), which removes the mechanical stops. This request targets the larger remaining half —
the discretionary ones.

## Initial read

**Recorded as a standing authorisation in `docs/pm/CHARTER.md` under "Standing authorisations —
never ask again," and as a hard rule in every agent definition under "Decide and log; do not ask."**
Writing, committing and pushing to this repo needs no approval, ever, and must not be announced as
a question or prefaced with a request.

The boundary that survives, unchanged, is the one the charter already reserved: escalate only for an
action that is irreversible, contradicts a written rule, spends money, or is a decision the founder
explicitly reserved. **Publishing anything outward-facing stays inside that boundary** — the repo is
private and contains his league data, so pushing content to a public host is not covered by this
authorisation and should still be raised.

One genuine constraint is *not* an approval gate and must not be confused with one: Fable mandates
run at the end of the week before the budget reset (FR-021). That is a scheduling fact to respect
silently, not something to ask about.

Status stays NEW until a later session confirms the ask rate actually fell — the rule is written
down, which this project's own meta-lesson says is the weakest of the three enforcement levels.
