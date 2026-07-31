# Draft board — reference research

Researcher, 2026-07-30. Commissioned by FR-135. Persisted by PM: the researcher agent has no shell and
its `Write` to this path was refused by the harness, so it returned findings as text. Content below is
the agent's, not PM's.

---

## 0. Sample quality — read before the findings

Three products verified. **Two of them are one decision unit.**

| Product | What it is | Verification |
|---|---|---|
| **Sleeper** | League platform with a live draftboard | `[VERIFIED]` — own support articles + two of its own board images viewed |
| **LiveDraftX** | Dedicated draft-board vendor, no league hosting | `[VERIFIED]` — site + guide + four product images viewed |
| **FanDraft** | Dedicated draft-board vendor, no league hosting | `[VERIFIED]` — site + two product images viewed |

FanDraft and LiveDraftX are **not two data points.** Both sell a board to people running an in-person
draft off a TV, both priced per league, neither hosts a season. They agree for a structural reason —
same customer, same room, same projector. The honest n for *"what a league platform puts on screen
during a draft"* is **1 (Sleeper)**, plus two specialists optimising for a 65-inch screen ten feet away.

**And that one is dated.** Sleeper's board images come from support articles dated 2022-04-07 carrying
~2021 rosters (McCaffrey on CAR, Cook on MIN, Hopkins on ARI). LiveDraftX/FanDraft captures are current
— they contain 2025/26 rookies.

**The two largest platforms are absent.** Yahoo and ESPN are the boards the founder most likely has in
mind. Both are blocked to this agent at the host. If the design turns on "what Yahoo does," that is
**unanswered** and needs a human with a browser, not another research pass.

All six product images are **vendor marketing captures** — the product as the vendor wants it seen:
mid-draft, well-populated, wide screen. Good for layout and cell content; weak for 14-team boards,
pre-draft empty boards, and error states.

---

## 1. Blocked, recorded, not routed around

| Host | Status | Consequence |
|---|---|---|
| Every Yahoo host | robots disallows `ClaudeBot`/`Claude-Web`/`anthropic-ai` by name (`docs/research/yahoo-draft-assistant-2026-07-29.md`) | Not attempted. No Yahoo screenshot, no verified layout |
| Every ESPN/Disney host | Recorded ToU block (thread 009; ADR-063 cites Disney ToU §2.B.x/§2.A/§3.H) | Not attempted. ESPN claims are search excerpts |
| `www.sportsvideo.org` | robots names `ClaudeBot` under `Disallow: /` | Not fetched — was the best third-party ESPN-redesign write-up |
| `fantasyteamadvice.com` | Blocks `ClaudeBot`, `anthropic-ai`, `GPTBot`, `CCBot` | Not fetched |
| Underdog | 301s; robots **could not be established for the second audit running**; help centre 403s | Not fetched (FR-004 conservative default). **Absent from this document** |
| `support.fantasypros.com` | HTTP 403 — technical, not robots | FantasyPros claims are `[SNIPPET]` |
| `fantasy.nfl.com` | `Disallow: /league*` — the board lives under `/league`. Also being retired into ESPN | Not fetched, and a poor reference regardless |
| `www.reddit.com` | Refused by the tool | No user-voice evidence on board usability |

---

## 2. The converged shape

### 2.1 Axis orientation — unanimous; the founder is right

**Managers across the top, rounds down the side.**

| Source | Columns | Rows | Evidence |
|---|---|---|---|
| Sleeper | 10 manager columns — avatar + name + online dot | rounds, top to bottom | `[VERIFIED]` |
| LiveDraftX | 10 fantasy-team-name columns | `R1..R10`, rotated labels in a left gutter | `[VERIFIED]` |
| FanDraft | 10 team-name columns | `RD` gutter, `1..12` bold numerals | `[VERIFIED]` |
| FantasyPros Draft Wizard | *"plots each team across the top and each round down the side"* | same | `[SNIPPET]` |

**Nobody transposes at any width** — `[VERIFIED]` ×3, `[GAP]` for Yahoo/ESPN. Narrow widths do not
transpose; they switch to a different component (§3). One dissent, about *physical* boards only:
horizontal suits a long table, vertical suits a wall `[SNIPPET]` — a room-shape constraint, not a UI one.

### 2.2 What occupies an empty cell — the founder's "empty at first" question

