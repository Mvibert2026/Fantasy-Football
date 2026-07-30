# FR-085 — does early-round RB underperformance support Zero RB?

**Ranker, 2026-07-30.** Founder's words: *"if early round RBs underperform other positions (I assume
mostly WRs) then that makes a case for 0 RB to some extent (especially if the RB deadzone no longer
exists?)"*

Follows `docs/analysis/adp-vs-production-2026-07-30.md` (backend) and my own
`component-model-rb-qb-te-pass-1.md`. Strategy rules were fixed in writing **before** any simulation
ran: `docs/ranking/fr085-strategy-sim-precommit.md`, committed as `a9e3b2b`.

**Exploratory. Nothing here is registered, nothing is confirmatory, and the sealed 2025 holdout was
never opened** — it is excluded in code (`season_vbd()` raises at ≥2025), not by convention.

Code: `experiments/strategy/`. Reproduce with

```
.venv/bin/python -m experiments.strategy.residuals
.venv/bin/python -m experiments.strategy.run_strategies --sims 300
.venv/bin/python -m experiments.strategy.run_strategies --sims 300 --rounds 11   # no-tail check
```

---

## 0. Read this before any number below

**337 interval tests were run across this document** (141 in the residual module, 196 in the
simulation). At the 5% level that is **about 17 false "clears zero" results by chance alone.** Every
result is graded on pass-1 §0's scale, unchanged:

| grade | meaning |
|---|---|
| **SURVIVES** | effect is many times its own standard error; survives any reasonable correction |
| **MARGINAL** | clears zero but a CI endpoint sits near it. **At this test count that is what a false positive looks like.** A hypothesis, not evidence |
| **NULL** | does not clear zero |

---

## 1. Conclusion first

**The premise is half right, the inference from it does not hold, and the strategy question comes
back a clean null.**

**(1) The founder's assumption that the shortfall is "mostly against WRs" is not supported in rounds
1–3.** There the early-round RB underperforms *every* position by a similar amount — WR by 26.6 VBD
points, TE by 28.1, QB by 34.9 — and only the QB comparison (n=14) reaches SURVIVES. It **is**
WR-specific in **rounds 4–8**, where RB − WR is −27.5 [−40.1, −11.9] **SURVIVES** while RB − TE and
RB − QB are both NULL. §2.

**(2) The result is source-dependent, which is the most important caveat in this document.** On
FantasyPros expert consensus over the same 2021–2024 window, early-round RB − WR is **−4.9, NULL**.
On FFC mock ADP restricted to that same window it is −23.0, also NULL. **The "early-round RB is
uniquely overpriced" finding survives only on FFC's full seven seasons, and only as MARGINAL.** §2.1.

**(3) The dead zone is not where the name says it is.** With draft cost held roughly constant by
comparing each RB band against the matching WR band, the classic dead-zone band **RB13–24 is NULL**
(−16.9 [−47.5, +18.1]). The two bands that survive are **RB1–6** (−58.2, SURVIVES — but poorly
controlled, see §3) and **RB25–36** (−26.0 [−39.1, −12.5], SURVIVES, and *well* controlled: mean
overall pick 76.8 vs 73.5). §3.

**(4) Nothing has measurably changed over time, and the design cannot see a change if there were
one.** Every per-season trend in every band is NULL, with intervals spanning ±15 to ±25 VBD points
per year against effects of order 30. "The dead zone no longer exists" is **not testable at this
sample size** and I am not going to pretend otherwise. §3.1.

**(5) And the strategy question, which is the one that actually matters: Zero RB is not
distinguishable from VBD in this league. On any metric. On either market. At any opponent noise
level.**

| FFC, 7 seasons, primary σ | margin vs VBD | 95% CI | grade |
|---|---|---|---|
| realistic season points | **+0.9** | [−19.8, +21.1] | NULL |
| best-ball season points | +11.0 | [−12.7, +35.7] | NULL |
| **P(make playoffs)** | **+0.000** | [−0.042, +0.041] | NULL |
| **P(win title)** | **+0.001** | [−0.020, +0.023] | NULL |

ECR, 4 seasons: +3.1 realistic points [−13.0, +19.3] NULL, P(playoff) +0.033 [−0.028, +0.093] NULL.
**Both sources, all four metrics, every σ: null.** §5.

