# Bottom-up ranking — research pass 2

## Where in the draft the tight-end mispricing can actually be spent

**Ranker, 2026-07-29.** Answers FR-039. **Exploratory.** Nothing here is confirmatory, nothing is
registered, no multiplicity correction is applied, and no result may be reported as an edge. Every
number is a hypothesis. The one confirmatory test worth running is registered as an *ask* in
thread **087** and has not been run.

Code: `experiments/bottomup/pass2_te_adp.py` (committed). Data: `data/nfl.db`, scored through
`src/scoring.py` with the real league config, stacking bonuses included.

**Look-ahead posture.** The market snapshot is `rankings` where
`source='fantasypros_ecr' AND is_preseason_final=1` — one snapshot per season, `as_of_date` in late
August, strictly before Week 1. Features for target season N read seasons ≤ N−1 only. Season **2025
is sealed**; no 2025 outcome was read. Two 2025 *pre-draft* rows were read (§4) and that judgment
call is referred to `strategist` in thread 087 rather than made here.

**Survivorship posture — this is the specific way this analysis fails, so it is stated first.** The
universe for season N is *every tight end on that season's pre-draft consensus list* — 75 to 95 TEs,
published in August, frozen before a snap was played. Tight ends who never took an NFL snap that
season score **0** and are **retained** (4–8 per season). Nothing in this document is defined by
having scored points. Building the universe from TEs who produced would have deleted every
late-round bust — which is most of them — and manufactured exactly the answer the request was
hoping for.

---

## 1. The three answers, in the order they were asked

### 1.1 Where the mispricing sits — **flat in error, front-loaded in accessible value**

Two measurements that look opposed. Both are real and the tension between them is the finding.

**(a) Consensus is equally wrong at every TE price.** Fit `points ~ a + b·ln(overall ECR rank)` per
season per position, take residuals. Residual scale by pre-draft band:

| band | TE1-3 | TE4-6 | TE7-10 | TE11-16 | TE17-24 | TE25-40 |
|---|---|---|---|---|---|---|
| **TE residual RMSE (pts)** | 45.9 | 51.0 | 45.7 | 43.5 | 41.0 | 43.4 |
| RB, comparable bands | 104.7 | 81.0 | 72.3 | 64.0 | 61.2 | — |
| WR, comparable bands | 80.6 | 52.0 | 56.5 | 64.3 | 57.8 | — |

**At TE, and only at TE, the size of the market's error does not shrink as the player gets
cheaper.** At RB it falls by 40%. That is the honest form of "TE is unpriced across the board", it
is new, and it is the strongest thing in this pass that supports the founder's instinct.

**(b) But error is not opportunity, and the *accessible* value is steeply front-loaded.** Hit rates,
universe frozen pre-season, Wilson 95% intervals, n = 4 seasons pooled:

| pre-draft band | overall ECR range | n | **P(realised top-6 TE)** | P(realised top-10 TE) | top-6 by season |
|---|---|---|---|---|---|
| **TE1-3** | 6–51 | 12 | **66.7%** [39.1, 86.2] | 75.0% [46.8, 91.1] | 2, 2, 2, 2 |
| **TE4-6** | 48–77 | 12 | **41.7%** [19.3, 68.0] | 41.7% [19.3, 68.0] | 2, 1, 1, 1 |
| **TE7-10** | 75–113 | 16 | **25.0%** [10.2, 49.5] | 43.8% [23.1, 66.8] | 0, 1, 2, 1 |
| **TE11-16** | 99–148 | 24 | **4.2%** [0.7, 20.2] | 20.8% [9.2, 40.5] | 0, 0, 0, 1 |
| **TE17-24** | 140–209 | 32 | **9.4%** [3.2, 24.2] | 18.8% [8.9, 35.3] | 1, 1, 1, 0 |
| **TE25-40** | 172–353 | 64 | **3.1%** [0.9, 10.7] | 10.9% [5.4, 20.9] | 1, 0, 0, 1 |

