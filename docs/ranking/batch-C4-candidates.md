# Factor batch C4 — candidate definitions (not registered, not run)

**backend, 2026-08-04.** Definitions only, per this batch's dispatch. **Nothing in this file has been
fitted, graded, or registered into the campaign manifest** — that is `ranker`'s call, at the point one
of these is actually about to be tested.

---

## 0. Interface state — this session, unlike C3's, had the real interface

This worktree branched from `2aa14ec` (ADR-069) and did **not** contain `factors_c1.py`/
`factors_c2.py`/`factors_c3.py` on disk — same situation `factors_c3.py`'s own NEXT STEP block
describes for its own session. The difference here: those files exist on `origin/claude/pm-agent-
setup-gobxa0` (tip `81cf84e`, "sweep070: VERIFY gate PASS"), which has not merged to `main`. That
branch was **merged into this worktree** (`git merge origin/claude/pm-agent-setup-gobxa0 --no-edit`,
plain non-destructive merge, no rebase, no force) before writing a line of `factors_c4.py`, so this
batch is written against the **real, current** C1/C2/C3 interface, not a reconstruction. Verified
after merging: `factors_c1.py`, `factors_c2.py`, `factors_c3.py`, `factors_c3_adapter.py`,
`docs/ranking/adr070-tier2-execution.md`, `docs/ranking/factor-campaign-manifest/batch-C3.md` are all
present and were read first.

**`factors_c4.py` follows `factors_c3.py`'s shape**, not `factors_c1.py`/`factors_c2.py`'s arm-
registry shape — the dispatch names C3 as "the interface contract and the pattern to follow," and
C3's own header explains why: registration/arm-wiring happens at *fit* time, owned by `ranker`
(`factors_c3_adapter.py` is that reconciliation step for C3; the same is expected for C4 and is
**not** done here, per the dispatch — "Do not register into the campaign manifest").

**Not touched, by this batch or by the merge that preceded it:** `experiments/bottomup/results/
sweep070/`, `factors_c1.py`, `factors_c2.py`, `factors_c3.py`, `factors_c3_adapter.py`, any
campaign-manifest file. The merge brought those paths into this worktree's git history as
already-committed `ranker` content; none of them was edited.

**All six loaders and `attach_*` functions were smoke-tested against the real `data/nfl.db`** (copied
into this worktree per `docs/environment.md` §4, never hardlinked) — a 39–40-player spot check for
2022 confirmed every block runs end to end, the holdout gate raises `HoldoutViolation` at cutoff=2025
and passes cleanly at cutoff=2024, and produces plausible values, with one caveat flagged at Factor K
below (`is_contract_year` rate higher than a naive prior — not resolved here, flagged for the fitter).
This is a runtime smoke test, not a unit-test file and not a fit; no number below has been measured
for predictive power.

---

## 1. Scope: what is covered elsewhere, and what was dropped and why

C1 covers F0–F6 (placebo, snap share, red-zone usage, xFP, NGS separation, routes, steep recency).
C2 covers A1–A5/B1 (WOPR, YAC, receiving points share, late-season role, implied team total, RB
high-carry hinge). C3 covers C–H (injury burden, practice severity, depth-chart end rank, combine
composite, neutral pass rate, efficiency-over-expected). None of the six factors below duplicate any
of those.

**Ledger rows this batch resolves into factors I–N:**

| ledger row(s) | factor | why in scope |
|---|---|---|
| T1-13 | I — target-share stability | `rejected-with-evidence` under the **old** consensus-derived frame; Section 0 of the ledger reclassifies that as untested for v2 |
| T1-21 | J — team pace | `blocked` in the ledger for "no PBP table" — that gate is stale, `pbp` (2009+) is now ingested and used by C1/C3 already |
| T1-27 | K — contract-year status | `untested`, tag confirmed correct (`[VERIFIED]`) by the external sweep, never run |
| T1-29b | L — head-coach continuity (as a lag-season disruption signal, not a target-season forecast) | `untested`, buildable-today per the ledger's own note |
| T1-23 / N27 | M — O-line run-blocking quality (single-stat, not full ALY) | `untested`, formula-availability correction applied 2026-07-30; simplified deliberately, see Factor M |
| T1-31 / N25 | N — two-WR (heavy) personnel rate | `untested`, buildable via `participation.offense_personnel`, 2016+ |

**Considered, dropped before writing** (a weak candidate is not free — recorded, not silently
omitted; **9 ledger rows** touched by this triage, none resurrected):

