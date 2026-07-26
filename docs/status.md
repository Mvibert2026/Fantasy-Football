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