There is **no late-round bump.** The decline is steep and it does not reverse. The intervals are
wide — every one of them overlaps its neighbour — but TE1-3 and TE11-16 do not overlap at all, and
that is the comparison the request turns on.

**(c) The decisive measurement: most of the late TE hits were never draftable.** Of the 24 top-6 TE
seasons in 2021–2024, **7 came from pre-draft TE11+**. Of those 7, only **2 sat inside the 150 picks
of a 10-team, 15-round draft** — and only **1** after adjusting for the measured ECR→ADP shift (§5).

| season | finish | pre-draft | overall ECR | inside 150 picks? | player |
|---|---|---|---|---|---|
| 2021 | TE3 | TE34 | 265 | **no** | Dalton Schultz |
| 2021 | TE6 | TE17 | 140 | yes | Rob Gronkowski |
| 2022 | TE5 | TE22 | 158 | **no** | Evan Engram |
| 2022 | TE6 | TE46 | 346 | **no** | Taysom Hill |
| 2023 | TE1 | TE19 | 161 | **no** | Sam LaPorta |
| 2024 | TE1 | TE11 | 103 | yes | Brock Bowers |
| 2024 | TE4 | TE26 | 204 | **no** | Jonnu Smith |

**Five of the seven were waiver-wire adds, not late-round picks.** They are the memorable cases, and
they are memorable precisely because they were free. In the band that actually *is* the last four
rounds — overall ECR 111–150 — **2 of 27 TEs finished top-6, 7.4% [2.1, 23.4]**, and the two were a
32-year-old Gronkowski and David Njoku at TE10. Neither is the unknown breakout the strategy imagines.

**So, plainly: the strategy as stated is not supported. The mispricing does not concentrate where
the founder wants to spend it.**

### 1.2 The part of his instinct that survives, and it is the actionable half

The finding does **not** argue "take a tight end early." It argues for a window one to three rounds
*earlier than he aimed and still nowhere near early*: **TE7-10, overall ECR 75–113, rounds 8–11.**

The reason is cost. Mean realised VBD (10-team, QB10 / RB30 / WR40 / TE10 replacement) of every
player on the consensus list in the overall ECR 75–113 window:

| position | n | mean VBD | P(VBD > +30) | E[VBD ǀ VBD > 0] |
|---|---|---|---|---|
| **TE** | 23 | **−12.2** | 21.7% | 41.9 |
| **WR** | 53 | **−12.2** | 26.4% | 45.2 |
| RB | 51 | −22.7 | 25.5% | 47.0 |
| QB | 29 | −56.3 | 17.2% | 44.4 |

**A tight end taken in rounds 8–11 costs exactly what a wide receiver costs at the same pick — the
same number to one decimal — and buys a 25% shot at a top-6 TE.** That is the cheapest real version
of the founder's idea, and it is a genuinely different recommendation from both "take one early" and
"wait for the last rounds".

Against it, the late-round alternative, using the measured 7.4% for ECR 111–150:

| strategy | picks spent | P(≥1 top-6 TE) |
|---|---|---|
| one TE in the TE7-10 window | **1** | **25.0%** |
| two darts at ECR 111–150 | 2 | 14.3% |
| three darts at ECR 111–150 | 3 | 20.6% |

**One mid-round pick beats three late-round darts and costs two fewer picks.**

One shape worth naming because it is the strongest remaining argument *for* late TE, and it does not
survive scrutiny. At overall ECR 140–210: TE mean VBD **−42.8** against WR −55.6 and RB −63.8 — a
late TE dart really is less bad on average. But P(VBD > +30) is TE **4.5%**, WR 4.7%, RB 5.9%.
**Late tight end has a higher floor and no better ceiling.** For a strategy whose entire premise is
finding upside, that is the wrong shape — and in a league whose stacking bonuses reward ceiling, it
is the wrong shape twice over.

### 1.3 Are late TE hits forecastable? — **No. And "take more shots" does not rescue it either.**