| ledger row(s) | reason dropped |
|---|---|
| N1, N2, N6 | Gated on FTN charting columns starting 2022 only. First lag-available target season is 2023 — S≤2 inside the tier-2 window, too shallow to register a serious arm against. |
| N4 | Buildable (`pbp` first-downs × `participation` routes), but is an arithmetic variant one step from C1's F5 (routes/TPRR), which already ran and returned NULL at all three skill positions. Re-registering a near-duplicate of an already-NULL construct taxes the campaign's `M` for a construct that already had its shot. |
| T1-19, T1-20 | Not new factors — both are ablations of features **already in** the base v2 spec (own TD rate, team-relative touch share). Re-registering an existing input as a "candidate" is out of scope for a new-factor batch. |
| T1-14, T1-25 | Same reason — already base-spec features (`adot_num`/`adot_den`; `draft_round`/`draft_pick`/`log_draft_pick`/`undrafted`). |
| T1-26 | No college-level usage/target-share data exists anywhere in `nfl.db` (checked: no `college_stats`-equivalent table across the 39-table schema). Genuinely blocked on data availability — stands, not resurrected. |
| T1-28 | The old result is a **proxy-contamination finding**, not a clean NULL. `rosters_weekly` now exists (the fix the ledger names), which makes this a real candidate — but building the join correctly (mid-season vs. preseason status, multi-team players) is substantial enough that folding it in here risks reproducing the same contamination under a new name. Flagged for `ranker`/`strategist` to schedule as its own batch, not defined in this one. |
| T1-29, T1-30 | Still genuinely `blocked` — `play_callers_preseason` exists as a table but the ledger records 0 rows landed from PFR (403); not re-verified this session since it is a data-availability disposition, which stands. Factor L is the *different*, already-flagged T1-29b proxy, explicitly not a substitute. |
| N29, N30 | Functional-form hypotheses about how to use *existing* features (a threshold gate; a realised-outcome oracle bound), not new input columns — out of scope for a factor-definitions batch. |
| N32, N33 | Games-channel work — explicitly the availability model's territory per `CLAUDE.md` §2 ("distinct from *draft* availability... do not conflate them"), out of scope for a ranking-factor batch. |
| N34 | Superseded by C3's Factor F, which already built a simpler position-relative z-score composite over `combine` rather than reproduce an unvalidated external formula — carried forward, not re-litigated. |

**Two more ledger dispositions checked and correctly left alone, same "data-availability/licensing
stands" rule C3 applied to odds/PROE:** T0-11/N12 (Vegas odds — C3 already flagged this tension and
did not resolve it; this batch doesn't either) and T1-22 (PROE — C3 explicitly chose N20, neutral
pass rate, instead; already covered by C3's Factor G).

---

## 2. Grading window and truncation, per factor

Grading is declared at **S=12, tier 2 (2013–2024)**, per-position, per `docs/ranking/
adr070-tier2-execution.md` D1 (QB/RB targets 2013–2024, S=12; WR/TE targets 2014–2024, S=11 — the
targets-hole constraint). **Three factors truncate the window and need their own matched control**,
same discipline as C1's CTRL-B/C and C3's T2-I/T2-P families — never differenced against the
full-window cells:

