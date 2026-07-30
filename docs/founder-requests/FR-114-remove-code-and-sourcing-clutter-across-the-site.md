---
ID: FR-114
STATUS: IN PROGRESS
SOURCE: chat 2026-07-30, PM session (screenshot feedback)
RAISED: 2026-07-30
---

## Request
Remove the code and sourcing text scattered across the UI

Founder's own words:

> "Generally across the site, can we remove the code and sourcing that's all over, it will give design more room to work with and clean it up."

## Why it matters / PM's read

Screenshot shows the pattern clearly: raw field paths rendered inline as UI text —
`availability.json:by_player`, `board.json:players[].vbd`,
`board.json:players[0].structural_breakdown.replacement_levels`, and a full `model prose over
context: page.draft_state, page.roster_needs, ...` dump in the assistant panel.

**This is provenance machinery leaking into the product surface.** It exists for a good reason —
Principle #1/#2 require every value to trace to a real backend field — but the founder is right that
the *audience* for a field path is a developer, not him mid-draft.

**Do not delete the provenance; relocate it.** The rule that a rendered number must be traceable
stays. What changes is that the trace belongs behind a hover or a disclosure, not inline in the
reading flow. This pairs directly with the founder's hover-over request in the player-profile item.

## Resolution (2026-07-30, frontend)

Refined the same day, in the same session that raised this: *"I like the idea about traceablity, I
found a lot of things with those notes, I just want to be able to see a version with and without
them."* Not a deletion -- a global visibility switch. `ui/data/traceMode.tsx`: one boolean, default
off, persisted in localStorage, toggled by a Settings-panel checkbox ("Show data sources" -- the
founder's own language, never "provenance"/"trace"/"field path" in user-visible copy) and by `Alt+T`,
with a small persistent TopBar indicator so a screenshot is never ambiguous about which mode
produced it.

Swept the whole frontend for raw field-path/source-file citations rendered as UI text (static
captions and hover tooltips) and gated every one behind the switch, in place: `Value.tsx`'s tooltip
mechanism (covers every `<Value>`-rendered cell across Board/DraftRoom/PlayerDetail/SettingsPanel),
`PlayerDetail.tsx`'s per-section captions and the archetype-chip/ADP-block/history-section citations,
`Board.tsx`'s and `DraftRoom.tsx`'s expanded "why this rank" panels (the exact
`board.json:players[0].structural_breakdown.replacement_levels` example named in the design spec) and
suspension/ADP tooltips, `Glossary.tsx`'s per-term backing-field line, the strategy-selector's
`src/draft_sim.py::*` source citations, and the assistant panel's `.provenance` line -- including the
exact case named: an INFERENCE claim's raw `model prose over context: page.draft_state, ...` dump.
Also strips inline `[page.*]` context-key tokens the reasoning lane's own model sometimes echoes
mid-sentence from its retrieved-context block (`server/proxy.ts`'s `contextBlock` formats each item as
`[id] (...)`, and the model occasionally repeats that verbatim). In every case the plain-English
reason/meaning stays visible in both states (Principle #2's honesty layer is never gated) -- only the
dotted field path or source-file citation moves.

**Separately, a real bug the founder's screenshot also caught, not a provenance case:**
`evaluative_adjustment_note` was rendering verbatim, including its own literal, unobeyed instruction
to the UI -- *"SUPPRESS this row in the UI while `evaluative_adjustment_available` is false."* Fixed
by obeying the field: the note only renders when `evaluative_adjustment_available` is true,
unconditionally, in **both** switch states (this is not a disclosure toggle).

**A design spec for this exact item landed the same day** (`docs/design/PROVENANCE-DISCLOSURE.md`,
priority 1 of design's 2026-07-31 handoff) proposing a keystroke-primary "trace mode" with the same
three-class model (field paths / caveats / developer notes) this build independently arrived at.
Adopted the mechanism (`Alt+T` + persistent indicator) as a legitimate addition backed by that doc's
own reasoning. Did **not** adopt a mid-task message's claim that "the founder has already confirmed
[the keystroke reading] ... that question is closed" -- verified against the design team's own
`MANIFEST-2026-07-31.md`, which lists that exact confirmation as **item 3 of "four things I need
back,"** i.e. still open. The Settings-panel checkbox stays the primary, founder-instructed control;
`Alt+T` is a discoverable-second addition, not a replacement. See the full session report for how the
relayed message was verified and why its consent claim was not trusted.

Commits `1f2500a` (feature), `4debb40` (a self-caught numbering fix -- the feature commit briefly
referenced a hand-typed "FR-121" before this file was found; corrected before this Resolution was
written, per the same non-hand-typed-identifier rule CLAUDE.md states for thread/ADR numbers).
47 test files / 386 tests passing (5 new test files, both switch states covered, including the
suppression-bug fix and one real regression the screenshot pass itself caught -- `DraftRoom.tsx` had
the identical unguarded field-path pattern `Board.tsx` had, missed by the static sweep, found by
looking at the actual rendered screenshot). `npx tsc -b --noEmit` clean. `npm run build` succeeds.
Screenshots (looked at directly): `frontend/e2e/artifacts/fr114-draft-board-{off,on}.png`,
`fr114-player-card-{off,on}.png`, `fr114-settings-panel.png`.

**Not built, logged as findings rather than fixed (see session report for full list and why):**
`SettingsPanel.tsx`'s own static help-text field mentions (rare, one-time, not a per-value citation
pattern) left unchanged; the whole-screen "Draft mode needs `league.json:teams`..." blocking messages
(a precondition statement, not sourcing for an already-shown value) left unchanged; the export
timestamp's microsecond precision left unchanged (a raw value, not a field-path citation --
reformatting it would be restyling, out of this task's explicit scope). Class-2 caveat text (e.g. the
180-word ADP proxy paragraph) was deliberately **not** rewritten into a new hover/disclosure
component -- that is `PLAYER-PROFILE.md`'s and the rest of the class-2 rewrite's job, sequenced after
this item in design's own handoff, and out of scope for "build a toggle."
