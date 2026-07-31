# 2026-07-30 — backend — four selectable ranking sources: board comparison + full consumer audit

Continuation of a prior run that died on a session limit partway through
(FR-2026-07-30-four-selectable-ranking-sources-driving-every-fe.md, ADR-068). The board-layer
work (`RANKING_SOURCE_SELECTIONS`, `RankingSourceNotBuilt`, contract 1.18.0, the three built board
files + `ranking_sources.json`) was already landed and committed before this session started. This
session did **verification only — no code changed.**

## Task 1 — do the three built boards actually differ?

Yes, confirmed by direct comparison (`data/export/board.json`, `board.expert_raw.json`,
`board.market_adp.json`), joined on `player_id_gsis` — **the exported `id` field is row position
(equal to `overall_rank`), not a stable player key; joining on it silently produces nonsense (I
did this first and got a false "not identical within position" result before catching it).**

| Pair | n common | Spearman ρ | Top-25 overlap | Within-position order identical? |
|---|---|---|---|---|
| expert_adjusted vs expert_raw | 527 | 0.944 | 22/25 | **Yes, all 4 positions** |
| expert_adjusted vs market_adp | 158 | 0.945 | 21/25 | No — 55/66 WR pairs swapped, similar for RB/QB/TE |
| expert_raw vs market_adp | 158 | 0.960 | 23/25 | No |

**Finding, stated as the dispatch asked:** `expert_adjusted` and `expert_raw` are NOT identical
overall (Spearman 0.944, not 1.0) — the FR's prediction that re-scoring through our VBD curve
"deviates only cross-positionally" holds exactly: within-position order (which RB is RB1 vs RB2)
never changes between the two, but a player's *overall* rank still moves because our VBD curve
values positions differently than raw consensus ordering does (e.g. a top RB and a top WR at the
same positional rank get different overall placement depending on the curve). `market_adp` is the
only one of the three that reorders players *within* a position too — it's the sole genuinely
independent re-ranking among the three built sources, not just a re-scored copy of consensus.

## Task 2 — consumer audit for silent fallbacks

Full sweep of every `src/*.py` module that reads `consensus_rank`, a `ranking_source`, or
`fantasypros_ecr`/`SOURCE`/`TRAINING_SOURCE` directly.

| Consumer | Verdict |
|---|---|
| `export_contract.build_board_json` (board order, VBD, tiers, ranks, deltas) | **Switches correctly** — already wired, all 3 built sources |
| `export_contract.build_availability_json` + every `board*.json`'s per-player `availability` block | **Hardcoded, confirmed** — 158/158 players byte-identical between `board.json` and `board.market_adp.json`. Root: `draft_sim.py:120` `CONSENSUS_RANK_SOURCE = "fantasypros_ecr"`, a module constant, not a `load_season` parameter |
| `availability.simulate_availability` | **Hardcoded** — via the `data` it's handed from `load_season`; its `sources`/`source_weights` params are the ADR-034 opponent-noise mixture, not a consensus-source selector |
| `live_availability.py` | **Hardcoded, same root cause** — re-weights a marginal computed elsewhere; not an independent bug |
| `mock_lab_store.predict_next_pick`/`replay_predictions` | Parameterized (caller supplies `available_ranks`/`board_ranks`), **but no live caller exists anywhere in `src/` or `frontend/`** — not wired to anything yet, out of scope |
| `export_strategies.py` (`strategies.json`), `candidate_rankings.py`, `backtest.py`, `run_pr007.py` | **Hardcoded by design** — historical-backtest/methodology validation over pre-2026 `DEV_SEASONS`/`TRAINING_SOURCE`, not live per-toggle app features. Correct as-is |
| Recommender fallback, predictions/opponents/grid views | Frontend surfaces, no separate backend export — inherit correctness from whichever board file is requested, no backend change needed |
| Assistant | No backend pipeline reads a ranking source for it directly; reads `docs/assistant-context.md` via frontend/librarian's retrieval layer (threads 032/033/088, out of this scope) |

**Not fixed on purpose, per explicit instruction:** `simulate_availability`'s source stays gated on
`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md` (strategist thread, mid-flight,
M0 already found FFC's `times_drafted` doesn't reconcile). Fixing it now would change availability
numbers before that pre-registration clears.

## Write-back

- `docs/CURRENT-STATE.md` — FR-2026-07-30 entry extended in place with the measured comparison and
  full audit table.
- `docs/founder-requests/FR-2026-07-30-four-selectable-ranking-sources-driving-every-fe.md` —
  "Backend follow-up" section appended.
- `docs/handoffs/2026-07-30-four-selectable-ranking-sources-board-contract-s.md` — reply appended
  (thread stays `OPEN`, still frontend's to close with the toggle UI + screenshot).
- No test suite changes — no code touched. Prior session's counts stand:
  `tests/test_make_board.py` 32/32, `tests/test_export_contract.py` 62/62.

## Nothing here requires a decision from anyone else beyond what's already gated (thread
2026-07-30-availability-adp-measurements-m0-m5). No new contract change, so no new frontend thread
opened per the dispatch's own instruction (reply on the existing one instead).
