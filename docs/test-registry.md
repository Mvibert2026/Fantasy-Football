# Test Registry

Every factor or question that could move our rankings, tiered from table stakes to speculative.

**League context:** 10-team, 0.5 PPR with stacking yardage bonuses, 3WR/2RB/1TE/2FLEX/1QB/1DEF,
6 bench + 1 IR, no kicker, 4-of-10 playoff (Wks 16–17, no reseed), $100 FAAB, Nov 28 trade
deadline, snake draft, 2026 slot 3.

**Status key**
- `PORT` — working code exists from prior exploratory sessions; needs porting + verification
- `SPEC` — designed, not built
- `NEW` — identified, not yet designed
- `BLOCKED` — waiting on a data source

**Effort:** L / M / H · **Edge:** differentiation vs. a well-informed opponent

> **Status was re-baselined on import.** Items previously marked DONE were built in an ephemeral
> analysis sandbox, not in this codebase. Nothing is DONE here until it is in the repo, covered by
> tests, and past Verifier. `PORT` means the thinking is proven and the code is a starting point —
> not that the work is finished.

---

## Data source legend

| Tag | Source | Notes |
|---|---|---|
| `nflverse` | `nflreadpy` / `nfl_data_py` | Free, no login, PBP back to 1999 |
| `nflverse:FTN` | FTN charting subset inside nflverse | **2022+ only.** CC-BY-SA, attribution required. Check columns before proxying anything. |
| `adp` | Per-site scrapes: FFC, Yahoo, ESPN, Sleeper, Underdog | No unified API; each needs `as_of_date` |
| `odds` | Vegas source, TBD | Benchmark accuracy across candidates before selecting |
| `pfr` | Pro Football Reference | Coaching histories; check terms before scraping |
| `league` | Yahoo league data (API blocked) or manual entry | See §Blockers |
| `derived` | Computed from other sources | No new ingestion |
| `manual` | Hand-encoded | One-time human input |

---

## Tier 0 — Table stakes

Everyone has these. Not having them is a loss; having them is not an edge.

| # | Test | Why | Source | Effort | Edge | Status |
|---|---|---|---|---|---|---|
| 1 | Multi-source ADP | Baseline market price | `adp` | L | None | SPEC |
| 2 | Consensus projections | Baseline value | `adp` / FantasyPros | L | None | BLOCKED — needs **component-level** projections, not fantasy points |
| 3 | Positional tiers | Draft-day decision units | `derived` | L | None | SPEC |
| 4 | Bye weeks | Roster legality | `nflverse` | L | None | SPEC |
| 5 | Depth chart / role | Opportunity | `nflverse` | L | None | SPEC |
| 6 | Injury designations & status | Availability | `nflverse` | L | None | SPEC |
| 7 | Age | Decline curves | `nflverse` | L | None | SPEC |
| 8 | Prior-year target / touch share | Opportunity baseline | `nflverse` | L | None | SPEC |
| 9 | Snap share | Role confirmation | `nflverse` | L | None | SPEC |
| 10 | Red-zone / goal-line usage | TD equity | `nflverse` | L | Low | SPEC |
| 11 | Vegas win totals & implied team totals | Offensive environment | `odds` | L | Low | NEW |
| 12 | Season-long strength of schedule | — | `nflverse` | L | **~Zero** | SPEC |

**On #12:** SOS is largely non-actionable for drafts — defenses shift year over year and the worst
units get the most offseason investment. **Weight near zero.** Retained only so we can say we
checked, and so the finding is reproducible rather than asserted.

**On #2 — this is the single biggest external blocker.** Fantasy points from any public source are
in *someone else's* scoring format and useless to us. We need pass yards, rush yards, receptions,
and TDs as separate components so the engine can re-score under our rules. This blocks rankings,
tiers, and league-ADP simultaneously.

---

## Tier 1 — Standard analytics

What a serious, well-read opponent has. Table stakes among the sharpest 2–3 managers in the league.

