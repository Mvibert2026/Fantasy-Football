---
ID: 058
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: draft-day usability
---

## Source

Founder side-by-side of the running app against the design reference, both at v0.9, Draft tab, Board
sub-tab. Screenshots are in the session record; the design reference is
`docs/design-reference/` and the spec is `docs/FRONTEND-SPEC.md`.

**Standing instruction from the founder:** *"the design version is better and more pleasing and
usable."* Where this thread and the spec disagree, the spec wins — this is a gap list derived from
two screenshots, not a new design. **Audit each item against `FRONTEND-SPEC.md` before building it**
and report any item where I have misread the design.

This thread is deliberately partitioned by component so it can be split across parallel frontend
agents. **Do not let two agents take the same section.**

---

## SECTION A · Pace indicators — the founder's explicit ask

> "Here on the draft board I'd like indicators to if the amount taken is expected or more or less
> than expected, it's shown in design."

**The quantity is: how many players at this position have gone, versus how many would be expected to
have gone by this pick.** A signed number already exists in the running app — the `+2`, `±0`, `-1`
column in Position Scarcity. So this is not absent. It is **unreadable**, and the design shows why.

Current app, per position: a bar, `43 / 45 left`, and a bare `+2`.

Design, per position: a bar, `12/22`, a signed pace number, **plus two lines the app does not have**:

- **`tiers 1–2 gone`** / `tier 1 gone · tier 2: 1 left` — tier depletion, which is what actually
  determines whether you must act. "45 quarterbacks left" is nearly meaningless; "tier 1 gone" is a
  decision.
- **`5 <50% by 38`** — how many players at this position fall below even odds of surviving to *your
  next pick*. This is the product's core number applied at position level, and it is absent from the
  running app entirely.

**Build:**

1. **Make the sign legible.** `+2` currently states nothing about direction of meaning — two more
   taken than expected, or two fewer remaining? Label it, or render it as an explicit phrase. A bare
   signed integer under a draft clock is a guess.
2. **Add the tier-depletion line** per position.
3. **Add the `N <50% by <your next pick>` line** per position.
4. **Add DEF** to the scarcity panel. The design has five rows; the app has four.
5. **Order positions by urgency, not by a fixed QB/RB/WR/TE order.** The design lists RB, WR, TE, QB,
   DEF — scarcity-sorted, so the position you need to think about is at the top. Confirm against the
   spec whether the ordering is dynamic or a fixed design choice; if dynamic, that is the better
   behaviour and the reason it exists.
6. **Traceability footer.** The design carries
   `board.position_remaining · board.position_tier · pace vs board.consensus_rank` beneath the panel.
   The app has nothing. Note that this footer is also what makes the pace number interpretable — it
   names the baseline the comparison is against.

**Honest-null discipline applies.** If the pace number cannot be computed for a position — no
consensus baseline, insufficient data — it renders `—` or `not yet`, never `±0`. A computed
on-pace and an unavailable comparison are different claims and `±0` currently expresses both.

---

## SECTION B · Board rows and sorting

**B1 · Tier grouping is absent.** The design groups the list into labelled tier bands —
`TIER 2 · 1 player left`, `TIER 3 · 3 players left`, `TIER 4 · 9 players left`. The app renders a
flat list. This is a significant usability gap: tier breaks are where draft decisions are actually
made, and "1 player left in tier 3" is the single most actionable string on the screen.

**B2 · Positional rank is missing.** The app shows bare position (`WR`, `RB`); the design shows
`WR12`, `RB11`, `TE3`, `QB1`. Without it the founder cannot tell whether a wide receiver is WR12 or
WR30 without counting rows.

**B3 · Sort controls do not exist.** The design has an explicit `SORT:` row —
`Our rank | Consensus | Delta | Proj pts` — with the active sort marked. The founder called this out
specifically. Four sorts, persisted within the session.

**B4 · DEF is missing from the position filter.** App: `ALL / QB / RB / WR / TE`. Design adds `DEF`.

