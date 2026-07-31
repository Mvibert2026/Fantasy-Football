---
ID: FR-133
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: backend (compute), gated on strategist thread 119
---

## Request

Founder's own words:

> "for me, all the leagues say they are hard coded, and none of the availability is tested, at least
> getting the site compute would be nice."

## He is right on both counts — measured, not taken on trust

**"Hard coded."** The primary league is a literal in code. `build_current_league()`
(`src/league_config.py:190`) constructs Westwood field-by-field, and `CURRENT_LEAGUE` is that literal
evaluated at import. The other 26 configs in `data/leagues/*.json` are generic presets —
`espn_10_half`, `espn_12_full`, `yahoo_14_standard` and so on — **not his real leagues.** So every
league the product knows about is either a code literal or a static preset. Nothing is loaded from a
platform.

**"None of the availability is tested."** Availability is computed for **2 of 26**:

| Has availability | Nothing computed |
|---|---|
| `data/export/availability.json` (primary) | the other 24 preset configs |
| `data/leagues/yahoo_standard_mock/availability.csv` | |

So a user on any non-primary league sees a screen with no numbers behind it.

## The blocker, and why it is not stalling

Computing 24 leagues now means computing them **twice**. Strategist thread 119 is live and may change
availability's central input from expert consensus to ADP — a change to the model's central tendency,
not a tuning parameter. Every number produced before it lands would be invalidated by it.

Sequence: **119 answers → compute all leagues once, on the right input.** PM's call, stated to the
founder, who can overrule it.

## Not covered by this request

Loading his *actual* leagues (the two beyond Westwood, still unconfirmed — FR-012) is a separate,
larger ask requiring platform access. This FR is about computing what the product already has configs
for.
