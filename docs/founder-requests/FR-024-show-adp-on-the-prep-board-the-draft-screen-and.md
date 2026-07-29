---
ID: FR-024
STATUS: IN PROGRESS
SOURCE: chat session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Show ADP on the prep board, the draft screen, and the player profile

> "ADP should be shown on both the prep and draft screens as well as player profile."

Founder's own words, 2026-07-29.

## Why it matters

ADP is where the market actually drafts, as opposed to where experts *rank*. The board today shows
only the second. Knowing a player is ranked 12th but going 30th is the whole basis of deciding
whether to reach or wait, and it is not currently visible anywhere in the app.

It is also the founder asking for something the project has been collecting daily and never once
displayed — the snapshots have been captured since 2026-07-26 precisely because a missed day cannot
be re-fetched, and until now nothing consumed them.

## Initial read

**Real work, not a display toggle: `board.json` carries no ADP field at all today.** Backend chain
dispatched 2026-07-29 to put one on the export contract, with a version bump and a thread to
frontend. Frontend is queued behind it and explicitly told not to invent a client-side substitute.

**The trap to avoid, and it has already caught people.** The `rankings` table column feeding
`consensus_rank` is named `adp_rank` but holds **FantasyPros expert consensus rank, not ADP**.
Anything that displays `consensus_rank` under an "ADP" label would be the app asserting something it
did not derive. The real ADP lives in a separate table (`adp_snapshots`, `adp_source='mfl_proxy'`).

**Two honesty constraints on the display**, both from `CLAUDE.md` rather than invented here:

1. **It is a proxy, and must be labelled as one.** The population is whoever drafts on
   MyFantasyLeague, not this league. `adp_source` must travel with the value, and platforms must
   never be blended into a single "consensus ADP" number.
2. **The format is close but not exact.** The capture is `FCOUNT=10`, matching the 10-team primary
   league, but `IS_PPR=1` while the league is **half**-PPR — MFL's flag is binary and offers no half
   option, so full PPR is the nearer of two settings rather than a match. Receivers come off the
   board earlier in full PPR, so the proxy is slightly receiver-forward relative to Westwood.

**Explicitly out of scope, and a different decision.** This is about *displaying* ADP, not feeding it
into the model. `src/availability.py::load_mfl_adp_source` exists and is tested but is deliberately
unwired, with a test asserting it stays out. **Do not quietly wire it in under cover of this
request.** That said — the availability model's opponent-noise parameter is uncalibrated *because*,
in its own docstring, "no ADP source exists to fit it against." That statement is now false twice
over (daily snapshots exist; FFC history is unblocked per FR-023), and closing it is arguably the
highest-value ADP work available. It belongs to the availability question, not to this one.

The likely-more-useful number is the **gap between our rank and ADP**, not ADP alone — but the board
already shows a delta against consensus, and two adjacent delta columns measuring different things
would confuse more than they reveal. Left to frontend, which can see the layout.