| # | Test | Why | Source | Effort | Edge | Status | **Measured verdict** |
|---|---|---|---|---|---|---|---|
| 13 | Target share **stability** YoY | Separates real role from one-year noise | `nflverse` | M | Med | SPEC | **NULL** — S1 stability arm: −0.035 targets MAE full universe (BH-sig at WR only), **0.02% on the ADP board**, no ranking effect anywhere. YoY persistence of target share measured: WR +0.652 [+0.624,+0.680], TE +0.632, RB +0.548 — role-tier, just below snap share +0.707. `factor-batch-1-results.md` |
| 14 | Air yards, aDOT | Big-play vs. volume profile | `nflverse` | M | Med | NEW | — (not run) |
| 15 | WOPR | Best single opportunity metric for WR | `derived` | M | Med | NEW | — (not run) |
| 16 | Yards per route run | Efficiency independent of volume | `load_participation()` (2016+), **confirmed: FTN cannot supply it** | M | Med | RUN | **NULL — and the route block's whole content is a coverage flag.** Batch 5 ran the per-route family (TPRR, routes/game, 1D/RR) at WR/TE/RB over 7 target seasons. Nothing BH-significant at the campaign denominator or the batch one; largest effect 0.80% of primary error. **8 of 8 treatment cells graded VOID — COVERAGE ARTIFACT**: the bare `routes_known` flag alone beats every feature built on it (WR 4.1×/3.7×/19.7×, TE 3.2×/1.06×/7.1×, RB 2.7×/1.3×). E1b confirms independently — route arms are **worse** on the ADP board (TE routes/game **+1.59** targets MAE) while neutral on the full universe, the signature of "is this an NFL pass-catcher" rather than a rate. `factor-batch-5-results.md` §1–2 |
| 17 | Route participation rate | Distinguishes starters from rotational | `load_participation()` (2016+) | M | High | RUN | **NULL, same family as #16.** The row's own rationale — "distinguishes starters from rotational" — is exactly what the measurement found, and it is the problem rather than the edge: the model already knows who the starters are. Descriptively (F3, outside the family), TPRR reaches ρ=+0.476 to next-season FPG on a survivor-filtered WR population against **prior FPG's +0.612 on the same rows** — below the incumbent, and 4for4's published ordering YPRR (0.535) > 1D/RR (0.528) > TPRR (0.476) replicates exactly. **Per the pre-commitment's stopping condition, do not re-specify a third time on the grounds the sample was short** — 7 target seasons off a 10-season source is what the corrected tag buys. `factor-batch-5-results.md` §2–3 |
| 18 | **Expected fantasy points (xFP) vs. actual** | Isolates luck from skill | `derived` (`nflreadpy.load_ff_opportunity()`, prebuilt) | L | **High** | NEW | — (not run) |
| 19 | TD-rate regression | Best-known regression signal | `derived` | M | **High** | SPEC | **HARMFUL as framed / already solved** — discarding own TD rate for the pooled mean (arm T2) is worse at **all four positions**: WR +0.0251, TE +0.0180, RB +0.0182, **QB +0.2295 pass TDs MAE**. Existing empirical-Bayes shrinkage already extracts the signal; a volume-conditional prior adds 0.8% full-universe and **nothing on the ADP board**. `factor-batch-1-results.md` |
| 20 | Opportunity share (carries+targets / team total) | Single best RB metric | `nflverse` | M | High | SPEC | **NULL at RB** — the position the row names. Ablating carry share costs −0.017 carries MAE [−0.050,+0.003]; share×pace reparameterisation −0.086 [−0.272,+0.068]. **At WR share does earn its place**: removing it costs +0.196 targets MAE on the ADP board (+0.6%). `factor-batch-1-results.md` |
| 21 | Team pace / plays per game | Volume multiplier | `nflverse` | M | Med | NEW | — (not run) |
| 22 | Pass rate over expectation (PROE) | Scheme tilt | `nflverse` | M | Med | NEW | — (not run) |
| 23 | O-line run-block & pass-block rankings | RB efficiency, QB time | `derived` (Adjusted Line Yards, public formula over PBP) / `nflverse` (`load_pfr_advstats()`, 2018+) | L | Med | SPEC | — (not run) |
| 24 | QB quality for pass catchers | Ceiling constraint | `derived` | L | Med | SPEC | — (not run) |
| 25 | NFL draft capital (rookies) | Best rookie predictor | `nflverse` | L | Med | SPEC | — (not run) |
| 26 | Breakout age / college dominator | Rookie projection | external | M | Med | NEW | — (not run) |
| 27 | Contract year / free-agency status | Motivation & usage | `nflverse` (contracts) | L | Low | NEW | — (not run) |
| 28 | Vacated targets & carries | Where opportunity actually opened | `derived` | M | High | SPEC | **NULL — re-tested on REAL pre-season rosters, 2026-07-30. The batch-1 HARM was a proxy artifact, confirmed directly.** Same harness, `rosters_weekly` instead of the Week-1 depth chart: RB **+0.203 → −0.012**, paired **V2−V1 = −0.2154 [−0.3003,−0.1384], p=0.0006**; TE +0.045 → +0.015; WR +0.082 → +0.028. In the high-vacancy bucket the RB harm goes +0.770 → +0.064 (92% gone), which is the mechanism batch 1 predicted. **But all three are NULL** — as are the two further constructions (V3 absence share; V4 player-level opportunity-vacated-*above*-this-player). Nine cells, zero wins. `factor-batch-2-results.md` |
| 29 | Coordinator continuity | High OC turnover league-wide | `wikipedia` (was `pfr`) | L | ~~High~~ **DEAD** | **CLOSED 2026-07-30** | **DEAD ON BOTH SPECIFICATIONS — do not re-specify a third time.** Batch 3 added the two arms batch 2 could not: *change at QB* (C1Q −0.0660, p=0.274, NULL) and *tenure*, the founder's own correction, at four positions (QB −0.2427 p=0.106 · WR +0.0140 p=0.179 · TE −0.1227 p=0.052 · RB +0.0492 p=0.244 — **nothing clears BH at campaign m=24**). QB tenure is the best number in the family and its own registered control arm is **46% of it**, a rounding error from the pre-declared VOID threshold. **Seven arms, two batches, two specifications, one model, nothing.** Source floor measured at 2010 (Wikipedia staff navboxes do not exist earlier; 96/192 team-seasons empty 2004–2009), censoring 3.1%, so the nulls are not artefacts of a truncated source. `factor-batch-3-results.md`. Batch 2's original finding, retained: **UNGATED 2026-07-30, then NULL.** `play_callers_preseason` (pre-Week-1 Wikipedia navbox revisions, 2012–2024, all 32 clubs, 803 OC+DC rows) gives `oc_known` **0.995/0.992/0.997** on the ADP board. "This player's club has a new OC": WR −0.006 (p=0.71), TE −0.003 (p=0.87), RB +0.093 (p=0.29) — **all NULL, and E1b positive at all three**, i.e. slightly worse where drafts happen. **Not underpowered: the OC changes for 46–48% of board player-seasons.** `factor-batch-2-results.md` |
| 30 | First-time play-callers | Week-to-week volatility | `wikipedia` (was `pfr`) | L | Med | **NO LONGER GATED** — `play_callers_preseason` carries OC/DC identity and head-coach name per club-season, 2012–2024. Note the ceiling before spending on it: only **17.9%** of OC changes bring in someone who was an OC elsewhere the prior season, so any prior-history signal can reach one change in six | — (not run) |
| 29c | **QB rushing volume as an input to PASSING volume** (new row, batch 3) | A rushing quarterback throws measurably less, and no QB-specific input exists anywhere in the shipped board | `nflverse` (already in `player_weekly_stats`) | L | Med | **MEASURED 2026-07-30** | **PROJECTION-ONLY.** Adding lagged rushing carries/game to the QB attempt-volume spec: **−1.4679 attempts MAE (−1.30%) [−2.276,−0.688], p = 0.0068**, BH-significant at campaign m=24, and better on the ADP board (E1b −3.03). E2 −0.016, so it does not yet improve the ranking. Separately, ABLATING the QB rushing block costs **+1.8065 carries MAE, +14.4% of the position's own error**, all 11 seasons worse — the first ablation of any QB feature in this project. `factor-batch-3-results.md` |
| 29d | **Efficiency offered to the VOLUME channel** (new row, batch 3, post-hoc) | The model fits yards-per-carry and uses it only for the yards channel; nothing connects a back's efficiency to how much work he gets next year | `derived` (already in the model) | **L — a wiring change, no new data** | **High** | **POST-HOC, registered with strategist, NOT RUN confirmatorily** | Lagged YPC added to the RB carry-volume spec: **−0.9331 carries MAE (−1.88%), E1b −0.7200** — better than the registered explosive-rate arm on both endpoints (−0.7508 / −0.0264). **Not a result. A hypothesis with a measurement attached**; it needs a `strategist` registration and a `backend` handoff before it means anything. `factor-batch-3-results.md` §1(1) |
| 29b | Head-coach continuity (separate, weaker candidate) | Cheap proxy, but not what #29/#30 test | `nflverse` (schedules) | L | Low-Med | **NEW** — data available 1999-2026, 100% populated | — (not run) |
| 31 | Personnel package trends | Structural WR3 headwind | `nflverse:FTN` | L | Med | SPEC | — (not run) |
| 32 | Pre-snap motion rates | Largely arbitraged league-wide | `nflverse:FTN` | L | **Low** | SPEC | — (not run) |

