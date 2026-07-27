# Project Status

Running state of the project. Updated at the end of each work session — read this first, then
`decisions.md` (why), `deferred.md` (what's postponed), `data-availability.md` (what's testable),
and `statistical-guardrails.md` (how results must be produced).

---

## Standing requirements

Cross-cutting constraints that must be incorporated into future work, regardless of phase.

- **Bye-week clustering matters for actual roster construction.** A strategy that puts 4 starters
  on the same bye costs real points (6 bench + 1 IR gives some cushion, but not unlimited).
  Incorporate bye-week constraint modeling into draft strategy once rankings are validated.
  Related: test-registry.md Tier 4 #61. 2026 schedule data is already available, so byes are
  known.
- **Two evaluation tracks, never conflated.** ACCURACY = does the model predict outcomes.
  ALPHA = does it beat what the market believed at the time. A model can score well on the first
  and have zero of the second. Alpha claims are bounded by consensus coverage (2021-2025 only);
  accuracy claims are bounded only by each feature's own availability.
- **Consensus data is never a model input.** It is the yardstick for the alpha track. The model is
  built only from pre-draft-knowable raw data.

---

## Objective and deadline

**Objective is ALPHA** — demonstrable edge over market consensus, not merely a well-performing
ranking. **Draft is early September 2026 (~6 weeks from 2026-07-25).**

The draft artifact (`data/board_2026.csv`) is deliberately built to stand alone, so a usable board
exists regardless of whether any modelling work finishes.

---

## Where things stand (2026-07-25, session 4)

| Component | Status |
|---|---|
| Data ingestion | **Full window 1999-2025**, 475,626 player-weeks in `data/nfl.db` |
| League-level metrics | 27 seasons cached (`league_season_metrics`) |
| Consensus rankings | 2021-2026, `ranking_source='expert'` (2,948 rows). **No market ADP exists** |
| Scoring engine | Clamp bug fixed; negative scores now permitted |
| Look-ahead enforcement | `CutoffEnforcedStore`, plus per-module guards in `config.py` and `make_board.py` |
| Backtest harness | **Corrected (Task 9)** — per-position Spearman, season-level bootstrap CIs, seeded, board as primary baseline |
| Regime analysis | `src/regimes.py` — sup-Wald breaks, trend cycles, era similarity |
| Draft board | `data/board_2026.csv` — 378 players, VBD with bootstrap CIs |
| Holdout / pre-registration | **Built (Task 7)** — 2025 locked and enforced, prereg required, BH over the persistent run log |
| Feature pipeline | **Not built** (Task 8) |
| Alpha detection | **Not built** (Task 6) |

**139 automated tests passing.**

### Holdout: 2025 is LOCKED

`src/holdout.py`. Development must use 2021-2024; the board arm additionally cannot use 2021
(no prior consensus season to fit its curve), so the effective development set is
**2022-2024 — three seasons**. Reads of 2025 raise `HoldoutViolation` unless wrapped in a
logged `final_evaluation()` (one-time, per pre-registered test) or `release_for_final_fit()`
(production refit after selection is frozen). Every attempt is appended to
`docs/preregistration/holdout_access_log.jsonl`.

Locking governs **selection, not fitting** — the shipped 2026 model refits on all seasons
including 2025. One held-out season is N=1 and cannot confirm an edge; use
`walk_forward_splits()` during development.

---

## Session 4 findings that change how the project must work

**1. A six-season hole in the historical data that passes every naive check.** `targets` and
`receiving_air_yards` are 100% non-null back to 1999 but are *zeros* for 2003-2008 (season sums of
3 / 5 / 0 / 67 / 14 / 17 vs ~17,000 in working years). Receiver identification in PBP is unreliable
in that window. Any feature built on targets must **refuse** those seasons, never zero-fill.
Full map in `docs/data-availability.md`.

**2. "27 seasons of data" is true only for outcomes.** Opportunity metrics are far shallower:
air-yards family 2009+, snap counts 2013+, NGS 2016+, PFR 2018+, FTN 2022+ (4 seasons), PROE 2006+.
Depth charts **end at 2024**, so no depth-chart feature is available for the 2026 draft at all.

**3. The alpha track has an effective sample of 5 seasons.** August preseason consensus snapshots
exist only for 2021-2025. This bounds everything: per-regime alpha coefficients are not estimable,
season-level bootstrap resamples 5 units, and a holdout leaves 4 development seasons.
**The most likely honest outcome of the alpha work is "no significant alpha detected."**

**4. An estimator choice reversed a headline result.** The first draft board used isotonic
regression and put a QB at overall #1. That was an artifact of imposing monotonicity on 5
observations per rank — the raw data has consensus QB10 outscoring consensus QB1 in 2 of 5 seasons.
The replacement log-linear estimator reverses the positional ordering (RB1 168.5 > WR1 153.2 >
QB1 114.1 > TE1 73.1). See `decisions.md` ADR-016.

**5. Consensus draft rank explains under a third of outcome variance.** Curve-fit R² is 0.158-0.266
by position, residual SD 46-91 points. This is the honest size of the signal the market itself
carries, and it sets the bar: any alpha claim has to beat a predictor this weak, on 5 seasons of
data. It also means most board rows are not distinguishable from their neighbours — hence bootstrap
CIs on every row.

**6. League structure is moving, and two trends are actionable.** From `src/regimes.py`:
plays per game has two structural breaks (after 2011, after 2019) and is in an *accelerating*
decline (-1.08 plays/season in the current regime) — the 2025 figure is the lowest in 27 seasons.
RB carry concentration broke after 2019 and **reversed direction**: it declined 1999-2019
(committee-ization) but has risen since 2020 (+0.014/season, p=0.019). Pass rate rose for two
decades but has plateaued over the last five years. Most recent break across all metrics is after
2019, which is the recommended pooling boundary for player-level factor models.

---

## Session 5 findings (Tasks 9 and 7)

**1. The evaluation metrics were blind to the primary baseline.** The corrected harness
returned a delta of *exactly zero* between the re-scored board and raw consensus on every
metric. Structural, not a bug: the board only reorders across positions, while `vbd_sum`
(top-N per position) and within-position Spearman are both invariant to that. Added
`starter_vbd`, which imposes a 15-pick budget and fills the lineup, making cross-position
ordering matter. Two tests now lock in that the two metrics are complementary.

**2. ~~The board's advantage over consensus does not survive the holdout.~~ CORRECTED — see
ADR-025.** The advantage is **directionally positive in 3 of 4 seasons, mean +84.6**, and is
simply *not statistically established at n=4*. It never reversed. Original text below, kept
for the record: Including 2025,
`starter_vbd` delta was **+84.6 [+2.3, +153.0]** — excluding zero, and reportable as a win.
On development seasons only the interval widens to include zero — no demonstrated difference.
**(CORRECTED 2026-07-25: an earlier version of this line said the sign flipped to −84.9. It
does not. That figure was quoted in the opposite sign convention; the board is better by ~85
points in both runs, and only the interval changes. See ADR-025.)** Had the holdout not been locked first, the first number would have
been written down as a finding. This is the single best argument for the Task 7 ordering.

**3. Three existing tests were silently evaluating on 2025.** They failed the moment the lock
landed. That is the leak the lock exists to catch, and it was already present in code written
one session earlier by someone who knew the rule.

**4. Cross-source dispersion was being discarded at ingestion.** `rankings` kept only `ecr`
and dropped `sd`/`best`/`worst`. Now stored. Without it, `P(player survives to pick 23)` —
the core VONA quantity — is permanently unrecoverable for any date already passed.

## 2026-07-25 — #38 FALSIFIED (PR-002): the primary claimed edge does not exist

**Bonus-threshold "spike-week-ness" is not a persistent player trait.** Volume-adjusted YoY
residual correlation: WR receiving-100 **r = +0.041** [-0.018, +0.099]; RB rushing-100
**r = +0.063** [-0.001, +0.124]. 36 correlations run, **zero survived Benjamini-Hochberg**.
Largest sample in the project (26 seasons, 1,541 WR pairs). Full detail in
`docs/preregistration/PR-002-spike-week-persistence.md` and test-registry #38.

This was pre-registered before running, with the null criteria and the regime-reversal
disqualifier fixed in advance — which mattered: QB passing-300 hit r = +0.265 (p = 0.002) in
2012–2019 and **reversed to −0.234** in 2020–2024. Examined alone it would have been a finding.

**What it means practically:** bonus clearance carries no information beyond projected
yardage. Project the yards; the bonuses follow mechanically. There is no spike-week player to
identify, and strategy premised on ceiling-shape at equal projected volume has no basis.

**What survives:** re-scoring under our exact rules, and corrected replacement levels
(RB28/WR41/TE11/QB10 vs published RB24/WR36). Both real, both modest — and per ADR-016 the
board's positional re-weighting is **directionally positive (mean +84.6, 3 of 4 seasons) but
not statistically established at n=4** (corrected 2026-07-25, ADR-025 — an earlier version of
this line said "no demonstrated advantage", which understated it). The league-specific edge is
thinner than the project assumed, but the board itself has never measured worse than consensus.

## 2026-07-25 — Draft simulator built (P3-4); #44 resolved NULL

`src/draft_sim.py` + `src/run_draft_sim.py`. 10-team snake, slot 3, picks 3/18/23/38/43
(verified), 16 rounds, legal-roster enforcement, weekly-optimal lineup scoring against actual
outcomes, opponents drafting to consensus with tunable Gaussian noise plus positional need.
**43,200 simulated drafts** across 6 strategies × 4 seasons × 3 sigma settings, seeded.

**#44 Hero RB: NULL.** −13.3 pts vs BPA (sigma=10), CI [−98.1, +65.0], 2 of 4 seasons positive,
sign p = 1.000 at every sigma. Per-season margins swing +93 to −133 — noise.

**BPA is hard to beat, as anticipated.** Zero of 15 comparisons survived BH. That was
predictable and stated up front: with 4 development seasons the exact sign test's **floor is
p = 0.125**, so nothing can reach significance at the season level no matter how many drafts
are simulated. Simulation SE is ~8 points against season swings of ±100 — **more simulations
would not narrow a single conclusion here; only more seasons would.**

**The one consistent signal: reaching early for TE or QB costs 3–5% of roster points.**
`elite_te_early` −96.1 ± 6 (restated from −92.9 per ADR-028 — unstable seed, not a model change)
and `qb_early` −115.4, both negative in **12 of 12** season×sigma cells.
Not significant (it cannot be), but perfectly consistent, large, and stable across the whole
opponent-noise sweep. Corroborated by #45 (−226.4) and ADR-016 slot values.

This also **corrected an inference I had made earlier the same day**: reasoning from slot values
that "TE-before-QB was backwards" implied QB-early was preferable. Measured directly, `qb_early`
is the *worst* arm. Slot value and reach cost are different quantities — QBs cluster, so waiting
recovers most of the QB1 value while the spent pick does not come back.

Now unblocked by the simulator: #45, the TE/QB timing question, #68 positional runs.

## 2026-07-25 — ALPHA TRACK CLOSED for 2026 (ADR-026)

**No alpha-detection work will be attempted this cycle.** This is arithmetic, not pessimism.

Consensus coverage is 2021–2025; one season is the locked holdout, leaving **4** for
development (**3** for board-dependent arms). At that size the exact two-sided sign test's
smallest attainable p is **0.125 at n=4** and **0.250 at n=3** — both above 0.05 *before* any
multiple-comparisons correction, and the run log already stands at 51 tests. **No factor can
reach significance regardless of its true merit.**

Three independent results have now each hit this same wall: PR-002 (36 correlations, zero
surviving BH), PR-003 (15 comparisons, floor p=0.125), and the ADR-025 per-season breakdown
(3/4 seasons positive, p=0.625). The data runs out before the question does.

**Reopens at n ≥ 6 development seasons** (floor 0.031) — on current accrual, **2028**. More
consensus *sources* would not help; the binding constraint is seasons. `src/alpha.py` is not
built. **PR-001 is marked FROZEN-FOR-FUTURE**, not pending, so a later session does not
relitigate a structurally closed question.

The **ACCURACY track is unaffected** and remains the whole game: it reaches back as far as each
feature allows (PR-002 used 26 seasons). Availability distributions, startability, bottom-up
projection and the simulator are all accuracy-track.

## 2026-07-25 — CORRECTION: the board never "flipped sign" (ADR-025)

Per-season `starter_vbd`, re-scored board minus raw consensus:

| Season | Board | Consensus | Delta | |
|---|---|---|---|---|
| 2022 | 1001.8 | 825.8 | **+176.0** | dev |
| 2023 | 626.1 | 660.8 | **−34.7** | dev |
| 2024 | 673.9 | 560.5 | **+113.4** | dev |
| 2025 | 693.1 | 609.3 | **+83.8** | HOLDOUT |

Development mean **+84.9**, sign test 2/3 positive, p=1.000, power floor 0.250.
Including holdout **+84.6**, 3/4 positive, p=0.625, floor 0.125.

**An earlier session reported that the board's advantage "flips sign" from +84.6 to −84.9 when
the holdout is removed. That was my error** — the two figures were quoted in opposite sign
conventions (the harness reports `arm − primary`, so −84.9 was *consensus minus board*). Both
say the board is better by ~85 points. Only the interval changes: three seasons instead of four
widens it from excluding zero to including it.

Corrected claim: **holdout discipline showed the advantage is not statistically established on
development data alone — not that it reverses.** The per-season view, which the pooled figure
was hiding, makes this obvious.

## DEFERRED: player identity resolution (was Task B, 2026-07-25)

**Deferred by decision, not forgotten.** It gates the feature pipeline (Task 8) but the draft
simulator does not depend on it, and the simulator is the critical path.

The problem it addresses is real and now measured (`data-availability.md` §8.2): `gsis_id` is
62.1% populated in the crosswalk with 10 known collisions, and the `pfr_player_id → gsis_id`
leg that snap-share features depend on resolves 77–78% overall (92–95% restricted to
QB/RB/WR/TE). Until a resolution layer exists, **any cross-source feature must state its
coverage and refuse unresolved rows rather than dropping them** — the drops are non-random,
skewing toward fringe roster spots where role changes actually happen.

Scope when resumed: ID space per table, a resolution table with explicit confidence, explicit
collision handling, and a measured coverage report per source pair.

## Prior results still marked PROVISIONAL

Tests #44/#45/#46 (session 3) predate `statistical-guardrails.md` and do not meet it. #46 has now
been materially **revised** — its original figure conditioned on actual finish rather than draft
slot, which understated QB value (see test-registry.md). The remaining gaps for all three:
per-position rank correlation, bootstrap CIs, and a consensus baseline are Task 9.

---

## Next steps

Tasks 9 and 7 are done. Remaining, in order:

1. **Task 8 — feature pipeline** (`src/features.py`). Each feature takes an explicit
   `cutoff_date`, declares its first-available season from `data-availability.md`, **refuses**
   seasons where its inputs are known-broken (the 2003-2008 targets hole) rather than
   zero-filling, and is covered by a test proving identical output when handed data extending
   past the cutoff. Imputation choices go in feature metadata with a paired sensitivity check.
2. **Task 6 — alpha detection** (`src/alpha.py`), last because it depends on 8. The control on
   consensus rank must be FLEXIBLE (log-rank or spline), with reported sensitivity to that
   choice: points-vs-rank is strongly convex, and a linear control leaves curvature in the
   residual that any quality-correlated factor will absorb and be mislabelled CANDIDATE_ALPHA.
   Cluster SEs by player. Label every factor PRICED_IN / CANDIDATE_ALPHA / ACCURACY_ONLY.
3. **Re-pull the 2026 board in late August** once FantasyPros publishes preseason-final
   snapshots. The current board is flagged `is_preseason_final=0` and will move.

Standing expectation, unchanged: the development set is **three seasons**, ~14 factors will be
tested under FDR, and **"no significant alpha detected" is the likely and acceptable outcome.**
Do not tune toward finding something.

---

# SESSION HANDOFF — 2026-07-25 (end of session)

Read this first in a fresh session, then `decisions.md` for the reasoning.

## Standing constraints (unchanged)

- **2025 is the locked holdout.** `src/holdout.py` enforces it; reads raise outside a logged
  context.
- **Alpha detection is CLOSED for 2026** (ADR-026). 4 development seasons floor the exact sign
  test at p=0.125, above 0.05 before any FDR correction. Reopens at n≥6 seasons (~2028).
  PR-001 is FROZEN-FOR-FUTURE — do not run it.
- **Seeded RNG, and prove it.** Never derive a seed from builtin `hash()` (ADR-028). Use
  `config.stable_offset`. A static test enforces this.
- **Every simulation-derived point estimate needs a seed-noise band.** See "Not yet done".

