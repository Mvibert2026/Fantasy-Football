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
