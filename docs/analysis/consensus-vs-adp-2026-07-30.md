# Consensus (ECR) vs. Market ADP: which is the better predictor, and what to do when they disagree

**Session:** backend, 2026-07-30. Answers **FR-099** ("isn't that also the spine that bottom up
rankings need? is bottom up better than top down? ... evening knowing if consensus or adp is
better is good insight" — founder, via PM). **This is a Sonnet/default-tier session, not a
dispatched Opus/high-effort one.** Per `docs/operating-model.md`, methodology work like this
should arrive dispatched to Opus at high effort; this dispatch did not specify that. Flagging
explicitly and proceeding rather than stopping to ask, per this session's own operating rules — a
second, Opus-tier read is exactly what the `strategist` handoff at the end of this doc requests.

**Script:** `analysis/consensus_vs_adp.py` (reproducible, no network calls, ~15s runtime against a
populated `data/nfl.db`). **Raw output:** `data/qa/consensus-vs-adp-2026-07-30.json`.

---

## 0. The dispatch's premise is corrected here, not silently worked around

The dispatch states: *"Five completed seasons (2021–2025) have both plus realised outcomes."*
**That is not what the data contains.** `ffc_adp_snapshots` (`adp_source='ffc_half_ppr_12team'`,
the only pre-draft, format-aware market ADP source in this database — thread 055) covers **only
2018–2024**. There is no 2025 archive in any FFC format (re-confirmed here by direct query; the
prior finding in `docs/handoffs/055-ffc-adp-history-harvest.md` stands). The single 2026 `mfl_proxy`
snapshot is current-day only and not usable for a completed season.

**The true ECR × ADP overlap with realised outcomes is 2021–2024 — four seasons, not five.**

This is good news for the holdout, not bad news for the analysis: **2025 is never read by this
script**, not because of holdout discipline but because the ADP side of the comparison does not
exist for that season. `analysis/consensus_vs_adp.py` still calls
`holdout.DEFAULT_LOCK.guard(SEASONS, ...)` explicitly on the season list used, so if a 2025 ADP
source ever lands and someone widens `SEASONS` without re-checking scope, the script fails loud
(`HoldoutViolation`) instead of silently reading the sealed season. No pre-registration/unseal
flow was needed for that reason.

It is bad news for power: **n=4 seasons instead of 5** for the per-season stability check, and the
season-clustered bootstrap CI on the win-rate is below `MIN_SEASONS_FOR_STABLE_CI=8`
(ADR-021) regardless.

---

## 1. Method

### 1.1 Universe and matching
Per season, restricted to `QB/RB/WR/TE` (the four positions this project's scoring engine covers;
K/DST excluded from both sides for consistency). `rankings` uses `gsis` player IDs natively;
`ffc_adp_snapshots` uses `mfl_id`, mapped to `gsis` via `ff_playerids` (the same table
`experiments/bottomup/components/adp_baseline.py` already uses for this exact join).

**Match rate: 100% across all four seasons** (605/605 FFC-listed skill-position players matched to
an ECR row; zero `mfl_id`s failed to resolve to `gsis`). This is the *good* direction for bias —
FFC's mock-draft universe (112–171 players/season) is a strict subset of ECR's much larger board
(442–522 players/season, includes deep bench/waiver names ECR covers but FFC mocks never reach),
so the constraining factor is "was this player relevant enough to appear in a 12-team mock,"
and every such player was found in ECR. No silent bias toward well-known players from a broken
join — the join was clean, the *coverage* asymmetry (ECR is deep, FFC-ADP is shallow) is the real
and expected shape of these two sources.

### 1.2 As-of-date (look-ahead)
`rankings` for `fantasypros_ecr` carries exactly one row per season with `is_preseason_final=1`
for 2021–2025 (`as_of_date` in late August, pre-Week-1) — **used as-is**, this is the correct
pre-draft snapshot, not a final/in-season revision. 2026's row has `is_preseason_final=0`
(current-day, mid-season-prep) and is excluded by the `SEASONS` restriction anyway. FFC ADP
carries its own verified pre-kickoff `as_of_date` per season (early September, before that
season's real Week 1 — see `adp_baseline.py`'s kickoff-date check, reused implicitly by using the
same table this project already trusts for that guarantee).

### 1.3 Comparable rank scale — the design point that makes the threshold defensible
ECR's board (~450–520 players) and FFC's mock-draft board (~112–171 players) are not the same
size, so raw `adp_rank` (ECR) is not directly comparable to raw FFC `rank`/`average_pick` — rank 200
on a 500-player ECR board is nowhere close to rank 200 on a 150-player mock board. **Both sides are
re-ranked to an ORDINAL position (1..M) within the matched subset only**, for that season. This
puts both sources on the same denominator (M = the actual number of players both systems ranked
that season, 112–171) so "one round apart" means the same thing on both sides, and both are
directly comparable to draft position in an actual 12-team draft of similar size.

**Disagreement threshold: `|ecr_ordinal − adp_ordinal| > 12`** — more than one full round in a
12-team draft, applied on the shared ordinal scale. This is the threshold the dispatch itself
proposed; adopted as stated, on the ordinal (not raw) scale for the reason above.

**Realised outcome, same treatment.** Actual fantasy points are computed with this project's own
scoring engine (`score_offensive_game`, `db.actual_season_outcomes` via `backtest._season_actuals`
— no hand-rolled scoring, per the dispatch's own instruction), converted to VBD
(`scoring.compute_vbd`, `ReplacementLevels()` — this league's ADR-029 measured RB30/WR40/TE10
flex-adjusted baselines), with replacement level computed from the **full season universe** (every
player with any weekly stats row, not just the matched ADP subset), matching the convention set in
`docs/analysis/adp-vs-production-2026-07-30.md` §1.2. **Survivorship (CLAUDE.md §6.2):** a player
matched by both ECR and ADP who never appears in the stats table (a bust) is floored at 0 raw
points, not dropped — this is exactly the population a market-vs-experts test cannot afford to
lose. Players are then re-ranked by realised VBD to the same ordinal scale (`actual_ordinal`).

### 1.4 Win/loss and effect size
**Primary metric — rank distance.** For each disagreement pair, the side (`ECR` or `ADP`) whose
ordinal rank is numerically closer to `actual_ordinal` wins; equal distance is a tie (0 ties
occurred in this data — the ordinal scale is fine-grained enough that exact ties are rare).

**Secondary metric — effect size in points.** Each season's own realised-value curve
(`value_curve[k]` = the VBD of the player who finished with the *k*-th best realised VBD that
season, among the matched subset) gives an "expected VBD at ordinal rank k." For a disagreement
pair, `error_side = |actual_vbd − value_curve[side_ordinal]|`; `effect_pts = error_ADP − error_ECR`
(positive = ECR's predicted slot was closer to reality, in fantasy points). This exact
value-curve-as-expectation construction is the one already vetted in
`adp-vs-production-2026-07-30.md` (including its caveat that comparing predicted-slot value against
its own season's realised curve does not by itself demonstrate market skill — see §1.5 there; it
applies here identically and is not re-derived).

### 1.5 Uncertainty
Wilson 95% CIs on win rate (binomial), pooled and per subgroup. Season-level stability reported as
a mandatory per-season table, not folded into the pooled number. A season-clustered bootstrap
(resampling *seasons*, not player-pairs — ADR-021 convention) is also reported on the season-level
win rates; flagged `degenerate=True` because n=4 < `MIN_SEASONS_FOR_STABLE_CI=8`, exactly the same
honesty flag ADR-021 requires elsewhere in this project.

---

## 2. Results — lead with power, then the disagreement subset

### 2.1 Overall correlation (reported first, as instructed — this sets the power expectation)

| Season | n matched | tau_b (ECR vs ADP) |
|---|---|---|
| 2021 | 171 | **+0.79** |
| 2022 | 112 | +0.74 |
| 2023 | 168 | +0.52 |
| 2024 | 154 | +0.62 |
| mean | — | **+0.67** |

**Correction to the dispatch's own framing:** the pre-registered expectation was "ECR and ADP are
likely correlated above 0.95." **They are not, at least not on this ordinal, matched-universe
scale — tau_b ranges 0.52–0.79, mean 0.67.** This is still a strong positive relationship (both
sources broadly agree who the good players are), but it is nowhere near saturated agreement, and
**2023 in particular (tau_b=0.52) shows real, substantial divergence between the room and the
experts that season.** This matters for the power read: a *correlation contest* on the whole board
would still likely be underpowered at n=4 seasons for detecting *which* source is better overall
(the difference between two already-agreeing sources is a second-order effect), but the
disagreement itself is not the small, dominated-by-noise sliver the 0.95 assumption implied — it is
a meaningfully sized subset, borne out below (315 of 605 matched player-seasons, 52%, exceed the
one-round threshold).

### 2.2 Disagreement subset — pooled

| | Value |
|---|---|
| n pairs (|diff| > 1 round) | 315 |
| n decided (ties excluded) | 315 (0 ties) |
| ECR win rate | **0.546** [Wilson 95% CI: 0.491, 0.600] |
| ADP win rate | 0.454 |
| Mean effect (VBD pts, + = ECR more accurate) | **+7.87** |

**The pooled CI crosses 0.5.** Read plainly, per the dispatch's own instruction for an honest null:
**pooled across all four seasons, positions, and draft ranges, ECR and ADP are statistically
indistinguishable as predictors on the disagreement subset.** ECR's point estimate leans favorable
(54.6%) and the mean effect size leans in points toward ECR (+7.87 VBD pts on the winning side),
but the interval does not clear 50%. This is *not* the same finding as §2.1's correlation
(agreement is real and strong); it is that **when they do disagree, neither reliably wins.**

### 2.3 Per-season stability — the mandatory check, and it shows real season-to-season swing

| Season | n | ECR win rate | Wilson 95% CI | Mean effect (pts) |
|---|---|---|---|---|
| 2021 | 76 | 0.474 | [0.365, 0.584] | +2.64 |
| 2022 | 34 | 0.529 | [0.367, 0.685] | +6.30 |
| **2023** | 112 | **0.652** | **[0.560, 0.734]** | **+14.41** |
| 2024 | 93 | 0.484 | [0.385, 0.584] | +4.84 |

**2023 alone clears 50% with a CI that excludes it, and no other season does.** The pooled result
(§2.2) is being carried almost entirely by 2023 — the same season §2.1 flagged as the year ECR and
ADP diverged most (tau_b=0.52, the lowest of the four). Season-clustered bootstrap CI on the mean
of season win rates: **[0.479, 0.621], degenerate=True (n=4 seasons < 8)**. Per the same honesty
standard ADR-021 applies elsewhere: **this is one good season for ECR, not an established edge.**
Three of four seasons individually sit within noise of a coin flip; only 2023 stands out, and one
season out of four is exactly the kind of single-season-driven result the guardrails require
flagging rather than reporting as a stable pattern.

**Read plainly: pooled or per-season, the honest answer is "indistinguishable, use either" for the
disagreement subset as a whole.** The one place a real, stable-looking interaction survives is
below (§2.4).

### 2.4 By position

| Position | n | ECR win rate | Wilson 95% CI | Mean effect (pts) |
|---|---|---|---|---|
| QB | 49 | 0.571 | [0.433, 0.700] | +10.11 |
| RB | 115 | 0.513 | [0.423, 0.602] | +4.04 |
| WR | 116 | 0.543 | [0.453, 0.631] | +8.52 |
| TE | 35 | 0.629 | [0.463, 0.768] | +15.17 |

No position's CI excludes 0.5. TE and QB lean the most toward ECR, RB is closest to a coin flip.
Sample sizes here (35–116) are too small individually to call any of these a finding on their own;
reported as the requested breakdown, not as a result.

### 2.5 By ADP range — the one interaction worth carrying forward

| Range (ordinal ≤ 60 = through round 5) | n | ECR win rate | Wilson 95% CI | Mean effect (pts) |
|---|---|---|---|---|
| **Early** (≤60) | 121 | **0.595** | **[0.506, 0.678]** | **+15.50** |
| Late (>60) | 194 | 0.515 | [0.446, 0.585] | +3.11 |

**This is the most interesting result in the analysis.** Early-round disagreements (top ~5 rounds
of a 12-team draft) favor ECR at 59.5%, with a Wilson CI that just barely excludes 0.5 (lower bound
0.506) and an effect size nearly 5x the late-round effect (+15.5 vs +3.1 VBD points). Late-round
disagreements are close to a coin flip. **The practical read: when the room and the experts
disagree early, lean toward the experts; late, it doesn't matter which you follow.** This is
directionally consistent with the position × range cross-tab below and is the one pattern that
would be worth a formal pre-registration if this ever gets revisited with more seasons — it is
NOT being reported as confirmed here (the CI barely clears 0.5, n=4 seasons, no correction for the
multiple subgroups tested in this document has been applied — see §3).

### 2.6 Position × range cross-tab (diagnostic, not pre-registered)

| Position/range | n | ECR win rate | Wilson 95% CI |
|---|---|---|---|
| QB/early | 16 | 0.688 | [0.444, 0.858] |
| QB/late | 33 | 0.515 | [0.352, 0.675] |
| RB/early | 51 | 0.549 | [0.414, 0.677] |
| RB/late | 64 | 0.484 | [0.366, 0.604] |
| WR/early | 49 | 0.633 | [0.493, 0.753] |
| WR/late | 67 | 0.478 | [0.363, 0.595] |
| TE/early | 5 | 0.400 | [0.118, 0.769] |
| TE/late | 30 | 0.667 | [0.488, 0.808] |

QB and WR both show the same early/late pattern as the pooled result (ECR favored early, coin-flip
late); RB is flat throughout; TE's early cell has n=5 and is not informative (its point estimate
should not be trusted). No cell here individually clears its own Wilson interval away from 0.5.
Reported for completeness, exactly the role `adp-vs-production-2026-07-30.md`'s equivalent
cross-tab played there — a diagnostic that shaped which pattern to trust (§2.5), not itself a
confirmed finding.

---

## 3. Multiple comparisons — not formally corrected, and why that matters here

This document reports one overall correlation check, one pooled win-rate test, one per-season
table, four position cells, two range cells, and eight position×range cells — roughly 16
Wilson-interval tests plus the correlation table. **No Benjamini-Hochberg or other correction has
been applied**, unlike `adp-vs-production-2026-07-30.md`, because **nothing here is being reported
as a confirmed finding** (§2.5 is explicit that it is a candidate for a future pre-registration, not
a result). If this ever becomes the basis for a ranking-model decision, it must go through the same
pre-registration/FDR discipline as any other factor test (`docs/preregistration/README.md`) before
being treated as more than a hypothesis — flagging this now so it isn't skipped later.

---

## 4. What this licenses and what it doesn't

**Does not license:** treating "ECR beats ADP" or "ADP beats ECR" as an established fact, at any
grain measured here. Pooled and three of four individual seasons are within noise of a coin flip.

**Does not license:** re-opening the 5-season assumption anywhere else in the project without
re-checking it — FFC ADP simply does not cover 2025, and any other document that assumed 5-season
consensus-vs-ADP coverage should be corrected the same way this one was.

**Does license, at low confidence, as a hypothesis for a future pre-registered test:** "when
expert consensus and the market disagree by more than a round early in a 12-team draft, lean
toward the experts; late, it doesn't matter." (§2.5)

**Does license, at reasonable confidence, as the direct answer to the founder's question:** ECR and
ADP substantially agree (tau_b ~0.67) but not so completely that their disagreements are noise —
52% of matched players in a given season differ by more than a round. On that meaningful
disagreement subset, **neither source is a reliably better predictor of realized outcomes** — the
honest, budget-saving answer FR-099 itself anticipated as a legitimate result. **Use either as a
starting board; the room's ADP is not worth paying for the sole purpose of second-guessing expert
consensus, and vice versa**, except possibly for the early-draft-only lean noted above.

---

## 5. The cheap add — ECR as a third baseline for the bottom-up model — NOT done, and why

FR-099 also asked, "if inexpensive... add ECR as a third baseline" to the bottom-up component
model's existing model-vs-consensus-ADP comparison (`docs/ranking/component-model-rb-qb-te-pass-1.md`
§1). **Assessed and skipped, not attempted.** The eval harness that comparison runs through
(`experiments/bottomup/components/pos_eval.py`, `adp_baseline.py`) is `ranker`-owned infrastructure
with its own look-ahead audit (`Runner.run()`'s `if a["max_feature_cutoff"] >= target...` check),
walk-forward folding, and baseline-column wiring (`_baseline_columns`). Adding a genuine
`b4_ecr` column correctly means writing an `ecr_baseline.py` mirroring `adp_baseline.py` (lower
effort than ADP's, since ECR's `player_id` is native `gsis`, no id-mapping layer needed), wiring it
into `Runner.run()` and `_baseline_columns`, and **re-running the full walk-forward evaluation for
QB/RB/TE/(WR)** to regenerate the metrics CSVs this doc's own component-model report cites. That
last step is not a quick add — it is a re-run of the confirmatory infrastructure another role owns
and is mid-methodology-review on (see `docs/handoffs/093-...md`, `PR-004`/`PR-005`). Logged as
follow-on work in `docs/ideas-inbox.md` rather than done speculatively in someone else's
in-progress harness.

---

## 6. Reproducing this

```
python3 analysis/consensus_vs_adp.py
```

Requires a populated `data/nfl.db` with `rankings` (`source='fantasypros_ecr'`, 2021–2024) and
`ffc_adp_snapshots` (`adp_source='ffc_half_ppr_12team'`, 2021–2024) — both already committed via
CSV/backfill per `docs/can-we-rebuild-the-database.md`. Output: console summary +
`data/qa/consensus-vs-adp-2026-07-30.json` (full per-season, per-position, per-range tables, and
every individual disagreement pair for audit).
