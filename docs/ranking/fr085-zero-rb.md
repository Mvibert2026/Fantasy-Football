# FR-085 — does early-round RB underperformance support Zero RB?

**Ranker, 2026-07-30.** Founder's words: *"if early round RBs underperform other positions (I assume
mostly WRs) then that makes a case for 0 RB to some extent (especially if the RB deadzone no longer
exists?)"*

Follows `docs/analysis/adp-vs-production-2026-07-30.md` (backend) and my own
`component-model-rb-qb-te-pass-1.md`. Strategy rules were fixed in writing **before** any simulation
ran: `docs/ranking/fr085-strategy-sim-precommit.md`, committed as `a9e3b2b`.

**Exploratory. Nothing here is registered, nothing is confirmatory, and the sealed 2025 holdout was
never opened** — it is excluded in code (`season_vbd()` raises at ≥2025), not by convention.

---

> ## CORRECTION, 2026-07-30 (FR-109) — read before §1(6), §5.1 and §5.4
>
> The founder challenged §1(6) — *"there's not 60 better players than the first rb"* — and he was
> right. **He was right about the claim and wrong about the cause, and the claim was mine.**
>
> | | |
> |---|---|
> | **Is the VBD arm mis-specified?** | **No.** At pick 1 the highest-VBD player on the board is RB1, and the arm takes him. Audit dump in **§5.5**. |
> | **Was "VBD takes its first RB in round 6.3" a sound thing to report?** | **No.** 6.33 is the mean of a violently bimodal distribution, and it is the single most extreme cell in the run's own σ grid. |
> | **Does the Zero RB null inherit a defect?** | **Not from the arm.** The arm behaves as the pre-commitment defines it. What the null does inherit is a **contrast problem** — see §5.4. |
> | **Was anything else wrong?** | **Yes, one real code bug.** §5.4's slot table was printed from the σ=20 sensitivity cell, not the primary σ. Fixed; §5.4 replaced. |
>
> §1(6), §5.1's closing two paragraphs, and all of §5.4 are **withdrawn and replaced**. The §5.2
> margins are unchanged and were not recomputed — nothing found in the audit touches them.
> Audit code: `experiments/strategy/audit_vbd.py`, `why_first_rb.py`, `slot_sweep.py`.

Code: `experiments/strategy/`. Reproduce with

```
.venv/bin/python -m experiments.strategy.residuals
.venv/bin/python -m experiments.strategy.run_strategies --sims 300
.venv/bin/python -m experiments.strategy.run_strategies --sims 300 --rounds 11   # no-tail check
```

---

## 0. Read this before any number below

