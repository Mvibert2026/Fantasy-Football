# 2026-07-29 — ranker — bottom-up research pass 1: where is the edge, and is it reducible at all

**Task.** Opening research pass for the founder's bottom-up ranking. Explore widely, commit to
nothing, ship no model. Answer first how much of a season's variance is reducible at all, then
survey four candidate edge channels cheaply. Deliverable:
`docs/ranking/bottom-up-research-pass-1.md`.

**Effort tier.** Opus/xhigh, per `.claude/agents/ranker.md`. Statistical methodology and model
design, CLAUDE.md §9.

## Premise check, done before any work

Every load-bearing claim in the brief was checked against the repo and holds — with one
correction that turned into the session's main finding. The "consensus explains 0.16-0.27"
figure is real (`docs/data-contract.md:95`) but it is the R² of the *consensus-rank curve*, not a
property of the game; the same curve fitted on realised finish rank has R² 0.91-0.98. The QB
slope series (`docs/ideas-inbox.md:229`) is real and reproduces; its *interpretation* is now
contested.

## What was measured

Five scripts, read-only handle on `data/nfl.db`, points scored through the real
`src/scoring.py` league config. **Season 2025 was never loaded** — not for features, not for
evaluation, not once. Universe frozen from season N−1 before N is opened, so busts and zero-game
seasons count. Bootstrap CIs resample seasons, not players.

1. An **oracle ladder** on season points (folds 2010-2024): naive baselines, consensus where it
   exists, and two impossible predictors that know exactly one thing about the target season.
2. A **three-way variance decomposition** of season ppg into stable player level, real
   season-specific shift, and week-to-week noise — the first from adjacent-season correlation
   (never the middle season), the third from within-season split-half.
3. **Bonus arithmetic**: every player-season 2009-2024 scored twice, with and without the
   stacking bonuses.
4. **Regime curves**: `points ~ a + b·ln(rank)` fitted per position per season, 1999-2024, on
   realised finish rank *and* on consensus rank, side by side.
5. **Two independent bounds on the team channel**: a perfect-foresight team-volume oracle, and a
   team fixed-effect ANOVA on prediction residuals against its own chance expectation.

## Findings, all exploratory, none registered

**The variance question has an answer and it is uncomfortable.** At WR, of observed season-ppg
variance: 12.5% week-to-week noise, 20.1% real season-specific change, 52.3% already priced by
consensus, ~15.1% stable quality left unpriced. Availability is the bigger unexplained block and
is near-unforecastable (prior games predicts games at r = 0.09-0.18). **The founder's edge is not
in forecasting a player's rate.**

**The shipped board's rank curve confounds positional value with market skill.** Realised QB value
spread is at an era *high* (era-mean slope −72.9 in 2021-2024 vs −57 to −59 before) while the
consensus-fitted slope fell. TE shows the same pattern; RB and WR do not. If that reading is
right, the recency-weighting fix on record would make the board chase market noise. **Opened
thread 085 to `strategist` rather than acting** — I do not rule on my own work, and this argues
against another agent's finding.

**TE is the position with unpriced stable signal**, on three independent lines: the ledger
(0.336 unpriced vs 0.151 at RB/WR), consensus failing to beat prior-season ppg there
(0.303 vs 0.407), and the prior prototype's only CI-clear VBD win.

**Two data gaps closed by deciding not to buy them.** The whole team-environment channel —
coaching a strict subset — is bounded at ≤ +0.055 τ by a *leaky, generous* oracle and shows zero
excess fixed-effect variance at every position. Coaching staff history and Vegas implied totals
should not be funded on this evidence.

**The bonus channel is now quantified for the first time**: half a positional rank of realised
reordering, less ex ante, and cross-positional rather than within-position (~6.8 points of
relative VBD between WR and TE). Real, small, and not the structural edge it has been called.

## Things I got wrong or nearly got wrong, recorded deliberately

- **Regression to the mean nearly became a finding.** Bucketing consensus residuals by consensus
  tier showed top-12 "underperforming" everywhere. That is Galton, not market error. Caught and
  removed by de-trending before anything was written down.
- **I rebuilt the V3 self-inclusion leak.** My first team-environment oracle let a player's own
  production into his team's total — the exact leak the ext-2 session found and named. Rebuilding
  it with self-exclusion produced a numerically unstable specification with negative τ, which I
  discarded as a broken spec rather than reporting as a negative result. The leaky version is
  reported as what it is: a generous upper bound.
- **The calibration prior applied to my own output.** Two consensus-residual patterns look like
  good stories (RB touchdown regression, WR post-injury over-rating). Both are r² ≈ 0.03 on n=4
  seasons with ~16 uncorrected comparisons. Recorded at half weight as hypotheses; neither is
  proposed as a factor.

## Repo defect fixed in passing

`tools/handoffs.py:31` — `ROLES` did not include `ranker` although `.claude/agents/ranker.md`
exists, so this role could not open a correctly attributed thread. One-line addition.

## Threads opened

- **084 → `data-ops`**: deepen expert consensus history before 2021. This is the only measured
  data gap that still binds; n=4 caps every market-relative claim below significance permanently.
- **085 → `strategist`**: rule on the rank-curve confound, and register (or reject) the
  decomposition experiment. No confirmatory run happens without it.

## Where I would go next

The decomposition experiment in thread 085 — it is the only candidate that touches a live defect
in a shipped artefact, needs no new data, is few-parameter, and is testable on 26 seasons rather
than 4. Runner-up and close: a TE arm built on `snap_counts` (2013-2025, 324,611 rows, already in
the database, never read by the prototype) as a labelled route-participation proxy.
