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

| # | Test | Why | Source | Effort | Edge | Status |
|---|---|---|---|---|---|---|
| 13 | Target share **stability** YoY | Separates real role from one-year noise | `nflverse` | M | Med | SPEC |
| 14 | Air yards, aDOT | Big-play vs. volume profile | `nflverse` | M | Med | NEW |
| 15 | WOPR | Best single opportunity metric for WR | `derived` | M | Med | NEW |
| 16 | Yards per route run | Efficiency independent of volume | `nflverse:FTN` | M | Med | NEW — check FTN columns first |
| 17 | Route participation rate | Distinguishes starters from rotational | `nflverse:FTN` | M | High | NEW — check FTN columns first |
| 18 | **Expected fantasy points (xFP) vs. actual** | Isolates luck from skill | `derived` | H | **High** | NEW |
| 19 | TD-rate regression | Best-known regression signal | `derived` | M | **High** | SPEC |
| 20 | Opportunity share (carries+targets / team total) | Single best RB metric | `nflverse` | M | High | SPEC |
| 21 | Team pace / plays per game | Volume multiplier | `nflverse` | M | Med | NEW |
| 22 | Pass rate over expectation (PROE) | Scheme tilt | `nflverse` | M | Med | NEW |
| 23 | O-line run-block & pass-block rankings | RB efficiency, QB time | external | L | Med | SPEC |
| 24 | QB quality for pass catchers | Ceiling constraint | `derived` | L | Med | SPEC |
| 25 | NFL draft capital (rookies) | Best rookie predictor | `nflverse` | L | Med | SPEC |
| 26 | Breakout age / college dominator | Rookie projection | external | M | Med | NEW |
| 27 | Contract year / free-agency status | Motivation & usage | `nflverse` (contracts) | L | Low | NEW |
| 28 | Vacated targets & carries | Where opportunity actually opened | `derived` | M | High | NEW |
| 29 | Coordinator continuity | High OC turnover league-wide | `pfr` | L | **High** | SPEC |
| 30 | First-time play-callers | Week-to-week volatility | `pfr` | L | Med | SPEC |
| 31 | Personnel package trends | Structural WR3 headwind | `nflverse:FTN` | L | Med | SPEC |
| 32 | Pre-snap motion rates | Largely arbitraged league-wide | `nflverse:FTN` | L | **Low** | SPEC |

**#18 is the highest-value unbuilt item in this tier.** Expected points from opportunity (target
volume, aDOT, carries, red-zone looks) vs. what a player actually scored separates luck from skill
better than any single stat. Above xFP → regression candidate; below → buy candidate.

**#29/#30 require the `coach_id` dimension**, not `team_id`. Coordinators change teams; tendency
signal keyed to franchise breaks the moment someone moves.

**#16/#17/#31/#32 are FTN-dependent and therefore 2022+ only.** That is 4 seasons — small. Treat
any finding here as provisional and flag the sample size in results. Do not let a 4-season factor
carry the same weight as a 20-season one.

---

## Tier 2 — League-specific (our structural edge)

Nobody else does these, because they only matter in *our* league.

| # | Test | Why | Source | Effort | Edge | Status |
|---|---|---|---|---|---|---|
| 33 | Re-score all projections under exact rules | Public half-PPR lists model neither our bonuses nor −2 INT | `derived` | M | **High** | **PARTIAL (2026-07-25)** — positional re-weighting done (`src/make_board.py`); player-level re-scoring still blocked by #2 |
| 34 | Replacement levels: RB28 / WR41 / TE11 / QB10 | Published VBD assumes 12-team RB24/WR36 | `derived` | L | **High** | **DONE (2026-07-25)** — `ReplacementLevels()` derived, used unmodified by board + backtest |
| 35 | Global flex baseline (~80th flex-eligible) | Correct baseline past mandated slots | `derived` | M | **High** | SPEC |
| 36 | VONA with pick-gap awareness (5 vs. 14) | Urgency differs ~3× between gap types | `derived` | M | **High** | SPEC |
| 37 | League-biased ADP (format + manager priors) | Yahoo board assumes 2WR/1FLEX/K | `league` + `adp` | H | **High** | SPEC |
| 38 | **Bonus-threshold hit rates** | Who *actually* clears 100/150/200, and how often | `nflverse` | M | **High** | NEW |
| 39 | No-kicker effect on pool depth | One extra skill player per team drafted | `derived` | L | Med | NEW |
| 40 | Post-draft players follow waiver rules | Undrafted pool isn't instantly free — changes Wk 1 FAAB | `manual` | L | Med | NEW |
| 41 | IR restriction (no direct waiver→IR) | Stashing costs a bench spot, not an IR spot | `manual` | L | Med | NEW |
| 42 | Trade deadline Nov 28 (~Wk 12) | Caps the trade-to-improve path | `manual` | L | Low | NEW |

**#38 is the most genuinely novel item in this registry.** Bonuses stack: a 200-yard game is worth
+4.5 on top of base. That rewards *spike-week* players over metronomes in a way no public ranking
captures. Two players with identical projected season totals can differ materially in our format
based purely on distribution shape. Computable from weekly data we already know how to pull.

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
| 44 | Hero RB vs. alternatives | Does the approach beat BPA? | `derived` | **RUN — PROVISIONAL** (2026-07-25, 2025 season): inconclusive, metric blind spot found. Does not yet meet `docs/statistical-guardrails.md` — see compliance note |
| 45 | Elite TE edge, measured | Prior claim had 2 of 3 inputs estimated | `derived` | **RUN — PROVISIONAL** (2026-07-25, 2025 season): measured cost -226.4 pts vs. plain BPA. Does not yet meet `docs/statistical-guardrails.md` — see compliance note |
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
| 64 | Best-ball vs. redraft ADP divergence | Best-ball ADP is pure points-value; redraft includes startability bias. **The gap is itself a signal.** | `adp` | M | NEW |
| 65 | Auction values as continuous value proxy | Finer-grained than ordinal ADP | `adp` | L | NEW |
| 66 | ADP momentum (July→August rate of change) | Rising players often keep rising past fair value | `adp` | L | NEW |
| 67 | Historical consensus-error analysis | Where has the market been *systematically* wrong? | `adp` + `derived` | H | NEW |
| 68 | Positional run / cascade modeling | If I take X, how does the room respond? | `league` | H | SPEC |
| 69 | Weeks 16–17 availability risk | Clinched teams rest starters; eliminated teams play backups | `nflverse` | M | NEW |
| 70 | Unsupervised tier clustering | Cluster on projected points + variance instead of eyeballing breaks | `derived` | M | NEW |
| 71 | Ensemble ADP weighted by historical accuracy | Which source has actually predicted best? | `adp` | M | NEW |
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

**First (validate the foundation):** port #33/#34 → run #49, #45, #46, #48 against real data →
#38 bonus-threshold hit rates → #44 with the rebuilt harness and BPA baseline.

**Then (test the objective function):** #56 full-season Monte Carlo → #55 P(top 4) →
#58 decision-cost modeling.

**Then (draft-day tooling):** #37 league-biased ADP → #35/#36 flex baseline + VONA → live tool.

**Parallel, cheap, independently useful:** #64 best-ball divergence, #66 ADP momentum,
#61 bye clustering.

**Start immediately regardless of sequence:** ADP snapshot capture with `as_of_date`. It gates #67
and #71 and cannot be backfilled.
