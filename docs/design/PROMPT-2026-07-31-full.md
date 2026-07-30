# Design prompt — 2026-07-31

Send this whole file. It supersedes `BRIEF-2026-07-31.md`, which covered five items; this covers
those plus everything raised since.

Screenshots referenced by filename are in `frontend/e2e/artifacts/`. They are the current shipping
app, captured within the last day — not mock-ups.

---

## Context you need before item 1

**This is a personal fantasy-football draft assistant for one non-developer user**, used live during a
draft under a clock, on a laptop, with a real draft board open in another window. It is not a
consumer product and does not need to look like one.

**Its defining rule: the app never fabricates a value.** Where data is missing it says so, in place,
with a reason. Three design proposals have already been rejected for hiding an absence behind a
plausible default. Assume any design that makes the app look more confident than its data will be
rejected.

**The built app is the reference. Design catches up to code, not the reverse.** Where a spec and the
shipped app disagree, the app is right unless you explicitly override it and say why.

**Phone is priority 4 and currently paused.** Design desktop only this round.

Existing token and marker vocabulary is in `SUPPLIED-VALUES.md` — including the established "you put
this here" marker (dotted underline plus lowercase monospace label, never the accent colour). Reuse
it rather than inventing new markers.

---

## 1. Provenance text is leaking into the product surface — HIGHEST PRIORITY

Founder's words: *"Generally across the site, can we remove the code and sourcing that's all over, it
will give design more room to work with and clean it up."*

The app currently renders raw field paths as visible UI text:
`availability.json:by_player` · `board.json:players[].vbd` ·
`board.json:players[0].structural_breakdown.replacement_levels` · and in the assistant panel, a full
`model prose over context: page.draft_state, page.roster_needs, page.recommendation, …` dump.

**Do not propose deleting the provenance.** It exists because every rendered number must trace to a
real backend field, and that rule is not negotiable. What is wrong is the *audience*: a field path is
for a developer, not for the founder mid-draft.

**Design the disclosure pattern.** Where does a trace live so it is one gesture away and zero
gestures present? This is the single highest-leverage item in the round — it recovers space on every
screen and unblocks several items below.

Related and to be solved with the same pattern: *"we should use hover over more for explanations and
sources."*

Screenshots: the assistant panel and player card in `fr083-player-card-westwood-adp-block.png`.

---

## 2. Player profile — order, density, and reading level

Founder's words:

> *"We need to think critically about the order of the information presented in player profiles"*
>
> *"Player Profile feels crowded and potentilally with low value information - justifications with
> statistcal explanations etc should be written for slightly lower sophistication and maybe in a
> hover over"*

Three separable asks; please answer them separately:

**Order.** The card has accreted rather than been designed. What leads, what is secondary, what is
disclosed.

**Density.** It carries rows of no value. The screenshot shows a breakdown where *both* components
read `±0`, followed by a long internal note beginning "Zero by construction, not by omission" and
ending with a literal instruction to the UI: *"SUPPRESS this row in the UI while
evaluative_adjustment_available is false."* **That suppression instruction is being rendered instead
of obeyed.** Treat it as representative rather than as one bug.

**Reading level.** Statistical justification should be written for slightly lower sophistication,
with the detail behind a hover.

**New input:** an archetype chip now sits in the identity strip. It has four states — a real label, an
honest `UNCLASSIFIED`, `ARCHETYPE N/A`, and `ARCHETYPE —`. Design around a label that is frequently
weak or absent, not one that is always confident.

---

## 3. The periodic-table draft board — reinstated by the founder

Founder's words: *"we do want to have the periodic table, thought we'd been ok with some set of
colors, just get it decided, maybe it needs to pop out because of spacing requirements, don't remove
stuff from the middle panel to put it in there, you can add it there, but don't remove the other
things."*

This overrides `DRAFT-MIDDLE-PANE.md`'s earlier rejection. Two objections were raised then:

- **Colour collision — already resolved, no action needed.** `POSITION-COLOUR-RESOLUTION.md` is
  `STATUS: RESOLVED — grid is unblocked`: no position hue changes, families separated by role and
  shape, **semantic accents banned from the grid outright.** Build against that.
- **Space — stands, and the founder has answered it.** The middle pane is ~640px at 1600; six cells
  across was called "a list with extra steps." **Pop-out is the expected shape.**

**Binding constraint, stated by the founder unprompted: additive only.** The four existing tabs
(Recommend · Scarcity · Queue · Insights) all stay. Nothing may be removed to make room — he had just
praised the pane.

Yours to decide: the pop-out mechanism, the grid's density, what a cell carries beyond identity, and
its behaviour at the widths a popped-out view actually gets.

---

## 4. The assistant window

Founder's words: *"Chat behavior is improving, but the window is crap - needs to have a constant
window to be able to continue the conversation, it also doesn't allow for scrolling."*

The behaviour improved (page context, standing input, conversation history, three suggestions).
The container did not: the dock is fixed at 430px × 72vh, the shipping screenshots already show text
overflow at that size, and the content does not scroll.

Needed: a persistent surface for a continuing conversation, that scrolls, at a size that fits an
answer. Screenshots: `fr077-followup-conversation.png`, `fr077-dock-open-3-suggestions.png`.

---

## 5. Light theme is too bright

Founder's words: *"Light fiew maybe needs a touch up, it's very bright, it could use some shading."*

The only unprompted visual-comfort complaint, and it touches every screen. Currently flat white with
hairline borders. Needed: a shading strategy — surface elevation, panel separation, where grey sits
against white.

**Constraint:** dark mode is what he mostly uses and it is not broken. Do not restyle dark to match a
new light system; the two stay independently coherent.

---

## 6. The draft rankings pane reads dated, and may be too narrow

Founder's words: *"there are parts that feel old… the rankings in the left on draft may need to be a
wider pane."*

Two things — please separate them. **Look and feel:** what specifically reads as dated, and what
replaces it. This is the screen he stares at for the entire draft. **Width:** he suspects the left
pane is too narrow.

Screenshots: `fr067-fr087-draft-board-1180w.png` and `fr067-fr087-draft-board-1500w.png` — the same
screen at two widths.

Note: column alignment on that board has been fixed once and **regressed** — he reports the headers
still do not line up. Do not propose a layout requiring header and rows to be defined separately.

---

## 7. Resizable / pop-out panes

Founder's words: *"it would be interesting to allow me to drag to change the pane size as needed…
These are ideas, not suggestions, design should weigh in based on best practices."*

**He has explicitly invited you to push back if dragging is wrong.** Options: drag handles, preset
layout modes, pop-out windows, or simply better defaults that make resizing unnecessary.

Remember the use context: under a clock, mid-draft. Anything needing fine mouse precision at that
moment is a bad answer. This interacts with item 3 — if a pop-out mechanism is being designed for the
grid, one mechanism may serve both.

---

## 8. Two numbers where there is currently one

Founder's words: *"VBD probably should show me both numbers value of that position, and based on flex
and other options."*

A drafter asks two questions, and the app answers one: *how good is this player at his position*, and
*how good is he against what else I could do with this roster spot.*

Both will be shown, labelled, **not blended** — this project keeps value definitions separate rather
than converging them. Design how two numbers coexist on a row and on a card without doubling the
visual weight or implying one is the "real" one.

---

## What NOT to spend this round on

- **Mobile.** Paused.
- **Anything implying our rankings beat consensus.** They do not. The app deliberately does not show
  proprietary rankings yet, and no design should presuppose them.
- **Anything implying a draft strategy carries a measured edge.** Zero RB tested null; the strategy
  selector states that on screen every time it fires. Design must not undercut that.

## Optional background

- `docs/design/BUILD-STATE-AUDIT-2026-07-30.md` — which prior specs were built, which were not
- `docs/design/POSITION-COLOUR-RESOLUTION.md` — the colour decision the grid builds on
- `docs/strategic-insights.md` — what the research has actually established, and why the app is
  cautious about claims
