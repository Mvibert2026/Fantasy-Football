# PREP front end — status

**Branch:** `frontend-prep` (git worktree at `../fantasy-football-prep`)
**Built against:** export contract **1.7.0**
**Last updated:** 2026-07-26

Run it with one command. Nothing else is needed:

```bash
npm install && npm run dev
```

`predev` copies `data/export/*.json` (and any `data/export/<league_id>/` subdirectory) into
`public/`, so the app always starts against whatever the backend last generated.

---

## Done

**Shell** — top bar, left sidebar, floating assistant dock, dark/light theme toggle. Ported
from the design handoff prototype (`Draft Assistant.dc.html`) with its DOM structure and
inline styles kept literal, per explicit fidelity instruction. Design tokens live in
`ui/styles/tokens.css` — one file, both the prototype's own var names (used verbatim by new
components) and the app's older var names (aliased onto the same palette).

**Board** — 378 players, table plus snake round grid. Built sparse-first: 233 of 378 rows
carry no displayable projection and no interval, and that is the designed default, not a
degraded state. Sortable, sticky-header columns; clicking a row opens a detail panel with
the structural-attribution breakdown and anchors the assistant to that player. Tier-band
dividers render in single-position views (`tier_label` is per-position, not global — see the
extensive comment on `Board.tsx`'s `bandsEnabled`). Filters by position; delta view sorts by
size of disagreement with consensus; empty results read as a state, not an error.

**Availability Explorer** — reads `availability.json` directly (`ui/data/availability.ts`,
`ui/views/Availability.tsx`): pick + sigma (5/10/20) selectors, per-position player lists
with real survival probabilities, a tier-availability spotlight. No fabricated single
`noise_band` figure — that field has never existed in this backend, confirmed directly with
the backend session; the real shape is the three-sigma sweep, shown as such.
`metadata.marginals_note` (unconditional marginals, not conditioned on live picks) is a
standing banner, not a tooltip.

**Multi-league support** — the top bar's league pill is a real switcher
(`ui/data/league-registry.ts`), backed by `public/data/_leagues.json`
(`sync-exports.mjs` writes it from whatever `data/export/<league_id>/` directories it
actually finds). `loadDataset()` refuses to render a non-default league if any of its
artifacts is missing or disagrees on `league_id` — wrong-league data that looks
authoritative is worse than an error. Verified against the real second league the backend
shipped (`yahoo_standard_mock`, contract 1.7.0/ADR-041), both directions of the switch,
including two real bugs the synthetic fixtures hadn't caught (see `docs/decisions.md`-style
detail in the commit history: `strategies.json` isn't part of a per-league export set, and
Vite's dev-server SPA fallback answers a missing file with 200+HTML, not a 404).

**Draft mode** — `ui/views/DraftRoom.tsx`, `ui/data/draft.ts`, `ui/data/recommendation.ts`.
Three-column layout ported from the prototype's Draft Room screen: command bar (mark-pick
search with autocomplete, undo, on-clock/picks-until-you/your-next stats), available
players, recommendation (on the clock) or watchlist (off the clock), roster + picks + draft
log. All six requested items landed:

1. Layout ported, not redesigned.
2. Manual pick entry for **all** teams, not just the user's — team-at-pick is derived
   (`teamSlotAtPick`, the inverse of `RoundGrid.tsx`'s own forward snake formula), never
   stored. Off-board names (a kicker, a rookie not on this board) are logged as raw text
   rather than refused.
3. Board removes drafted players as picks land; state is `picks[]` + `watchlist[]`,
   persisted to `localStorage` per league, no backend call per pick.
4. Availability during a live draft is explicitly labelled approximate: this app's real
   Prep-mode marginal probabilities (`ui/data/availability.ts`), filtered to who's still on
   the board, never re-simulated against picks made. The honest client-side conditional
   simulator (`availability.json:client_simulation_parameters` exists for it) is unbuilt,
   separate, larger work.
5. **Export draft log** button downloads the completed/in-progress draft as JSON matching
   the backend's mock-logging schema field-for-field: `mock_id, overall_pick, round,
   team_slot, player_name_raw, timestamp`. No `mfl_id` — `board.json` carries
   `player_id_gsis`, never an `mfl_id`, so the honest field is the name as entered.
6. Recommendation score (`ui/data/recommendation.ts`): `vbd + 8 (unfilled need) + 18
   (tier-1 TE) − 25 (QB, round<6)`. No DEF term — board.json carries no DEF players at all
   (ADR-039), so that branch of the spec formula is structurally unreachable, not omitted
   by oversight.

Deliberately not built this session, and why: **"Auto-fill to my pick"** (the prototype's
`simToMe`) would inject randomly-generated opponent picks into exactly the log the export
feature exists to keep real — fabricating picks conflicts with the stated purpose of manual
entry. **Position-scarcity bars and the decision-rules-with-evidence list** (prototype lines
316–386) are polish beyond the six requested items. **Mock lab UI, column customization,
glossary rework** — explicitly out of scope for this session per instruction.

**Reasoning lane refusal loosened** — previously any question matching no player name, no
glossary term and no `nulls.json` keyword returned zero context and refused outright, even
when the export held a real answer. `ui/assistant/reasoning.ts` now falls back to
`strategies.json`'s full comparison set plus every `nulls.json` finding when narrow
retrieval finds nothing — verified end-to-end with real `claude-opus-5` calls producing
caveated, sourced answers instead of refusals. The lane's earlier "no credit" blocker is
resolved; live calls succeed.

**Attribution panel** — structural only, one honest claim. No evaluative row, suppressed
or otherwise: the board assigns every player at the same positional consensus rank an
identical projection, so it holds no player-level opinion and there is nothing to
attribute. A zeroed-out row would imply a measurement that was never taken.

**Strategy guide** — `sign_test_p` is never rendered against a 0.05 threshold (the floor is
0.125 at n=4, so nothing can clear it), and `power_floor.plain_english` sits beside every
significance number. Renders an honest "not available for this league" state when
`strategies.json` isn't part of a league's export set (every league but the default,
today).

**Glossary, Methodology** — straight from the exports, including the registered nulls as a
first-class section. `nulls.json`'s per-league `NOT_YET_RUN_FOR_THIS_LEAGUE` result
sentinel (contract 1.7.0) renders as plain English, not the raw enum string.

**Assistant** — one entry point, three lanes, every claim tagged:
- `MODEL` — deterministic templates over the exports, citing a field path and run id.
- `SOURCE` — news feed items with publisher, URL, timestamp, and age past ~48h. No body
  text is stored or re-rendered; the prose is licensed.
- `INFERENCE` — model prose over retrieved context (narrow match, or the fallback above),
  via a local proxy.

**Provenance** — every rendered value goes through a `Cell`, so it carries the field path
it came from. Absence is a variant of the same type with a reason attached.

**Trace-field registry** (`ui/data/trace-fields.ts`) — field paths are user-visible text
(tooltips, provenance lines), so renaming one is a product change. The registry pins them
to a contract version with a changelog, and a test fails if the export adds, drops or
renames a displayed field.

**Refresh data control** — visible in the top bar. Re-reads `data/export/`, reports a
before/after table, and says "no update available" explicitly rather than doing nothing
visible.

**Reasoning proxy** — Vite dev-server middleware, so `npm run dev` stays the only command.
Key read from a gitignored `.env` in Node; never enters the client bundle. No-key,
proxy-down, offline, no-credit, bad-key and rate-limited are all permanent first-class
states with plain-language remedies.

**Tests** — 90 across 11 files, each with a positive control so a broken assertion cannot
pass silently. Includes synthetic-fixture coverage for multi-league loading and the
wrong-league guard (no second real league existed when that mechanism was first built) and
for the snake-order draft math (checked against `RoundGrid.tsx`'s own forward formula, not
just against itself).

---

## Left

**Blocked on you**

- **The design reference never reached the earliest sessions.** Some visual values in
  `ui/styles/tokens.css` may still be a reading of described language rather than the
  literal reference for screens built before the handoff arrived. Board/shell/Availability/
  Draft Room are now ported directly from `Draft Assistant.dc.html`; older screens
  (Strategy Guide, Methodology, Glossary) have not been re-verified against it.
- Any API key rotation flagged in earlier sessions — check before assuming a stale key is
  still in use.

**Deliberately not built**

- Season mode, Opponents, mock lab UI (mocks list, per-pick review, pooled model
  validation), column customization, inline glossary popovers + categorized Glossary view.
  Glossary is a complete view but unreachable from navigation. None of these are stubbed
  as "coming soon" fabrication — each renders an explicit not-built pane.
- Live client-side conditional availability (recomputing survival probabilities against
  actual picks made, using `availability.json:client_simulation_parameters`). Draft mode
  uses the honest filtered-marginals approximation instead; the real simulator is separate,
  larger work.
- "Auto-fill to my pick" in Draft mode — see the Draft mode section above for why this was
  a deliberate cut, not an oversight.
- News ranking, relevance scoring, recency weighting, dedup, retrieval tuning. There is no
  corpus, so anything built now would be guesswork.
- Non-snake draft geometry (linear, 3rd-round-reversal, auction) — Draft mode assumes snake
  only, matching this league's actual format.

**Known rough edges**

- The reasoning lane's narrow retrieval is plain substring matching on player names and
  glossary terms. Adequate for a board this size, deliberately untuned for the same reason
  the news lane is.
- `best available at pick N` (assistant template) assumes the preceding picks took the top
  N−1 board players. Stated in the answer itself, not hidden.
- Draft mode's roster-slot assignment (`buildRosterSlots` in `DraftRoom.tsx`) is a simple
  greedy fill (position match → FLEX if eligible → bench), not a claim about how any real
  platform assigns slots — good enough for a dry run.
- Draft mode's recommendation score is an unvalidated stopgap, not backtested the way the
  rankings themselves are. Said so on screen, not just here.