| Product | Unmade cell contains | Evidence |
|---|---|---|
| **Sleeper** | **The pick label, nothing else** — `2.10`, `3.2`, `7.1` top-right of a flat grey tile | `[VERIFIED]` |
| **FanDraft** | **The pick label as a watermark** — `6.1`…`12.10` in light grey, whole future rounds pre-labelled | `[VERIFIED]` |
| **LiveDraftX** desktop | **A skeleton only** — dark rounded rectangle, small grey stub where the position chip sits. No number | `[VERIFIED]` |
| **LiveDraftX** mobile, round list | **The owner's name** — `2.05 Bed Bath & Bijan` | `[VERIFIED]` |
| **LiveDraftX** mobile, single team | **An em-dash** — `R4 —` | `[VERIFIED]` |

**Convergent: an empty cell is never blank.** It always carries at least its own address. Two of three
carry the pick number; the third keeps a shaped placeholder so the grid holds its rhythm. Nobody
leaves a hole.

### 2.3 How the snake is expressed — **nobody draws it**

No arrow, no serpentine line, no direction marker, in any of the three `[VERIFIED]`. It is conveyed by:

1. **Numbering.** Sleeper's filled cells carry `round.pick`, and on even rounds those run *backwards
   across the row*: round 2 reads `2.10` in the leftmost column and `2.1` in the rightmost.
   `[VERIFIED]` in **both** Sleeper captures independently. On Sleeper the snake is arithmetic you can
   read off the board, filled or unfilled.
2. **Fill order.** LiveDraftX's round view has **no numbers in cells at all**. Round 8's filled cells
   run right-to-left, on-the-clock at column 3, columns 1–2 empty `[VERIFIED]`. The snake is inferable
   only from which cells are filled — which works only while you are watching it happen.

**FanDraft's numbering does not demonstrate a snake and the agent declined to claim it does.** Whether
FanDraft renumbers even rounds is `[GAP]`.

FanDraft documents the failure mode, and it is the most decision-relevant sentence found `[SNIPPET]`:

> "Because a standard draft board works in a column/row type grid, if you have a different draft order
> for multiple/all rounds, the 'Draft Board Display' will appear confusing, so you can utilize either
> the 'Roster Board' or 'Player Board' displays during your draft instead."

The vendor's own answer to "the grid stopped being legible" is **switch views**, not annotate the grid.

### 2.4 What a filled cell carries

| Element | Sleeper | LiveDraftX | FanDraft |
|---|---|---|---|
| Surname, largest text | yes | yes | yes |
| First name / initial | initial, truncated | full, small, above surname | full, small, above surname |
| Position | text **and** whole-cell colour | filled chip + coloured border + tint | whole-cell colour + small text |
| NFL team | yes | yes, footer right | no |
| Bye week | yes, in parentheses | yes, `BYE 11` | yes, before the position |
| Pick number | **yes**, top-right | **no** | **no** (only in empty cells) |
| Player photo | **yes**, headshot | no | no |

**Convergent minimum: surname + position colour.** All three make the surname the largest thing.

**None of the three drops the surname at any density observed.** Worth stating plainly given this
project shipped a screen that dropped the player's name at 1180px. The surname is the last thing to
go, not the first.

### 2.5 Current pick, and your own picks

**Current pick — redundantly marked, always more than once.**

- **LiveDraftX** marks it **four ways at once** `[VERIFIED]`: column header red, row header red, cell
  becomes a red-bordered `PICK YOUR PLAYER` target, plus a bottom-bar `ON THE CLOCK` panel with timer.
- **FanDraft** marks it in-cell (`● PICKING`, green border) **plus** a top bar with timer, round/pick,
  team name, a `NEXT UP` chain of the next three, and a previous-pick card `[VERIFIED]`.
- **Sleeper** — `[GAP]`. Neither capture shows an on-the-clock state.

**Your own upcoming picks — `[GAP]`, and it is a real gap.** No capture shows distinct treatment for
the viewing user's column or next pick. Do not read this as "nobody does it"; read it as unverified.

### 2.6 A position-ordered view exists — **but it is not the one the founder described**

**This is the most important divergence in the document.**

It exists, in both specialists `[VERIFIED]`. LiveDraftX's guide on its Roster view: *"will re-arrange
the draft board and sort all picks by position."*

**What the Roster view actually is** `[VERIFIED]`: the same ten manager columns in the same order, but
the left gutter changes from `R1..R10` to **roster slots** — `QB, RB, RB, WR, WR, TE, FLEX, K, DST, BN`.
Each manager's picks are re-slotted into the lineup they would start; unfilled slots are ghost cells.
It answers **"what has each team built, and what do they still need?"**

