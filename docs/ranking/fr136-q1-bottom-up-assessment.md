# FR-136 Q1 — bottom-up rankings: where it actually stands

**Ranker, 2026-07-30.** Assessment only. **No model was built in this pass and nothing here is a
new result about football** — every number is either a re-measurement of an existing artifact or a
structural property of code already shipped. Prior passes are cited, not re-derived.

Reproduce: `.venv/bin/python`, `data/nfl.db`, main checkout, branch `claude/pm-agent-setup-gobxa0`.

---

## 0. Data preconditions — checked first, as instructed

| Precondition | Verified | Evidence |
|---|---|---|
| **Half-PPR only for the board source** | **PASS** | `board.json:scoring_format = "half_ppr"`, read from `rankings.scoring_format`, not hardcoded (`src/export_contract.py:341-355`). Both 2026 snapshots of `fantasypros_csv_2026draft` carry `half_ppr` on every row. |
| **One snapshot, not two** | **PASS** | `board.json:snapshot_as_of_date = "2026-07-30"`, `consensus_source_count = 1`. Both `make_board._consensus_board` and `export_contract` filter on `as_of_date = (SELECT MAX(as_of_date) ...)`. The 07-27 snapshot is retained in the table for as-of-date-correct backtesting and is not read by the live board. |
| **Nothing derived from FFC `times_drafted`** | **PASS** | `board.json:adp_source = "mfl_proxy"`. FFC's `times_drafted` is carried into the export payload but the sigma it would feed is explicitly **withheld**, gated on M0 (`src/export_contract.py:686-693, 761, 915`). No board field derives from it. |

**One precondition finding that was not on the list, and it matters.**

The board's *display* source is confirmed half-PPR. The **curve is trained on a different source
whose scoring format is unknown.** `make_board.TRAINING_SOURCE = "fantasypros_ecr"` (2021–2025) has
`scoring_format = NULL` on all 2,540 rows — the DynastyProcess mirror never carried the column. So
`projected_points` is `E[our half-PPR points | rank on a consensus board of unrecorded format]`.
The *outcome* side is scored correctly under this league's rules; the *rank* side is a consensus
ordering that may have been PPR or standard. This is not fatal — expert overall ranks are broadly
format-insensitive at the top — but it is an unlabelled assumption sitting under every projection on
the screen, and it should be labelled.

**A second one:** historical FFC ADP in `nfl.db` covers 2013–2024 and is **12-team** at every
format; the primary league is **10-team**. 2025 is absent from FFC entirely. Any "beats market ADP"
claim on history is a claim against a 12-team market, not this league's.

---

## 1. Q1 — what is built, measured against §6.5's baseline rule

### 1.1 The shipped board holds no player-level opinion. Verified, not asserted.

`data/board_2026.csv`, 378 rows, all four positions:

| position | n | is the board's within-position order identical to consensus order? |
|---|---|---|
| RB | 116 | **yes** |
| WR | 148 | **yes** |
| QB | 45 | **yes** |
| TE | 69 | **yes** |

`projected_points` is a deterministic log curve of consensus positional rank. Refitting
`a + b·ln(positional rank)` to the shipped column returns **max |residual| = 0.005 points** at every
position — the 2-dp rounding in the CSV, nothing else:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| intercept | 359.01 | 303.16 | 276.48 | 180.31 |
| slope | −49.38 | −50.62 | −41.21 | −30.45 |

Independently reproduced by pass 3 §0 from a different direction (the intercept cancels in VBD, so
all 510 board rows reconstruct from four slopes and four replacement ranks with zero mismatches).

**The board's entire deviation from consensus is cross-positional.** `delta_vs_consensus`: mean
|Δ| = 35.1 places over the full board, but **mean |Δ| = 5.9 places, max 20, across the top 100** —
which is every pick in a 10-team draft. In the draft-relevant region the board is consensus moved by
about six places.

### 1.2 The primary harness metric cannot see the board's only edge channel. Measured.

`src/backtest.py:_rank_correlation_by_position` computes Kendall's τ_b **within** each position
(ADR-B forbids any cross-position aggregate — not computed, not stored, not on request). Because
within-position order is identical to consensus, the two arms are the same object under that metric.
Measured, `rescored_consensus_board` vs `fantasypros_ecr_raw`:

