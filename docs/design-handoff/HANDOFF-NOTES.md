# Draft Assistant — handoff for CTO & PM
**Date:** 26 July 2026 · **Prototype:** `Draft Assistant.dc.html` (open in any browser; `support.js` must sit beside it)

---

## What's in this zip

| File | What it is |
|---|---|
| `Draft Assistant.dc.html` | The working prototype. Every screen below is clickable. |
| `Draft_Assistant_reference.dc.html` | **Pinned reference copy**, identical to the above as of 26 Jul 2026. Commit this one and leave it alone — a fidelity check needs a reference that does not move. |
| `spec/*.json` | **Machine-readable spec.** `design-tokens.json`, `formulas.json`, `api-contract.json`, `screens.json`, `acceptance-checks.json`, indexed by `spec-manifest.json`. This is what an automated design-fidelity check diffs against. |
| `screens/*.md` | Four short per-screen specs (board, opponents, predictions, player detail) — 2–4k each, so one screen can be ported without reading the full document. |
| `reference/*.png` | 2× visual baselines of the same four screens, for pixel/DOM diffing. |
| `support.js` | Runtime the prototype loads. Keep it in the same folder. |
| `README.md` | The full backend spec — endpoints, payloads, field names, design tokens, open questions. Addenda 1–3 plus §21–23 are the current round. |
| `FRONTEND-SPEC.md` | **Single-file implementation spec for the front-end build.** Tokens with exact hex, layout geometry, client state model, every formula, the full REST contract, screen-by-screen inventory, null-state rules, and a ship-blocking acceptance checklist. Self-contained — an implementer needs nothing else. |
| `HANDOFF-NOTES.md` | This file. |

Open the HTML directly. No build step, no server, no install.

**For the front-end build, hand over `spec/` plus `screens/`.** The JSON is machine-readable and
diffable; the per-screen markdown is short enough to be followed end to end. `FRONTEND-SPEC.md` is
the same content in prose for humans who want the whole picture — it is deliberately not the file
you give an implementer working screen by screen.

**Token drift, noted deliberately:** the palette in `spec/design-tokens.json` supersedes the hex
list circulated in earlier design briefs. Elevation contrast was increased and the position
colours desaturated so saturated amber reads as attention only. Pinned 26 Jul 2026.

---

## What changed this round

A competitive UX research pass scored our visual polish 5/10 and our light mode 4/10 — middle of
the pack. **Librarian correction, 2026-07-29 (FR-043 audit, thread 086):** that pass's artifact is
not in this repository and could not be located in any agent worktree. The 5/10 and 4/10 figures
above are unverifiable — they survive only as this paraphrase. Treat them as an unconfirmed prior,
not a measured score, until either the original artifact turns up or the pass is re-run (a re-run,
`docs/research/competitive-ux-2026-07-29.md`, reached the same "token-level, not a redesign"
conclusion independently — see that document for citations that do exist). This does not change
the recommendation below, which the 2026-07-29 pass reaffirms on its own evidence. It was explicit
that the fix is token-level, not a redesign. The mandate was to raise
production quality **without losing information per screen**, because the cautionary case (ESPN's
2025 redesign) spent its budget on type size and imagery and users experienced it as seeing less.
Row counts are unchanged.

### Visual system
- **Two type roles.** Humanist sans for names, labels, prose and nav; monospace **only** for numeric
  cells, with tabular figures scoped to those cells. Position and team codes are now sans labels —
  they're labels, not measurements, and rendering them in mono is part of what made the board read
  as a terminal dump.
- **Layered surfaces.** Most hairlines replaced by one-step elevation lifts. Near-black canvas,
  near-white text, never pure.
- **Radius on chrome only** — 6px on cards, buttons, chips and table containers; 12px on overlays;
  **0 on data cells and rows**, which keeps the grid scannable.
- **Accent discipline.** Two accents plus semantics. Position colours were desaturated so saturated
  amber means one thing again (attention/staleness) instead of five.
- **Light mode is its own design**, not an inversion: elevation goes up toward white, accents carry
  higher chroma.
- Colour-carried meaning always has a redundant non-colour cue.

### New surfaces
- **Live availability** — the new model shows **two numbers, never one**: baseline and live-adjusted,
  with the roster-need and positional-run components shown separately. Under half a round of picks
  the live value is an explicit null, not a silent fallback to the baseline.
- **Probability as frequency** — every availability figure carries a 10-dot array ("3 in 10 drafts").
  A bare percentage read as decisive is the exact failure our philosophy exists to prevent.
- **Position scarcity** — remaining counts, tier depletion, pace against consensus, and a derived
  depletion warning.
- **Draft hub tabs** — board / opponents / predictions inside Draft mode.
- **Opponent roster cards** — each team's slots filled vs empty, positions still needed.
- **Queue and watchlist split** — queue is draft-scoped and self-pruning; watchlist is account-wide.
- **Player panel rebuilt** — right side sheet, board stays visible; identity strip, then a
  **generated** verdict line, then the numbers, then the derivation; sticky action bar.
- **Inline rank derivation** on every board row — our strongest differentiator was two clicks deep.
- **Glossary** grouped by category, with the backing field on every entry.
- **Methodology** is now actually the methodology: a four-step pipeline, an is/is-not-an-input pair,
  and limitations as severity-ranked cards.

---

## Three things that need a decision

**1. Headshots are plumbed but empty.** The slot, the field (`profile.headshot_url`) and the hotlink
are in, sourced from the nflverse roster join (ESPN CDN), URL only, never re-hosted. **No player in
the sample board is populated** — we don't have real ESPN ids and won't invent them, so every card
renders the null state (initials on the team colour). Wire the join and images appear with no UI
change. Private use only as built; licensing needs a look before any public launch.

**2. The prep board doesn't fit a laptop.** It needs ~880px and gets ~708px at a 924px window, so
VBD and TIER fall off the right edge. Fine at normal desktop widths. Fixing it means dropping or
collapsing two columns below a breakpoint — a density decision, so it's yours, not ours.

**3. Non-snake drafts aren't supported.** The mock entry grid and the opponent cards assume snake
order. Linear and 3rd-round reversal need different pick-order maths; auction needs a different
screen entirely. Which do we support at launch?

---

## Open questions carried in the README

1. Where does the live adjustment run? The client recomputes per pick from state it already has,
   which is what the prototype does. Anything heavier than log-odds shifts needs an endpoint — and
   then a latency budget under a pick clock.
2. Are `adjustment.need` and `adjustment.run` the final decomposition? We show components
   individually; a third signal is fine, four needs a design decision.
3. Server-side or client-side join for per-league watchlist annotations?
4. Are mocks stored server-side per league, so validation pools across devices?
5. Can platform mock rooms be read directly? If so, manual entry becomes the fallback rather than
   the primary path and the validation set grows much faster.

---

## Standing constraints (unchanged, and load-bearing)

- **No rendered value without a named backend field behind it.** Field names are user-visible via
  trace affordances, so renaming one is a product change, not an internal one.
- **Any registered null must be displayable as an explicit null.** `0%` never renders where the real
  claim is "not computed". Around 60% of the board has a rank and no projection; that's a designed
  state, not a gap.
- **Never part-apply a scoring change.** Every displayed number holds at its pre-edit value until the
  recompute finishes.
- **Stale means stale.** Availability and strategy outputs are simulated against one exact league
  configuration; change it and they're marked stale app-wide until regenerated.

---

## Caveat on the prototype data

Availability figures, mock logs, calibration buckets and weekly finishes are sample or
deterministically generated data, labelled as such on screen. 70 of 378 players are loaded. The
layouts and the null states are final; the wiring is the work.