**(6) The reason is mechanical and worth more than the null itself. VBD in this league is already a
late-RB strategy.** Under the primary opponent model, plain VBD takes its first RB in **round 6.3 on
average**. Zero RB moves that to 10.7. **Both are already "zero RB" by any conventional definition** —
the founder's question turns out to compare two flavours of waiting, not waiting against not
waiting. §5.1.

**(7) The one thing that did beat VBD is not a strategy at all: doing what the room says.**
`bpa_consensus` — take the highest-consensus player available — is +24.1 realistic points and
**+0.046 P(playoff) [+0.006, +0.096] MARGINAL** against a VBD board built from this league's own
measured replacement levels. That is one MARGINAL among 196 tests and must not be quoted as a
finding, **and it comes with a failure rate**: bpa left an unfillable roster in 4.5% of drafts (it
waits on QB and TE until they run out), and those drafts are dropped, which flatters the 95.5% that
remain. §5.3.

---

## 2. Q1 — is the RB shortfall specifically against WR?

Method reuses backend's residual definition unchanged (`analysis/adp_vs_production.py`), so numbers
are directly comparable to that report. residual = actual VBD − the VBD of the season's own realised
value curve at that player's ADP ordinal. Season-clustered bootstrap, 4,000 reps, **seasons as the
resampling unit**.

**FFC half-PPR 12-team mock ADP, 2018–2024 (7 seasons):**

| round bucket | RB | WR | TE | QB | **RB − WR** | **RB − TE** | **RB − QB** |
|---|---|---|---|---|---|---|---|
| **1–3** | −50.6 SURVIVES | −24.0 SURVIVES | −22.5 NULL | −15.7 MARGINAL | **−26.6 MARGINAL** | −28.1 NULL | −34.9 SURVIVES |
| **4–8** | −24.0 SURVIVES | +3.5 NULL | −8.2 NULL | −27.2 MARGINAL | **−27.5 SURVIVES** | −15.8 NULL | +3.2 NULL |
| **9+** | +34.1 SURVIVES | +58.5 SURVIVES | +64.0 SURVIVES | +10.6 NULL | −24.4 MARGINAL | −29.8 SURVIVES | +23.6 MARGINAL |

**In rounds 1–3 the shortfall is not WR-specific.** It is about the same size against WR (−26.6), TE
(−28.1) and QB (−34.9); the point estimates are within 8 points of each other and only the QB
comparison — on 14 QBs across seven seasons, so the least trustworthy cell in the table — reaches
SURVIVES. **The founder's parenthetical assumption is the one part of his premise the data does not
support.**

**In rounds 4–8 it is WR-specific, and that is the cleanest result in this section.** RB − WR is
−27.5 [−40.1, −11.9] SURVIVES; RB − TE and RB − QB are both NULL. If there is a positional trade
being mispriced, it is *mid*-round RB against *mid*-round WR, not first-round RB against first-round
WR.

### 2.1 Second market, and it disagrees

FantasyPros expert consensus rank, 2021–2024, and FFC restricted to the same four seasons so the
comparison is like for like:

| rounds 1–3, RB − WR | seasons | margin | grade |
|---|---|---|---|
| FFC, full window | 2018–2024 | −26.6 | MARGINAL |
| FFC, ECR-matched window | 2021–2024 | −23.0 | **NULL** |
| **ECR** | 2021–2024 | **−4.9** | **NULL** |

Two things are going on and they should not be conflated. Restricting FFC to 2021–2024 costs
significance (7 seasons → 4), but the point estimate barely moves (−26.6 → −23.0). Switching to ECR
on the *same* seasons collapses the estimate to −4.9. **So the difference is mostly the market, not
the window.** On the expert board, early-round RB, WR and TE all underperform by a similar large
amount (−46.5, −41.7, −56.6): the market is badly calibrated at the top of the draft in general,
without RB being special about it.

In rounds 9+ the two sources agree strongly (FFC RB − WR −24.4 MARGINAL, ECR −25.7 SURVIVES): **late
RBs return less than late WRs on both boards.** That is the opposite of what Zero RB needs to be
true.

---

## 3. Q2 — does the RB dead zone still exist?

The founder flagged this as open. It is testable in shape and **not** testable in trend.

Residual by *positional* ADP rank, FFC 2018–2024. Bands were declared in the code before any number
was read.

