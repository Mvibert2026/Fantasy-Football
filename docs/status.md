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

**2. The board's advantage over consensus does not survive the holdout.** Including 2025,
`starter_vbd` delta was **+84.6 [+2.3, +153.0]** — excluding zero, and reportable as a win.
On development seasons only it is **−84.9 [−166.1, +34.7]** — no demonstrated difference,
with the sign flipped. Had the holdout not been locked first, the first number would have
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
board's positional re-weighting still shows no demonstrated advantage over raw consensus on
development seasons. The league-specific edge is now considerably thinner than the project has
been assuming.

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