**347 interval tests were run across this document** (151 in the residual module, 196 in the
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

**(4) The founder's recollection that the dead zone "used to be a thing but now is not" is not
supported, and the finding he is remembering is not in this repo** — `docs/test-registry.md` test 43
has never been run. Measured directly, 2018–20 against 2022–24: **RB13–24 is NULL and points the
wrong way (−13.4), RB25–36 is NULL (+7.5).** What *did* move is the far end of the board — **RB37+
improved by +48.3 [+21.6, +75.1] SURVIVES against the WRs drafted alongside them.** So the
supportable statement is "late-round RB got better relative to late-round WR", **not** "the dead
zone went away". One SURVIVES among 151 tests, so a hypothesis. §3.2.

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

> **(5, qualification added 2026-07-30 after the FR-109 slot sweep.) The null stands, and it is
> weaker evidence than it reads as.** Measured at every fixed draft slot, **Zero RB and VBD draft
> 94–96% of the same players at slots 5–10** — VBD is already waiting there, so seven of the ten
> seats carry almost no treatment. The contrast the founder is asking about lives at slots 1–3, where
> the arms still share 83–87% of a roster and the per-slot intervals are ±60 to ±100 realistic points
> on seven seasons. **"Not distinguishable" is correct; "tested" is generous.** §5.4.

**(6) — WITHDRAWN 2026-07-30 (FR-109). The original text is struck through below; the replacement
follows it.**

> ~~**The reason is mechanical and worth more than the null itself. VBD in this league is already a
> late-RB strategy.** Under the primary opponent model, plain VBD takes its first RB in **round 6.3
> on average**. Zero RB moves that to 10.7. **Both are already "zero RB" by any conventional
> definition** — the founder's question turns out to compare two flavours of waiting, not waiting
> against not waiting.~~

**(6, replacement) VBD is an elite-RB-or-nothing strategy, and "round 6.3" is a mean of a
distribution that has almost no mass anywhere near 6.** Measured over 2,100 drafts at the primary σ:
**44.6% take an RB in round 1**, 44.0% take their first RB in round 11 or 12, and **rounds 3–5
together account for 0.5%** — 11 drafts out of 2,100, with **none at all in round 3**. At slot 1 the
arm takes RB1 with the first overall pick in **100%** of drafts; at slot 10, in 22%. The mean was
reported without its distribution and it described a behaviour the model essentially never exhibits.
§5.5.

Two further things make the original sentence indefensible rather than merely imprecise. **6.33 is
the most extreme value in the run's own 14-cell sensitivity grid** — every other (board, σ) cell puts
VBD's first RB between round 1.17 and 4.64, and on the *second* market board (ECR) it is **1.39 at
the primary σ**. And the round-11/12 mode is not a value judgement at all: **94% of those picks are
driven by the positional-need penalty**, the amendment to the pre-commitment, not by the RB being the
best player available. §5.5.

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

### 3.2 "It used to be a thing and now is not" — the direct test, and what it actually shows

The founder recalls a finding that the RB dead zone **used to be a thing but now is not, and a
reason why**. Before measuring anything: **that finding is not in this repo.** `docs/test-registry.md`
line 210, test 43 — *"RB dead zone by round, our scoring"* — is still `SPEC` and has never been run.
So either he is recalling outside commentary, or a measurement exists that never reached a durable
document. **"We never measured this" is the honest help**, and it is the first half of the answer.

The second half is that a slope over seven noisy seasons has almost no power (§3.1), so here is the
more direct instrument: a straight early-era vs late-era contrast, per band, with an interval — and
the same contrast run on the **RB minus matched-WR gap**, which holds draft cost roughly constant.

**2018–2020 against 2022–2024. Positive = the band got better (less underpriced).**

| band | late − early | 95% CI | grade | same, on the RB − WR gap | grade |
|---|---|---|---|---|---|
| RB1–6 | +20.1 | [−16.7, +58.6] | NULL | +29.4 [−8.9, +67.7] | NULL |
| RB7–12 | −2.0 | [−44.0, +38.4] | NULL | −5.4 [−74.1, +63.3] | NULL |
| **RB13–24** | **−13.4** | [−45.7, +21.6] | **NULL** | −2.2 [−61.0, +68.6] | NULL |
| **RB25–36** | **+7.5** | [−19.2, +31.2] | **NULL** | +11.7 [−9.9, +33.3] | NULL |
| **RB37+** | **+40.1** | **[+7.1, +87.3]** | **MARGINAL** | **+48.3 [+21.6, +75.1]** | **SURVIVES** |

**The dead zone has not measurably weakened, and I am not going to characterise it as having
moved.** Both dead-zone bands are NULL, and RB13–24 — the classic definition — has a point estimate
pointing the *wrong* way (−13.4, i.e. slightly worse in the recent era, not better). There is no
honest reading of this table in which the mid-round RB penalty went away.

**What did change is at the other end of the board.** RB37+ improved by +40.1 VBD points, and
against the WRs drafted alongside them by **+48.3 [+21.6, +75.1], SURVIVES** — the best-controlled
cell in the contrast, since those bands sit at mean overall picks 123.0 and 119.9. Late-round backs
have become materially better value relative to late-round receivers.

**That is one SURVIVES among the 151 interval tests in this module and it is a hypothesis, not a
finding** — but it is worth stating precisely, because it is close enough to what the founder
remembers to be mistaken for it. The supportable statement is:

> *Not* "the dead zone stopped being a thing." What is measurable is that **late-round RB got better
> relative to late-round WR** between 2018–20 and 2022–24. The mid-round penalty is unchanged.

If the recollection is really "you can wait on RB now", the data is consistent with that — but via
the *late* tier improving, not via the *middle* tier recovering, and those imply different draft
behaviour. A mechanism for it (higher RB committee turnover, more in-season role change reaching
waivers) is **not** tested here and I am not going to supply one to fit the shape of the result.

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

**The two paragraphs that stood here are WITHDRAWN (FR-109, 2026-07-30).** They read the 6.33 mean as
a description of the strategy. It is not one — see §5.5 for the distribution, the σ grid, and the
cause breakdown. The point estimates in the table above are arithmetically correct and unchanged;
what was wrong was the interpretation placed on the last column, and the fact that a mean was
reported for a bimodal quantity with no interval and no distribution. That is the failure mode
`CLAUDE.md` §6 exists to prevent, and I committed it in the same document that names it.

The one part of the withdrawn text that survives audit is the *within-round-1* mechanism: RB
value-over-replacement does cross zero at RB30 while WR's runs to WR40, so after the top handful of
backs are gone the highest-VBD player is a receiver for a long stretch. What that produces is not
"VBD waits until round 6" — it is **"VBD takes an elite RB if one is on the board at its first pick,
and otherwise takes no RB on value grounds again for the rest of the draft."** Those are different
claims and only the second is supported.

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

### 5.4 Draft slot — REPLACED 2026-07-30 (FR-109)

> **The table that stood here was from the wrong σ cell, and it was a code bug, not a wording
> slip.** `run_strategies.py` assigned `playoff_rate_by_slot` *after* the σ loop closed, reading a
> dict that is rebound at the top of every σ iteration — so the only slot table ever written was the
> **last** cell (flat σ=20), while the heading said "FFC primary σ". The tell was visible and I
> missed it: its VBD row averaged 0.77 against a primary-σ pooled P(playoff) of **0.398** three
> sections above. Confirmed against the stored run — flat20's pooled VBD P(playoff) is 0.774.
> Fixed; the value is now recorded per σ.
>
> ~~| strategy | picks 1–3 | picks 4–7 | picks 8–10 |~~
> ~~| VBD | 0.760 | 0.777 | 0.781 | Zero RB | 0.714 | 0.750 | 0.745 |~~
> ~~| Robust RB | 0.750 | 0.778 | 0.788 | BPA-consensus | 0.777 | 0.774 | 0.796 |~~

The replacement is a proper sweep: every arm run at **every fixed slot 1–10** rather than a slot
drawn per simulation. FFC, primary σ, 300 sims × 7 seasons **per slot**
(`experiments/strategy/slot_sweep.py`, `data/qa/fr109-slot-sweep-ffc-r16.json`).

**Mean round of first RB, by slot.** This replicates §5.5.2 with fixed rather than drawn slots:

| slot | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **VBD** | **1.00** | 1.61 | 3.63 | 6.34 | 7.86 | 8.69 | 8.55 | 8.14 | 8.52 | 8.30 |
| Zero RB | 10.65 | 10.74 | 10.81 | 10.81 | 10.75 | 10.67 | 10.70 | 10.69 | 10.69 | 10.67 |
| gap | **9.65** | 9.13 | 7.18 | 4.47 | 2.89 | **1.98** | 2.15 | 2.55 | 2.17 | 2.37 |

**And the number that matters most in this whole document — roster overlap with the VBD arm:**

| slot | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Zero RB** | 0.825 | 0.836 | 0.870 | 0.913 | 0.943 | **0.960** | 0.955 | 0.941 | 0.946 | 0.947 |
| Robust RB | 0.822 | 0.798 | 0.765 | 0.732 | 0.705 | 0.694 | 0.696 | 0.713 | 0.715 | 0.714 |
| Balanced | 0.699 | 0.682 | 0.642 | 0.613 | 0.593 | 0.589 | 0.576 | 0.589 | 0.603 | 0.622 |
| BPA-consensus | 0.468 | 0.442 | 0.421 | 0.385 | 0.360 | 0.361 | 0.388 | 0.383 | 0.385 | 0.426 |

**At slots 5–10, Zero RB and VBD draft 94–96% of the same players.** Seven of the ten seats produce
almost no contrast at all, because VBD is already waiting there. The comparison the founder actually
asked about — draft an elite back early, or don't — **exists only at slots 1–3**, and even there the
two arms share 83–87% of a roster.

That is the honest qualification on §5.2, and it is a power statement, not a result: **the pooled
null is measured across ten seats of which roughly three carry the treatment.** It does not make the
null wrong. It does mean "Zero RB is not distinguishable from VBD" is substantially a statement about
seats where nobody was proposing to draft an RB early in the first place.

**Per-slot margins vs VBD, realistic points** (the full four-metric grid is in the JSON):

| slot | Zero RB | Robust RB | Balanced | BPA-consensus |
|---|---|---|---|---|
| 1 | +23.0 [−64.4, +106.4] | +2.5 | +26.2 [+3.1, +52.7] MARG | +15.7 |
| 2 | +10.8 [−27.8, +49.7] | +13.0 | +18.4 | +6.5 |
| 3 | −19.1 [−88.6, +41.3] | +22.3 | +6.7 | −13.1 |
| 4 | +8.6 | +67.3 [+0.5, +135.4] MARG | +0.0 | +61.1 [+0.8, +128.4] MARG |
| 5 | +16.1 | +21.5 | +19.3 | +59.1 |
| 6 | +6.2 | +3.2 | +28.7 [+0.4, +53.4] MARG | +46.1 |
| 7 | −5.4 | +33.7 | +21.9 | +53.6 |
| 8 | −10.1 | +43.2 | +11.8 | +26.7 |
| 9 | −16.3 | +15.7 | +1.3 | +4.2 |
| 10 | −21.5 [−73.1, +6.9] | −20.3 | +2.5 | −5.9 |

**Every Zero RB cell is NULL at every seat.** The point estimates drift from positive at slots 1–2 to
negative at slots 7–10, which is *directionally* the opposite of the usual Zero RB argument (it is
supposed to help most from the back of the round, where no elite back is available). **That drift is
a hypothesis and nothing more** — this sweep runs **160 interval tests**, at 5% expects ~8 false
"clears zero" results, and observed **5 MARGINALs**. Fewer than chance would hand you. Nothing in
this table is evidence of anything.

**What the sweep does establish is negative and worth stating plainly:** with 7 seasons the per-slot
intervals are ±60 to ±100 realistic points at the very seats where the strategies differ. **This
design cannot answer the founder's question at slots 1–3 at any effect size he would care about.**
Splitting by slot buys resolution on *mechanism* and costs all remaining power on *outcome*. Anyone
wanting an outcome answer at a specific seat needs a different design, and `strategist` should
specify it before it is run rather than after.

---

## 5.5 FR-109 — the audit of the VBD arm

The founder's objection, verbatim: *"Hard for me really to believe vbd doesnt take a RB before 6th
round. Maybe a certain slot. But there's not 60 better players than the first rb. I have real
questions about that test."*

Both halves are correct. There are not 60 better players than the first RB — **the model agrees, and
always did.** And "maybe a certain slot" is exactly the shape of the distribution.

### 5.5.1 The dump — what the arm actually sees at pick 1

Top 10 available by the simulator's own VBD, 2022 FFC board, primary σ, seed `20260730+season*1000`,
sim index 0. This is the raw output of `experiments/strategy/audit_vbd.py`.

```
-- overall pick 1 (round 1) -- USER ON THE CLOCK; user roster so far: empty
    # pos   raw VBD  VBDrank  need pen    score consensus  name
    1 RB      229.5        1       0.0      1.0         1  Jonathan Taylor
    2 RB      206.5        2       0.0      2.0         2  Christian McCaffrey
    3 WR      180.8        3       0.0      3.0         4  Justin Jefferson
    4 RB      174.7        4       0.0      4.0         3  Derrick Henry
    5 WR      162.9        5       0.0      5.0         6  Cooper Kupp
    6 RB      154.5        6       0.0      6.0         5  Dalvin Cook
    7 WR      140.3        7       0.0      7.0         8  Ja'Marr Chase
    8 RB      135.3        8       0.0      8.0         7  Najee Harris
    9 WR      128.2        9       0.0      9.0        13  Davante Adams
   10 RB      121.0       10       0.0     10.0         9  Joe Mixon
```

**The best player on the board by VBD is RB1, the second-best is RB2, and five of the top ten are
running backs. The arm takes Jonathan Taylor first overall.** The need penalty is zero at pick 1 for
every player, so nothing is being suppressed. There are not 60 better players than the first RB;
there are none.

What the arm goes on to draft from slot 1, same draft:

```
 rd  ovr  pos      VBD  VBDrk  cons  name
  1    1  RB     229.5      1     1  Jonathan Taylor
  2   20  WR     111.2     13    20  CeeDee Lamb
  3   21  WR     103.7     15    22  Deebo Samuel Sr.
  4   40  WR      70.0     30    40  Jaylen Waddle
  5   41  WR      66.0     32    41  DJ Moore
  6   60  WR      47.3     46    57  DeAndre Hopkins
  7   61  WR      44.4     48    59  Brandin Cooks
  8   80  QB       7.4     80    79  Dak Prescott
  9   81  TE       5.5     83    91  Zach Ertz
 ...
  first RB round = 1
```

And the same draft from **slot 10**, which is where the "waits until round 6" impression came from:

```
-- overall pick 10 (round 1) -- USER ON THE CLOCK; user roster so far: empty
    # pos   raw VBD  VBDrank  need pen    score consensus  name
    1 WR      128.2        9       0.0      9.0        13  Davante Adams
    2 WR      118.1       11       0.0     11.0        14  Stefon Diggs
    3 TE      112.8       12       0.0     12.0        18  Travis Kelce
    4 WR      111.2       13       0.0     13.0        20  CeeDee Lamb
    5 RB      107.2       14       0.0     14.0        10  Austin Ekeler
    ...
-- overall pick 20 (round 2) --
   ... best available RB is #17 on this list: RB Leonard Fournette raw VBD 61.2
-- overall pick 40 (round 4) --
   ... best available RB is #18 on this list: RB Elijah Mitchell raw VBD 32.8
-- overall pick 60 (round 6) --
   ... best available RB is #16 on this list: RB Rashaad Penny raw VBD 13.1
```

**This is the mechanism, and it is legible.** At pick 10 the best available RB is the model's 5th-best
player, 21 VBD points behind the best WR — a close call, not a dismissal. Ten picks later the best
available RB has dropped from 107 to 61 while the best available WR has only dropped from 128 to 111.

The reason is that the market itself front-loads running backs. Mean composition of the consensus
top 20 and top 25 over 2018–2024: **RB 11.6 / WR 7.4** in the top 20, RB 13.0 / WR 9.7 in the top 25.
**Roughly 58% of the first two rounds of the room are spent on backs.** So by the user's second pick
the RB pool has been stripped to its 12th-best member while the WR pool is still on its 8th, and the
RB curve is far steeper than the WR curve in exactly that range. After that the RB curve never
recovers.

Note what that implies about the founder's original question. A strategy that takes an elite back at
pick 1 and then no back for ten rounds is not a rejection of running backs — **it is the model saying
the room is already paying full price for RB2 through RB12, so buy the one player whose price is
right and let the room have the rest.**

### 5.5.2 The distribution behind the 6.33 mean

`experiments/strategy/audit_vbd.py`, ffc, primary σ, 300 sims × 7 seasons = 2,100 drafts.

| first-RB round | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drafts | **937** | 27 | **0** | 2 | 9 | 66 | 28 | 10 | 20 | 74 | **476** | **449** | 2 |

Mean 6.33, median 7.0, and **round 6.3 is a value the arm essentially never produces**. By slot:

| slot | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean first-RB round | **1.00** | 1.64 | 3.80 | 6.22 | 7.47 | 8.73 | 8.98 | 8.17 | 8.28 | 8.46 |
| median | 1 | 1 | 1 | 6 | 11 | 11 | 11 | 11 | 11 | 11 |
| share taking RB in round 1 | **100%** | 90% | 68% | 44% | 35% | 22% | 22% | 29% | 20% | 22% |

The founder's "maybe a certain slot" is the whole of it.

### 5.5.3 Why the arm takes the RB when it does

Every first-RB pick classified at the pick itself (`experiments/strategy/why_first_rb.py`, 200 sims ×
7 seasons × 10 slots = 14,000 drafts). **VALUE** = the RB had the highest *raw* VBD of all available
legal players. **PENALTY** = he did not, and only won once the positional-need penalty was added.
**FORCED** = legality had removed every non-RB option.

| | VALUE | PENALTY | FORCED |
|---|---|---|---|
| pooled | **54.2%** | 45.8% | **0.0%** |
| slot 1 | 100.0% | 0.0% | 0.0% |
| slot 3 | 80.4% | 19.6% | 0.0% |
| slots 5–10 | 32–39% | 61–68% | 0.0% |
| first RB in rounds 1–7 | ~100% | ~0% | 0.0% |
| first RB in rounds 11–12 | 6% | **94%** | 0.0% |

**The two modes have different causes.** Round 1 is the arm buying the best player on the board.
Rounds 11–12 are the **need penalty** — 25 rank units per surplus at 6 WR, plus the QB/TE caps of 2 —
finally making a replacement-level RB the least-penalised option. Those late RBs carry raw VBD of
roughly 0 to −50. **Legality never forces the pick; the penalty does.**

That penalty is the amendment I made to the pre-commitment after the smoke test, and it is doing
about half the work in the headline number I reported. That is exactly the kind of load an
after-the-fact amendment should not silently carry, and it is why the amendment needed the
`strategist` ruling I asked for before, not after, the number was quoted to the founder.

### 5.5.4 Is 6.33 even a property of the strategy? No — mostly of σ

The same quantity across every cell the run already computed:

| board / σ | measured | flat 5 | flat 10 | flat 20 |
|---|---|---|---|---|
| **FFC, 16 rounds** | **6.33** | 3.36 | 1.83 | 1.24 |
| FFC, 11 rounds | 4.64 | 2.64 | 1.62 | 1.20 |
| **ECR, 16 rounds** | — | 2.08 | **1.39** | 1.18 |
| ECR, 11 rounds | — | 1.72 | 1.33 | 1.17 |

**6.33 is the single most extreme value in its own 14-cell grid**, and the primary cell on the second
market board is 1.39. The FFC measured σ is very small at the top (~1.2 picks at pick 1), so the room
takes the elite backs in near-deterministic order and they simply never reach slots 5–10. Loosen σ
and they do, and the arm takes them. **The first-RB round is measuring how often an elite RB falls to
you, not what the VBD rule prefers.** Reporting it as the latter was the error.

### 5.5.5 Reconciliation against the ledger's 168.5 / 153.2 / 114.1 / 73.1

FR-109 asserts these two cannot both be right. **They can, and both are.** They are different
estimators of the same object, and they agree on the ordering that matters.

VBD of the positional rank-1 slot, mean 2021–2024:

| | RB | WR | QB | TE |
|---|---|---|---|---|
| **simulator** (finish-rank curve, `experiments/strategy/board.py`) | **223.1** | 178.6 | 107.1 | 109.5 |
| **shipped board / ADR-016** (log-linear on *consensus* rank, `src/make_board.py`) | **168.5** | 153.2 | 114.1 | 73.1 |
| my reconstruction of ADR-016's form on the FFC board | 171.9 | 151.3 | 118.3 | 100.8 |

**RB1 is the highest-VBD slot in this league under both estimators**, which is the claim FR-109
thought was contradicted. It is not. The simulator's arm acts on it: it takes RB1 first overall
whenever RB1 is on the board at its first pick.

They are not the same number, and the difference is real and should be recorded:

- The simulator reads **finish**-rank curves (mean season total of whoever *finished* RBk) at a
  player's **consensus** positional rank. The shipped board fits `points ~ α + β·ln(consensus rank)`.
  Finish ranks are order statistics, so the simulator's curve is inflated — ratio 1.1–1.5× at the top
  of each position and 1.5–2× deeper.
- **ADR-016 explicitly settled against conditioning on the outcome** (*"That conditions on the
  outcome. What a drafter actually chooses is a draft slot"*). The pre-commitment specified a
  finish-rank curve anyway, and I did not notice the conflict. **That is an undeclared departure from
  a settled ADR** and it is mine.
- It does **not** explain the behaviour under audit. The round-2 RB-vs-WR call comes out the same way
  under both curves: finish-curve RB12 69.6 vs WR8 94.9 (WR +25.3); consensus-curve RB12 46.3 vs WR8
  66.0 (WR +19.7). The estimator changes the magnitudes, not the decision.
- Second undeclared departure: the pre-commitment says *"mean points per game … multiplied by the
  target season's scheduled game count"*; the code uses **season totals rescaled by the games ratio**.
  `board.py` documents the choice and I think it is the better one, but the pre-commitment was never
  amended to say so.

### 5.5.6 QB crowd-out — tested directly, and it is not the mechanism

Raised 2026-07-30: the shipped board places QB1 at overall **6** against a consensus of 26, so a
highest-VBD arm might be taking quarterbacks in round 1 and crowding out the backs. The shipped-board
figures reproduce exactly (`data/export/board.json`: QB1 +20, QB2 +19, QB3 +16, QB4 +14 vs consensus,
inverting from QB9). **But the simulator does not draft from that board**, and on the board it does
draft from the effect is much smaller and is not the cause:

| | |
|---|---|
| simulator board's overall VBD rank of its own best QB, 2018–2024 | **15, 16, 14, 13, 16, 14, 11** (consensus 18–27) |
| QBs the arm takes before its first RB, pooled | **0.98** |
| WRs the arm takes before its first RB, pooled | **3.26** |
| share of those QBs taken in round 1 | **0.000** |
| mean round of a pre-first-RB QB | 4.92 (median 4) |
| at slot 1 | 0.00 QB, 0.00 WR, 0.00 TE — RB1 goes first overall |
| at slots 6–10 | 1.3–1.5 QB against 4.5–4.8 WR |

**The answer to "is it two or three QBs inside the first four rounds" is no: it is about one QB,
typically round 4–5, against three times as many receivers.** The crowd-out is WR, not QB. The
board-level QB concern is real and belongs to the shipped board — it is a different object with a
different owner and it should be raised there, not resolved here.

### 5.5.7 The parameter that actually decides this, and it was never tested

Both baselines in play are "teams × starting slots": QB10 / RB30 / WR40 / TE10. The alternative
principle — replacement sits where a position becomes *freely replaceable*, i.e. at the last player
actually rostered — gives, measured from the FFC board's own top 150 (10 teams × 15 offensive
rounds), a mean composition of **QB 24 / RB 54 / WR 57 / TE 15**.

| baseline | RB | WR | QB | TE | RB12 vs WR8 (the round-2 call) |
|---|---|---|---|---|---|
| starting slots (current) | 223.1 | 178.6 | 107.1 | 109.5 | **WR by 25.3** |
| last rostered | 282.6 | 210.0 | 218.0 | 125.4 | **RB by 2.8** |

**The round-2 decision that produces the entire late-RB behaviour flips sign under a baseline choice
that is at least as defensible as the one used.** Neither is obviously right — the "last rostered"
depth for QB (24 in a 1-QB, 10-team league) is itself a product of draft convention rather than
scarcity, and it drives QB1's VBD to 218, which is plainly wrong for this format.

**This is the single most influential free parameter in the whole exercise and no version of this
document has tested it.** It is not adjacent to test-registry #35 (global flex baseline, closed NULL
by backend) — #35 replaced all four baselines with one; this is a per-position question. It needs a
pre-registered test owned by `strategist`, not a number chosen here after seeing which way it goes.

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
