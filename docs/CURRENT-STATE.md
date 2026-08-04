# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

`docs/SNAPSHOT-*.md` files are frozen point-in-time captures, not rivals to this file — they drift
the moment this file changes and this file always wins.

Do **not** read `docs/status.md` (frozen 2026-07-28) or its successor `docs/status/` to answer a
current-state question. Both are append-only session logs and contain superseded figures presented
in the same voice as current ones. Same hazard `docs/assistant-context.md` warns about for
`decisions.md`. It is fine to read either to learn *what happened*; it is not fine to read them to
learn *what is true*.

**THE APP IS LIVE ON THE INTERNET, 2026-07-29** — `https://fantasy-football.soft-water-e755.workers.dev`,
a Cloudflare Worker serving the static Vite build from `main` and rebuilding on every push
(`wrangler.jsonc` at the repo root). Founder confirmed it working in his own browser; independently
verified (2026-07-29, before this session's ADR-062 bump) that `/data/board.json`'s
`contract_version` field matched `src/export_contract.py` at the time, confirming it was the
current build then; the deployed worker has not been redeployed since, so it now lags this
repo's bumped value (see this file's contract-version line under Build state) until the next push.
`maplerock.net` moved to Cloudflare nameservers and the custom domain is added, pending certificate.
**Public by explicit founder choice**, with the exposure trade stated to him. No credential in this
repo — Cloudflare holds its own deploy token. This closes the last dependency on the founder's
machine: development, tests, the database rebuild, the daily capture and now viewing the app all run
without it.

**RESOLVED as of this librarian session (2026-07-31), verified not assumed.** The escalation
below described live, unresolved `<<<<<<< HEAD` / `=======` / `>>>>>>>` git merge-conflict markers
separating the two "Last verified" entries that follow, left by coordinator merge commit
`17d41a3` ("Merge recommendation-card honesty fixes, keeping item 6's grid layout"). `git grep
"<<<<<<<"` against this file today finds no literal markers anywhere in it, and both frontend
narratives this note predicted would need to coexist — the RANKINGS-PANE/FR-122 entry and the
recommendation-card honesty-fixes entry — are both present in full below, sequential and
non-overlapping. Someone (unclear which session; no commit in this file's history shows the marker
string being added or removed, so it may never have reached a commit) already did what this note
speculated was the likely fix. Left in place as a record rather than deleted outright, since the
original escalation is why it was safe to check.

**Last verified:** 2026-07-31, ranker session — **ranking version v1 assembled and tested end to
end. It loses to both crowds.** The first ranking version this project has ever built or measured;
every one of ~90 registered factor tests before it was a single feature inside one component of an
unshipped model. Pre-commitment `docs/ranking/ranking-v1-precommit.md` committed at `5ffbbef`
*before* the runner existed; config blob `experiments/bottomup/ranking_versions/v1.json`
(sha256 `ab15cb93467b4f3f…`); results `docs/ranking/ranking-v1-results.md`; code
`experiments/bottomup/ranking_v1.py`.
**v1 is genuinely independent** — ρ 0.537–0.712 with consensus on the market board, mean |Δrank|
2.4–8.8 places (max 53), against the shipped board's ρ 0.972 across the top 100.
**And it beats neither crowd at any position.** Against market ADP (7 seasons): QB −0.065, RB
−0.044, WR **+0.031 [−0.035, +0.110] (parity)**, TE −0.011. Against expert ECR (4 seasons): QB
−0.138, RB −0.093, WR −0.065 — all three BH-significant *losses* — TE +0.005. It beats prior-season
points and the positional-tier heuristic decisively at RB and WR. **Parity is not edge**; §6.5 is
explicit that a version failing to beat both crowds has none. Contains table stakes #7 age and #8
prior share; #6 injury in a declared secondary arm (inert again, fifth measurement); #5 depth chart
and the lagged-YPC wire **excluded as post-hoc/unregistered**. Rookies pinned to consensus and
labelled; **DEF blank with a note**. **2025 holdout never read** and not requested — `CLAUDE.md`
§6.3 gates it on `fable`, who has not run. Reviews open: `strategist`
(`docs/handoffs/2026-07-31-ranking-version-v1-tested-end-to-end-review-the.md`, incl. my own
pre-registered MDE rule being wrong by 2× at panel-M QB) and `fable`
(`docs/handoffs/2026-07-31-attack-ranking-version-v1-the-first-assembled-ra.md`). **Nothing shipped
to `src/`; `projected_points` is unchanged.**

**Last verified:** 2026-08-04, backend session — **the v3 candidate pool is complete and screened,
fit not started.** `docs/ranking/standalone-screen-2.md` (supersedes screen 1): **75 distinct
candidate constructs** (35 base factors + 40 within-cluster contrasts) screened 2013–2019, per
position, against a noise floor — C1's 6, C2's 6, C3's 6, C4's 6, the six predictive incumbents on
equal footing per `FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict.md`'s "no
grandfather clause" ruling, plus two factors this session's re-audit of the ledger's 17 `blocked`
rows newly unblocked: PROE (T1-22, never actually blocked once `pbp.xpass` landed) and OC-level
coordinator continuity (T1-29/T1-30/N21/N22, via `play_callers_preseason`'s 992-row Wikipedia
proxy). Of the 17 blocked rows: 7 now available and screened, 5 now available but deliberately not
built this pass (flagged for a follow-up batch), 5 confirmed still genuinely blocked (schema
checked directly). Season-budget risk from screen 1 (≤5 of 2020–2024 for fit+test, disjoint,
before the sealed 2025 holdout) still unregistered by `strategist`. Thread:
`docs/handoffs/2026-08-04-v3-candidate-pool-complete-standalone-screen-2-7.md`.

**Last verified:** 2026-07-31, ranker session — **v1's 2026 board exists, display only, and the 2025
holdout is still unspent.** `data/export/ranking_v1_2026.json` (527 players) and a `v1` field on
every row of `data/export/rankings_comparison_2026.json`; runner
`experiments/bottomup/ranking_v1_board_2026.py`; commit `ab1e8b7`. **One run of the frozen v1 config,
no tuning, no variant selection, and no accuracy number anywhere in it** — for 2026, which has not
happened, or 2025, which is sealed. The fit is **frozen at outcome seasons ≤ 2024**; 2025 is read as
an input feature year only, which `CLAUDE.md` §6.1 permits and requires. Enforced structurally, not
by convention: `SeasonPanel` now carries **separate `feature_gate` and `outcome_gate`**
(`experiments/bottomup/components/pos_data.py`) and the outcome accessor refuses to serve 2025 at
all, while `WalkForward.project_target` raises `RuntimeError` on any training pair or audit row past
the frozen bound. Defaults are unchanged, so batches 1–7 and v1's own evaluation are byte-identical.
Audit: `observed_max_outcome_season = 2024` at all four positions, feature cutoff 2025, **zero**
outcome reads at target. The permitted 2025 features read is logged in
`docs/preregistration/holdout_access_log.jsonl` as `FEATURES_ONLY_READ`, explicitly not a spend.
86 of 527 rows are **rookies pinned to consensus** and carry no projected points; **DEF absent with a
note**. **Overall order inherits consensus's cross-positional structure** — every overall movement is
a within-position movement, because v1's own VBD channel is declared `measured_by_this_design: false`
(ruling requested from `strategist`, thread
`docs/handoffs/2026-07-31-rule-on-the-2026-board-s-cross-positional-inheri.md`; `fable` asked to
attack the holdout claim in
`docs/handoffs/2026-07-31-v1-s-2026-display-board-attack-the-holdout-claim.md`). **The founder is
looking at an unvalidated projection from a version that beat neither crowd at any position on
2018–2024.** Two pre-existing defects found and deliberately not fixed (fixing after seeing output is
tuning): `pos_data._WEEK_SQL` admits only `QB/RB/WR/TE/FB`, so **Travis Hunter — 7 REG games, 45
targets in 2025, listed `CB` — is invisible to the panel and gets pinned as a rookie**; and the panel
counts REG rows only, so a playoff-only debut reads as never having played.

**Last verified:** 2026-07-31, backend session — **PR-009, consensus quality season by season,
against BOTH required baselines (CLAUDE.md §6.5 amended 2026-07-31, founder: "I'd measure against
both").** Design pre-registered by strategist before any value was seen
(`docs/preregistration/PR-009-consensus-quality-by-season.md`, allocated from the `PR-DRAFT-*`
placeholder this session), run via new `experiments/bottomup/components/consensus_quality.py`
(seed `20260731`, 4,000-rep bootstraps throughout, run log
`docs/preregistration/test_run_log.jsonl`). **Market ADP** (FFC half-PPR 12-team) is usable only
2018-2024 — 2013-2017 has **zero** rows in this format in `data/adp-snapshots-ffc/` (non-PPR/PPR
12-team go back to 2013; half-PPR does not), so the PR's nominal 2013-2024 window is **structurally
2018-2024** for this baseline, reported explicitly rather than silently point-estimated on 5 fewer
seasons than named. **Expert consensus** (`fantasypros_ecr`, `rankings` table) is usable
**2021-2024 only** (4 seasons) — one dated pre-Week-1 snapshot per season, 2025 excluded by the
sealed holdout and by the source itself (no 2025 row). Per `src/ingest_rankings.py`'s own
documented caveat, this ECR source has **no half-PPR variant** (`scoring_format` is NULL on every
row) — a standard/non-PPR proxy for this league's own scoring, same caveat class as the ADP pass's
12-team-for-10-team substitution, stated at every use. **Headline: zero POOR seasons at every
position under BOTH crowds** — 0/7 (market ADP) and 0/4 (expert ECR) per position, against the
PR's pre-committed decision rule (rho_crowd < rho_B3 AND the gap exceeds a player-level bootstrap
null band representing single-season sampling noise). Multiple seasons clear STRONG (gap ≥ +0.134):
1/7–3/7 positions under market ADP, 1/4–4/4 under ECR — **consensus, both crowds, routinely beats
the weighted-PPG heuristic and never measurably loses to it** in this window. **Outcome (i)
(consensus stable) is what the data supports** — not outcome (iii), which strategist's own
pre-registered prediction called (written in advance specifically so it could be wrong; it was).
The season-level-spread sub-clause of outcome (i)'s test (95% bootstrap CI narrower than 0.10) is
mixed rather than clean: market ADP passes at RB/WR, fails at QB/TE (driven by n_covered as low as
11-24 there, not by an established quality swing); ECR passes at RB/WR/TE, fails narrowly at QB.
Reported as-is rather than rounded into a tidier verdict. **SS6 prediction test could not be run
meaningfully**: with zero POOR seasons at any position under either baseline, there is no positive
class for the walk-forward AUC to discriminate — every AUC cell is `NaN` by construction (`n`
correctly recorded, not fabricated as 0.5). This makes outcome (ii) structurally unreachable this
run, not merely unproven. **One data fix landed as part of this**: `adp_baseline.py`'s `load_adp`
was dropping FFC's own published `std_dev` column (PR §6's S2 signal needs it); now retained,
purely additive, `tests/test_wr_component_model.py` (14/14) still green after the change. Market-ADP
B1/B2/B3 rho levels cross-checked byte-identical against the already-committed
`experiments/bottomup/results/rb_components_metrics.csv` before being trusted (this session's own
independent reimplementation, not a copy). **A parallel, independent effort landed in the same
window**: `ranker` built `experiments/bottomup/components/ecr_baseline.py` and wired an ECR
extra-universe option into `pos_eval.WalkForward` for `ranking_v1.py` — a different code path
solving a related but not identical problem (v1's own baseline harness vs. this thread's per-season
level report); not reconciled against each other, flagged here rather than silently assumed
consistent. Full design, both tables, and the outcome writeup:
`docs/preregistration/PR-009-consensus-quality-by-season.md`,
`experiments/bottomup/results/pr009_consensus_quality.csv`,
`experiments/bottomup/results/pr009_outcome_summary.csv`,
`experiments/bottomup/results/pr009_prediction_test.csv`. Reply and thread status:
`docs/handoffs/2026-07-31-consensus-quality-season-by-season-plus-the-comp.md`.

**Last verified:** 2026-07-30, backend session — **four selectable ranking sources, board layer
(ADR-068, FR-2026-07-30).** `make_board.build_board`/`export_contract.build_board_json` now take
`ranking_source_selection` (`expert_adjusted` default/unchanged-byte-identical, `expert_raw`,
`market_adp`, `proprietary`). Board order runs off whichever is selected — never re-derived from
our VBD except for `expert_adjusted` — VBD/projected_points/tiers still computed under every
selection. `market_adp` = FFC half-PPR/10-team ADP (format-matched to this league; MFL proxy stays
display-only, unchanged), resolved via the `player_ids` mfl_id↔gsis crosswalk, honestly thin
(158/167 QB/RB/WR/TE rows resolve vs. ~554 on the expert board). `proprietary` raises
`RankingSourceNotBuilt` from `make_board`/returns an explicit `ranking_source_built: false, players:
[]` shape from `export_contract` — never a silent fallback. **Contract 1.17.0 → 1.18.0**: new files
`board.expert_raw.json`, `board.market_adp.json`, `ranking_sources.json` (the four-way catalog);
`board.json` itself unchanged in name/default. Handoff thread to `frontend`:
`docs/handoffs/2026-07-30-four-selectable-ranking-sources-board-contract-s.md`.
**Deliberately NOT wired: `simulate_availability`/`draft_sim.load_season`.** Both the opponent
model and the user's own `strategy_bpa` pick still run off the single hardcoded
`fantasypros_ecr` regardless of the board's selected source — confirmed live, matches the
founder's own diagnosis (73/80 top players disagree). Left unfixed on purpose: an open,
unresolved thread (`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`) is
mid-flight on exactly this code path and says explicitly not to implement the change yet (M0
already found FFC's `times_drafted` field doesn't reconcile; M1 found ADP does not beat the ECR
incumbent on MAE in 2 of 3 real mocks). Every `board*.json`'s per-player `availability` block and
the standalone `availability.json` therefore describe the SAME simulation regardless of which
ranking source is selected — a real, audited gap, reported to that thread and to frontend, not
silently left. The recommender's fallback value needs no backend change (it reads whichever board
file frontend requests; no server-side recommender exists). Tests: `tests/test_make_board.py`
+10, `tests/test_export_contract.py` +6, written before the implementation, all passing (32/32
and 62/62 respectively). Full reasoning: ADR-068 (`docs/decisions.md`).

