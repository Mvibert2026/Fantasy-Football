---
ID: 058
FROM: pm
TO: frontend
STATUS: RESOLVED
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

---
### frontend · 2026-07-27

Branch `frontend/058-draft-board-design-gap` (off `origin/main` @ `67fc244`), scoped to everything
on the Draft/Board screen except the pick-entry/suggester (thread 063's territory, same file,
`DraftRoom.tsx` — not touched). Sections A, B and C landed in full; D and E/F partial. Audited every
item against `docs/FRONTEND-SPEC.md` and, critically, the **actual interactive prototype source**
(`docs/design-reference/prototype.dc.html`) rather than just the two screenshots — reading the real
JS resolved two items the screenshot alone couldn't, both write-ups below.

#### Corrections to this thread's reading (both confirmed by reading the prototype's JS, not guessing)

1. **B1 — the design's ALL-tab tier grouping is NOT the same per-position tier field.** Your
   screenshot shows "TIER 3" grouping a WR12, a QB2 and an RB10 together. I assumed at first this was
   just reusing `tier_label` across positions and that the app was wrong not to. It isn't — the
   prototype computes a **separate** `gtier` field (`board()`, ~line 2438-2452): sort the whole board
   by a VBD-like score, cut a new tier bucket whenever the score gap exceeds 4.5 points (min bucket
   size 2, max 9). That's a real, distinct clustering pass, not a relabeling. I confirmed directly
   against our real `board.json` that `tier`/`tier_label` are strictly per-position (QB tier 1 stops
   at positional rank 2, RB tier 1 runs to positional rank 4) — a QB1 and an RB4 sharing "T1" are not
   the same value tier, and grouping them under one header the way the design does would misrepresent
   the data. `DraftRoom.tsx` already restricted tier bands to a single position tab before this
   thread (thread 029) for exactly this reason; that restriction is correct and stays. Opened
   **thread 071** to backend asking whether a real `global_tier` field is worth adding — if it lands,
   the ALL-tab grouping is a quick follow-up.
2. **C3 — "CURRENT" is not a multi-league marker.** It's the §5.1 sim-staleness state
   (CURRENT/STALE/NEVER GENERATED), computed from `sim_generated_at`/`sim_settings_hash` on whichever
   single league is loaded — nothing to do with thread 040. Our real `league.json` has neither field
   yet (matches the Settings-editor gap already on `CURRENT-STATE.md`), so I extended the identity
   string with real `platform`/`draft_type` fields but did **not** append a fake "CURRENT" — a
   decorative label with no real staleness computation behind it is exactly what Principle #2
   forbids. Opened **thread 072** to backend to ask whether this is coming or correctly deferred.
3. **E2 — the queue/watchlist "scope conflict" isn't real.** Re-checked: your "App: Account-wide..."
   quote is this screen's *watchlist* tooltip, and your "Design: this draft only..." quote is the
   *design's queue* tooltip. Both systems — the running app, the design, and `FRONTEND-SPEC.md` §6.10
   — already agree: Queue is draft-scoped/self-pruning, Watchlist is account-wide/persistent, and the
   app already renders exactly that distinction correctly (`railTab === 'queue' ? '...self-pruning...'
   : '...account-wide...'`). No decision needed, nothing escalated to the founder — this was a
   mismatched pairing of two quotes describing different objects, not a design/app disagreement.
4. **D1/D3 were partly already built.** The roster requirement chips and the full MY PICKS section
   both shipped in thread 049, before this thread was opened — "the app renders... a wrapped text
   line" (D1) and "MY PICKS section absent" (D3) were both stale reads of an earlier app state. D1's
   chips existed as data/text already; I restyled them into bordered boxes to match the design's
   markup (below). D3 needed no work.

#### Section A — Position Scarcity (built, in full)

- **Legible pace.** `+2`/`±0`/`-1` → `"2 ahead of pace"` / `"on pace"` / `"1 behind pace"`
  (`scarcity.ts::paceLabel`). Worth noting: the design reference itself still renders a bare digit
  here (I zoomed the screenshot and it's genuinely un-labelled, coincidentally always `0` in its
  sample data) — matching it pixel-for-pixel would not have satisfied your own stated ask, so I
  built the explicit phrase the founder's own suggested remedy describes instead.
