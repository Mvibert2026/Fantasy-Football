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
| Backtest harness | Works; **statistical corrections still pending (Task 9)** |
| Regime analysis | `src/regimes.py` — sup-Wald breaks, trend cycles, era similarity |
| Draft board | `data/board_2026.csv` — 378 players, VBD with bootstrap CIs |
| Alpha detection | **Not built** (Task 6) |
| Holdout / pre-registration | **Not built** (Task 7) |
| Feature pipeline | **Not built** (Task 8) |

**89 automated tests passing.**

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

## Prior results still marked PROVISIONAL

Tests #44/#45/#46 (session 3) predate `statistical-guardrails.md` and do not meet it. #46 has now
been materially **revised** — its original figure conditioned on actual finish rather than draft
slot, which understated QB value (see test-registry.md). The remaining gaps for all three:
per-position rank correlation, bootstrap CIs, and a consensus baseline are Task 9.

---

## Next steps (Tasks 6-9, post-checkpoint)

1. **Task 9 first, not last.** `_rank_correlation` still pools positions, there are still no CIs,
   and the re-scored board is not yet wired in as the primary baseline. Every downstream result
   depends on these being right.
2. **Task 7 before any factor sweep.** Holdout lock + pre-registration + persistent test count must
   exist *before* factors are tested, or the multiple-comparisons correction is applied to a
   subset chosen after the fact.
3. **Task 8** feature pipeline, with each feature declaring its first-available season from
   `data-availability.md` and a test proving cutoff-invariance.
4. **Task 6** alpha detection last, since it depends on 7 and 8. Note the flagged specification
   issue: a *linear* control on consensus rank is misspecified (points-vs-rank is strongly convex),
   and would manufacture false alpha; use a flexible control and report sensitivity.
5. **Re-pull the 2026 board in late August** once FantasyPros publishes preseason-final snapshots.
   The current board is flagged `is_preseason_final=0` and will move.
