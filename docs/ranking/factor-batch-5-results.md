# Factor batch 5 — pass-catcher opportunity — results

**Ranker, 2026-07-30.** Design: `docs/ranking/factor-batch-5-precommit.md`, committed **`c857c67`
before any arm was fitted**. Campaign registration:
`docs/ranking/factor-campaign-manifest/batch-5.md`. Raw output:
`experiments/bottomup/results/factor_batch5_results.csv`,
`factor_batch5_f3_contradiction.csv`, `factor_batch5_f3_matched.csv`.

**Headline, in one line: 17 registered tests, 0 survive, and the strongest single number in the
whole external sweep does not reproduce — but 4for4's does, three times over, on our data.**

| | |
|---|---|
| Registered tests run | **17 of 17, once each.** No arm re-specified after a result was seen |
| BH-significant at the campaign denominator (m = 80, q = 0.10) | **0** |
| BH-significant at the batch-local m = 17 (secondary) | **0** — smallest p = 0.0084 against a rank-1 threshold of 0.0059 |
| Grades | 11 NULL · 5 MARGINAL · 1 MARGINAL-HARMFUL |
| Route treatment cells whose interpretation is **VOID — COVERAGE ARTIFACT** | **8 of 8** |
| Too-good trigger (> 2% of primary error) | **did not fire.** Largest effect anywhere: 0.90% |
| Season-N proxy reads, all 17 arms | **0**, asserted structurally, not by review |

---

## 1. The single most important result is the control arm, not any treatment

**`routes_known` on its own — a bare 0/1 flag for "we have evidence he ran routes in the last three
seasons" — beats every route feature built on top of it, at every position.**

| position | control `routes_known` E1a | TPRR | routes/game | 1D per route run | control ÷ treatment |
|---|---|---|---|---|---|
| WR | **−0.0544** [−0.0895, −0.0210] | −0.0132 | +0.0147 | +0.0028 | **4.1× · 3.7× · 19.7×** |
| TE | **−0.1514** [−0.2944, −0.0650] | −0.0474 | −0.1422 | −0.0214 | **3.2× · 1.06× · 7.1×** |
| RB | +0.0161 [−0.0047, +0.0506] | +0.0059 | +0.0120 | — | **2.7× · 1.3×** |

The pre-registered rule (precommit §7, imported from batch 3) voids a treatment's *interpretation*
when a control reaches **50%** of its effect. Every one of the eight route treatment cells is past
that line, most of them by several multiples. The numbers stand; **the football reading does
not.** Whatever the route block contributes, it is contributed by *presence*, not by *rate*.

**This is batch 2's `move_known` defect recurring in a different block, and it was caught the same
way — in advance, by a registered control, rather than afterwards by an argument.** That is the
single strongest argument for keeping the control-arm discipline: it cost three slots of campaign
m and it prevented three positions' worth of "TPRR helps at TE" from being written down.

### A second, independent line of evidence that says the same thing

E1b — the same MAE restricted to players on the consensus ADP board — is **worse** for every route
arm at WR and TE, often by an order of magnitude more than the full-universe effect:

| arm | E1a (full universe) | E1b (ADP board) |
|---|---|---|
| WR TPRR | −0.0132 | **+0.2150** |
| WR routes/game | +0.0147 | **+0.5256** |
| TE TPRR | −0.0474 | **+0.5126** |
| TE routes/game | −0.1422 | **+1.5867** |
| TE 1D/RR | −0.0214 | **+0.4963** |

That is the exact signature of a feature whose content is "is this person an NFL pass-catcher at
all": it helps sort the deep tail of a 200-player universe and **actively hurts among the ~50
players a draft actually chooses between**, where everyone has routes. Two independent
instruments — a registered control arm and a population restriction — agree.

---

## 2. Family F1 — all 17 registered tests

E1a = out-of-sample MAE of the `targets` component, arm − primary, paired by season, season-block
bootstrap 4,000 reps. **Negative = better.** `%` is E1a as a share of the primary's own error.

**Season counts differ by block and the two blocks are not comparable without saying so:** route
arms have **7** target seasons (2018–2024, the floor fixed in advance by the same rule batch 3
used for NGS), first-down arms have **11** (2014–2024).

