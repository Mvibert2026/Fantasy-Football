# Code map

**For giving accurate instructions about this code without reading all of it.**

Read-only survey, 2026-07-29. Every claim carries a `file:line`. Nothing was refactored to
write this, and nothing here is a recommendation — where something looks wrong, it is reported
as it is, with a pointer to the doc that already tracks it.

**Partially stale, corrected in place 2026-07-31 (librarian pass).** `CONTRACT_VERSION` below was
last measured at 1.13.0; it is now `1.18.0` (§4 updated). §1's "two ranking sources" is now four —
see the note added to §1. Several modules that landed since 2026-07-29 are not yet described
anywhere in this file: `src/ingest_pbp.py` (play-by-play ingestion), the batch factor-testing
modules under `experiments/bottomup/factors/` (`factor_features2.py`...`factor_features7.py`,
`run_factors2.py`...`run_factors7.py`, `coord_preseason.py`, `coord_join_diagnostic.py`), and
`frontend/ui/components/TraditionalDraftBoard.tsx` — each is named where it fits below, but this
file has not been given a full re-survey pass and should not be trusted as exhaustive for anything
that landed after 2026-07-29 beyond what is noted here.

Five questions, one section each.

---

## 1. How does a board get built, and what feeds it?

**Entry point:** `src/make_board.py:452` (`main`) → `build_board` at `src/make_board.py:342`.
The JSON the app actually consumes is built separately by
`export_contract.build_board_json` (`src/export_contract.py:135`).

**Two ranking sources, deliberately not interchangeable** (`src/make_board.py:106-107`):

| Constant | Value | Role |
|---|---|---|
| `SOURCE` | `fantasypros_csv_2026draft` | The live 2026 board. Half-PPR-native, from the founder's manual export |
| `TRAINING_SOURCE` | `fantasypros_ecr` | The multi-season mirror. The **only** source with pre-2026 history |

**As of ADR-068 (2026-07-30), the exported *board* itself is selectable across four sources**, a
separate axis from the training/live split above: `RANKING_SOURCE_SELECTIONS` at
`src/make_board.py:129` (`expert_adjusted` default/unchanged-byte-identical, `expert_raw`,
`market_adp`, `proprietary`) drives `build_board`/`export_contract.build_board_json`'s
`ranking_source_selection` parameter. `expert_raw` orders by the source's own consensus;
`market_adp` orders by FFC half-PPR/10-team ADP (`_consensus_board_market_adp`,
`src/make_board.py:229`); `proprietary` has no implementation and deliberately raises
`RankingSourceNotBuilt` (`src/make_board.py:147`) rather than falling back silently. VBD/
projected_points/tiers are still computed under every selection except that only
`expert_adjusted` re-derives board order from our own VBD. **`simulate_availability`/
`draft_sim.load_season` are NOT wired to this selector** — both the opponent model and the
availability figures still run off the single hardcoded `fantasypros_ecr` regardless of the
board's selected source (`src/draft_sim.py:120`, `CONSENSUS_RANK_SOURCE`); see
`docs/CURRENT-STATE.md`'s 2026-07-30 backend "Follow-up audit" entry for the full consumer list.

The split matters: the 2026 source is format-correct but has one season; the training source has
2021–2025 but is *not* half-PPR (`src/ingest_rankings.py:25-37` explains why the swap was not
made — the FantasyPros free API caps every response at 10 rows). Both are now committed
(`data/rankings-history/`, `data/raw/founder-export/`) because neither is re-pullable.

**The pipeline, in order:**

1. `resolve_training_seasons` (`:194`) — picks which historical seasons to fit on.
2. `collect_observations` (`:220`) — pairs each player's preseason consensus rank against actual
   finish, per position.
3. `fit_rank_curves` (`:274`, one fit per position via `_fit_one` at `:251`) — the model is a
   per-position curve from consensus rank → expected points. This is the "ranking algorithm";
   it is a fitted curve, not ML, consistent with CLAUDE.md §6.3.
4. `bootstrap_vbd_intervals` (`:297`) — resampled intervals around value-over-baseline.
5. `build_board` (`:342`) — assembles `BoardRow`s.
6. `write_board_csv` (`:406`) → `data/board_2026.csv`.

