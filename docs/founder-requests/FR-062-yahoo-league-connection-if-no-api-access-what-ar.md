---
ID: FR-062
STATUS: NEW
PRIORITY: HIGH
ROUTED-TO: researcher
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Yahoo league connection if no API access — what are the real options

Founder's own words:

> "Also put somebody on figuring out what happens if I cant get a yahoo API, can I still connect
> through my username and password somehow through you"

## Why it matters

All three of his leagues are on Yahoo or ESPN. Connecting to them is what turns this from a tool he
maintains by hand into one that knows his league — settings, rosters, live picks. FantasyPros ships
exactly this as a one-click "Sync Your League" control (`docs/design-handoff/competitor-screenshots/README.md`),
so it is table stakes in the category, not an ambition.

Everything currently known about his leagues was typed in or read off a screenshot. That is the cost
of not having it.

## The project already has a position on this, and it should be stated before anything is built

`CLAUDE.md` §10, unchanged since it was written:

> "Prefer official OAuth over browser automation for provider access. **Storing a real account
> password for scripted login is a last resort, not a parallel path** — it creates a credential
> liability, is brittle, and may violate provider terms."

**So the answer to "can I connect through my username and password" is: technically probably, and it
is the option of last resort for three concrete reasons**, none of which is squeamishness:

1. **Credential liability.** A stored password is a standing risk on a machine and in a backup. An
   OAuth token is scoped, revocable, and cannot be reused elsewhere. A Yahoo password can.
2. **Brittleness.** Scripted login breaks on any login-flow change, and it breaks silently, usually
   on the day it is needed. Every Yahoo host already blocks research agents by name — the same
   defences apply here.
3. **Terms.** It may violate them. That needs checking, not assuming, and it needs checking *before*
   anything is built rather than after.

**None of that is a refusal.** It is his account and his call. But he asked what happens *if* the API
is unavailable, which means the first job is establishing whether it actually is.

## What the researcher should establish, in order

1. **Is Yahoo's Fantasy Sports API actually available to him?** It has existed for years with a
   documented OAuth2 flow and a free developer registration. **Establish whether that path is open
   before treating it as closed** — the founder's question assumes it may not be, and that assumption
   has not been tested. This is the question that makes the rest moot if it comes back yes.
2. **What does registration actually require?** App registration, redirect URI, review process,
   approval time, and any per-app limits. Concrete steps he can follow, not a summary.
3. **What can the API reach?** League settings, scoring, rosters, draft results, live draft state.
   **Live draft state is the one that matters most and is least likely to be available** — say so
   explicitly either way.
4. **ESPN, same questions.** It has no official public API; establish what that means in practice.
5. **Only then, the fallback.** If OAuth is genuinely unavailable, what are the options, what does
   each cost in the three terms above, and what do Yahoo's terms of service actually say about
   automated access with user credentials. **Quote the clause; do not characterise it.**

**Do not attempt to fetch Yahoo hosts.** They block research agents by name and that block is
recorded and respected. Use documentation, developer portals and secondary sources, and mark
anything unverifiable as a gap rather than inferring it.