### Block R — routes (`participation` proxy). Registry #16/#17, re-tagged off FTN

| # | arm | pos | seasons | E1a | 95% CI | % | p | E1b | E2 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | R1 TPRR | WR | 7 | −0.0132 | [−0.0282, +0.0042] | −0.06% | 0.200 | +0.215 | −0.0005 | NULL · **VOID** |
| 2 | R1 TPRR | TE | 7 | −0.0474 | [−0.1184, −0.0032] | −0.25% | 0.218 | +0.513 | −0.0017 | MARGINAL · **VOID** |
| 3 | R1 TPRR | RB | 7 | +0.0059 | [+0.0001, +0.0137] | +0.04% | 0.182 | −0.027 | +0.0007 | MARGINAL-HARMFUL · **VOID** |
| 4 | R2 routes per game | WR | 7 | +0.0147 | [−0.0365, +0.0862] | +0.06% | 0.694 | +0.526 | −0.0013 | NULL · **VOID** |
| 5 | R2 routes per game | TE | 7 | −0.1422 | [−0.3755, +0.0033] | −0.75% | 0.258 | +1.587 | +0.0042 | NULL · **VOID** |
| 6 | R2 routes per game | RB | 7 | +0.0120 | [−0.0143, +0.0446] | +0.09% | 0.497 | −0.036 | −0.0008 | NULL · **VOID** |
| 7 | R3 1D per route run | WR | 7 | +0.0028 | [−0.0133, +0.0218] | +0.01% | 0.788 | +0.208 | −0.0004 | NULL · **VOID** |
| 8 | R3 1D per route run | TE | 7 | −0.0214 | [−0.0784, +0.0172] | −0.11% | 0.475 | +0.496 | +0.0010 | NULL · **VOID** |
| 9 | R1c **CONTROL** `routes_known` | WR | 7 | −0.0544 | [−0.0895, −0.0210] | −0.24% | 0.031 | +0.350 | +0.0003 | MARGINAL |
| 10 | R1c **CONTROL** `routes_known` | TE | 7 | −0.1514 | [−0.2944, −0.0650] | −0.80% | 0.076 | +0.909 | −0.0067 | MARGINAL |
| 11 | R1c **CONTROL** `routes_known` | RB | 7 | +0.0161 | [−0.0047, +0.0506] | +0.12% | 0.380 | −0.057 | +0.0005 | NULL |

### Block D — receiving first downs (`ff_opportunity`)

| # | arm | pos | seasons | E1a | 95% CI | % | p | E1b | E2 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 12 | D1 1D per game | WR | 11 | −0.0517 | [−0.1129, +0.0086] | −0.21% | 0.140 | **−0.152** | +0.0032 | NULL |
| 13 | D1 1D per game | TE | 11 | −0.1762 | [−0.3254, −0.0413] | −0.90% | 0.049 | **−0.021** | +0.0213 | MARGINAL |
| 14 | D1 1D per game | RB | 11 | −0.0635 | [−0.1595, +0.0248] | −0.44% | 0.220 | **−0.002** | −0.0050 | NULL |
| 15 | D2 1D per target | WR | 11 | −0.0590 | [−0.1301, +0.0089] | −0.24% | 0.139 | **−0.146** | +0.0011 | NULL |
| 16 | D2 1D per target | TE | 11 | −0.1386 | [−0.2181, −0.0625] | −0.71% | **0.008** | +0.041 | +0.0025 | MARGINAL |
| 17 | D2 1D per target | RB | 11 | −0.0371 | [−0.1297, +0.0366] | −0.26% | 0.423 | −0.011 | −0.0033 | NULL |

Primary errors the percentages are taken against: WR 23.05 / 24.08 targets, TE 18.86 / 19.60,
RB 13.92 / 14.33 (route window / 11-season window).

### Coverage gates, measured on the ADP board before any result was read

| block | flag | measured | gate | outcome |
|---|---|---|---|---|
| firstdown | `fd_known` | **1.000** at WR, TE, RB | ≥ 0.95 | PASS — and this is the measured justification, fixed in the precommit, for block D shipping without a control arm |
| routes | `routes_known` | 0.897 WR · 0.937 TE · 0.837 RB | ≥ 0.80 | PASS |

