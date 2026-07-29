---
ID: FR-053
STATUS: NEW
PRIORITY: MEDIUM
ROUTED-TO: researcher, design
SOURCE: chat 2026-07-29, PM session, Yahoo draft room screenshots
RAISED: 2026-07-29
---

## Request
Yahoo draft room reference capture — features to consider, and component projections exist

Founder's own words, with five screenshots of a live Yahoo draft room:

> "Some views of the draftboard that could be useful in general - also, I think we have more features
> which is great, couple missing ones though that could be useful or not, just look, send to research
> team, log the stuff for design consideration, generally I think we are pacing better though"

**This is direct observation of a competitor under a real clock — which every prior research pass
recorded as a gap it could not fill.** Yahoo blocks research agents by name; thread 061 and thread
086 both closed with zero behavioural observations of any competitor mid-draft. These screenshots
are the first.

## What is actually in them, observed not inferred

**Layout.** Left rail: queue/picks, autodraft, last-pick ticker. Centre: tabbed pane —
**Players / Board / Results / Standings**. Right rail: your roster as labelled empty slots
(QB, WR, WR, RB, RB, TE, W/R/T, K), filling as you pick. Header: clock, whose pick, *"You're up in 4
Picks"*, round and pick number. A strip of manager avatars showing the upcoming pick order.

**Two things that answer requests already open here:**

- **The tabbed centre pane is exactly FR-049.** Yahoo ships four tabs in the space this project has
  one screen in.
- **The Board tab is essentially FR-044's periodic table** — managers as columns, rounds as rows,
  each cell a pick coloured **by position** (orange WR, green RB), showing player, team and pick
  number (1.1, 1.2 …). Undrafted cells show their pick number, so the grid doubles as the schedule.
  It confirms the founder's *"pretty standard draft room stuff"* — this is convention, and the
  palette should follow it rather than invent one.

**Three features this project does not have:**

1. **A "YOUR TURN — 14TH PICK" divider rendered inline in the player list.** A line across the
   ranked list marking where your next pick falls. Everything above it is likely gone; everything
   below is plausibly reachable. **This is close to FR-051** — the reference point the founder asked
   for — expressed as a position in the list rather than a number in a column. Cheaper to read at a
   glance than either.
2. **Selectable projection source**: 2026 Proj Stats, 2025 Total, 2025 Advanced, plus FTN, Rotowire
   and THE BLITZ as paid options. Multiple opinions, switchable, side by side.
3. **ADP trend**: the sort control offers *Avg Pick*, *ADP*, and **"Last 7 Days ADP"** (paid). That
   is ADP velocity, which this project has as an unbuilt item.

**The finding that matters most, and it is not a UI feature.** Yahoo's player card publishes
**component projections** — Drake London 2026: 93.9 receptions, 1,265 receiving yards, 8.3 receiving
TD, 2 rushing yards, 0.2 fumbles lost — alongside 2025 actuals in the same shape.

**This project has no component projections at all.** Verified today: `board.json`'s
`projected_points` is a single per-position rank-curve lookup (`a + b·ln(rank)`), never a per-player
component forecast. That was the reason full custom scoring cannot be computed in the browser
(FR-040) and the reason the answer there was "definitively dead."

**It is not dead if components can be sourced.** The founder had already reached for this:

> "we'll have to talk more about the custom scoring in the browser, maybe there's a calculation step
> back to the back end for things that we haven't backtested already"

Component projections would make any scoring format computable from one set of numbers — which is
custom scoring, multi-league support, and this league's stacking-bonus edge, all from the same input.
**Whether they can be obtained, and under what terms, is a research question, not a build one.**
Licensing must be established before use, not after.

## Initial read

Not the founder's own words — PM's read.

Three separate pieces of work, deliberately not collapsed:

| | Owner | Ask |
|---|---|---|
| Where component projections can be sourced, and on what licence | `researcher` | The unblocking question for FR-040 |
| Which of the three missing features are worth having | `researcher` → `design` | Evidence, not preference |
| Layout and palette for the tabbed pane and the board grid | `design` | FR-044 and FR-049 now have a reference |

**Do not treat "Yahoo has it" as "we should build it."** Thread 086 found the opposite for at least
one feature — an ambient recommendation feed users explicitly asked to have removed. The value of
these screenshots is as evidence of convention, not as a specification.

---

## Addendum — FantasyPros captures, same session

Founder's verdict on both products, verbatim:

> "yahoo seems to have gotten worse and looks like a childs toy"
> "fantasy pros still looks pretty good"
> "Their league settings is pretty good, only thing it's really missing is bonuses - this is what I've
> used for years, so probably my bias, but I like it - the player card looks great, the tabs etc, so
> easy"

**He named his own bias, which makes the read more useful rather than less.** He has used FantasyPros
for years, so "it looks good" partly means "it is familiar." That is still the standard his eye will
judge our screens against.

### The finding that matters commercially

**FantasyPros' custom scoring does not do yardage bonuses.** The founder has used it for years and
names this as the one real gap. Their Draft Configuration offers Standard / PPR / Half PPR / Custom
— reception value and the usual per-unit values, no threshold bonuses.

**That is this league's entire distinguishing feature.** Westwood pays +1/+1.5/+2 at 100/150/200
rushing and receiving and 300/350/400 passing, and they stack. If the tool the founder has used for
years cannot express them, and Yahoo's own rankings may not price them either (still untested — the
one-minute check in FR-052), then **no product his league-mates use is valuing ceiling the way his
scoring actually pays for it.**

This upgrades the bonus-pricing claim from "a plausible edge" to "an edge with a named, observed gap
in the incumbent." It also sharpens FR-054: a threshold bonus needs a per-game distribution, which is
exactly what a component-level bottom-up projection would produce and what nobody else appears to be
computing.

### Structure worth studying (observed, not endorsed)

- **Draft Configuration**: league type, scoring, draft type, **Opponent Pick Logic (Basic /
  Advanced)**, team count, **Draft Position with a Randomize button**, pick clock, and *"Sync Your
  League Settings From: Yahoo"*. Directly relevant to FR-040 — this is the settings screen we are
  about to specify, already built by someone else.
- **Position Values** — QB/RB/WR/TE/DST/K/Rookies each set Normal/… . That is per-position opponent
  bias, and with Opponent Pick Logic it is FR-047's territory shipped as two controls.
- **Draft Against** — expert rankings *or* a choice of ADP sources (composite, several best-ball
  providers, Yahoo and ESPN pre-draft lists). Multiple opinions, explicitly selected rather than
  blended.
- **Centre pane tabs**: Suggestions / Cheat Sheets / Draft Board. Right rail: picks with real team
  names and *"Next turn in 7 Picks"*.
- **Suggestion cards** carry *"48% Experts"* — the share of experts recommending that player — plus
  an **Upside Mode** toggle.
- **Player card**: ADP / ECR / Last Season / SOS across the top, then tabs (news, game logs, season
  stats, outlook, depth chart), and an AI "Consensus Draft Sentiment" panel scoring OVERALL / UPSIDE
  / BUST with prose beneath.

**Two cautions carried from thread 086.** "A competitor ships it" is evidence of convention, not of
value — that pass found a feature users explicitly asked to have removed. And the AI sentiment panel
is precisely the shape this project deferred on hallucination grounds; seeing it shipped elsewhere
does not change that reasoning.