**Four cost/source corrections, 2026-07-30 (external analyst sweep,
`docs/research/analyst-factor-sweep-2026-07-30.md` §1, all `[VERIFIED]`). None of these change any
result or edge rating — only the facts about what it costs and where it comes from.**

- **#18 xFP, re-costed `H` → `L`.** It was listed as the "highest-value unbuilt Tier 1 item" at
  effort `H`. `nflreadpy.load_ff_opportunity()` is a free, prebuilt, versioned xgboost xFP model
  over nflverse PBP, 2006–current — a download, not a build.
- **#16 YPRR and #17 route participation, re-tagged `nflverse:FTN` → `load_participation()`,
  2016+.** FTN charting has **no per-player columns at all** — 28 columns, play-level only, no
  receiver ID, no routes-run. It cannot supply either factor. The real source is
  `load_participation()`'s `offense_players` per play, which gives **ten seasons, not four.** The
  wrong tag has been suppressing both tests.
- **#23 O-line, re-tagged `external` → `derived` / `nflverse`.** Adjusted Line Yards is a public
  formula over play-by-play, and `load_pfr_advstats()` (2018+) ships yards-before-contact, broken
  tackles, drops, and pressure/hurry/blitz rates for free — no PFR scrape, no HTTP 403 risk.

**The `Measured verdict` column (added 2026-07-30).** `Status` records whether a factor is *built*.
It has never recorded what a factor turned out to be *worth*, which is the only thing that should
decide whether it goes in the model. The `Edge` column beside it is a **prior written before any
measurement** — where a verdict exists, the verdict supersedes it. Vocabulary:

- **`IN FORMULA`** — measured, positive, **and actually wired into the shipped model.** Nothing in
  this tier carries it and nothing should until a `strategist` registration and a `backend` handoff
  have both happened.
- **SURVIVES / MARGINAL / NULL / HARMFUL / BLOCKED** — as defined in `docs/strategic-insights.md`.
  **BLOCKED means the test ran and could not answer**, which is different from NULL and must not be
  collapsed into it.
- **`— (not run)`** — no measurement exists. Not knowledge. Do not read the `Edge` column as one.

**#18 is the highest-value unbuilt item in this tier.** Expected points from opportunity (target
volume, aDOT, carries, red-zone looks) vs. what a player actually scored separates luck from skill
better than any single stat. Above xFP → regression candidate; below → buy candidate. **It is now
the last untested HIGH-edge `derived` item in Tier 1** — #19, #20 and #28 were run on 2026-07-30 and
none of them survived (`docs/ranking/factor-batch-1-results.md`). Note before building it: #19's
result suggests the model's existing shrinkage already does part of what xFP is meant to do, so the
xFP test should be specified as an *increment over the current component model*, not against a naive
baseline it will beat trivially.

**#29/#30 require the `coach_id` dimension**, not `team_id`. Coordinators change teams; tendency
signal keyed to franchise breaks the moment someone moves.

**#29/#30 UNGATED, 2026-07-30 — this supersedes the two paragraphs below.** PFR is still 403 and
still not the source. The source is **pre-Week-1 revisions of each club's Wikipedia staff navbox**
(`experiments/bottomup/factors/coord_preseason.py` → `play_callers_preseason`). Three things that
were assumed and are now measured:

- **The `coach_id` join works across team moves.** 53 of 126 named OCs (**42.1%**) appear for two or
  more clubs, covering **243 of 400** club-seasons, with **zero** same-season name collisions. Greg
  Roman SF→BUF→BAL→LAC; Nathaniel Hackett BUF→JAX→GB→NYJ.
- **End-of-season staff cannot be used for either test, and the reason is not staleness.**
  `play_callers` stores `{{NFL final staff}}`, which for a club that fired its OC in November names
  the *replacement* — and the firing is caused by the season going badly, so the contamination points
  the **same way as the hypothesis**. Two tables, two questions; they must not be merged.
- **#29 itself is now NULL** (see the row above). #30 is unblocked but unrun, and its ceiling is
  17.9% of changes.