Base rate per late shot (pre-draft TE11-40, 120 player-seasons): top-6 **5.0%** [2.3, 10.5]; top-10
**15.0%** [9.7, 22.5].

AUC computed **within each season** and then averaged — pooling ranks across seasons would compare a
2021 player to a 2024 player — bootstrap resampling the 4 seasons. Hit = realised top-6 TE:

| signal | AUC | per-season |
|---|---|---|
| NFL draft capital (overall pick) | 0.713 [0.50, 0.90] | 0.37, 0.92, 0.89, 0.67 |
| **expert `rank_best` (most optimistic expert)** | **0.692 [0.61, 0.78]** | 0.64, 0.57, 0.72, 0.83 |
| **consensus ECR rank within the band** | **0.649 [0.56, 0.74]** | 0.50, 0.62, 0.72, 0.75 |
| rookie flag | 0.644 [0.47, 0.83] | 0.48, 0.45, 0.95, 0.70 |
| prior-year snap share (`snap_counts`, proxy) | 0.630 [0.36, 0.89] | 0.89, 0.64, —, 0.36 |
| age (younger better) | 0.587 [0.38, 0.83] | 0.41, 0.34, 0.97, 0.62 |
| prior-year targets | 0.517 [0.23, 0.81] | 0.86, 0.76, 0.05, 0.40 |
| prior-year games | 0.508 [0.17, 0.83] | 0.95, 0.53, 0.05, 0.50 |
| **expert disagreement (`spread_sd`)** | **0.487 [0.41, 0.56]** | 0.50, 0.38, 0.59, 0.48 |
| prior-2yr ppg | 0.362 [0.11, 0.61] | 0.61, 0.62, 0.05, 0.17 |

**Only two signals have intervals excluding 0.5, and both are the market restated** — the consensus
rank itself, and the single most optimistic expert on the panel. Everything genuinely new is a coin
flip. The per-season columns are the honest picture: with one or two hits per season these estimates
swing from 0.05 to 0.95 and back.

Three specific kills worth recording:

- **Expert disagreement is dead.** `spread_sd` was my one cheap, novel, already-in-the-database
  hypothesis — "the experts disagree about him" as a mispricing tell. It runs 0.487, 0.500, 0.432
  across three band/threshold configurations. Nothing.
- **Prior points-per-game runs the wrong way** at TE11-40 (0.362). Late tight ends coming off better
  seasons hit *less* often. That is consistent with the market pricing exactly that information.
- **The composite I built post hoc (snap share × rookie draft capital) scored 0.752 [0.60, 0.90]**
  and I am not reporting it as a finding. It was constructed after seeing the component results, on
  four seasons, as one of a hundred-plus comparisons. It is what an overfit looks like.

**So neither actionable form works.** "Take the right one" fails because nothing knowable separates
them. "Take more shots" fails on arithmetic: three darts at 7.4% is 20.6%, still below one mid-round
pick at 25.0%. The correct conclusion is a third one — **take one, earlier, in the window where it
is free.**

### 1.4 The Kraft case — **the pattern does not recur, and the example is misremembered**

Going into 2025, **Tucker Kraft was consensus TE11 at overall ECR 105**, coming off a **TE9 finish
in 2024** (138.3 points, 17 games). His 2023 was TE28, 63.0 points. Adjusted by the measured TE
ECR→ADP shift (§5), his real draft cost was around pick **117 — round 12 of 15**.

The 2025 preseason TE board, as the market saw it:

> TE1 Bowers (17) · TE2 McBride (19) · TE3 Kittle (31) · TE4 Hockenson (64) · TE5 LaPorta (69) ·
> TE6 Kelce (75) · TE7 Njoku (84) · TE8 Engram (85) · TE9 Andrews (88) · TE10 Warren (104) ·
> **TE11 Kraft (105)** · TE12 Ferguson (110)

