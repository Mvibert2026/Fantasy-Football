# Strategic insights ledger

**Purpose.** The accumulating record of what we have actually measured, written in decision language
rather than statistical language. This is the source document for the eventual **Draft Guide**
(FR-098) — that guide should be assembled from this file, not reconstructed from scattered agent
reports.

**Rules for this file.**

1. **Nothing enters without a grade and a source.** Every row names the document it came from.
2. **Negative results are first-class.** Most of what is below is negative. That is the honest state
   of the work and the guide must say so — a draft guide that only lists what worked would misrepresent
   how much is actually known.
3. **Confidence language is fixed and means what it says:**
   - **SURVIVES** — effect is many times its own standard error; would survive any reasonable correction
   - **MARGINAL** — clears zero but an interval endpoint sits near it. *This is what a false positive
     looks like.* A MARGINAL row is a hypothesis, never advice.
   - **NULL** — does not clear zero
   - **UNTESTED** — no measurement exists. Never present as knowledge.
4. **Edited in place when superseded**, never appended-to. Same discipline as
   `docs/assistant-context.md`, for the same reason: a log of superseded figures stated in the
   present tense is how a document becomes untrustworthy.

---

## 1. The headline: we do not beat the market yet

**Our bottom-up model does not beat consensus ADP at any position.** Reported as a failure per
`CLAUDE.md` §6.5, which requires the comparison against baselines to be the headline rather than the
raw accuracy number.

| Position | Model − consensus ADP | Can the test resolve anything? |
|---|---|---|
| WR | +0.051 | **No power** — seven seasons cannot even show ADP beats a three-line heuristic |
| **RB** | **−0.052** | **Has power.** ADP − heuristic +0.134 [+0.043, +0.223] |
| QB | −0.069 | No power |
| TE | −0.024 | No power |

**Read the right-hand column first.** At WR, QB and TE the experiment cannot resolve the question at
all. At RB it can, and we lose. That makes RB the one position where "we do not beat the market" is a
measurement rather than a shrug — and RB is where this league's scarcity bites hardest.

*Source: `docs/ranking/component-model-rb-qb-te-pass-1.md` §1.*

**Draft-day implication:** none yet. Nothing in our rankings currently justifies departing from
consensus. That is why the app does not show our rankings.

---

## 2. What we have actually established

| Finding | Grade | What it means at the draft |
|---|---|---|
| Component projections beat naive persistence at **every** position | **SURVIVES** | The modelling approach is sound even though it does not yet beat the market. This is the one unambiguous win. |
| **~1 in 4 late-round picks return startable value** — 24.1% [19.1, 30.0] train, 24.5% [14.6, 38.1] holdout, round 10+ | **SURVIVES** (holdout confirmed) | Late rounds are a **volume game, not a selection game.** Across ~6 late picks you expect ~1.5 hits with no skill at all. Agonising over a single round-12 pick is worth less than taking enough shots and cutting fast. |
| Young WR/TE (age ≤ 23) beat ADP by ~35 VBD pts/season, both eras | **MARGINAL** (moderate-high) | A hypothesis worth a pre-registered retest, **not advice**. Held on the full board; underpowered when restricted to late rounds (n=47/8). |
| Early-round RB underperforms same-round peers at other positions by ~3× | **MARGINAL** | Survives an era split; the broader position-level framing did **not** clearly survive the 2024 holdout. Suggestive, not settled. |
| QB passing-bonus calibration drifts **+0.043 per season** [+0.003, +0.084] | **SURVIVES** | Regime change is real and measurable — right in 2014, over-predicting by 40% by 2024. Any model using a fixed passing baseline is wrong and getting wronger. |

---

## 3. What we tested and found nothing

**These are results, not gaps.** Each one tells us where not to spend model complexity.