**Feeds into the board JSON** (`src/export_contract.py:135`): the board rows, plus
`_load_availability_csv` (`:115`) for survival probabilities, `_bye_weeks` (`:93`),
`_canonical_team` (`:81`), and a freshness check via `fr.require_fresh` whose result became
exported fields at contract 1.13.0.

**Two ways in for backtesting** rather than the export path: `board_ranking_for_season` (`:421`)
and `board_as_ranking` (`:437`).

---

**Play-by-play ingestion, landed 2026-07-30, not otherwise described in this file's original
survey.** `src/ingest_pbp.py`: `fetch_pbp` (`:64`) pulls nflverse play-by-play via `nflreadpy`,
`ingest` (`:105`) upserts into `nfl.db`, CLI `main` (`:119`). Coverage starts **2009, not 1999**,
and the table has **no `yards_after_catch` column** — both discovered and recorded during factor
batch 7 (`docs/CURRENT-STATE.md`'s 2026-07-30 ranker "factor batch 7" entry), not assumptions.

**The factor-testing campaign's own code**, batches 2 through 7, lives under
`experiments/bottomup/factors/` — not `src/`, deliberately (this is experimental/methodology code,
not shipped product code). One `factor_features{N}.py` / `run_factors{N}.py` pair per batch
(`factor_features2.py`...`factor_features7.py`), plus `coord_preseason.py` (the Wikipedia
staff-navbox coordinator scrape feeding registry #29/#30) and `coord_join_diagnostic.py`. Each
batch's actual registered arms, results, and grades are in `docs/ranking/factor-batch-N-precommit.md`
/ `-results.md`, not in the code — read those, not this file, for what a batch found.

## 2. Where does league configuration enter, and where is it bypassed?

**The type:** `LeagueConfig` dataclass, `src/league_config.py:41`.
**The founder's league:** built by `build_current_league()` (`:168`), exposed as the module
constant `lc.CURRENT_LEAGUE`, scoring assembled by `_current_league_scoring()` (`:160`).

**It enters as a default argument, consistently:**

| Function | Line |
|---|---|
| `build_board_json` | `src/export_contract.py:137` |
| `build_availability_json` | `src/export_contract.py:424` |
| `build_league_json` | `src/export_contract.py:545` |
| `build_rosters_json` | `src/export_contract.py:673` |
| `write_all` | `src/export_contract.py:810` |
| `build_glossary` / `build_nulls` / `build_opponents` | `src/export_static.py:43, 335, 364` |

Both CLIs select a non-primary league the same way — `lc.CURRENT_LEAGUE if args.league ==
lc.PRIMARY_LEAGUE_ID else lc.LeagueConfig.load(args.league)` (`export_contract.py:843`,
`export_static.py:436`). Other configs are generated by `src/generate_config_matrix.py:76` and
`src/league_builder.py:139`.

**Where it is bypassed — three places, all real:**

1. **`NEED_ADJUSTMENT_SCALE = 10.0`** (`src/draft_sim.py:284`, applied `:303`). A module
   constant, not a config field. CURRENT-STATE records D-001 as *delete this parameter*, and
   also records that whether the code matches the decision was not checked. It is still here.
2. **A hardcoded WR adjustment** — `adj[data.positions == POSITIONS.index("WR")] -= 10.0`
   (`src/draft_sim.py:263`). A per-position magic number outside any config or versioned weights
   file. CLAUDE.md §4 requires model weights live in versioned config, "never hardcoded"; this
   does not.
3. **`DEFAULT_SIGMA = 10.0`** (`src/draft_sim.py:106`, swept at `:107`) — documented at `:23` as
   "roughly one round in a 10-team league," i.e. a value that silently assumes the primary
   league's size.

`user_draft_slot` is *not* in this list — it is read from config at `src/draft_sim.py:565`, and
`src/run_availability.py:121` notes a previously hardcoded `(18, 23)` pick pair has since been
generalized.

---

## 3. What does the availability model take as input, and what is hardcoded?

**Two layers, and the distinction is the thing to get right.**

**Layer 1 — prep-mode marginal P0.** `availability.simulate_availability`
(`src/availability.py:167`) runs a Monte-Carlo of thousands of simulated drafts and writes a CSV
per league config. Driven by `src/run_availability.py`. Inputs: `default_ranking_sources`
(`:79`), `positional_ranks` (`:157`), and the league config's own draft slot. Optional MFL ADP
source at `:86` — **available but deliberately not wired in** (thin sample, ADR-035).

**Layer 2 — live re-weighting.** `src/live_availability.py`. Fully parameterized: `live_survival`
(`:190`), `_hazards_at_pick` (`:164`), `hazard_from_marginal` (`:153`), `run_multiplier` (`:130`),
`run_z_scores` (`:101`), `need_share`/`n_need` (`:83`, `:91`). Nothing about a specific slot or
league is hardcoded in the hazard math itself.

**The structural consequence, verified by reading both files end to end:** layer 2 needs a P0
from layer 1, and **there is no function anywhere that returns a P0 for an arbitrary
(config, slot, as-of-date) triple on demand.** P0 is a batch artifact keyed to one config's fixed
`user_draft_slot`, not a callable prediction source. This is why the batch mock path uses the D-3
model-free baseline instead (`src/mock_prediction.py` on branch
`backend/mock-calibration-kickers`, and ADR-054 there).

**Hardcoded constants:**

| Constant | Line | Standing |
|---|---|---|
| `DEFAULT_LAMBDA = 0.352` | `src/live_availability.py:77` | **Measured.** n=160, the 2025 real draft, conditional logit, se=0.070, z=5.04. One season, one draft — keep the caveat attached. Source data now committed at `tests/fixtures/real_draft_2025/` |
| `DEFAULT_DELTA = 0.10` | `src/live_availability.py:78` | **Unvalidated prior**, and the code comment says so. Pre-registered rule: if need+run does not beat marginal-only on Brier across ≥30 conforming mocks, δ goes to zero |

Also note the config matrix runs against the primary league only — the hazard model has not been
re-run per config. That is a known limitation, not a bug.

---

## 4. What is in the export contract, and who reads each field?

**`CONTRACT_VERSION = "1.18.0"`** at `src/export_contract.py:48` (measured 2026-07-31; was 1.13.0
when this section was last written 2026-07-29 — six bumps landed between the two dates, latest
ADR-068's four selectable ranking sources, new files `board.expert_raw.json`,
`board.market_adp.json`, `ranking_sources.json`). The frontend pins the same string at
`frontend/ui/data/contract.ts:17` (`EXPECTED_CONTRACT`) — not re-verified this pass; check it
matches before trusting either number. **These two lines must move together** — a contract change
requires a version bump *and* a handoff thread to `frontend`, per the agent operating rules.

**Builders → artifacts:**

| Builder | Line | Artifact |
|---|---|---|
| `build_board_json` | `:135` | `board.json` |
| `build_availability_json` | `:424` | `availability.json` |
| `build_league_json` | `:545` | `league.json` |
| `build_rosters_json` | `:672` | `rosters.json` |
| `write_all` | `:808` | writes the set; the shared path everything goes through |

Static artifacts come from `src/export_static.py`: `glossary.json` (`:43`), `nulls.json` (`:335`),
`opponents.json` (`:364`).

**Field lineage worth knowing** (each was a contract bump, so each has a consumer):

- `scoring_format`, `board_source`/`consensus_source` — ADR-051, 1.10.0-era. `consensus_source`
  names `fantasypros_csv_2026draft` so the app can show *which* board it is looking at.
- `roster_status` — ADR-050. A **proxy** derived from `contracts.is_active`, not a real
  active/IR/practice-squad feed. CURRENT-STATE open item 7 tracks the real ingest.
- Four suspension fields (`suspension_flag`, `suspension_games`,
  `projected_points_suspension_adjusted`, `suspension_adjustment_note`) — ADR-053, 1.12.0. Real,
  dated, sourced, and **currently empty by verification, not by oversight**.
- Five snapshot-freshness fields (`snapshot_as_of_date`, `snapshot_age_days`,
  `snapshot_max_age_days`, `snapshot_stale`, `snapshot_freshness_note`) — thread 074, 1.13.0.
  Previously computed on every call and only printed to the build console.

**A fourth hub tab, `frontend/ui/components/TraditionalDraftBoard.tsx` (FR-135, 2026-07-30), reads
board/rosters/league exports the same way `Board.tsx` and `DraftRoom.tsx` do** — additive, wired
into `DraftRoom.tsx` alongside Board/Opponents/Predictions, no new export fields and no contract
change. Two views (pick-order snake, and by-roster-slot) over the same underlying pick data; see
`docs/design/research/draft-board/FINDINGS.md` for the design spec it was built against.

**Readers.** The app entry is `frontend/ui/App.tsx`; `frontend/server/autoSync.ts` moves exports
into `frontend/public/data/`. Field-level consumption is registered in
`frontend/ui/data/trace-fields.ts`, which is the honest place to look for "who reads this
field" — the trace registry exists precisely so a field cannot be added without naming a
consumer. Test coverage per field cluster is visible in the test filenames, e.g.
`frontend/ui/__tests__/suspension-and-scoring-format.test.tsx`,
`.../predictions.test.tsx`, `.../refresh.test.tsx`, `.../no-invented-numbers.test.ts`.

**Known stale:** `strategies.json` is still at contract 1.7.0 while everything else has moved
(CURRENT-STATE open item 5, thread 042). The app's version banner flags it correctly.

---

## 5. What do the acceptance harness and the mock capture each verify?

**They do not overlap.** One checks that the app *renders* what the data says; the other checks
that a logged draft is *trustworthy enough to calibrate against*.

### Acceptance harness — `tools/acceptance/`

Runner `harness.mjs`, checks in `lib/checks.mjs`, expected values in `lib/groundTruth.mjs`,
server control in `lib/server.mjs`. Node/Playwright, separate `package.json` from the frontend.

Its design note (`lib/checks.mjs:6`) states the intent: compare against **current, real data**
rather than a pixel diff that rots. Checks are content assertions:

| Check | Line | Asserts |
|---|---|---|
| `checkLeagueName` | `:49` | rendered league name == `groundTruth.league.league_name` |
| `checkPlayerCountHeader` | `:77` | header count == `groundTruth.playerCount` |
| `checkBoardRowsRendered` | `:112` | **rows actually in the DOM** == `groundTruth.playerCount` |
| `checkStatusBanner` | `:138` | banner matches `snapshot_stale` / `snapshot_age_days` / `snapshot_max_age_days` |

`checkBoardRowsRendered` is the one that matters most: it is the guard against the failure mode
this project has already hit — a fully green suite coexisting with a screen that renders nothing,
because no test asserted the screen existed.

### Mock capture — `src/ingest_mock_drafts.py`

Ingests a draft file and decides whether it can be used for calibration. Entry
`ingest_mock_draft_file` (`:193`), CLI `main` (`:303`), schema via `ensure_tables` (`:124`) and
`_migrate_add_column` (`:131`).

Three independent gates:

1. **Identity** — names resolve to real player ids or the pick is quarantined. The docstring at
   `:35` gives the reason: calibration numbers computed from guessed identities would be worse
   than none. This is why `mock_pick_quarantine` exists, and why the 2025 draft is 145 + 15
   rather than 160 clean.
2. **`format_conforms`** (`:143`) — the mock's `league_config_id` must point at a `LeagueConfig`
   matching this league's shape. A 12-team full-PPR mock cannot calibrate a 10-team half-PPR
   league.
3. **`_bot_seat_status`** (`:164`) — flags drafts with too many bot seats, which are not evidence
   about how humans draft.

Config resolution at `_load_league_config` (`:187`), defaulting to `lc.CURRENT_LEAGUE` (`:189`).

**The gap between them:** the acceptance harness verifies the UI against exported data, and the
mock capture verifies input data quality. **Neither checks that the model is any good** — that is
the backtest's job, and CLAUDE.md §6.5's baseline rule governs it. A green run of both proves the
app shows what the pipeline produced and the drafts were clean; it proves nothing about edge.