**#29/#30 status correction (2026-07-25).** `load_schedules` carries `home_coach`/`away_coach`
(1999-2026, 100% populated, 177 coaches) and this was briefly noted as a partial substitute.
**It is not one.** The premise of both tests is that *coordinators move between teams* and the
tendency signal follows the person. Head coach is a different, coarser variable: it misses
every OC/DC change under a retained head coach, which is the majority of coordinator turnover
and the exact case these tests exist to catch. Both remain **gated on coordinator-level data**,
which is unobtainable — Pro Football Reference returns HTTP 403 on both `robots.txt` and its
terms page, so no scraper was built (CLAUDE.md §10, `data-availability.md` §7.9).

Head-coach continuity is logged separately as **#29b**: cheap, buildable today, and a genuinely
different hypothesis. It should not be reported as evidence for or against #29/#30.

**#67 is NOT ADP-blocked (2026-07-25 correction).** It was tagged `adp`, but the test — where
has consensus been *systematically* wrong — runs against expert consensus, which we have for
2021-2025. The residuals from ADR-016's log-linear rank→points fits (R² 0.158-0.266, residual
SD 46-91 points) **are** the consensus errors, already computed. Reclassified `derived` and
**PARTIAL / runnable now**, bounded by the 5-season consensus window (4 after the holdout) and
by the fact that it measures expert-consensus error, not market-ADP error. Those are different
quantities and the distinction must be stated in any result.

**#16/#17/#31/#32 are FTN-dependent and therefore 2022+ only.** That is 4 seasons — small. Treat
any finding here as provisional and flag the sample size in results. Do not let a 4-season factor
carry the same weight as a 20-season one.

---

## Tier 2 — League-specific (our structural edge)

Nobody else does these, because they only matter in *our* league.

| # | Test | Why | Source | Effort | Edge | Status |
|---|---|---|---|---|---|---|
| 33 | Re-score all projections under exact rules | Public half-PPR lists model neither our bonuses nor −2 INT | `derived` | M | **High** | **PARTIAL (2026-07-25)** — positional re-weighting done (`src/make_board.py`); player-level re-scoring still blocked by #2 |
| 34 | Replacement levels: RB30 / WR40 / TE10 / QB10 | Published VBD assumes 12-team RB24/WR36 | `derived` | L | **High** | **DONE (2026-07-25)** — `ReplacementLevels()` derived, used unmodified by board + backtest. Revised from RB28/WR41/TE11 by measurement (ADR-029); the change is inside measurement noise except TE |
| 35 | Global flex baseline (~80th flex-eligible) | Correct baseline past mandated slots | `derived` | M | ~~**High**~~ **NONE (measured)** | **RUN — NULL (2026-07-30, PR-006).** Global-flex-eligible replacement (one points figure at the 80th-ranked RB/WR/TE, replacing per-position RB30/WR40/TE10) vs. the current scheme, driven through `src/draft_sim.py` unmodified on decisions/realised outcomes, not VBD magnitudes. Season-paired points margin +1.7 [-67.6,+74.8] sigma=10, -6.7 [-51.2,+37.8] sigma=20 — sign flips, both CIs wide around zero, well under the measured simulation noise floor (~8.5 pts at 300 sims/cell; the n=4-season bootstrap is the binding limit, not simulation count). **No change to `scoring.ReplacementLevels` — current per-position scheme (ADR-029) stays in production.** Full design `docs/ranking/valuation-tests-35-36-precommit.md`, registration `docs/preregistration/PR-006-global-flex-baseline.md`. |
| 36 | VONA with pick-gap awareness (5 vs. 14) | Urgency differs ~3× between gap types | `derived` | M | ~~**High**~~ **NONE (measured)** | **RUN — NULL on realised outcome, decision-divergence CONFIRMED (2026-07-30, PR-008).** Real user-slot gaps (3.5x alternation, 14 vs. 4 intervening picks for `USER_SLOT=3`) vs. a gap-blind constant (one-round assumption), same underlying VBD. Realised-points margin -37.2 [-118.8,+36.0] sigma=10, -2.8 [-48.0,+37.1] sigma=20 — NULL, CIs include zero. **But the two arms pick a different full roster in 100% of paired simulated drafts, every one of 8 season x sigma cells** — gap-awareness changes WHICH player almost every time; it does not reliably change whether the resulting roster is better at this sample size. Secondary, consistent-but-uncorrected finding: this VONA formulation (either gap variant) underperforms plain BPA-by-VBD by ~110-125 pts both sigmas (CIs exclude zero, but sign test floors at p=0.125 and neither survives BH) — a caution against shipping VONA reaching under this share-based scarcity estimate, not a confirmed loss. **Not wired into any live strategy.** Full design `docs/ranking/valuation-tests-35-36-precommit.md`, registration `docs/preregistration/PR-008-vona-pick-gap-awareness.md`. |
| 37 | League-biased ADP (format + manager priors) | Yahoo board assumes 2WR/1FLEX/K | `league` + `adp` | H | **High** | SPEC |
| 38 | **Bonus-threshold hit rates** | Who *actually* clears 100/150/200, and how often | `nflverse` | M | ~~**High**~~ **NONE** | **RUN — NULL (2026-07-25, PR-002)**. Volume-adjusted clearance does NOT persist YoY. See below |
| 39 | No-kicker effect on pool depth | One extra skill player per team drafted | `derived` | L | Med | NEW |
| 40 | Post-draft players follow waiver rules | Undrafted pool isn't instantly free — changes Wk 1 FAAB | `manual` | L | Med | NEW |
| 41 | IR restriction (no direct waiver→IR) | Stashing costs a bench spot, not an IR spot | `manual` | L | Med | NEW |
| 42 | Trade deadline Nov 28 (~Wk 12) | Caps the trade-to-improve path | `manual` | L | Low | NEW |

**~~#38 is the most genuinely novel item in this registry.~~ FALSIFIED 2026-07-25 (PR-002).**

The original claim: bonuses stack, a 200-yard game is worth +4.5 on top of base, so *spike-week*
players are worth more than metronomes with identical projected totals — an edge no public
ranking captures.

