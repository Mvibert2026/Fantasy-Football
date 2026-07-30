# Contract answer: `vs your options` (design's second value column)

**One sentence:** `vs your options` is a pure client computation — every input it needs
(candidate and alternative players' `projected_points`/`vbd`/`position` from `board.json`, and
`starters`/`flex_slots`/`flex_eligible` from `league.json`) already exists in the export today,
live roster state is browser-only by design and always will be, so no export field, no contract
bump, and no backend build is needed — frontend can ship it against `contract_version` `1.16.0`
as-is.

Author: backend session, 2026-07-30. Answers the open question in
`docs/design/TWO-VALUE-COLUMNS.md` (`main`, `f47b863`).

---

## 1. Export field or client computation

**Client computation.** Walked through what the computation needs, checked each input against
the current contract:

| Input | Needed for | Exists today? | Where |
|---|---|---|---|
| Candidate player's position | which slot type this pick would fill | Yes | `board.json:players[].position` (`src/export_contract.py:412`) |
| Candidate + every alternative's value (points or VBD) | the comparison itself | Yes | `board.json:players[].projected_points` (`:424`), `.vbd` (`:443`) — 510 players across QB/RB/WR/TE in the current export, not a top-N slice |
| Roster shape: starters per position, flex slot count, flex-eligible positions | to know when a position's own starters are full vs. still open, and which positions compete for the shared flex slot | Yes | `league.json:roster.starters` (includes a synthetic `FLEX` key), `roster.flex_eligible` (`src/export_contract.py:848–849`) |
| **Live roster state** — which slots are already filled, by whom | the entire reason this number is roster-dependent (design's own framing) | **No, and it is not supposed to.** Grepped `src/export_contract.py` and `src/make_board.py`: no export claims to carry a live, mid-draft roster. `board.json` and `availability.json` are static, pre-computed snapshots generated before a draft starts — they cannot know what the user has picked in a draft that hasn't happened yet. Live roster state exists only in the browser's draft session (per design's own correct structural argument, and consistent with `docs/handoffs/002-per-pick-draft-state.md`'s scope: draft-time state is a frontend concern) |
| Which players are still on the board (not yet drafted by anyone) | the alternative pool must exclude gone players | Live draft state, browser-only, same as above | — |

Every input that is *not* live draft state already ships in the contract. The one input that
does need live state is, by construction, never going to be an export field — a static file
generated before the draft cannot carry it, and it would be wrong to try (a `board.json` that
claimed to know the user's roster would be stale the instant the next pick landed). This
confirms design's own structural argument rather than complicating it.

**No export change. No contract version bump. No new backend code to ship this.**

The shape of the computation, for whoever implements it (not pinning frontend to my exact
arithmetic, since the roster-slot-assignment logic is a display/UX call, not a backend one):
for candidate player P at position `pos`, if `pos`'s mandatory starters are already filled on
the live roster, the alternative pool is every other flex-eligible position's best
still-available player (competing for the shared `FLEX` slot(s)); if `pos` still has an open
starter slot, the comparison is against the board more broadly. All of that is arithmetic over
data already in hand — `board.json` + `league.json` + the browser's own roster state.

## 2. Prep-board empty-roster behavior (design's constraint 3)

**Achievable, trivially, client-side.** The client already has to distinguish "Prep mode, no
picks made" from "live draft, N picks made" for other reasons (recommendation panels, on-deck
logic). Rendering `—` for `vs your options` whenever roster state is empty is a one-line
condition on the same signal — no export field required to make this distinction either;
"has any pick been made in this session" is client session state, not something `board.json`
needs to say.

## 3. Reconciliation with #35/#36 — is this the same quantity that came back NULL?

**Different quantity.** Read `docs/preregistration/PR-006-*`,
`docs/ranking/valuation-tests-35-36-precommit.md`, and `docs/CURRENT-STATE.md`'s recorded
results before answering this.

| | #35 (global flex baseline) | #36 (VONA, pick-gap aware) | `vs your options` (design) |
|---|---|---|---|
| What it changes | The replacement-level constant feeding **every player's VBD number**, structurally, for the whole board | Which player a **selection rule** recommends this turn, reasoning about a **future** turn (`gap_length` picks ahead) | A **second number shown next to** the unchanged VBD ranking, for the **current** roster state only |
| Roster-dependent? | No — applies uniformly regardless of what anyone has drafted | No — reasons about the generic snake gap for the user's slot, not the actual roster built so far | **Yes** — this is the entire point (Gibbs example: same player, same board position, different number once RB is already rostered) |
| Time horizon | N/A (static constant) | Forward-looking: expected best-available at the user's *next* turn | Immediate: best alternative *right now*, given roster filled so far |
| What was measured | Whether swapping the constant produces better realised rosters (win condition: season-paired margin over the current per-position scheme clears zero, corrected p<0.05) | Whether gap-aware urgency produces better realised rosters than a gap-blind constant | **Nothing yet** — this specific roster-state-conditioned quantity has never been run through `draft_sim.py` as a strategy and graded against a win condition |
| Result | **NULL** — CIs include zero at both sigmas, sign flips | **NULL** on the margin (decision divergence was a clean YES — the two arms pick differently 100% of paired drafts — but that divergence did not reliably produce better rosters) | Not applicable — not the same test |

So: **no, this is not the quantity #35 or #36 measured.** #35 changed the ranking's own
denominator globally; #36 changed a forward-looking selection policy. `vs your options` is a
third thing — a live, roster-conditioned *display* number that never touches the ranking or the
`vbd` field at all. It is in the same conceptual family as #36 (both are "value over some
notion of the next-best alternative"), which is exactly why the reconciliation has to be
explicit rather than assumed away.

**But the family relationship is precisely why the honest-framing rule still applies.** This
quantity has not been tested for the thing #35/#36 tested — whether reasoning about
flex/alternative value produces better draft outcomes than plain VBD. Two independent
pre-registered attempts at *that general idea*, at two different formulations, both came back
NULL at this project's current sample size (n=4 seasons, sign-test power ceiling p=0.125,
CLAUDE.md §6.3/§6.5). A founder looking at a second, larger-looking-than-VBD-alone number is
liable to read "the app is telling me this is the better pick" — and this project has twice
measured that exact style of reasoning and found no demonstrated edge.