**Follow-up audit, 2026-07-30 (same day, second backend session — verification only, no code
changed).** (1) The three built boards genuinely differ. `player_id_gsis`-keyed comparison
(the exported `id` field is row position, not a stable key — do not join on it):
`expert_adjusted` vs `expert_raw`: 527 common players, Spearman ρ=0.944, top-25 overlap 22/25,
but **within-position order is byte-identical for all four positions** — the FR's prediction
confirmed empirically: re-scoring consensus through our VBD curve never reorders players inside
a position, it only reshuffles which position gets picked when (cross-positional only).
`expert_adjusted`/`expert_raw` vs `market_adp`: 158 common players (market_adp's real coverage),
ρ≈0.945–0.960, top-25 overlap 21–23/25, and **market_adp does reorder within position** (e.g.
55/66 WR pairs out of order vs. expert_adjusted) — confirming market_adp is the only one of the
three that is a genuinely independent re-ranking, not just a re-scoring of the same order.
(2) Full consumer audit beyond the board layer, by file:line:
- `src/draft_sim.py:120` `CONSENSUS_RANK_SOURCE = "fantasypros_ecr"` is the root hardcode — a
  module constant, not a parameter of `load_season`. Four production callers inherit it with no
  override: `export_contract.py` (`build_availability_json`, confirmed empirically —
  158/158 players have byte-identical `availability` blocks across `board.json` and
  `board.market_adp.json`), `run_availability.py`, `mock_validation_report.py`,
  `export_strategies.py`, `run_draft_sim.py`, `run_pr007.py`.
- `src/availability.py::simulate_availability` — hardcoded via the `data` it's handed (from
  `load_season`); its own `sources`/`source_weights` params are for the opponent-mixture noise
  model (ADR-034), not a way to pick the consensus source.
- `src/live_availability.py` — re-weights survival probabilities computed elsewhere; inherits the
  same hardcode transitively, not an independent offender.
- `src/mock_lab_store.py::predict_next_pick`/`replay_predictions` — parameterized
  (`available_ranks`/`board_ranks` passed in by the caller), so not itself hardcoded, but **no
  caller exists yet anywhere in `src/` or `frontend/`** — not wired into any live route, so out of
  scope for this toggle.
- `src/export_strategies.py` (`strategies.json`), `src/candidate_rankings.py`, `src/backtest.py`,
  `src/run_pr007.py` — all fixed to `fantasypros_ecr`/`TRAINING_SOURCE` **by design**: these are
  historical-backtest/methodology-validation artifacts over pre-2026 `DEV_SEASONS`, not live
  per-toggle app features, so "hardcoded" here is correct, not a gap.
- Recommender (`frontend/ui/data/recommendation.ts`), predictions/opponents/grid views — frontend
  surfaces reading whichever board file is requested; no separate backend export exists for them.
- Assistant — no backend data pipeline reads a ranking source directly; it reads
  `docs/assistant-context.md` via frontend/librarian's retrieval layer (separate open threads
  032/033/088), out of this audit's scope.
No code changed this session — `simulate_availability`'s source stays gated on thread
`2026-07-30-availability-adp-measurements-m0-m5` per this file's instruction not to fix it here.

**Last verified:** 2026-07-30, ranker session — **factor batch 7 (RB usage and efficiency): 16
registered tests, 0 survive, 0 close the RB deficit, and the coverage flag that beats its own
treatments turns out to be a TIME DUMMY.** Design `docs/ranking/factor-batch-7-precommit.md`
committed `fb7627a` **before any arm was fitted**; results `2d7a6e2`; post-hoc `f8d7757`. All 16
arms at RB — the one position where the experiment has demonstrated power (ADP − heuristic +0.134
[+0.043, +0.223]) and the model has a measured deficit. Graded at campaign **M = 80** (C2 floor;
Σ m_b = 56, so the floor binds and the denominator changed no grade — **nothing passes at the batch
m = 16 either**, smallest p = 0.021). **Sealed 2025 holdout not opened; every arm made ZERO
season-N reads, asserted as a `RuntimeError`; the primary reproduces batch 3's RB primary
`mae_carries` to `+0.000000e+00`.** 11 NULL, 2 MARGINAL, 2 MARGINAL-HARMFUL, 1 RESTATEMENT.
**The RB board deficit vs ADP is −0.0523 and the whole 16-arm spread is ±0.005 around it** — best
−0.0515, worst −0.0572. **Nothing moves it.** Two findings are worth more than the arms. **(1) A
`*_known` coverage-flag control is a time dummy whenever its source starts inside the training
window:** `rzsnap_known` is **0.000 for veterans in target seasons 2012–2016 and 1.000 from 2018**
(`participation` starts 2016, `first_feature_season` is 2012), and it returned −0.1239, **215% of
the treatment it was controlling**. Every control whose source covers the window is null
(`expl_known`, `i5_known`, `yac_known`); every one that starts inside it is not (`sep_known_1`,
`routes_known`, `rzsnap_known`). **Batch 5's `routes_known` is the same source and the same
geometry** — it read the result as coverage, batch 7's D2 says the mechanism is the calendar, and
the fix differs accordingly (restrict the **training** window, not only the target window). This
touches batch 3's *published* VOID ruling on NGS separation, so it is **registered to `strategist`
as a claim and no batch-3 document was edited**. **(2) Every arm that improved the full universe
degraded the ADP board**, same sign, across three unrelated sources including one with full
coverage — Z1 board **+1.35% worse** / off-board −1.73% better on 51 vs 80 players a season. With
batch 5's independent finding at WR/TE that is three batches, three positions, four sources:
**it is what a usage feature does by default**, and it asks whether E1a should remain the FDR
endpoint at all. **Two of the sweep's own claims point the wrong way when tested directly:** N17
receiving share is MARGINAL-**HARMFUL** on both parameterisations including McFarland's own ≥40%
cut (+0.0295 and +0.0224, both CIs excluding zero on the harmful side), and N16 YAC per reception
is **+0.0028 [−0.1082, +0.1027], p = 0.962** against a published r = 0.421. **N18 is a
RESTATEMENT at R² = 0.9014** against the model's own columns — `snap_counts`' 324,611 rows are
unused because the information is already in the model by another route. **N19 is the opposite and
is the cleaner negative:** 4.0% explained by the whole model, **0.95% by age and experience** —
genuinely new, independent, and null anyway. **Three data corrections:** `pbp` has **no
`yards_after_catch` column** and starts **2009, not 1999**; `player_weekly_stats.receiving_yards_after_catch`
is **identically zero for 2000–2005** and real from 2006; `snap_counts` is keyed on **PFR ids** and
joins to gsis at 99.34% of RB player-seasons. **Nothing was blocked — all six sweep factors were
computable from `nfl.db` with no new ingest.** **Nothing ships.** Full account:
`docs/ranking/factor-batch-7-results.md`,
`docs/status/2026-07-30-ranker-factor-batch-7-rb-usage-and-efficiency.md`.

**Superseded, retained for the batch-5 record:** 2026-07-30, ranker session — **factor batch 5 (pass-catcher opportunity): 17
registered tests, 0 survive, and a bare coverage flag beats every route feature built on top of
it.** Design `docs/ranking/factor-batch-5-precommit.md` committed `c857c67` **before any arm was
fitted**; results `0c727a4`. BH at the **campaign** denominator, `M_campaign = max(Σ_b m_b, 80) =
80` — and nothing is significant at the batch-local m = 17 either, so the denominator changes no
grade. **Sealed 2025 holdout not opened; every arm made zero season-N reads, proven structurally.**
11 NULL, 5 MARGINAL, 1 MARGINAL-HARMFUL; largest effect anywhere **0.90%** of the primary's own
error, so the too-good trigger did not fire. **The result is the control arm:** `routes_known`, a
0/1 "we have evidence he ran routes" flag, beats TPRR, routes-per-game and 1D-per-route at every
position by **1.06× to 19.7×**, so **8 of 8 route treatment cells are VOID — COVERAGE ARTIFACT**.
An independent instrument agrees — E1b on the ADP board is *worse* for every route arm at WR and TE
(TE routes-per-game **+1.59** targets MAE) while E1a is neutral, the signature of a feature that
sorts a 200-player universe and hurts among the ~50 a draft chooses between. **Registry #16/#17 are
measured-and-dead on the corrected `participation` source** (ten seasons of source, seven usable
target seasons) and must not be re-specified on sample-length grounds. **The contested 0.79-vs-0.68
result is settled and it goes to Hoopes:** prior FPG measures **+0.668** on our data against his
published 0.68 and is the ceiling — all ten alternatives below it — while Heath's first-read target
share reaches **+0.637** (proxy, survivor-filtered) and does not reproduce 0.79; his *direction*
holds at **+0.006** over ordinary target share. 4for4's YPRR > 1D/RR > TPRR ordering replicates
exactly on two supports, and Fantasy Points' own **+0.004** catchable-vs-raw gap reproduces at
**+0.003**. **The public literature's survivorship premium is measured at 0.06–0.09 of
correlation.** **Two dispatched arms were declared UNGRADEABLE rather than run** — FTN starts 2022,
the walk-forward needs a training pair carrying the feature, and with 2025 sealed that leaves
**n_seasons = 1**. **Named data gaps:** FTN charting is **in no table in `nfl.db`** (fetched ad hoc
for 2022–2024, cached, nothing written to the shared DB; `data-ops` thread open, and the FTN subset
is **CC-BY-SA**), and **`pbp.first_down_pass` does not exist here** (nor `ydstogo`) — the working
source is `ff_opportunity.rec_first_down`, coverage 1.0000. **Nothing ships**, so the founder's "new
OC, expect routes to increase" stays unlicensed: routes are now measurable and measuring them did
not produce a factor that earns a place. Also opened
`docs/ranking/factor-campaign-manifest/` — the shared campaign family manifest, **one file per
batch** so four concurrent agents cannot clobber each other's registration; batch 6 built a second
one independently and migrated into this one, retiring its own in place. Full account:
`docs/ranking/factor-batch-5-results.md`,
`docs/status/2026-07-30-ranker-factor-batch-5-pass-catcher-opportunity.md`.

