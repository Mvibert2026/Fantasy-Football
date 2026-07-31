# 2026-07-30 — frontend — player profile (item 2), archetype chip built both ways

Dispatched specifically to build design round-1 item 2 (`docs/design/PLAYER-PROFILE.md`), with the
archetype chip's placement built BOTH ways behind a flag because the founder has not ruled between
his own FR-075 placement request (identity strip, beside the name) and design's disclosed-section
amendment, and asked to see both before he does (thread 117 "Prepared answer 1", held).

## What shipped

- `frontend/ui/data/archetypePlacement.ts` — the flag. `'identity-strip'` (default, the founder's
  standing FR-075 instruction) vs. `'disclosed'` (design's amendment). Flippable per-screenshot via
  `?archetypePlacement=disclosed` on the URL or a `localStorage` key, no rebuild needed. Documented
  as temporary scaffolding, naming thread 121, to be deleted once the founder rules.
- `PlayerDetail.tsx`'s `showArchetypeChipInStrip` gates the identity-strip chip: always shown under
  Arrangement A; shown only for a real label under Arrangement B (absences move to the disclosed
  ARCHETYPE section, unconditionally rendered either way).
- **Design's second-order point** — the three archetype absences must be tellable apart, not three
  identically-grey chips — now holds in BOTH arrangements. `archetypeChipStyle` gives the four chip
  states (real / `UNCLASSIFIED` / `ARCHETYPE N/A` / `ARCHETYPE —`) four different border treatments
  (solid-filled / dashed / none+italic / dotted) — border STYLE, not colour, so it survives both
  themes and colour-blindness. Confirmed the three absences against real data rather than assuming
  the dispatch's own labels were the real ones: `UNCLASSIFIED` (covered position, classifier ran,
  met no threshold — James Cook III), `ARCHETYPE N/A` (position outside the taxonomy's scope —
  QB/DEF/K, confirmed with Josh Allen), `ARCHETYPE —` (league has no `player_descriptions.json`
  export at all — confirmed against `espn_10_full`'s real, on-disk export, true of every non-primary
  league today).
- Also shipped, self-contained: `PLAYER-PROFILE.md` §3's reading-level rewrite for the PROJECTION
  section's caveat. Design's plain-English sentence renders by default; the raw
  `board.json:curve_caveat` formula (R-squared etc.) moves behind the "show data sources" switch
  (same FR-114 pattern as every other trace-mode gate on this card), never deleted — Principle #2
  applies to prose, not just numbers.

## What was NOT built, and why

`PLAYER-PROFILE.md` §1's "both values" row (vs replacement / vs your options, side by side) and half
of §2's density rule 2 (one anchored "Disclosed" section, reached from the strip via a *Why that
matters* gesture). Both require a disclosure gesture that doesn't exist anywhere in this app yet.
Both also overlap work this dispatch did not assign: the "both values" row is item 8's own spec
(`TWO-VALUE-COLUMNS.md`), and a **2026-08-01** amendment already sitting in the repo
(`TWO-VALUE-COLUMNS-CONTAINER.md`) further redesigns that exact gesture for the ADP caveat
specifically. Building a competing version now risked shipping something design would immediately
have to redesign around once that round is released — flagged to thread 121 instead of guessed at.

Density rule 1 (zero-by-construction rows don't render) and rule 3 (human-precision timestamps) were
checked against the current card and found already satisfied by prior sessions' work — no change
needed.

## Verification

61 test files / 478 tests passing (was 59 files / 459 tests) — 3 new test files
(`archetypePlacement.test.ts`, `player-detail-reading-level.test.tsx`, plus 16 new cases appended to
`player-detail-archetype.test.tsx`). `npx tsc -b --noEmit` clean. `npm run build` not separately
run this session (dev server + tsc + full test suite were the checks used).

**18 screenshots**, looked at directly (not just a passing suite):
`frontend/e2e/artifacts/item2-arrangementA-dark-{01..04}-*.png` (real / unclassified /
not-applicable / not-available), the same four for Arrangement B, two light-theme pairs (one real +
one unclassified per arrangement), the reading-level default-vs-trace-mode pair, and a composite
`item2-absence-states-side-by-side.png` putting the three absence chips directly next to each other.
Script: `frontend/e2e/verify-item2-player-profile.mjs`.

## Handoff

Opened thread 121 (`FROM: frontend, TO: pm`) — both arrangements are built and screenshotted; PM
needs to put them in front of the founder for a ruling, then tell frontend which branch to delete
(the flag itself, the losing arrangement's code path, and the scaffolding-specific tests). Also
logged the "both values"/Disclosed-section gap and the border-style design decision to
`docs/ideas-inbox.md` per the decide-and-log standing instruction.

Did not touch the rest of the general frontend inbox (threads 003/006/007/030/031/035/036/037/040/
043/047/049/059/066/086/093/109/110/116) — this session's dispatch was scoped specifically to item 2;
those are a separate backlog for a future dispatch.

Commit `cacca25`.