| band | mean residual | 95% CI | grade | 2018–20 | 2021–22 | 2023–24 |
|---|---|---|---|---|---|---|
| **RB1–6** | **−89.3** | [−112.7, −66.9] | SURVIVES | −91.3 | −106.8 | −68.9 |
| RB7–12 | −35.3 | [−55.5, −15.1] | SURVIVES | −40.4 | −29.9 | −33.0 |
| **RB13–24** | −32.0 | [−48.6, −13.6] | SURVIVES | −21.3 | −55.7 | −24.1 |
| RB25–36 | −13.2 | [−25.2, −0.5] | MARGINAL | −19.4 | +1.9 | −19.0 |
| RB37+ | **+28.3** | [+14.8, +47.9] | SURVIVES | +8.0 | +33.5 | +39.7 |

Read alone, this says the *worst* value on the RB board is at the very top, not in the dead zone.
**But read alone it is close to meaningless**, because backend's §1.5 objection applies hardest
exactly there: rank-ordered residuals against a skewed value curve regress toward the mean even for a
perfectly calibrated market, and the effect is strongest at the top of the board. The control is to
compare each RB band against the WR band sitting at a comparable place on the same curve:

| comparison | margin | 95% CI | grade | mean overall pick, RB vs WR |
|---|---|---|---|---|
| RB1–6 − WR1–6 | −58.2 | [−80.2, −33.9] | SURVIVES | **4.6 vs 11.1 — poorly matched** |
| RB7–12 − WR7–12 | −19.1 | [−51.9, +12.7] | NULL | 15.5 vs 23.7 |
| **RB13–24 − WR13–24** | **−16.9** | [−47.5, +18.1] | **NULL** | 39.9 vs 43.7 — well matched |
| **RB25–36 − WR25–36** | **−26.0** | [−39.1, −12.5] | **SURVIVES** | 76.8 vs 73.5 — well matched |
| RB37+ − WR37+ | −24.7 | [−44.4, −1.8] | MARGINAL | 123.0 vs 119.9 |

**The mean-overall-pick column is the honest part of this table and I added it precisely so the top
row could not be over-read.** RB1–6 are drafted at mean overall pick 4.6 and WR1–6 at 11.1 — those
are different places on a steeply convex curve, so the −58.2 is *partly* the mechanism backend
warned about, not a pure positional penalty. The two well-matched rows are RB13–24 (NULL) and
RB25–36 (SURVIVES, −26.0).

**So: the classic dead zone, RB13–24, is not distinguishable from the WRs drafted alongside it. The
band immediately after it, RB25–36 — roughly rounds 6–8 — is, by 26 VBD points.** That is the
narrowest, best-supported version of the claim available, and it is one band, not a region.

### 3.1 Has it moved? Unanswerable here, and that is the finding

Every per-season trend, in every band, on both sources: **NULL**.

| quantity | slope | 95% CI | grade |
|---|---|---|---|
| RB1–6 residual | +2.75/yr | [−14.44, +23.63] | NULL |
| RB13–24 residual | −1.03/yr | [−14.71, +12.88] | NULL |
| RB25–36 residual | −0.93/yr | [−8.28, +8.57] | NULL |
| RB37+ residual | +5.49/yr | [−4.29, +20.63] | NULL |
| rounds 1–3 RB − WR gap | +5.66/yr | [−12.76, +16.36] | NULL |

The per-season gap in rounds 1–3 runs −61.7, +6.5, −36.1, −27.5, −54.3, −37.9, **+26.8** (2024). It
is negative in five of seven seasons and swings 88 points between adjacent years. **Seven seasons of
ADP cannot resolve a trend against that much year-to-year noise**, and the intervals say so: they
span roughly ±15 to ±25 points per year against effects of order 30. My own pass-1 §7 detected regime
drift at QB using *twenty-five* seasons of play-by-play. Here there are seven seasons of ADP and no
more exist.

**"Does the dead zone still exist" is therefore not a question this project can currently answer.**
What it can say is that the sign has been stable across all three eras in every band except RB25–36,
and that 2024 was the one clearly contrary season. Closing this properly needs more ADP history —
named as a gap in §7 rather than proxied.

---

## 4. The logical gap, stated plainly

**"Early-round RBs underperform their ADP" and "do not draft early-round RBs" are different claims,
and §2–§3 can only establish the first.**

