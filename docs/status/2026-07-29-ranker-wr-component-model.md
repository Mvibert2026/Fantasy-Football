# 2026-07-29 — ranker — WR component model, pass 1 (FR-054)

Worktree `agent-a642ecc75591d1614`. Commits `61012d0`, `43ad7b1`, and the test commit that
follows them. 14 new tests, all passing.

## What was asked

Start the bottom-up model proper. Not a better ordering — a per-player projection of the
components scoring consumes, from which a rank falls out under any ruleset, carrying a per-game
distribution so the stacking bonuses are computable. One position, done properly.

## What was built

`experiments/bottomup/components/` — five modules:

| file | what it is |
|---|---|
| `wr_data.py` | player-season panel with a hard cutoff gate and a per-read audit log; pre-season universe builder |
| `wr_features.py` | lagged features, all from seasons ≤ N−1 plus April-of-N draft slots |
| `wr_model.py` | the component model — availability, volume, three shrunk efficiency rates, and a binomial GLM for the per-game exceedance distribution |
| `adp_baseline.py` | FFC archived ADP, re-gated against real Week 1 kickoffs parsed from PFR game ids |
| `wr_eval.py` / `run_wr.py` | walk-forward 2014-2024, three required baselines, season-block bootstrap |

Report: `docs/ranking/component-model-wr-pass-1.md`. Results CSVs:
`experiments/bottomup/results/wr_components_{walkforward,metrics}.csv`.

## Result, stated the way CLAUDE.md §6.5 requires

**The model does not beat consensus ADP.** +0.048 Spearman, 95% CI [−0.013, +0.124], seven
seasons. It beats prior-season points (+0.128 [+0.072, +0.186]) and the weighted-PPG heuristic
(+0.091 [+0.013, +0.163]).

**The design is underpowered and that is the more useful observation.** On the same seven seasons,
consensus ADP itself cannot be shown to beat the weighted-PPG heuristic (+0.043 [−0.035, +0.124]).
A beats-consensus test is not resolvable from this data, so registering one would spend the sealed
2025 holdout on a question it cannot answer.

**The component projections — FR-054's actual deliverable — beat naive persistence on every
component with clear intervals.** Receiving yards MAE −31.0 [−37.4, −25.0] per player-season,
receptions −2.4, receiving TDs −0.28, games −0.64, targets −4.3.

**The ceiling channel is closed at WR.** Oracle with perfect foresight of realised stacking-bonus
points: +0.026 ρ [+0.018, +0.033]. Modelled version: +0.0002, moving five receivers out of 2,271
by three or more ranks. Conditional on mean yards per game, between-player dispersion in
100-yard-game rate is *below* binomial noise (excess −0.00176, n=1,360), and the residual does not
persist (r = −0.006 [−0.073, +0.060]).

## What changes for other sessions

- **Ceiling/variance pricing should stop being planned work at WR.** Referred to `strategist`
  (thread 094) rather than asserted; it is a WR result and does not automatically transfer to RB or
  TE.
- **`nfl.db.injuries` (79,816 rows) is unused by every model in this project and is the highest-value
  unexploited input found this pass.** The model's ten worst calls versus market are all receivers
  coming off a season lost to injury or suspension; the availability sub-model cannot tell "did not
  play" from "played badly".
- **"We have 26 seasons" is false for anything usage-based.** Targets are empty 2003-2008, air yards
  begin 2009, three seasons go to lags. The real number is 13.
- **The FFC ADP backfill CSVs are usable without the database.** `adp_baseline.py` reads
  `data/adp-snapshots-ffc/` directly, so a session that cannot rebuild `nfl.db` still has real ADP.

## Open

Thread **094** to `strategist`: register the availability factor as the confirmatory test, and rule
on dropping the beats-consensus test. Nothing in this pass is confirmatory and nothing is claimed
as an edge.