### The one thing worth a second look, labelled post-hoc

**All six block-D point estimates are negative.** Under a null that is a 1-in-32 event, but the six
cells are not independent — D1 and D2 at one position share a source and a population, so the
effective count is nearer three, and the honest read is **p ≈ 0.25, not 0.03**. Block D is also
the only block where the direction is *consistent across all three instruments* at WR: better on
the full universe (−0.05, −0.06), better on the ADP board (−0.15, −0.15), and positive on E2
(+0.003, +0.001).

**That is a hypothesis for a future registered test, not a finding, and it is stated here in the
weaker form on purpose.** It is exactly the shape of thing that gets promoted by accident.

---

## 3. The contested 0.79-vs-0.68 result — RESOLVED, and it resolves in Hoopes's favour

Family F3. **Descriptive, outside the FDR family, no refit, no BH claim, no promotion path.**

The published contradiction: Heath (Fantasy Points) puts first-read target share at **0.79** to
next-season PPR FPG; Hoopes (4for4), sweeping 23 rate stats, puts the ceiling at **prior FPG
itself, 0.68**, with the best rate stat at 0.59.

### The decisive table — WR, survivor-filtered, every predictor on identical rows

All ten predictors measured on **the same two season pairs (2022→2023, 2023→2024)** and the same
players (≥30 targets in both seasons, n = 82 and 84). Comparing a 2-pair number against an 18-pair
number is comparing two experiments, so the matched table is the one that answers the question.

| predictor | 2022→23 | 2023→24 | mean ρ | **vs prior FPG** |
|---|---|---|---|---|
| **prior FPG — the incumbent, Hoopes's 0.68** | +0.765 | +0.571 | **+0.668** | — |
| **first-read target share [PROXY]** | +0.686 | +0.587 | +0.637 | **−0.031** |
| catchable target share [PROXY] | +0.684 | +0.585 | +0.634 | −0.034 |
| targets per game | +0.728 | +0.538 | +0.633 | −0.035 |
| 1D per game | +0.703 | +0.561 | +0.632 | −0.036 |
| target share | +0.697 | +0.565 | +0.631 | −0.037 |
| YPRR [PROXY routes] | +0.642 | +0.497 | +0.569 | −0.087 |
| 1D per route run [PROXY routes] | +0.607 | +0.517 | +0.562 | −0.095 |
| TPRR [PROXY routes] | +0.634 | +0.465 | +0.550 | −0.107 |
| 1D per target | +0.204 | +0.334 | +0.269 | −0.399 |
| catchable rate [PROXY] | +0.068 | +0.367 | +0.217 | −0.451 |

**Four findings, in descending order of confidence.**

**1. Hoopes's ceiling replicates almost exactly.** He reports prior FPG at **0.68**; we measure
**+0.668** on our data under his kind of filter. And it *is* the ceiling: **all ten alternatives
are below it, without exception.** An independent pipeline, a different scoring system (half-PPR
with stacking bonuses, not full PPR), a different survivor filter — and the same number and the
same ordering.

**2. Heath's 0.79 does not reproduce.** Our first-read target-share proxy reaches **+0.637** on the
survivor population and **+0.607** on our frozen universe. Neither is near 0.79, and neither
exceeds prior FPG. **The contradiction is resolved as a sample-or-definition artifact rather than a
real ranking of the two statistics** — one of the two answers the sweep said was worth having.

**3. Heath's *direction* is right and his *magnitude* is not.** First-read share does beat
ordinary target share — by **+0.006** (0.637 vs 0.631). That is a real sign and a negligible size,
and it is nowhere near enough to lift the statistic past prior FPG.

**4. The strongest corroboration is an accident of the design.** Fantasy Points' own published
numbers put catchable-target share at **0.948** against raw targets' **0.944** — a gap of
**+0.004**, which they describe as essentially no gain. We measure catchable share at **+0.634**
against target share's **+0.631** — a gap of **+0.003**. **We reproduce a shop's own
smallest published difference to within a thousandth**, on independently computed data, which is
the best evidence available that the F3 pipeline is measuring what they measured.

