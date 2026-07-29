---
ID: FR-028
STATUS: SCOPING
SOURCE: chat session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Research what Yahoo's in-draft assistant shows - the room drafts off it

> "we'll need to research what Yahoo's in draft assistant does, all the drafters will see that, some
> will probably have their own PPR boards (Kione sanders for sure) but others will rely at least for
> ideas on the yahoo board"

Founder's own words, 2026-07-29.

## Why it matters

The project already holds the principle and had not applied it to its own league. `src/ingest_mfl_adp.py`'s
docstring states that **drafters pick off their own platform's displayed ranks, so ADP is a
per-platform behavioural variable** and platforms must never be blended. Westwood drafts on Yahoo,
looking at Yahoo's numbers. If much of the room takes cues from what is on their screen, the
rankings that predict *this* draft are Yahoo's — not a market aggregate from MyFantasyLeague or FFC.

His second clause matters as much as the first: the room is **mixed**, some managers running their
own boards and others taking ideas from the platform. Mixed anchoring is a harder and more
interesting modelling problem than assuming everyone drafts off one list.

## Initial read

Researched same day: `docs/research/yahoo-draft-assistant-2026-07-29.md`. Findings that change things:

**"The Yahoo board" is at least three differently-computed numbers** — a league-aware Default Rank
derived from that league's own scoring settings, an Expert Rank computed on Yahoo's *default* scoring
which also drives autopick, and platform-wide ADP. **Collapsing them would reproduce exactly the
blending error the MFL docstring exists to prevent.** Any future work here must name which one it
means.

**The scoring wedge is narrower than assumed on receptions and wider on bonuses.** Yahoo's default
football scoring is already half-PPR — confirmed from inside this repo, since
`data/leagues/ethans_expert_league.json` carries `receptions: 0.5` with empty `bonuses: []`. So
Westwood's real divergence from the platform default is the **stacking yardage bonuses**, plus INT
−2 rather than −1, no kicker, and two flex.

**The highest-value question is an open `[GAP]`, deliberately not filled: does Yahoo's league-aware
ranking price bonus thresholds at all?** A threshold bonus is a nonlinear function of a per-game
distribution and cannot be derived from a season total, so there is a real chance Yahoo ignores it.
If so, **the entire room under-prices ceiling in a league that pays for it** — which would be a
genuine, mechanical edge rather than a modelling opinion.

**A free test exists and the founder can run it himself.** Compare his Pre-Draft Rankings ordering in
Westwood against Ethan's Expert League — both Yahoo, both 10-team, one with stacking bonuses and one
without. **If the orderings are identical, Yahoo ignores the bonuses.** No scraping, no API, no code.
This is the single most valuable next action on this thread.

**What is legitimately obtainable is narrow.** Only `draft_analysis` (`average_pick`,
`average_round`, `percent_drafted`) via the official OAuth API, which `CLAUDE.md` §10 prefers — the
*behavioural* number, which is the useful one. Three blockers make it a founder decision rather than
an agent task: a 24-hour data-deletion clause (unresolved whether aggregate ADP falls under it, which
decides whether snapshots are storable at all), a no-competing-product clause (Yahoo ships Draft
Scout; so does this project), and unconfirmed format/league-size filtering. The displayed list, tiers
and Draft Scout output have **no sanctioned export**.

**Draft Scout is paywalled during real drafts and free only in mocks.** So the modal free drafter in
his league sees an ordering plus ADP columns, not a recommender. Its metric, VOLS, is the same family
as this project's replacement-level VBD — meaning **positional revaluation, recorded in
`docs/pm/MEMORY.md` §1 as the board's only edge channel, is partly competed away against any manager
who pays.** That is an uncomfortable finding and should not be softened.

**How much of the room actually drafts off the platform is a `[GAP]`** with no usage statistic found.
Platform-wide market-share figures exist and were deliberately excluded as a category error against a
ten-person room. The useful move is for the founder to label each manager
`own-board / mixed / platform-default / unknown` **before** 7 September — converting his own read
into a checkable pre-registration rather than a post-hoc story.

**Boundary note, and it constrains what any future pass can deliver:** every Yahoo-owned host
disallows this agent class by name in robots.txt, so **no Yahoo page was fetched and no `[VERIFIED]`
claim about the draft room exists in the report — nor can one, from an agent.** Anything firsthand
must come from the founder's own screen.