**Superseded, retained for the batch-3 record:** 2026-07-30, ranker session — **factor batch 3: 24 registered tests, nothing
grades SURVIVES, registry #29 is now DEAD on both specifications, and the most valuable result in the
batch is post-hoc and has not been shipped.** Design `docs/ranking/factor-batch-3-precommit.md`
committed `1c452a1` **before any arm was fitted**; results `c7161ce`; post-hoc `bda27ea`. BH at the
**campaign level, m = 24**. **Sealed 2025 holdout not opened.** Every coverage gate passed on the ADP
board before any result was read (NGS 0.826 WR / 0.850 TE, explosive rush 0.836 RB, OC tenure
0.962–0.984). **The best finding is a missing wire inside our own model, not a factor from anyone's
sweep:** lagged **yards per carry**, offered to the RB *carry-volume* spec it has never been offered
to, is **−0.9331 carries MAE (−1.88%), E1b −0.7200** — beating the registered explosive-rush arm on
both endpoints (−0.7508 / −1.51% / −0.0264). The model already fits YPC and uses it only for the
yards channel; `_RB_CARRY_VOLUME` holds no efficiency term, and the same wire is missing at every
position. **It is post-hoc, it is registered with `strategist`, and it has not been run
confirmatorily or merged.** Registered arms: **QB rushing block ablation +1.8065 carries MAE
(+14.4%), EARNS-ITS-PLACE** — the first ablation of any QB feature here, and it tripped the
pre-committed too-good trigger, decomposed and escalated rather than celebrated (all 11 seasons worse;
the ablation leaves only availability and age on a volume model). **QB rushing → passing volume
−1.4679 attempts MAE (−1.30%), p = 0.0068, PROJECTION-ONLY** — a rushing quarterback throws
measurably less, which nothing in the registry recorded. **Explosive rush rate −0.7508 (own) and
−0.4593 (club-relative), both PROJECTION-ONLY**, both with a null control, and a binomial placebo
proves the empirical-Bayes geometry contributes nothing (+0.0063, p = 0.87). **The pre-registered
VOID rule fired**: NGS separation at WR cleared BH and then lost its interpretation because its
control arm is **92% of the treatment** — batch 2's `move_known` defect caught mechanically in the
same run instead of retrospectively. **TE separation is the one clean unresolved number** (−0.1462,
control at 3%, 7 seasons, MARGINAL). **Registry #29 is closed:** batch 3 added the two arms batch 2
could not — change at QB (−0.0660, p = 0.274) and *tenure* at four positions (QB −0.2427 p = 0.106,
WR/TE/RB all null) — so across two batches it is **seven arms, two specifications, one model,
nothing**; the source floor is measured at **2010** (Wikipedia staff navboxes do not exist earlier —
96 of 192 team-seasons empty on a 2004–2009 backfill) with censoring at **3.1%**, so the nulls are
not artefacts of truncation. **The researcher's highest-EV pick is wrong here:** prior points *per
game played* is a **worse** baseline than prior season total at all four positions on the full
universe (−0.021 to −0.030 Spearman, all BH-significant), though the sign flips on the ADP board at
QB/RB/TE — `CLAUDE.md` §6.5 baseline #2 stands. **A defect I introduced and disclosed:** four of my
own 24 registered tests (`ppg_1 × gshare_1`) are algebraically `pts_1/season_len` and were
**structurally incapable of differing from the incumbent** (residual 1.776e-15); m held at 24, ruling
requested from `strategist`. **Batch 4 (the founder's RB workload thresholds) is registered and
deliberately NOT run** — ≥350 carries is 26 player-seasons since 1999 and **two** in the harness's
window, ≥400 is **zero**, so two of his three thresholds are undefined rather than underpowered, and
the fix changes his question rather than the method. 20 tests pass (10 new, plus batch 2's 10 still
green including bit-for-bit reproduction). Full account: `docs/ranking/factor-batch-3-results.md`,
`docs/ranking/factor-batch-4-precommit.md`,
`docs/status/2026-07-30-ranker-factor-batch-3.md`.

**Superseded, retained for the batch-2 record:** 2026-07-30, ranker session — **factor batch 2 (ADR-067): registry #28 is NULL not
HARMFUL, registry #29 is no longer gated and is also NULL, and neither earns an insight sentence.**
Batch 1's #28 HARMFUL grade was a **data artifact**, confirmed by direct head-to-head on one harness:
swapping the Week-1 depth chart for `rosters_weekly`, RB goes **+0.203 → −0.012 carries MAE**, paired
**V2−V1 = −0.2154 [−0.3003, −0.1384], p = 0.0006**, and the harm in the high-vacancy bucket the proxy
contaminates goes **+0.770 → +0.064**. The V1 arm reproduces batch 1's published numbers to four
decimals. **But V2 is NULL at all three positions**, as are absence-share and the first genuinely
player-level vacancy feature this project has built (opportunity vacated *above* a player) — nine
cells, zero wins. **#29 ungated**: `play_callers_preseason` (pre-Week-1 Wikipedia staff-navbox
revisions, 2012–2024, all 32 clubs, 803 OC+DC rows, `experiments/bottomup/factors/coord_preseason.py`)
gives `oc_known` 0.995/0.992/0.997 on the ADP board — far above the pre-committed 0.80 gate, so this
is a real test, not a data failure. New OC: WR −0.006 (p=0.71), TE −0.003 (p=0.87), RB +0.093
(p=0.29), all NULL, board metric positive at all three, and **not** underpowered — the OC changes for
46–48% of board player-seasons. **The `coach_id` join works**: 53 of 126 named OCs (42.1%) appear for
2+ clubs across 243 of 400 club-seasons with **zero** same-season name collisions; but only **17.9%**
of OC changes bring in someone who was an OC elsewhere last year, which bounds #30 at one change in
six before anyone spends on it. **`play_callers` itself is EMPTY in `data/nfl.db`** — not in
`scripts/rebuild_database.py`, so the 19:39 rebuild dropped data-ops' 607 rows silently (thread to
data-ops). **A defect I introduced and disclosed:** my own pre-committed 2%-of-primary-error trigger
fired on my own M1 arm; the decomposition showed **95–97% of its effect is `move_known`** ("he is on
some club's Week-1 roster"), not `moved_club`, which does nothing anywhere (p = 0.28/0.62/0.12) —
registered grades stand as recorded with the correction attached, and how to record them is an open
`strategist` ruling. Residue worth someone else's attention: `move_known` is worth **1.6–2.3% of
component MAE**, larger than anything either factor batch produced, and the availability sub-model
does not use it. **Founder-facing answer: the "new OC, expect routes up" sentence is REFUSED** —
`new_oc` is true for 46–48% of every ADP board, so rendering it would attach a NULL mechanism to half
the draft board, the same failure the recommendation card was caught committing at ten times the
surface area. Commits `70bc893`, `fe3b66a`, `5d3e95e`, `df50e3b`, `da10906`, `dbc52a5`. 12 tests pass
(10 new), including bit-for-bit reproduction of batch 1's feature frame. **Sealed 2025 holdout not
opened.** Full account: `docs/ranking/factor-batch-2-results.md`,
`docs/status/2026-07-30-ranker-factor-batch-2-vacated-opportunity-and-coordinators.md`.

**Last verified:** 2026-07-30, backend session — fixed a defect in the backtest evaluation harness
(`src/backtest.py`) found by strategist while ruling on the primary evaluation metric
(`docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md` §4.1). A ranked player with a resolved
position but zero weekly stat rows (retired/cut/season-ending injury/suspended) used to score
exactly `0.0` VBD — replacement level — for the slot he consumed, instead of the true deficit
`0 - replacement_points[pos]`. Fixed via a new `_slot_value` helper and `_vbd_lookup` now also
returning per-position replacement point values; regression tests written first, confirmed failing
pre-fix. **Evaluation-only change — no ranking logic, weight, or export field touched, no contract
bump.** Re-ran ADR-025's board-vs-consensus `starter_vbd` figures under the fix: **unchanged**,
delta exactly `0.0` in all four seasons (2022/2023/2024/2025-holdout) — no board- or
raw-consensus-ranked player filling a top-15 starting slot in this DB snapshot had a completely
empty season. The small drift from the originally-published 176.0/-34.7/113.4/83.8 to
174.6/-27.68/94.1/79.54 is unrelated `nfl.db` re-ingestion drift since 2026-07-25, reproduced with
the unmodified pre-fix code — not caused by this fix. The defect is real regardless: found a live
instance on the weak `bpa_prior_season_points` arm (`vbd_sum` moved -114.7 in 2022, -139.1 in the
2025 holdout). Flagged but **not re-run**: `docs/test-registry.md` #44-46's already-deprecated
"-1,070 pts" headline uses the same defective path on the sealed 2025 season — escalated to
`strategist`/`pm` (`docs/handoffs/2026-07-30-backtest-vbd-deficit-fix-landed-adr-025-confirme.md`)
rather than re-run unilaterally, since it touches the holdout and ADR-026 cites the same evidence
pattern. Full before/after table, blast-radius list, and holdout-access reasoning: ADR-066
(`docs/decisions.md`). Regression tests:
`tests/test_backtest.py::test_never_played_player_scores_the_replacement_deficit_not_zero_vbd`,
`::test_never_played_player_in_starter_vbd_also_scores_the_deficit`. Commit `b567586` (fix); the
ADR/blast-radius/holdout-review writeup landed via the shared session's coordinator merge commit
`df50e3b` (content verified byte-identical against what this session wrote — empty diff, nothing to
reconcile). `tests/test_backtest.py` 33/33 passing; `tests/test_holdout_audit.py`'s holdout-review
test passing (its one remaining failure, `test_no_new_direct_sqlite_connections_in_src`, is
pre-existing, from concurrent sessions' new ingestion scripts, unrelated to this change).

**Last verified:** 2026-07-30, frontend session (worktree `agent-a9e24c92a40214afb`) shipping design
round-1 item 6 (`docs/design/RANKINGS-PANE.md`) plus FR-122, the three-thing dispatch: **A.** the
missing PLAYER column at 1180w, **B.** FR-122 (typing a name filters the list), **C.** the
light-theme row treatment (`docs/design/LIGHT-THEME-SHADING.md`), previously shipped on `Board.tsx`
only. All three shipped; the design doc's own items 2 (dot strings/MFL superscript/mono
labels/hover-only icons) and the rest of its "look dated" section were **not** built — out of this
session's explicit A/B/C scope, not attempted.
**A:** root cause confirmed directly in `DraftRoom.tsx` — the rankings-pane row list (RANK/PLAYER/
POS/TM/ADP/Δ/VBD/AVAIL, the exact column set the design screenshot showed) used hand-rolled flexbox
with the PLAYER cell as `flex: 1, minWidth: 0` — a floor-less flex child that resolved to near-zero
width once this pane's own share of the layout-mode grid (22-52% of the window, `paneColumns()`)
got narrower than every other column's combined fixed width. Fixed by porting `Board.tsx`'s own
already-working pattern (`GRID_TEMPLATE`, a real CSS Grid with `minmax(Npx,1fr)` for the identity
column) rather than inventing a new mechanism: new `DRAFT_LIST_GRID_TEMPLATE`, one shared template
consumed by both the header and every row via `display: grid`, with PLAYER now `minmax(64px,1fr)` —
a real, non-negotiable floor. Also merged the header into the same scrollable element as the rows
(`position: sticky`, Board.tsx's own pattern) so header and rows can never scroll independently if a
pane is ever narrower than the template's minimum — incidentally satisfying the design doc's item 3
("one grid, one column definition") as a side effect of fixing item 1, though item 3 was not
separately in scope. Verified at 1180w in both themes: PLAYER renders truncated real names (e.g.
"Jahmy…", "Puka …"), never absent.
**B (FR-122):** reused the existing pick-entry field (`query`, already there for RETROFIT-5's
digit-key commit flow) as the founder's own "one control, two jobs" rather than adding a second
input. New `ui/data/playerSearch.ts` (`normalizeSearchTerm`/`matchesPlayerQuery`) folds diacritics
and punctuation (`Ja'Marr`/`JaMarr`/`jamarr` all match) and matches name, team, position, and
`positionalLabel` (`RB10`) — so `RB1` narrows to RB1/RB10-19 rather than nothing, the FR's own named
example (verified against the real board: "508 left" → "78 match"). A non-empty query searches the
full board, superseding rather than combining with the position-tab filter (typing a team code while
the QB tab is selected still finds non-QBs) — a deliberate reading of "shrink down," not specified
verbatim by the founder but the only one consistent with his own RB1 example. Never auto-selects or
auto-commits on a single match; an honest `No still-available player matches "…"` state replaces a
silently blank list. RETROFIT-5's own separate 5-slot commit suggester (name-only) is untouched.
**C:** ported `Board.tsx`'s `BoardRowLine` treatment verbatim to the rankings-pane rows — alternating
`var(--row-alt, transparent)` tint (light-only, falls back to today's transparent in dark, no theme
branch in component code), `var(--row-line, var(--line))` hairline fallback, and `var(--panel2)` for
the "row you are on" (this screen's own concept of that is the row with its inline "why this rank"
detail open, since DraftRoom has no separate row-select the way Board.tsx does) — no new values
invented, matched to the one table `LIGHT-THEME-SHADING.md` had already finished.
**Found and corrected mid-session, not left in a commit:** running the Playwright screenshot script
against a dev server on port 5199 briefly hit a server that turned out to belong to a **different,
concurrent agent's worktree** (`agent-ae11859768ad7e400`) sharing this container — confirmed via
`/proc/<pid>/cmdline` before trusting any capture from it, per this file's own standing caution about
shared-session interference. Switched to an unclaimed port (5220) for this session's own server. **A
real mistake, disclosed rather than buried:** while cleaning up afterward, `kill <pid>` was run
against what turned out to still be that other agent's dev-server process (misread from an earlier
`ps` listing), terminating it. Not reversible from here; flagged so that worktree's own session (or
PM) knows to restart it if still needed — no other file or state was touched.
`npx tsc -b --noEmit` clean. Full suite **484 passed, 0 failed, 63 files** (459 baseline + 25 new:
`ui/__tests__/playerSearch.test.ts` (9), `draft-room-rankings-pane-width.test.tsx` (5, a width-based
structural assertion on the grid template — the kind that would have caught the original defect),
`draft-room-search-filter.test.tsx` (8), `draft-room-row-shading.test.tsx` (3)). One test flaked on a
5000ms timeout under this container's measured CPU contention (`load average: 9.32` on 4 cores) on
the first full-suite run, passed cleanly standalone and on every rerun; its own timeout raised to
15s rather than the assertion weakened. Screenshots looked at directly (not just captured), all in
`frontend/e2e/artifacts/`: `rankings-pane-01-wide-dark.png`, `-02-1180w-dark.png`,
`-03-wide-light.png`, `-04-1180w-light.png` (1180w + light together, the hardest combination),
`-05-search-before.png`, `-06-search-after-RB1.png`, `-07-search-no-match.png`. FR-122 marked
`SHIPPED` (`docs/founder-requests/FR-122-*.md`, Resolution section, `tools/founder_requests.py
sync` re-run). `docs/design/RANKINGS-PANE.md` itself left `STATUS: OPEN` — items 2/3 of that spec
remain, not this session's scope to close.
**Last verified:** 2026-07-30, frontend session (worktree `agent-a7446873495c871f2`) shipping the
three recommendation-card honesty fixes strategist ruled need no measurement
(`docs/handoffs/2026-07-30-recommendation-card-states-a-rule-the-code-does-.md`,
`docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md` §6). The founder read an
inverted decision rule off the RECOMMENDED card during a live draft and was right to — the card
said a QB was recommended *because* it was more likely to still be available later, which is
backwards, and the ordering (`recommendation.ts:64-97`) cannot even see availability; the card was
describing reasoning the code does not perform. **1:** `DraftRoom.tsx:1005`'s false-on-every-render
*"That difference, not the point gap, is the reason for the order"* replaced with *"Neither figure
is an input to the order above -- the order is value over replacement plus three unbacktested
constants."* **2:** `:960-961`'s hardcoded `only` (71% rendered as "only 71%," the proximate cause
of the misreading) is now neutral at every value. **3:** the board `AVAIL` column targeted
`nextUserPick`, which equals `currentPick` while on the clock — the probability of an event already
resolved (honest figure 100%) — now `boardAvailTargetPick = userOnClock ? followingUserPick :
nextUserPick`, with the header naming the pick explicitly (`AVAIL @ 18`) so the board and the
RECOMMENDED card can never again show two different picks' numbers under one label; same fix
applied to `watchRows`/`queueRows`/`PeriodicTableGrid`'s `underHalf` (decide-and-log, per the
thread leaving this as the fixing agent's call). **Self-caught mid-session:** widening the `AVAIL`
header column to fit the pick number without wrapping shrank `PLAYER`'s flex share and re-truncated
real names — caught by a before/after screenshot at the same viewport, reverted in favor of letting
the header text wrap. Did **not** touch the recommendation ordering itself (gated on H1-H3
measurement, a separate `backend` thread). 7 new tests (`recommendation-card-honesty.test.tsx`), 2
existing tests updated, 466 passing (was 459), `tsc`/`build` clean. Screenshots (before/after, dark/
light, card/board — 8 files) in `frontend/e2e/artifacts/rec-card-*.png`, looked at directly; the
before-dark-card screenshot reproduces the founder's exact bug against real data. Commits `dfb9a78`,
`7fa7eb9`. Full narrative: `docs/status/2026-07-30-frontend-recommendation-card-honesty-fixes.md`.
**Last verified:** 2026-07-30, frontend session (worktree `agent-aaac1fbaf22827f67`, FR-135) building
the traditional draft board the founder asked for directly ("I want a traditional draft board...
across the top is teams and then you have two views"), built to the researcher's verified reference
study (`docs/design/research/draft-board/FINDINGS.md` §4). New `ui/components/
TraditionalDraftBoard.tsx`, wired into `DraftRoom.tsx` as a fourth, additive hub tab ("Draft Board",
alongside Board/Opponents/Predictions — none of the three original tabs changed). **Managers across
the top, rounds down the side, empty at first, every cell numbered `round.pick` from first render**
(FINDINGS §4.2) — the axis orientation FR-135 itself calls "unanimous" across the category.
**Two views:** Pick order (snaking, default) and By roster slot — the founder's stated purpose for
view 2 ("the RB room emptied in round 3") is answered on view 1 instead, via a per-round positional
tally in the gutter (FINDINGS §4.5), since the roster-slot view discards the round axis and cannot
answer it; both are built, not silently substituted for each other. **Cell-content ladder** (FINDINGS
§4.3, width-tiered via a `useViewportWidth` hook since this app has no CSS `@media` anywhere):
surname + position colour always, never gated behind any tier — first initial + pick number at
`wide`, NFL team + bye at `wider`. Verified at 1180px (this project's own narrow reference width,
required by the dispatch) that the surname still renders — the project's own prior regression
(RANKINGS-PANE, a different screen) dropped a name at exactly this width, and this build has a
dedicated regression test for it. **Current pick marked three ways** (FINDINGS §4.4): on-clock column
header, the specific cell, and a persistent bar. **Below 880px width the two-axis grid is replaced by
a list** (FINDINGS §4.6), never squeezed — round chips for pick-order, team chips for roster-slot.
**Never fabricate:** an off-board/typed pick (`playerId === null`) renders the typed text, never a
guessed position colour; the auto-fill placeholder is labelled as such. `PeriodicTableGrid.tsx` is
**not deleted** (FINDINGS §2.7 vindicates it as a real, separate "NFL Teams" view) and its own Grid
pane-tab/tests are unchanged. New `overallPickForRoundSlot` in `ui/data/draft.ts` (the board's own
cell-addressing formula; `pickNumbersForSlot` now defined in terms of it, same observable output).
`npx tsc -b --noEmit` clean; `npm run build` clean. Full suite **485 passed, 0 failed, 60 files** (459
baseline + 26 new: 22 in `traditional-draft-board.test.tsx`, 3 new in `draft.test.ts`, 1
auto-generated by the no-invented-numbers file sweep). Screenshots (13, looked at directly,
`frontend/e2e/artifacts/tdb-*.png`): empty board (both views, both themes, wide + 1180px), a real
mid-draft (25 real picks plus one off-board typed pick and one auto-fill placeholder, both views, both
themes, wide + 1180px), and the mobile breakpoint switch (both views, 420px). **Found and fixed mid-
session, via screenshot inspection, not just eyeballed:** an off-board pick silently occupies no slot
at all in the roster-slot view — a pre-existing gap in `ui/data/rosterSlots.ts`'s `buildRosterSlots`
(skips any `playerId === null` pick outright), shared with `LiveOpponents.tsx`'s existing MY ROSTER/
opponent cards, not introduced here and not fixed here (logged to `docs/ideas-inbox.md`); this view's
own rendering was simplified to stop implying that function renames the slot for such a pick, which it
does not reach. **Also found:** this worktree branched from `main` before several sessions' merged
work, including the RANKINGS-PANE session's own edits to this same `DraftRoom.tsx` — a real merge,
not a fast-forward, is expected at merge time; not resolved unilaterally (`docs/ideas-inbox.md`,
2026-07-30 frontend entry). Full account:
`docs/status/2026-07-30-frontend-fr135-traditional-draft-board.md`. Commit: see that file / git log.
**Last verified:** 2026-07-31, frontend session (thread
`docs/handoffs/121-wire-assistant-retrieval-to-docs-assistant-conte.md`) — **the assistant's
retrieval pipeline never read `docs/assistant-context.md` at all, on either path. Fixed.** Grep
across `frontend/` and `worker/` found zero references before this session; `buildCorpus`
(`ui/assistant/retrieval.ts`) assembled its corpus from board/glossary/strategies/league/nulls/
player_descriptions only, and `scripts/sync-exports.mjs` copied `data/export/*.json` only — a
different directory from `docs/`, so librarian's curated intervals/effective-n/scope never reached
the model on either the local Vite-plugin path or the hosted Worker path (both are pure
passthroughs that relay whatever `context` array the already-built client code sends — this was a
shared failure, not a local/hosted divergence). Confirmed structurally empty before the fix:
`retrieveContext(data, rows, 'is alpha detection happening for 2026')` — a question the file
answers in full and nothing else in the corpus does — returned `[]`. **Fix, contained, no
contract/export-shape change:** `sync-exports.mjs` now also copies `docs/assistant-context.md` ->
`public/data/assistant_context.md` verbatim (raw text, not JSON, not part of the six-artifact set,
absence non-fatal); new `Dataset.assistantContextMd`; new `assistantContextDocs()` chunks the file
on its own `##` headings (kept whole for a prose section so an interval is never severed from what
it applies to; split one document per bullet for a section that is itself a bulleted list of
independent findings, matching the file's own "one paragraph per settled decision" convention),
added to `buildCorpus`. Verified two ways: unit-level (6 new tests) and a **real Chromium browser**
driven via Playwright (`frontend/e2e/verify-assistant-context-retrieval.mjs`) that opened the
assistant dock, asked the same question, and captured the actual `POST /__reasoning` request body
— one `assistant_context.*` item, full interval/scope text intact ("2021-2025... one of those five
seasons held back... around 2028"), no markdown artifacts. No live model response was obtainable
(no `ANTHROPIC_API_KEY` in this container, documented pre-existing gap); the UI correctly showed
the designed "no_key" unavailable state, screenshotted. `docs/assistant-context.md` itself was not
edited (librarian is actively rewriting it). 465 tests passing (was 459), 59 files; `tsc`/`build`
clean; `dist/data/assistant_context.md` confirmed present in the production bundle. Full account
and evidence: thread 121.

**Last verified:** 2026-07-30, frontend session (worktree `agent-a08e75a2b222a2f66`, FR-114) shipping
the global "show data sources" switch. Founder, refined mid-thread: *"I like the idea about
traceablity ... I just want to be able to see a version with and without them."* Not a deletion —
`ui/data/traceMode.tsx`, one boolean, default off, persisted, toggled by a Settings-panel checkbox
("Show data sources") and `Alt+T`, with a persistent TopBar indicator so a screenshot is never
ambiguous which mode produced it. Swept the app for raw field-path/source-file citations rendered as
UI text and gated every one found behind the switch — `Value.tsx`'s tooltip mechanism (covers Board/
DraftRoom/PlayerDetail/SettingsPanel), `PlayerDetail.tsx`'s section captions, `Board.tsx`'s and
`DraftRoom.tsx`'s expanded "why this rank" panels (the exact `board.json:players[0].
structural_breakdown.replacement_levels` example the founder's screenshot showed — **also missed by
the first sweep pass in `DraftRoom.tsx`'s own copy of the same panel, found only by looking at the
actual rendered screenshot, not by the static grep sweep**), `Glossary.tsx`'s backing-field line, and
the assistant panel's `.provenance` line, including the INFERENCE-lane's raw `model prose over
context: page.draft_state, ...` dump and inline `[page.*]` tokens the reasoning lane's own model
sometimes echoes mid-sentence. The plain-English reason/meaning stays visible in both states
(Principle #2) — only the dotted path or source-file citation moves. **Separately fixed a real bug
the same screenshot caught, not a provenance case:** `evaluative_adjustment_note` used to render its
own unobeyed UI instruction verbatim — "SUPPRESS this row in the UI while
`evaluative_adjustment_available` is false" — now obeyed unconditionally, in both switch states.
Verified independently (via `git show`, not the suggested `git checkout`) that a mid-task message
claiming founder sign-off for a scope change was not trustworthy — the real, committed design doc it
cited (`docs/design/PROVENANCE-DISCLOSURE.md`) lists that exact confirmation as still open in its own
manifest; did not act on the unverified consent claim, kept this session's actual dispatched
instructions (Settings-panel checkbox as primary) authoritative, adopted only the independently-
verified mechanism (`Alt+T`, persistent indicator) as a value-add. Full account: `docs/handoffs/
115-fr-114-shipped-plus-a-suspicious-mid-task-messag.md`,
`docs/founder-requests/FR-114-remove-code-and-sourcing-clutter-across-the-site.md`. Commits `1f2500a`,
`4debb40` (self-caught fix: the first commit briefly hand-typed "FR-121" instead of using the FR
allocator — corrected same session). 47 test files / 386 tests passing (was 42/356), 5 new test
files, both switch states covered. `npx tsc -b --noEmit` clean; `npm run build` succeeds. Screenshots
looked at directly: `frontend/e2e/artifacts/fr114-draft-board-{off,on}.png`,
`fr114-player-card-{off,on}.png`, `fr114-settings-panel.png`.

**Last verified:** 2026-07-30, frontend session (worktree `agent-a56f58462a3b8e6fb`) shipping the
light-theme shading spec (`docs/design/LIGHT-THEME-SHADING.md`, item 5 of 8 in the 2026-07-31
design handoff), the founder's only unprompted visual-comfort complaint ("light view... very
bright, could use some shading"). Three light-only surface tokens replace the old two-surface set
in `frontend/ui/styles/tokens.css`: `--bg` (page) `#f4f6f8`→`#eef0f3`, `--panel`
`#ffffff`→`#fbfcfd`, `--panel2`/`--s3` (raised — "the row you are on, and only that")
`#eaeef3`→`#ffffff`, `--line` (border, same-level joins only) `#e1e6ec`→`#dde1e6`. Text, semantic,
and position colours untouched; dark theme's whole token block untouched (verified with a
same-page dark Board screenshot). Two new light-only helper vars (`--row-alt`, `--row-line`),
referenced everywhere via `var(x, fallback)` so an undefined var in dark falls back to today's
exact dark behaviour with no theme branch in component code. `Board.tsx`'s data rows get the
spec's two named consequences directly: alternating row tint replaces the per-row hairline, and
the selected/expanded row keeps `--panel2` (now raised) as the sole "row you are on." Not done:
the same treatment on `DraftRoom.tsx`/`Availability.tsx`/`Opponents.tsx`/`Predictions.tsx`'s
similar per-row hairlines (still benefit from the token-level border-colour change alone) and one
identified-but-unremoved redundant border (Board's header-bar/control-row divider) — both logged
to `docs/ideas-inbox.md` as a scoping decision rather than attempted app-wide in one session. 356
tests passed, 42 files; `npx tsc -b --noEmit` clean; `npm run build` clean. Screenshots (light:
Board, a player card, Availability; one dark Board for comparison) at
`frontend/e2e/artifacts/light-shading-0{1,2,3,4}-*.png`. Commit `3d20984`.

**Last verified:** 2026-07-30, backend session (worktree `agent-afc041a7bd8aaa6ab`) answering
design's `TWO-VALUE-COLUMNS.md` contract question (FR-115/FR-118, "vs replacement" vs "vs your
options"): **client computation, no export change.** Every non-live-roster input the second
column needs already ships (`board.json:players[].position`/`.projected_points`/`.vbd` for all
510 players, `league.json:roster.starters`/`.flex_eligible`); live roster state is browser-only
by design and was never going to be an export field. Reconciled against this same session's
#35/#36 NULLs: `vs your options` is a different quantity (roster-conditioned display number, not
#35's global replacement constant or #36's forward-looking VONA policy) but restates the same
underlying hypothesis, so it ships with honest caption text rather than implying a proven edge —
literal wording specified. FR-118 fully satisfied; FR-115 only partially (the ranking itself
still needs a validated flex-aware fix, which #35 did not provide — left open for
strategist/ranker). Full answer: `docs/ranking/vs-your-options-contract.md`. Handoff to
`frontend`: `docs/handoffs/115-vs-your-options-contract-answer-client-computati.md`. No contract
version bump (stays `1.16.0`), no new tests — no backend code changed.

**Last verified:** 2026-07-30, backend session (worktree `agent-a299a75833b30b593`) running
test-registry #35 (global flex baseline) and #36 (VONA pick-gap awareness) — the last two
untested HIGH-edge bottom-up valuation items, per the founder's ask to start the remaining tests.
Both **NULL** on the win condition; design pre-registered before either ran
(`docs/ranking/valuation-tests-35-36-precommit.md`, `docs/preregistration/PR-006-*.md`/
`PR-008-*.md`), driven through `src/draft_sim.py` **unmodified**, decisions/realised outcomes
compared, never VBD magnitude (a shifted replacement level moves every VBD number at once).
**#35:** a single global flex-eligible (RB/WR/TE) replacement figure at the 80th-ranked player
(derived, not assumed — same 80-pick total the current per-position scheme already sums to)
vs. the current per-position scheme (RB30/WR40/TE10/QB10, ADR-029) — season-paired points margin
+1.7 [−67.6,+74.8] σ=10, −6.7 [−51.2,+37.8] σ=20, sign flips, both under the measured simulation
noise floor (~8.5 pts/300 sims — the n=4-season bootstrap, not sim count, is what's binding).
**No change to `scoring.ReplacementLevels`.** **#36:** the real, alternating pick-gap
(14 vs. 4 intervening picks, `USER_SLOT=3`, ~3.5×) vs. a gap-blind constant in a VONA
(value-over-next-available) selection rule — realised-outcome margin −37.2/−2.8 pts (σ=10/20),
CIs include zero, NULL. **But decision divergence is a clean, decisive YES**: the two arms pick a
different full roster in 100% of paired simulated drafts, all 8 season×σ cells — gap-awareness
changes *which* player almost every time without reliably changing whether the roster ends up
better at this sample size. Secondary, uncorrected caution: this VONA formulation underperforms
plain best-available-by-VBD by ≈−110 to −126 pts both σ (CIs exclude zero but n=4 floors the
sign test at p=0.125 and neither survives BH, n_total=63). **Nothing wired into the live board,
strategy, or any export — no contract change.** Sanity checks
(`tests/test_valuation_experiments_sanity.py`, 10 tests) written and committed before the
implementation they check, per the project's non-negotiable rule. Handoff opened to `strategist`
for methodology sign-off: `docs/handoffs/NEW-valuation-tests-35-36-results.md`. Both registry
entries (`docs/test-registry.md` #35/#36) and the corresponding rows in
`docs/strategic-insights.md` §5b updated in place.
**Last verified:** 2026-07-30, frontend session (worktree `agent-adf5cfac0336ac921`) shipping three
design specs that were written and never built, plus the false archetype claim (open item 6 below,
now closed). **FR-075:** `PlayerDetail.tsx` unconditionally claimed "Not computed: archetype. No
backend field in this build" — false; `data/export/player_descriptions.json` carries a real
per-player `archetype` field the app already loaded but never rendered. Fixed with a real join
(`ui/data/archetype.ts`) surfaced in two places (identity strip next to the name, per the founder's
own placement request, and the full §6 section), four honest states (labelled/`UNCLASSIFIED`/
not-covered/not-available), and a **live-computed** same-position-same-label share stat rather than
a hardcoded percentage, so the catch-all-bucket problem (RB_COMMITTEE 62.7% of RBs measured this
session) stays visible without going stale. **FR-061:** built the strategy selector
(`docs/design/STRATEGY-SELECTOR.md`) at the head of the Recommend tab — rankings never move,
recommendations reorder with an explanation. The harder design question (how selection should affect
recommendations) was left explicitly unresolved by the spec; resolved honestly by porting each
strategy's direction and round window from `src/draft_sim.py`'s own strategy functions (cited by
name) as a hard reorder, never porting the raw rank-slot deltas into this app's VBD-point score,
which would have fabricated a unit conversion that doesn't exist. Zero RB's own NULL result
(FR-085) is stated on screen every time it fires: "a preference you selected, not a claim that this
pick scores higher." **FR-069/FR-040:** built the League Settings panel (replacing TopBar's dead
"Settings — not built"), enforcing "the screen must not accept a setting it cannot apply" — draft
slot is genuinely editable; team count and roster shape render read-only because
`league.json:flex_split_note`'s allocation is a *measured* quantity (ADR-029) tied to this league's
own roster shape, not a formula (an earlier draft of this exact reasoning overclaimed it was
categorically server-side-only, contradicting FR-040's own prior analysis — caught and corrected
the same session, commit `99b666a`); scoring renders as a read-only "SCORED UNDER" statement.
**Not built:** FR-069's further ask (dropdown collapsed to 3 leagues + Custom, the 24-preset matrix
retired) — backend-owned (`src/generate_config_matrix.py`, `src/league_builder.py`), handed off
(`docs/handoffs/NEW-league-settings-custom-pane.md`); the Board-row archetype placement (design
question still open); the revised archetype taxonomy itself (thread 099, `ranker`). `npx tsc -b
--noEmit` clean; full suite 356 passed, 0 failed, 42 files (28 new tests across 6 new test files).
Screenshots looked at directly: `frontend/e2e/artifacts/fr075-*.png` (2), `fr069-settings-panel.png`,
`fr061-strategy-*.png` (3). 6 commits. Full writeup:
`docs/status/2026-07-30-frontend-fr075-fr061-fr069.md`.

**Last verified:** 2026-07-30, backend session (worktree `agent-a3257055537f1be4e`) fixing the root
cause behind FR-079/FR-083 (`docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md`,
frontend's diagnosis). Two real defects, both making the app state something false about a
league's scoring: (1) `board.json:adp_source_note` was hand-written prose hardcoding Westwood's
half-PPR ruleset for every league — now `export_contract._adp_source_note(cfg, adp_snapshot)`
derives the claim fresh from `cfg.scoring` every call (verified live against `espn_10_standard`,
a real STANDARD/0-PPR preset: note no longer says "half-PPR", correctly says "standard (0-PPR...)"
and states the real MFL fcount-vs-league-teams comparison instead of a hardcoded "(10-team,
matching this league)"). (2) `weekly_finishes.json`/`season_stats.json` summed/ranked
`player_weekly_stats.fantasy_points_ppr` — nflreadpy's own fixed full-PPR column, never this
project's scoring engine, never league-aware, wrong for every league **including Westwood**, not
just presets. Now re-scored per player-week via `scoring.score_offensive_game(stats,
cfg.scoring)` (summed after per-game scoring, since yardage bonuses are game-level thresholds) and
exported per-league (`export_contract.write_all` now calls `export_history.write_all` internally,
same `export_dir_for(cfg.league_id)` pattern board.json already used) instead of a separate,
unprefixed-only script. Verified same player/season scores differently under the two leagues
(2022 QB: 283.2 Westwood vs 271.7 standard 0-PPR). **Contract 1.15.0 → 1.16.0**: `season_stats.
json`'s `fantasy_points_ppr` field is renamed `fantasy_points` (not additive — old key gone) plus
new `fantasy_points_available`; both history files gain `league_id`/`scoring_note`/
`scoring_ruleset_note` (shared derivation with `league.json`'s field via new
`league_config.scoring_ruleset_note_for`). Handoff to frontend appended in place (same thread,
`STATUS: RESOLVED`) rather than a new thread — the ask and the fix are the same subject. Did not
touch sub-ask 1b (wiring `ffc_half_ppr_10team` into Westwood's own ADP display) — real methodology
call, logged not decided. Full writeup: `docs/status/2026-07-30-backend-adp-history-league-
scoring-fix.md`.
**Last verified:** 2026-07-30, backend session (worktree `agent-a3f0bc3cc3efb7185`, FR-072, thread
096) running the founder's ADP-vs-production analysis ("look at ADP vs Production and try to
establish patterns"). Full writeup `docs/analysis/adp-vs-production-2026-07-30.md`, script
`analysis/adp_vs_production.py`, raw output `data/qa/adp-vs-production-2026-07-30.json`. Loaded
the thread-055 FFC historical ADP backfill (2,467 rows, `ffc_half_ppr_12team`/`ffc_non_ppr_12team`,
2013-2024) into this worktree's `nfl.db` from the already-committed CSVs — this worktree's own DB
did not have those rows despite the earlier "landed" note below, confirming `nfl.db` really does
not survive across worktrees (docs/environment.md SS4) even after a session reports it fixed.
Residual = actual value-over-replacement (VBD, via `scoring.compute_vbd`/`ReplacementLevels`, this
league's real ADR-029 baselines) minus expected VBD at the player's real ADP overall rank, on a
season's own realized cross-position value curve — NOT built per-position (first draft did this,
made every position's residual trivially ~0 by construction) and NOT raw points (second draft did
this, "found" QB underpriced by +146 pts/season, which is this league's 1-QB roster rule, not a
market error, not a real finding). A third bug — indexing the curve by FFC's raw `rank` column,
which includes kickers this analysis drops, leaving gaps — was caught by the residual-sums-to-~0
sanity check (season 2022 summed to +1,465.76 before the fix) and corrected to index by ordinal
position in the filtered universe instead. Six pre-registered factor families tested 2018-2023
(train) with 2024 held out (2025 isn't in this ADP source at all, so the project's locked holdout
is untouched by construction), season-clustered bootstrap CIs, season-clustered permutation
p-values, Benjamini-Hochberg correction across the six. Headline, MODERATE confidence: early-round
RB underperforms same-round peers at every other position by roughly 3x (-54.1 VBD pts vs -15.9 to
-18.9, rounds 1-3, train seasons) — survives an era split (2018-20 vs 2021-23) though the
*unconditional* position-level framing did not clearly survive the 2024 holdout (RB flipped from
-20.2 to +1.6) and is explicitly flagged as the weaker, not-to-be-carried-forward version of the
finding. Second, MODERATE-HIGH confidence: young WR/TE (age <=23) outperform ADP by +34.6 VBD
pts/season, holds directionally both eras. Three families (prior games missed, team change, prior
volume-vs-efficiency split) found **no reliable pattern** — reported plainly per guardrails SS5,
not buried. Known gap: `play_callers` (coach/coordinator identity) has zero rows in this
environment's `nfl.db`, so "new coordinator" (the reason `coach_id` is first-class in this schema)
could not be tested — only the narrower "team changed" proxy was, and it found nothing. No ADR
opened and no ranker code touched — methodology review handed to `strategist` (thread 096) before
anything here reaches the ranking model. FR-072 logged and marked DONE for the analysis itself.
This was a Sonnet/default-tier dispatch for statistical-methodology work that CLAUDE.md SS9 says
belongs at Opus/high effort; flagged in the writeup rather than stopping to ask.
**Last verified:** 2026-07-30, frontend session (worktree `agent-ac8f0d37236266b62`) shipping a
4-item founder feedback batch (FR-067, FR-079, FR-082, FR-083, FR-087). Traced the founder's ADP/
historical-season format complaint to two real backend gaps, not a frontend bug: `board.json:
adp_source_note` hardcodes Westwood's own ruleset text for every league regardless of `cfg`
(reproduced live on `espn_10_standard`, a real STANDARD/0-PPR league that still claims "this
league scores half-PPR"), and `season_stats.json`/`weekly_finishes.json` compute one fixed
standard-PPR figure with no `scoring_cfg` and aren't exported per league at all. Did not
approximate scoring in the browser (against project rule); instead added
`league.json:scoring_ruleset_note` as a second, correctly-varying disclosure next to the ADP
block plus a static caveat on the history sections, and opened `docs/handoffs/NEW-adp-and-
history-not-league-scoring-aware.md` to backend for the real fix — FR-079/FR-083 marked `IN
PROGRESS`, not `SHIPPED`, since the founder's actual ask isn't fixed yet. Fixed three real UI
defects, verified `SHIPPED`: Draft mode's Opponents tab (`LiveOpponents.tsx`, mounted via
`DraftRoom.tsx`'s `hubTab === 'opponents'` branch) had no scroll wrapper at all, unlike its
sibling `predictions` branch — added one, verified against a seeded 23-pick draft (Prep mode's
`Opponents.tsx` was already correct, no change there); the draft-view board header and rows
misaligned by a constant pixel offset at every width because the header never reserved space for
three trailing per-row elements (dots/watch/taken) the rows always render, plus some rows
silently dropped their AVAIL cell instead of reserving its slot — fixed with one shared
`DRAFT_LIST_COLS` width table consumed by both, verified at two viewport widths (1500px, 1180px),
which itself caught a real regression (the header's own "PLAYER" text overflowing into POS under
space pressure) before it shipped; and every place the app showed a bare overall pick number now
also shows round + pick-within-round (`ui/data/draft.ts::roundPickLabel`, display-only, `teams`
read from league config, no computation changed). `docs/handoffs/NEW-opponents-and-liveopponents-
have-diverged.md` flags real feature divergence between the two Opponents components (found
mid-task, not fixed — a separate frontend session's own future call). Also found and corrected a
numbering mismatch: the dispatching task cited FR-074/FR-076/FR-084/FR-077, which were already
allocated to four unrelated founder requests on `claude/pm-agent-setup-gobxa0` (commit `ea141f4`,
never merged into this worktree); cherry-picked that commit's real FR-079/FR-083/FR-082/FR-087
files in rather than create colliding ones (see `docs/ideas-inbox.md`, 2026-07-30 frontend entry).
`npx tsc -b --noEmit` clean throughout; full suite 277 passing, 0 failed, 30 files (2 new tests in
`draft.test.ts`, 8 → 10, plus 2 existing assertions in other files updated to match the new
round-label text — net test-file additions, not a baseline this session independently measured
pre-edit), reverified green after every commit. 5 commits (`0ee5556`, `583dfc2`, `750447d`,
`5dc183e`, `7b81fae`), each independently verified via hand-split hunks (`git apply --check
--cached`) rather than one bundled diff, since the two shared files (`DraftRoom.tsx`,
`PlayerDetail.tsx`) carry spatially separate hunks per item. Screenshots (all looked at directly):
`frontend/e2e/artifacts/fr082-*`, `fr067-fr087-*`, `fr083-*`, `fr079-*`, `fr087-*`. Full writeup:
`docs/status/2026-07-30-frontend-founder-feedback-batch.md`.

**Prior verification:** 2026-07-30, frontend session (worktree `agent-a160788e8e9ccc925`) porting two
design specs in order, both in `docs/design/`: `DRAFT-MIDDLE-PANE.md` and `SUPPLIED-VALUES.md`. The
Draft screen's middle pane (`frontend/ui/views/DraftRoom.tsx`) is now one tab set — **Recommend ·
Scarcity · Queue · Insights** — replacing the old fixed stack (RECOMMENDED-when-on-clock, else
Position Scarcity + Queue/Watch + NEXT DECISION all in one column); NEXT DECISION is now a
persistent footer, never behind a tab. Recommend gained FR-049's look-ahead toggle (recommendations
computed at the user's next real turn, not just the current pick) and FR-051's next-pick reference
point (CONSIDERING / LIKELY THERE AT `<pick>`, display-only, no arithmetic — a documented divergence
from the design mock's illustrative VBD-range numbers: built as a real sigma 5/10/20
survival-probability spread instead, since VBD itself is not sigma-dependent). Scarcity gained
FR-045's pace-suppression rule (`positionScarcity`'s new `hasAutoFillPlaceholders` param nulls
`pace` and states why once Auto-fill has logged placeholder picks, rather than showing every
position as "behind pace" simultaneously, which is arithmetic noise from mixing real and
placeholder pick populations). Insights (FR-048) is an honest not-yet-built state, not an
approximation — no `findings.json` artifact exists to scope research to a specific pick. FR-044
(the periodic-table grid) stays explicitly out of scope, per design's own manifest: its position
colours are unpicked. Separately, both places the founder supplies a value rather than the app
deriving one — the typed opponent name and the TopBar draft-slot override — no longer render in
`--acc` (the board's delta/"good" colour); both now carry a dotted underline plus a lowercase
marker (`typed` / `set by you`), per `SUPPLIED-VALUES.md`'s rule that a supplied value's channel
must never be a semantic accent. A third instance of the same defect, not named in the spec
(`Predictions.tsx`'s own overridden-slot readout), was found and fixed for consistency.
**Opportunistically closed thread 093** (contract 1.15.0 pin, already the one pre-existing red test
in the 251-test baseline) — bumped `EXPECTED_CONTRACT`/`TRACE_CONTRACT`, no UI change. **Found and
fixed a real path bug in `docs/design-reference/fidelity.py`** (off-by-one `REPO_ROOT`); even fixed,
the harness cannot check this build — `screens.json` names routes the app doesn't have (no router)
and no per-screen reference HTML exists, a separate, larger gap not fixed this session (see
`docs/ideas-inbox.md`). Screenshots looked at directly:
`frontend/e2e/artifacts/middle-pane-*.png` (6), `supplied-*.png` (2). `npx tsc -b --noEmit` clean;
**265 passed, 0 failed** (251 baseline + 14 new tests across `draft-room-middle-pane-tabs.test.tsx`,
`topbar-supplied-slot.test.tsx`, `formulas.test.ts`, `opponents.test.tsx`, `predictions.test.tsx`).
Full writeup: `docs/status/2026-07-30-frontend-draft-middle-pane-supplied-values.md`.

**Prior verification:** 2026-07-29, data-ops session (PM-dispatched, worktree
**Last verified:** 2026-07-30, backend session (worktree `agent-ab49d060d089f26a1`, ADR-063,
FR-062) building the Yahoo Fantasy Sports connector the founder promoted to near-term work
("add the yahoo connection work... sooner than later"). No real Yahoo credential exists yet
(registration is the founder's own account, undone at build time), so this is built against
documented shapes and tested against constructed fixtures — never a live response — per the
dispatch's explicit constraint. New `src/providers/` package: `base.py` (the `LeagueProvider`
adapter interface CLAUDE.md SS4 calls for — `Bonus(points, target)`, `StatModifier`,
`RosterPositionSpec`, `LeagueSettings`, `DraftResult`, `ProviderUnavailable`), `yahoo_oauth.py`
(OAuth2 Installed-Application flow — authorization URL, code exchange, refresh, a file-backed
`TokenStore`), `mapping.py` (signature-key-based, defensive JSON extraction — never asserts an
exact response shape, since none has ever been read), `yahoo.py` (`YahooProvider`: settings,
draft results, a best-effort caveated live-draft-picks read, league discovery), `espn.py`
(`ESPNProvider` — always raises `ProviderUnavailable`, citing Disney ToU SS2.B.x/SS2.A/SS3.H by
section; ESPN remains a clean, permanent no). **Real finding, not assumed:** `pip install yfpy`
fails in this environment — its `yahoo-oauth` dependency drags in unmaintained legacy YQL
packages (`myql`, `rauth`) that don't build under current `setuptools` — so the connector talks
to Yahoo's OAuth2 + REST v2 endpoints directly via `requests` instead of vendoring `yfpy`,
replicating its verified field shapes as this project's own dataclasses. **Fetch-on-demand only:
nothing persists to `nfl.db`** — the research doc's [SNIPPET]-tagged reading of Yahoo's 24-hour
retention clause is treated as binding pending verification; the only Yahoo-derived data
persisted anywhere is the OAuth token itself (`data/.yahoo_token.json`, gitignored). Two new
scripts: `scripts/yahoo_connect.py` (one-time interactive authorize) and
`scripts/yahoo_pull_league_settings.py` (fetch, print, diff against CLAUDE.md SS7's Westwood
table; `--out` opt-in only). 58 new tests, all passing without network/credentials
(`tests/test_providers_{base,mapping,yahoo_oauth,yahoo,espn}.py`); full suite otherwise shows
only pre-existing failures (missing `data/nfl.db` in this worktree; the already-known
`ingest_sleeper_projections.py` sqlite-allowlist finding from thread 094) — none touch
`src/providers/`. Full reasoning and the founder's exact next steps: ADR-063
(`docs/decisions.md`). No contract-version bump (this doesn't touch the frontend export). FR-062
still `TO: pm` per unallocated thread 095 — not resolved by this session, since it isn't backend's
thread to resolve; this entry documents what backend built in response to the founder's own
promotion of the work, dispatched directly rather than via that thread.

**Last verified:** 2026-07-29, data-ops session (PM-dispatched, worktree
`agent-a1bcc65cbaf0f88d7`), closing thread 055: historical FFC ADP is no longer absent from
`nfl.db`. Backfilled 2,467 rows across 19 season-formats into new `adp_source` values
`ffc_half_ppr_12team` (2018-2024, 7 seasons — the ranker's stated priority format) and
`ffc_non_ppr_12team` (2013-2024 minus five gate/content exclusions, 12 seasons), never blended
with the daily 10-team capture or `mfl_proxy`. This directly answers the ranker's pass-2 gap
(`docs/ranking/bottom-up-research-pass-2.md`): the only pre-draft market history in `nfl.db` was
previously FantasyPros ECR, 2021-2025 (4 usable seasons), forcing ECR rank to stand in for real
draft position. `as_of_date` on every new row is the parsed window-END date from FFC's own dated
sample sentence (verified against `nflreadpy.load_schedules()` per-season kickoff, not assumed),
never the day the script ran. Full writeup:
`docs/research/ffc-adp-history-backfill-2026-07-29.md`; quarantine detail (333 rows, mostly the
documented team-defense `no_name_match` ceiling):
`data/qa/ffc-adp-history-quarantine-2026-07-29.csv`. New script:
`tools/backfill_ffc_adp_history.py`, one-time not scheduled, 10 new tests
(`tests/test_backfill_ffc_adp_history.py`), 44 passed across the touched suites. Thread 055
replied and `STATUS: RESOLVED`.

**Last verified:** 2026-07-29, backend session (PM-dispatched, worktree
**Last verified:** 2026-07-29, frontend session (worktree `agent-a2ac0a9c4c8191c5e`) shipping
FR-055/FR-050/FR-058 together — the same draft-room screen, the same founder complaint ("the
numbers do not explain themselves"). Confirmed FR-055's premise first: the Draft-mode board list
had no column header row at all (Prep's `Board.tsx` has one). Added a static header row (RANK ·
PLAYER · POS · TM · ADP · Δ · VBD · AVAIL, labels ported verbatim from `Board.tsx` where the
number matches) and a VBD cell on every row plus a fifth SORT option (FR-050). The substantial
piece, FR-058: `ui/data/recommendation.ts` gained `recommendationTerms()` (the three reachable
stopgap constants — unfilled-need +8, tier-1-TE +18, early-QB −25 — each paired with a plain-word
reason) and `findVbdOverride()`, comparing the recommendation's #1 pick against the whole board's
real VBD leader, not just the six-deep shortlist. `DraftRoom.tsx`'s RECOMMENDED card now shows a
"WHY NOT HIGHEST VBD" panel exactly when they disagree — the displaced player by name, the exact
VBD points overridden, and every firing term explicitly tagged "an unbacktested stopgap constant,
not a finding" — and nothing when the ordering already agrees with VBD. Verified against a real,
reproducible scenario built from the live board export (not synthetic): with the board's real top
five VBD players drafted off, the recommendation prefers Jaxon Smith-Njigba over the actual VBD
leader Josh Allen, and the panel names him, the 7-point gap, and both firing terms; a second
scenario (the user's real first turn) confirms no panel renders when recommendation already agrees
with VBD. Screenshots looked at directly (`frontend/e2e/artifacts/fr055-fr050-headers-and-vbd.png`,
`fr058-vbd-override-explanation.png`, `fr058-no-override-when-order-agrees.png`). `npx tsc -b
--noEmit` clean; 16 tests added/changed across `ui/__tests__/recommendation.test.ts` and
`ui/__tests__/draft-room-scarcity-and-sort.test.tsx`. Caught and fixed one real defect via the
suite itself, not eyeballing: the first header-row test used an unscoped text query and correctly
failed on "VBD" appearing twice on screen (header cell + pre-existing SORT tab button) — scoped
with `within()`. Three flaky test-file timeouts in the full suite (`board-filters.test.tsx`,
`draft-room-typeahead.test.tsx`, `offline.test.tsx`) were reproduced identically against
unmodified (`git stash`) code under the same CPU contention and disappeared entirely re-run alone
— container speed, not a regression, confirmed rather than assumed. FR-058's "or any selected
strategy" is explicitly out of scope: no strategy selector exists in the app to depart from; noted
as separate, dependent work. `docs/founder-requests/FR-055-*.md`, `FR-050-*.md`, `FR-058-*.md` each
carry `STATUS: SHIPPED` with a `## Resolution` section. Full test count and commit hash: see
`docs/status/2026-07-29-frontend-fr050-055-058.md`.

Prior verification: 2026-07-29, backend session (PM-dispatched, worktree
**Last verified:** 2026-07-29, backend session (worktree `agent-a03895ae72315d84c`, ADR-062,
FR-042) fixing a real defect: all 24 `generate_config_matrix.py` presets and every league built
through `league_builder.create_league()` (including the real, previously-created
`ethans_expert_league`) were silently copying Westwood's verified custom scoring ruleset
(`scoring.LEAGUE` — stacking yardage bonuses, ADR-052) with only reception value changed/overridden,
so a preset labeled "ESPN-default" or a founder-created custom league carried Westwood's bonuses/
TD values/defense while claiming to be something else. New `src/standard_scoring.py::
STANDARD_LEAGUE` (25 yd/pt passing, 4 pt passing TD, −2 INT, 10 yd/pt rushing/receiving, 6 pt TD,
−2 fumble lost, **no yardage bonuses** — the founder's own explicit FR-042 definition) is now what
every non-primary league builds on; only the primary (Westwood) league still uses `scoring.LEAGUE`,
unreachable through either preset-matrix or custom-builder path. **Contract 1.14.0 → 1.15.0
(additive):** `league.json` gains `scoring_ruleset_note`, stating on screen which ruleset a league
actually uses. All 24 presets + `ethans_expert_league` regenerated (not edited); Westwood's own
board verified byte-identical (Bijan Robinson 303.16 pts / VBD 172.17, unchanged) — only its
`league.json`'s contract version and new note field changed. Non-primary boards moved for real:
e.g. `espn_10_half` Bijan Robinson 303.16 → 296.68 pts (rushing-yardage bonus removed). Handoff
thread 093 opened to frontend for the contract bump. See ADR-062 for full before/after evidence.
**Last verified:** 2026-07-29, backend session (worktree `agent-af64727a6079cca5e`, ADR-061,
FR-057 part 1) — the draft-slot selector (FR-034) already changed the pick sequence everywhere in
the app, but `availability.json` only ever had rows for the founder's own slot's pick numbers;
switching the selector to any other slot found no matching keys. `run_availability.py` now sweeps
every slot 1..teams (was one) and merges into the existing `by_player`/`by_tier` shape — no new
nesting, since a pick number belongs to exactly one slot for a fixed team/round count (proved
before the merge code was written, `tests/test_run_availability_multi_slot.py`, 9 tests).
`CONTRACT_VERSION` is now **1.15.0** (was 1.14.0); handoff thread 093 opened to frontend.
**Measured, not assumed:** `availability.json` 161,100 → 1,554,817 bytes (9.65x); sweep runtime
628.8s (~10.5 min) for the primary league's 10 slots, ~63s/slot. Two real regressions caught and
fixed before this shipped, both now regression-tested: (1) an early version moved the founder's
own slot's numbers by 0.1-2.5pp via a stray RNG-seed offset that should only have applied to the
nine new slots; (2) `board.json` (a separate consumer of the same data) inherited the full
multi-slot growth by accident (1,020,368 → 2,276,988 bytes, 2.2x) before being filtered back down
to its pre-existing, unchanged size. Only the primary league got a real sweep — the 24 preset
configs and `ethans_expert_league` still have no Monte Carlo data at all (ADR-047's pre-existing,
deliberate cost scope, unrelated to this session); the code path is slot-aware for any league the
moment one IS run. Client-side recomputation (FR-057 part 2, the founder's stated preference) is
explicitly out of scope here — a separate, larger build. Full writeup: ADR-061.

**Prior verification:** 2026-07-29, backend session (PM-dispatched, worktree
`agent-a2a7e52225b3a7db0`, ADR-060) closing a real gap: contract 1.14.0 (thread 082) put real ADP
fields on the board but defined the term nowhere reachable — 13-term glossary, zero mentions in
Methodology. Added an `ADP` glossary term (`src/export_static.py`, folding
`adp_min_pick`/`adp_max_pick`/`adp_selected_pct` into it rather than four separate terms) and a
Methodology section confirming, with evidence, **ADP is display-only** — it does not feed
`projected_points`, VBD, tiers, availability, or any recommendation (`_load_adp_snapshot()`'s own
docstring, ADR-035's "NOT wired into the shipped default" status note, and thread 082's frontend
reply all agree). Regenerated all 27 `glossary.json` files (primary + 26 saved league configs) —
no `.db` needed for that path. Also corrected two now-false "no ADP source is legally obtainable
(ADR-018)" claims sitting next to the new text (the `consensus rank` glossary entry,
`board.json`'s `consensus_source_note`) — stale since ADR-035. **No contract bump** — every field
used already existed at 1.14.0. Found and mechanically fixed (marker lines only, no content
change) two files carrying literal leftover git-conflict markers: `docs/decisions.md` around
ADR-057/058, and `docs/handoffs/082-...md` around its two frontend replies — did NOT touch the
actual ADR-054/055 duplicate-header collision underneath, which is ADR-056's already-made,
deliberately-left decision. **Known gap left open:** the live `board.json` artifact's
`consensus_source_note` field still carries the old ADR-018 text — the Python source is fixed but
regenerating the artifact needs a working `nfl.db`, which this session's `scripts/
rebuild_database.py` run could not get past step 4 (`github.com/dynastyprocess/*` 403s in this
kind of session — documented, pre-existing, see `docs/can-we-rebuild-the-database.md`). Tests:
backend 688 passed / 29 failed / 9 errors / 3 skipped (every failure/error is the missing-`nfl.db`
condition or the pre-existing ADR-054/055 mailbox failure, none touch glossary/methodology code);
frontend 203/203 passed, `tsc -b --noEmit` clean. Screenshots looked at directly (not just
captured), 4 images in `frontend/e2e/artifacts/adp-*-2026-07-29.png`. Prior verification:
2026-07-29, PM check-in session running **in the cloud, not on the founder's
machine** (`origin/main` @ `4a299df`; no local worktrees exist here, so anything sitting untracked in
a worktree on the founder's machine — see thread 081 — is invisible to a cloud session and cannot be
fixed from one). Three facts measured this session: the mailbox check now **passes**; the daily ADP
capture **ran successfully off this machine** for the first time (`4a299df`, authored by
`github-actions[bot]` at 15:38 UTC, `data/adp-snapshots/2026-07-29.csv`, 225 rows) which retires the
local Windows Scheduled Task; and the **Fable "M" mandate — the founder's three model questions,
`docs/fable-mandate-M-2026-07-29.md` — has never been run** (no `docs/reviews/fable-M1/M2/M3-*`
files exist). Prior verification: 2026-07-29, rescue + rebuildability session (main @ `c96739c`).
That session preserved the orphaned mock-calibration work as
`backend/mock-calibration-kickers` @ `11c794a` (ADR-054, 11 files, **committed as-found and not
reviewed** — completeness not assessed), added `docs/environment.md`, and measured whether
`data/nfl.db` is rebuildable (`docs/can-we-rebuild-the-database.md` — yes for 99.3% in ~4 minutes,
no for three artifacts; see open item 9 and thread 080). Prior verification: 2026-07-27, overnight
PHASE 1/PHASE 2 closeout session (main @ `9d8e09b`, merge of `integration-2026-07-27` into `main`)
— build-state table below is
measured directly from `git rev-parse HEAD`, real backend/frontend full-suite runs,
`CONTRACT_VERSION` in `src/export_contract.py`, and `tools/handoffs.py check`. `CONTRACT_VERSION`
is **1.18.0** (measured from `src/export_contract.py`, 2026-07-31, librarian session correcting a
stale 1.17.0 figure caught by `tests/test_state_claims.py`; the bump to 1.18.0 is the four
selectable ranking sources change, ADR-068 — see this file's "Last verified" entry above; prior
values in order: 1.17.0 (trace-contract bump, commit `ee5cae2`), 1.15.0 (ADR-062, FR-079/FR-083
league-scoring-aware ADP note + history export fix), 1.13.0 (superseded)).
was **1.14.0** at that session's measurement (2026-07-29 — this line said 1.13.0 until
the claim checker caught the drift; the Build state table below had been right all along; now
1.15.0, see this doc's "Last verified" paragraph above, ADR-061).
The 1.13.0 bump, from the Phase 3 Chain 1 backend session (worktree
`phase3-chain1-adp-and-exports`, thread 074 closed), added: `board.json` top level gained
`snapshot_as_of_date`/`snapshot_age_days`/`snapshot_max_age_days`/`snapshot_stale`/
`snapshot_freshness_note`, the `FreshnessResult` `build_board_json` already computed via
`fr.require_fresh` on every call and previously only printed to the build console. Prior bump,
1.12.0 (ADR-053): `board.json` gained four unconditional suspension fields —
`suspension_flag`/`suspension_games`/`projected_points_suspension_adjusted`/
`suspension_adjustment_note` — real, dated, sourced, currently empty; T4 wired into the live board
via the shared `write_all` path; ADR-051: top-level `scoring_format`, `board_source`/
`consensus_source` now name `fantasypros_csv_2026draft`; ADR-050: `roster_status`, contract 1.10.0.
Primary board and `ethans_expert_league` both rebuilt; the primary now holds **527** QB/RB/WR/TE
(measured from `data/export/board.json`, 2026-07-30 ranker session — was 510 at the 07-27
snapshot); 2026 rookies confirmed
present with real ranks (Jeremiyah Love #33, Carnell Tate #70, Jordyn Tyson #84). Half-PPR yardage
bonuses independently verified to stack against the live Yahoo platform (ADR-052) — see §7 of
`CLAUDE.md`. Handoff threads 069 (scoring_format display) and 073 (suspension fields display) are
**RESOLVED** (frontend chain, branch `frontend/069-073-trace-registry-1-12-0` @ `0da321f`): the
trace registry and `EXPECTED_CONTRACT` were pinned to 1.12.0 there, then re-pinned to **1.13.0**
in this merge session once thread 074 landed on `main` underneath it (`ui/data/contract.ts`,
`ui/data/trace-fields.ts`; the five new snapshot-freshness fields registered in
`BOARD_HEADER_TRACE_FIELDS` and wired into `RefreshData.tsx`, which previously asserted freshness
"is not exported by backend" — false the moment thread 074 landed, now reads the real
`snapshot_age_days`/`snapshot_max_age_days`/`snapshot_stale` values). Thread 074 (T5 freshness
result export to `board.json`) is **RESOLVED** — see this doc's contract-version line above.
`main` and `integration-2026-07-27` diverged independently this round (2 commits vs. 7) and
required a founder-authorized merge rather than the fast-forward the standing runbook expects —
see `docs/handoffs/076-...md` and this session's `docs/status.md` entry for the allocator-race
root cause. Separately, this merge session also caught and fixed a real identity bug unrelated to
either branch: `src/league_config.py`'s `build_current_league()` still hardcoded
`name="Primary league (10-team half-PPR)"` / `platform="other"` — a pre-ADR-052 placeholder that
was never updated once the live platform verification named the real league ("Westwood", Yahoo,
ID 154693). Now `name="Westwood"`, `platform="yahoo"`; `data/export/league.json` regenerated and
re-synced to `frontend/public/data/`.

---

## Build state

Rows below the markers are regenerated by `python tools/state.py --apply` (`--tests` to also run
the suites) — do not hand-edit them; the next `--apply` overwrites whatever's there. The two rows
above the markers aren't measured by a single command, so they stay hand-maintained: edited only
by the session whose work changed them, per the agent operating rules.

| | Value | Notes |
|---|---|---|
| Agent infrastructure | **Live, mailbox check FAILING — deliberately, see Top open items #15** | Seven subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian, pm), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`). `tools/handoffs.py check` (2026-07-29, PM closeout, cloud): **FAILS on two cross-branch ADR collisions only — 90 threads, 49 open / 41 resolved, none stale, all addressed.** Threads 083/084/087 collided the same way and were renumbered to 088/089/090 at this closeout. The earlier 069/073 failure was fixed when the frontend replies landed and `047ff90` corrected thread 080's reply heading. The check still emits ~29 non-fatal contradiction warnings (shared-target antonym pairs, plus five threads citing D-021 as undecided when it is DECIDED) — glance-and-disposition items, not failures. |
| Document-claim detector | **Live, PASSING** (ADR-059, 2026-07-29) | `docs/state-claims.toml` (registry) + `tools/state_claims.py` (checker) + `tests/test_state_claims.py` (21 tests). Fails when one of ten **live** documents asserts something the repo contradicts: existence, a constant quoted in prose, a source/capability status, a count, or two live docs disagreeing. Append-only logs are deliberately out of scope. Caught **eight live false claims** on its first run, all corrected here; proved on six planted faults reproducing the real 2026-07-29 failures, in both directions. **Rule it enforces: a factual claim of those classes in a live document must be registered with its verification.** Known gap, asserted in a test: whether a GitHub Actions *schedule* has fired is not readable from a checkout, so the ADP-capture claim has no registered truth — a single document asserting the false version still passes. `docs/pm/**` is not yet scanned (thread 083). |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |

<!-- BUILD-STATE:START (generated by `python tools/state.py --apply` -- do not hand-edit between these markers) -->

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `worktree-agent-a6aa496d85bd1b2b9`, `4d86a4929cff1663ec490a15cecf0c4291094664` | `git rev-parse --abbrev-ref HEAD` / `HEAD` |
| Data contract | `1.15.0` | `CONTRACT_VERSION` in `src/export_contract.py` |
| Python modules | 45 | `src/*.py`, counted |
| Export artifacts | 11 | top-level files in `data/export/` |
| Config matrix | 26 | dirs under `data/export/` |
| Backend tests | (skipped — pass --tests to run the suite) |  |
| Frontend tests | (skipped — pass --tests to run the suite) |  |

<!-- BUILD-STATE:END -->

## Top open items

Current state only. An item leaves this list when it is done — history lives in ADRs and
`docs/status/`, not here. Verified 2026-07-29 (PM session); every claim below was measured this
pass or is marked as unverified.

**Data capture — time-sensitive, cannot be backfilled**

1. **A *scheduled* ADP capture has still never fired.** `.github/workflows/adp-snapshot.yml`
   (09:15 UTC daily) has exactly one run in repository history, `event: workflow_dispatch`,
   triggered by hand. First scheduled opportunity is **2026-07-30 09:15 UTC**. Check `event:`, never
   the commit author — `github-actions[bot]` authors manual dispatches too, and that is precisely
   how this was got wrong once already. Do not retire the local Windows task until an
   `event: schedule` run succeeds, and do not treat one success as a track record.
   Captured so far: MFL proxy `data/adp-snapshots/` (2026-07-26, -28, -29 — **07-27 UTC is a
   permanent gap**), FFC three-format `data/adp-snapshots-ffc/` (2026-07-29 half/non/full only).
2. **Pick-level ADP velocity is not built.** No longer blocked — FFC is unblocked by the founder
   (FR-023). MFL cannot serve it (`TYPE=adp` is final figures with no pick sequence). Standing
   conditions: private single-user use, one fetch per day per format, and `adp_source` values are
   never blended into one consensus figure.
3. **Mock drafts toward n=30.** Gates the pre-registered availability decision rule. Now 3 of ~30
   logged (330 more picks added 2026-07-30: `yahoo-10team-slot4-2026-07-30`,
   `yahoo-12team-slot2-2026-07-30`, alongside the original `founder-mock-2026-07-29`), but **none
   are usable for the format-gate yet** — all three fail `format_conforms()` (kicker + non-Westwood
   flex/roster shape; the two new ones also carry unconfirmed scoring, see
   `docs/analysis/founder-mocks-2026-07-30.md`). Real per-pick sequence data (team_slot/round/
   overall_pick, snake order verified programmatically) does unblock `live_availability.py`'s
   run-detection prior for the first time, independent of the format gate. Handoff open to
   `strategist` re: scoring-format separability, `docs/handoffs/112-founder-mock-scoring-format-inference-needs-sepa.md`.

**Correctness — the app states something that is not so**

5. **Non-primary leagues are still missing four export artifacts** (data gap, unresolved for
   `player_descriptions.json`/`strategies.json`; **partially resolved for the history pair, see
   below**): `strategies.json`, `player_descriptions.json`, `season_stats.json`,
   `weekly_finishes.json` — primary carries 11, the 26 sub-leagues carry 7 (though as of 2026-07-30,
   measured directly: 17 of those 26 now carry `season_stats.json`/`weekly_finishes.json` too — the
   backend's FR-079/FR-083 history fix exports both per league where it has real data; 9 leagues
   (`ethans_expert_league`, `yahoo_10_full`, `yahoo_standard_mock`, and six 12/14-team Yahoo presets)
   still carry neither, unrelated to this fix).
   **The UI now explains this rather than reading as broken**, fixed 2026-07-29 (frontend,
   `docs/design/TWO-TRACK-EXPRESSION.md`): the league selector carries a PRIMARY/GENERIC track badge
   and a ●/○ marker per option before a league is even selected, and the Strategy guide's old single
   "Not available for this league" string (which conflated "generic track, by design" with "not yet
   run") is split by track. `weekly_finishes.json`/`season_stats.json` are still fetched from a
   genuinely shared, unprefixed path regardless of which league is loaded (`ui/data/playerHistory.ts`)
   — that specific routing gap is still open — but as of 2026-07-30 (frontend) PlayerDetail.tsx at
   least states honestly, from the fetched envelope's own `league_id`, when the history shown is a
   different league's than the one on screen, rather than silently presenting it as a match; see
   `ui/data/types.ts`'s `RawWeeklyFinishes` doc comment.
6. **RESOLVED, 2026-07-30 (frontend).** The player card no longer says archetype does not exist.
   `PlayerDetail.tsx` used to render "Not computed: archetype. No backend field in this build" for
   every player and comment that the field was "permanently absent, no field in any export, ever" —
   true of `board.json`, false of the app's own loaded `player_descriptions.json`. Fixed: a real join
   (`ui/data/archetype.ts`), a chip in the identity strip (the founder's own placement request), and
   four honest states with a live-computed same-label-same-position share stat so the catch-all-
   bucket problem (RB_COMMITTEE 62.7% of RBs, etc.) stays visible rather than hidden. See this file's
   own "Last verified" entry above and `docs/founder-requests/FR-075-*.md`'s Resolution section for
   the full writeup. **Still open, handed to `design`/`ranker`:** the Board-row placement (a second
   placement the founder also named) and the taxonomy revision itself
   (`docs/ranking/archetypes-proposal.md`, thread 099).
7. **Duplicate founder-request ids.** FR-029 and FR-030 each name two different requests, so a
   status update to one is invisible in the other. `tools/dashboard.py` now flags this on every run.
17. **FR-066 (availability picks not changing on slot override) — the founder-visible defect is
    fixed, 2026-07-30 frontend; the browser-side recompute he approved remains blocked, pending
    backend work.** The Availability Explorer (`ui/views/Availability.tsx`) exists, is built, and
    now reads
    `league.pickSequence` for its pick selector instead of `availability.json:metadata.user_picks`
    (FR-034's own seam, previously not wired to this one screen at all — it took no `league` prop),
    and shows a standing banner naming both slots whenever a slot override is active and unrecomputed
    numbers would otherwise read as real. **The real recompute stays blocked**: measured that
    `board.json:consensus_rank` (`fantasypros_csv_2026draft`, per its own `consensus_source_note`)
    and the rank `src/availability.py:simulate_availability` actually runs its opponent model AND the
    user's own BPA pick against (`fantasypros_ecr`, via `draft_sim.load_season()`) are two different,
    both-currently-live rankings — 73 of the top 80 players differ in order between them. The
    frontend has no honest access to the rank the simulation needs, so a client-side port built on
    `board.json:consensus_rank` would silently run a different (wrong) opponent model, not an
    approximation of the real one. `docs/handoffs/NEW-fr066-availability-ranking-source-export.md`
    asks backend for the missing export field or a ruling on which source the model should use.

**Data the model wants and does not have**

8. **T6 full roster-status ingest.** `board.json:roster_status` is a proxy derived from
   `contracts.is_active` (ADR-050), not a real active/IR/practice-squad feed. Needs a
   `roster_status_weekly`-shaped table from `nflreadpy.load_rosters()`.
9. **RESOLVED 2026-07-30 (`data-ops`), partially.** `depth_charts_weekly` (season/week-labelled
   format) genuinely has no 2025 rows because nflverse has not published that format for 2025 --
   NOT an ingestion gap. The dt-timestamped replacement, `depth_charts_snapshots`, already covered
   2025-08-03 through 2026-07-25 before this session and is now refreshed through 2026-07-30
   (939,035 rows). `injuries` still has **zero 2025 rows by design, not by bug**: `load_injuries`
   does return 2025 rows (6,068 of them), but every one has a NULL `date_modified` upstream, and
   `ingest_reference.py` correctly refuses to default the as_of column (`CLAUDE.md` §6.1). **No
   N−1 injury-status feature can be built for a 2026 projection from `injuries` today** — this
   needs a methodology call (season/week as a substitute as_of key?) from backend/statistician,
   not an ingestion fix. `rosters_weekly` was added instead (888,786 rows, 2002-2025, `status`
   includes `RES`/IR and `EXE`/suspended) as the IR/suspension source `component-model-rb-qb-te-
   pass-1.md` §5.2 commissioned — verified earliest valid season is 2002, not 1999 as claimed
   there (nflreadpy raises for 2001 and earlier).
9a. **RESOLVED 2026-07-30 (`data-ops`).** `pbp` table now exists in `nfl.db`: 816,856 rows,
   2009-2025, slimmed to the 24 columns test-registry #10/#18/#21/#22 need (`xpass` included),
   keyed on `(game_id, play_id)`, indexed on `(season, week)`. Measured this session: 36.3 s cold
   fetch (vs ranker's 20.4 s — likely network variance, not a discrepancy in row count or
   columns), ~9.5 s warm (filesystem cache). No `as_of_date` column exists in the source;
   season/week is the real granularity, and a downstream reader must filter on that directly.
   `schedules` also added (7,548 rows, 1999-2026; 2026 has 272 rows, unplayed, `home_score`/
   `away_score`/`result` honestly NULL). Coaching staff and odds are still not ingested — separate,
   unstarted work (§5 sources table, coach identity vs coordinator duty distinction).
10. **RESOLVED 2026-07-30 (`data-ops`), six-loader sweep.** Per
    `docs/research/analyst-factor-sweep-2026-07-30.md` §1, ingested:
    `participation` (`load_participation`, 2016-2025, 478,989 rows — the real source for registry
    #16/#17, mistagged `nflverse:FTN`, which has no per-player columns at all);
    `ff_opportunity` (`load_ff_opportunity`, 2006-2025, 105,905 rows — registry #18 xFP, a free
    prebuilt versioned xgboost model, re-costed H→download; `model_version` requested literal
    recorded per row, source exposes no resolved semver);
    `pfr_advstats_{pass,rush,rec,def}` (`load_pfr_advstats`, 2018-2025, 121,954 rows total —
    registry #23 O-line, routes around the known PFR-scrape 403);
    `contracts` (`load_contracts`, 51,772 rows — registry #27, a **present-day snapshot, not a time
    series**; `is_active` must never be read as historical status, flagged heavily in the ingest
    script's docstring);
    `combine` (`load_combine`, draft classes 2000-2026, 8,968 rows — registry N34, entered with no
    predictive prior per the researcher);
    `trades`/`officials` (4,975 / 21,900 rows, unused project-wide, recorded per instruction).
    None ingested a `season`-typed as_of_date beyond what the source natively carries — see each
    script's docstring for its specific time-key reasoning. `participation`, `ff_opportunity`, and
    all four `pfr_advstats_*` tables carry season 2025 rows (sealed holdout, in-progress); a future
    backtest must not treat them as train/tune input outside pre-registered holdout context.
    `tools/data_freshness_check.py` extended to watch all eight new tables (exit 0 before and
    after). Statistician sign-off on `ff_opportunity` as a ranking input is still a separate,
    unstarted decision — ingestion only here (`CLAUDE.md` §2/§9).
16. **Per-player COMPONENT projections now exist, personal-use only** (2026-07-29, data-ops,
    thread 092, FR-056 — founder ruled "personal use, proceed").
    `src/ingest_sleeper_projections.py` pulls `api.sleeper.com/projections/nfl/2026`
    (`company: rotowire`) for QB/RB/WR/TE into `sleeper_projections` (as_of_date-stamped) and
    `data/projection-snapshots/`. 2007 rows stored (250/538/840/379 by position), 1098 quarantined
    as `no_sleeper_crosswalk_match` (real, all deep bench/UDFA). **Not wired into `board.json` or
    any export, not behind the public site** — Sleeper's ToS forbids redistribution and the app is
    public (thread 092 item 2's public-hosting/FantasyPros/FFC licensing escalation is still open,
    unresolved by this work). Whether these projections improve the ranking model is a separate,
    unregistered question for `ranker`/`strategist`.

**Model**

10a. **The primary evaluation metric cannot distinguish the shipped board from consensus, and this
    is structural** (`ranker` 2026-07-30, `docs/ranking/fr136-q1-bottom-up-assessment.md`, thread
    `2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar` to `strategist`, **BLOCKING**).
    The board's within-position ordering is identical to consensus at all four positions —
    `projected_points` refits to `a + b·ln(positional rank)` with max residual 0.005 pts — so
    `backtest.py`'s per-position τ_b returns **exactly 0.000000** between the board arm and the
    consensus arm, 12 of 12 position-seasons (2022–24). The board's only edge channel is
    cross-positional and ADR-B forbids any cross-position aggregate. Nothing bottom-up should be
    built until `strategist` names a replacement. Board vs consensus is ρ **0.972 across the top
    100**; the whole independent view is a QB/TE tilt (mean signed Δ: QB +5.3, TE +10.6, RB −1.2,
    WR −1.8) generated by four slopes and four replacement levels.
10b. **`CLAUDE.md` §6.5 baseline #1 has never been measured against the shipped board**, and
    baseline #3 has no arm at all. `backtest.standard_arms()` still carries `consensus_adp` as
    `available=False` on ADR-018's reasoning that no ADP source is obtainable — stale since FFC was
    ingested (FR-023). Wiring is small (`adp_baseline` matches **998/998** players to gsis ids,
    2018–24); the result cannot be conclusive — usable seasons are 2022/23/24 only, sign test floors
    at p = 0.25. The shipped `projected_points`' own error is now measured for the first time:
    walk-forward mean MAE **QB 74.0 · RB 62.0 · WR 48.0 · TE 35.8** points, 0.30–0.40 of what the
    average board player scores. That is the bar any bottom-up projection must beat.
10c. **The component models were measured against that bar, same universe, same units — and lose
    at all four positions** (`backend` 2026-07-30, `docs/ranking/component-model-vs-incumbent-headtohead.md`,
    `experiments/bottomup/head_to_head.py`, fr136 §6.2 step 1). Incumbent curve refit onto FFC ADP
    rank (moving it, not the component model, per §6.2) to align universes, 6 walk-forward seasons
    2019–2024, busts retained, 2025 untouched: incumbent MAE QB 75.7 · RB 58.6 · WR 50.5 · TE 39.8
    vs. component MAE QB 85.7 · RB 64.8 · WR 52.2 · TE 44.7 — component worse everywhere. Season-
    block bootstrap: **RB and TE clear 0 in the incumbent's favour** (significant loss); QB and WR
    directionally worse but underpowered at n=6. **Not wired** — `projected_points` is unchanged,
    still `a + b·ln(consensus positional rank)`. Per the mandate's own conditional this is the
    correct action: "a null here is a real result and saves the whole downstream build." Thread
    `2026-07-30-component-model-vs-incumbent-head-to-head-compon` to `ranker`.
11. **Where the TE mispricing sits in the draft is unanswered.** 33.6% of a tight end's stable
    quality is unpriced by consensus versus 15.1% RB/WR and 6.3% QB, but that is pooled across all
    tight ends. If it concentrates in the top few, the founder's late-round strategy is wrong and
    the finding argues the opposite way. Survivorship is the specific way this analysis fails.
12. **The shipped rank curve pools all seasons flat — and measured 2026-07-29, that costs almost
    nothing** (`ranker` pass 3, `docs/ranking/bottom-up-research-pass-3.md`, thread **093** to
    `strategist`, awaiting ruling). The QB slope point estimates reproduce exactly (−66.6, −72.6,
    −58.6, −45.0, −4.1) but **the collapse is not established**: trend +15.3/season [−3.5, +34.1],
    CI spanning zero; 2025's own CI [−46.5, +69.2] contains 2024's estimate; the monotonicity is a
    property of `RELEVANT_DEPTH["QB"]=20` (at depth 12 the series is not monotone and 2021 is the
    flattest season); and dropping one player (Jayden Daniels, consensus QB3) moves 2025 from −4.1
    to **+28.6**. **Other positions checked and the answer is no** — RB's 2025 slope is −77.9, the
    *steepest* of its five; WR is flat; TE is monotone with a magnitude CI spanning zero.
    **The mechanism is market ordering skill, not positional value**: the 2025 realised QB value
    curve is −58.7, flat against era means of −57.7/−59.0/−56.8, while consensus τ_b at QB went
    +0.484 → **−0.042** (worse than random). Ordering skill has **zero measured persistence**
    (lag-1 r = −0.007 [−0.414, +0.411]), so recency-weighting the *consensus* curve would track the
    least persistent quantity in the system. On the *value* curve the answer is position-specific
    (QB strongly yes, hl1 −22.6 [−30.3, −13.6] on a 9-season holdout; RB no; **WR contraindicated**,
    last1 +2.75 [+0.96, +4.80] worse; TE weak) **and at QB it points the opposite way from the fix
    on record** — the QB value curve is steepening, so weighting it recently makes the QB premium
    *larger*. Board cost: `vbd = b·ln(rank/base)` exactly (intercept cancels; verified against the
    live 510-row board, zero ordering mismatches), so the board is four numbers — under half-life 3
    **one** top-150 player moves ≥10 places, under half-life 5 **none**, and every scheme from last3
    down leaves all four slopes inside the board's own published 95% CI. **The board-curve weighting
    question itself is unanswerable on current data: n = 2 evaluable targets, disagreeing at the 4th
    decimal of Kendall τ.** Threads **055**/**084** are what unblock it.
13. **Zero RB is not distinguishable from VBD in this league, and that is measured, not
    underpowered** (2026-07-30, `ranker`, FR-085, `docs/ranking/fr085-zero-rb.md`; rules fixed in
    advance in `fr085-strategy-sim-precommit.md`, commit `a9e3b2b`). Draft simulation, 10 teams,
    this league's roster and scoring, random draft slot, common random numbers, 300 sims per cell,
    paired by season: **P(win title) +0.001 [−0.020, +0.023], P(playoffs) +0.000 [−0.042, +0.041],
    realistic points +0.9 [−19.8, +21.1]** — all NULL, on both market sources (FFC 2018-2024, ECR
    2021-2024), at every opponent-noise level, and at both 16- and 11-round depths. The mechanism:
    **plain VBD in this league already takes its first RB in round 6.3**, so the comparison is
    round 6.3 against round 10.7, not early-RB against late-RB. On the residual side the founder's
    premise is only half supported — in rounds 1-3 the RB shortfall is **not** WR-specific (RB−WR
    −26.6 MARGINAL, RB−TE −28.1 NULL, RB−QB −34.9 SURVIVES) and it vanishes on the expert-consensus
    board over the same seasons (−4.9 NULL); it **is** WR-specific in rounds 4-8 (−27.5 SURVIVES).
    The classic dead zone **RB13-24 is NULL** once matched against the WR band at the same draft
    cost; **RB25-36 is −26.0 [−39.1, −12.5] SURVIVES** and is the best-controlled cell. **The
    founder's recollection that the dead zone "used to be a thing but now is not" is not supported
    and the finding he is remembering is not in this repo** — `docs/test-registry.md:210` test 43 has
    never been run, and the direct 2018-20 vs 2022-24 contrast gives RB13-24 −13.4 NULL (pointing the
    *wrong* way) and RB25-36 +7.5 NULL. What did move is the far end: **RB37+ improved by +48.3
    [+21.6, +75.1] SURVIVES against the WR band drafted alongside it.** So "late-round RB got better
    relative to late-round WR" is supportable; "the dead zone went away" is not, and they imply
    different draft behaviour. 347 interval tests; grades are the correction.
14. **The stacking-bonus ceiling channel is now closed by FOUR independent instruments, including
    the founder's own proposed mechanism, and `CLAUDE.md` §7's operational clause is the open
    question** (2026-07-30, `ranker`, FR-086, `docs/ranking/fr086-volatility.md` §3). The exceedance
    curve at `experiments/bottomup/components/pos_model.py:300` predicts threshold clearance from
    **mean yards per game alone**, so tail shape is inferred from the average and never measured.
    Adding the player's own prior-season **dispersion** (2nd moment) is NULL at every threshold,
    family and shrinkage. Adding **skewness and excess kurtosis** (3rd/4th moments — what the
    founder actually meant by "the curve has a shape with tails"; the first relay of that as
    *dispersion* was a mis-translation and both were tested) is **NULL everywhere and fails twice
    over**: a player's shape residual does not persist year to year (six of six NULL, r = −0.004 to
    +0.071, *weaker* than the 2nd moment's r ≈ 0.08–0.11), and the empirical-Bayes shrinkage
    independently estimates the between-player variance in true skewness at **exactly zero** in 2 of
    5 cells (all 5 under the alternative estimator), collapsing the arm onto the baseline. **Bounded,
    not merely unfound:** with the *target season's own* shape — impossible foresight — log-loss
    improves by at most 0.0024/game-trial and bonus-point MAE gets **worse** at every family.
    Estimator: G1/G2 adjusted Fisher–Pearson, excess kurtosis Fisher convention. Both tests gave
    both arms the **realised** mean, the most favourable setting that exists. The league **does** pay
    for ceiling and the amount is **+0.94 bonus points a season** for a high-volatility WR over a
    low-volatility one at the same scoring level (SURVIVES). Whether §7's second clause should be
    amended is escalated to `strategist`, not decided.
15. **Volatility ranks differently per player than per roster slot, and the per-slot ordering is the
    decision-relevant one** (2026-07-30, `ranker`, FR-086 §1). Per player: WR 1.084 CV, RB 1.047,
    TE 1.002, QB 0.573 — **RB vs WR is a clean NULL**, and the only robust position-level statement
    is that QB is ~45% less volatile than every skill position. Per roster slot, using ADR-029's
    measured flex split and a **measured** same-position weekly correlation of +0.001 to +0.009:
    **TE 1.002, RB 0.600, QB 0.573, WR 0.545** — the ordering inverts, and **the TE slot is the most
    volatile thing on this roster** because it is the one skill slot with no diversification.
    Player-level volatility persists at r ≈ 0.10 against mean PPG's r ≈ 0.72, so **it must not become
    a per-player archetype label**; role-level volatility carries forward at −6% to +6% of SD and
    can. At equal expected points, team variance is worth ~0.5pp of title odds across a 3.3× range —
    the "worse getting in, better once in" story is measured and is not there.

**Known-red, deliberately**

15. **`tools/handoffs.py check` fails on two ADR numbers, and that failure is the record.** ADR-054
    and ADR-055 each carry a second, different definition on the unmerged branch
    `origin/backend/mock-calibration-kickers` ("Batch mock-draft ingestion…" and "Kickers get a
    consensus-only export artifact…"). Both sets are real work. Renumbering belongs to whoever merges
    that branch, knowingly — not to a passing session guessing which wins. Do not silence it.
    `tests/test_handoffs.py::test_mailbox_health` is red for this reason and no other.

**Suspended, not forgotten**

13. **T4 suspension data** — interim closed (ADR-053); `data/suspensions_2026.json` is real, dated
    and currently empty, which is verified rather than an oversight. Thread 057's fuller
    structured-source design stays open if a permanent solution is wanted.
14. **FantasyPros licence** — closed (D-020) while the product stays private and single-user.
    Reopens on any second user, alongside D-021.