| Tested | Grade | Note |
|---|---|---|
| Prior-season games missed → ADP mispricing | **NULL** | Not significant; sign order not even monotonic; both extreme buckets flip sign between eras. This is the input every injury-risk product is built on. |
| Team change → ADP mispricing | **NULL** | |
| Prior volume-vs-efficiency split → ADP mispricing | **NULL** | |
| Sleeper screen: young / efficient-low-volume / rising-share | **NULL** | None reached significance *even before* multiple-comparisons correction (raw p 0.209 / 0.643 / 0.266). Rising share **inverted** on its holdout look. |
| Ceiling / stacking-bonus effect at RB (transfer from WR null) | **NULL** | Worth 0.57%–2.39% of realised points; moves **three players by three or more rank positions across 4,792 player-seasons.** |
| "Spike-week players" as an identifiable category (PR-002) | **NULL** | Zero of 36 correlations survived BH correction. |
| QB rushing-regime lag | **NULL** | +0.176 pct-pts/season [−0.105, +0.456]. Expected the model to lag here; it does not. |

**The stacking-bonus null matters for the spec.** `CLAUDE.md` §7 asserts the yardage bonuses "reward
ceiling outcomes over floor, which should influence how variance is valued in rankings." The
arithmetic is fine; the *operational* claim is currently unsupported by two independent measurements.
**Open decision for the founder.** One live test may yet rescue it — see §5.

---

## 4. Things that turned out to be built, broken, or absent

| | |
|---|---|
| **Archetype is already built and exported** — `PlayerDetail.tsx:425` claims otherwise and is wrong. But the labels are badly imbalanced: `RB_COMMITTEE` holds 62.7% of RBs, `TE_SECONDARY_RECEIVER` 51.0% of TEs, and **~34% of eligible players met no criterion at all.** |
| **The injuries table answers the question backwards.** 79,816 rows, read by no model. It captures 26–35% of short absences but only **2.5–4.8% of absences of nine games or more**, because season-ending IR removes a player from the weekly report. *The absences that destroy a season are exactly the ones it cannot see.* |
| **The availability fix that WR pass 1 called "the highest-value fix available"** is real, partially fixable, and **improves the ranking at no position.** The ranker withdrew its own recommendation after measuring it. |
| **`play_callers` was empty.** Now 607 rows (2015–2024, all 32 teams) via Wikipedia — but it is *end-of-season* staff, not who was hired going in. Every row is flagged `is_final_season_snapshot=1`; the look-ahead semantics are unresolved. |
| **No 10-team historical ADP exists anywhere.** All ADP analysis runs on FFC's 12-team archive. A structural source limit, not a gap to chase. |
| **Three industry sources define "bell cow" three incompatible ways**, and our code is a fourth. Only Footballguys and Sharp Football publish checkable numbers at all. |
| **Route participation is genuinely unavailable** in every ingested table. |

---

## 5. Open tests that could still change the picture

| Test | Why it matters |
|---|---|
| **Bust screen** (FR-096) | Must beat two nulls: regression to the mean, and injury. |
| **Run crossover + PR-007** (FR-102) | Does the recommendation ever move off a position being run? And do the unvalidated constants (`+8` / `+18` / `−25`) beat plain VBD? |
| **Age × injury; is the young edge a games-played effect?** (FR-104) | Decides what an existing MARGINAL finding actually *is*. |
| **Playoff-weeks (16–17) schedule quality** (FR-105) | Season-long SOS averages out over 17 games; two playoff games do not. Never examined. Subject to FR-106 — a tiebreaker only. |
| **Season-long SOS, run properly** (FR-105) | `test-registry.md` #12 records "~Zero" in the edge column for a test that has **never been run**. That is received wisdom, not a measurement. |

---

## 5b. Tests closed on 2026-07-30 — answered, moved out of §5