**The arithmetic was never in doubt. The assumption underneath it was, and it failed.** For the
edge to exist, "clears thresholds more often than volume alone implies" has to be a persistent
player trait. It is not:

| Primary case | YoY residual r | 95% CI (player-clustered) | BH-adjusted p |
|---|---|---|---|
| Receiving 100, WR | **+0.041** | [-0.018, +0.099] | 0.668 |
| Rushing 100, RB | **+0.063** | [-0.001, +0.124] | 0.336 |

36 correlations run, 24 testable, **zero survived Benjamini-Hochberg**. Largest sample in the
project: 26 seasons, 1,541 WR pairs / 404 players. The CI upper bounds cap the effect at ~1% of
explained variance even at their optimistic end — this rules a large effect out rather than
merely failing to find one.

**Consequence: bonus clearance carries no information beyond projected yardage.** There is no
"spike-week player" to identify; project the yards and the bonuses follow mechanically. Any
strategy preferring ceiling-shaped players at equal projected volume has no measured basis.

Two further points from the same run:

- **The 150 and 200 thresholds barely occur.** League-wide there are 18–41 receiving games ≥150
  and **1–8 games ≥200 per season** (2025: one). Twelve of the 36 tests were not testable for
  this reason. The `+1.5 @ 150` and `+2.0 @ 200` bonuses are close to irrelevant to draft
  planning in expectation, separately from persistence.
- **A regime-dependent near-miss, disqualified in advance.** QB passing-300 in 2012–2019 gave
  r = +0.265 (raw p = 0.002) — the strongest result in the pass — but it fails BH (0.072) and
  **reverses to −0.234 in 2020–2024**. Examined alone it would have been written up as a
  finding. PR-002 pre-committed that regime reversal disqualifies.

**What survives:** re-scoring under our exact rules (a *level* correction to projected points,
not a shape signal) and the corrected replacement levels (RB28/WR41/TE11/QB10 vs the published
12-team RB24/WR36). Both real, both modest, neither dependent on #38. Note ADR-016 found the
board's positional re-weighting is **directionally positive (mean +84.6, positive in 3 of 4
seasons) but not statistically established at n=4** — corrected 2026-07-25 per ADR-025, which
retracted an earlier claim that it had "no demonstrated advantage" / reversed sign. Measured on
development seasons, so even these are unproven rather than established.

**#33/#34 note:** the ported scoring engine treats `flex_split` as an explicit tunable assumption
rather than a hidden constant. Preserve that design — replacement level depends on how flex slots
get filled league-wide, which is not knowable a priori. It is an assumption, and it must stay
visible as one.