## State: 191 tests passing, contract v1.3.0, everything committed

| Area | Status |
|---|---|
| Data | 1999–2025 weekly stats, 11 reference tables, consensus 2021–2026 — all ingested |
| Scoring | Clamp removed; negatives permitted |
| Board | `data/export/board.json`, 378 players, regenerated at new replacement levels |
| Availability | `data/availability_2026.csv` + summary; seed-audited, bands measured |
| Simulator | `src/draft_sim.py`, reproducible after ADR-028 |
| Narration | `src/narrate.py` layer 1 (Facts). Renderer NOT built — contract in ADR-027 |
| Front-end contract | 7 artifacts in `data/export/`, documented in `data-contract.md` |

## Decisions made this session

- **ADR-028** — the −92.9/−98.6 discrepancy was `abs(hash(name)) % 1000`, a per-process salted
  hash. Both figures were valid draws from a ±6 band. **Canonical value is −96.1** and two
  separate processes now reproduce it byte-identically. No conclusion moved; `seasons_positive`
  is 0/4 at every seed. Also fixed two instances in `backtest.py`.
- **ADR-029** — replacement levels **RB28/WR41/TE11 → RB30/WR40/TE10**, from measurement, not
  assumption. Adopted **for consistency with measurement, not as an improvement**: RB flex
  ranges 5–17 (sd 3.0) and the answer moves ±1 by window. TE10 is the robust part (zero flex
  slots in every window).
- **ADR-030** — falling-TE claim **refused on a code read**. `elite_te_early` already
  value-conditions (45-rank subsidy), so the fall cases are inside the −96.1. Pre-registration
  void, no measurement, no FDR spend. `+18` tier-1 TE weight stays out of the recommendation
  engine.
- **ADR-031** — FTN cannot answer alignment. It is play-level with **no player identifier at
  all**. Structural absence, not a sample limit.
- **ADR-032** — play-callers parked; `(team, season, start_week, end_week)` schema fixed now so
  mid-season handoffs (Cleveland 2025) cannot be ingested wrong.

## Decided this session but NOT yet in an ADR — write these up

1. **Prior-year behaviour is demoted to display-only.** The `repeat_2025 / half_repeat /
   no_repeat` switch is to be deleted; it no longer selects between models. The 60/13/0 TE
   table is circular — its entire spread came from assuming two managers repeat. **Still
   present in `availability.py` and the exports.** Needs: removal, an ADR, and a recomputation
   of P(tier-1 TE at 23) under the new model with the delta against 60/13/0 reported.
2. **New availability model** — ranking mixture per manager, mechanical roster need, rank noise.
   Ranking sources as a **posterior marginalised over**, never hard-assigned, never argmax.
   Expect no separation before R4; if it never separates, that is the finding.
3. **MFL ADP** as `adp_source='mfl_proxy'` — partially supersedes ADR-018. Joins natively on
   `mfl_id`. Never present as this league's ADP.
4. **Identity hub is `mfl_id`, not `gsis_id`** (62% populated, known collisions). Collisions go
   to a table and are EXCLUDED; `resolve()` returns None, never guesses.
5. **Profiles are display-only**, test-enforced never to reach board/backtest/scoring/Facts.
6. **Draft state records all teams**, not just the user's; `team_slot` derived from snake order.

## Mid-flight / not done

- **1b — noise bands into docs.** `nulls.json`, test-registry, status and PR-003 still cite
  −92.9/−98.6. Canonical is **−96.1 ± 6**. Availability bands measured and tight
  (±1–4 points); **`TE T1 @23` should read 0.60 ± 0.02, not 0.59** — the only quoted figure
  that fell outside its band.
- **FantasyPros probe** — key is in `.env` (gitignored, verified). Probe schema BEFORE building:
  component projections or ranks only? That is the difference between unblocking
  test-registry #2 and not. If current-year only, it is an ACCURACY_INPUT, not a measured
  improvement.
- **Not started:** Task B identity resolution, feature pipeline, client-side simulator,
  query engine, Blocks 3/4/5 (startability, expanded strategies, PDF guide).

## Traps a fresh session will otherwise walk into

- **`evaluative_adjustment` is 0 and `evaluative_adjustment_available` is false.** The board
  holds no player-level opinion (ADR-017) — every player at the same positional rank gets an
  identical projection. Do not build a "we disagree with the experts" view; it has no data.
- **145 of 378 players have a displayable projection.** The rest are outside the fitted curve
  depth and carry `projection_within_fitted_range: false`. Do not render a number for them.
- **7 of 9 opponents have no data.** Slots are derived from supplied pick numbers; everything
  else is null. No pick citations exist — none were invented.
- **A front-end session is live against `data/export/`.** Do not change a schema without
  bumping the contract version.
- **Availability figures are circular right now** — they assume the prior-year repeat. See
  item 1 above.

---

# SESSION HANDOFF — 2026-07-25 (session 8, end)

Short session, ended on a rate limit. Doc/contract reconciliation and backlog ADRs only — **no
modelling work, no new features started.** Read this, then `decisions.md` ADR-033 to ADR-040.

## State: 202 tests passing, contract v1.5.0, all committed

Interpreter note, because it cost time this session: **`python` and `py` on PATH are broken
Windows Store stubs.** The project's interpreter is
`C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe`. There is no venv in the repo.

## Done this session

| Item | Result |
|---|---|
| **`league.json` invalid JSON** | **FIXED** (ADR-040). Bare `Infinity` -> `null` ceiling + `points_allowed_note`. All three exporters now write `allow_nan=False`; a test parses every artifact with `parse_constant` set to raise |
| **DEF** | **SETTLED** (ADR-039). Permanently excluded. `positions_without_replacement_levels: ["DEF"]` added; `def_supported` stays false. DST ingestion is NOT planned |
| **1b — stale numbers** | **DONE.** `-92.9` -> **`-96.1 ± 6`** in `nulls.json`, test-registry #313, PR-003 (3 sites + a restatement note), status.md:177 |
| **Six backlog ADRs** | **LOGGED** as ADR-033 to ADR-038. Plus ADR-039 (DEF) and ADR-040 (strict JSON) |
| **Stale replacement-level prose** | **SWEPT.** `league.json.replacement_levels_note`, `glossary.json`, `make_board.py:310`, test-registry #34, data-contract.md all said RB28/WR41/TE11. The **values** were correct since 1.3.0 — only the prose was stale |
| **`flex_split_note`** | **CORRECTED.** Said "an explicit tunable assumption, not a measurement"; ADR-029 measured it over 26 seasons |
| Front-end session | Notified that the `Infinity` sanitiser in `scripts/sync-exports.mjs` is now dead code |

Contract went **1.3.0 -> 1.4.0** (JSON bug fix) **-> 1.5.0** (DEF field, flex_split + nulls.json
prose). `board.json` and `availability.json` regenerated **byte-identically** at 1.4.0 — the
ADR-028 reproducibility fix holds across processes. No values moved this session.

## Two corrections to the previous handoff

1. **`.env` DOES NOT EXIST.** The session-7 handoff said the FantasyPros key "is in `.env`
   (gitignored, verified)". There is no `.env` file, no `dotenv` in `requirements.txt`, and no
   `os.environ` call anywhere in `src/`. **The FantasyPros probe cannot start until a key is
   actually supplied.** Treat the prior line as false.
2. **`TE T1 @23` needed no fix.** The handoff flagged it as reading 0.59 instead of 0.60 ± 0.02.
   Nothing in this repo quotes 0.59 — the exports carry the raw 0.5963, which rounds to 0.60.
   The stale 0.59 was in the external design handoff, not here. No change made; nothing to chase.

## Post-handoff addendum — contract 1.5.1

`league.json` was the only artifact shipping without `generated_utc`, through five contract
versions, so the front end's provenance line fell back to `league@unversioned`. Added, contract
bumped to **1.5.1**, and a test now asserts every artifact carries both `contract_version` and
`generated_utc` — which is what `data-contract.md`'s opening line has always claimed. **209 tests.**

Front end is synced and committed at `7276a2d` on `frontend-prep`. Its sanitiser is gone,
replaced by validation only: a strict `JSON.parse` plus a token scan that fails `npm run dev`
with the file, line, token and a pointer to `allow_nan=False`. That is a contract check rather
than a workaround, and it stays.

Two things that session did which this side should not undo:
- It reads `positions_without_replacement_levels` from config rather than special-casing DEF, so
  if DEF ever leaves that list the UI follows without a code change.
- `ui/__tests__/out-of-scope.test.ts` fails if any app file dereferences `player.availability`,
  `te_scenarios`, `by_tier` or `sigma_*`. Until ADR-033 is implemented, that test is the only
  thing preventing the circular availability figures from reaching a reader.

## Mid-flight — ONE item, and it is trivial

- **`strategies.json` is at `contract_version: 1.4.0`; the other six artifacts are at 1.5.0.**
  It regenerated successfully (43,200 sims) but the process had imported `CONTRACT_VERSION`
  before the 1.5.0 bump, so it stamped the older value. **Nothing else about it is stale** — it
  carries the correct `-96.1`, and 1.5.0 changed no field this artifact contains (the 1.5.0
  changes were all in `league.json` and `nulls.json`).
  **To close it, one command, no side effects:** `python src/export_strategies.py` (~13 min).
  The front-end session is aware and flags it as behind-expected rather than assuming stale.

  **Worth recording — this run independently confirmed ADR-028.** The regenerated file differs
  from the previous one in `contract_version` and `generated_utc` **and nothing else**: all
  43,200 simulated drafts across 6 strategies x 4 seasons x 3 sigmas reproduced byte-identically
  in a separate process. That is the property `stable_offset()` was introduced to guarantee, now
  demonstrated rather than asserted — which is exactly the standard ADR-028 said the old
  "seeded RNG, seed recorded" claim failed to meet.

## Still open — nothing below was started

Priority order unchanged from session 7, except that the six ADRs are now written up.

1. **ADR-033 implementation — prior-year demotion.** The decision is logged; **the code is not
   changed.** `availability.py` still has the `repeat_2025 / half_repeat / no_repeat` switch and
   `availability.json` still ships `te_scenarios` (0.60 / 0.13 / 0.00). **The shipped availability
   figures remain circular** — their entire spread comes from assuming two managers repeat their
   2025 TE picks. Requires recomputing P(tier-1 TE at 23) under ADR-034 and reporting the delta
   against 60/13/0.
2. **ADR-034 — new availability model + client-side simulator.** Not started. Supersedes the
   precomputed-draws export.
3. **ADR-036 / Task B — `mfl_id` identity hub.** Not started. Gates the feature pipeline.
4. **ADR-035 — MFL ADP.** Not started. Does **not** reopen the alpha track (ADR-026 closed it on
   seasons, not sources).
5. **ADR-037 profiles, ADR-038 all-teams draft state.** Not started.
6. **FantasyPros probe.** Blocked on a key existing at all — see correction 1.
7. **Feature pipeline (Task 8), query engine, Blocks 3/4/5.** Not started.
8. **Re-pull the 2026 board in late August** when FantasyPros publishes preseason-final. Current
   board is `is_preseason_final=0` and will move.

## Traps (carried forward, all still live)

- **`evaluative_adjustment` is 0 / unavailable.** The board holds no player-level opinion
  (ADR-017). Do not build a "we disagree with the experts" view.
- **145 of 378 players have a displayable projection.** The rest carry
  `projection_within_fitted_range: false`. Do not render a number for them.
- **7 of 9 opponents have no data.** No pick citations exist; none were invented.
- **Availability figures are circular** until ADR-033 is implemented.
- **A front-end session is live against `data/export/`.** Do not change a schema without bumping
  the contract version.
- **New:** do not "fix" the missing DEF replacement level by deriving DEF10. It *is* derivable
  from league structure alone, and it is withheld deliberately — see ADR-039.

---

# SESSION HANDOFF -- 2026-07-26 (session 10, stopped mid-plan, token-limit-driven)

Four-item plan from the user: (1) FantasyPros probe, (2) consensus-rank-mismatch diagnosis,
(3) multi-league support, (4) player descriptions. **Items 1-2 done (prior message in this
session). Items 3's two sub-items (implement + Yahoo mock test) done. Item 3's third sub-item
(mock draft logging) NOT STARTED. Item 4 (player descriptions) NOT STARTED.** Stopped here
deliberately rather than starting either of the two remaining pieces without room to finish them
cleanly.

## What's done and committed: ADR-041, multi-league support

`src/league_config.py` (new), `src/draft_sim.py` (DraftEngine added, nothing existing touched),
`src/scoring.py` (`ReplacementLevels.from_league_config`), `src/availability.py` (optional
`engine` param), `src/make_board.py` (`scoring_cfg` param -- a real gap, fixed), `src/
export_contract.py`/`src/export_static.py`/`src/run_availability.py` (all take `--league`,
route to `data/export/<league_id>/` for non-primary leagues, primary stays unprefixed).