| Test | Answer | Grade |
|---|---|---|
| **Zero RB vs. VBD**, simulated | P(title) **+0.001** [−0.020, +0.023]. Null on every metric, market, σ, depth and ban length. **The mechanical reason matters more than the number: plain VBD already takes its first RB in round 6.3**, so the comparison was 6.3 vs 10.7, not early vs late. VBD is already most of the way to Zero RB without being told. | **NULL** |
| **Positional volatility per roster slot** | Per player WR 1.084 / RB 1.047 / TE 1.002 / QB 0.573. **Per slot the ordering inverts: TE 1.002 (worst) / RB 0.600 / QB 0.573 / WR 0.545 (best).** The TE slot is the most volatile thing on the roster — one skill slot with no diversification. Same-position weekly correlation +0.001 to +0.009, so the √k reasoning holds. RB vs WR per player is a clean null. | **SURVIVES** |
| **Per-player dispersion in the exceedance curve** | Null at every threshold, family and shrinkage, with both arms given the *realised* mean — the most favourable setting available. | **NULL** |
| **Skewness and kurtosis in the exceedance curve** (the founder's actual hypothesis; PM originally mis-relayed it as dispersion) | **Fails upstream, before any model is fitted.** Shape does not persist year to year: rec skew +0.014, rec kurt −0.004, rush skew +0.049, rush kurt −0.031, pass skew +0.071, pass kurt −0.000 — six of six null, two negative. Empirical-Bayes τ̂² for skewness driven to **exactly zero in all five cells** under g1/g2: the estimator, given every chance, concluding there is no between-player variance in true shape beyond sampling noise. **Oracle arm** using the target season's own shape improves log-loss by ≤0.0024 and makes bonus MAE *worse*. | **NULL** |
| **Archetype dimension autocorrelation** | **Close to the reverse of what PM predicted.** Snap share r=+0.707, yards per carry r=+0.175 — **role is more persistent than skill.** The recommended treatment survives but for the opposite reason. Player-level volatility must **not** be an archetype label (persists r≈0.10 vs mean PPG's r≈0.72); role-level can. | **SURVIVES** |
| **Does the RB dead zone still exist / has it moved?** | **Cannot honestly be called moved or vanished.** Era contrast (2018–20 vs 2022–24) on the RB−WR gap: RB13–24 **−2.2 NULL** (pointing the *wrong* way), RB25–36 +11.7 NULL, **RB37+ +48.3 [+21.6, +75.1] SURVIVES**. So "you can wait on RB now" is consistent with the data — but via the **late tier improving**, not the middle tier recovering. Those imply different draft behaviour. One SURVIVES among 151 tests in that module, so: hypothesis. | **MARGINAL** |
| **Consensus (ECR) vs. market ADP** | Pooled on disagreements ECR wins 54.6% [0.491, 0.600] — **crosses 50%, indistinguishable.** Per season, only 2023 clears (0.652 [0.560, 0.734]); the other three sit at a coin flip, so one season carries the pooled result. **The one interaction worth keeping: early-round disagreements (through round 5) favour ECR 59.5% [0.506, 0.678], effect +15.5 VBD pts vs +3.1 late.** Practical read: when the experts and the room disagree early, lean expert; late it doesn't matter. CI *just* clears 0.5 — worth pre-registering, not confirmed. | **MARGINAL** |
| **Late-round sleeper screen** | Base rate **24.1%** [19.1, 30.0] train / 24.5% holdout. No feature separated hits from misses — raw p 0.209 / 0.643 / 0.266, none significant *before* correction; rising share **inverted** on holdout. No flag ships. | **NULL** (base rate SURVIVES) |

**`CLAUDE.md` §7's operational clause now has four independent instruments against it** — the WR
ceiling ablation, the RB stacking-bonus transfer, the dispersion test, and the founder's own
skew/kurtosis mechanism tested at its most favourable setting. The arithmetic in §7 is fine; the
claim that bonuses "should influence how variance is valued" is unsupported. **This is a founder
decision, escalated and not made.**

---

## Appendix A — Backfill: findings that predate 2026-07-30

**Added 2026-07-30 by `librarian`, per founder request** ("I feel like we've had and tested more
and had more insights as well but they come and go"). This appendix recovers measured findings
from research passes, ADRs, the test registry, and pre-registrations written before this ledger
existed. Everything above this line was written today and is untouched. Grading follows the same
scheme (rules at the top of this file); where a source document did not use SURVIVES/MARGINAL/
NULL/UNTESTED itself, it is graded here — conservatively, and marked as such.

Two sourcing notes that apply to every row below:

- The three `docs/ranking/bottom-up-research-pass-*.md` documents and
  `component-model-wr-pass-1.md` are self-described as **exploratory** ("nothing here is
  confirmatory... no result may be reported as an edge"). That caveat is preserved in every grade
  below — a MARGINAL grade here often reflects the source's own hedge, not just a statistical
  borderline.
- `PR-004`, `PR-005`, and `PR-007` are registered but carry no `result:` field — **not run**. They
  are omitted from this backfill entirely per the ledger's own rule (UNTESTED is not knowledge).
  `PR-001` is `FROZEN-FOR-FUTURE` (reopens ~2028 on current trajectory) — its underlying structural
  finding is included below, but its confirmatory predictive test is not, because it was never run.

### A.1 Positional slot value and reach cost (settled-ish)

| Finding | Grade | What it means at the draft | Source |
|---|---|---|---|
| **VBD of the rank-1 slot over replacement, 2021–2025: RB 168.5 [131.9, 217.9] > WR 153.2 [135.6, 172.7] > QB 114.1 [57.0, 155.2] > TE 73.1 [53.3, 93.2].** | **SURVIVES** | RB1/WR1 are worth more than QB1/TE1 in this league's format. Confirms taking RB/WR ahead of QB/TE at the top of the draft. | `docs/test-registry.md` #46 (revised 2026-07-25), corroborated by `docs/decisions.md` ADR-016 |
| **Reaching early for an elite TE or an elite QB costs roster points, and the direction is consistent but not statistically significant.** Elite-TE-early −96.1 pts, QB-early −115.4 pts vs. best-available, negative in 12 of 12 season×sigma cells simulated. | **MARGINAL** (doc's own words: "neither reaches significance — four seasons floor the sign test at p=0.125") | A consistent signal against reaching for TE or QB early, worth weighting as a leaning — not proof. | `docs/test-registry.md` #44/#45/#46, `PR-003` |
| **Hero RB (early workhorse RB, fade WR) does not beat best-available drafting.** Margin −13.3 pts vs. BPA, 95% CI [−98.1, +65.0], 2 of 4 seasons positive, sign p = 1.000 at every opponent-noise setting tested. | **NULL** | No basis for Hero RB as a strategy in this league. Registered, run, clean null. | `PR-003` (status: RUN, pre-registered confirmatory test) |
| An earlier, cruder backtest reported our VBD-ranked-by-last-year's-points model losing to FantasyPros consensus by **−1,070 points** (2025 backtest, point estimate, no CI). | **Discarded as superseded** | Superseded by this ledger's §1 headline (component model vs. ADP, with CIs and a power analysis) — do not cite the −1,070 figure, it predates confidence intervals and per-position baselines being required. | `docs/test-registry.md` Tier 3 #44/#45/#46 note (2026-07-25) |

### A.2 The QB rank-curve "collapse" — genuinely contested, not settled

`docs/decisions.md` contains an ADR (its own `##` header appears to be missing from the file —
content sits between the ADR-059 and ADR-058 entries, referenced elsewhere in the same file as
"ADR-057") that measured the shipped board's QB value slope falling from −66.6 (2021) to −4.1
(2025) and called it a **"monotone collapse,"** real enough to flag the board's flat-pooled curve
as carrying a stale regime. Two later research passes, run the same day, dispute this directly.

| Finding | Grade | Source |
|---|---|---|
| 56.5% of the "elite QB" VBD edge comes from **rushing production, scored at RB rates** — not from passing. Uncontested by either later pass. | **SURVIVES** | `docs/decisions.md`, ADR ~line 2257 (header missing in file; cross-referenced elsewhere as ADR-057) |
| The same document's claim that the 2021→2025 QB slope collapse is **real and monotone** | **CONTESTED — see unresolved conflict, Appendix B** | same ADR |
| The QB rank-curve slope trend 2021–2025 is **[+15.3 slope-units/season, CI −3.5 to +34.1]** — includes zero — and the single flattest point (2025, −4.1) reverses to +28.6 if one player (Jayden Daniels) is dropped. The "collapse" is depth-cut dependent: at draft depth 12 rather than 20, 2021 is the *flattest* season, not the steepest. | **NULL** (does not establish a real collapse) | `docs/ranking/bottom-up-research-pass-3.md` §1(1), §3.1 |
| The QB **realised value spread** (as opposed to the market's ability to order QBs) has been **steepening**, not collapsing, since 1999: −0.461 slope-units/season [−0.874, −0.034]. What actually moved is the market's QB ordering skill, whose 2025 τ_b was −0.042 (slightly worse than random). | **SURVIVES** | `docs/ranking/bottom-up-research-pass-3.md` §3.2 |
| Consensus QB ordering skill has **zero measured year-to-year persistence**: lag-1 r = −0.007 [−0.414, +0.411]. A market that was bad at ranking QBs one year gives no signal about the next. | **NULL** | `docs/ranking/bottom-up-research-pass-3.md` §1(4) |
| RB realised value spread has been **flattening** since 1999: +0.990 slope-units/season [+0.721, +1.274] — the strongest deep-sample trend measured in either pass. | **SURVIVES** | `docs/ranking/bottom-up-research-pass-3.md` §3.2 |
| Recency-weighting the **realised value curve** (not the consensus curve) at QB is strongly supported on a 9-season holdout: RMSE 45.00 → 22.41, Δ −22.6 [−30.3, −13.6]. At WR it is **harmful** (last-1-season fit is +2.75 [+0.96, +4.80] worse). At RB nothing clears zero. At TE it is weak and the training split picked the wrong scheme (a live overfitting demonstration). | **SURVIVES (QB, WR-harmful) / NULL (RB) / MARGINAL (TE)** | `docs/ranking/bottom-up-research-pass-3.md` §4b |
| Under every recency-weighting scheme the data actually supports, the live 2026 board would move **≤1 player in the top 150 by ≥10 places** — the shipped board's own published VBD confidence intervals already say this class of fix is beneath its resolution. | **SURVIVES** | `docs/ranking/bottom-up-research-pass-3.md` §5 |

**Draft-day implication:** none yet, and this is deliberately unresolved — see Appendix B. Do not
treat either "the QB premium is collapsing" or "the QB premium is fine as pooled" as settled.

### A.3 Tight end market structure

| Finding | Grade | What it means at the draft | Source |
|---|---|---|---|
| **TE consensus pricing error does not shrink as price falls**, unlike RB (−40% RMSE) and WR — TE is mispriced roughly equally at every price tier. New, unexplained. | **MARGINAL** (n=4 seasons, doc calls it new and unexplained) | Worth a dedicated pass; not yet actionable. | `docs/ranking/bottom-up-research-pass-2.md` §1.1(a) |
| **The "wait for a late-round sleeper TE" strategy is not supported.** Hit rate falls steeply with pre-draft price and does not bump back up late: TE1-3 66.7% [39.1,86.2] top-6 rate vs. TE11-16 4.2% [0.7,20.2] — non-overlapping intervals. Most remembered late-TE "hits" (Schultz, Engram, LaPorta, etc. — 5 of 7 top-6 finishes from pre-draft TE11+, 2021–2024) were **waiver-wire adds, never inside 150 draft picks.** | **NULL** | Stop planning around a cheap sleeper TE; the anecdotes driving the belief were mostly never draftable. | `docs/ranking/bottom-up-research-pass-2.md` §1.1(c), §1.4 |
| The cheapest real version of "get a TE cheaply": a TE taken **rounds 8–11** (overall ECR 75–113) costs the same VBD as a WR at the same pick and buys a **~25% chance at a top-6 TE finish** — better than three late-round darts (20.6% combined) for two fewer picks spent. | **UNTESTED — registered, not run** (thread 087) | **This is a live hypothesis, not advice.** Do not act on it until the confirmatory test runs. | `docs/ranking/bottom-up-research-pass-2.md` §1.2 |
| Expert disagreement (`spread_sd`) as a late-TE mispricing signal | **NULL** (AUC 0.487–0.500, killed) | | same, §1.3 |
| Prior-season PPG identifying late-TE breakouts | **NULL** — runs backwards (AUC 0.362; better prior seasons predict *worse* late-TE outcomes) | | same, §1.3 |
| "Young TE + early-ish NFL draft capital" (the "Tucker Kraft pattern") recurring as an exploitable signal | **NULL** — 1.9% vs. 2.5% baseline, marginally worse than not applying the filter | The specific anecdote (Kraft) also turns out to be misremembered: he was priced as a mid-round TE off a top-10 season, not a late-round unknown. | same, §1.4 |
| Snap share as a route-participation proxy for identifying late-TE hits | **NULL** at TE11+ (AUC 0.630 [0.36, 0.89], wide CI) | | same, §1.3 |

### A.4 Ceiling/variance pricing at WR — the channel is closed

Independently confirms and sharpens the existing §3 spike-week NULL (PR-002) with a different
instrument (variance decomposition rather than year-over-year correlation).

| Finding | Grade | What it means at the draft | Source |
|---|---|---|---|
| **Perfect foresight of every WR's stacking-bonus points would improve rank correlation by only +0.026** on the ADP board (+0.008 full universe). That is the hard ceiling on any ceiling-pricing model at WR. The model built to capture it gets +0.0002 — none of it. | **NULL** | The stacking-bonus "ceiling pricing" channel at WR is closed. Do not spend further model complexity chasing it. | `docs/ranking/component-model-wr-pass-1.md` §6.2 |
| Conditional on mean yards per game, WRs do **not** differ in spike-week rate: observed variance around the exceedance curve is *below* what binomial chance alone predicts (excess = −0.00176), and the residual does not persist year to year (r = −0.006 [−0.073, +0.060]). | **NULL** | There is no player-level "ceiling type" at WR beyond what the mean projection already implies. | same, §6.3 |
| Rank-correlation gains from the component model **do not translate into better rosters**: share of the true top-24 captured by the model vs. ADP is +0.012 [−0.048, +0.071]; mean points of the drafted top-24 is +0.79 [−7.3, +8.4]. Both intervals are wide open. | **NULL** | A reminder that CLAUDE.md §6.6's gap (rank correlation is a proxy, not the decision-relevant metric) is real and measured, not theoretical. | same, §5.1 |
| Where the component model disagrees with the market by 21+ ranks, it is right about as often as a coin flip (51.0%). Its apparent edge over consensus comes from a smaller average miss in large-disagreement cases, not from better individual calls. | **NULL / weak** | Do not read model-vs-ADP disagreement as "the model knows something." | same, §5.2 |

### A.5 Coach/coordinator/team-environment channel — do not fund the sourcing

| Finding | Grade | What it means | Source |
|---|---|---|---|
| The entire team-environment channel (of which coach/coordinator tendency is a subset) is bounded at **≤ +0.055 τ_b** by a perfect-foresight oracle, and a team fixed-effect on prediction residuals finds **no excess variance over random grouping at any position** (WR, the best-powered test, at exactly 0.000). | **NULL** | Confirms the standing decision not to build the `coaches`/`coaching_staff_seasons` table or scrape Pro Football Reference (also blocked at HTTP 403 per `docs/test-registry.md` #29/#30) — the ceiling is too small to justify it even if sourcing were free. | `docs/ranking/bottom-up-research-pass-1.md` §4.3 |
| Vegas implied team totals forecast the same team-environment channel just bounded near zero. | **NULL by extension** (not directly measured, inferred from the same bound) | Deprioritised, not sourced. | same |

### A.6 Variance decomposition and availability

| Finding | Grade | What it means | Source |
|---|---|---|---|
| Share of season-ppg variance that is stable player quality **and not priced by consensus**: QB 0.063, RB 0.151, WR 0.151, **TE 0.336** — more than double RB/WR and five times QB. | **MARGINAL** (exploratory, doc's own hedge; n=4 consensus seasons for the priced part) | The TE headroom referenced elsewhere in this ledger and in Appendix A.3 traces back to this decomposition. | `docs/ranking/bottom-up-research-pass-1.md` §3.2 |
| **Availability (games played), not rate, is the larger unexplained variance block, and it is near-unforecastable**: prior-two-season games predicts target-season games at r = 0.09–0.18 across positions. A durability/games model built and tested was worse than the flat position mean. | **NULL** | Do not expect an availability-prediction model to work; the founder's edge is not going to come from forecasting who stays healthy. | same, §3.3, §5 |
| Consensus beats a naive prior-PPG baseline at RB and WR, but **not** at QB or TE (where prior-PPG actually wins). Same QB/TE-vs-RB/WR split shows up three ways in the same document (slope analysis, variance ledger, this comparison) — not independent confirmations. | **MARGINAL** | | same, §4.4 |
| The yardage stacking bonuses lift top-3 VBD by **+9.4 (WR), +7.4 (RB), +5.7 (QB), +2.7 (TE)** — real, consistent across 16 seasons, but small (2–4% of VBD magnitude). Supports keeping the bonuses in the scoring engine; does **not** support "ceiling pricing is our structural edge" (see A.4 — the exploitable version of that claim is NULL at WR). | **SURVIVES** (the arithmetic effect) but does not license the edge narrative | | same, §4.1 |

### A.7 RB carry concentration — a structural break, not yet a tradeable signal

| Finding | Grade | What it means | Source |
|---|---|---|---|
| Share of carries going to workhorse (top-30) RBs **declined 1999–2019** (−0.00686/season, p<0.001) and **reversed to rising 2020–2025** (+0.01402/season, p=0.019). Structural break test: sup-F=9.12, bootstrap p=0.043 — borderline, and the source document itself flags this as low-powered (27 annual observations). | **MARGINAL** | If real, it would mean workhorse-back value is *increasing* again after two decades of committee-era decline — worth watching, not worth drafting on. | `PR-001` (source_finding, frozen registration) |
| Whether this reversal has incremental predictive value for RB rankings above consensus rank | **UNTESTED — frozen** (`status: FROZEN-FOR-FUTURE`, reopens ~2028 on current data trajectory) | Do not treat the trend above as an exploitable signal; the confirmatory test that would establish that has never been run and is structurally blocked until more consensus seasons accumulate. | `PR-001` |

---

## Appendix B — Unresolved conflicts (backfill)

Per the backfill task's instructions: when this session could not establish which of two
conflicting figures is current, both are named here rather than silently resolved. **This is not
mine to rule on** — it belongs to `strategist` (thread 085 is already open and unanswered on
exactly this question) or the founder.

1. **Is the 2021–2025 QB rank-curve "collapse" real?**
   - `docs/decisions.md` (ADR ~line 2257, header missing from the file — cross-referenced
     elsewhere as ADR-057) measured the shipped board's QB slope falling from −66.6 to −4.1 across
     2021–2025 and called it **"a monotone collapse... real,"** recommending the board's flat
     pooling be treated as carrying a stale, disappearing regime.
   - `docs/ranking/bottom-up-research-pass-1.md` §4.2 and `docs/ranking/bottom-up-research-pass-3.md`
     (both dated 2026-07-29, the same day) directly re-examined this and found it **"not
     established"** — the trend's confidence interval includes zero, the monotone shape is an
     artifact of the draft-relevant depth cut (it disappears at depth 12), and the single flattest
     point (2025) is driven by one player (Jayden Daniels) whose removal alone reverses the slope
     from −4.1 to +28.6.
   - Both documents agree on the underlying mechanism (rushing QBs drive the "elite QB" edge) and
     both were written the same day; neither is unambiguously later. **This librarian did not
     resolve it** — it is exactly the question thread 085 (`ranker` → `strategist`) was opened to
     settle, and that thread is still open. Do not cite either "the QB premium is collapsing" or
     "the QB premium is stable as pooled" as current fact until it closes.

2. **How many usable "deep" backtest seasons exist for anything usage-based.** `docs/decisions.md`
   ADR-016 and several other passages describe "26 seasons" of history (1999–2024). WR-pass-1 §3
   measured that receiver **targets are effectively absent 2003–2008** (WR target sums of 3, 1, 0,
   29, 6, 5 across those years), so any usage-based (non-points-only) model has **13** usable
   seasons, not 26. This is not a contradiction of a specific figure so much as a scope
   qualification — "26 seasons" remains true for points-only baselines and false for anything
   reading targets/air-yards. Flagging because a future session could easily read "26 seasons" out
   of context and apply it to a usage-based claim it does not support.

**How many measured findings existed nowhere except a status log, and were therefore excluded from
this backfill entirely:** none identified. Every measured finding located this session traced to a
research pass, an ADR, the test registry, or a pre-registration document — not to `docs/status.md`
or `docs/status/`. That does not mean none exist there; it means this session's search (grep across
`docs/ranking/`, `docs/decisions.md`, `docs/test-registry.md`, `docs/preregistration/`,
`docs/handoffs/`) did not have to fall back to a status log to recover anything. See the completion
report for the count of findings recovered and discarded.

---

## 6. What the Draft Guide must not do

Written here because the guide will be produced later, possibly by an agent without this context.

- **Do not present MARGINAL findings as advice.** Two of our most interesting results are marginal.
- **Do not omit §3.** A guide listing only what worked would badly misrepresent how much is known.
- **Do not restate superseded figures.** Read this file and the source documents it names — not
  `docs/status.md` or `docs/status/`, which state superseded numbers in the present tense.
- **Every football claim needs a source in the pipeline.** `CLAUDE.md` §11: "everyone knows X" is a
  hypothesis, not a finding.