**B5 · Probability rendering differs** — app shows `16% → 9%`, design shows `1% - 2%`. Check the spec
for which is canonical rather than matching the screenshot. Whichever it is, the `<1%` case must
render distinctly from `0%`; that defect class was fixed once and must not regress.

**B6 · Row affordances.** The app has a star and an `X` per row; the design shows only `X` in the
captured region. Do not remove the star on the strength of a screenshot — check the spec. Report the
answer.

---

## SECTION C · Navigation and chrome

**C1 · Tab placement and treatment.** App: `BOARD / OPPONENTS / PREDICTIONS` in all-caps, in a
separate strip below the header, underline-active. Design: `Board / Opponents / Predictions` in
sentence case, as boxed tabs sitting on the content panel itself, with a filled active state. The
founder named the tab location specifically. Match the design system rather than approximating.

**C2 · No live-draft state indicator.** The design shows a `DRAFT LIVE` badge beside the product
name. The app shows nothing, so there is no visual distinction between a live draft and a dormant
board. Confirm against the spec what states exist and how each renders.

**C3 · League identity is thinner.** App: `PRIMARY LEAGUE (10-TEAM HALF-PPR) · 10T · PICK 3`. Design:
`Dynasty of Dorks · Sleeper · 10T · pick 3 · Snake · CURRENT` — real league name, provider, draft
type, and a current-league marker. This connects to the multi-league work in thread 040; coordinate
rather than duplicating it.

**C4 · Assistant placement.** The design docks the assistant bottom-right with a context line —
`Assistant · Draft room · pick 24`. The app does not show it on this screen. Cross-check thread 032
and D-014 before building; the assistant already exists and this may be a placement issue rather than
a missing feature.

---

## SECTION D · Roster rail

**D1 · Requirement chips are missing.** The design puts a compact chip row at the top —
`QB 0/1 · RB 1/2 · WR 2/3 · TE 0/1 · FLEX 0/2 · DEF 0/1 · BN 0/6`. The app renders the same
information as a wrapped text line above the roster. The chips are scannable under a clock; the text
line is not.

**D2 · No IR slot.** The design roster includes `IR`; the app's does not. Given the injury and
suspension work now specified in `docs/fable-mandate-2026-07-27.md` Addendum 2, this is about to
matter more than it currently does.

**D3 · `MY PICKS` section absent** from the app rail. Present in the design.

---

## SECTION E · Queue and Watchlist

**E1 · Presentation.** App: two large side-by-side buttons. Design: two tabs with a populated table
beneath, columns `PLAYER · BASE · LIVE IN 10`.

**E2 · Scope semantics differ, and this is a real behavioural difference, not styling.** App:
*"Account-wide: persists across leagues and seasons."* Design: *"this draft only · self-pruning ·
drafted players leave on their own."* Those are opposite designs for the Queue. **Do not guess.**
Check the spec; if the spec is silent, this is a decision and it comes to me before anything is
built.

**E3 · Empty-state copy.** The design's empty states carry the mechanic —
*"drafted players leave on their own"*, *"he leaves on his own if someone else takes him"*. The app's
is generic. The design copy teaches the behaviour at the moment it matters.

**E4 · Traceability footer** beneath the panel:
`availability.baseline_p → availability.live_p · adjustment.need + adjustment.run`. Absent from the
app.

---

## SECTION F · Traceability footers as a pattern

Two panels in the design carry a monospace footer naming the exact fields feeding the panel. The app
carries none. This is not decoration — it is the traceability principle made visible, and it is what
lets the founder tell a computed number from a placeholder without opening the code.

Audit **every** panel against the design for a missing footer, not only the two captured here.

---

## Done looks like

Per section: commits, tests, and a reply naming any item where the design reference or
`FRONTEND-SPEC.md` contradicts my reading above. **A correction is a successful outcome for this
thread** — I derived it from two screenshots and the spec is authoritative.

Screenshots of each changed surface if the sandbox permits it; if screenshots fail again, say so
rather than reporting the work as visually verified.

**File boundary:** `frontend/` only. Coordinate with threads 027, 028, 040, 049 and 051 — several
touch the same surfaces, and the suggester fixes in 051 are on the same screen.
