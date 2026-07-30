---
ID: 121
FROM: frontend
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Design round-1 item 2 (`docs/design/PLAYER-PROFILE.md`) was dispatched with the archetype chip
placement built BOTH ways behind a flag, per thread 117 "Prepared answer 1" — FR-075's own
placement request (identity strip, beside the name) vs. design's disclosed-section amendment. The
founder has not ruled between them and asked to see both first. This is now built, tested, and
screenshotted both ways. **Ask: put both arrangements in front of the founder for a ruling, then
tell frontend which one wins so the losing branch and the flag itself can be deleted** (this file's
own comment already flags itself as scaffolding for exactly that removal).

**What's built:**
- `frontend/ui/data/archetypePlacement.ts` — the flag. `ArrangementPlacement = 'identity-strip' |
  'disclosed'`. Default `'identity-strip'` (the founder's standing FR-075 instruction — if this flag
  is never touched, the shipped behaviour is what he actually asked for). Override for a screenshot
  without a rebuild: `?archetypePlacement=disclosed` on the URL, or
  `localStorage.setItem('prep.archetypePlacement', 'disclosed')`.
- `frontend/ui/components/PlayerDetail.tsx` — `showArchetypeChipInStrip` gates the identity-strip
  chip: always shown under Arrangement A; shown only for a real label under Arrangement B (absence
  states move to the disclosed ARCHETYPE section, which renders unconditionally either way).
- **Design's second-order point** (three absence states must be tellable apart, not three
  identically-grey chips) is now true in BOTH arrangements: `archetypeChipStyle` gives each of the
  four chip states (real / unclassified / not-applicable / not-available) a different border
  treatment — solid-filled / dashed / none-italic / dotted — not colour alone, so it survives both
  themes and colour-blindness. The three absence cases, confirmed against the real data this
  session (not assumed): `UNCLASSIFIED` (covered position, classifier ran, met no threshold),
  `ARCHETYPE N/A` (position outside the taxonomy's scope — QB/DEF/K), `ARCHETYPE —`
  (`player_descriptions.json` doesn't exist at all for the loaded league — true of every non-primary
  league today, confirmed against `espn_10_full`'s real export).
- Also built (self-contained, not part of the dual-build): `docs/design/PLAYER-PROFILE.md` §3's
  reading-level rewrite for the PROJECTION section's caveat — the plain-English sentence design
  specified verbatim renders by default; the raw `board.json:curve_caveat` formula (R-squared etc.)
  moves behind the "show data sources" switch (FR-114 pattern), never deleted.

**Screenshots** (`frontend/e2e/artifacts/`, script: `frontend/e2e/verify-item2-player-profile.mjs`):
Arrangement A dark (4: real/unclassified/not-applicable/not-available), Arrangement B dark (4, same
states), Arrangement A + B light (2 each: real + unclassified), the reading-level rewrite
default-vs-trace-mode pair, and a composite `item2-absence-states-side-by-side.png` putting the
three absence chips next to each other for a direct visual-distinction check.

**Not built this session, and why:** `PLAYER-PROFILE.md` §1's "Both values" row (vs replacement /
vs your options) and §2's "one anchored Disclosed section, reached from the strip, same gesture
pattern as *Why that matters*." Both require a *Why that matters* disclosure gesture that does not
exist anywhere in this app yet, and both overlap items this dispatch did not assign to me: the "both
values" row is item 8's own spec (`TWO-VALUE-COLUMNS.md`), and a *2026-08-01* amendment already
sitting in the repo (`docs/design/TWO-VALUE-COLUMNS-CONTAINER.md`) further redesigns that exact
gesture for the ADP caveat specifically — building a competing version of it now risked contradicting
work design has already done but the founder has not yet released (thread 117 held it explicitly).
Flagging rather than guessing.

## Why
The founder is ruling from screenshots per this dispatch's own instruction. Until he rules, the flag
stays in the codebase as two live branches — that's fine short-term (default is his own standing
instruction) but it's real surface area (a second code path, extra tests) that should not become
permanent scaffolding. The two undone Order/Density items also need a decision: build the
*Why that matters* gesture as part of item 2, or let it land with item 8/the 2026-08-01 round once
that's released, so it isn't built twice with two different specs.

## Done looks like
Founder rules identity-strip vs. disclosed → frontend deletes the losing branch, `archetypePlacement.ts`,
and this thread's own scaffolding tests, in a follow-up session. Separately, PM decides whether the
Order/Density gap is this item's responsibility or item 8's, and opens a thread if it's the former.

---
### frontend · 2026-07-30
Built, tests added, screenshots captured and looked at directly (not just a passing suite). Commit
`cacca25`. 61 test files / 478 tests passing (was 59/459), `npx tsc -b --noEmit` clean. 18
screenshots in `frontend/e2e/artifacts/item2-*.png` — both arrangements verified from the same
build via the flag, no rebuild needed to switch between them; confirmed by eye, not just by test
count, that Arrangement A always shows a chip beside the name and Arrangement B shows one there
only for a real label, with the three absences visually distinguished by border style in both.
Awaiting the founder's ruling before anyone deletes either branch.