| season | QB | RB | WR | TE |
|---|---|---|---|---|
| 2022 | Δτ_b = 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2023 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2024 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

Exactly zero, twelve of twelve. This is not a null result about football. **It is a structural
property**: the project's primary evaluation metric is mathematically incapable of distinguishing
the shipped board from raw consensus, and always was. `top_k_starter_vbd` exists precisely to fix
this and says so in its own docstring — it is the *secondary* metric.

### 1.3 The comparison that has been run, and the two that have not

| §6.5 required baseline | run against the shipped board? | result |
|---|---|---|
| **1. Consensus market ADP** | **NEVER MEASURED** | The `consensus_adp` arm is `available=False` in `standard_arms()`, with ADR-018's reason ("no market ADP source obtainable"). **That reason is stale** — FFC ADP is now ingested (2018–2024 half-PPR, 12-team) and FR-023 records the founder confirming it unblocked. The arm was never re-enabled. |
| 2. Prior-season points, ranked | yes | `bpa_prior_season_points` is a live arm |
| 3. Positional-tier heuristic | **NEVER MEASURED** for the shipped board | No tier-heuristic arm exists in `standard_arms()`. Test-registry #3 is still `SPEC`. |

**The one real comparison on record** is the board against *raw expert consensus* (not market ADP),
on `starter_vbd`, ADR-025:

| Season | Board | Raw consensus | Δ |
|---|---|---|---|
| 2022 | 1001.8 | 825.8 | **+176.0** |
| 2023 | 626.1 | 660.8 | **−34.7** |
| 2024 | 673.9 | 560.5 | **+113.4** |
| 2025 (**holdout**) | 693.1 | 609.3 | **+83.8** |

Development-only: **+84.9, 2/3 positive, sign-test p = 1.000, power floor 0.250.** With the holdout:
+84.6, 3/4 positive, p = 0.625, power floor 0.125. **The correct reading is ADR-025's own: the
board's advantage is not statistically established on development data alone.** Four seasons cannot
establish it, and the sign test's floor (0.125) is above 0.05 — *this design cannot produce a
significant result at any effect size*.

### 1.4 The component models — measured, and they do not clear the market

Already reported in `component-model-wr-pass-1.md` §5 and `component-model-rb-qb-te-pass-1.md` §3.
Restated, not re-derived:

| position | model − consensus ADP (Spearman) | 95% CI | does the design have power? |
|---|---|---|---|
| WR | +0.051 | [−0.011, +0.129] | **no** — ADP − heuristic +0.043 [−0.032, +0.126] |
| **RB** | **−0.052** | [−0.126, +0.038] | **yes** — ADP − heuristic +0.134 [+0.043, +0.223] |
| QB | −0.069 | [−0.255, +0.104] | no |
| TE | −0.024 | [−0.182, +0.123] | no |

Against B2 (prior points) and B3 (weighted prior PPG) they win clearly at all four positions on the
full universe. **Against baseline #1 they do not, and at RB — the one position where the experiment
demonstrably has power — the point estimate is negative.**

Decision-relevant (§6.6), top-k capture and mean actual points of the drafted top-k: **every interval
is open at every position.** Nothing translates into better rosters.

### 1.5 The sealed holdout has never been spent on a ranking model

`HOLDOUT_SEASON = 2025`. `docs/preregistration/holdout_access_log.jsonl` has **three entries**, all
one 2026-07-25 backtest decomposition (ADR-025). No component-model result has ever touched it.
Thread 094 (ranker → strategist) asked for the one registration worth making; the ranker's own §9
then withdrew the factor it proposed, because it measured null. **There is currently no registered
confirmatory test of any bottom-up ranking, and nothing is queued to spend the holdout on.**

---

## 2. Q2 — is it proprietary yet? Quantified.

**No. It is consensus plus a positional tilt, and the tilt is eight numbers.**