The residual measures a player against the value curve *at his own draft slot*. The draft decision is
not that. At pick k the question is whether taking RB_i beats taking WR_j **given what will still be
available at your next pick**. An RB who returns less than his slot's curve value is still the
correct pick whenever the drop-off behind him is steeper than the drop-off behind the alternative —
which is the entire content of VBD and is invisible to a rank residual. `CLAUDE.md` §6.6 says this
outright: rank correlation is a proxy, the decision-relevant object is the roster.

There is a second gap, less obvious. The residual is **zero-sum within a season by construction** —
it is a permutation of the same realised values. "RB underperforms" therefore *always* implies "some
other position overperforms", at every ADP slot, in every league, whether or not the market is
mispricing anything. It measures relative mispricing and cannot measure absolute value.

**So the residual finding does not license a draft recommendation, and this document does not treat
it as one.** §5 is the vehicle.

---

## 5. Q3 — the simulation

Rules in the pre-commitment, fixed before running. 10 teams, snake, 16 rounds (one reserved for DEF,
which scores zero for everyone), this league's exact roster shape and scoring with bonuses stacked.
User's draft slot **drawn uniformly 1–10 per simulation**. Common random numbers: every strategy sees
the same slot and the same board-noise realisation for a given (season, sim). 300 sims per cell.

**One improvement over `src/draft_sim.py` worth naming.** That module's assumption 1 states the
opponent noise σ "is NOT fitted to anything: no observed draft-position data exists in this repo or
is obtainable." **That is no longer true.** FFC ships a per-player `std_dev` of realised mock-draft
pick position over 700–1,300 drafts per player, rising from ~1.2 picks at the top of the board to
~12 by round 8. That is the primary σ here. The old flat sweep {5, 10, 20} runs as sensitivity.

### 5.1 What the strategies actually did

FFC, primary σ, pooled over seven seasons:

| strategy | best-ball pts | realistic pts | P(playoff) | P(title) | **mean round of first RB** |
|---|---|---|---|---|---|
| VBD | 2003.2 | 1782.1 | 0.398 | 0.096 | **6.33** |
| Zero RB | 2014.2 | 1783.1 | 0.398 | 0.097 | **10.71** |
| Robust RB | 2008.6 | 1798.3 | 0.411 | 0.115 | 1.00 |
| Balanced | 1992.2 | 1796.2 | 0.427 | 0.105 | 3.68 |
| BPA-consensus | 2016.4 | 1806.2 | 0.443 | 0.112 | 1.77 |

**The first-RB column is the finding underneath the null.** VBD, with no positional rule of any kind
and this league's measured RB30 replacement level, already waits until **round 6.3**. It does that
because RB value-over-replacement crosses zero at RB30 while WR's runs to WR40, so once the top backs
are gone — and at the primary σ the room takes them almost deterministically — the highest-VBD player
is a receiver for several rounds running.

**So "VBD vs Zero RB" in this league is round 6.3 against round 10.7.** It is not a test of drafting
backs early against not drafting them early. Nobody had checked this, and it reframes the question
the founder asked.

### 5.2 The comparison

FFC, 7 seasons, primary σ, paired by season, resampling seasons. Minimum attainable two-sided
sign-test p at n=7 is **0.0156** — stated so the power ceiling is visible in the result rather than a
footnote.

| vs VBD | realistic pts | best-ball pts | P(playoff) | P(title) |
|---|---|---|---|---|
| **Zero RB (ban 4)** | +0.9 [−19.8, +21.1] NULL | +11.0 [−12.7, +35.7] NULL | **+0.000** [−0.042, +0.041] NULL | **+0.001** [−0.020, +0.023] NULL |
| Zero RB (ban 3) | +1.2 NULL | +11.2 NULL | +0.001 NULL | +0.001 NULL |
| Zero RB (ban 5) | +1.4 NULL | +11.5 NULL | +0.001 NULL | +0.000 NULL |
| Zero RB (ban 6) | −0.2 NULL | +9.6 NULL | −0.002 NULL | +0.000 NULL |
| Robust RB | +16.2 NULL | +5.5 NULL | +0.013 NULL | +0.019 NULL |
| Balanced | +14.1 NULL | −10.9 NULL | +0.030 NULL | +0.009 NULL |
| BPA-consensus | +24.1 [−1.6, +54.6] NULL | +13.3 NULL | **+0.046 [+0.006, +0.096] MARGINAL** | +0.016 NULL |

