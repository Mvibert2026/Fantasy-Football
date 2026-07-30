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
| **Does per-player dispersion improve the exceedance curve?** `pos_model.py:300` predicts threshold-clearing from **mean yards per game only** — so a 60/60/60 player and a 20/20/140 player with the same average get identical bonus expectations. Never tested. | If it lifts, volatility is real and monetizable through exactly the channel §7 claims. If not, §7's operational half should be cut from the spec. |
| **Zero RB / Robust RB / Balanced vs. VBD**, simulated on realised roster points | The only honest way to answer a *strategy* question. Rank correlation compares lists; this compares rosters. |
| **Positional volatility per roster slot**, not per player | TE volatility passes straight through (one slot); WR volatility partially cancels (three starters + flex). Same number, different meaning. |
| **Archetype dimension autocorrelation** — which dimensions are stable traits vs. situational roles | Determines whether career history helps or actively misleads, per dimension. |
| **Bust screen** (FR-096) | Must beat two nulls: regression to the mean, and injury. |

---

## 6. What the Draft Guide must not do

Written here because the guide will be produced later, possibly by an agent without this context.

- **Do not present MARGINAL findings as advice.** Two of our most interesting results are marginal.
- **Do not omit §3.** A guide listing only what worked would badly misrepresent how much is known.
- **Do not restate superseded figures.** Read this file and the source documents it names — not
  `docs/status.md` or `docs/status/`, which state superseded numbers in the present tense.
- **Every football claim needs a source in the pipeline.** `CLAUDE.md` §11: "everyone knows X" is a
  hypothesis, not a finding.