**He was not a late-round unknown. He was a mid-round tight end off a top-10 season, priced one slot
outside the starter tier** — that is, sitting exactly on the TE7-10/TE11-16 seam this pass
identifies as the value window. The market had already repriced him a full year before the season
being remembered. Correctly priced, the founder's own example supports §1.2, not §1.1.

**No 2025 outcome was read.** The two 2025 rows above are pre-draft rankings — features, carrying
zero information about what happened. Thread 087 asks `strategist` to confirm that is clean.

**The pattern, tested rather than assumed.** "Kraft type" defined entirely pre-draft: pre-draft
TE11+, third NFL season or earlier, drafted by an NFL team. 2021–2024:

| group | n | P(top-6 TE) | P(top-10 TE) |
|---|---|---|---|
| Kraft-type | 107 | **1.9%** [0.5, 6.6] | 6.5% [3.2, 12.9] |
| other late TE | 197 | **2.5%** [1.1, 5.8] | 6.1% [3.5, 10.3] |

**No advantage. Marginally worse.** The pattern the example represents does not recur.

A narrower cut does show something, and it is exactly the kind of thing this project has been wrong
about before: young **and** top-100 NFL draft capital gives top-10 rate 14.6% [6.9, 28.4] against
4.9% [2.9, 8.3], from 41 players and 6 hits. Rookie draft capital is an **already-eliminated channel
project-wide** (`experiments/bottomup/REPORT.md`), this is one of a hundred-plus comparisons here,
and the calibration prior — four of five registered predictions wrong, every miss over-crediting a
situation story — applies directly. **Recorded at half weight. Not a finding.**

---

## 2. What I am escalating rather than celebrating

**TE1-3 produced exactly two top-6 tight ends in each of the four seasons: 2, 2, 2, 2.** Under a
binomial with p = 0.667 the chance of landing on exactly two is 0.444 per season, so 3.9% across
four. That is unusual enough to name. I do not think it is leakage — the input is a pre-draft
ranking and the outcome is realised points, with no path between them — but **the stability must not
be read as precision.** The interval on that 66.7% is [39.1, 86.2] and the four-season regularity is
almost certainly coincidence.

Nothing else in this pass looks too good. Most of it is null.

---

## 3. Hypotheses generated, and their status

| Hypothesis | Status |
|---|---|
| TE mispricing is back-loaded, exploitable in the last rounds | **Rejected.** §1.1 |
| TE mispricing is front-loaded, so take a TE early | **Not supported either.** TE1-3 hits most often but costs picks 6–51, where the VBD alternatives are far better |
| **TE7-10 (rounds 8–11) is VBD-free and buys a 25% top-6 shot** | **Live. The one worth confirming.** Registered as an ask in thread 087, not run |
| Consensus error scale is flat across TE price, unlike RB/WR | **Live, unexplained, and new.** No mechanism proposed. Worth a pass of its own |
| Expert disagreement (`spread_sd`) flags mispriced late TEs | **Killed.** 0.487 / 0.500 / 0.432 |
| Prior ppg identifies late TE breakouts | **Killed**, runs backwards (0.362) |
| Snap share as a route-participation proxy identifies late TE hits | **Not supported at TE11+** (0.630 [0.36, 0.89]). Absorbs the queued TE arm on `snap_counts`; it was the right idea and it does not work in this band |
| Young + early NFL draft capital at TE11+ | Half weight, eliminated channel, one of many comparisons. **Not a finding** |
| Late TE has a higher floor than late RB/WR | **Supported** (mean VBD −42.8 vs −55.6 / −63.8) but with **no better ceiling** (4.5% vs 4.7% / 5.9%) |

---

## 4. What I need that does not exist

