---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 1 (briefing §12)
DATE: 2026-07-29
COVERS: FR-049, FR-044, FR-048, FR-050, FR-055, FR-051, FR-045
---

# The draft screen's middle pane, specified once

Visual spec: `docs/design/spec-2026-07-29.html` (self-contained, opens in a browser).
Written against the running app per the founder's parity instruction. Where a screenshot and an
earlier spec of mine disagreed, the screenshot won.

## Two findings that change the shape of this before it is written

**1. The position colours already collide with the semantic accents.** `tokens.css` defines
`--rb #63b39b` against `--acc #5ecf9e`, `--wr #c39468` against `--down #f0993f`, and
`--te #7d9fcf` against `--up #5bb4f2`. Three of five positions sit on the same hues as the three
accents that already mean good / bad / delta. This is survivable today because positions only
appear as thin text labels. Fill a grid cell with them and the periodic table reads as a verdict on
every player. FR-044 raised this as a risk; it is already real.

**2. A pattern view cannot be a pattern in the middle pane.** The pane is roughly 640px at 1600.
Six cells across is a list with extra steps.

## The decision

**One tab set, in the pane, four tabs: Recommend · Scarcity · Queue · Insights.**

- **Not a second nested level.** The screen already has tabs eight inches above. Two levels of the
  same control, both switching content, is a guess every time under a clock.
- **NEXT DECISION is a persistent footer**, never behind a tab.
- **The grid leaves the pane** and becomes a full-width view beside Board / Opponents / Predictions.

### Separate finding, not fixed here

The existing top-level tabs swap the *entire* body — selecting Predictions during a live draft
removes the player list and the roster rail. That is the wrong trade under a clock. Recorded as a
finding; changing it is out of scope for this pass.

### Tabs

| Tab | Contents |
|---|---|
| **Recommend** | Default. The FR-049 ask. **Look-ahead is a toggle inside it**, not a second tab — same content computed at your pick instead of this one. Carries the not-backtested label described below. |
| **Scarcity** | Today's panel unchanged, plus the FR-045 suppression rule. |
| **Queue** | Queue and Watchlist, already in the pane. A tab because it is a between-picks view. |
| **Insights** | FR-048. Scoped to players on screen and to this pick. |

**Recommend carries a standing label.** `recommendation.ts` runs on four hand-picked constants
(+8 unfilled need, +18 tier-1 TE, −25 early QB) that the module itself calls a stopgap. Promoting
this panel to the default tab increases how much weight it carries. The label travels with it until
the model is registered with `strategist`. FR-049's own note says the honest sequence is to fix or
label before promoting; this is the label half.

**Insights scope rule.** An insight earns the tab only if it is tied to a pick available now.
Anything general belongs in the Strategy Guide. Otherwise this becomes the ambient
trending/recommended feed that the competitive research names as the one feature ESPN users
explicitly asked to have removed.

**FR-045 in Scarcity.** With auto-fill placeholders present, `gone` and `currentPick` are drawn
from different populations, so every position reads behind pace at once. The pace line renders
`not yet` and names the cause. It does not render a number computed across two populations. This is
option 1 in FR-045 and it is the one consistent with the null vocabulary.

## 1.1 The grid (FR-044)

Both questions the grid answers — *how much of this position is left*, *am I stacking one offence* —
are asked **between** picks. The position-by-team matrix is 32 teams by 5 positions and cannot be
squeezed at all. So the grid is a full-width view.

### The colour rule — decide this before anything is built

- Position hue **tints** the cell at low alpha (~13%) and owns its **left edge**. It never fills the
  cell at strength.
- **The semantic accents `--acc`, `--down`, `--up` are banned from the grid.** No exceptions. This is
  what keeps the collision above from becoming visible.
- **Depletion is the fast channel**, because it is what changes under a clock: available is full
  text, gone is dimmed and struck through, under 50% by your next pick carries a dot.
- **Every cell states its position as text.** The grid must survive a colour-blind reader and
  greyscale print. Hue is the fast channel, never the only one.
- **The text label is load-bearing, so it has its own rule.** `--f-ui` always — **never mono, in any
  context.** Position codes are labels, not measurements; `tokens.css` opens by naming mono on them
  as the thing that made the earlier board read as a terminal dump. Mono stays on the numeric cell
  beside it (rank, counts, VBD, ADP).

  **Size and weight depend on which of two jobs the code is doing:**

  | Job | Where | Treatment |
  |---|---|---|
  | **Dense label** — the non-hue channel, nothing else identifies the position | grid cells, table rows, roster chips, scarcity rows | **10px floor, semibold.** The case the colour rule rests on. Does not bend. |
  | **Inline annotation** — follows a player name at display size, which already carries identity | recommendation panel, next-pick reference block, player detail | 11px, regular weight. Semibold competes with the name it annotates. |

  The distinction is whether the code is the *only* thing identifying the position. In a grid cell it
  is, and it is doing accessibility work. Beside a 15px player name it is not.
- Hues are the five already in `tokens.css`, unchanged. `TEAM_COLOR` stays out of the fill — it is
  identity-only and belongs on an axis or a label, which is what the founder described anyway.

**Blocked input:** the founder said he would send Yahoo and FantasyPros captures so the hues match
what he reads fluently. Only one Yahoo capture is in the repo and no FantasyPros capture at all. I
have not re-picked the hues from memory of the category. If matching convention matters, that is the
missing input.

## 1.2 The next-pick reference point (FR-051)

Per the founder's own correction: **show the reference point, do not do the arithmetic.** No
advantage number, no subtraction. Two plain figures side by side; he does the comparison.

    CONSIDERING                    LIKELY THERE AT 3
    Jahmyr Gibbs  RB2              Puka Nacua  WR2
    VBD 62.4                       VBD 54.1 · 48.9-58.2 across sigma

- Overall by default, one per position on request.
- **The range is not decoration.** It is the spread across the sigma settings, shown the way the
  Predictions deviation control already shows uncertainty — never a single confident number. FR-047
  (deviation widening later in the draft) moves this figure directly.
- **Display only.** FR-051 also floats feeding this into the recommendation. That is a model change
  to register with `strategist`, not a display decision.

Fields: `availability.json:by_player` · `board.json:players[].vbd` · sigma from the deviation control.

## 1.3 Review of what shipped — column headers and VBD (FR-050, FR-055)

**I could not review the built version.** Every draft-room artifact in `frontend/e2e/artifacts/`,
including those dated 2026-07-29, shows the list with no header row. These landed after the last
capture and reviewing from stale screenshots would be guessing. Four rules to check against, and a
capture request so the next pass is a real review:

1. **Port Prep's labels verbatim** where the column is the same number. RANK, POS, TM, BYE,
   PROJ (CI), CONS, ADP, delta, VBD, TIER exist in `Board.tsx`. Two names for one number across two
   screens is its own defect.
2. **Sticky.** A header that scrolls away at row 11 has solved the problem for the first ten rows of
   a 511-row list.
3. **Abbreviations must survive without a legend, or the header reaches the glossary.** ADP and VBD
   are the two that will not survive alone — VBD is the number the board ranks on and nothing on
   screen currently says so.
4. **VBD needs real width, not a squeeze.** If something must give, the frequency dots are the least
   load-bearing thing in the row; they repeat what the percentage already carries.