### 4for4's rate-stat ordering replicates three times over

| | Hoopes (4for4) | ours, 8 season pairs, survivor-filtered | ours, matched 2 pairs |
|---|---|---|---|
| YPRR | 0.59 | **+0.535** | +0.569 |
| 1D per route run | 0.57 | **+0.528** | +0.562 |
| TPRR | 0.53 | **+0.476** | +0.550 |
| ordering | YPRR > 1D/RR > TPRR | **identical** | **identical** |

Levels sit 0.02–0.06 below his — consistent with a route denominator we have already labelled as
inflated by ~10–20% — but the ordering, and the size of the gaps between the three, replicate. The
dispatch's specific claim that **1D/RR (0.57) sits above TPRR (0.53)** is confirmed: we get +0.528
against +0.476, a gap of +0.052 against his +0.04.

### And the whole literature's survivorship discount, measured

The same predictors on our bust-retaining frozen universe are uniformly weaker than on the
survivor population — **prior FPG falls from +0.668 to +0.605, TPRR from +0.550 to +0.457.** Every
public number in the sweep is measured on the left column. `CLAUDE.md` §6.2's warning is not
theoretical here: it is worth roughly **0.06 to 0.09 of correlation**, in the direction that
flatters the publisher.

### What F3 is not

It refits nothing, it grades nothing, and **it does not license adding first-read target share to
anything.** It is a measurement of published claims on one population. The model-arm question for
these statistics is separate and, for the FTN pair, currently unanswerable — see §4.

---

## 4. The two dispatched arms that were not registered, and why

**N1 (first-read target share) and N2 (catchable share / rate) are UNGRADEABLE in this harness, and
that is a different disposition from "tested and null".**

FTN charting starts **2022**. `WalkForward` needs at least one *training* pair carrying the
feature, which puts the first target season at **2024**; the 2025 holdout is sealed. **n_seasons =
1**, and a season-paired endpoint with a season-block bootstrap has no sampling distribution at
n = 1. Registering them would have spent campaign m to buy a guaranteed NULL that would then be
misread as evidence against the factor.

They become gradeable in **2027** and every year after. Declared in the pre-commitment §2 before
any number existed, so this is not a retreat from a bad result.

**The proxy caveat travels with every N1/N2 number above, on screen and in any write-up.** Ours is
`read_thrown == '1'` from FTN joined to the pbp receiver id. It is **not** Heath's charted
definition, whose filters are unstated. Under the sweep's §4 licensing note, a factor proxied off a
paid definition is labelled a proxy and never presented as the named metric.

---

## 5. Data findings — reported because the reason a factor was untested matters as much as the result

**1. FTN charting is in no table in `nfl.db`.** Two of the four dispatched factors name it as their
only source. It is fetchable (`nflreadpy.load_ftn_charting`, no auth, seconds per season) and joins
to our `pbp` at 99.5% of pass plays carrying a receiver id. Batch 5 fetched 2022–2024 ad hoc — the
sealed season was never requested — and cached it to
`experiments/bottomup/results/factor_batch5_ftn_cache.csv`. **Nothing was written to `nfl.db`**;
three other factor agents are on this checkout. Thread open to `data-ops`
(`2026-07-30-ftn-charting-is-not-in-nfl-db-batch-5-fetched-it`), including the licensing point that
the FTN subset is **CC-BY-SA**, not CC-BY, and the `' CHK'` leading-space value any ingest must
normalise.

**2. `pbp.first_down_pass` does not exist here.** The dispatch specified it for N4. This database's
`pbp` has 25 columns and neither `first_down_pass` nor `ydstogo`, so it cannot be derived either.
The working source is `ff_opportunity.rec_first_down` — coverage **1.0000** for players with ≥15
targets, at all three positions, in every season 2009–2024, and its target counts agree with the
box score at r = 0.9985.