| Need | Why it binds here | Route |
|---|---|---|
| **Historical market ADP** | There is **no ADP history in the database at all** — only FantasyPros ECR, 2021–2025. Every "late round" claim in this pass uses ECR rank as a draft-cost proxy. `docs/research/historical-adp-availability-2026-07-29.md` establishes FFC half-PPR is obtainable for 2018–2024, which would take this from 4 seasons to 7 and replace the proxy with a real draft position | Thread **055**, already OPEN to `data-ops`. This is now the binding constraint on FR-039, not a nice-to-have |
| Expert consensus before 2021 | 24 top-6 TE outcomes total is the entire evidence base | Thread **084**, OPEN |
| 2025 outcomes | The founder's own example sits in the sealed holdout and cannot be examined without spending it | Thread **087** asks whether it is worth spending |

---

## 5. The proxy error, measured rather than assumed

ECR rank is not ADP. Measured on the only season where both exist — 2026 FFC half-PPR 10-team
against 2026 ECR, matched on name:

- All positions, n = 179: median ADP − ECR **−2**, IQR [−14, +5], mean absolute difference 19.0
- **Tight ends only, n = 18: median ADP − ECR = +12**, IQR [+4, +16]

Tight ends go **later** in real drafts than their expert rank. So the ECR-rank equivalent of the
150th pick is roughly ECR 138, which *tightens* §1.1(c) — the count of draftable late TE hits falls
from 2 of 7 to 1 of 7. **The proxy error runs against the founder's hypothesis, not for it.** One
season and eighteen tight ends is a weak calibration and it is stated as one.

---

## 6. Method, and the checks applied

- **Look-ahead:** structural. 2025 outcomes never read; the market snapshot is a dated pre-Week-1
  file; features read seasons ≤ N−1 only. Two 2025 pre-draft rows read, declared, referred to
  strategist.
- **Survivorship:** universe frozen from the pre-season consensus list; never-played TEs scored 0
  and retained; realised finish computed across *all* tight ends in `player_weekly_stats`, not just
  list members, so a hit from outside the list would have been visible (there were none).
- **Within-season statistics:** every rank-based statistic is computed inside a season and then
  averaged. An earlier pooled version of the same table is discarded — pooling ranks across seasons
  compares a 2021 player to a 2024 player and inflates AUC through between-season composition.
- **Uncertainty:** Wilson intervals on every rate; bootstrap resampling **seasons** (not players),
  seed 20260729, 4000 draws, per `docs/statistical-guardrails.md` §7. With n = 4 the intervals are
  wide and coarse; per-season values are printed alongside every headline so the spread is visible
  rather than hidden inside an interval.
- **Multiple comparisons: not corrected.** Well over 100 descriptive quantities. This pass is
  exploratory and no result is claimed as significant. Nothing new survived even *uncorrected*,
  which is why the negative is reportable; thread 087 asks strategist to confirm that reading.
- **Known impurity:** 3 of 344 consensus-listed TEs had a non-TE realised modal position (Jacob
  Harris ×2, Connor Heyward) and are scored as non-hits. Their combined realised total is 14.1
  points; the effect is nil.
- **Band sensitivity, found while verifying the committed script and worth recording as a trap.**
  The forecastability band is **TE11-40**, not TE11-open. Letting the band run to the end of the
  consensus list (TE41-95, overall ECR 300+) moves the same AUCs to 0.826 / 0.860 / 0.629 / 0.555 /
  0.803 — every signal appears to work, including the ones killed above. Nothing changed but the
  denominator: separating a top-6 tight end from TE80 is trivial and is not the decision anyone
  faces. **Any late-round AUC quoted without its band is uninterpretable**, and the flattering
  version is the one an unconstrained analysis produces by default.

**Reproduction:** `.venv/bin/python experiments/bottomup/pass2_te_adp.py --db data/nfl.db` prints
the hit-rate table, the draftability table, the TE7-10 cost table and the AUC table. Verified
2026-07-29 to reproduce every headline figure in §1 exactly.

**What would falsify the main conclusion:** real ADP history (thread 055). If tight ends' true draft
positions diverge from ECR rank far more than the 2026 calibration suggests, the draftability
argument in §1.1(c) — which is doing most of the work — weakens, and the late band could contain
more genuinely draftable hits than measured here.