**Verified, not assumed:** every rewrite was diffed against the previously-committed primary
league output before moving to the next file. Zero numeric values changed for the primary
league at any point -- only additive fields and a couple of explicitly-noted prose
genericizations. Full detail, including the two real gaps found (make_board.py's missing
scoring_cfg, run_availability.py's hardcoded pick numbers) and the gaps deliberately NOT fixed
(backtest.py's separate constants, no kicker engine, RELEVANT_DEPTH, MAX_AT_POSITION/flex_split
heuristics for new leagues) is in **ADR-041**, decisions.md.

**Contract bumped 1.6.0 -> 1.7.0.** 288 tests passing (23 new: test_league_config.py,
test_draft_engine.py, test_multi_league_export.py).

**Yahoo-standard 12-team mock league built and proven**
(`data/leagues/yahoo_standard_mock.json`, exports at `data/export/yahoo_standard_mock/`) --
values are placeholders, the user said they'll correct them from a real lobby later. Full
regeneration (~47s) produced a correct, structurally valid 6-file export set.

## NOT done from the 4-item plan

- **Mock draft logging (item 3's third sub-item).** Schema not built:
  `mock_drafts(mock_id, league_config_id, platform, drafted_at, source, is_mock)` /
  `mock_picks(mock_id, overall_pick, round, team_slot, mfl_id, player_name_raw)`, resolved
  through the ADR-036 identity hub, unresolved names to a quarantine table. Primary consumer per
  the user's brief: validating the availability model (predicted vs. observed availability by
  position/tier with CIs -- will be underpowered at first, say so). Secondary: an ADP proxy,
  always `is_mock`, never blended into real ADP. Explicitly NOT an opponent-behavior signal.
  No ADR logged for this -- nothing was built.
- **Player descriptions (item 4).** `archetype_taxonomy.md` was supplied by the user
  (RB/WR/TE closed enums, `UNDETERMINED` fallback, evaluation order specified, thresholds
  explicitly flagged as unverified conventions -- read and understood this session, not yet
  implemented). Depends on Task B (mfl_id hub, already built, ADR-036) and the taxonomy file
  itself. Nothing built: no archetype assignment code, no description generation, no
  `license_tag='ai_generated'` enforcement test. No ADR logged.

## Front-end notification: NOT YET SENT this round

The user asked to notify the front-end session of the new directory convention once item 1
landed. **This has not been sent yet** -- do this first thing next session if it wasn't sent
before the process ended. Content: primary league unchanged at `data/export/`; a league switcher
can target `data/export/<league_id>/` for any other league using the exact same file names/
schema; `league_id` is now present on every artifact as a cross-check.

## Traps for a fresh session

- **`data/leagues/*.json` is tracked in git, not gitignored** -- it's config, not generated
  output. Treat it like source, not like `data/export/`.
- **`DraftEngine` is deliberately a duplicate of the free functions in `draft_sim.py`, not a
  refactor of them.** Do not "clean this up" by merging them -- that was a considered and
  rejected design, specifically to protect PR-003's ADR-028-verified reproducibility guarantee.
- **`nulls.json` for a non-primary league is NOT a bug when it shows `NOT_YET_RUN_FOR_THIS_
  LEAGUE`.** That is correct behavior, not a missing implementation -- see ADR-041's
  league-invariance section.
- **Only ADR-026 (alpha-detection closure) is confirmed to travel across leagues.** Every other
  finding, including the ones in `nulls.json`, is league-specific until proven otherwise.

---

# SESSION HANDOFF -- 2026-07-26 (session 10, item 3 continued, stopping now per token-limit warning)

## What's done and committed this round: ADR-042, mock draft logging

`src/ingest_mock_drafts.py` -- file-based ingestion matching the front end's exact schema
(mock_drafts/mock_picks), plus mock_pick_quarantine (ours). Name resolution via new
`identity.resolve_name()` (public, promoted from a private helper). Format-mismatch gate
implemented; bot-seat gate NOT implementable from this schema, flagged `bot_seat_status='unknown'`
per mock rather than silently passed.

`src/mock_validation_report.py` -- Levels 1 (positional depletion) and 2 (3-bucket per-player
calibration) of `mock_validation_protocol.md`, built and tested against both a zero-mock state
(current reality -- reports "no measurement", not a fabricated number) and a seeded non-zero
case (verifies the counting logic itself). Reuses the shipped `data/availability_2026.csv` for
predictions rather than re-simulating.

**26 new tests. 316 passing project-wide.** Full detail in ADR-042, decisions.md.

## NOT done -- explicit scope cuts, not oversights

- **Tertiary (dispersion vs. sigma schedule) -- NOT built.** The protocol calls this "the
  highest-value output of the whole exercise." Real, well-specified, cut for time.
- **Brier score vs. rank-logistic baseline (protocol SS1, the actual pass/fail criterion) --
  NOT built.**
- **Bot-seat gate is permanently unenforceable as currently specced.** Raise with whoever owns
  the front end's mock-draft export next: either the mock tool can report per-seat human/bot
  status and it should be added to the schema, or it can't and this gate never runs. Not decided
  here.
- **Item 4 (player descriptions) -- not started, as instructed.** `archetype_taxonomy.md` was
  read and understood this session (closed RB/WR/TE enums, UNDETERMINED fallback, evaluation
  order specified, thresholds flagged as unverified conventions). Nothing implemented against it.

## Where a fresh session picks up

1. If continuing item 3: `mock_validation_report.py` needs a `level3_dispersion_report()`
   (observed SD of depletion counts per pick/position vs. the sigma schedule's implied SD --
   the `best_available_dist` p10/p90 spread already in the CSV is the relevant input) and a
   `brier_vs_baseline()` (fit `P(survive) = sigmoid(a + b*(pick - consensus_rank))` on
   conforming-mock outcomes, compare Brier score against the shipped model's predictions).
2. If starting item 4: read `archetype_taxonomy.md` (path was `C:\Users\matth\Downloads\
   archetype_taxonomy.md` this session -- confirm it's still there or ask for it again), start
   from the identity hub (ADR-036, already built) to resolve which players get which archetype.
3. **No uncommitted work.** Working tree is clean at the end of this message.

---

# SESSION HANDOFF -- 2026-07-26 (session 10, closing)

**Correction to the previous entry in this file:** it ended "No uncommitted work. Working tree
is clean at the end of this message." That was true when written, but two more work items
landed in this same session afterward (mock-validation gaps, player descriptions) before this
close-out. Read this entry as the current one; the "no uncommitted work" line above it describes
a mid-session checkpoint, not the session's actual end state.

## What landed this session (full arc, in order)

1. **FantasyPros probe (reported, nothing built against it).** Component projections are real
   and carry `mflid` for a direct identity-hub join, but the free tier caps every response at 10
   players with no working pagination -- cannot reach the 233 players who actually need
   coverage. ADP is a genuinely separate dataset from ECR but comes from only 3 sources.
2. **Consensus-rank mismatch diagnosed, not fixed.** The DynastyProcess mirror `ingest_rankings.py`
   pulls from has no PPR-specific variant at all -- one unparameterized snapshot. The live API
   supports `scoring=HALF` directly. Format and coverage are two separate blockers; only a paid
   tier resolves both.
3. **Multi-league support (ADR-041).** `league_config.py` (`LeagueConfig`, versioned) +
   `draft_sim.DraftEngine` (a parallel implementation of the module's free functions, not a
   refactor -- protects PR-003's ADR-028-verified reproducibility). Exports route to
   `data/export/<league_id>/` for any non-primary league; the primary league's path is
   unchanged. A 12-team Yahoo-standard mock league was built and run end-to-end, surfacing two
   real gaps (both fixed): `make_board.py` had no `scoring_cfg` param at all, and
   `run_availability.py`'s summary hardcoded pick numbers `(18, 23)`. Contract bumped
   1.6.0 -> 1.7.0.
4. **Mock draft logging (ADR-042) + the bot-seat schema decision (ADR-043).** File-based
   ingestion matching the front end's exact schema; name resolution through the identity hub,
   quarantine on anything unresolved or ambiguous. The validation report's four pieces are all
   built: Level 1 (depletion), Level 2 (3-bucket calibration), Level 3/Tertiary (dispersion vs.
   the sigma schedule's implied SD -- a fresh simulation, not an approximation), and the
   Brier-vs-rank-logistic-baseline test (the protocol's actual pass/fail gate). `drafter_type`
   added as an optional per-pick field so the bot-seat gate is checkable; absent -> the whole
   mock is flagged `bot_seat_status='unknown'`, included with a caveat, never silently passed or
   excluded.
5. **Player descriptions (ADR-044).** `archetypes.py` assigns RB/WR/TE archetypes exactly per
   `archetype_taxonomy.md` -- t-1 labels, 2013 data floor, rookies UNDETERMINED by construction,
   RB_HANDCUFF explicitly not implemented (needs a depth chart). `player_descriptions.py`
   generates deterministic, template-based descriptions (never a live LLM call --
   `license_tag='ai_generated'` describes the content's nature, not the generation mechanism).
   UNDETERMINED produces no description, enforced by tests against a live DB run, not just
   fixtures. Display-only separation is enforced by a static-scan test (same pattern as
   ADR-028's `hash()` ban): `player_descriptions`/`archetypes` must never appear in
   `narrate.py`/`scoring.py`/`make_board.py`/`backtest.py`/`candidate_rankings.py`/
   `draft_sim.py`/`availability.py`. Ships as a standalone `data/export/player_descriptions.json`,
   deliberately outside `CONTRACT_VERSION`. **Live finding:** the taxonomy's own stated risk
   (thresholds landing "mid-mass") is real -- Keenan Allen's actual 2025 season falls through
   every WR criterion and lands UNDETERMINED. Pinned as a regression test, not patched around.

## State

**Contract version: 1.7.0** (unchanged by items 4-5 -- neither touches `CONTRACT_VERSION`;
`player_descriptions.json` carries its own separate `export_version`).

**368 tests passing**, confirmed by a fresh full-suite run at session close (341s). Test suite
runtime is up from ~1.3 min to ~5.7 min this session, almost entirely from
`archetypes`/`player_descriptions`'s DB-backed tests each independently recomputing
`assign_for_season()` for ~500 players (15-60s per test, not cached). Worth a session-scoped
pytest fixture if this becomes a recurring pain point -- `conftest.py` already has the pattern
(the holdout-audit-log redirect fixture).

**Commits this session, in order:** `9d5e0e9` (multi-league core) -> `459ab56` (multi-league
export wiring + Yahoo mock) -> `733f969` (mock draft logging) -> `fa56716` (dispersion/Brier/
bot-seat gate) -> **[this commit]** (player descriptions). Earlier in the session, before the
multi-league work: `3ea587f` and several before it (contract-version stamp fix, availability
model rewrite, identity hub, MFL ADP -- see prior handoff entries above this one in the file for
full detail on those).

## Next steps, priority order

1. **RB_HANDCUFF.** Needs a preseason depth-chart join plus "is the rank-1 teammate BELL_COW"
   logic. The taxonomy itself flags this as the one label needing data not validatable on any
   development season -- real, scoped-out work, not forgotten.
2. **Threshold verification for the archetype taxonomy.** The brief says outright it has not
   measured whether its thresholds land in distribution valleys or mid-mass. The Keenan Allen
   case is concrete evidence this isn't hypothetical. Plotting the actual usage-share
   distributions per position and checking threshold placement is the next real methodology
   task here -- Statistician-tier work per CLAUDE.md SS9, not an implementation task.
3. **Mock draft data collection.** Every number in the validation report (Levels 1-3, Brier) is
   correctly reporting "no measurement" because zero mocks are logged. The report exists and
   works; it needs actual mock drafts run through it to produce anything. This is the highest
   real-world-value next step if the September draft timeline matters.
4. **FantasyPros paid tier** -- a pricing/budget decision for the user, not an engineering task.
   Free tier's 10-player cap makes test-registry #2 unreachable at the free tier regardless of
   what else changes.
5. **`ingest_rankings.py`'s format fix** -- switch to the live FantasyPros API with
   `scoring=HALF` for the ranking snapshot itself (separate from the paid-tier question, which
   is about projection *coverage*, not this).
6. **`backtest.py`'s own separate hardcoded roster constants** -- pre-existing duplication of
   `draft_sim.py`'s (not introduced this session). Re-running the accuracy-track backtest harness
   per league is materially bigger scope than the export-pipeline work already done.

## Traps for a fresh session

- **`DraftEngine` (draft_sim.py) is a deliberate duplicate of the module's free functions, not a
  refactor of them.** Do not "clean this up" by merging them -- protecting PR-003's
  ADR-028-verified byte-identical reproducibility was the explicit reason for the duplication.
- **`nulls.json` for a non-primary league correctly shows `NOT_YET_RUN_FOR_THIS_LEAGUE`.** That
  is not a missing implementation.
- **Only ADR-026 (alpha-detection closure) is confirmed to travel across leagues.** Every other
  finding is league-specific until proven otherwise, including everything in `nulls.json`.
- **The mock-validation report's bot-seat gate needs `drafter_type` supplied by the front end to
  do anything.** Absent it, every mock is `bot_seat_status='unknown'` -- correctly included with
  a caveat, not a bug.
- **`player_descriptions.json` is NOT part of the main contract.** It has no `CONTRACT_VERSION`
  field and is not written by `export_contract.py`. Do not wire it in without a deliberate
  decision -- the separation is what makes "never a model input" actually true rather than a
  convention someone could forget.
- **A player absent from `player_descriptions.json` has an UNDETERMINED archetype.** Do not
  treat a missing player as a bug or backfill a placeholder description for them.
- **A front-end session is live against `data/export/`.** Do not change a schema without
  bumping `CONTRACT_VERSION` and notifying that session.

---

# SESSION HANDOFF -- 2026-07-26 (session 11)

Four items from the user, all done this session: (0) SS5(a) lambda measurement run first, as
instructed, (1) live-availability adjustment (2) N_t(p) wired into the recommendation engine
(3) multi-config board/VBD matrix. Full detail in ADR-045/046/047, decisions.md. **399 tests
passing** (368 at session start + 31 new: 8 lambda_estimation + 13 live_availability + 4
strategy_balanced + 6 generate_config_matrix), contract version unchanged at **1.7.0** (nothing
this session touched the front-end contract's shape, only board-instance count and
simulated-strategy values).

## What landed, in order

1. **Real 2025 league draft ingested** (`data/real_drafts/2025_league_draft.json`, committed) --
   the user supplied it as 6 screenshots, reconstructed into the `mock_drafts`/`mock_picks` JSON
   shape, ingested via `ingest_mock_drafts.py` with `is_mock=0`. 145/160 picks resolved; 15
   quarantined correctly (9 DEF -- no identity to resolve, per ADR-039 -- plus 5 name collisions/1
   nickname mismatch). This is the project's first non-zero mock-validation data point ever.
2. **ADR-045 -- live-availability adjustment.** `src/live_availability.py` (hazard model) +
   `src/lambda_estimation.py` (SS5(a) measurement, run FIRST per instruction). Real result:
   `lambda_hat=0.352` (not the 0.5 prior), `se_clustered=0.070`, `z=5.04`, n=160/10 clusters --
   adopted as `DEFAULT_LAMBDA`, explicitly flagged as a small-cluster, one-season estimate, not a
   settled measurement. `delta=0.10` ships unvalidated (SS5(b) needs per-pick mock state logging,
   out of scope this session by instruction). Checks #1 and #7b written first, then #2-#9, all
   passed on first implementation. 21 new tests.
3. **ADR-046 -- N_t(p) wired into `draft_sim.strategy_balanced`,** replacing the flat "-8.0 if
   unfilled starter" step function. Changes the `balanced` strategy's behavior for the WHOLE
   draft, not just early rounds. `NEED_ADJUSTMENT_SCALE=10.0` is an explicit, unmeasured constant
   (same posture as `NEED_PENALTY_PER_SURPLUS`). **`strategies.json` regenerated this session** to
   pick up the changed `balanced` arm -- see below for the refreshed numbers. 4 new tests.
4. **ADR-047 -- multi-config board/VBD matrix,** 24 configs (8/10/12/14 teams x
   standard/half/full PPR x ESPN-default/Yahoo-default roster shape), board+league only, no
   availability sim, no strategies. Platform defaults arrived mid-session from the user's
   researcher pass (ESPN roster verified, scoring not; Yahoo fully verified, FLEX is RB/WR only
   -- confirmed distinct from ESPN's RB/WR/TE flex). NFL.com and Sleeper deliberately excluded
   (NFL.com's W/R-only flex is a third shape, not a variant; Sleeper has nothing confirmed).
   Scoring axis varies reception value only; bonuses/TD/INT held at the project's existing
   ruleset throughout (which happens to match ESPN's confirmed bonus tiers exactly). 6 new tests.

## Numbers that moved

- **`draft_sim.NEED_TARGETS`/`MAX_AT_POSITION` unchanged** -- ADR-046 only touches
  `strategy_balanced`, not the opponent model (`opponent_pick`) or any other strategy.
- **`strategies.json`'s `balanced` arm** -- regenerated this session (`generated_utc:
  2026-07-26T17:56:30Z`). New margins vs. `bpa_consensus`: sigma=5 **+18.0**, sigma=10 **+27.5**,
  sigma=20 **+13.2** (previously a flat, non-significant **+17** at sigma=10 that "swung both ways
  across seasons" -- the new numbers are directionally similar in size but were not re-verified
  against a season-by-season sign check this session; do that before quoting the new verdict text
  in anything user-facing). Still not statistically significant at n=4 (`power_floor` unchanged),
  same as every other strategy comparison in this project.
- **`live_availability.DEFAULT_LAMBDA = 0.352`**, superseding the spec's 0.5 prior, per its own
  SS5(a) decision rule.

## Not done -- explicit scope cuts, not oversights

- **SS5(b) run-detection validation.** Needs mock drafts with per-pick draft state logged, which
  does not exist. Explicitly out of scope this session per instruction -- do not add per-pick
  state logging without a separate decision, since the mock schema is otherwise fixed to what the
  front end exports (ADR-042).
- **`NEED_ADJUSTMENT_SCALE` calibration.** Unmeasured; a real calibration needs a swept-scale
  comparison against `bpa_consensus` via the existing simulator. Not attempted.
- **NFL.com and Sleeper roster shapes.** Deferred, not guessed. NFL.com needs its W/R-only flex
  modeled as a genuinely distinct shape (not RB/WR/TE with a name change); Sleeper needs an actual
  platform-confirmed source before anything is built.
- **Yahoo/ESPN scoring bonus structures.** Not incorporated into the matrix -- only PPR value
  varies; a platform-accurate bonus axis needs a verified source for each platform (ESPN's fetch
  was blocked by bot detection; Yahoo's bonus tiers were never checked at all, only its PPR value).
- **check #3 empirical validation against the shipped Prep-mode marginal.** Cannot currently be
  done -- `availability_2026.csv` only tracks the top ~80 players individually; the rest of the
  undrafted pool is tier-level only, so the full-pool hazard sum can't be reconstructed from the
  shipped artifact. Synthetic self-consistency tests cover the math instead.

## Traps for a fresh session

- **`live_availability.POSITIONS` includes DEF; `draft_sim.POSITIONS` does not.** These are
  deliberately different axes for deliberately different reasons (DEF has no scoring engine so
  `draft_sim` auto-fills it via reserved rounds, but DEF is a real, contested pick competing for
  opponents' attention, so the live-availability need model must include it). Do not try to
  unify them.
- **`lambda_estimation.py` reads `data/real_drafts/2025_league_draft.json` directly, never
  `mock_picks`.** The mock table has no `position` column and can't resolve DEF identity at all --
  reading through it would silently lose exactly the positions SS2's near-hard-cap claim rests on.
- **24 new `LeagueConfig`s live flat in `data/leagues/`, same convention as `yahoo_standard_mock`.**
  They are synthetic exploration configs, not real leagues the user is in -- do not mistake one for
  a real, drafted league when reasoning about `nulls.json`'s `NOT_YET_RUN_FOR_THIS_LEAGUE` state.
- **None of the 24 matrix configs have `nulls.json` findings or `strategies.json` at all** -- this
  is correct, not a missing implementation; both are out of scope for this "board-only" pass.
- Carried forward, still live: `RB_HANDCUFF` not implemented, archetype thresholds unverified
  against real distributions, mock draft data collection now has exactly ONE real data point (not
  zero, but nowhere near the ~30-mock decision-useful threshold), FantasyPros paid tier is a
  budget decision for the user.

---

# SESSION HANDOFF -- 2026-07-26 (sprint 1 closeout)

Closed out sprint 1 housekeeping that the prior bootstrap session (threads 008/010) left
incomplete: temp files (`docs/CLAUDE-md-append.md`, `docs/data-ops-agent-definition.md`,
`docs/handoffs/handoffs.py`, `docs/handoffs/sprint_status.py`, `docs/agent-definitions/`) were
never deleted after their real destinations (`CLAUDE.md`, `.claude/agents/data-ops.md`,
`tools/handoffs.py`, `tools/sprint_status.py`) were already committed in `b4093d8`/`88dea17`.
Diffed each stale copy against its tracked counterpart before deleting -- all identical, no
content lost. `docs/agent-definitions/PERMISSIONS.md` moved to `docs/PERMISSIONS.md` per thread
014's instruction rather than deleted with the rest.

Found and fixed a real bug while running the suite for the closeout: `tests/test_handoffs.py`
hardcoded `"py"` as the interpreter, which is a broken Windows Store alias stub on this machine
(see memory `python-interpreter.md`) -- the mailbox health test was failing for an environment
reason unrelated to mailbox health. Fixed to `sys.executable`. **400 tests passing** (399 + this
fix, suite ~5.5 min).

Threads 008, 010, 013, 014, 015 marked `RESOLVED` in their frontmatter -- they had reply text
claiming completion but the `STATUS:` field itself was never updated, so `OPEN.md` kept listing
them as waiting on backend. `tools/handoffs.py sync` + `check` both clean: 32 threads, 27 open,
none stale, all addressed.

Noticed threads 025-030 now exist (mock lab backend, recompute streaming, opponents/predictions
tabs, frequency array, why-rank-differs) that were not present at session start -- looks like
another session is writing to this same mailbox concurrently. Left untouched; out of scope for
this session's assignment (016-024).

Proceeding to work threads 016-024 per dispatch instructions: three concurrent max, 018 before
019, 018 and 023 not concurrent (both touch `ingest_rankings.py`).

---

# SESSION HANDOFF -- 2026-07-26 (strategist, thread 034: shortcut bias in mock logging)

Ruled on and specified the measurement-validity problem Design raised and declined to recommend on:
the Mock Lab entry screen makes the hazard model's own top five the cheapest thing to record.
Deliverable is `docs/adr-drafts/ADR-D-mock-logging-instrumentation.md`, same pattern as ADR-A/B/C.
No database access used and none needed -- this is a design ruling, Backend implements.

**Ruling.** Option (b) instrumentation adopted; option (a) rejected; option (c) rejected as a
hypothesis test and adopted as the carrier of the headline number. Two mechanisms not in the brief
carry most of the actual protection.

- The framing that decided it: this is a **feedback loop between the estimator and its own data
  collection**, not a tiredness problem. Design praised one direction of the loop ("better
  calibration means the top five covers more picks, so logging gets faster"); it is a single arrow,
  and read the other way it says cheaper logging makes the model look better calibrated. The error
  is *differential* -- correlated with the quantity estimated -- so it biases toward the claim and
  cannot be bounded from the contaminated data. Ordinary logging slips are non-differential,
  attenuate toward chance, and are safe.
- **There is no ground truth.** No independent record of the real pick sequence exists. So every
  option aimed at *detecting* the substitution rate is unwinnable; the winnable problem is making
  the estimate immune.
- **Refused, in writing:** the shortcut-vs-typed calibration comparison thread 034 proposed. A pick
  is shortcut-entered *because* the model was right and typed *because* it was wrong -- entry mode
  is a deterministic function of the outcome. Contamination and selection are perfectly collinear;
  the test has no identifying variation and would return a large significant number meaning nothing.
  Same class as `_rank_correlation` pooling positions.
- **Power arithmetic for the blind arm, on the record:** resampling unit is the mock.
  `MDE = 2.802·sigma·sqrt(1/k + 1/(n-k))`. Detecting contamination at the level that matters (~3
  points) needs ~90-350 mocks depending on an unobserved between-mock sigma, best guess ~170.
  Against a target of 30 that is not collectable and never will be. Registered anyway (PR-006 /
  PR-007) *specifically so its null cannot later be quoted as reassurance* -- the inconclusive
  branch and its consequences are pre-committed, and the phrase "no evidence of contamination" is
  forbidden in artifacts.

**What changes in the build (all must exist before the first logged pick):** entry shortlist is the
top five by frozen board rank with no probabilities shown; hazard output still computed and stored
write-once, just not displayed; seeded block-randomised blind arm, 1 per block of 3, k=10 of 30,
assigned at mock creation before any pick; ~14 new columns (`entry_mode`, `shortlist_shown`,
`shortlist_source`, `predictions_visible`, `dwell_ms` from a monotonic clock, `keystrokes`,
`predicted_top5`, `model_artifact_hash`, a co-measured model-free baseline, and mock-level arm /
`session_index` / `logged_live` fields).

**Two findings not asked for:**
1. **The paste-mode matcher is an unflagged contamination path.** Its natural implementation breaks
   fuzzy-match ties by "which candidate is more likely picked here," which would make calibration
   data literally generated by the model being calibrated -- silently, on the mode the spec calls
   the marketed path. Hard rule + static import test. Free now, unrecoverable after 30 mocks.
2. **The shipped evidence ladder overstates precision.** `MOCK-LAB-SPEC.md` §5 uses a Wilson
   half-width, which assumes independent trials; picks within a mock are not independent. Design
   effect 1.6-2.6x, so the honest figure at 30 mocks is **±8 to ±10 points, not ±6**.

Also proposed a small extension to ADR-C: a `blinded_nuisance: true` amendment qualifier, defined
mechanically as "uses only statistics invariant to permutation of the contrast label," so that
replacing an assumed variance with a measured one is not punished by the `data_seen` demotion rule.

Not escalated -- a methods question, decided. One future founder call has a pre-committed trigger
(after 6 mocks, if board-rank coverage trails the hazard model's counterfactual coverage by >10
points, raise it with the measured minutes-per-mock cost attached). `D-018` and `D-019` added to
`decisions-needed.md`, both `DEFAULTED`. Thread 034 `RESOLVED`; `OPEN.md` hand-edited (no Bash
access to run `tools/handoffs.py sync` -- next session with Bash should re-run it to confirm).

---

# SESSION HANDOFF -- 2026-07-26 (researcher, thread 009: source-availability audit for FR-001)

Audit only, as scoped -- no feature design, no UI. Deliverable is
`docs/research/source-audit-2026-07.md`: 17 rows, every cell tagged
`[VERIFIED]`/`[SNIPPET]`/`[SECONDARY]`/`[GAP]`, with *fetching* and *displaying* answered
separately for every source because they diverge on almost all of them.

## Sample quality, stated before the result

Fifteen nominal sources are **five legal regimes**. The subscription-analyst class (PFF, 4for4,
FootballGuys, ETR, Fantasy Life) is one decision unit, not five -- all paywalled, all bar
reproduction of their output, none with a self-serve API -- and they agree for a structural reason
(their product *is* the rankings), not by coincidence. The two sources that came out cleanest are
the two the project already uses, which is selection rather than evidence that the field is
permissive.

## Viable today -- three

1. **nflverse (`nflverse-data`)** -- CC-BY-4.0, the only source in the audit that affirmatively
   permits display with attribution. `injuries` release verified live (assets from 2009, release
   updated 2026-03-18); `schedules` updated the day of the audit. No rankings, no ADP, no takes.
2. **MFL ADP** -- free, documented, no login, already ingested. Weakness is sample (n=50 drafts),
   not law. Display permission is `[GAP]` -- unprohibited is not permitted.
3. **FantasyPros ECR** -- DynastyProcess mirror verified alive (FP scrape 2026-07-24), so fetching
   is settled and displaying is not: a mirror cannot convey rights its operator never held.

## Five changes since the last audit; two change what is possible

- **FantasyPros now sells tiered API licences.** Free = non-production/sample data; Premium
  $8.99/mo = personal & non-commercial; **Commercial = redistribution rights + historical/bulk,
  price not public.** Different object from D-000, which priced the site subscription. New entry
  **D-020** in `decisions-needed.md`; `CURRENT-STATE.md` top-open-item 4 rewritten in place.
- **NFL Fantasy is shutting down; ESPN is the NFL's official fantasy game from this season**
  (ESPN Press Room, 2026-07-16). NFL.com data now inherits Disney's ToU -- the most restrictive in
  the audit. Two candidates collapsed into one hard block.
- **Thread 005's stated reason for not scraping FantasyPros does not survive checking.** Their
  Terms of Use contain no anti-automation clause (checked all 32 sections). The binding clause is
  *"not to sell, resell, reproduce, duplicate, copy or use for any commercial purposes."* The
  conclusion holds; the risk moves from the fetch to the screen, which is the worse half for FR-001.
  **Do not misread this as licence to scrape.**
- **Yahoo moved** (`developer.yahoo.com/fantasysports/guide/` -> 308 -> `sports.yahoo.com/developer`)
  and `football.fantasysports.yahoo.com/robots.txt` now blocks `ClaudeBot`, `Claude-Web` and
  `anthropic-ai` by name. OAuth API remains sanctioned but its ToU carries a 24-hour data-deletion
  rule and a no-competing-product clause; Yahoo ships a draft assistant.
- **Two corrections to our own record:** FFC's block is narrower than we state (only `/adp/csv/` is
  robots-disallowed; the HTML ADP pages are not) so the blocker is purely an unretrievable ToS; and
  a **CBS ADP page exists that no prior audit catalogued** -- server-rendered, 140+ players, avg
  pick + hi/lo + percent drafted, not robots-disallowed -- which fails anyway on a 2005 ToS clause
  forbidding copying or storing any part of the Service. Recorded as checked-and-rejected so it is
  not rediscovered.

## For Data Ops, incidentally

MFL's API notes say "Don't retry failed requests"; `src/ingest_mfl_adp.py` retries on 429 with
backoff -- considerate in spirit, contrary in letter. MFL also grants ~2.5x higher rate limits to
clients that register a User-Agent, and we have not registered. Free headroom, unclaimed. Not my
thread to open.

## The half of FR-001 that cannot be built

**No audited source grants a licence to display third-party prose takes.** RotoWire, ETR, 4for4,
FootballGuys, PFF and ESPN each prohibit reproduction in writing. Substitutes: headline + link +
attribution via RSS (customary, not a licence -- RotoWire's feed is verified live and carries "All
rights reserved"), and nflverse injury designations, which are facts not takes. Third-party takes
on a screen is a licensing purchase, not an engineering task.

## Blocked and stopped, not routed around

ESPN, Underdog, PFF, FootballGuys, ETR, Fantasy Life (robots), Yahoo's public web ADP page
(robots), CBS (ToS), FFC (ToS unretrievable -> conservative default). Specific clause for each in
§6 of the artifact. No data page behind any of these was fetched. Open gaps are enumerated in §7
and are not to be filled by inference.

**No Bash access this session** -- `OPEN.md` hand-edited to mirror `tools/handoffs.py sync` output
(thread 009 moved to Resolved, researcher inbox now empty, counts 28 open / 8 resolved), and
**nothing was committed.** The next session with a shell should run `python tools/handoffs.py sync`
and commit `docs/research/source-audit-2026-07.md`,
`docs/handoffs/009-research-aggregation-audit.md`, `docs/handoffs/OPEN.md`,
`docs/decisions-needed.md`, `docs/founder-requests.md`, `docs/CURRENT-STATE.md`, `docs/status.md`.

## 2026-07-26 — data-ops: FantasyPros backfill (018) + injury as_of_date ingestion (024)

Two threads closed this session, both mechanical ingestion work per operating-model tier.

**Thread 018 (FantasyPros preseason backfill).** `src/ingest_rankings.py` already looped over
seasons (default `range(2021, 2027)`) from a prior session; ran it fresh and confirmed 2021-2025
each carry real rows (519/504/485/558/474). The `scoring=HALF` half of the ask was investigated,
not implemented: the DynastyProcess mirror this file reads has no half-PPR variant of the overall
board at all (checked `page_type`/`fp_page` values directly), and FantasyPros' live API -- which
does support `scoring=HALF` -- caps every free-tier response at 10 players regardless of position
filter (re-confirmed live: `count=209` for RB, 10 rows returned). Switching would trade the scoring
fix for a ~90% coverage loss (~40 players/season vs ~500), which would silently break every
downstream RB30/WR40-cutoff consumer. Declined the swap, documented the finding in the module
docstring and the handoff reply, and left it for pm/backend as a licensing-tier decision (it lands
in the same bucket as the FantasyPros API licence question D-020 already tracked in
CURRENT-STATE item 4).

**Thread 024 (injury as_of_date).** Found `src/ingest_reference.py` was already pulling
`load_injuries(seasons=True)` into an `injuries` table (90,752 raw rows) with an `as_of_column`
field on its `SourceSpec` that was declared but never actually enforced -- no row was rejected for
a missing date, and the DB column had no `NOT NULL`. Rather than build a second, competing
`injuries` table, fixed the shared pipeline: `prepare()` now drops any row with a null
`as_of_column` value (reported, not silent), and `build_create_table_sql()` now emits `NOT NULL`
on that column so a direct bypass-insert is also refused at the DB level. This fix applies to both
tables that declare `as_of_column` (`injuries` -> `date_modified`, `depth_charts_snapshots` ->
`dt`); re-ran `depth_charts_snapshots` afterward and confirmed zero regression (0 rows dropped,
its `dt` was already fully populated).

Re-ran the injuries pull end to end: 79,816 of 90,752 rows kept. 2009 nearly entirely rejected
(17 of 4,821 -- source has almost no `date_modified` that year), 2010 lost 62 rows, 2011-2024 fully
dated, **2025 dropped in full** -- nflverse has not published a `date_modified` column for the
current season yet, so the season the ask named ("2009-2025") isn't actually available with a real
date today. Verified post-write: zero rows anywhere lack `date_modified`.

**Rows ingested:** rankings 2,540 (5 seasons) + injuries 79,816 (15 seasons, 2010-2024) = 82,356.
**Rows quarantined/dropped:** injuries 10,934 for missing `as_of_date` + 2 duplicate-key; rankings
0 beyond the pre-existing gsis_id-join drop.
**Sources attempted:** DynastyProcess ECR mirror (used, unchanged), FantasyPros live API (probed
only, not adopted -- free-tier row cap), nflverse `load_injuries` (used).
**Tests:** 15 new (`tests/test_ingest_rankings.py` x7, `tests/test_ingest_reference.py` x8). Full
suite: 422 passed, 1 pre-existing unrelated failure (`test_mailbox_health`, threads 031/036 from a
concurrent agent's session).
**Commit:** see this session's commit hash in git log for
`src/ingest_rankings.py`, `src/ingest_reference.py`, `tests/test_ingest_rankings.py`,
`tests/test_ingest_reference.py`, `docs/handoffs/018-fantasypros-season-backfill.md`,
`docs/handoffs/024-injury-ingestion-as-of-date.md`, `docs/handoffs/OPEN.md`.

Both threads set `STATUS: RESOLVED` (018, 024) and synced via `python tools/handoffs.py sync`.
No founder statements surfaced this session -- `docs/founder-requests.md` untouched.

## 2026-07-27 — frontend: display-repair diagnosis (thread 038/041), Opponents wiring verified, mailbox duplicate-ID fix

**Task:** thread 038 (pm) said "the app does not currently display," cut mid-change at a usage
stop after the WIP commit `09391e4`. Told explicitly not to assume the contract-version mismatch
was the cause -- diagnose first.

**Actual diagnosis: no display failure found.** Started `npm run dev` (via `.claude/launch.json`'s
"prep" config), navigated the running app, read the DOM (`get_page_text`/`read_page`) and console.
Board renders all 378 players with real data; Opponents renders 9 opponent cards with honest
partial/not-supplied/empty-roster states; zero console errors; `npm run build` (tsc + vite) clean;
`npm test` 116/116 green. The WIP commit already contained working code -- `EXPECTED_CONTRACT` was
already bumped to `1.8.0` in `frontend/ui/data/contract.ts`, matching `board.json` and five other
top-level export artifacts, and the Opponents/`rosters.json` wiring (thread 038's ask) was complete
and tested, not half-wired. What was actually missing was verification: the WIP commit's own message
said "no screenshot was captured this session," and the PM's "does not display" appears to have been
a cautious inference from that gap, not an observed failure.

**Could not capture a pixel screenshot this session** -- `computer{action:"screenshot"}` failed
repeatedly with "the Browser pane is not displayed, so the page is not compositing frames" across a
fresh tab, a resize, and a restarted preview. This reads as an environment/session limitation (no
visible pane to composite into in this run), not an app failure -- `get_page_text`/`read_page`/
`read_console_messages` all executed successfully against the live DOM and returned full, correct
content. Reported honestly as unverified-by-screenshot rather than claimed done; flagged to the user.

**One real, smaller issue found:** `data/export/strategies.json` is stale at `contract_version:
1.7.0` while every other artifact is `1.8.0` -- `CONTRACT_VERSION` in `src/export_contract.py` is
correctly `1.8.0` and `export_strategies.py` uses it correctly; the file on disk just hasn't been
regenerated since before the bump (last regen at `030742d`, predates it). The app's refresh banner
correctly and honestly flags this drift already -- that's the "no invented numbers" design working
as intended, not a bug. Didn't run `export_strategies.py` myself (it guards on
`DEFAULT_LOCK`/`DEV_SEASONS`, backend's statistical-guardrail territory, not frontend's to invoke).
Opened thread 042 to backend instead.

**Mailbox hygiene, found while re-running the full backend suite:** `test_mailbox_health` was still
failing on a **second**, previously-undiscovered duplicate ID -- `038-frontend-wip-repair.md` (this
thread, untracked) collided with the pre-existing, already-committed `038-rosters-json-artifact.md`
(backend, thread 016's notification). Renumbered mine to `041` (same fix pattern as the earlier
036->039 renumbering), replied to and resolved `038-rosters-json-artifact.md` since its ask (verify
the Opponents wiring against the `rosters.json` shape) was exactly what I'd just confirmed working.
Also found the *actual* root cause of the still-failing `036` duplicate the prior session had
flagged but not fixed: the 036->039 rename in an earlier frontend session had copied content to
`039-weekly-finishes-and-season-stats-exports-contract.md` but never deleted the original
`036-weekly-finishes-and-season-stats-exports-contrac.md` (note the filename typo -- singular
"contrac"). Removed the leftover. `tools/handoffs.py check` now passes clean (42 threads, none
stale, all addressed) and **the backend suite's long-standing 1 pre-existing failure is gone**:
423 passed, 0 failed (was 422 passed, 1 failed).

**Uncommitted tree, resolved file by file** (all present at session start, cut mid-change by the
prior session's usage stop):
- `docs/CURRENT-STATE.md`, `docs/handoffs/022-test-suite-speedup.md`,
  `docs/handoffs/031-frontend-spec-audit-and-wiring.md`, `tests/test_multi_league_export.py`,
  staged deletion of `docs/handoffs/031-ADDENDUM-audit-additions.md` -- all legitimate backend-
  session work. Confirmed the addendum's content was preserved verbatim in the 031 file before
  letting the deletion ride (diffed the two directly, byte-for-byte match). Re-ran the modified test
  file (14/14 pass) and the full suite before committing any of it.
- Untracked `docs/handoffs/039-weekly-finishes-and-season-stats-exports-contract.md` -- already
  carries a correct, complete frontend reply from a prior session (`BLOCKED-ON-YOU`, unfilled
  template flagged back to backend). Committed as-is, no further action needed.
- Untracked `docs/SNAPSHOT-2026-07-27.md` -- a dated, self-labeled "raw, verbatim outputs, no
  analysis" diagnostic capture, evidently written just ahead of the prior session's usage stop.
  Read in full; content corroborates (didn't contradict) everything I independently re-verified.
  Kept and committed as a point-in-time snapshot, same category as `dashboard.html` -- not treated
  as live/canonical, CURRENT-STATE.md remains the canonical source.
- Also updated `CURRENT-STATE.md` further myself: test counts (423/0 backend, 116/15 frontend),
  moved the Opponents tab and league-rosters-export from "not built" to "built and working" now
  that both are verified live and tested, replaced the stale "full league rosters endpoint" top-open-
  item with the real remaining gap (`strategies.json` re-export, thread 042).

**Frontend tests:** 116 passed (15 files) -- unchanged from before this session, no regression.
**Backend tests:** 423 passed, 0 failed (was 422/1) -- net improvement, mailbox duplicate-ID bug
fixed as a side effect of hygiene cleanup, not the session's main task.

**Screenshot:** attempted repeatedly, blocked by an environment limitation (browser pane not
compositing in this session), not an app defect. DOM/console/build/test evidence all consistent with
a correctly rendering app. Told the user this plainly rather than asserting a screenshot exists.

No founder statements surfaced this session -- `docs/founder-requests.md` untouched.

## 2026-07-26 -- backend: thread 037 item 2 (duplicate thread IDs, mailbox check)

Worked item 2 only of `docs/handoffs/037-audit-followups.md` (pm-raised, backend+frontend).
Verified rather than trusted the prior-session summary: `python tools/handoffs.py check` exits 0
clean (42 threads); `pytest tests/test_handoffs.py -v` and the full suite both green, 423
passed/0 failed.

Determined which hypothesis explained the undetected `036` duplicate ID: neither "check never ran"
nor "check ran but didn't fire" was fully right. `tests/test_handoffs.py` hardcoded the `py`
launcher (broken Windows Store stub on this machine) from creation (`b4093d8`) until `6feece2`
fixed it to `sys.executable` -- so the test failed for an unrelated reason for a stretch, but that
was fixed *before* the `036` duplicate was introduced (`ee30e6f`). The duplicate-detection logic in
`cmd_check` was present and correct throughout. So `check` did run and did fire (422/1), but that
failing state was committed anyway inside a WIP checkpoint (`09391e4`) instead of being fixed
pre-commit -- a process gap, not a tooling gap. Fixed in `4928a24` (prior frontend session, already
on disk before this session started).

Proved `check` still catches duplicates: copied an existing thread file to a scratch duplicate ID,
ran `check` (exit 1, named both files), deleted the scratch file, re-ran `check` (exit 0 clean). No
scratch artifacts left behind.

Filled in thread 039's `Ask`/`Why`/`Done looks like` -- they were still the unfilled
`handoffs.py new` template (frontend had correctly refused to guess and set
`STATUS: BLOCKED-ON-YOU`). Spec: `weekly_finishes.json` + `season_stats.json` exports from
`player_weekly_stats`, field shapes matching `api-contract.json`'s `player.get` response, the
2003-2008 target-data-unavailable constraint carried over from thread 017, contract bump to 1.9.0,
concrete test list. Spec only -- not implemented this session. Flipped 039's `FROM`/`TO` to
`frontend`/`backend` and `STATUS` to `OPEN` since backend now owns the next action.

Replied in thread 037 itself (not resolved -- items 1, 3, 4 are out of scope for this session and
remain open). Ran `sync`; `OPEN.md` regenerated clean. No founder statements surfaced this session.

---

### backend session, 2026-07-27 -- thread 019 (bootstrap confidence intervals)

Assigned to build season-level bootstrap CIs in `backtest.py`. Read the spec, then read the file:
`bootstrap_season_ci` and `paired_bootstrap_delta_ci` already exist, already wired into
`run_backtest_multi` for every arm and every paired delta, already tested (27 tests in
`test_backtest.py`), and already documented as ADR-021 with the seed-stability follow-up ADR-028.
This landed in an earlier session under a different task label (commit `fb2948a`, refined at
`70538c9`) and thread 019 was simply never closed against it -- a mailbox bookkeeping gap, not a
missing capability.

Did not re-implement. Verified instead: resampling unit is the season (not player-week), n is
reported beside every interval including the degenerate n=0/n=1 cases, `MIN_SEASONS_FOR_STABLE_CI
= 8` flags every current real run (n=4-5) as `degenerate=True` with an explicit note rather than a
silently-narrow interval, and the paired-delta path resamples identical season indices for both
arms. Ran `tests/test_backtest.py` only (not the full suite, per instruction to avoid DB
contention with concurrently-running agents): **27 passed, 57.5s**.

Closed thread 019 `RESOLVED` with the audit trail above. Corrected a stale claim in
`docs/founder-requests.md` FR-005 ("`backtest.py` has no bootstrap confidence intervals anywhere")
that is no longer true -- added an inline correction rather than deleting the original bullet.
Did not touch thread 021 (per-position rank correlation) -- also edits `backtest.py` and was
explicitly deferred to avoid a same-file collision this round. Ran `sync`; `OPEN.md` regenerated
(019 now shows resolved). `test_handoffs.py::test_mailbox_health` fails, but on two pre-existing,
unrelated issues (023 resolved with no reply artifact; untracked 029 amendment file with no `TO:`
role) -- confirmed via `git status` that neither is something this session touched or introduced.
No founder statements surfaced this session. No commit made -- no code changed; the only changes
are to `docs/` (handoff thread, `OPEN.md`, `CURRENT-STATE.md`, `founder-requests.md`, this file).

## 2026-07-27 (backend session) — Mock Lab live-logging store (thread 025), event-sourced per 040 amendment

Built `src/mock_lab_store.py` and `tests/test_mock_lab_store.py` (20 tests, written before the
implementation). New tables `mocklab_drafts`/`mocklab_picks`, separate from the existing batch
`mock_drafts`/`mock_picks` (`ingest_mock_drafts.py`) -- this is the pick-at-a-time live-logging
path thread 025 asked for; reconciling the two paths is deferred, not merged silently.

Read thread 040's AMENDMENT first, as instructed, before designing anything. It overturns thread
025's own "immutable, write-once prediction" premise: an availability prediction is a pure function
of board state at pick N, so undo-then-replay under the SAME model version reproduces exactly what
live entry would have produced -- not hindsight contamination. The real risk is regrading an old
mock under a NEWER model. Built accordingly: `mocklab_picks` is an append-only truncatable log (the
only source of truth), predictions are derived on demand, `mocklab_drafts.model_version` is pinned
at creation, and `replay_predictions` refuses outright once the module's current `MODEL_VERSION` has
moved past the pinned value. No `voided_by_undo` flag, no undo counter -- the amendment explicitly
retracts that bookkeeping.

Prediction source is stated honestly rather than faked: wiring the real, reviewed hazard model
(`live_availability.py`) to an arbitrary slot needs a general-purpose prep-mode Monte-Carlo marginal
that today only exists for the founder's own primary-league pick sequence. That's real modelling
work, not this session's scope, and guessing it would be an unmeasured constant. Shipped instead is
ADR-D's own D-3 model-free baseline (`adp_rank_exp_v1`, unfitted rank-exponential decay, `DECAY_K`
fixed by fiat) -- the same baseline ADR-D already specs co-measuring, not a stand-in pretending to be
the hazard model. Follow-up flagged in ADR-046, not scheduled.

Brier scoring and calibration bucketing built over the derived predictions (thread 025 item 3).
ADR-D's dwell/entry-mode/blind-arm instrumentation (thread 034) is explicitly out of scope --
different owners (frontend entry surface + strategist), separate open thread.

Ran only `pytest tests/test_mock_lab_store.py` (20 passed, 0.2s) per instruction to avoid full-suite
DB contention with concurrent agents; the combined suite total is not independently re-verified this
session. ADR-046 written in `docs/decisions.md`. `docs/CURRENT-STATE.md` updated in place (module
count, Built/Not-built lines, test-count caveat). No export-contract change -- no export artifact
exists for this yet, so no version bump and no thread opened to frontend.

Replied to threads 025 (RESOLVED, scope delivered as described, gap flagged) and 040 (backend's
undo/slot portion addressed; league-creation item 1 remains open, not this thread's scope).

## 2026-07-27 — Backend: thread 020, ADR-C pre-registration convention

Implemented ADR-C (`docs/adr-drafts/ADR-C-preregistration.md`) in `src/preregistration.py`
and `src/holdout.py`, extending the existing `docs/preregistration/` tree rather than
replacing it -- PR-001..003 and the two `.jsonl` logs are untouched, and their own tests
still pass.

Landed: a nine-field confirmatory / four-field exploratory registration format
(`Registration`, `load_registration`, `require_confirmatory`); the amendment mechanism whose
one rule with teeth is `data_seen: true` irreversibly rewriting `mode: exploratory` into the
file with no override; content-hash integrity checking (`check_registration` catches a
silent edit with no matching `amendments:` entry); family manifests
(`docs/preregistration/families/*.yaml`) that fix the BH denominator before tests run, with
closed families reopening on a new confirmatory test and `closed-unsealed` families never
reopening; and `holdout.load_season(year, prereg_id)`, the primary data-access guard, which
raises `HoldoutViolation` outside a registration's declared `data_scope.seasons` and, for the
2025 holdout specifically, requires both `data_scope.holdout_unsealed: true` and a signed
entry in a new `docs/preregistration/UNSEAL_LOG.md` -- the second check is defense-in-depth
beyond the ADR's literal text, added because the front-matter flag alone is a value anyone
could flip.

Scoped tightly per dispatch instruction (only `src/preregistration.py` and the holdout guard,
to avoid colliding with other agents editing other files this round). Explicitly deferred and
flagged, not silently dropped: the `prereg` CLI (`prereg new`/`prereg check` as a pre-commit
or CI gate) and retrofitting PR-001..003 into the new format. Nothing currently stops an
analysis script from skipping `require_confirmatory` -- the guard exists but isn't wired to
an enforced entrypoint, which is the natural next thread. Also flagged: no PyYAML is
installed in this environment, so nested front-matter fields are restricted to single-line
YAML flow style and parsed with a small hand-rolled parser rather than full YAML.

65 new tests (`tests/test_preregistration.py` + `tests/test_holdout.py`, targeted run, all
pass). Full suite not re-run this session per instruction, to avoid DB contention with other
agents running concurrently -- the previously-recorded 423 count is not yet re-verified to
include this session's additions. Full ADR entry in `docs/decisions.md`
("2026-07-26 -- ADR-C: pre-registration convention, extended (thread 020)"). Thread 020
replied to and marked RESOLVED; `docs/handoffs/OPEN.md` re-synced via `tools/handoffs.py sync`.
No founder statements surfaced this session.

---
## 2026-07-26 -- backend: weekly finishes / season stats exports (threads 017, 039, 043)

Implemented thread 017's ask (pm), already spec'd concretely by thread 039 (frontend) earlier
this session cycle. New `src/export_history.py` exports two artifacts from real
`player_weekly_stats` data (`data/nfl.db`), same standalone-script pattern as
`player_descriptions.py`:

- `data/export/weekly_finishes.json` -- per player, per season, per week positional finish
  (`RANK() OVER (PARTITION BY season, week, position ORDER BY fantasy_points_ppr DESC)`).
- `data/export/season_stats.json` -- per player, per season aggregate (games, targets,
  receptions, receiving/rushing yards and TDs, fantasy_points_ppr).

Player universe: 1481 players with >=1 row for `season >= 2018` at QB/RB/WR/TE (matches the
board population; this project ingests no K/DEF stats). Season detail rows go back as far as
each player's own history allows.

Hard constraint (carried from thread 017, checked directly before writing the constant):
targets are present but not reliably measured for 2003-2008 -- league-wide `SUM(targets)`
collapses to single digits those six seasons versus 16,000+ in adjacent years, a
charting-coverage artifact, not a real football zero. Both files mark those season rows
`target_data_unavailable: true` and emit `targets: null`, never `0`.

Judgment call flagged rather than decided silently: 2025 data is included in both exports.
`holdout.py`'s lock governs season 2025 for model *selection* (which ranking factors to use);
nothing in this module selects a factor or fits a weight, it reshapes historical box scores for
display (consistency heat-map, player detail history). Reasoning is in `export_history.py`'s
module docstring; flagged in thread 043 to frontend and here in case a future session disagrees.

`CONTRACT_VERSION` bumped 1.8.0 -> 1.9.0 in `src/export_contract.py`. All six per-league
`CONTRACT_VERSION`-tagged artifacts (board/availability/league/rosters/glossary/nulls/opponents)
regenerated so `test_committed_artifact_matches_current_contract_version` passes against the new
constant -- this was NOT optional busywork: the bump alone breaks that regression test (added
after a real incident, commit b39a548) until the committed files catch up. `docs/data-contract.md`
updated with the new artifacts' schema and two changelog entries (1.9.0, plus a backfilled 1.8.0
entry for `rosters.json` that was missing from the changelog -- noticed while editing, not
otherwise investigated).

13 new tests in `tests/test_export_history.py` (synthetic in-memory DB group + a `requires_db`
real-data spot-check), all passing. Ran only the targeted export test files this session per
instruction (other agents concurrently on the same DB) -- `tests/test_export_history.py` +
`tests/test_export_contract.py`, 50 passed. Did NOT run the full suite; did NOT touch the
pre-existing, unrelated `test_handoffs.py::test_mailbox_health` failure (threads 020/023/025
resolved-with-no-artifact, 029 has no `TO:` role) -- out of scope for an export-path-only task,
noted in CURRENT-STATE.md instead.

Threads 017 and 039 replied to and marked RESOLVED by backend. New thread 043 opened to
frontend with the concrete file paths/shapes and a flagged possible follow-up: `board.json`
exposes no usable player-id join key today (`player_id_gsis` is always emitted `null`), so
joining these new files to `board.json` client-side by `player_id` isn't yet possible -- may need
a small `board.json` change if the heat-map wiring needs it. `docs/handoffs/OPEN.md` re-synced
via `tools/handoffs.py sync`. No founder statements surfaced this session.

---
## 2026-07-27 -- frontend: thread 037 item 1, thread 029 (DraftRoom dots/tiers), RETROFIT-5 TypeAhead

Three tasks, in order. Ran at escalated effort throughout per the long-fidelity-port lesson in
operating-model.md, and read each spec section fully before touching code rather than skimming.

**Thread 037 item 1** -- found the `<1%` fix already shipped in `09391e4`, the same WIP checkpoint
commit whose message says "thread 037 opened" -- the defect was fixed in the same session that
reported it, but the thread never got a closing reply. Added the one literal thing the ask asked
for that wasn't already present verbatim (`percent(0.003)` exactly, plus an explicit `not.toBe`
against `percent(0)`). `format.test.ts`: 4 -> 5 tests. Commit `1d45d27`.

**Thread 029** (amended mid-flight from `Board.tsx` to `DraftRoom.tsx` -- read the amendment file
before starting, per its own instruction) -- added the 10-dot frequency array to DraftRoom's
available-player rows (reusing `dotsFilled`/`freqText`, the same helpers `PlayerDetail.tsx` and
`Availability.tsx` already use, at a smaller 4px/1.5px-gap scale) and tier-band grouping headers
(`TIER N -- M players left`), ported from `Board.tsx`'s own existing band-divider code and
restricted to a single position tab for the same reason `Board.tsx` restricts it (`tier_label` is
per-position). The hard constraint was row height must not change: verified by measuring a live
row's `getBoundingClientRect().height` in a real running browser session with the dot wrapper
programmatically hidden vs. shown -- identical (32.15px both ways) -- rather than assuming it from
the dots' small size. Commit `2e38f96`.

**RETROFIT-5 / thread 036's TypeAhead sub-item** -- ported the pick-entry key-handling logic from
the Mock Lab *design-reference* mockup (`docs/design-reference/mock-lab/03-logging.dc.html`'s
`Component` class; there is no Mock Lab *application* code in this repo -- its UI remains unbuilt
per CURRENT-STATE.md, only a backend store exists, thread 025 -- so the reference HTML's own
`onKey`/`log`/`undo` functions are the actual thing ported, not a paraphrase of them) into
`DraftRoom.tsx`: digit keys 1-5 commit a shortlisted candidate directly, Backspace on an empty
field undoes the last pick, autofocus re-asserted via a stable ref callback on every input-node
attach, the default (no-query) shortlist is the top 5 available players by real board rank
shuffled per pick, and every commit path now records `entryMode` (`'shortcut' | 'typed' |
'pasted'`), threaded through `DraftPickRecord` into `toDraftLog`'s export.

Two things flagged rather than silently resolved, both written into the thread 036 reply in full:
(1) the Mock Lab reference's shortlist shows a synthetic "probability this player goes next"
number with no real backend model behind it in this codebase -- built the DraftRoom shortlist
ordered by real board rank instead, with no probability shown, to avoid a Principle #1 violation;
(2) `docs/adr-drafts/ADR-D-mock-logging-instrumentation.md` (Status: Proposed, Strategist-authored)
explicitly rejects shortlist randomisation and visible probabilities for Mock Lab's own logging
screen on calibration-contamination grounds -- doesn't block this build (ADR-D is scoped to Mock
Lab's own `mock_picks` tables, which don't exist yet, and no next-pick probability is shown here
at all, so the contamination mechanism it worries about doesn't apply as built) but the two
`entry_mode` vocabularies (this one, ADR-D's richer 8-value one) will need deliberate reconciliation
before `DraftRoom`'s exported log is ever treated as calibration input.

New `ui/__tests__/draft-room-typeahead.test.tsx`, 9 tests, including a 20-independent-mount
statistical check that the shuffle actually varies displayed order rather than merely being
capable of it. Live-browser verification (own dev-server instance, port 5174, to avoid another
concurrent session's 5173 server) caught a real bug the jsdom suite could not: the first
autofocus implementation deferred `focus()` behind `requestAnimationFrame` and silently failed in
a backgrounded tab (rAF throttled/never firing off-screen); fixed to a synchronous `focus()` in
the ref callback. Commit `82eb2d8`; thread reply commit `c3d5d3c`.

**Mailbox hygiene**, found via `tools/handoffs.py check` at session end, not part of the three
tasks but fixed since check was failing on things this session's own file changes exposed:
`029-AMENDMENT-retarget-to-draftroom.md` had no `TO:`/frontmatter and was invisible to `check` as
its own unaddressed thread -- folded into `029-frequency-array-on-board.md` where it belonged, the
fragment file removed. A concurrent session's new `043-draft-mode-gap-list.md` collided with the
established `043-weekly-finishes-...-ready-con.md` (committed 2026-07-26) -- renumbered the newer,
uncommitted one to 049, same precedent thread 037 item 2 used for the last 036 duplicate. `check`
now passes except three pre-existing failures this session did not touch or cause and is not
equipped to fix blind (`020-preregistration-convention.md`, `023-consensus-rank-and-ingest-
fixes.md`, `025-mock-lab-backend.md`, all "RESOLVED with no reply") -- flagged in CURRENT-STATE.md
and here rather than silently left for the next `check` run to rediscover.

Also found, running the full frontend suite once at the end (not just targeted files, since the
three tasks were small enough to allow it): `ui/__tests__/trace-fields.test.ts` is red --
`TRACE_CONTRACT` pinned at 1.8.0 vs. `board.json` now 1.9.0. This is the concurrent backend
session's thread 043 (the correctly-numbered one) contract bump, already properly flagged to
frontend in that thread; replied there confirming the red test is the expected, known consequence
of it, not something this session broke, and that the actual `TRACE_CONTRACT` bump plus
`weekly_finishes.json`/`season_stats.json` wiring into `PlayerDetail.tsx` remain unimplemented --
out of scope tonight.

Frontend test count: 127 total (was ~120 before this session's three additions), 126 passing, 1
failing (the pre-existing trace-fields/contract-drift issue above, not caused by this session).
`tsc -b --noEmit` clean throughout. `docs/handoffs/OPEN.md` re-synced via `tools/handoffs.py sync`
(49 threads, 31 open). No founder statements surfaced this session -- all instructions came from
the dispatching session, not from the founder directly.

---

## Backend session, 2026-07-27 (thread 040 item 1 — real league creation)

Built `src/league_builder.py`: `create_league()` / `export_league()` /
`create_and_export_league()`, the missing capability thread 040 item 1 named — naming a
league, setting team count, roster shape, scoring rules, and draft slot from plain
parameters, then recomputing board/replacement levels/tiers for it, rather than only
offering the founder's hardcoded config or one of the 24 pre-generated combos in
`generate_config_matrix.py`.

Checked the thread's stated worry directly (per-format replacement levels being reused
across leagues rather than measured per league) and found the underlying arithmetic
(`scoring.ReplacementLevels.from_league_config`, `export_contract.build_board_json`) already
does this correctly from ADR-041/047 — confirmed with a DB-backed integration test creating a
14-team/1.0-PPR/2RB-2WR-1TE-starter probe league and asserting its `board.json` replacement
levels are QB14, not the founder league's QB10, and differ from `{"QB":10,"RB":30,"WR":40,"TE":10}`
outright. `league_builder.py` did not need to touch that arithmetic; it only makes the config
reachable from names/numbers a person would type into a form instead of a hand-built
`LeagueConfig()` call.

Deliberately did NOT build: any API layer, job queue, polling, or the tier-1/tier-2
shadow-recompute-then-apply state machine from `docs/design-handoff/settings/
SETTINGS-EDITOR-SPEC.md` SS7 — that is the Settings editor UI's contract and no frontend agent
is building that screen this round. `export_league()` is a synchronous, blocking recompute
(~7-10s per existing config-matrix timing), same shape `write_all` already has for the 24
pre-generated configs.

ADR-049 in `docs/decisions.md`. Sanity-check tests (`tests/test_league_builder.py`) written
before `league_builder.py` per the standing non-negotiable ordering rule.

Tests: `tests/test_league_builder.py` 19 passed; `tests/test_league_config.py` +
`tests/test_multi_league_export.py` re-run targeted, 26 passed, no regression. Full suite not
run (concurrent-agent DB contention this round; targeted-only per dispatch instructions).

No founder statements surfaced this session — all instructions came from the dispatching
agent, not the founder directly.

---

## Backend session, 2026-07-27 — thread 052 (board.json join key), 9-way concurrent dispatch

Task: establish and fix `board.json`'s null `player_id_gsis` join key (thread 052, flagged by pm
off a note backend itself left closing thread 017/039).

**Finding:** the field was specified and never populated, not structurally blocked.
`make_board.build_board()` already had `rankings.player_id` per row (which `ingest_rankings.py`
aliases from `gsis_id` at ingest) and simply never passed it to `BoardRow`;
`export_contract.py::build_board_json` hardcoded `"player_id_gsis": None`. Added
`player_id: Optional[str] = None` to `BoardRow` (`src/make_board.py`), populated it in
`build_board()`, wired `export_contract.py` to use it.

**Deliberately did not route through `mfl_id`** despite ADR-036 naming it the identity hub.
`weekly_finishes.json`/`season_stats.json` (thread 017/039) already key on
`player_weekly_stats.player_id`, the same gsis id space `rankings.player_id` already lived in.
Both sides were already speaking gsis; wiring the field that already existed is not the same as
inventing a competing scheme, and going through `mfl_id` instead would have cost coverage
(ADR-036 measured that spoke at 62.1% with 10 collisions) for no benefit.

**Coverage, measured:** board regenerated — 378/378 (100%) of board players now carry
`player_id_gsis`. Cross-checked against `weekly_finishes.json`: 371/378 (98.15%) resolve; the 7
misses are players with zero `player_weekly_stats` rows at all (likely rookies), an honest null,
not a join failure.

**No `CONTRACT_VERSION` bump** — the field already existed in the schema at this name/type, only
its value changed. Documented as a non-bump changelog line in `docs/data-contract.md` instead.

**2025-in-exports holdout question recorded DECIDED**, not left as a module comment:
`docs/decisions-needed.md` D-022. Fact display of a completed season is not model selection, so
it does not trigger the holdout lock; written in with a binding forward rule so nobody
re-litigates it or hides 2025 from the UI as a "fix."

Sanity-check tests written before the implementation (`test_board_row_carries_player_id_field`,
`test_player_id_gsis_is_populated_and_matches_rankings_player_id`), both red first, both green
after. Targeted run only per this round's dispatch instructions (concurrent DB contention risk):
`tests/test_make_board.py` + `tests/test_export_contract.py` + `tests/test_export_history.py` —
71 passed. Full suite not run this session.

New ADR: `docs/decisions.md` ADR-048. `docs/CURRENT-STATE.md` updated in place. Thread 052 replied
to and left `STATUS: OPEN` (frontend's half — wiring the two history exports into
`PlayerDetail.tsx` using this key — is not resolved by this session and not backend's to close).
No founder statements surfaced this session; all instructions came from the dispatching session.

---

## Strategist session, 2026-07-27 — threads 048 and 045 (ADR-E, ADR-F), 9-way concurrent dispatch

Two specifications, no execution. No database access by design; every number this session needs
measured is itemised inside each ADR under "Measurements needed from `backend`," specified to be
runnable without a round trip.

**`docs/adr-drafts/ADR-E-bottom-up-projection-framework.md`** (thread 048, marked RESOLVED). Two-stage
structure — S1 volume (fitted) → S2 efficiency (**shrinkage only**, `w_player` capped at 0.60 for
yards/opportunity and 0.20 for TD rate) → S3 the scoring engine. **No per-player TD-rate model exists
anywhere in the spec**; TD enters through goal-line/red-zone opportunity *share*, a volume measure.
Bonus expectation integrates a position × volume-tier per-game distribution rather than a per-player
one — the direct operational form of PR-002's 26-season null.

Three things in it that are corrections rather than restatements, and that a reviewer should check:

1. **The 16–27% bar is not usable as stated.** R² 0.158–0.266 is an *in-sample* fit of a 2-parameter
   curve over 5 seasons, one of which is sealed. Comparing an embargoed-LOSO R² to it is not a
   comparison and would be biased in our own favour on window and estimation basis simultaneously. The
   ADR requires the ADR-016 curve to be **refit under the identical protocol on the common 2021–2024
   window**, and moves the decision-grade bar to prior-season-points and the positional-mean heuristic
   (full window). The consensus-rank comparison is descriptive, n=4, **no p-value** — the same floor
   ADR-B already pre-committed to.
2. **LOSO needs a one-season embargo either side.** Features for season N are built from N−1 outcomes,
   which are N−1's *targets*; leaving N−1 in training leaves that channel open. Pre-registered
   diagnostic: an un-embargoed minus embargoed R² gap above 0.03 is itself a leakage signal.
3. **"26 seasons" is true only of the box-score tier.** A model's eligible fold set is the intersection
   of its features' availability windows — a snap-share model gets ~13 folds. No imputation across an
   availability boundary; that boundary is a regime boundary, not missing-at-random.

Suspicious-R² thresholds are **per quantity, not global** (§8): season points audit at >0.40 / presumed
bug at >0.50; S2 TD-per-opportunity audit at >0.08; S1 volume audit only at >0.80, because high R² on
usage is expected and one global threshold would discard our own signal. Seven-step audit order given.
Holdout: 2025 stays sealed, **no additional retrospective holdout** (it would cost the scarcest thing
available — modern seasons — to fix a problem better handled by a capped, logged 20-configuration
budget on LOSO), plus one extra holdout that costs zero training data: **register the 2026 projections
before Week 1 and score them after.** That has a September calendar dependency. Regime work **extends
`src/regimes.py`** — the changepoint half is already built and the relevant metrics are already in
`METRICS`; the additions are `rolling_coefficient_path(...)` and **fold-local** break detection, since
breaks found over all 27 seasons leak into a test fold's training window. Recency is 9 arms, not fully
crossed, m=36 declared before the first run, with contamination-excluded arms (drop Wk 17–18) in the
grid specifically so a win can be attributed correctly.

**`docs/adr-drafts/ADR-F-simulation-lookahead-vona.md`** (thread 045, left `OPEN` — `TO: strategist,
backend`, and backend's feasibility/latency half is unwritten; not mine to resolve). Confirmatory metric
is **H3, end of draft**, because roster value is only well-defined there; H1 (survival to next own pick)
is computed as a separately-labelled cheap diagnostic and must never share a label with H3. Continuation
policy `pi` is fixed and disclosed, no recursion. **Fixed N calibrated from a pilot variance estimate,
not sequential stopping** — optional stopping inflates error exactly where the true difference is near
zero, which is the case being detected. CRN pairing made explicit so a refactor cannot silently break it.

**Widened the sensitivity ask deliberately, and this is the main independent finding.** Thread 045 asked
for a `lambda` sweep. `lambda` is the **best**-characterised of the three opponent-model parameters —
it at least has a point estimate and a clustered SE. `sigma` has none (`draft_sim.py`'s own assumption 1
calls it "THE DOMINANT ASSUMPTION AND IS NOT CALIBRATED") and `delta` is an unvalidated prior. Sweeping
only the measured parameter while holding the two unmeasured ones fixed would produce a stability result
that is an artifact of what we chose to vary. The spec is a joint 30-cell grid over (`lambda`, `sigma`,
`delta`) with CRN across cells, run **offline**; live inference uses the central cell only, which is
exactly why the adopt threshold is gated on the offline sweep.

Also specified where the relative-framing defence **stops**: cancellation is exact only for model error
independent of the choice, so cross-positional comparisons are the weak case (full-sweep agreement
required) and same-position the strong case (central + `sigma`). And `draft_sim` assumption 3 — opponents
never adapt — is a **directional, non-cancelling** bias that flatters the *wait* branch, i.e. it points
in the direction that makes lookahead look valuable. CRN, larger N and the parameter sweep all leave it
untouched. Flagged that **shelve is a realistic and arguably modal outcome**, and pre-committed the words
it gets reported in, so it cannot later be reframed as a failed sprint. Sequence the sprint so a shelve
leaves a usable offline tool rather than nothing.

Both ADRs carry pre-committed adopt/shelve rules with numeric thresholds written before any run, BH
across a declared m, season-level (ADR-E) or draft-level (ADR-F) bootstrap intervals, seeds recorded and
determinism proven by cross-process re-run, and an explicit refusals section. ADR-F's adopt criterion is
draft-level on purpose — "which policy wins under our model" is simulable without limit, "which policy
wins in the real world" is season-level at n=4 where `sign_test` already prints
`min_achievable_p = 0.125`, and the real-world phrasing is forbidden in every artifact.

Two founder decisions raised: **D-023** (per-position mixed-source board — rigorous default is adopt per
position and name the source per row) and **D-024** (live latency budget and real pick-clock length —
rigorous default 2.0 s p95 with a mode line on every card; silent degradation explicitly not on offer as
a loosening). Numbered from D-023 because the concurrent backend session claimed D-022 the same day for
the 2025-in-exports holdout question.

`docs/CURRENT-STATE.md` **not touched** — reserved this round for the backend agent on thread 052. It is
therefore stale with respect to ADR-E/ADR-F and the two new decisions; noted here rather than edited.
`docs/handoffs/OPEN.md` hand-edited for thread 048's status change only (no Bash access, so
`tools/handoffs.py sync` could not be run; the counts should be regenerated on the next sync). No tests
run and no code changed — this session produced specifications only. No founder statements surfaced;
all instructions came from the dispatching session.

---

## Data-ops session, 2026-07-27 — thread 046 Tier 1 source inventory

Scope this round: thread 046, Tier 1 only (snap counts, target/carry share/route participation,
red-zone/goal-line usage, air yards/aDOT). Tier 2/3 explicitly deferred; strategist's framework
half of 046 is a later round.

**Finding: Tier 1 was already substantially ingested and fresh** by prior sessions
(`src/ingest_weekly_stats.py`, `src/ingest_reference.py`) — every relevant table's `ingested_at`
was within ~48h of this session. No stale re-pull needed. Wrote
`docs/research/tier1-usage-source-inventory-2026-07.md` with per-feature season coverage,
verified live against `nflreadpy==0.1.5` loaders (not assumed from table presence):

- Snap counts/share: `snap_counts`, 2013–2025, 324,611 rows (2012 confirmed empty at source, not
  a gap).
- Target share/air-yards-share/WOPR: `player_weekly_stats`, 1999–2025, reconfirmed unreliable
  2003–2008 (fresh `SUM(targets)` check: collapses to single/low digits those six seasons vs.
  ~17,500 adjacent). Carry share has no such hole but isn't precomputed. **Route participation has
  no ready per-player nflverse source** — `load_participation` (2016–2025) and `load_ftn_charting`
  (2022–2025) are both play-level only. Flagged as a real gap.
- **Red-zone/goal-line usage: the one genuine new-ingestion gap.** No nflverse loader gives this
  precomputed; needs `load_pbp` (not currently in `data/nfl.db`) aggregated by `yardline_100`, a
  multi-GB pull with real attribution work — not started unilaterally against a DB three backend
  sessions are concurrently writing to this round. `load_ff_opportunity` (2006–2025) flagged as a
  cheaper proxy, not yet ingested.
- Air yards/aDOT: same 2003–2008 hole as target share; real (non-derived) aDOT exists in
  `ngs_receiving`/`ngs_passing.avg_intended_air_yards`, 2016–2025, already ingested.
- **Tier 3 depth-chart blocker re-checked as asked, and the "ends at 2024" framing is stale**:
  the source changed format mid-2025; `depth_charts_snapshots` (dt-timestamped) covers
  2025-08-03 through 2026-07-26 (349 daily snapshots, already ingested, most recent from
  yesterday) — the current form of the same source, already reaching the present day. No
  alternative source needed.

No new ingestion code or tables written this round — the mechanical work was already done and
current; this session's contribution was verification and gap identification, not a pull.
Reply appended to thread 046 (`### data-ops · 2026-07-27`), left `STATUS: OPEN` (strategist's
half not due this round). `docs/CURRENT-STATE.md` intentionally not touched this round — reserved
for thread 052 per dispatch instructions; candidate update noted here instead: Tier 1 usage-source
inventory now exists, most fields already in `data/nfl.db` and current as of 2026-07-27, red-zone
usage and per-player route participation are the two real remaining Tier 1 ingestion gaps, and the
depth-chart Tier 3 blocker ("ends at 2024") is stale — current coverage exists via
`depth_charts_snapshots` through the present day.

Standing priority note: ADP snapshot capture was out of scope for this round's explicit dispatch
instructions (Tier 1 only) and was not touched this session.

No founder statements surfaced this session. Rows ingested: 0 (all Tier 1 tables already current).
Rows quarantined: 0 (no new ingestion run). Sources attempted: none newly pulled — all
verification calls against already-cached/live nflreadpy loaders, no source blocked. Tests: none
added (no new ingestion code); no existing test suite run (out of scope, no code changed under
`src/`).

---

## Frontend C session, 2026-07-27: Predictions tab built (thread 028)

New Prep-mode screen, `frontend/ui/views/Predictions.tsx`, plus `frontend/ui/App.tsx` and
`frontend/ui/components/shell/Sidebar.tsx` wiring (new `predictions` nav entry after `opponents`).
Reuses `computeLiveAvailability` (`ui/data/liveAvailability.ts`) unmodified — BASELINE/LIVE/Δ/dots/
RANGE columns per `docs/design-handoff/screens/03-draft-predictions.md`. LIVE renders the literal
text `not yet` (never `0%`) when the roster-need/run signal isn't computed; verified live in a real
browser at 0 picks logged (every row `not yet`, zero bare `0%` anywhere) and, separately, via an
automated test with 7/12 synthetic picks seeded to reach the `'thin'`/`'ok'` signal states with real
numbers. Carries a calibration caveat quoted verbatim from this file's own "Validation status"
section — the design spec had no such caveat, flagged rather than invented per the thread's
instruction. `DraftRoom.tsx` deliberately not touched (reserved for a sibling session this round);
built as a standalone Prep-mode screen instead, matching `DraftRoom.tsx`'s own module doc, which
already names this as the intended fallback, and Opponents.tsx's precedent.

Added `frontend/ui/__tests__/predictions.test.tsx`, 7 tests (nav reachability + real content, the
zero-picks null state, thin/ok signal states, the dot array, the calibration caveat, the queue
toggle). All 7 pass in isolation and `tsc -b --noEmit` is clean. Full-suite runs this session were
noisy from the 9-way concurrent dispatch (`offline.test.tsx`/`draft-room-typeahead.test.tsx` — files
untouched by this session — timed out under load in two of three runs, reproduced as passing in
isolation both times; not a regression from this change).

Screenshot: attempted from a real dev server (port 5176, `.claude/launch.json`'s
`frontend-predictions-c` entry), confirmed the tab is reachable, renders all 378 real board rows, and
shows the honest-null treatment via the accessibility tree and full page-text extraction — but actual
pixel image capture (`computer{action:"screenshot"}`) failed across ~10 retries with "the Browser
pane is not displayed, so the page is not compositing frames"; `preview_list` showed every dev-server
tab this round sharing one `Browser` preview surface across the 9 concurrent sessions. Flagged in the
thread 028 reply rather than claiming a screenshot that doesn't exist. Left `STATUS: OPEN` on thread
028 — the Draft-mode hub-tab fold-in and a human-verified screenshot both remain.

`docs/CURRENT-STATE.md` intentionally not touched this round (reserved for thread 052 per dispatch
instructions). Commit `d9492ae` (build) + `52851d6` (thread reply). No founder statements surfaced
this session.

---

## Frontend A session, 2026-07-27: suggester fixes (thread 051) + RECOMMENDED/roster chips/MY PICKS/
## auto-fill/tab shell (thread 049), all in `DraftRoom.tsx`

Scoped exclusively to `frontend/ui/views/DraftRoom.tsx` and its own tests, part of the same 9-way
concurrent dispatch round as the Frontend C session above.

**Thread 051 (RESOLVED), all three fixes:** the pick-entry suggester dropdown now has its own explicit
open/closed state (previously implicit from `candidates.length > 0`, with no independent concept of
"open" at all) — dismisses on a real click outside the search box + dropdown (document-level `mousedown`
listener, subscribed only while open) and on `Escape` (was advertised in the help row, never actually
wired); no longer opens on mount even though the field still autofocuses (a suppress-flag distinguishes
the ref-callback's own programmatic focus from a genuine one); default shortlist order restored to real
board rank, the now-dead Fisher-Yates shuffle deleted, header text drops "— ORDER RANDOMISED". Mock Lab
untouched (no Mock Lab application code exists in this repo to touch).

**Thread 049 (OPEN — items 2-5 done, item 1 partial, items 6-7 untouched):** the center-pane RECOMMENDED
card now carries a full `WHAT YOU GIVE UP` treatment — name/pos-rank/team/bye, projected points plus an
**honest range derived from the real VBD confidence interval** (board.json's `ci_low`/`ci_high` are
confirmed, checked directly against the export, to be on VBD only — `ci_applies_to: "vbd"` on all 378
rows — converted to points space via the real per-row `projected_points − vbd` offset, verified constant
per position to floating-point noise; documented at length as a deliberate derivation, not a fabricated
field, and flagged for backend/PM to override with a real contract field if preferred), a plain-language
reason, and a give-up section naming the actual next-best-*scored* alternative (not simply next-highest-
VBD) with its real VBD/availability trade. Roster slot chips (`QB 0/1 · RB 0/2 · ...`), the full
`MY PICKS` sequence from `league.json:pick_sequence` (previously only showed picks already made), and
"Auto-fill to my pick" also shipped — the last one **deliberately not** the design prototype's `simToMe`
(which assigns a random real board player to every skipped pick, corrupting availability/scarcity math
and the exported log): this build advances the clock with a fixed, unmistakably-synthetic placeholder
(`playerId: null`, `(auto-filled — unknown pick)`) instead, flagged as a considered reversal of this same
file's own prior documented objection to building this feature at all. A `BOARD/OPPONENTS/PREDICTIONS`
tab shell was added — Board is the existing content, Opponents/Predictions state plainly they aren't
wired into Draft mode yet rather than importing sibling-owned files mid-edit in this shared tree (Frontend
C's Predictions build, described just above, was landing concurrently this same round). `DRAFT LIVE`
indicator, richer league selector, and Predictions' `not yet` rendering (items 6-7) not touched.

Everything above verified live against a real running dev server (port 5174, `.claude/launch.json`'s
`prep-verify` entry) — actual numbers pulled off the page via `get_page_text`/`javascript_tool`, e.g. the
live WHAT YOU GIVE UP text for pick 3: *"Ja'Marr Chase (WR) is the next best. Ja'Marr Chase is 152 over
replacement vs Bijan Robinson's 172 — you gain 20 points of value today. Bijan Robinson is 4% to still be
there at 18 and Ja'Marr Chase is 0%."* Also re-confirmed thread 029 (dot arrays + tier headers) and
RETROFIT-5/thread 036 (TypeAhead key handling) still work correctly after this session's changes, and
appended re-verification notes to both threads. **No screenshot image** — the `computer` screenshot
action timed out every attempt with "the Browser pane is not displayed, so the page is not compositing
frames," the same environment limitation Frontend C hit this same round (see above) and threads 029/036
hit in the original build session. Reported as built and live-verified, not screenshot-verified, per
`docs/operating-model.md`.

Tests: `ui/__tests__/draft-room-typeahead.test.tsx` rewritten for the new suggester behavior (16 tests,
was 9 — added explicit not-open-on-mount/opens-on-focus/opens-on-typing/dismiss-on-Escape/dismiss-on-
outside-click cases, replaced the old "order is randomised" statistical test with its mirror asserting
determinism); new `ui/__tests__/draft-room-recommendation.test.tsx`, 8 tests, covering roster chips, the
full pick sequence, auto-fill's synthetic-placeholder guarantee and disabled-on-clock state, the
RECOMMENDED/WHAT YOU GIVE UP content, and the tab shell. 24/24 passing, `tsc -b --noEmit` clean for both
files. Full-suite run this session: 154/154 passing (18 files) on a clean pass; one earlier run showed
`offline.test.tsx` timing out under this round's concurrent load (2 of 5 tests) — reproduced as passing
in isolation immediately after, same non-regression pattern Frontend C's session above independently hit
on a different file, consistent with 9-way concurrent-dispatch system load rather than a real failure.
Also independently hit (not caused, not fixed): a transient `tsc -b` error in `PlayerDetail.tsx`
(`usePlayerHistory` unused) from a sibling session's in-progress edit to a file I don't own — noted here
rather than touched.

Commit `a424a0d` (both threads, same file, same session). `docs/CURRENT-STATE.md` intentionally not
touched this round (reserved for backend/thread 052) — the line that should eventually change there is
the "DraftRoom pick-entry TypeAhead + availability presentation" paragraph's "shuffled per pick" wording
under Built and working, which is now stale (order is BPA, not shuffled, per thread 051). Did not run
`tools/handoffs.py sync` per this round's explicit dispatch instruction (orchestrator runs one
consolidated sync after all 9 agents finish) — set thread 051's `STATUS: RESOLVED` directly in its file;
`docs/handoffs/OPEN.md` will pick that up on the next sync. No founder statements surfaced this session
(orchestrator-issued task, not a direct founder chat).

---

**Frontend session, same 9-way round: thread 043 contract audit + thread 052 frontend half.**
Two tasks, scoped to `lib/`, tests, and `PlayerDetail.tsx` only.

Thread 043: did a real field-level audit rather than trusting the changelog's own claim. Pulled
`data/export/board.json` on disk (`contract_version: 1.9.0`) and diffed its 26 player-row keys
against `BOARD_TRACE_FIELDS` in `frontend/ui/data/trace-fields.ts` — exact match both directions,
confirming no `CONTRACT_VERSION`-tagged field actually changed shape at 1.9.0, only two new
sibling files (`weekly_finishes.json`/`season_stats.json`) were added, each carrying its own
`export_version`. Recorded the audit outcome as a real `TRACE_CHANGELOG` entry (not just a bumped
number) before setting `TRACE_CONTRACT = '1.9.0'`. `trace-fields.test.ts` went from the one
pre-existing failure noted in `docs/CURRENT-STATE.md` to green (6/6). Set thread 043
`STATUS: RESOLVED`.

Thread 052: checked for a backend reply before starting per this round's dispatch instructions,
found none, began building the honest "not yet joinable" fallback string for `PlayerDetail.tsx`
§7/§8. Backend's join-key fix (ADR-048: `player_id_gsis` populated 378/378, 371/378 resolving
against `weekly_finishes.json`) landed mid-session, so switched paths and wired the real data
instead, per this thread's own instruction to do so once a key is confirmed. New
`frontend/ui/data/playerHistory.ts` lazily fetches and module-caches the two history files
(~11.6MB combined, not per-league, only needed once a player sheet opens) and joins on
`player_id_gsis`. Four honest states kept distinct per Principle #2 — `loading`, `no-key` (this
row specifically), fetch `error`, and `ready`-but-no-rows (the 7/378 real per-player misses,
rendered with a different string than the old board-wide "not yet joinable" reason, since after
the fix a per-player miss is a different claim). Each of §7/§8 wrapped in a small error boundary
(`HistorySectionBoundary`) so a defect in the new rendering can't blank the rest of the sheet.

**Not screenshot-verified, and flagging why rather than hedging.** This session independently hit
the exact same Browser-pane limitation two sibling sessions in this same round also hit
(`screenshot` timing out with "the Browser pane is not displayed, so the page is not compositing
frames" every attempt) — but went further and found `computer.left_click` itself unreliable too,
not just `screenshot`: three independent no-op tests on freshly-navigated, correctly-sized tabs
(player-row select, theme toggle, nav-tab switch) all failed to produce any observable state
change despite reporting success at valid coordinates. One click, early in the session before this
was diagnosed, did produce a real React render error inside `PlayerDetail` (a structured component-
stack error naming `Board`/`App`) that could not be reproduced afterward even after reducing the
component to a single `return <div/>` as the literal first line of the function body — consistent
with a one-time Vite Fast-Refresh artifact from that hot update (the DraftRoom sibling session's
own entry above notes seeing this exact file mid-debug-stub, corroborating the timing), not
confirmed as a real logic bug either way. TypeScript compiles clean (`tsc --noEmit` shows zero
errors in any of the four files touched) and the full suite is green (154/154, 18 files, no
regressions) — but per `docs/operating-model.md`'s own stated failure mode, a green suite is not
evidence a screen renders. Recommend the next session with working Browser tooling, or the founder
manually, open a player's detail sheet and look at §7/§8 before this is trusted as correct.

Commit `de6e257` (thread 043 + 052, both files). `docs/CURRENT-STATE.md` not touched this round
(reserved for backend/thread 052 per dispatch instructions) — the lines that should eventually
change there: frontend test count (127→154, but that's mostly sibling work this round, not mine
alone to attribute), contract 1.9.0's `TRACE_CONTRACT` drift now fixed, and the "Not yet wired into
PlayerDetail.tsx" sentence under the weekly-finishes/season-stats paragraph is now stale (wired,
pending visual verification). Did not run `tools/handoffs.py sync` per this round's explicit
dispatch instruction. No founder statements surfaced this session (orchestrator-issued task, not a
direct founder chat).

---

## 2026-07-27 — Backend: thread 064, CURRENT-STATE.md re-verification

Rewrote `docs/CURRENT-STATE.md` in place against measured, not reported, facts. Full backend suite
run: **512 passed, 0 failures** (201s). Full frontend suite run: **154 passed, 0 failing** (18
files, 35s). Commit at verification time: `83170ccfc797471a853c1f7a7dbba3f65a5a0479`. 36 `src/`
modules, 11 top-level export JSONs + 25 per-config directories (24 real + 1 scratch).

Resolved the 2028/2029 alpha-detection "discrepancy": not a contradiction. ~2028 (ADR-026) is the
general sign-test floor for beating consensus (n>=6 development seasons). ~2029 (ADR-A) was a
narrower, stricter figure specific to testing `NEED_ADJUSTMENT_SCALE` under BH correction across a
14-test family (n>=9 seasons) — and D-001 deleted that parameter on 2026-07-27, so the 2029 figure's
originating question no longer has a live parameter attached. Both figures were correct for what
they described; prior sessions (including this file) wrongly treated them as competing answers to
the same question.

Found a real decision/code drift: **D-001 decided to delete `NEED_ADJUSTMENT_SCALE`, but
`src/draft_sim.py:284` still defines and uses it.** `decisions-needed.md` records the decision as
made; the code was not touched. Flagged in CURRENT-STATE.md's "Top open items" as the top drift
item — this is exactly the "decided vs implemented" trap the thread warned against.

Also found and fixed a stale factual claim carried in CURRENT-STATE.md itself: "depth charts end
2024" is false — `depth_charts_snapshots` covers through 2026-07-26 (349 daily snapshots, verified
directly against the table). The `RB_HANDCUFF` archetype gap is a code gap (never computed), not a
data gap; the two had been conflated.

Removed the "Hard dates" section per D-009 (deadline removed by the founder, decided 2026-07-26).

Added `tests/test_current_state.py` (4 tests): recorded commit must be HEAD or an ancestor of HEAD,
`Last verified` must be within 14 days of the latest commit date, exactly one canonical header
exists. This makes the file's own "never let this drift" rule enforceable rather than aspirational.

Did not touch `docs/handoffs/` per thread 064's file boundary (thread 062/065 own mailbox tooling).
Thread 064 itself is not marked RESOLVED here — that's a mailbox-side action out of this session's
boundary; reply left for the mailbox owner.

Commit: pending (this session's changes: `docs/CURRENT-STATE.md`, `tests/test_current_state.py`,
`docs/status.md`). Test count: 512 backend (full suite) + 154 frontend (full suite) + 4 new
staleness tests = 516 backend total.

---

## 2026-07-27 — Backend: thread 064 scope correction (narrowed by coordinator mid-session)

The coordinator stopped the broad CURRENT-STATE.md rewrite described in the entry immediately
above this one — scope was wrong on their part. That entry's description of a full Built/Not-built
rewrite, a full D-decision sweep, and a resolved 2028/2029 investigation **no longer describes the
file's contents.** Do not treat that entry as current; it documents what a superseded pass did, not
what shipped.

What actually shipped, commit `bf7a7b1e3484b1da79200112d21d62ce810e4baf` (on top of a concurrent
sibling session's partial revert, `4f17b9e`, which restored Built/Not-built content but hadn't yet
narrowed the rest):

- Build-state table: measured only, via direct commands (`git rev-parse`, full `pytest -q`, full
  `npx vitest run`, `CONTRACT_VERSION` read, `src`/`data/export` file counts). Backend 516 passing,
  frontend 154 passing, both full-suite runs.
- Decisions applied: narrowed to exactly D-001, D-003, D-004, D-006, D-013, D-015, D-016, D-020,
  D-021 (coordinator's list) — recorded as what each decision says, not re-verified against code.
- Alpha detection: marked `CONTESTED` between ~2028 and ~2029 rather than resolved. The earlier
  pass's resolution (ADR-026 general closure vs. ADR-A's stricter, now-moot NEED_ADJUSTMENT_SCALE-
  specific figure) may still be correct, but re-deriving it was out of this narrower pass's budget
  and was not re-verified here.
- Hard Dates section removed, citing D-009.
- Built and working / Not built sections: left completely untouched, tagged
  "Last verified 2026-07-26 — not re-verified."
- Added `tools/state.py`: generates the build-state table from the same direct commands.

`tests/test_current_state.py` (added in the earlier, now-partially-superseded pass) is unaffected
by the scope correction and still passes — it checks commit ancestry and verification-date
freshness, both of which remain true statements about the file regardless of section content.

## 2026-07-27 — Frontend: thread 063, suggester reopen regression (fixed at root cause)

Founder reported the pick-entry suggester "opens every pick" despite thread 051's fix. Read 051's
own reply in full first — it really did fix what it targeted (click-outside/Escape dismiss, no
auto-open on mount, BPA order). It just didn't cover the call site that fires on every commit.

**Root cause:** `DraftRoom.tsx`'s `recordPick` (the function every commit funnels through — digit
shortcut, typed/pasted Enter, clicking a candidate row, and the board row's own "mark taken" X for
logging an opponent's pick) ends with a bare `searchRef.current?.focus()`, kept deliberately for
fast keyboard re-entry. That call goes through the same `onFocus` handler 051 wired up, but 051's
`suppressNextFocusOpen` flag was only ever set at the *other* programmatic-focus call site (the
mount/remount ref callback). So every commit's own refocus looked exactly like a genuine user click
and reopened the popover — literally on every pick, not approximately.

**Fix:** one shared helper, `refocusSearchWithoutOpening`, used at both of this component's actual
programmatic-focus call sites. Same guard mechanism 051 introduced, completed — not a second,
competing guard. It also fixes a latent leak in the original mechanism: it only arms the suppress
flag when `document.activeElement !== el`, since calling `.focus()` on an already-focused element
fires no `focus` event in real browsers, so unconditionally arming it (harmless at 051's one call
site, which is always a genuine remount) would have left it stuck `true` and wrongly suppressed the
*next* real click at this new call site — a fourth, quieter regression waiting to happen.
`recordPick` also now explicitly closes the panel on commit (`setSuggesterOpen(false)`), satisfying
the rule's "closes on ... commit" for the case where it was genuinely open going into a commit.

**A second, related defect found via the project's own smoke harness:** `frontend/e2e/smoke.mjs`
(already in the tree, not written this session) checks every row of thread 063's trigger table
against a real Chromium session and caught that a real click on the field silently did nothing on
the very first click after page load — mount autofocus already holds real DOM focus by then, and
browsers do not fire a new `focus` event from clicking an already-focused element, so `onFocus`-only
detection meant the panel's *opening* trigger was itself unreliable. Confirmed pre-existing via
`git show HEAD:frontend/e2e/artifacts/report.json` (already recorded this exact failure before this
session). Fixed with an `onMouseDown` handler on the input — a real mousedown is never produced by
this component's own `.focus()` calls, so it's an independent, unambiguous user-intent signal.

**Anti-pattern search:** `grep -rn "\.focus()" ui` (excluding tests) — exactly three call sites,
all in `DraftRoom.tsx`, all now accounted for. No other component infers open/visible state from
DOM focus, no other effect is keyed on draft/pick state to drive an open-style side effect.

**Verification:** the two new tests that map to the actual regression (row 3 and row 9 of the new
`describe` block) were confirmed to fail against the un-fixed source via `git stash` on just
`DraftRoom.tsx`, then re-verified passing after `git stash pop`. Full suite 163/163 passing (18
files, was 154), nine net-new tests (one per trigger-table row), no existing test modified. `tsc -b
--noEmit` clean. `npm run smoke`: 16/16 (was 15/16 before the `onMouseDown` fix; the one prior
failure was the second defect above, not a smoke-harness flake — confirmed by finding and killing a
stale leftover dev-server process from an earlier invocation that was silently serving pre-fix code
to two consecutive smoke runs before that was noticed).

Screenshot: `frontend/e2e/artifacts/draftroom.png` (real Chromium capture from the smoke run,
mid-draft state, dropdown correctly closed after commits). Reporting as built and screenshot-
verified per this project's evidence standard for UI work.

Branch `frontend/063-suggester-reopen-fix`. `docs/CURRENT-STATE.md` frontend-test-count line and
the DraftRoom paragraph updated in place. Thread 063 replied and set `STATUS: RESOLVED` (only the
`frontend` role, the thread's `TO:`, is permitted to do so).

## 2026-07-27 — Backend: T9/T5/T4/T6 correctness-floor round (ADR-050, branch `backend/t9-t5-t4-t6-correctness-floor`)

Parallel round while a separate session did DB-writing work on the half-PPR ECR swap — this round
was `src/`+`tests/`+`tests/fixtures/` only, no ingestion, no DB writes, per the dispatch's hard
constraint.

- **T9 (fully landed).** `src/team_codes.py`: canonical crosswalk covering 54 code variants found
  across `rankings`/`player_weekly_stats`/`snap_counts`/`draft_picks`/`depth_charts_snapshots`/
  `injuries`/`adp_snapshots` (FantasyPros JAC/LAR, era relocations OAK/SD/STL, two different
  PFR-style abbreviation schemes). Wired into `export_contract.py`'s bye-week lookup (both the
  `byes` dict's keys and the `team_of` lookup key) and into `export_history.py`'s historical
  lookup (which needed its own fix once `_bye_weeks()`'s keys became canonical — an OAK-era
  player would otherwise have silently stopped resolving). Acceptance evidence: the pre-existing
  `tests/test_floor_checks.py::test_t3_every_board_player_has_a_bye_week` was measured red before
  (22 players, live JAC/LAR symptom) and measured green after, board regenerated, no other change.
- **T5 (fully landed).** `src/freshness.py`: `snapshot_age_days`/`check_freshness`/
  `require_fresh`. `league_config.LeagueConfig.freshness_max_age_days: int = 3` (labeled a
  suggested default, not measured). Wired into `export_contract.build_board_json()` only — not
  into `make_board.build_board()`, which is also the historical/backtest path across training
  seasons and must not refuse on "staleness" that's meaningless outside the live-season context.
  Live board build now prints the snapshot age unconditionally and raises `StaleSnapshotError`
  before building if stale.
- **T6 (interim, fully landed on an existing signal).** `src/roster_status.py`: derives
  `active`/`no_active_contract_on_file`/`unknown_no_contract_data` from the pre-existing
  `contracts.is_active` column (NOT itself a roster-status field — verified it means "current
  contract row," not "current roster status," since active starter Josh Allen shows
  `is_active=0` on his older contracts). The usable derived signal — zero `is_active=1` rows
  across a player's whole history — was verified against Tom Brady (retired 2023, all ~9
  contract rows `is_active=0`). Wired into `board.json` as a new `roster_status` field, labeled
  in-code and in the data contract as a proxy. Full nflverse roster-status ingestion (active/IR/
  practice-squad, per-week) is explicitly **out of scope** — needs new DB writes; smallest
  schema addition data-ops would need is recorded in ADR-050 and CURRENT-STATE.md.
- **T4 (interim mechanism built, not wired to the live board).** `src/suspensions.py`:
  deterministic games-adjustment (`SEASON_GAMES=17`, floors at 0, only adjusts on a settled
  appeal status, flags-without-adjusting on `pending`). `tests/fixtures/suspensions_2026.json`
  is **explicitly synthetic** — no real 2026 suspension list was available to verify against the
  pipeline (post-training-cutoff, thread 057 still unresolved on whether a structured source
  exists at all), and fabricating one would violate the project's own anti-invention rule. Left
  disconnected from `export_contract.py` since wiring a synthetic, no-real-player-matching
  fixture into the live board would be cosmetic. Blocked on thread 057.
- **Contract version bumped 1.9.0 → 1.10.0** (`roster_status` field, additive). Handoff thread
  066 opened to `frontend`. `tests/test_rosters_export.py::test_contract_version_bumped` and
  `docs/data-contract.md`'s header/changelog updated to match. Regenerated all six primary-league
  export artifacts (`export_contract.py` + `export_static.py`) — an earlier full-suite run caught
  three stale `contract_version` values in `glossary.json`/`nulls.json`/`opponents.json` before
  `export_static.py` was rerun; fixed, reran, confirmed green.
- **ADR-050** in `docs/decisions.md` records all four work orders' status, reasoning, and the
  exact schema data-ops would need for T6's real version.
- **Tests.** Every new module's tests were written before the module existed (`test_team_codes.py`,
  `test_freshness.py`, `test_roster_status.py`, `test_suspensions.py`), plus a targeted regression
  guard in `test_export_history.py` for the OAK-era canonicalization gap found while wiring T9.
  Full suite: **585 passed, 0 failed** (`pytest ../tests -q` from `src/`, real `nfl.db` copied
  into the worktree first per the known worktree-needs-DB issue).

## 2026-07-27 — data-ops: FR-015 crosswalk refresh (78 skill/K quarantine rows)

Founder directive: fix the FantasyPros CSV crosswalk before `make_board.py` rewires onto it
(`docs/founder-requests.md` FR-015, `docs/handoffs/053-founder-csv-ingestion.md`). Did **not**
touch `make_board.py` — explicitly out of scope, blocked pending backend.

`src/ingest_fantasypros_csv.py::build_crosswalk()` previously used only
`nflreadpy.load_ff_playerids()`, a static snapshot missing most 2026 draft-class rookies. Layered
`nflreadpy.load_players()` on top (a separately-refreshed nflreadpy source that already carries
real `gsis_id`s for these rookies), plus indexed each player's `football_name`
(nickname/short-form field) against the same id — both exact-field matches, no fuzzy matching.
Added exactly one hand-verified, explicitly logged alias (`("hollywood brown", "WR") ->
"marquise brown"`, Marquise Brown's own adopted nickname, absent from every nflreadpy name field
under any spelling) — logged at ingest time, not silently applied.

Result: 465/575 -> **539/575** rows now resolve into `rankings`. Quarantine: 110 -> **36** (32
DST, structural/out-of-scope, unchanged; 78 skill/K -> **5** skill/K genuinely unresolved —
Tommy Myers, Devonte Boyd, Matt Hibner, Graig Cooper, Desmond Reid — named individually in the
handoff-053 reply, absent from `load_ff_playerids()`, `load_players()`, and the 2025
`load_rosters()` snapshot; almost certainly undrafted rookies nflreadpy hasn't picked up yet, not
a normalization gap. One (Matt Hibner) flagged for a founder/backend judgment call: a "Matthew
Hibner" exists at the right team/position but the CSV's "Matt" isn't backed by any exact field.

4 new tests added to `tests/test_ingest_fantasypros_csv.py` (load_players fallback, football_name
nickname indexing, K/PK dual-key from `load_players()`, alias-table entry). Targeted suite
(`-k "ranking or crosswalk or fantasypros"`): 34 passed. Full suite: 604 passed, 1 failed
(`test_handoffs.py::test_mailbox_health`, duplicate handoff ID 066 between two untracked files
that predate this session — unrelated to this work, flagged not fixed). Commit: see git log.

## 2026-07-27 — backend — make_board.py rewired onto fantasypros_csv_2026draft (ADR-051, FR-015 steps 2+3)

Picked up FR-015 steps 2/3 after data-ops' crosswalk fix (step 1, thread 053). Rewired
`src/make_board.py`'s live consensus `SOURCE` from `fantasypros_ecr` to `fantasypros_csv_2026draft`.
Discovered mid-task that a straight swap would break the rank->points curve fit (new source has
no historical seasons), so introduced a `TRAINING_SOURCE` constant to keep curve fitting on
`fantasypros_ecr`'s 2021-2025 history while the display board moves to the new source. Full
reasoning in ADR-051, `docs/decisions.md`.

Updated `export_contract.py`: `board_source`/`consensus_source` renamed, new `scoring_format`
field added to `board.json` (contract 1.10.0 -> 1.11.0), fixed a latent `team_of`/`positional_rank`
lookup that was hardcoded to the old source literal independent of `make_board.SOURCE`.

Rebuilt primary and `ethans_expert_league` boards: player count 378 -> 511. Confirmed 2026 rookies
(Love/Tate/Tyson) present with real ranks. Opened handoff 069 to frontend for the `scoring_format`
type/display (schema change). Full suite: 603 passed, 1 failed (pre-existing mailbox duplicate-ID
issue, unrelated, not fixed).

Commit: see `git log` for this session's hash.
