---
ID: FR-124
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
NEEDS: researcher (source), then design
---

## Request

Founder's own words:

> "News feed (global), and per player (leading to roster specific) needs to start - this will be
> useful for drafts"

He has now raised the news feed three times across two sessions (*"I would like to get the news feed
going"* previously). It has not been dispatched. That is a prioritisation failure worth naming.

## Why it matters

His stated reason is the right one: **it is useful during a draft.** A late scratch, a training-camp
injury, a depth-chart change on the morning of the draft is exactly the information a static
pre-computed board cannot carry — the board is built from data as of its export timestamp and says
so. News is the one input that is genuinely live, and the draft is the one moment it changes a
decision.

Three scopes, and he sequenced them himself:

1. **Global** — what happened today, across the league.
2. **Per player** — on the card, for the player being considered.
3. **Roster-specific** — filtered to who he has drafted. He flagged this as where it leads, not
   where it starts.

## Initial read

**The blocker is a source, and nothing else can be decided before it.** There is no news ingestion
in this project at all. `frontend/ui/assistant/news.ts` exists but handles *intent routing* for
news-shaped questions, not content — and it is the module whose regex matched "trade" inside "trade
offs" and misrouted a founder question this session.

Before any design or build:

- **What source, under what terms.** `CLAUDE.md` §5 requires licensing be checked *before* a scraper
  is built, not after. Most fantasy news is aggregated from wire services under terms that do not
  permit redistribution. A source that cannot be used is the likeliest outcome and should be
  established cheaply.
- **Yahoo and ESPN are off the table for research agents** — both block them by name. Do not dispatch
  a fetch at either.
- **Per-player attachment needs a join key.** A headline is useless on the card unless it resolves to
  a `player_id_gsis`. Name-matching news text to a player is the same problem that quarantined eight
  players in this session's mock ingestion, on cleaner input.

**The honesty constraint applies with unusual force here.** A news panel that is empty because
ingestion failed looks identical to a news panel that is empty because nothing happened. Under
`CLAUDE.md`'s never-fabricate rule those must read differently, and the distinction has to be
designed in from the start rather than retrofitted — this is the single most likely place for the
app to silently mislead him on draft morning.

**Sequencing:** `researcher` establishes source and licensing first; that answer determines whether
this is a build item at all. Behind the eight items in flight. Related: FR-119's backlog entry
(*"the news feed: what makes an item appear"*) is waiting on this to be answerable.