ECR, 4 seasons, primary σ (minimum attainable sign-test p is **0.125** — *no* result on this board can
reach conventional significance regardless of effect size):

| vs VBD | realistic pts | P(playoff) |
|---|---|---|
| Zero RB | +3.1 [−13.0, +19.3] NULL | +0.033 [−0.028, +0.093] NULL |
| Robust RB | −1.1 NULL | +0.003 NULL |
| Balanced | +13.9 NULL | +0.022 NULL |
| BPA-consensus | +21.8 NULL | +0.032 NULL |

**Every Zero RB margin against VBD, on both markets, on all four metrics, at every σ, is NULL.** The
title-probability point estimate is +0.001 on a base of 0.096. The ban-length sweep — 3, 4, 5, 6
rounds, all declared in advance and none selected on — moves nothing on FFC, and on ECR the longer
bans drift mildly negative (ban 6: −24.2 realistic points, still NULL).

**"Zero RB is not distinguishable from VBD in this league" is the answer, and it is a real answer.**

### 5.3 Three things that qualify it, none of which rescue Zero RB

**BPA-consensus has a failure rate and it is not in the headline number.** Taking the highest-
consensus player available left a roster that could not field a legal lineup in **96 of 2,100 FFC
drafts (4.5%)** — it defers QB and TE until both run out, since a 10-team room drafts 20 QBs from a
board carrying about 20. Per the pre-commitment those are recorded as failed runs, not as zero-point
seasons. **The +24.1-point margin is therefore measured only on the 95.5% of drafts where it worked**,
which flatters it. Zero RB and VBD failed in 0–13 drafts depending on σ.

**Metrics A and B bracket the truth from opposite sides and both are reported.** Best-ball flatters
deep, high-variance rosters (it is an upper bound no manager reaches); realistic — start your
highest-valued players who actually appeared that week — flatters top-heavy rosters and allows no
in-season skill. Zero RB's margin is mildly positive on A (+11.0) and flat on B (+0.9) on FFC, which
is the direction you would expect if its advantage lives in bench optionality. Both are NULL.

**Board depth required a construction on FFC and did not on ECR.** FFC boards carry 112–171 offensive
players against the 150 a 15-round offensive draft needs. Layers per season: 2018 needed 34 tail
players, 2019 needed 19, and **2020–2024 needed none**. ECR needed none in any season.

The declared **11-round sensitivity** (110 offensive picks, below the smallest market-only board, so
**no synthetic-tail player can be drafted by anyone**) reproduces the null and is the cleaner run of
the two on that axis. FFC, primary σ, vs VBD:

| vs VBD, 11 rounds | realistic pts | P(playoff) | P(title) |
|---|---|---|---|
| **Zero RB** | **+9.0** [−18.0, +37.0] NULL | **+0.017** [−0.036, +0.067] NULL | **+0.002** [−0.014, +0.020] NULL |
| Robust RB | +59.3 [−7.8, +125.1] NULL | +0.054 NULL | +0.052 [+0.006, +0.118] MARGINAL |
| Balanced | +53.8 [−3.5, +107.9] NULL | +0.079 NULL | +0.053 [+0.008, +0.108] MARGINAL |
| BPA-consensus | +71.9 [−5.8, +145.6] NULL | +0.078 NULL | +0.046 NULL |

**Zero RB is null again. What changes at 11 rounds is that the roster-aware strategies get better** —
Robust RB and Balanced both go MARGINAL positive on title probability, and every margin grows. That
is the expected direction: with only 11 picks there is no bench to absorb a positional hole, so
filling starters early is worth more. Two MARGINALs among 196 tests, so hypotheses, not findings —
but the direction is consistent across four strategies and both metrics, and it is the opposite of
what Zero RB predicts.

### 5.4 Draft slot

P(make playoffs) by slot group, FFC primary σ. Zero RB does not become correct from any seat:

| strategy | picks 1–3 | picks 4–7 | picks 8–10 |
|---|---|---|---|
| VBD | 0.760 | 0.777 | 0.781 |
| Zero RB | 0.714 | 0.750 | 0.745 |
| Robust RB | 0.750 | 0.778 | 0.788 |
| BPA-consensus | 0.777 | 0.774 | 0.796 |

