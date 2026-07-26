# Deferred Decisions

## Normalized `players` dimension table

`CLAUDE.md` §4's core-tables sketch lists both `players` and `player_weekly_stats`. Only
`player_weekly_stats` was built (2026-07-25). A separate `players` table would require making
identity-resolution judgment calls (current team/position when they change mid-season or
year-to-year, name changes, etc.) with no current consumer — the raw fact table already carries
`player_name`, `position`, and `team` per row, which is sufficient for Step 1. Build it when the
scoring engine (Step 2) or ranking algorithm (Step 4) actually needs a stable per-player entity
to join against, not before.

## `player_season_stats` table

Also in `CLAUDE.md`'s sketch, not built. Season-level aggregates are a derived view over
`player_weekly_stats` (sum/avg by player+season) with no independent source data — better as a
SQL view or computed at read time once there's a real consumer, rather than a second cached copy
that can drift out of sync with the weekly table.

## Coaching staff, odds, ADP ingestion

Explicitly out of scope for this pass — the task was weekly player stats only. `coach_id`,
`odds_snapshots`, and `adp_snapshots` remain unbuilt. Per `CLAUDE.md`'s own flag: ADP snapshot
capture with `as_of_date` should start "immediately regardless of sequence" since it can't be
backfilled later — this is the next highest-priority ingestion gap, not weekly stats.

## True multi-source ADP (2026-07-25, attempted, blocked)

Requested sources: FFC, Yahoo, ESPN, Sleeper, Underdog. None ingested. Per-source finding:

- **FFC (Fantasy Football Calculator):** `robots.txt` explicitly disallows `/api/`, `/ajax/`,
  and `/adp/csv/`. No published API docs or ToS permitting programmatic access were found.
  `CLAUDE.md` §10 requires checking terms *before* building a scraper. Blocked, not attempted.
- **Yahoo / ESPN:** Would require OAuth and league-scoped access for any real draft data; no
  known public bulk ADP export. `CLAUDE.md` §10 explicitly discourages scripted-login workarounds.
  Not attempted.