**The founder's stated purpose is different.** FR-135 records view 2 as *"the thing that tells you the
RB room emptied in the third round."* The Roster view **cannot** tell you that — it has thrown the
round axis away. On every product reached, positional runs are read off the **colour of the pick-order
board**, not off a second view. Sleeper says so itself `[VERIFIED]`: *"By seeing the entire board, you
gain extra context into … position runs."*

So: **the founder asked for one artifact and named the purpose of a different one.** Both are real and
both are shipped. That is a decision to make deliberately, not a discrepancy to paper over.

### 2.7 The fourth view — and the disposition of `PeriodicTableGrid.tsx`

LiveDraftX's fourth view, **NFL Teams**, *"lays out the entire player pool in columns, one per NFL
franchise"* `[SNIPPET]` — and the agent viewed it `[VERIFIED]`: 32 columns headed `ARI ATL BAL BUF…`,
rows grouped by position, each cell a position chip + name + bye + team, and **drafted players rendered
dimmed and greyed** while available players stay bright.

**That is, feature for feature, the component this project already built** and the one
`docs/design/PERIODIC-TABLE-GRID.md` specced ("gone is dimmed and struck"). FR-135 asks whether to keep
it under an honest name. **The evidence says yes** — it is a real, shipped view in a real draft-board
product. It is simply the *fourth* view, alongside the board, never in place of it. Naming it what
LiveDraftX calls it ("NFL Teams") would describe it accurately.

---

## 3. The screen-size problem

10 columns × 16+ rows. The constraint most likely to break the build.

**The verified answer is a breakpoint switch, not a scroll.** LiveDraftX's guide, verbatim `[VERIFIED]`:

> "On a phone (or any window narrower than a tablet), the draft board switches to a mobile view built
> for small screens."

Both mobile views were viewed. **The grid is abandoned outright** — not frozen-column, not
horizontally scrolled, not zoomed:

| Mobile view | What replaces the grid |
|---|---|
| **ROUND** | Vertical list of picks within one round. The round axis becomes a horizontally-scrollable chip row `R1…R7`, current round ringed red. Rows carry pick number · player · fantasy team · position chip · NFL team. Unmade picks are rows too, showing pick number + owner |
| **TEAMS** | One manager's picks as a list. Manager axis becomes a chip row; a second toggle switches **BY ROUND / BY ROSTER**; future picks read `R4 —` |

**Both axes survive; only the two-dimensional rendering dies.** Whichever axis you are not listing
along becomes a chip selector at the top. That beats a frozen first column because cell content stays
full size.

Corroborating: **Sleeper** ships two different board implementations and says so — Big Screen Mode is
web only, *"not available from a mobile device"* `[SNIPPET]`. **ESPN's** modernised board is *"available
only in the ESPN Fantasy app"* `[SNIPPET]`, unverified.

### 3.1 The arithmetic this implies

From the LiveDraftX desktop capture `[VERIFIED]`: ten manager columns plus the round gutter occupy ~90%
of frame width, so **one column gets roughly 1/11 of the viewport.**

Derived: at **1180px** — the width at which this project already dropped a player's name — a 10-team
board gives each column **~107px**; a 12-team board **~90px**. At 90px you fit a surname and a position
chip. You do not fit a surname, a first name, an NFL team, a bye week, a pick number *and* a headshot.
**Something must be designed out, and the boards that work designed it out on purpose rather than
letting it overflow.**

---

## 4. Recommendation

### 4.1 Build the board the whole category builds
Managers across the top, rounds down the side, one cell per pick, empty at the start. Unanimous, and
exactly the founder's description. No evidence for a variant; no reason to invent one.

### 4.2 Number every cell, filled and empty, and let the numbers carry the snake
Take **Sleeper's** treatment over LiveDraftX's: `round.pick` in every cell from first render. One small
label buys three things — the empty board is legible before a pick is made (otherwise it is a wall of
identical rectangles); the snake becomes *readable* rather than inferable, because round 2 visibly
counts **down** across the row, matching the category's refusal to draw it; and the founder's slot-3
position and next pick become countable off the board. This project already ships `roundPickLabel` in
`ui/data/draft.ts`.

### 4.3 A cell-content ladder, decided now rather than discovered at 1180px

```
always      surname (largest) · position colour
wide        + first initial · pick number
wider       + NFL team · bye week
widest      + anything else
```

Drop in that order, because it is the order in which the three verified products differ — every item
below the surname is already absent from at least one shipping board. **No product verified puts a
projection, VBD figure or delta in a board cell** (`[VERIFIED]` ×3, `[GAP]` Yahoo/ESPN);
`PERIODIC-TABLE-GRID.md` reached the same conclusion independently.