*(Slot table is from the last σ cell run and is reported as a diagnostic, not a headline; the paired
comparisons in §5.2 are the evidence.)*

---

## 6. Which factor families were considered, per position — and which were carried over from WR

The founder's note — *"maybe different factors apply for different positions, so just using the WR
model on others doesn't make sense"* — is right one level up from what pass-1 §2 answered. Pass-1
established that the *component structure* is position-specific. It did not establish that the
*factor families considered* were. They largely were not. Naming that is the deliverable:

| position | families used here | position-specific reason, or carried over from WR |
|---|---|---|
| **RB** | positional ADP band, receiving share of touches, team carry share, snap share | receiving share and carry share are genuinely RB-shaped (committee vs. bell-cow). **Round bucket and ADP band are carried over from the WR framing with no RB-specific justification.** |
| **WR** | aDOT / air yards, target share, ADP band | native — this is where the family came from |
| **TE** | aDOT, target share, snap share | **carried over from WR wholesale.** The TE-specific concept (in-line vs. slot deployment) is not derivable from anything in `nfl.db` |
| **QB** | rushing share of points, ADP band | rushing share is QB-specific and was added for that reason |

**Named in the founder's list, testable from `nfl.db`, tested here:** committee vs. bell-cow (team
carry share and receiving share of touches — see `docs/ranking/fr086-volatility.md` §2 and
`fr095-dimension-stability`), QB rushing floor as a separate driver (tested), WR air-yards family
(tested).

**Named, and NOT testable — no proxy built, work stopped rather than faked:**

| factor | why not |
|---|---|
| Team run-block / o-line quality | **not in `nfl.db` in any form.** No PFF, no ESPN line rankings, no adjusted line yards |
| Vegas implied team totals, game script | **not in `nfl.db`.** `odds_snapshots` is in the `CLAUDE.md` §4 schema and has never been built |
| Goal-line share, distinct from red-zone usage | needs play-by-play. **There is no pbp table in `nfl.db`** — only aggregated weekly stats |
| Route participation rate | **not available.** `snap_counts` (2013+) gives offensive snap share, which I use and label `[PROXY]` everywhere it appears. A blocking TE and a route-running TE are the same row |
| In-line vs. slot deployment | needs alignment data. Not present |
| Pace / PROE | needs play-by-play |
| Coordinator identity | **`play_callers` is EMPTY.** data-ops is on it in parallel |

The first four are the ones I would most want. **`odds_snapshots` is the cheapest of them** — it is
already in the schema, the data is free, and implied team total is the single most direct proxy for
the game-script mechanism the founder named for RB.

---

## 7. What I am not claiming

- **Not claiming Zero RB is bad.** It is *indistinguishable*, which is different. Every interval
  contains zero.
- **Not claiming VBD is good.** It did not beat following consensus either — BPA-consensus outscored
  it on every metric, MARGINAL on one. That is one MARGINAL among 196 tests and I am not quoting it
  as a finding, but the direction is not encouraging for a board built from a positional-rank curve.
- **Not claiming early-round RBs are correctly priced.** RB25–36 is a well-controlled SURVIVES.
- **Not claiming the dead zone has or has not gone.** §3.1 — unanswerable at seven seasons.
- **Not claiming the simulator is calibrated.** Opponents do not adapt to the user, which makes
  reaching look cheaper than it is and biases toward whichever strategy reaches. σ is now measured
  rather than guessed, which is an improvement, not a solution.
- **Not claiming this generalises to a 10-team market.** No 10-team historical ADP exists in this
  project. §2 of the pre-commitment states the substitution and its direction.

## 8. What should happen next

1. **`strategist` should decide whether anything here is worth registering.** My reading is: not
   Zero RB (a null with tight intervals is already the answer), possibly RB25–36 relative pricing.
   Thread opened (`docs/handoffs/NEW-fr085-fr086-methodology-review.md`).
2. **The binding constraint on Q2 is ADP history, and it is a data problem, not a method problem.**
   Seven seasons cannot resolve a trend. `researcher` should be asked what pre-draft ADP exists
   before 2018 and on what terms.
3. **`odds_snapshots` should be built.** Named in `CLAUDE.md` §5 and §4's schema, never built, and it
   is the only cheap route to the game-script factor the founder named for RB.
4. **Do not spend the sealed 2025 holdout on any of this.** Nothing here is close enough to a
   positive to justify it.
