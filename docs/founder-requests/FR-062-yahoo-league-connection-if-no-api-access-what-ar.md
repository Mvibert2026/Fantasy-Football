---
ID: FR-062
STATUS: SCOPING
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

---

## Answered 2026-07-30 (researcher) — the premise did not hold

Full audit: `docs/research/yahoo-espn-league-connection-2026-07-30.md`, thread 095.

**Yahoo's API appears to be open, self-serve, and free.** Five independent third-party SDKs document
the same path: sign in with the account holding the leagues, create an *Installed Application* at
`developer.yahoo.com/apps/create/`, redirect URI `https://localhost:<port>`, tick Fantasy Sports →
Read, Client ID and Secret issued immediately. **What disappeared is Yahoo's documentation, not the
API** — an unofficial mirror says so in as many words, and that is almost certainly what prompted the
founder's worry.

**So the password fallback buys nothing** and does not need deciding.

**The biggest payoff has nothing to do with draft day.** `yfpy`'s models carry `stat_modifiers`,
`roster_positions`, playoff settings, and a `Bonus` class with exactly `points, target` — **the shape
of a yardage-bonus threshold.** If it populates, all of `CLAUDE.md` §7 becomes readable from Yahoo's
own source of truth rather than transcribed from a screenshot, and FR-012's two unconfirmed leagues
close in one call.

**Live draft picks: probably readable, on a single source.** One SDK docstring says a call during a
draft returns players drafted so far. **n = 1, undated, unconfirmed by the other four**, with latency
and throttling unknown. The researcher flagged that the "yes" arrived pointing exactly the direction
that makes the product most interesting — **a free Yahoo mock draft and a 5-second poll settles it in
twenty minutes.** Writing a pick: no.

**ESPN is a clean no.** Obtaining the auth cookies "cannot be done programmatically"; the only
mechanism that works is the one Disney's terms forbid by name. That does not improve with effort.

**The clause that actually constrains the build is data retention, not passwords:** Yahoo user data
must be deleted within 24 hours unless explicitly storable. If that holds, **"sync my league into
`nfl.db`" is the one design the terms forbid** — fetch-on-demand-and-discard is the compliant shape.
That is a real architectural constraint and it should be settled before anyone builds a sync.

**Correction the researcher caught in this project's own records:** FR-062 said all three leagues are
Yahoo/ESPN. FR-052's body carries the founder's own correction that they are not, while **its
filename still says otherwise.** If the third league is Sleeper, that API is public and needs no auth
at all. **The founder should say which platform his third league is on** — it changes the work.

---

## Founder's answers, 2026-07-30

> "Third league is espn. May be a manual draft for me. But add the yahoo connection work to our near
> term work. Would love to have that working sooner than later."

**The third league is ESPN, and ESPN is a clean no.** So that league stays manual — settings typed
in, picks entered by hand. Recorded as a settled product constraint rather than an open gap: no
amount of effort improves it, because the only mechanism that works is the one Disney's terms forbid
by name. **This resolves the contradiction the researcher found** between FR-052's body and its
filename slug: two Yahoo leagues (Westwood, Ethan's Expert League) and one ESPN.

Consequence worth stating plainly: **the two-track split now has a third shape.** Westwood becomes
the connected league, Ethan's is connectable, and the ESPN league is manual-only. Any "sync your
league" affordance must say which of the three a league is, not offer sync everywhere and fail on
one.

**Yahoo connection promoted to near-term work.**

The sequencing constraint is that **only the founder can do step one** — the app registration is tied
to the Yahoo account holding the leagues. So the work splits:

| Who | What |
|---|---|
| **Founder** | Register the app, obtain Client ID and Secret |
| **Agent, now** | Build the connector against the documented OAuth2 flow so it is ready the moment credentials exist |
| **Agent, after** | Pull settings for both Yahoo leagues; confirm whether `Bonus(points, target)` actually populates |
| **Founder, 20 min** | A free Yahoo mock draft plus a poll, to settle whether live picks are readable |

**Two things to settle before a sync is designed, not after:**

1. **The 24-hour retention clause.** If Yahoo user data must be deleted within 24 hours unless
   explicitly storable, **persisting a league into `nfl.db` is the design the terms forbid.**
   Fetch-on-demand-and-discard is the compliant shape and it is a different architecture. Decide
   first.
2. **The no-competing-product clause**, which the researcher named as the same fault line already
   live for FFC and FantasyPros. One ruling should cover all three rather than three separate
   judgements.

**Credentials go in `.env`, gitignored, never committed** — `CLAUDE.md` §10. The same rule that
applies to the site password applies here.