**#33 status detail (2026-07-25).** `src/make_board.py` re-scores the *positional value structure*
under our exact rules and emits `data/board_{season}.csv`. What it cannot yet do is re-score an
individual player, because that needs component-level projections (#2) which no accessible source
provides — FantasyPros ECR was verified to be rank-only. Consequence: every player at the same
positional consensus rank receives an identical projection, so the bonus-structure edge that makes
#38 valuable is currently averaged away rather than captured. See `docs/decisions.md` ADR-017.

---

## Tier 3 — Strategy tests (the backtest queue)

Scoped; all need the data pipeline before they can run.

| # | Test | Question | Source | Status |
|---|---|---|---|---|
| 43 | RB dead zone by round, our scoring | Is it real for us? | `derived` | SPEC |
| 44 | Hero RB vs. alternatives | Does the approach beat BPA? | `derived` | **RESOLVED — NULL** (2026-07-25, PR-003 draft simulation): margin -13.3 pts vs BPA, CI [-98.1,+65.0], 2/4 seasons, sign p=1.000 at every sigma |
| 45 | Elite TE edge, measured | Prior claim had 2 of 3 inputs estimated | `derived` | **RUN — PROVISIONAL** (2026-07-25): measured cost **-226.4 pts** vs. plain BPA. Was blocked on P3-4; simulator now exists — re-run under it. See TE reversal note |
| 46 | QB1 vs. QB10 spread, our scoring | Justifies waiting — or doesn't | `derived` | **RUN — PROVISIONAL** (2026-07-25, 2025 actuals): justifies waiting. Does not yet meet `docs/statistical-guardrails.md` — see compliance note |
| 47 | Handcuff value by round | When does insurance beat a lottery ticket? | `derived` | SPEC |
| 48 | Injury rates & duration by position | Positional availability priors | `nflverse` | SPEC |
| 49 | Positional composition of top-30/60 | Replaces an estimate with a measurement | `derived` | SPEC |
| 50 | Draft-slot value curve | Is pick 3 actually the best seat? | `derived` | NEW |
| 51 | Rookie RB hit rate by draft capital + landing spot | Archetype risk | `nflverse` | NEW |
| 52 | Post-injury return curves by injury type | ACL vs. Achilles vs. Lisfranc vs. soft tissue | external | NEW |
| 53 | Second-year WR leap / third-year TE breakout | Do the classic patterns survive testing? | `derived` | NEW |
| 54 | New-team adjustment penalty | First year in a new offense | `derived` | NEW |

**#44/#45/#46 backtest findings (2025 season, 10-team VBD, `src/backtest.py`).** All three used a
VBD-ranked BPA baseline built from 2024 actual points as the common starting point (`ReplacementLevels()`
defaults: QB10/RB28/WR41/TE11 — confirmed, not the 12-team figure the run was originally requested
with; corrected to match this doc's own league context before running). Look-ahead cutoff enforced
and verified (`CutoffEnforcedStore`, `cutoff_season=2025`); no negative-point or >500-point outlier
seasons in 2025 actuals (2,019 players checked).

**Headline result nobody should skip: our own VBD-based ranking lost to FantasyPros' preseason
consensus by a wide margin** (-1,070 points of value-over-replacement, summed across the startable
pool). Per `CLAUDE.md` §6.5, this is reported as a failure, not softened. Mechanism: a backward-looking
"rank by last year's value" approach can't see the current-year information (injuries, depth-chart
moves, offseason changes, rookies) that expert consensus incorporates. True market ADP remains
unavailable (`docs/deferred.md`), so "beats the market" could only be checked against FantasyPros, not
real draft behavior.

**#44 Hero RB: the test is inconclusive, and the reason matters more than the number.** The +30% value
bonus on the top-24 RBs (by 2024 VBD) produced a `candidate_vbd_sum` *identical* to plain BPA
(delta = 0.0) — but this is a harness blind spot, not evidence the strategy is neutral. Our
"points vs. baseline" metric only counts *which* players land in each position's startable pool
(top-N by `ReplacementLevels`), not the draft order/cost paid to get them. Boosting players who were
already comfortably inside the top-28 RB cutoff can't change pool membership, so the metric can't see
what Hero RB actually does (buy RBs earlier at the cost of reaching elsewhere). A real test needs a
metric sensitive to draft-slot opportunity cost — logged as a harness gap in `docs/deferred.md`, not
silently reported as a tie.

**#45 Elite TE: real, measured cost, precisely mechanistic.** Brock Bowers and Trey McBride were
*already* the natural TE1 and TE3 by 2024 VBD — forcing them into overall ranks 8-9 didn't create value
BPA was missing. The entire -226.4-point cost comes from refusing every other TE (including that
season's actual natural TE2, a different player) in favor of nobody, pushed to the bottom of the whole
draft board. This is a faithful cost measurement of "only these two TEs, full stop" — not a knock on
Bowers/McBride themselves. Whether that cost is worth paying for playoff-bracket upside is **not
answered by this run**: this harness scores season-long value only, with no playoff-probability or
variance model (that's Tier 4 #55/#56, both still `NEW`). Reporting the plain-value cost, not a verdict
on "does the pick cost justify the playoff upside" — answering that honestly requires infrastructure
that doesn't exist yet.

**#46 QB1-vs-QB10, measured on real 2025 outcomes: justifies waiting.** QB1 (369.1 pts) to QB10
(294.4 pts) spread = 74.7 points (25% premium). RB1 (369.6) to RB28-replacement (143.8) spread = 225.8
points — roughly 3x the QB spread to replacement. QBs cluster much tighter than RBs in this scoring
format; the positional-scarcity case for not reaching for QB early holds up against actual 2025 results,
not just theory.

> **REVISED 2026-07-25 (session 4) — the number above measures the wrong quantity for a draft
> decision.** The 74.7-point figure is the spread between the players who *finished* QB1 and QB10.
> That conditions on the outcome. What a drafter actually chooses is a *draft slot*, and the player
> taken as consensus QB10 may bust, get hurt, or lose the job — so the decision-relevant quantity is
> `E[points | consensus positional rank]`, not `points | actual finish rank`.
>
> Measured that way over 2021-2025 (`src/make_board.py` curve fits, draft-relevant depth only):
>
> | Position | VBD of the rank-1 slot over replacement | 95% CI (season bootstrap) |
> |---|---|---|
> | RB | 168.5 | [131.9, 217.9] |
> | WR | 153.2 | [135.6, 172.7] |
> | QB | 114.1 | [57.0, 155.2] |
> | TE | 73.1 | [53.3, 93.2] |
>
> **The directional conclusion survives** — QB1's slot value is below RB1 and WR1, so the case for
> taking RB/WR before QB holds. But the 74.7-point framing *understated* QB slot value by
> conditioning on success; on a like-for-like basis the QB1 slot is worth ~114 points over
> replacement, not ~75. Note the QB interval [57, 155] is by far the widest of the four positions:
> QB slot value is both larger and less certain than the original entry implied.
>
> Both numbers are correct measurements of different things. Future entries must state which
> conditioning they use; they are not interchangeable.

**Compliance status update (2026-07-25, session 5).** Three of the gaps listed below are now
closed: `_rank_correlation` no longer pools positions (it is deleted; per-position only),
every reported metric carries a season-level bootstrap CI with degeneracy flagged, and all
RNG is seeded and recorded. The remaining gap is **consensus ADP**, still unobtainable
(ADR-018). Holdout discipline and FDR infrastructure now exist (ADR-022/023), so any future
factor test is subject to them — but #44/#45/#46 were run before they existed and remain
PROVISIONAL. Re-running them under the corrected harness is a prerequisite to promoting them,
and must use development seasons only.

**#44 / #45 / TE-QB timing were BLOCKED ON P3-4, and read as testable when they were not.**
Until the draft simulator existed, none of these could be answered: every metric measured which
players ended up in a lineup, not what was surrendered to get them. `starter_vbd` (ADR-020)
partially closed the gap by making cross-positional ordering visible, but it assumes you receive
your top-K picks uncontested — which is precisely the assumption a "reach for X" strategy
violates. The session-3 #44 result of *exactly 0.0* was not a tie; it was a metric that could
not see the strategy. The simulator (`src/draft_sim.py`, PR-003) is the first instrument that
can, and all three should be re-run under it.

**REACHING EARLY FOR TE *OR* QB IS COSTLY (2026-07-25).** Three independent instruments agree:

| Evidence | Finding |
|---|---|
| #45 direct measurement | Elite-TE construction cost **-226.4 points** vs. plain BPA |
| ADR-016 slot values | RB1 168.5 > WR1 153.2 > **QB1 114.1** > **TE1 73.1** |
| **PR-003 draft simulation** | `elite_te_early` **-96.1 ± 6** (seed-noise band, ADR-028), `qb_early` **-115.4** vs. BPA; both negative in **12 of 12** season×sigma cells |

The prior elite-TE-early framing is not supported.

**Correction to an inference made earlier the same day, before the simulator ran.** An earlier
version of this note argued from the ADR-016 slot values (QB1 114.1 > TE1 73.1) that
"TE-before-QB was backwards", implying QB-early is preferable. **The simulation measures that
decision directly and does not support it** — `qb_early` is the *worst* arm tested, consistently
worse than `elite_te_early` at every sigma.

Slot value over replacement and the opportunity cost of *reaching* are different quantities.
QBs cluster tightly (#46: 74.7-point QB1→QB10 spread on actual finish), so waiting recovers most
of the QB1 slot value, while the early pick spent on him cannot be recovered. **Correct reading:
both early reaches are costly, and QB-early is the more costly of the two.** Neither reaches
significance — four seasons floor the sign test at p=0.125 — but the direction is perfectly
consistent and the magnitude is 3-5% of a roster total.

**Guardrails compliance note (added 2026-07-25, after `docs/statistical-guardrails.md` landed
mid-session — the #44/#45/#46 runs above predate it).** Per that doc's own standard: "a result
reported without going through this checklist is not a result — it's an unverified claim." Running
its pre-mortem checklist (§8) against the three runs above, honestly:

| Check | Status |
|---|---|
| Look-ahead cutoff enforced programmatically | **Pass** — `CutoffEnforcedStore`, tested |
| Player universe defined before outcomes known | **Pass, with a gap** — universe = all 2024 (pre-2025) performers, so it's pre-outcome by construction; but it excludes true rookies with zero 2024 stats, which isn't classic survivorship bias but is a real coverage gap worth naming |
| Untouched holdout season | **N/A** — these are fixed heuristic rules, not fit/tuned models; no holdout-contamination risk to violate, but also no formal holdout discipline was exercised |
| Multiple-comparisons correction | **N/A at this scale** — 3 configurations, not a factor sweep; revisit once more configs are tested in one pass |
| Confidence interval, not just point estimate | **Fail** — every number above (-1,070 pts, -226.4 pts, 74.7-pt QB spread) is a point estimate. §7 explicitly says this is close to meaningless with ~5 seasons of data. No bootstrap CIs were computed |
| All three required baselines (BPA, ADP, expert consensus) | **Fail** — BPA and FantasyPros present; consensus ADP still unavailable (`docs/deferred.md`) |
| Rank correlation computed within position group | **Fail** — `backtest.py`'s `_rank_correlation` correlates across the whole candidate pool (QB/RB/WR/TE mixed together), not within each position as §6 requires. The reported correlation numbers (e.g. -0.255 full-universe, 0.390 restricted) mix positions and should be treated as directional only |
| Surprising result investigated before reporting | **Pass** — the negative full-universe correlation was investigated (top-20 position-mix comparison, realistic-universe restriction, mechanism identified: QB scoring-format inflation + QB YoY predictability) before being reported, not reported at face value |

**Net effect: the directional findings above (FantasyPros beats naive VBD, the Hero RB metric
blind spot, the Elite TE mechanism, QB flatness vs. RB) are real and stand on their own reasoning —
none of them depend on a p-value or a clean correlation number. But none of the three should be
treated as a validated go/no-go result until: (1) `_rank_correlation` is fixed to compute within
position group, (2) bootstrap confidence intervals are added, (3) consensus ADP is resolved as a
baseline. Logged as concrete follow-up items in `docs/deferred.md`.**

**#53 is a multiple-comparisons trap.** "Second-year WR leap" is folk wisdom with a plausible
mechanism and a large surface for p-hacking. Pre-register the test definition before running it.

---

## Tier 4 — Creative

Where real differentiation likely lives.

| # | Test | Why it could matter | Source | Effort | Status |
|---|---|---|---|---|---|
| 55 | **Optimize P(top 4), not E[points]** | Different objective functions. With 4 of 10 making playoffs and a 2-week bracket, the variance-seeking answer may win. | `derived` | H | NEW |
| 56 | **Full-season Monte Carlo w/ H2H schedule** | 2025: 4th in scoring, 6th in standings. Schedule noise is enormous and must be modeled, not ignored. | `derived` | H | NEW |
| 57 | **Startability index** | % of weeks a player is an obvious start. Value beyond points, because it reduces decision cost. | `derived` | M | NEW |
| 58 | **Decision-cost / manager-bandwidth modeling** | A roster of ambiguous RBs demands correct start/sit calls weekly. If a strategy's edge depends on decisions that won't reliably get made, the edge is fictional. | `derived` | H | NEW |
| 59 | Bench-points-left-behind, measured | Quantifies the leak directly | `league` | M | BLOCKED — needs weekly lineup history |
| 60 | Intra-roster variance correlation | Committee backs have correlated bad weeks. Portfolio risk, not individual risk. | `derived` | H | NEW |
| 61 | Bye-week clustering cost | 6 bench spots; 4 starters on one bye is avoidable | `nflverse` | L | NEW |
| 62 | In-season acquisition share of championship rosters | If most winning points come post-draft, draft optimization is worth less than we think | `league` | M | NEW |
| 63 | FAAB market efficiency in 10-team | What do winning bids actually cost? | `league` | M | NEW |
| 64 | Best-ball vs. redraft ADP divergence | Best-ball ADP is pure points-value; redraft includes startability bias. **The gap is itself a signal.** | `adp` | M | **BLOCKED** — no ADP source exists (ADR-018) |
| 65 | Auction values as continuous value proxy | Finer-grained than ordinal ADP | `adp` | L | **BLOCKED** — no ADP source exists (ADR-018) |
| 66 | ADP momentum (July→August rate of change) | Rising players often keep rising past fair value | `adp` | L | **BLOCKED** — no ADP source exists (ADR-018) |
| 67 | Historical consensus-error analysis | Where has the market been *systematically* wrong? | ~~`adp`~~ `derived` | H | **PARTIAL — runnable now.** Not ADP-blocked; see note |
| 68 | Positional run / cascade modeling | If I take X, how does the room respond? | `league` | H | **IMPLEMENTED (ADR-045)** — `live_availability.py`'s `R(p)`; `delta=0.10` is an unvalidated prior, needs mocks with per-pick draft state (SS5(b), not built) |
| 69 | Weeks 16–17 availability risk | Clinched teams rest starters; eliminated teams play backups | `nflverse` | M | NEW |
| 70 | Unsupervised tier clustering | Cluster on projected points + variance instead of eyeballing breaks | `derived` | M | NEW |
| 71 | Ensemble ADP weighted by historical accuracy | Which source has actually predicted best? | `adp` | M | **BLOCKED** — needs ≥2 ADP sources; zero exist (ADR-018) |
| 72 | Value-of-information ranking | Which uncertainties are worth resolving before draft day? Meta-test that prioritizes everything else. | `derived` | M | NEW |

**#55 and #58 are the two highest-value items in the registry.**

**#55** may invert conclusions. Expected-points maximization and playoff-probability maximization
are different objective functions, and prior strategy work assumed the former without ever
checking whether it is correct for this format. That is an unexamined foundational assumption.

**#58** is the only item here specific to *the manager* rather than the league. If a strategy's
returns depend on weekly decisions that won't reliably get made, its paper edge is fictional. The
highest-EV strategy in the abstract may not be the highest-EV strategy in practice. Nothing public
models this.

**#67 and #71 are the strongest arguments for ADP snapshot discipline.** Both require historical
ADP with correct `as_of_date` values. Without dated snapshots, neither can ever be run. Start
capturing now even though the analysis is far off — this data cannot be reconstructed later.

---

## Tier 5 — Considered and rejected

Listed so the rejection is explicit and revisitable, not forgotten.

| Test | Verdict |
|---|---|
| Weather | Matters for in-season lineups, not drafting |
| QB–WR stacking correlation | DFS concept; in redraft H2H mainly adds variance. May matter for #55. |
| DFS ownership as sentiment proxy | Different game, different incentives |
| Beat-writer sentiment scoring | High effort, low signal, hard to validate |
| Nash-equilibrium drafting | Elegant, but opponents aren't optimizing, so equilibrium is the wrong model |
| Coaching scheme fit (zone vs. gap) | Real effect, too noisy to act on at draft |

---

## The null hypothesis

**Every backtest must include "draft best available off a good half-PPR list" (BPA) as an explicit
arm.**

If the model doesn't beat BPA by a meaningful margin across multiple holdout seasons, the honest
conclusion is to use BPA and redirect the effort to in-season management. This is not a rhetorical
caveat — the 2025 roster finished 4th in scoring and 6th in the standings, which is direct evidence
that roster construction was not the binding constraint that year.

Per `CLAUDE.md` §6.5, BPA joins consensus ADP and prior-season-points as a required baseline. A
result reported without its baseline comparison is not a result.

---

## Known gaps and open questions

1. **Opponent adaptation is unmodeled.** Every backtest assumes opponents draft to ADP with noise.
   Sharp managers adapt to repeated behavior. One season can't detect this; three or four might.

2. **Late-round TE hit rate is unmeasured.** A single Round-15 TE hit is one data point, but it
   raises a real question: if late-TE hit rates are meaningfully above zero, the elite-TE case
   weakens considerably. Belongs in #45.

3. **The 2025 "slow start" is unverified.** That framing rests on recollection, not weekly scores.
   Treat the entire branch as unconfirmed until weekly data exists. Flagged because it has been
   influencing strategy conclusions without evidence.

4. **Look-ahead bias.** Prior sessions treated this as unavoidable, to be mitigated by preferring
   robustness across seasons. **`CLAUDE.md` §6.1 supersedes that** with a stricter requirement:
   structural enforcement at the data-access layer. This is the primary reason the prior backtest
   harness is being rebuilt rather than ported.

5. **Component-level projections (#2) block the most downstream work.** Highest-value non-code task.

---

## Suggested build order

Sequenced by information value per unit of effort. Assumes the Phase 1 pipeline from `CLAUDE.md` §3
lands first — none of this runs without ingestion, scoring, and a leakage-safe harness.

> **REVISED 2026-07-25.** The order below is superseded in part. #38 is falsified, the
> ADP-dependent items are blocked rather than cheap, and the draft simulator now exists.

**Superseded original order, kept for the record:** port #33/#34 → #49, #45, #46, #48 → #38 →
#44 → #56 → #55 → #58 → #37 → #35/#36 → live tool, with #64/#66/#61 in parallel and ADP capture
started immediately.

### Corrected order

**Done or resolved:** #33/#34 (partial — positional re-weighting only, #2 still blocks
player-level re-scoring), #46 (revised — the draft-slot framing supersedes the actual-finish
figure), **#38 (FALSIFIED — see above)**, P3-4 draft simulator (built).

**Now unblocked by the simulator:** #44 Hero RB, #45 elite TE, the TE/QB timing question, and
#68 positional-run modelling. These were untestable before it, and the earlier #44 "result" of
exactly 0.0 was an artifact of a metric blind to draft cost.

**Runnable now, previously mis-tagged:** #67 consensus-error analysis — `derived`, not `adp`.
The ADR-016 residuals already are the consensus errors.

**Cheap and genuinely parallel:** #61 bye clustering (2026 schedule is available), #29b
head-coach continuity.

**BLOCKED — do not schedule as cheap work:** #64, #65, #66, #71 all require an ADP source, and
ADR-018 established that none is obtainable within CLAUDE.md §10. #2 (component-level
projections) still blocks player-level re-scoring. #29/#30 are gated on coordinator data
(PFR returns 403).

**~~Start immediately: ADP snapshot capture~~** — cannot be started. There is no source to
capture from. What *can* be captured, and now is, is the cross-source **dispersion** of expert
consensus (`spread_sd`/`rank_best`/`rank_worst`, ADR-024), which is what VONA survival
probabilities need. Note this is expert disagreement, not market draft position; they are not
interchangeable.