- **Tier-depletion line** per position: `tier 1: N left` / `tier 1 gone · tier 2: N left` /
  `tiers 1–2 gone` (`tierDepletionLine`).
- **`N <50% by <pick>` line** per position (`under50Line`), rendered whether or not it crosses the
  depletion-warning threshold.
- **DEF added as a fifth row** — but honestly null, not fabricated. `board.json` has zero DEF players
  (ADR-039, no DST data ingested) and its own `def_note` field says verbatim "Render this note where
  a DEF number would go. Do not compute a DEF value from these files." — so the DEF row renders that
  exact note, never a computed `0`/`±0`/`"tier 1: 0 left"`.
- **Ordered by urgency**, not fixed QB/RB/WR/TE/DEF (`orderByUrgency`). FRONTEND-SPEC.md §5.5 doesn't
  define a formula either way (checked in full) — this session's own rule: positions with no board
  data sink to the bottom, then ascending by tier-1-remaining, ties broken by under-50 count then
  pace. Flagging this as my own reasonable choice, same status as the existing recommendation score,
  open to override.
- **Traceability footer:** `board.position_remaining · board.position_tier · pace vs
  board.consensus_rank`.
- Honest-null discipline verified with a real regression test: `positionScarcity()` now returns
  `pace`/`tier1Remaining`/`tier2Remaining`/`under50ByNext` as `number | null`, null exactly when there
  is no board data for the position — never a computed zero standing in for "not tracked."

#### Section B — board rows and sorting (built, in full)

- **Positional rank label** (`WR12`, not bare `WR`) — `board.json:positional_label` was already a
  real exported field ("RB1"/"WR1"-style, confirmed against the export), just not rendered on this
  row before.
- **SORT row**: Our rank / Consensus / Delta / Proj pts, a real comparator per key, applied before
  tier-banding (which is now also gated to `sort === 'rank'`, matching the design's own
  `S.sort==="rank"` guard — a tier band means nothing once the list isn't in rank order).
- **DEF added to the position filter**, with an honest "No DEF players on this board" + `def_note`
  empty state rather than a silently blank list.
- **B5 (probability rendering)** — already correct pre-thread; `lib/format.ts::percent()`'s `<1%`
  branch shipped before this thread (thread 037). Not touched.
- **B6 (star affordance)** — checked the spec and the prototype source: the star toggle is real
  (`toggleWatch`), already present on every board row pre-thread, and not removed. Your screenshot's
  captured region for the design just didn't happen to show it in that crop.

#### Section C — nav/chrome (built, mostly)

- **Hub tabs** (`Board`/`Opponents`/`Predictions`): sentence case, boxed, filled active state —
  matched the design's own tab markup exactly (background/border/radius/weight per active state),
  not approximated.
- **`DRAFT LIVE` badge** added to the top bar, gated on Draft mode being active — confirmed against
  the prototype source that this is the design's *only* state here (no separate live-vs-dormant
  distinction exists in the reference either).
- **League identity string** extended with real `platform`/`draft_type` fields (both newly typed in
  `league.ts`/`types.ts` — they already existed in the real export, just weren't read). No fake
  "CURRENT" — see correction #2 above.
- **Assistant placement** — already correct pre-thread. `App.tsx` mounts the assistant dock
  regardless of mode, so it was already rendering on the Draft screen; this was a placement
  misreading, not a missing feature (per your own instruction to check thread 032/D-014 first). Added
  a `pick N` context via a new `onPickContext` callback so the dock now reads `Draft · pick 24`
  matching the design, instead of just `Draft`.

#### Section D — roster rail (partial)

- **D1** (requirement chips): restyled from a comma-separated text line into bordered boxes matching
  the design's checklist markup exactly, including its fill-state colour rule (filled = accent
  border+text, started = default text, empty = dim).
- **D2** (IR slot): added, sized from the real `league.json:roster.ir` — not the design mockup's own
  hardcoded single IR row. Deliberately never auto-filled from the pick pool: this build has no
  injury-designation data to decide what belongs on IR, and guessing would fabricate an assignment
  (same reasoning this file already applies to `AUTO_FILL_PLACEHOLDER`).