| measure | value |
|---|---|
| Spearman(board rank, consensus rank), full board | **0.934** |
| Spearman(board rank, consensus rank), **top 100** — every pick in a 10-team draft | **0.972** |
| top-15 set overlap (one roster's worth of picks) | **80%** — 3 players differ |
| top-30 / top-50 / top-100 set overlap | 90% / 92% / **93%** |

**Where the disagreement is.** Mean signed Δ vs consensus in the top 100, positive = board ranks the
player higher:

| QB | RB | WR | TE |
|---|---|---|---|
| **+5.3** | −1.2 | −1.8 | **+10.6** |

**All twelve of the board's largest top-100 disagreements are quarterbacks or tight ends.** The
three biggest are Josh Allen (+20), Lamar Jackson (+20), Travis Kelce (+19).

**So the honest description of the proprietary content is one sentence:** *in a 10-team half-PPR
league with replacement levels QB10 / RB30 / WR40 / TE10, take quarterbacks and tight ends a few
places earlier than the expert consensus does.* That is a real, defensible, league-specific claim —
it is `test-registry.md` #33/#34 and it is the thing consensus genuinely does not do. It is **not** a
player-level opinion, it is **not** a projection, and it is generated by **four slopes and four
replacement ranks**, fitted on 725 rank–outcome pairs from 5 consensus seasons.

### 2.1 The board's biggest opinions are its least resolvable ones

Using the board's own published 95% VBD intervals, top 100:

| | |
|---|---|
| median number of *other* top-100 players whose interval overlaps a given row's | **18** |
| Josh Allen (board #5, +20 vs consensus) | overlaps **28** others |
| Lamar Jackson (board #12, +20 vs consensus) | overlaps **36** others |

The two players the board moves furthest are the two whose value is least distinguishable from the
field. This is not new — the mandate names it — but it is still live in the shipped artifact.

---

## 3. Q3 — projections

### 3.1 What is on screen is not a projection

`board.json:curve_fits`, from the live artifact:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| R² | 0.158 | 0.263 | 0.266 | 0.217 |
| residual SD (fantasy points) | 91.1 | 74.2 | 61.4 | 46.3 |
| n_obs | 100 | 225 | 300 | 100 |

Put that next to the size of the thing being predicted — the points spread from the #1 player at a
position down to the last draftable one:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| full positional value range (rank 1 → depth) | 147.9 | 192.7 | 168.7 | 91.2 |
| 95% band on **one player's** projection | 357.1 | 290.8 | 240.8 | 181.7 |
| **band ÷ range** | **2.41×** | **1.51×** | **1.43×** | **1.99×** |

**At every position the uncertainty on a single player's projected points is wider than the entire
spread between the best and the worst draftable player at that position.** The board already says
"treat projections as weak" in `curve_caveat`; this is how weak.

### 3.2 A real bottom-up projection exists — in `experiments/`, for the wrong seasons

`experiments/bottomup/components/` projects, per player: games · volume · efficiency · touchdowns ·
fumbles · and a per-game exceedance distribution for the stacking bonuses. It beats naive
persistence decisively on **every component at all four positions** (`component-model-*-pass-1.md`
§4). That is a genuine projection from player inputs and it is the one unambiguous win in the
bottom-up work.

**It has never produced a 2026 number.** `run_position.py:36` reads `FIRST, LAST = 2014, 2024`. A
2026 projection needs 2025 features, and 2025 is the sealed holdout. `holdout.HoldoutLock.
release_for_final_fit()` exists for exactly this transition — but it releases the holdout *after the
model decisions are frozen*, and no decision has been frozen because nothing has cleared a baseline.

### 3.3 What a real bottom-up projection needs, and what the database actually holds

| requirement | in `nfl.db`? | detail |
|---|---|---|
| Player weekly production, all positions | **yes** | `player_weekly_stats`, 1999–2025, 146 columns, 475,626 rows |
| Usage analytics — `target_share`, `air_yards_share`, `wopr`, `receiving_air_yards` | **yes, 2009+** | 100% populated 2009–2025. **0% before 2009**, and targets are effectively absent 2003–2008 |
| Efficiency — EPA, RACR, CPOE | **partial** | `receiving_epa`/`racr` ~72% populated; `passing_cpoe` **11%** |
| Snap counts (the documented route-participation proxy) | **yes, 2013+** | 324,611 rows. **Unused by any model in this project.** |
| Next Gen Stats (separation, cushion, time-to-throw) | **yes, 2016+** | `ngs_receiving`/`rushing`/`passing`. **Unused by any model.** |
| Games played / availability history | **yes** | derivable from `player_weekly_stats` |
| Draft capital for rookies | **yes** | `draft_picks` 1980–2026 (mandate: eliminated as an edge channel) |
| **Play-by-play** | **NO** | There is no PBP table. This is the single biggest inventory surprise — `CLAUDE.md` §5 says "most Tier 0/Tier 1 factors derive from this." |
| **Red-zone / goal-line usage** (registry #10) | **NO** | needs PBP. No red-zone column exists anywhere. |
| **PROE, team pace, xFP** (registry #21, #22, #18) | **NO** | all need PBP |
| **Team-level table / schedules** | **NO** | no `teams`, no `team_weekly_stats`, no schedules. Team volume must be reconstructed by summing player rows. `league_season_metrics` is *league*-wide (27 rows), not per team. |
| **Coaching staff history** (`coach_id`, `CLAUDE.md` §4/§5) | **NO** | no coaching table. `coach_id` is a first-class schema dimension with nothing behind it. |
| **Vegas odds / implied team totals** (§5) | **NO** | no odds table |
| **Route participation** (§5) | **NO** | not directly available; `snap_counts` is the labelled proxy and is unused |
| **2025 injuries and depth charts** | **NO** | `injuries` and `depth_charts_weekly` both stop at **2024** — zero 2025 rows. Any N−1 feature built on them is unavailable for a 2026 projection. |
| DEF / DST anything | **NO** | a starting slot in this league with zero coverage (`board.json:def_supported = false`) |

**Player coverage of the 2026 board is not a problem.** Of the 527 QB/RB/WR/TE on the 2026-07-30
consensus board, 82.9% have a 2024–25 stat line; in the draft-relevant range it is **98% of the top
50, 96% of the top 150**. The six missing from the top 150 are all 2026 rookies (highest: Jeremiyah
Love, consensus #33).

---

## 4. How much room is there? The oracle ladder — asked because nobody had

The mandate is right that this bounds everything else. It is answerable cheaply and had never been
run. Universe: FFC half-PPR 12-team ADP boards **2018–2024** (7 seasons), the same universe the
component models used; busts retained; **the 2025 holdout was not touched.** Season-block bootstrap,
4,000 reps.

| pos | consensus ADP | **oracle: perfect per-game rate**, no availability knowledge | **oracle: perfect games played**, no talent knowledge |
|---|---|---|---|
| QB | 0.335 [+0.239, +0.443] | **0.771** [+0.693, +0.841] | 0.700 [+0.532, +0.830] |
| RB | 0.484 [+0.375, +0.597] | **0.883** [+0.850, +0.916] | 0.609 [+0.542, +0.662] |
| WR | 0.485 [+0.421, +0.545] | **0.839** [+0.793, +0.884] | 0.617 [+0.570, +0.659] |
| TE | 0.390 [+0.234, +0.541] | **0.816** [+0.748, +0.883] | 0.713 [+0.663, +0.767] |

Paired gaps against consensus:

| pos | rate-oracle − ADP | games-oracle − ADP |
|---|---|---|
| QB | **+0.435** [+0.311, +0.555] | **+0.364** [+0.204, +0.521] |
| RB | **+0.399** [+0.300, +0.511] | +0.125 [−0.058, +0.261] |
| WR | **+0.354** [+0.289, +0.419] | **+0.132** [+0.066, +0.196] |
| TE | **+0.426** [+0.274, +0.580] | **+0.323** [+0.146, +0.499] |

**Two readings, and the second one is the uncomfortable one.**

**(1) Projection is not a solved problem, and the room is large.** The distance from consensus to
perfect rate knowledge is **+0.35 to +0.44 ρ at every position, clearing zero at all four.** For
scale, the component models' measured advantage over consensus is +0.051 at WR and negative at RB.
The channel the project deprioritised as "everyone does that" is, on this measurement, by far the
largest one on the table.

**(2) Perfect foresight of *who stays healthy*, with zero knowledge of how good anyone is, beats the
entire expert consensus at all four positions** — significantly at QB, WR and TE. More of a
season's fantasy outcome sits in availability than in the talent ordering every ranking argues
about.

### 4.1 What this does NOT establish, stated before anyone quotes it

- **These are oracles, not forecasts.** They use the target season's own realised values. They bound
  the size of the room; they say nothing about whether any of it is reachable. Much of realised
  per-game rate is genuinely unknowable in August — an upstream QB injury, a midseason trade, a
  coordinator firing.
- **The rate oracle shares its numerator with the outcome** (PPG = points ÷ games), so ρ is
  mechanically near 1 and its shortfall from 1.0 *is* the games-played channel. It is an upper bound
  by construction. It must not be read as an achievable target.
- **Descriptive, exploratory, uncorrected.** 7 seasons, 12 tests here, no multiplicity correction,
  and a 12-team ADP board against a 10-team league. **This is a hypothesis about where to look, not
  a finding.** If anyone wants to act on it, `strategist` registers it first.

---

## 5. Q4 — the gap list, ordered by what it buys

**39 days to 7 September.** Costs below are **measured, not estimated** — every acquisition time in
this section was timed in this container against the live source today.

### 5.0 The finding that reorders the whole list

Four of the named "expensive" gaps are not expensive. They are unnoticed.

| dataset | measured today | what it unblocks |
|---|---|---|
| `nflreadpy.load_pbp(2009…2025)` | **816,856 rows in 20.4 s**; the 24 columns needed slim to **15.2 MB** parquet, `xpass` included | registry **#10 red-zone/goal-line**, **#18 xFP**, **#21 team pace**, **#22 PROE** — all four currently marked unbuildable, three of them High edge |
| `load_rosters_weekly(2025)` | **46,849 rows in 1.0 s**, `status` includes `RES` (IR) and `EXE` | the IR/suspension signal `component-model-rb-qb-te-pass-1.md` §5.2 commissioned from `data-ops` and which is still not in the DB |
| `load_injuries(2025)` | **6,068 rows in 0.5 s** | closes the `injuries` table's 2025 hole (it stops at 2024) |
| `load_depth_charts(2025)` | **554,215 rows in 0.7 s** | closes the `depth_charts_weekly` 2025 hole (stops at 2024) |
| `load_schedules([2025, 2026])` | **557 rows in 1.3 s**, 2026 present | byes and opponent structure from source rather than derived |

**Total acquisition: under half a minute of wall clock.** The reason four Tier-1 factors are
untested is not that the data is hard to get. Nobody fetched it. That is a finding in its own right
and it should be reported as one.

**Acquisition is not validation.** Testing four factors properly, with §6.3's multiplicity exposure
handled at the campaign level rather than per test, is the expensive half — and it is the half that
does not fit comfortably in 39 days.

### 5.1 The ordered list

| # | Gap | What it buys | Cost | Validatable before 7 Sep? |
|---|---|---|---|---|
| **1** | **Re-enable the `consensus_adp` baseline arm** (`backtest.py:standard_arms`, `available=False` on ADR-018's now-stale reasoning) | `CLAUDE.md` §6.5 **baseline #1**, which the shipped board has never been measured against. Buys no accuracy — buys knowing whether the board is worth anything | hours; FFC ADP already ingested | **Yes.** Cheapest item on the list and it is a compliance gap, not a model gap |
| **2** | **A primary metric that can see the board** | §1.2: per-position τ_b returns exactly 0.000000 between board and consensus. `top_k_starter_vbd` and `src/draft_sim.py` already exist and are cross-position sensitive | days | **Yes** — but **`strategist` must choose it, not me.** A ranker picking the metric that scores the ranker is the failure this structure exists to prevent |
| **3** | **Ship real component projections as `projected_points`** (FR-054/FR-056 and today's founder request) | The founder's actual ask. Replaces a curve fit to consensus rank with a projection from player inputs that beats naive persistence at all four positions | model exists; needs `release_for_final_fit`, a 2026 run, and a `backend` handoff on the export contract | **Acquisition yes, justification no.** The component model is *measured* not to beat consensus on rank. Shipping it as the ranking would ship a thing known not to beat the market. Shipping it as *displayed projections beside* a consensus-derived rank is defensible and different — **that is a PM/strategist call, not mine** |
| **4** | **Ingest PBP + the four factors it unblocks** (#10, #18, #21, #22) | The only untouched High-edge block in the registry | 20 s to acquire; **weeks to test honestly** | **Partly.** Ingest and one pre-registered factor: yes. All four with campaign-level multiplicity control: **no** |
| **5** | **Availability, re-approached** | The oracle says perfect games-played foresight alone beats consensus at all four positions (§4). The channel is the largest single one after rate | `load_rosters_weekly` is 1 s; the modelling is not | **Test yes, expect null.** Every availability arm already tried measured null on ranking (`component-model-rb-qb-te-pass-1.md` §5.1). The channel is huge and our features for it are empty — those are both true and the second one is the binding constraint |
| **6** | **The rate channel — better projection of the same variables** | §4: **+0.35 to +0.44 ρ** of room at every position, against a component model delivering +0.051 at WR and negative at RB. Largest measurable gap in the project | open-ended | **No, and this is the "cannot be earned in time" item.** A bounded slice can be: `snap_counts` (2013+) and NGS (2016+) are both in the DB and **untouched by any model**. That is a real, testable, pre-registerable factor batch that fits in 39 days. The channel itself does not |
| **7** | **DEF / DST** | A **starting slot** in this league with literally zero coverage (`board.json:def_supported = false`). On 7 September he will draft one and the tool will say nothing | low-moderate: scoring rules + ingest | **Coverage yes, edge no.** DST is close to unpredictable; a "best DEF ranking" claim is not earnable by September. A *number where a blank currently sits* is |
| **8** | **Vegas odds / implied team totals** (`CLAUDE.md` §5 gap) | Offensive environment | sourcing + licensing; **historical odds need a paid source** — `researcher` thread | **No — and it should not be attempted.** `bottom-up-research-pass-1` bounded the entire team-environment channel at **≤ +0.055 τ_b by oracle**. It cannot be validated in time *and* its own ceiling says it is small. Both reasons, and the second is the better one |
| **9** | **Coaching / coordinator history** (`coach_id`, §4/§5) | Registry #29/#30, tagged High edge | PFR returns HTTP 403; `src/ingest_coordinators_wikipedia.py` and `ingest_play_callers.py` exist and **have landed no table in `nfl.db`** | **No. Cannot be earned in time.** Sourcing is unresolved, the factor is untested, and the calibration prior in the mandate applies directly — this is a situation story, which is the project's most reliable way to be wrong |
| **10** | **Rookies** | 6 of the top 150 have no stat history (highest: Jeremiyah Love, consensus #33) | — | **No, and it should not be tried.** Rookie draft capital is already cleanly eliminated as an edge channel. The correct action is to **fall back to consensus for rookies and label it on screen**, not to model them |

### 5.2 What "not earnable in time" means here, stated plainly

Items **8, 9, 10** cannot be earned by 7 September, and for each the reason is stronger than "hard":
odds have a measured oracle ceiling of ≤ +0.055 τ_b, coaching has no obtainable source and an
untested premise, rookies are an eliminated channel. Item **6** is the one that is genuinely
*valuable and out of reach* — the room is real and large, and 39 days is not how long it takes.

Items **1 and 2 are the only two that change what the founder can trust on draft day**, and neither
of them makes a single ranking better. They make it possible to know whether it is.

### 5.3 The independent checks — named, not asserted

Per the mandate, nothing here is validated by me:

| claim | who checks it, and how |
|---|---|
| §1.2, the primary metric is structurally blind | `strategist` — this is a methodology defect in `backtest.py`, and the replacement metric must be chosen by someone who did not build the thing it scores |
| §4, the oracle ladder | `strategist` to register before anyone acts; `fable` to attack. It is 12 uncorrected tests on 7 seasons of a 12-team board against a 10-team league |
| §5.0, the acquisition costs | reproducible in 30 seconds by anyone; `data-ops` owns the ingest and will discover if I am wrong |
| whether any of this is good enough to draft on | **not mine.** `strategist` for methodology, `fable` for adversarial review, `backend` for anything that ships |

---

## 6. The build plan

**Founder direction received mid-pass, 2026-07-30, verbatim:**

> "Let's prioritize bottoms up. I think availability is probably most based on ADP, then the way the
> draft has fallen so far, other teams needs etc. The recommender would depend on both."

He has ordered the three questions into a dependency chain they did not previously have:
**bottom-up → availability → recommender.** §1.1 is why that ordering bites. The shipped board is
within-position identical to consensus, so availability is currently simulating a draft over
consensus ordering, and the recommender's opportunity-cost term is pricing "value now vs. value at
my next pick" entirely out of four slopes. **A wrong ranking does not stay contained; it makes both
downstream models confidently wrong.** Fixing the ranking is the only one of the three that improves
the other two for free.

### 6.1 Step 0 — the metric has to change before anything is built. This is a finding, not a delay.

§1.2 measured per-position τ_b at exactly **0.000000** between the board and raw consensus, twelve
of twelve position-seasons. Build a component projection, grade it with that instrument, and you
have graded it with a ruler that already cannot distinguish the incumbent from consensus.

**I am not choosing the replacement.** What I can supply is the missing half of the problem: the
incumbent's error, on the metric the product actually displays, which had never been measured.

**The bar.** Shipped `projected_points` against realised points, walk-forward (curve for season S
fitted only on `fantasypros_ecr` seasons < S), universe = that season's consensus board, busts
retained at zero, 2025 untouched:

| season | QB | RB | WR | TE |
|---|---|---|---|---|
| 2022 | 76.8 | 53.3 | 46.4 | 32.6 |
| 2023 | 80.5 | 62.3 | 49.4 | 38.0 |
| 2024 | 64.7 | 70.4 | 48.2 | 36.9 |
| **mean MAE (points)** | **74.0** | **62.0** | **48.0** | **35.8** |
| MAE ÷ mean actual points | 0.30 | 0.40 | 0.32 | 0.31 |

**The number on the screen is wrong by about a third of what the player scores.** That is the bar,
it is unambiguous, and any bottom-up projection either beats it or does not.

This metric has three properties the current primary lacks: it is **sensitive to player-level
opinion**, it does **not** require demonstrating "beats consensus on rank order" (§1.4 shows that is
unreachable at this sample size at three of four positions), and it is **exactly what the founder
asked for** — projections.

**Systematic, worth flagging, not yet a finding:** the QB curve's bias runs **+33.4, +36.8, −15.3**.
Three seasons; noted, not acted on.

### 6.2 Step 1 — measure the component models against the incumbent. Nobody has.

`component-model-*-pass-1.md` measured the component models against consensus ADP, prior-season
points, and weighted prior PPG. **They were never measured against the thing actually shipped**, and
never on projection error. That comparison is the cheapest real answer available: both objects
exist, both are committed, no new model is required.

**One structural fix belongs here, and it is about power, not accuracy.** The head-to-head is
currently limited to **three seasons (2022–2024)** — not by the component models, which have seven
(FFC ADP 2018–2024), but by the incumbent, whose training source `fantasypros_ecr` starts in 2021
and so cannot produce a walk-forward curve before 2022. Refitting the same object
(`E[our_points | positional market rank]`) on FFC ADP instead yields **six** evaluation seasons.
That doubles the power of every board-vs-anything comparison at zero model complexity.

**Caveat, and `strategist` must rule on it.** Today's H1 result measured **NULL**: ADP is *not* more
accurate than expert consensus at predicting realised pick order (mean gap −1.27 picks, in the
incumbent's favour). So this substitution must be argued as **a longer rank series for power**, not
as "ADP is a better input." Those are different claims and only the first is supportable.

### 6.3 Step 2 — re-enable baseline #1, knowing what it can and cannot settle

**Wiring: small.** `experiments/bottomup/components/adp_baseline.py` already loads FFC half-PPR ADP
and matches **998 of 998 players to gsis ids across 2018–2024, all four positions — 100%.** Promoting
it to `src/` and building a `RankingConfig` is hours.

**Statistically: it cannot settle the question, and that must be said when it is enabled.** Usable
board-vs-market-ADP evaluation seasons are the intersection of *board-buildable* (2022+) and *FFC ADP
coverage* (≤2024), minus the sealed holdout: **2022, 2023, 2024 — three seasons.** A sign test on
three seasons floors at p = 0.25. Re-enabling the arm converts a **"never measured"** into a
**measured-but-underpowered** result. That is worth doing — a known-inconclusive number beats a blank
— but it will not tell the founder whether the board has edge, and §6.2's FFC refit is what raises
it to six.

FFC history is **12-team** against a **10-team** league. Real confound, must travel with the number.

### 6.4 Step 3 — the smallest genuinely bottom-up thing, and it already exists

**The minimum real projection is not a new model. It is the component models, pointed at 2026.**
They project games · volume · efficiency · touchdowns · fumbles · per-game exceedance from player
inputs, they beat naive persistence on **every component at all four positions**, and
`pos_model.score_components()` re-scores them under any ruleset without refitting. Building a second
one would be the over-engineering finding this project treats as a defect.

What stands between them and a 2026 number, in order:

1. **Freeze the decision** — which requires §6.1's metric and §6.2's comparison first. `holdout.py`'s
   own design releases 2025 for the production refit *after* selection is frozen, never before.
2. `release_for_final_fit(reason=...)`, then `FIRST, LAST` extended to a 2026 target
   (`run_position.py:36`). **Not in this pass; the holdout stays sealed.**
3. **Rookies fall back to consensus and are labelled on screen.** Six of the top 150 have no stat
   history, the highest being Jeremiyah Love at consensus #33. Rookie draft capital is an already-
   eliminated edge channel — modelling them is the wrong move and consensus is the honest one.
4. **DEF stays a blank with a note.** A starting slot with zero coverage; that does not change by
   September.

### 6.5 Step 4 — one factor at a time, and only two candidates fit the window

Both are **already in `data/nfl.db`** and **untouched by any model in this project**:

| candidate | coverage | why it is the right size |
|---|---|---|
| `snap_counts` | 2013–2025, 324,611 rows | the documented route-participation proxy `CLAUDE.md` §5 names; WR pass 1 deliberately withheld it so as not to contaminate a baseline pass. That baseline now exists |
| `ngs_*` | 2016–2025, 26,723 rows | separation, cushion, time-to-throw — the only in-DB signal not derived from box score volume |

Each is one pre-registered factor with a falsifier and a stopping condition, registered by
`strategist` before running, evaluated against §6.1's bar. **Two, not twenty** — §6.3's
multiple-comparisons exposure applies to the campaign, not per test.

### 6.6 What cannot be earned by 7 September — separately from what is merely hard

| | status | reason |
|---|---|---|
| Vegas odds / implied team totals | **cannot be earned** | historical odds need a paid source, *and* the whole team-environment channel is bounded at **≤ +0.055 τ_b by oracle**. The second reason is the better one |
| Coaching / coordinator tendency | **cannot be earned** | PFR 403, no table has ever landed, premise untested. The mandate's calibration prior applies squarely: this is a situation story |
| Rookie projection | **cannot be earned, and should not be attempted** | eliminated channel; use consensus and label it |
| The rate channel in full (§4, +0.35–0.44 ρ) | **cannot be earned** | real, large, and not a 39-day object. §6.5 is the slice of it that fits |
| DEF edge | **cannot be earned** | coverage can be added; a defensible *ranking* cannot |
| **Beating consensus on rank, demonstrably** | **cannot be earned at QB, WR, TE** | measured, not assumed: seven seasons cannot show consensus beats a three-line heuristic at those positions. **Only RB has power.** Do not design toward it |
| PBP + the four factors it unblocks | **hard, not impossible** | 20.4 s to acquire; ingest and *one* registered factor fits, all four with campaign-level multiplicity control does not |

### 6.7 Sequencing, one line each

1. `strategist` rules on the primary metric (§6.1) — **blocking; nothing should be built first**
2. `data-ops` ingests the half-minute of missing data (§5.0) — parallel, blocks nothing
3. Component models vs. the incumbent on projection error, FFC-refit curve for six seasons (§6.2)
4. Baseline #1 re-enabled with its power caveat attached (§6.3)
5. Two registered factors, snaps and NGS (§6.5)
6. Only then: freeze, release the holdout for the production refit, produce 2026 (§6.4)

**Steps 1 and 2 are the only ones that can start today, and step 1 is not mine to do.**

---

## 7. Status of this document

**Settled:** §0 preconditions and the two extra precondition findings; §1.1–§1.3; §2 (the board is
consensus at ρ 0.972 in the top 100, and its whole opinion is a QB/TE positional tilt); §3.1 (the
projection's own noise band is 1.4–2.4× the positional value range); §3.3 (the database inventory,
measured table by table).

**Exploratory, must not be quoted as a finding:** §4, the oracle ladder.

**Not judged here, by design:** whether any of this is good enough for 7 September. That is not the
ranker's call to make about the ranker's own object. Independent checks are named in §6.

**Still open:** nothing in this pass. The build plan in §6 is a plan, not a result — every step in it needs the check named beside it.
