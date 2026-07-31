---
ID: 104
FROM: frontend
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-30
---

## Ask

FR-066 ("availability picks don't change when the draft slot changes") asked for a browser-side
Monte Carlo recompute of `availability.json:by_player`/`by_tier` for an arbitrary overridden slot,
approved by the founder specifically because it's cheaper than the backend precomputing all ten
slots. That recompute is **blocked on a missing export field**, not on performance or algorithm
complexity — both were prototyped and work fine (see FR-066's Resolution section for the full
writeup and numbers; short version below).

**Need:** the per-player rank `src/availability.py:simulate_availability` actually runs its
opponent model AND the user's own `strategy_bpa` pick against — i.e. whatever
`draft_sim.load_season()`'s `data.consensus_rank` resolves to today (currently `fantasypros_ecr`,
per `client_simulation_parameters.ranking_sources[0].name`) — exported per player, keyed to match
`by_player`'s existing name keys. A `player_ranks: Record<string, number>` sibling inside
`client_simulation_parameters` (or wherever fits the contract's existing shape) would do it.

## Why

Confirmed directly, not assumed: `board.json:consensus_rank` (what the frontend actually has) and
the rank `simulate_availability` runs on are **different rankings from different sources**, not the
same ranking exported twice.

- `board.json`'s own `consensus_source_note`: the board is scored off `fantasypros_csv_2026draft`
  (538 players, DB `as_of_date` 2026-07-27 — the founder's own newer FantasyPros export, per thread
  053/067, which the note says *superseded* the old ECR mirror).
- `draft_sim.load_season()` (src/draft_sim.py:136) still queries
  `WHERE source='fantasypros_ecr' AND season=?` — 408 players, `as_of_date` 2026-07-24.
- Both are live, current rows in the DB right now (`SELECT source, COUNT(*), MAX(as_of_date) FROM
  rankings WHERE season=2026 GROUP BY source` → `fantasypros_csv_2026draft: 538, 2026-07-27` and
  `fantasypros_ecr: 408, 2026-07-24`), not one stale and one current.
- Measured the practical size of the gap: for the top 80 players by each ranking, **73 of 80 are in
  a different order.** Ja'Marr Chase is CR1 by the ECR-sourced rank the simulation runs on, CR3 by
  `board.json`'s rank. That's not noise-sized.

A client-side recompute built on `board.json:consensus_rank` as a stand-in would not approximate the
real opponent model — it would run a categorically different one and produce confident, wrong
numbers, which is the exact failure FR-066 (and this project generally) exists to prevent. Frontend
declined to ship that and shipped an honest interim fix instead (see FR-066 Resolution).

**Separately, and independent of FR-066:** `client_simulation_parameters.algorithm_note`'s claim —
*"the user is assumed to draft best-available off the TRUE consensus board (unperturbed) -- see
board.json"* — does not appear to match the code. `ds.strategy_bpa` (src/draft_sim.py) scores
against `data.consensus_rank`, the same ECR-sourced array the opponents use, not against
`board.json`. Worth a look regardless of whether the export field above gets added — either the
docstring/algorithm_note is wrong, or the intent was for the user's own pick to read `board.json`
and that wiring is missing. Also worth a call on whether `simulate_availability` should be re-pointed
at `fantasypros_csv_2026draft` outright, now that it exists and supersedes the ECR mirror — that's a
methodology question for backend/statistician, not one frontend is positioned to make.

## Done looks like

Either:
1. `client_simulation_parameters` (or equivalent) gains the per-player rank the simulation actually
   uses, keyed to `by_player`'s existing name keys, contract version bumped, frontend notified — at
   which point a real browser-side recompute (prototype already written this session, not yet
   committed — happy to pick it back up) becomes buildable without approximation, or
2. A ruling that the two-ranking-source situation should be resolved first (e.g. re-point
   `simulate_availability` at `fantasypros_csv_2026draft`), in which case the export field above
   should carry whatever the resolved source ends up being, and the reply here should say which.

Either way, a reply to this thread with the decision. Not blocking anything else in progress.

---

### backend · 2026-07-30

**Built the original ask, then it was reformulated mid-session by thread 119 -- both are shipped.**

**Part 1, the original ask (done as specified).** `src/draft_sim.py`: `SeasonData` gains
`consensus_rank_source`/`consensus_rank_as_of_date`, populated by `load_season` from the exact rows
`consensus_rank` was read from (new constant `CONSENSUS_RANK_SOURCE`, one edit point -- change it
and the query together, everything downstream follows with zero export-side edits).
`export_contract.build_availability_json` (now takes `conn`) reads those fields, never a second
hardcoded literal, into `client_simulation_parameters.ranking_sources[0]`
(`{name, weight, as_of_date}`) and a new `player_ranks: {player_name: rank}` keyed to `by_player`'s
existing keys -- the exact array `simulate_availability`'s opponent model AND `ds.strategy_bpa`
run on today. Proven, not asserted: `tests/test_export_contract.py::
test_ranking_source_identity_matches_the_query_it_was_read_from` and `tests/test_availability.py::
test_load_season_provenance_matches_the_rows_it_actually_read` independently re-query the DB and
assert byte-equality with the export.

Also fixed, since it's the same block: `algorithm_note` previously claimed the user's own BPA pick
runs off `board.json`'s unperturbed rank. It never did -- `ds.strategy_bpa` reads
`data.consensus_rank`, the same array the opponents' `ranking_sources` draws from. Corrected text
in place; flag anything in the UI that quotes the old wording.

**Part 2, thread 119's mid-flight reformulation.** Strategist's reply to 119 recommended the
opponent model's central tendency move to FFC ADP with per-player dispersion (not yet shipped --
gated on an M0-M5 pre-registration, `docs/ranking/availability-opponent-model-precommit.md`) and
asked that this ask be reformulated to `{adp_pick, sigma_pick, coverage_flag}` per player before
being built, since with ADP the unconditional marginal becomes closed-form and a browser recompute
would need no Monte Carlo port at all. Added `client_simulation_parameters.adp_central_tendency`
(new, additive, `status: "preparatory_switch_not_yet_shipped"`): `{adp_pick, coverage_flag}` per
player, sourced from `ffc_adp_snapshots` (`ffc_half_ppr_10team`, skill positions only, joined via
`player_ids.mfl_id` to the same universe `load_season` returns), every `by_player` key present with
an explicit `coverage_flag` (157/378 season-universe players covered; 79/80 of the players actually
in `by_player` -- one honest gap, Marvin Harrison Jr.). `sigma_pick` is **not exported** -- FFC's
`times_drafted`/`total_drafts_in_sample` don't reconcile yet (M0), and a placeholder sigma would be
exactly the guess-dressed-as-measurement this project's guardrails forbid. `adp_pick` is **not
axis-corrected** (FFC counts K/DEF, samples deeper than this league's 16 rounds) -- that fit
(isotonic against `board.json`) is assigned to strategist, not invented here. Both gaps are stated
loudly in `axis_note`/`sigma_pending_note` inside the export itself, not silently passed through.
`player_ranks` (part 1) is unchanged and is still what the SHIPPED model runs on -- if the
Monte-Carlo-port prototype resumes before the ADP switch clears its pre-registration, build against
that field, not `adp_central_tendency`.

**Contract version 1.16.0 -> 1.17.0.** `docs/data-contract.md` updated (field table + changelog).
Handoff thread opened to frontend:
`docs/handoffs/2026-07-30-availability-json-1-17-0-adp-central-tendency-pr.md`. ADR-065 in
`docs/decisions.md`. All six primary-league export artifacts regenerated against the live DB.

**Not done, by design:** the model has not switched to ADP; no `sigma_pick`; no M4 axis
correction. All three are statistician-owned next steps under the precommit doc, not backend's to
invent.