**3. The registry correction is confirmed and is now measured, not asserted.** #16/#17 were tagged
`nflverse:FTN`, which has no per-player columns. `participation.offense_players` supplies routes
for **2016–2025, every pass play, full 11-man personnel** — ten seasons of source, seven usable
target seasons. **`CLAUDE.md` §5's "route participation is not in `nfl.db`" and batch 2 §7's
refusal to say anything about routes are both now out of date**, with the caveat that what exists
is a labelled proxy, not charted routes.

**4. The route proxy's three named departures**, all fixed in the precommit before fitting: on the
field for a dropback ≠ ran a route (worst at RB, which is the direction that flatters the RB
cells); the denominator is inflated ~10–20% by sacks, scrambles, penalty-wiped plays and the
postseason; `participation.offense_positions` is NULL throughout, so position comes from the panel.

---

## 6. Guardrails, as run

| check | outcome |
|---|---|
| Look-ahead | Every arm's audit: `max_feature_cutoff = N−1`, `max_outcome_season < N`, `n_outcome_reads_at_target = 0` |
| Season-N reads | **`proxy_reads = 0` on all 17 arms and all 3 primaries**, enforced by `allow_preseason_proxy=False` raising in `WalkForward.run`. Not a convention — a structural proof |
| Holdout | 2025 sealed at the SQL gate and at batch 5's own gate. Never opened. FTN fetched for 2022–2024 only |
| Survivorship | Universe frozen pre-season, busts retained at 0. F3 additionally ran both populations side by side, and the discount was measured (§3) |
| Multiple comparisons | BH at the **campaign** denominator, `M_campaign = max(Σ_b m_b, 80) = 80` (only batch 5 had registered when grading ran, so the floor bound). Batch-local m = 17 reported as a labelled secondary. **Neither changes any grade — nothing is significant under either** |
| Coverage-flag confound | Three registered controls; the 50% VOID rule fired on 8 of 8 route treatment cells |
| Too-good trigger | Did not fire. Largest effect 0.90% of primary error, against a 2% threshold |
| Unequal support | Every row carries its season count; route (7) and first-down (11) arms are never compared without it |
| Reproduction | Batches 1–3 unaffected: `factor_features5` only ever appends columns to `build_factor3_features` |

**One deviation from the pre-commitment, recorded rather than absorbed.** F3's first run compared
each predictor over its own maximum season support, which reads a predictor's strength correctly
and reads the *contradiction* wrong. The precommit §6 says "the same population **and the same
season pairs**", so `f3_matched` was added to honour that. It is a fidelity fix to the registered
design, not a new analysis, and both tables are published. No F1 number changed; F1 ran once.

---

## 7. What this licenses, and what it does not

**Nothing ships.** No arm graded SURVIVES or PROJECTION-ONLY, so under the precommit §7 rules and
batch 2 §7's insight-string rule, **no sentence about routes, route participation or receiving
first downs may render on any surface.** In particular the founder's *"new OC, expect routes to
increase"* remains unlicensed: routes are now measurable, and measuring them did not produce a
factor that earns a place.

**Registry #16 and #17 are measured-and-dead on the corrected source**, and per the pre-commitment's
stopping condition they must not be re-specified a third time on the grounds that the sample was
short. Seven target seasons off a ten-season source is the sample the corrected tag buys.

**What genuinely changed:** the project now knows that prior points per game is the ceiling among
pass-catcher rate statistics — measured independently, replicating 4for4's 0.68 at 0.668 — and that
the entire public literature's numbers carry a survivorship premium worth 0.06–0.09 of correlation.
That is a bound on a whole channel, not a factor.

---

## 8. Who checks this, because I do not check my own work

| claim | independent check | status |
|---|---|---|
| the design, the campaign denominator, and the UNGRADEABLE disposition | **`strategist`** | thread open, opened before results existed |
| the result — and specifically whether the route proxy's blocking-snap contamination invalidates the RB cells, and whether the block-D sign consistency is being under- or over-sold in §2 | **`fable`**, maximum effort | to be dispatched |
| whether FTN should be ingested and versioned | **`data-ops`** | thread open |
| whether Heath's 0.79 and Hoopes's 0.68 are even the same quantity — the part our data cannot settle | **`researcher`** | thread open |
| anything that ships | **`backend`** | nothing ships from this batch |