**Does CLAUDE.md §6.5 (baseline rule) technically apply?** No — §6.5 governs *ranking versions*
(does a candidate config beat consensus ADP on holdout). `vs your options` per design's own
spec never reorders the board or the Recommend pane; it is informational only, sitting beside
an unchanged VBD-ranked list. It is not a ranking version and does not need a baseline
comparison to ship. But the *spirit* of the rule — never let a number imply an edge that was
not measured, and report NULLs plainly rather than let them be forgotten once something ships
next to them — does apply, because this is the same underlying hypothesis (flex-aware
valuation beats plain VBD) restated as a display feature instead of a ranking change.

### The literal words that should appear on screen

Design's mockup shows two columns with no accompanying copy. Add a caption/tooltip on the
`vs your options` header (or its column footnote), literal text:

> **vs your options** — this player's value against the best other player available right now
> for the same roster spot, given your picks so far. It does not change the ranking above.
> This project tested whether reasoning about flex/alternative value produces better draft
> outcomes than plain positional value (test-registry #35, #36) and found no measurable edge at
> the current sample size (n=4 seasons) — treat this number as a way to see where the two
> questions disagree, not as a stronger recommendation.

This satisfies "report NULL plainly" (§6.5's spirit) without refusing the founder's own
explicit ask to see the disagreement (FR-118) — the number ships, honestly labelled.

## 4. FR-115 / FR-118 — does this recommendation satisfy them?

Read both in full (`docs/founder-requests/FR-115-*.md`, `FR-118-*.md`) before answering.

- **FR-118** ("VBD probably should show me both numbers"): **fully satisfied** by design's spec
  plus this answer. Two labelled, equal-weight, non-blended numbers, exactly as FR-118 and
  `docs/design/TWO-VALUE-COLUMNS.md` describe. No export change needed to ship it.
- **FR-115** ("Value of next Flex... TE over-suggestions from pure VBD"): **only partially
  satisfied, and the gap should be stated to the founder plainly.** FR-115's underlying
  complaint is that the **Recommend pane's ranking itself** over-suggests TEs because it is
  driven by pure per-position VBD (TE10 replacement, almost never the real flex alternative).
  Showing `vs your options` as a *second, informational* column lets the founder **see** that a
  given TE is a weak use of the roster spot — but it does **not** change which player the
  Recommend pane surfaces first, because design's spec is explicit that rankings never move.
  The only tested attempt to fix the ranking itself (#35, replacing TE10-style per-position
  replacement with a shared flex-eligible baseline) came back NULL — no validated fix for the
  ranking exists yet. **Left undone:** the recommendation ordering still needs a validated
  flex-aware ranking change (or a re-scoped, better-powered re-test of #35/#36's hypothesis) to
  fully close FR-115; that is a `strategist`/`ranker` methodology question, not something this
  display feature resolves.

## Bottom line for the implementer (frontend)

1. Build `vs your options` as a client-side computation off existing `board.json` +
   `league.json` fields plus live draft-session roster state. No backend work, no contract
   bump.
2. Empty roster (Prep board) renders `—`, driven by the client's own "any picks made yet"
   session flag — not an export concern.
3. Ship the caption text in §3 above verbatim (or materially equivalent) so the column does not
   imply a validated edge that two pre-registered tests did not find.
4. This closes FR-118. FR-115 remains open on the ranking side; flagged to `strategist`/`ranker`
   separately (see handoff thread).
