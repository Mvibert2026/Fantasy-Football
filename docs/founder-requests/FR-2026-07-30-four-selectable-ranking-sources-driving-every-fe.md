---
ID: FR-2026-07-30-four-selectable-ranking-sources
STATUS: IN-PROGRESS
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — an architecture requirement, not a feature
NEEDS: backend (contract) DONE for the board layer; frontend (toggle) NEXT; librarian (assistant) after that
---

## Backend progress, 2026-07-30

**Board layer wired across all three built sources.** `make_board.build_board`/
`export_contract.build_board_json` take `ranking_source_selection` (`expert_adjusted` default,
`expert_raw`, `market_adp`, `proprietary`). Board order, VBD, tiers, projected_points all run off
the selection — never re-derived from our VBD under `expert_raw`/`market_adp` (never-blend, CLAUDE.md
§4). `proprietary` returns an explicit not-built shape, never a silent fallback. Contract
1.17.0 → 1.18.0: `board.expert_raw.json`, `board.market_adp.json`, `ranking_sources.json` (new).
Full detail: ADR-068 (`docs/decisions.md`), `docs/CURRENT-STATE.md`.

**Explicitly not done, and why:** `simulate_availability` (opponent model + the user's own BPA
pick) still runs off one hardcoded source, unaffected by the toggle — gated on an open, unresolved
`strategist`→`backend` thread already mid-flight on that exact code path
(`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`), which says explicitly not to
implement the change yet. Reported, not silently skipped.

**Handoff to frontend:**
`docs/handoffs/2026-07-30-four-selectable-ranking-sources-board-contract-s.md` — contract shape,
exact fields, exact files, what's wired and what isn't.

## Request

> "The draft board should be able to be fully functional off of consensus or my own rankings. All
> features. Toggle able.
>
> From me I'd like 3 rankings. Proprietary bottom up, consensus adjusted, consensus and ADP. App
> should run based on any at user toggle.
>
> And all of this information and inference you're doing needs to be available in chat bot."

## This resolves the §4 tension rather than violating it

**PM raised this exact conflict to him earlier today and it was the open escalation from PR-004 §11.3:**
`CLAUDE.md` §4 says ranking sources stay **separate, never blended**, so the model's independent view
is always visible against consensus — while his stated product shape, "consensus adjusted by
bottom-up", is a blend.

**His answer resolves it, and in §4's favour.** He is not asking for one merged number. He is asking
for **four separate, named, selectable sources, side by side**, with the user choosing which drives
the app. The independent view stays visible against consensus at all times — which is precisely what
§4 exists to protect. "Consensus adjusted" is a distinct artifact under its own name, not a
contamination of the proprietary one.

**The schema already anticipated this.** `ranking_source` is an enum with exactly four values —
`proprietary` / `expert` / `league_adp` / `market_adp`. His four map onto it directly. This was
designed for on day one and never wired.

## The four sources

| Founder's name | `ranking_source` | State today |
|---|---|---|
| Proprietary bottom-up | `proprietary` | **Does not exist.** Component models measured worse than the incumbent at all four positions (2026-07-30) |
| Consensus adjusted | `expert` (re-scored) | **This is what ships today** — consensus re-scored into league value structure. Within-position identical to consensus; deviation is cross-positional only |
| Consensus | `expert` (raw) | In the DB — `fantasypros_csv_2026draft`, 554 rows, `as_of` 2026-07-30 |
| ADP | `market_adp` | In the DB — FFC half-PPR 10-team plus MFL proxy, both current |

**Ambiguity flagged, not silently resolved:** he says "3 rankings" then names four things. Building
all four as separate selectable sources is the safe superset — if he meant three, one is simply never
selected. Worth confirming, not worth blocking on.

## "All features" is the hard part, and it is the point

Every consumer must run off the selected source, not just the board:

- The board's ordering, VBD and tiers
- **Availability** — `simulate_availability` currently hardcodes `fantasypros_ecr` for both the
  opponent model *and* the user's own BPA pick (thread 119). Two sources disagree on 73 of the top 80
  players, so this is not cosmetic
- **The recommender** — its `g` term is value over the realistic fallback, which is a ranking output
- Predictions, opponents, the grid, the assistant's answers

**Anything that silently keeps using a different source than the toggle says is the exact class of
defect the founder caught this morning** — a surface asserting something the code does not do.

## The chatbot half

Already underway: `docs/assistant-context.md` now carries 11 curated entries with number, interval,
effective n and scope inline, and a thread is open to `frontend` to confirm the retrieval layer
surfaces them. **This request extends it** — the assistant must also know *which source is selected*
and answer accordingly, or it will explain a board the user is not looking at.

## Backend follow-up, 2026-07-30 (second session, verification only)

**The three built boards genuinely differ**, verified by `player_id_gsis` join (the export's `id`
field is row position, not a stable key — do not join on it). `expert_adjusted` vs `expert_raw`:
within-position order is byte-identical for every position — VBD re-scoring reorders only across
positions, never within one, exactly as the "within-position identical to consensus" line above
predicted. `market_adp` (158/527 coverage) is the only one of the three that reorders *within*
position too, confirming it is the sole genuinely independent re-ranking among the three built
sources.

**Consumer audit widened past `simulate_availability` (thread 119, still the headline gap,
confirmed empirically: 158/158 players have byte-identical `availability` blocks whether the
board is `expert_adjusted` or `market_adp`).** Everything else that reads a ranking was checked:
board order/VBD/tiers/deltas switch correctly (already shipped); `live_availability.py` inherits
the same hardcode as `simulate_availability` (not an independent bug, same root cause,
`draft_sim.py:120`); `mock_lab_store.py`'s prediction replay is parameterized but has no live
caller anywhere yet, so it's not part of the toggle's surface today; `strategies.json`,
`candidate_rankings.py`, `backtest.py`, `run_pr007.py` are fixed to `fantasypros_ecr` **by
design** (historical-backtest/methodology validation, not live per-toggle features — correctly
hardcoded); the recommender fallback and predictions/opponents/grid views are frontend surfaces
with no separate backend export, so they inherit whichever board file is requested with no
backend change needed; the assistant has no backend pipeline reading a ranking source directly.

No code changed this pass. Full detail: `docs/CURRENT-STATE.md`'s FR-2026-07-30 entry,
`docs/handoffs/2026-07-30-four-selectable-ranking-sources-board-contract-s.md`.