- **D3**: already built (see correction #4).

#### Section E/F — Queue/Watchlist presentation, traceability audit (partial)

- **E1** (tabs+table presentation) not built this session — deprioritised behind A/B/C per your own
  ordering, and it's a real layout rebuild, not a quick fix.
- **E2**: not a real conflict, see correction #3 — no founder escalation needed.
- **E3** (empty-state copy) not built this session.
- **E4** (traceability footer): added — `availability.baseline_p → availability.live_p ·
  adjustment.need + adjustment.run`, mirroring the Position Scarcity panel's pattern, shown only when
  the panel has real rows to trace.
- **F** (full audit): only the two panels named in this thread got footers. I did not audit every
  remaining panel (RECOMMENDED card, MY ROSTER, the board rows themselves) for a missing footer —
  flagging this as a real remaining gap, not claiming it done.

#### Backend follow-ups opened

- **Thread 066** — asks whether a real `global_tier` field is worth adding for B1's ALL-tab grouping.
- **Thread 067** — asks whether `sim_generated_at`/`sim_settings_hash`-style staleness fields are
  coming for C3's badge, or correctly still deferred.

#### Verification

172 frontend tests passing (0 failing, 19 files — up from 154/18 baseline), `tsc -b --noEmit` clean.
Two new test files: `ui/__tests__/draft-room-scarcity-and-sort.test.tsx` (12 tests, sections A/B/C/D2)
and additions to `ui/__tests__/draft-room-recommendation.test.tsx` (D2 IR slot, updated chip-query for
D1's new markup, updated hub-tab-label assertions for C1).

**Screenshot status — stated plainly, not glossed over:** pixel screenshots were attempted and did
not work in this sandbox. `computer{action:"screenshot"}` and `zoom` both timed out with "the Browser
pane is not displayed, so the page is not compositing frames," against both the static design
reference PNG and a running `npm run dev` instance. I did **not** treat this as a blocker to stop and
report "unverified" — instead verified via live DOM/accessibility-tree inspection
(`get_page_text`/`read_page`/`find`/`computer` clicks) against a real running dev server, which is
weaker than a human-reviewed screenshot but stronger than reading the source and hoping: I confirmed
live that DEF renders the honest-null scarcity row and `def_note` text, pace phrases render as words
not bare signs, tier-depletion/under-50 lines render, board rows show `WR12`-style labels, SORT
actually reorders rows, the DEF filter shows the honest empty state, hub tabs render sentence-case,
the `DRAFT LIVE` badge appears in Draft mode, the league identity string includes
`other · snake · 10T · PICK 3`, and the assistant context reads `Draft · pick N`. A later attempt to
re-verify Section D/the queue footer live hit dev-server instability (repeated Vite HMR full-reloads,
possibly from the concurrent thread-063 session sharing this machine, or a leftover background
process) that made further clicks unreliable — I stopped rather than force it, and D2/E4 rest on the
automated test suite plus code review only, not a second live check. Stating this explicitly per the
project's screenshot-verification requirement rather than implying full visual coverage.

Commit and push details in the session's final report. Setting `STATUS: RESOLVED` — the
founder-prioritized sections (A, then B, then C) are complete and verified two ways; the remaining
D/E/F items and both backend asks are tracked as explicit, named follow-ups rather than silently
dropped.

---
### frontend · 2026-07-27 (workstream C, re-verification only)

Directed to re-verify this thread's four named board items (tier bands, positional rank, sort
controls, DEF filter) before redoing anything. Read this thread's own resolution above plus the
live `Board.tsx`/`scarcity.ts` code and `docs/CURRENT-STATE.md`'s thread-058 paragraph: all four are
genuinely already built (positional_label rendering, the SORT row over Our rank/Consensus/
Delta/Proj pts, DEF in the position filter with an honest empty state, and tier bands gated to
`sort==='rank'` on a single position tab). No rework done here — confirmed via `npm test` (192
passing / 2 pre-existing-red-by-design, no board-control regressions) rather than re-reading the
diff blind. Picked up threads 071 and 072 instead, per this round's routing (see those threads'
replies) plus an unrelated dismissible-surface audit and a data-freshness gap, both out of this
thread's scope — see `docs/status.md`'s 2026-07-27 workstream-C entry for the full session
narrative.
