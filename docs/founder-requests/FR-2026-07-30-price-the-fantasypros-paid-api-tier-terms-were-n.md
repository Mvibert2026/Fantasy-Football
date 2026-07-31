---
ID: FR-2026-07-30-price-the-fantasypros-paid-api-tier
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: MEDIUM
NEEDS: founder (account tier), then researcher (pricing), then data-ops
---

## Request

Founder's own words:

> "fantasy pros has an API link on the rankings - are you sure that for private use only we can't API
> them? like it's not possible? because based on their site and my personal use and the fact I can
> look at them there it should be fine from a terms standpoint"

## He is right that terms are not the problem, and he is arguing against a position this project never held

**Nobody ever said FantasyPros' terms forbid API use.** Searched `docs/deferred.md` for any
terms/ToS/scraping objection attached to FantasyPros: there is none. The recorded blocker is
entirely different and entirely technical.

## What the blocker actually is — measured, 2026-07-25

A live probe (`docs/deferred.md`, "FantasyPros API — probed 2026-07-25") against
`api.fantasypros.com/public/v2/json/nfl/{season}/{projections,consensus-rankings}` using the
`FANTASYPROS_API_KEY` already in `.env`:

- Every response returns `limit: 10`, `public_api_limited: true`, `tier: "free"`.
- `count` reports the true total — 598 for all-position projections, 580 for consensus-rankings —
  but `players` is **truncated to 10 regardless**.
- `offset`, `page` and `start` were all tried. All silently ignored; all returned the identical
  top-10 players.

So it is not a permissions question and never was. **The free tier physically cannot return a full
board.** Position-filtering to QB/RB/WR/TE would yield 40 players, which are almost certainly already
inside the 145 the existing rank-to-points curve covers — it does not reach the 233 players that
actually lack a projection, who are by definition the ones outside consensus-rank depth.

The existing code says so directly (`src/ingest_rankings.py:37`): *"Do not 'fix' this by pointing at
the live API without addressing the row cap first."*

## What is genuinely open, and it is his to answer

The key that was probed reported `tier: "free"`. **Whether the founder holds — or can buy — a paid
FantasyPros subscription whose API tier lifts the cap has never been established.** The probe measured
the free tier because the free tier is what the key had.

Two things follow, in order:

1. **Founder:** does your FantasyPros account have a paid subscription, and is the key in `.env` tied
   to that account or to a separate free developer signup? These can differ.
2. **If a paid tier exists:** price it and confirm, from their documentation rather than inference,
   that the paid tier actually returns full boards. `public_api_limited: true` implies a non-limited
   mode exists; it does not prove what that mode returns.

The "API link on the rankings page" he mentions may also be a different, subscriber-facing endpoint
from the `public/v2` one that was probed. Worth checking directly rather than assuming it is the same
API.

## Why this matters beyond convenience

It would replace a manual browser export the founder performs by hand — currently the board's ranking
source, currently 3 days old and at its freshness limit, and the one source no agent can refresh. It
would also fix a known scoring mismatch: the live API accepts `scoring=HALF`, which is this league's
format, while the DynastyProcess mirror's scoring is ambiguous.
