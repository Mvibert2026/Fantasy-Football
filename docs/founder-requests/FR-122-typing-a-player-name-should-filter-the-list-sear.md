---
ID: FR-122
STATUS: SHIPPED
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
---

## Request

Founder's own words:

> "when typing in a player's name , the list should begin to shrink down based on possible
> parameters so it can be used as a searcha s well as 'drafted' function"

## Why it matters

**One control, two jobs, and the second one is on the clock.** Marking a player drafted is the most
frequent action in a live draft — it happens on every pick, by every team, and every second it costs
is a second not spent deciding. Today that means finding a row. With incremental filtering it means
three keystrokes.

The search half matters for a different reason: it is the only way to answer *"where is he?"* about
a player who is not near the top of the board. On a 510-row list with the name column truncating to
seven characters at 1500w — and **absent entirely at 1180w** (`RANKINGS-PANE.md`) — visual scanning
is not a reliable way to find anyone.

## Initial read

**Buildable now, no design needed, and it is small.** Incremental substring filter over the board
list. The founder described the behaviour precisely enough that there is nothing to spec.

Details worth getting right, none of which need a designer:

- **Match on more than the display name.** Team, position, and positional rank (`RB10`) should all
  filter, because at 1180w the positional rank is the only identity a row has. Typing `RB1` should
  narrow to running backs ranked 1 and 10–19, not return nothing.
- **Diacritics and punctuation folded.** `Ja'Marr`, `JaMarr` and `jamarr` all match. Name matching
  has already cost this project real work — the mock-draft ingestion quarantined eight players on
  ambiguous names this session — so fold aggressively for *search*, where a wrong match costs one
  keystroke, while keeping ingestion's strict matching where a wrong match corrupts data.
- **Do not auto-select on a single match.** A filter that narrows to one row and then acts is how a
  mistyped name becomes a wrong pick recorded in a live draft.

**Sequencing conflict:** it lives in the same component as item 6 (`RANKINGS-PANE.md`), which is
already queued and rewrites that list's column structure. Building both in parallel means a merge
conflict in one file for no gain. **Fold it into the item 6 dispatch** rather than dispatching it
separately.

## Resolution (2026-07-30, frontend)

Built exactly as scoped, folded into the same item-6 dispatch as this file predicted. Reuses the
existing pick-entry field (`query` state, `DraftRoom.tsx`, already there for RETROFIT-5's digit-key
commit flow) rather than adding a second input — "one control, two jobs."

- **New `ui/data/playerSearch.ts`**: `normalizeSearchTerm` (NFD-normalize, strip combining marks,
  strip everything but letters/digits, lowercase — so `Ja'Marr`/`JaMarr`/`jamarr` and
  `RB10`/`rb-10`/`RB 10` all reduce identically) and `matchesPlayerQuery`, matching against display
  name, team, bare position, and `positionalLabel` (`RB10`) — the four fields this FR names.
  `RB1` correctly substring-matches `RB1`/`RB10`–`RB19` (and `RB100`+, a safe superset, never a
  narrower result than the FR's own example) because `positionalLabel` values start with it.
- **Wired into the rankings pane's row list**, not just the existing 5-slot commit suggester (which
  is untouched, still name-only, still exactly RETROFIT-5's own scope): a non-empty query searches
  the **full** board, superseding — not additionally constrained by — whichever position tab is
  selected, so `RB1` while the `QB` tab is active still finds running backs rather than "narrows to
  nothing." Tier bands (position-scoped, see the code's own pre-existing ALL-tab reasoning) are
  suppressed the same way they already are for the `ALL` tab, since a search result can span
  positions.
- **Does not auto-select or auto-commit.** Narrowing to exactly one row does nothing beyond
  narrowing; committing still requires Enter, a digit shortcut, or a click, per the FR's own
  explicit "wrong pick recorded in a live draft" caution.
- **Honest states**: the row-count label switches from "`N` left" to "`N` match" while a search is
  active (a different claim, not the same number relabelled), and a zero-match query renders
  `No still-available player matches "…"` rather than a silently blank list.

Verified against the real board (511 players): typing `RB1` narrows "508 left" to "78 match" and
still surfaces `RB10`–`RB19` rows; a nonsense query renders the honest empty state. Screenshots:
`frontend/e2e/artifacts/rankings-pane-05-search-before.png`,
`rankings-pane-06-search-after-RB1.png`, `rankings-pane-07-search-no-match.png`. Tests:
`ui/__tests__/playerSearch.test.ts` (9, pure matching-logic unit tests) and
`ui/__tests__/draft-room-search-filter.test.tsx` (8, wired end-to-end against `DraftRoom`).