- **Sleeper:** Has a public read-only league API, but no known public *aggregate ADP* dataset
  (as opposed to one league's own draft results). Not attempted — would need more research.
  Underdog: no known public API at all. Not attempted.

**What's actually available today:** FantasyPros Expert Consensus Rankings (ECR), via
`nflreadpy.load_ff_rankings()` → DynastyProcess.com's mirror — already ingested for 2025
(`src/ingest_rankings.py`, `source="fantasypros_ecr"`). This is expert opinion, not observed
draft position; the backtest harness (`src/backtest.py`) reports `consensus_adp` as explicitly
unavailable rather than substituting ECR under the ADP label. Test-registry.md's own tracked
status for "Multi-source ADP" (Tier 0 #1) was already `SPEC` (not started) before this pass —
this finding narrows the scope (FFC ruled out) rather than starting from zero.

**Next step if this becomes a priority:** get explicit authorization/API-key access to FFC (email
them — some hobby-analytics API access has historically been grantable on request even where
`robots.txt` blocks anonymous crawling), or have the user manually export ADP snapshots from
sites requiring login.

## FantasyPros preseason rankings for other backtest seasons (2021-2024)

Only the 2025 preseason snapshot was ingested (as literally requested). `load_ff_rankings(type=
"all")` already returns the full history back to 2020 in one call, so extending
`src/ingest_rankings.py` to backfill 2021-2024 preseason snapshots is a cheap follow-up (no new
data source, same function, just loop over seasons) — needed before the backtest harness can
evaluate any season other than 2025.

## Backtest harness: no draft-cost-sensitive comparison metric (2026-07-25, found while running #44)

`_vbd_sum_for_ranking()` (`src/backtest.py`) only tests whether a ranking puts the right players
*in* each position's startable pool (top-N by `ReplacementLevels`) — it's blind to the *order*
players are ranked in beyond that cutoff, and therefore blind to draft-slot opportunity cost.
Discovered running the Hero RB config (test-registry.md #44): boosting the value of RBs already
comfortably inside the RB28 cutoff produced an *identical* result to plain BPA, because the boost
never changed pool membership. This isn't evidence Hero RB is neutral — the test just can't see
what the strategy does.

Needed before any "pick X earlier than consensus" strategy (Hero RB, Zero RB, elite-TE-early,
etc.) can be tested for real: a metric sensitive to what you gave up elsewhere by reaching, e.g. a
draft-pick-slot simulation (take the ranking, assign players to picks in snake order, compare the
resulting roster's total value against a baseline roster built the same way) rather than a pure
value-over-replacement sum. Bigger lift than the current metric; not attempted this pass.

## Statistical guardrails compliance gaps (2026-07-25, found auditing #44/#45/#46 against the new doc)

`docs/statistical-guardrails.md` landed after the #44/#45/#46 runs. Auditing those runs against its
own pre-mortem checklist (full table in test-registry.md) surfaced concrete, fixable gaps — not
retracting the findings, but none of them are "validated" by that doc's standard yet:

1. **`backtest.py::_rank_correlation` computes correlation across all positions mixed together.**
   `statistical-guardrails.md` §6 requires it within position group (QB ranks vs. QB outcomes,
   not QB/RB/WR/TE pooled). Fix: group by position before calling `spearmanr`, return a per-position
   dict (and probably a position-weighted or separately-reported aggregate, not a single blended
   number — needs a design decision, not just a mechanical change).
2. **No confidence intervals anywhere in `backtest.py` output.** §7 requires season-level bootstrap
   resampling for any reported metric (correlation, vbd_sum delta). With 5 seasons of data, every
   point estimate reported so far (-1,070 pts, -226.4 pts, etc.) is, per that doc, "close to
   meaningless" without one. Needs a `bootstrap_seasons()` utility and a decision on how many
   backtest seasons are actually available to resample from (currently only 2025 has FantasyPros
   preseason data ingested — see the FantasyPros-backfill item above; bootstrapping single-season
   metrics needs a different resampling unit, e.g. players-within-season with a
   caveat, until multi-season data exists).
3. **No multiple-comparisons correction infrastructure.** Not urgent at 3 configs, but test #53 and
   any future factor sweep (Tier 1's ~20 items) will need Benjamini-Hochberg FDR correction
   (§3.2) before reporting "significant" factors. Build this before, not during, that sweep.
4. **No pre-registration workflow.** §3.4 requires writing down the exact metric/threshold that
   counts as confirmation *before* running a test, especially for folk-wisdom factors. No file or
   convention exists yet for recording a pre-registration. Needed before test #53 runs.

## Defense/DST scoring and ingestion

`scoring.py` ports `score_defense_game()` from the source code as given, but no ingestion
pipeline feeds it — `player_weekly_stats` and the `rankings` table are both skill-position-only
by construction (DST rows are dropped in `ingest_rankings.py` for lack of a `gsis_id`). The
league does have a DEF slot (`CLAUDE.md` §7 / test-registry.md league context). Out of scope for
this pass since it wasn't part of the requested narrow schema; the backtest harness currently
only evaluates offensive skill positions.

## Phase 3 — draft-time tooling (deferred, but constrains the schema TODAY)

These are not being built now. They are recorded here because each imposes a data-capture
requirement that becomes unrecoverable if ignored, and the capture is cheap today.

### P3-1. VONA-based board ordering, replacing VBD

VBD ranks by value over a *positional replacement*, which is the right static question and
the wrong draft-day one. The draft-day question is value over the *next available
alternative at your next pick* — VONA. At pick 18 with your next pick at 23, the relevant
quantity is not "how much better is this RB than RB28" but "how much better is he than the
RB who will still be there at 23".

**Schema requirement, already satisfied (2026-07-25):** `rankings` stores `spread_sd`,
`rank_best` and `rank_worst` per source per `as_of_date`, alongside the point estimate.
VONA needs `P(player survives to pick 23)`, which requires a *distribution* over where the
room may take a player. A collapsed consensus point estimate makes that probability
permanently unrecoverable for that date — no later analysis can reconstruct dispersion that
was never stored. Any future ADP source must be ingested the same way: **per-source rows,
never a pre-blended consensus.**

### P3-2. Date-parametrised board refresh with injury and news status

The board must be rebuildable as of any date, not only "now": `board(as_of=2026-08-28)`
should reflect only what was known then. Two dependencies:

- Consensus snapshots are already dated and stored per `as_of_date`, so the ranking side
  works today.
- Injury status is **not** yet captured with an `as_of_date`. `load_injuries` covers
  2009-2025 (docs/data-availability.md §1) but is not ingested. Without dated injury
  snapshots, any historical board rebuild silently uses final-season injury knowledge —
  textbook look-ahead (CLAUDE.md §6.1).

Also blocking: `load_depth_charts` **ends at 2024**, so depth-chart role is unavailable for
the 2026 draft from this source entirely.

### P3-3. Pick-gap-aware urgency for the 3/18/23 slot sequence

From slot 3 in a 10-team snake, picks fall at 3, 18, 23, 38, 43, ... The gaps alternate
wildly: 15 picks between 3 and 18, then 5 between 18 and 23. Urgency at a 15-pick gap is
roughly 3x that at a 5-pick gap — a player you can plausibly get at 23 is not worth
reaching for at 18, while a run-prone position at pick 3 must be addressed because 15 picks
will pass.

This is test-registry.md #36. It depends on P3-1 (survival probabilities) and on modelling
opponent behaviour, which is currently unmodelled — every backtest assumes opponents draft
to ADP with noise (test-registry.md "Known gaps" #1).

### P3-4 (implied). Draft simulation as the evaluation metric

Recorded here because Tasks 9's metrics still cannot answer it. `starter_vbd` is sensitive
to cross-positional ordering but assumes you receive your top-K uncontested. Neither it nor
`vbd_sum` models opponents, scarcity, or pick timing, so no current metric can evaluate a
strategy whose entire effect is *when* a player is taken (Hero RB, Zero RB — test-registry
#44). A real draft simulation is the missing evaluation layer.

### FantasyPros API — probed 2026-07-25, not built against

`.env` exists with `FANTASYPROS_API_KEY`. Live probe (not a build) against
`api.fantasypros.com/public/v2/json/nfl/{season}/{projections,consensus-rankings}`.

**Component projections ARE present.** `projections` returns `pass_yds`/`pass_tds`/
`pass_ints`/`rush_yds`/`rush_tds`/`rec_rec` (receptions)/`rec_yds`/`rec_tds`, plus
bonus-threshold flags matching this league's scoring shape almost exactly
(`pass_yds_300`/`pass_yds_400`, `rush_yds_100`/`rush_yds_200`, `scrimage_yards_100`/`_200`).
`mflid` is returned per player — a direct crosswalk to the ADR-036 hub, no name matching.
This is real, in principle, test-registry #2 material.

**The free tier caps every response at the top 10 players, with no working pagination.**
`limit: 10`, `public_api_limited: true`, `tier: "free"` on every response. `count` reports
the true total (598 for all-position projections, 580 for consensus-rankings) but `players`
is truncated to 10 regardless. Tried `offset`/`page`/`start` query params — all silently
ignored, all returned the identical top-10 players. **This is the load-bearing finding: the
free tier cannot deliver full-board coverage of anything.** At best, four position-filtered
calls (`position=QB/RB/WR/TE`) would surface the top 10 *per position* — 40 players — and
those are almost certainly already inside the 145 players the existing rank-to-points curve
covers. It does not reach the 233 players currently without a displayable projection, which
are specifically the ones *outside* consensus-rank depth. **Unblocking #2 for the players
that actually need it requires a paid tier**, not just a key.

**ADP is filterable to half-PPR, and it is genuinely separate from ECR.** `type=ADP&scoring=HALF`
returns a distinct dataset from `type=ST&scoring=HALF`: different `rank_ave`/`rank_std`/count,
and critically **`total_experts=3`** (vs 92 for the ECR/consensus type) — this is FantasyPros'
own small ADP composite, likely 3 draft-tracking sites, not their full analyst panel. Same
"thin sample" caveat as MFL's `totalDrafts=50` (ADR-035) applies here if it is ever ingested:
worth having, not worth weighting heavily without measurement.

**Historical seasons are queryable** (2023 tested successfully, 105 QB rows reported), subject
to the same 10-row-per-call cap.

**No rate-limit telemetry beyond the per-call cap.** No `X-RateLimit-*` headers, no quota
field in the body. Whether there is also a daily/monthly call quota on top of the per-call
truncation was not tested — that would require deliberately exhausting it, which this probe
did not do (roughly a dozen calls total).

**Next step if this becomes a priority:** either accept 40-player top-tier coverage as a
partial answer to #2, or price FantasyPros' paid API tier. Nothing was built against this
tier — per instruction, report only.

## Per-pick mock draft state logging (2026-07-26, ADR-045)

`live_availability.py`'s positional-run term `R(p)` ships with an unvalidated prior
(`delta=0.10`) because validating it (SS5(b) of `live_availability_adjustment.md`) needs mock
drafts with the FULL draft state recorded at every pick, not just the final board. The current
`mock_drafts`/`mock_picks` schema (ADR-042) logs only the final sequence of picks — sufficient
for Level 1/2/Tertiary calibration and the Brier-vs-baseline test, but not for reconstructing
what the model would have predicted for `R(p)` at each historical pick, which needs the room's
state (who was gone, what each team had drafted) at that exact moment.

**Like P3-1's ADP dispersion requirement, this is cheap to add now and unrecoverable later**: a
mock draft that already happened without per-pick state logged cannot have that state
reconstructed after the fact. Deliberately NOT added this session (explicit instruction — the
mock schema is otherwise fixed to what the front end exports, ADR-042, and a schema addition
needs its own decision, not a side effect of an unrelated feature).

**Next step if this becomes a priority:** decide the per-pick state shape (likely: drafted
counts per team, or the raw ordered pick list up to that point, from which counts are derived)
and add it as an optional field to `mock_picks`/`mock_drafts`, same migration pattern ADR-043
used for `drafter_type` (`ALTER TABLE ADD COLUMN`, not a rebuild — mock data already logged must
survive the change).