| factor | source floor | first usable target season | truncates? |
|---|---|---|---|
| I — target-share stability | 2009 | 2010 | **no** — full S=12/S=11 coverage |
| J — team pace | 2009 | 2010 | **no** — full S=12/S=11 coverage |
| K — contract-year status | 2011 (judgment call, density-based — see Factor K) | 2012 | no truncation of target range, but early cells (2013–2015) will have visibly thinner `contract_known` coverage than 2018+ — report per-cell, don't assume flat |
| L — coaching disruption | 1999 | 2001 | **no** — full S=12/S=11 coverage |
| M — O-line YBC/carry | 2018 (`pfr_advstats_rush`'s own floor) | 2019 | **yes** — RB target range 2019–2024, S_pos = 6 |
| N — two-WR personnel rate | 2016 (`participation`'s own floor) | 2017 | **yes** — target range 2017–2024, S_pos = 8 |

---

## 3. Factor definitions

### I — Target-share stability (persistence, not level)

- **Mechanism.** The base spec already carries the lag-weighted *level* of target share (`tshare_w`,
  T0-8, included). This factor is orthogonal: a player whose share has been *consistent* across his
  last two or three seasons is a more reliable bet to repeat it than a player at the identical
  average level whose share swung season to season. T1-13's old result tested whether stability
  improves fit to a share *target*, not whether raw share matters — the framing carries over
  unchanged: added alongside the level feature, not instead of it.
- **Scope.** WR/TE only. RB receiving role is already captured jointly by `cshare_w`/`tshare_w` in
  the base spec, and RB target share behaves differently at low absolute volumes — conflating the
  two would average over two different processes. A parallel RB-scoped version is a natural
  follow-up, not registered here.
- **Construction.** Inverse of the lag-weighted coefficient of variation of `target_share` across up
  to 3 prior seasons, empirical-Bayes shrunk (k0=2.0 seasons, fixed a priori) toward the pooled mean
  CV. Higher = more stable. `tshare_stability_known` requires ≥2 valid lag seasons — a CV needs at
  least two points; one lag season is coded unknown, same as zero.
- **Source.** `player_weekly_stats.target_share`, per (player, season) via a games-weighted mean of
  the weekly column. Measured floor: 100% populated WR/TE/RB from 2009 (0 nulls; 2008 has 145 of
  4,517, i.e. not real coverage).
- **Columns.** `tshare_stability_prior`, `tshare_stability_known`.

### J — Team pace (plays per game)

- **Mechanism.** An offense that runs more plays per game hands out more total opportunity (targets +
  carries + attempts) to every skill player on it, as a pure environment multiplier orthogonal to
  *who* gets the opportunity or *how* it's called. Distinct from C3's Factor G (neutral pass *rate*,
  a play-calling frequency) and C2's implied team total (points environment) — pace is volume of
  snaps, independent of both.
- **Source.** `pbp`, rows where `posteam` is real and `pass_attempt=1` or `rush_attempt=1` (same
  scrimmage-play definition C1's red-zone-usage factor uses), REG season only via `season_length`.
  Measured floor: `season`/`week`/`posteam` present from 2009.
- **Control.** `pace_known` = 1 iff the lag team-season recorded ≥8 games (guards against strike-year
  or franchise-move artifacts). Team-level; requires the caller to resolve a per-lag `team` column,
  enforced with an explicit `ValueError`.
- **Columns.** `pace_prior_w`, `pace_known`.

### K — Contract-year status

- **Mechanism.** A player entering the final year of his current contract carries a
  behavioral-incentive signal orthogonal to lag production — direct financial incentive to maximize
  a walk-year performance, and a team-side role-allocation incentive of its own (showcase for trade
  value, or bench a declining vet rather than pay a dead-cap hit). Sign not asserted a priori; this
  factor supplies the indicator only.
- **Look-ahead discipline, stated explicitly.** A contract's `year_signed` is a real calendar event
  (free-agency signings happen March–August, well before Week 1) and is knowable pre-draft in the
  year it is signed — unlike Week-1 roster status, which is dated *after* the draft. This factor
  therefore allows `year_signed ≤ target_season` (not `<`), the one place in this batch a
  same-calendar-year read is legitimate, flagged in the code so it doesn't read as an off-by-one
  against the rest of the file's `< target_season` convention.
- **Construction.** Per player, the most recent contract with `year_signed ≤ target_season`.
  `contract_end = year_signed + years − 1`. `is_contract_year = 1` iff `target_season == contract_end`.
  `contract_years_left = contract_end − target_season` (can be negative for an unrenewed expired
  deal still on file — a real state, not an error).
- **Source.** `contracts`, crosswalked `gsis_id` (91,945 of 100,224 rows, ~92%). Measured floor:
  thin before 2011 (783 rows at `year_signed=2011`), denser from 2016+ (4,137+). `CONTRACTS_FIRST =
  2011` is a **density-based judgment call, flagged as such, not a measured breakpoint.**
- **Smoke caveat, measured not assumed.** A 39-player spot check (2022, WR/TE/RB/QB) put
  `is_contract_year` at **62%** — high against a naive prior. The merge/filter/"most recent as of
  target season" logic was hand-checked against sample rows and reproduces the intended behaviour;
  two real (not construction-bug) mechanisms plausibly explain it — high one-year "futures"/prove-it
  deal turnover among backup-tier players, and possible under-representation of restructures in
  `contracts`. **Flagged for whoever fits this arm to re-check on the full graded population before
  trusting the rate at face value — not resolved here.**
- **Control.** `contract_known` = 1 iff a contract row satisfies the filter.
- **Columns.** `is_contract_year`, `contract_years_left`, `contract_known`.

### L — Prior-season coaching disruption

- **Mechanism.** **Not** a forecast of whether the player's team changes coaches in the target season
  (that needs a hire that may happen in the target season's own January/February offseason — legal
  pre-draft information but awkward to gate cleanly against this file's lag-only convention).
  Instead: was the *lag season's own production* generated under a first-year coach or an established
  multi-year system? A confidence weight on the lag stats themselves, not a target-season forecast —
  sidesteps the look-ahead question C3's Factor E flagged for Week-1 depth charts entirely, since
  nothing here is dated later than the end of the lag season.
- **T1-29b, explicitly**, named in the ledger as "a genuinely different hypothesis from #29/#30, not
  a substitute for them" (coordinator/OC continuity, both still `blocked`). This factor is
  head-**coach** continuity only, and is not represented anywhere as evidence about coordinator-level
  effects.
- **Source.** `schedules.home_coach`/`away_coach`, 1999–2026, 100% populated (7,548/7,548 checked).
  Team-season coach resolved as the plurality coach across that team's REG games (handles a rare
  in-season interim switch without reading Week-1 as final). Change reading requires two
  *consecutive* resolved team-seasons — a gap (relocation, missing data) reads unknown, never
  silently as continuity.
- **Control.** `hc_disruption_known` = 1 iff both the lag season and its immediate predecessor
  resolved for that team.
- **Columns.** `hc_disruption_prior1`, `hc_disruption_known` (lag-1 only — a transition reading is
  about one specific season, not something to recency-weight across three lags).

### M — O-line run-blocking quality (yards before contact / carry)

- **Mechanism.** RB rushing efficiency is bounded by how much room the line creates before contact.
  Team-level `pfr_advstats_rush.rushing_yards_before_contact_avg`, carries-weighted across every
  carry the team ran (not one back), isolates O-line contribution net of any single runner's talent
  — a persistence-worthy environment prior for a returning or newly-arrived RB, distinct from the
  runner's own lag efficiency (already in the base spec) and from Factor J's pace.
- **Deliberately not the full Adjusted Line Yards composite** the ledger names at T1-23/N27 (which
  blends YBC with broken-tackle rate, pressure allowed, opponent adjustment into one published
  formula). This is the single cleanest slice of it — team YBC/carry alone — both because ALY's exact
  weighting hasn't been validated in this project (same "enter with no prior" caution the ledger
  applies to combine-derived composites at N34) and because one clean single-stat factor is one arm,
  not five unvalidated sub-choices bundled as "one change."
- **Scope.** RB only — the mechanism is specifically ground-game blocking.
- **Source.** `pfr_advstats_rush`, team-season aggregate. Measured floor: table's own coverage starts
  2018 (18,461 rows, `MIN(season)=2018`). **Truncates the window** — RB target range 2019–2024,
  S_pos = 6, needs its own matched control, never differenced against full-window cells.
- **Control.** `ol_ybc_known` = 1 iff the lag team-season recorded ≥150 aggregate carries.
- **Columns.** `ol_ybc_prior_w`, `ol_ybc_known`.

### N — Two-WR (heavy) personnel rate

- **Mechanism.** A team's rate of lining up with exactly two WRs (vs. 3+ "spread" sets) is a
  snap-level statement of offensive identity, structurally capping how much target volume can reach
  a WR3/4 and routing more of it to the extra RB/TE/FB on the field. Distinct from C3's Factor G
  (neutral pass *rate*, a play-calling frequency) — this is about who's on the field, not what's
  called once they're there. N25 in the ledger cites the WR-side receiver effect (+29% PPR/route in
  2-WR vs. 3-WR); this factor is the buildable team-level rate behind that number, not the
  receiver-level effect itself.
- **Construction.** `participation.offense_personnel` is free text (`"1 RB, 1 TE, 3 WR"`, sometimes
  with defensive-substitution suffixes). Parsed via `(\d+)\s*WR` regex against every non-empty value;
  empties dropped as unparseable rather than assumed. `two_wr_rate` = share of a team-season's
  charted snaps with exactly 2 WR on the field.
- **Source.** `participation`. Measured floor `MIN(season)=2016` (478,989 rows, 2016–2025).
  **Truncates the window** — target range 2017–2024, S_pos = 8 at every position, needs its own
  matched control.
- **Control.** `two_wr_known` = 1 iff the lag team-season recorded ≥300 charted snaps.
- **Columns.** `two_wr_rate_prior_w`, `two_wr_known`.

---

## 4. What was NOT done in this pass

- No factor was registered into `docs/ranking/factor-campaign-manifest/` — `ranker`'s call, at fit
  time, per the dispatch.
- No factor was run, fit, or graded. §0's smoke test confirms the code executes against real data
  (including a correct `HoldoutViolation` at cutoff=2025) and produces plausible values — not
  evidence of predictive power.
- No ADR was opened — this batch adds no new decision, only candidate definitions.
- `factors_c1.py`/`factors_c2.py`/`factors_c3.py`/`factors_c3_adapter.py`, `docs/ranking/
  batch-C1-results.md`/`batch-C2-results.md`, and `experiments/bottomup/results/sweep070/` were not
  touched — read only, to build against the real interface.