**One divergence handed back to design deliberately:** all three verified products use *saturated*
position colour. `POSITION-COLOUR-RESOLUTION.md` settled on a ~13% tint plus a filled pill. That is
`STATUS: RESOLVED` and is not reopened here — recorded only that the category runs considerably hotter,
and that on a board read from across a room the colour *is* the data.

### 4.4 Mark the current pick more than once; the user's own pick has no precedent
Current pick: **column header + the cell + a persistent panel** `[VERIFIED]`. Redundancy is the
convention, not decoration — on a 10×16 grid a single highlight is a needle in a haystack.

The user's own next pick: **`[GAP]` — no product verified marks it.** This project has a reason to want
it the category lacks (fixed slot, 4-team playoff, an availability model that already computes what
survives to his next turn). Treat it as an original design decision with no precedent to copy, and say
so on the spec rather than implying convergence.

### 4.5 The two views, named honestly

**View 1 — Pick order (snaking).** As above. Default.

**View 2 — ship the description, not the label.**

- The category's "position view" keeps manager columns and swaps rows to **roster slots** `[VERIFIED]`.
  It answers *what has each team built and what do they still need.* It **cannot** answer the RB-room
  question — it discarded the round axis.
- The RB-room question is answered on **view 1**, by colour, in every product reached.

**Recommendation: build the roster-slot view as view 2** — two independent implementations to copy,
genuinely useful, and it reuses the same manager columns so the transition is a row-axis animation
rather than a new screen. Then satisfy the stated *purpose* on view 1 with something cheap: a per-round
positional tally in the left gutter (already present, holding only the round number, and empty space in
all three products). `4 RB` next to round 3 is the RB-room answer, on the board that still has the
round axis.

**Do not silently ship the roster view and call FR-135 satisfied.** The founder will look for the RB run
and it will not be there. If design prefers a literal position-sorted grid of made picks, that is
defensible — but it has **no precedent in anything reachable**, and should be recorded as an original
invention, not as following the category.

### 4.6 Narrow width: switch component, do not squeeze the grid
Adopt LiveDraftX's rule `[VERIFIED]`. Below tablet width the board becomes a list and the un-listed
axis becomes a chip selector. Unmade picks still render, as `R4 —`. The team list's **BY ROUND / BY
ROSTER** toggle means **view 2 arrives free on mobile**.

A frozen first column plus horizontal scroll is the obvious alternative and **no product was found
doing it.** That is not proof it is wrong — it is `[GAP]` on whether anyone has tried.

---

## 5. Gaps — enumerated, not to be filled by inference

1. `[GAP]` **Yahoo's board** — layout, cell content, empty state, narrow-width, all of it. Blocked at
   robots by agent name. **Biggest hole in the document; needs a human with a browser.**
2. `[GAP]` **ESPN's board.** Blocked. Only a search excerpt survives: *"shows everyone's draft results
   … including color coding for each position… available only in the ESPN Fantasy app"* `[SNIPPET]`.
   The app-only claim, if true, is significant and is unconfirmed.
3. `[GAP]` **Underdog** — robots could not be established for the second audit running. Absent entirely.
4. `[GAP]` **Sleeper's current board.** Captures are ~2021/22 vintage.
5. `[GAP]` **Sleeper's on-the-clock treatment.**
6. `[GAP]` **Whether FanDraft renumbers cells on even rounds.**
7. `[GAP]` **Whether any product marks the viewing user's own next pick.**
8. `[GAP]` **Any product using a frozen first column + horizontal scroll.** Found none; did not
   establish none exists.
9. `[GAP]` **How FanDraft's grid degrades on a phone.**
10. `[GAP]` **12- and 14-team boards.** Every capture is 10 columns. The primary league is 10, so not
    blocking — but §3.1's arithmetic worsens and nothing verified says where these products give up.

---

## 6. Images — viewed, deliberately not committed

See `IMAGE-SOURCES.md` for the manifest of eight images the agent fetched and looked at directly.

**They are not in this repo, on purpose.** The agent's own note: *"Fetching is settled; redistributing
is not — committing a vendor's marketing capture into this repo is republication, and none of these
vendors grants it."* This repo is deployed publicly. PM has left that decision open rather than
downloading them.

**Dead end, recorded:** the App Store route. `apps.apple.com/robots.txt` permits listing pages
`[VERIFIED]`, but the Sleeper listing serves screenshots as `1x1.gif` placeholders with no reachable
real URL without executing page JS. This looked like a clean way to get publisher-supplied Yahoo/ESPN
captures without touching their hosts. It is not one.
