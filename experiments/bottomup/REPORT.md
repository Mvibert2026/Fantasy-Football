# Bottom-up ranking prototype — results (2026-07-27, branch fable/ext-2026-07-27)

**One line, the registered question first: the usage-arm bottom-up model beats
last-season-rank at WR (Δτ_b +0.043 [95% CI +0.017, +0.071], better in 10 of 13
seasons) and RB (+0.041 [+0.001, +0.080], 10 of 13), is positive but
inconclusive at TE, and clearly LOSES at QB (−0.108 [−0.212, −0.013]).**
Against pre-season consensus ECR (descriptive only, n=4 seasons, veterans-only
common universe): the model still loses at QB and RB, and is within noise of
ECR at WR (−0.033) and TE (−0.001). No suspicious-R² audit trigger fired; every
number sits inside the ceiling bands registered before fitting.

Protocol: `docs/reviews/fable-ranking-design-2026-07-27.md` (registration
frozen before any fit). Code: `experiments/bottomup/`. Raw results:
`experiments/bottomup/results/{long,usage}.json` (per-season, per-position,
every baseline). Variant log: `VARIANTS.md` — 2 model configurations total.
Holdout 2025: never read (structurally sealed; test-pinned).

## Across-season summary (mean over folds, season-level bootstrap 95% CI)

### Usage arm (folds 2012–2024, n=13; targets/shares/air-yards features)

| Pos | τ_b model | τ_b last-season-rank (B1) | Δ model−B1 | folds model>B1 | τ_b volume-only (B3) | R² season | R² ppg |
|---|---|---|---|---|---|---|---|
| QB | +0.168 [+0.077,+0.258] | +0.275 [+0.185,+0.364] | **−0.108 [−0.212,−0.013]** | 3/13 | +0.096 | −0.13 | −0.20 |
| RB | +0.337 [+0.275,+0.395] | +0.296 [+0.248,+0.346] | **+0.041 [+0.001,+0.080]** | 10/13 | +0.282 | +0.17 | +0.30 |
| WR | +0.401 [+0.361,+0.448] | +0.358 [+0.310,+0.407] | **+0.043 [+0.017,+0.071]** | 10/13 | +0.288 | +0.29 | +0.36 |
| TE | +0.321 [+0.239,+0.396] | +0.248 [+0.161,+0.350] | +0.073 [−0.005,+0.152] | 8/13 | +0.149 | −0.85 | −1.83 |

Draft-weighted co-primary (VBD capture at QB10/RB30/WR40/TE10): model−B1 =
QB **−0.224 [−0.357,−0.095]**, RB +0.016 [−0.007,+0.038], WR +0.014
[−0.006,+0.037], TE **+0.076 [+0.032,+0.123]**.

### Long arm (folds 2002–2024, n=23; box-score volume, no targets)

| Pos | τ_b model | τ_b B1 | Δ model−B1 | folds model>B1 | R² season |
|---|---|---|---|---|---|
| QB | +0.230 | +0.258 | −0.028 [−0.072,+0.019] | 7/23 | −0.08 |
| RB | +0.359 | +0.336 | +0.023 [−0.006,+0.050] | 15/23 | +0.22 |
| WR | +0.351 | +0.341 | +0.010 [−0.018,+0.034] | 15/23 | +0.25 |
| TE | +0.331 | +0.299 | +0.031 [−0.040,+0.103] | 11/23 | −0.10 |

Reading the two arms together: **the edge over naive persistence comes from the
usage features** (target share, air yards, WOPR). With box scores only, the
model is at parity with last-season-rank; adding usage moves RB/WR/TE clearly
positive. That is the single most decision-relevant finding for ADR-E: the S1
feature tier that starts in 2009 is where the value is; the 26-season box-score
tier adds validation depth, not edge.

### Consensus comparison (2021–2024, n=4, DESCRIPTIVE — no p-values, per ADR-B)

Veterans-only common universe (rookies excluded from the prototype universe,
which removes exactly the rows where ECR has an information advantage; noted).
Per-season paired Δτ_b (model − ECR), usage arm: QB −0.223 (0/4 seasons
positive), RB −0.110 (0/4), WR −0.033 (1/4), TE −0.001 (2/4).

**Honest statement:** this prototype does not beat pre-season expert consensus
at ranking veterans, anywhere; it approaches parity at WR/TE. It beats *naive*
baselines at RB/WR/TE. Consensus embeds situation knowledge (depth-chart moves,
coaching changes, vacated opportunity, holdouts, camp news) that the P1 review
identified as exactly the features ADR-E lacks data for. The gap to consensus
is the measured size of that missing-information channel: roughly 0.03–0.11 τ
depending on position, largest where situation-change matters most (QB, RB).

## Per-season Δτ_b (model − B1), usage arm — the series IS the finding

```
QB: 12:-0.37 13:-0.42 14:-0.02 15:-0.05 16:-0.05 17:-0.16 18:+0.12 19:+0.15
    20:-0.19 21:-0.32 22:-0.05 23:+0.15 24:-0.19
RB: 12:+0.04 13:-0.04 14:-0.01 15:+0.03 16:-0.12 17:+0.09 18:+0.03 19:+0.02
    20:+0.03 21:+0.05 22:+0.14 23:+0.16 24:+0.13
WR: 12:+0.00 13:+0.00 14:+0.00 15:+0.12 16:+0.06 17:+0.05 18:+0.05 19:+0.01
    20:+0.13 21:-0.01 22:+0.06 23:-0.02 24:+0.10
TE: 12:-0.06 13:+0.06 14:-0.08 15:+0.03 16:+0.17 17:-0.05 18:+0.16 19:+0.05
    20:+0.29 21:+0.36 22:+0.23 23:-0.11 24:-0.09
```

No pooled average hides a bad stretch: WR is non-negative in 11 of 13 and never
worse than −0.02; RB's gains concentrate 2017+; QB is bad across eras, not in
one; TE swings hard both ways (n=20 universe — single players move τ a lot).

## Registered mechanism predictions, scored

| Prediction (frozen in P1 review §Q4 before fitting) | Outcome |
|---|---|
| (i) volume features carry most of the signal | **Supported.** Model > volume-only B3 everywhere (Δτ +0.05 to +0.26), and B3 alone already recovers most of B1's level at RB/WR — usage level + S2 regression is the working core. |
| (ii) TD-rate shrinkage gives a real but small gain over raw prior points, mainly WR/RB | **Supported at RB/WR** (that is where model beats B1, and B1's handicap is exactly its TD/luck retention). **Directionally wrong at QB** — and V2 showed loosening the TD cap does NOT fix QB, so the QB deficit is not the shrinkage being too aggressive. |
| (iii) age terms ≈ nothing inside draft depth | **Unresolved** — no ablation run (would have been config #3; budget discipline kept it unspent). |
| (iv) games-played projection ≈ nothing over position mean | **Confirmed, slightly worse than nothing:** games R² −0.01 to −0.22 vs test mean, negative at every position. The 2-parameter base rate adds noise. ADR-E's base-rate humility is vindicated; even the humble version may be too confident. |

## Ceiling check (registered bands vs observed)

WR season R² 0.293 [0.239, 0.356] — top of the registered 0.15–0.30 band, near
the registered ceiling ~0.35, no trigger. PPG R² 0.359 — inside 0.25–0.45. RB
0.17/0.30 — inside. QB/TE negative R² on the points scale while τ is healthy:
rank information is real but the point calibration at those positions is not
usable (QB S3 mis-scales; TE universe is tiny). Nothing crossed an ADR-E §8
audit trigger; nothing needed the presumed-bug protocol.

## What is doing the work

Beats naive persistence where target-competition data exists (RB/WR/TE usage
arm); at parity with box scores alone; loses to persistence at QB, where a
17-game starter's rank IS his identity and our regression-to-mean of pass TD
rate + attempts churn hurts more than it helps (V2 falsified the cap
explanation). The gap to consensus is concentrated where situation features
(vacated opportunity, depth charts, coaching) would live — the P1 review's R1
feature is the obvious next lever, not more model capacity.

## Most promising direction not tried

**Vacated-opportunity features (P1 work order R1)** — team-level departed
target/carry share for season N, joined to returning players. It is the
largest mechanism absent from both this prototype and ADR-E §4.1, the data is
mostly ingestable, and the consensus-gap pattern above (worst at QB/RB, near
zero at WR/TE) is exactly the fingerprint of missing situation information.
Second: a QB-specific arm that keeps prior-season points as a feature
(own-production, not consensus — legal under ADR-E §4.1) instead of forcing
the full decomposition at the one position where decomposition hurts.

## Limitations, stated

- Rookies excluded (registered). Real boards must rank them; consensus
  comparison here is veterans-only and says nothing about rookie rows.
- No suspension/retirement/holdout knowledge (same limitation as the shipped
  product's floor, table-stakes review items 4–7).
- Games model is worse than the position mean — season-point predictions
  inherit that noise.
- Walk-forward expanding window, not ADR-E's embargoed LOSO: early folds train
  on 2–5 pairs and are noisier; the per-season series shows no era cliff, but
  the confirmatory run should use the registered LOSO protocol.
- `k` grid for S2 is coarse; caps bind frequently at TD/INT stats (by design).

---

# Session-3 appendix (2026-07-27): V3–V6 — vacated opportunity and the QB arm

Registrations: `docs/reviews/FABLE-EXT2-2026-07-27.md`, frozen and committed before each run
(`678615c` for V3/V4; `1c16ab4` for V5/V6). Four configurations this session; six total across
both sessions, plus fix F1. Holdout 2025: never read.

**One line: clean vacated/arrived-opportunity features (V5) give the model its best
last-season-rank results yet at RB (+0.057 [+0.018,+0.095]) and TE (VBD +0.073
[+0.034,+0.118]) — and move the consensus gap NOWHERE; at QB, nothing in six configurations
beats ranking by last season's points, and the one result that appeared to (V3) was an
availability leak that the clean rerun eliminated.**

## The leak, named before the numbers

V3 as registered assigns a no-early-appearance player to his old franchise, whose vacated
pool includes his own production: his own `vac_*_share` then encodes "not playing early in
season t". Class size (usage folds): QB 14/260 — ~1 per fold in a 20-player universe. V3's
QB numbers below are therefore an UPPER BOUND with a known intra-season availability leak;
V5 (self-excluded) is the only carry candidate. V3 is retained in the table because the
V3−V5 spread *measures* the leak's worth — at QB, essentially all of it.

## Usage arm (folds 2012–2024, n=13), Δτ_b model−B1, with VBD-capture Δ

| Pos | V1 (no situation) | V3 (leaky) | **V5 (clean — carry)** | V6 (clean+QB-direct) | V5 ΔVBD |
|---|---|---|---|---|---|
| QB | −0.108 [−0.212,−0.013] | −0.018 [−0.120,+0.080] | **−0.125 [−0.218,−0.026]** | −0.141 [−0.201,−0.079] | −0.210 [−0.315,−0.124] |
| RB | +0.041 [+0.001,+0.080] | +0.040 | **+0.057 [+0.018,+0.095]** (10/13) | = V5 | **+0.032 [+0.002,+0.063]** |
| WR | +0.043 [+0.017,+0.071] | +0.033 | **+0.036 [+0.007,+0.067]** (9/13) | = V5 | +0.010 [−0.011,+0.033] |
| TE | +0.073 [−0.005,+0.152] | +0.091 | **+0.081 [+0.006,+0.160]** (8/13) | = V5 | **+0.073 [+0.034,+0.118]** |

Absolute τ_b, V5 usage arm: QB +0.151 / RB +0.352 / WR +0.394 / TE +0.330 (B1: +0.275 /
+0.296 / +0.358 / +0.248). Long arm (n=23) V5: QB −0.035 / RB +0.036 [+0.006,+0.066] /
WR +0.014 / TE +0.030 — same shape, smaller, consistent with the edge living in the usage
tier. No R² left its registered ceiling band; no §8 audit trigger fired (WR season R² 0.287).

## Consensus (ECR, 2021–2024, n=4, DESCRIPTIVE, veterans-only common universe)

Mean paired Δτ (model − ECR), V1 → V5: QB −0.223 → −0.241 · RB −0.110 → −0.110 ·
WR −0.033 → −0.046 · TE −0.001 → −0.016. Per-season V5 deltas: QB all 4 negative;
RB all 4 negative; WR 3/4 negative; TE 2/2 split. **The consensus gap did not narrow at any
position.**

## Findings against the registered predictions (the scorecard)

1. **R1's diagnosis splits in two.** "Vacated opportunity is real signal the model lacks" —
   CONFIRMED at RB (both co-primaries CI-clear, 10/13 folds; V3's registered RB magnitude
   band +0.05..+0.08 is hit by the CLEAN variant at +0.057) and TE (VBD). "Vacated
   opportunity explains the consensus gap" — **REFUTED at every position: the gap moved
   nowhere.** Consensus already prices this information; the feature lifts us relative to
   naive persistence, not relative to the market. The leading hypothesis for the consensus
   gap is eliminated as tested. Remaining candidates: rookie-driven situation change (the
   registered blind spot — arrivals are production-visible only), depth-chart/coaching
   information, injury-status timing, and plain aggregation efficiency.
2. **QB is closed.** Six configurations (V1, V2, V3, V4, V5, V6) across two sessions: none
   beats B1; the direct ridge *containing prior points as a feature* (V6) still loses
   −0.141, because at n≈18–20 QBs/fold a regularised 28-feature ridge cannot rediscover
   "weight prior points 1, everything else 0". The PM's hypothesis is refuted in mechanism
   (QB attempts/g y2y r=0.62 ≈ RB/WR — volume is NOT unusually team-stable) but confirmed in
   consequence: QB points persistence lives in the efficiency+rushing bundle S2 deliberately
   shrinks, and last-season-points rank carries it whole. Stop spending on QB modelling
   until a genuinely new information source exists (e.g. team pass-attempt projections from
   Vegas totals — no odds table yet, R-order territory).
3. **Prediction scorecard, stated plainly:** of the four registered prediction sets this
   session, three were materially wrong (V3: RB flat where gain was predicted, QB gain 5×
   the predicted band — leak; V5: QB fell below the predicted floor — the "genuine QB
   situation channel" is ≈0; V6: QB outside the predicted band on the wrong side). The
   registration discipline is what caught the leak and prevented a false "QB solved"
   headline. This is the system working, and the numbers above should be read with exactly
   that scepticism.

## Product recommendation (the mandate's hybrid-board question)

Measured evidence: consensus ≥ our best clean model at ALL positions (RB by −0.110, QB by
−0.241, WR/TE within noise). Therefore: (a) a position-hybrid RANKING (bottom-up RB/WR/TE +
consensus QB) is better than pure bottom-up but still not better than pure consensus as a
ranking; (b) the honest 2026 board stays consensus-anchored, with the bottom-up model
published as a LABELLED independent overlay at RB/WR/TE — where it demonstrably beats naive
persistence and sits within noise of ECR — and not offered at QB at all; (c) if the founder
wants mixed provenance in the primary board anyway, every row must carry its source per the
traceability principle, and the RB −0.110 must be printed wherever the overlay is sold.
V5's feature group belongs in ADR-E §4.1 (amendment queued with R3/R5/C3 for the
F-BOTTOMUP-CORE registration), self-exclusion mandatory.

---

# Session-4 appendix — V7, the rookie-arrival hypothesis (2026-07-27)

Registration: `docs/reviews/FABLE-EXT3-2026-07-27.md`, commit `5af349e`, frozen before any
V7 code existed (implementation `bf1c2d1`). One configuration: V5 + three same-position
rookie-arrival draft-capital features (`rook_cap_same` = Σ 1/√overall, `rook_top64_same`,
`rook_cap_x_vac` interaction with the self-excluded vacated share). Both arms, same folds.

## Result: the registered RB prediction FAILED — cleanly

Usage arm (the registered primary), V5 → V7:

| Pos | Δτ_b vs B1 | ΔVBD vs B1 | Consensus gap (n=4, descriptive) |
|---|---|---|---|
| RB | +0.057 → **+0.054** [+0.010,+0.097] | +0.032 → **+0.018** | −0.110 → **−0.112** |
| WR | +0.036 → +0.044 [+0.014,+0.075] | +0.010 → +0.019 | −0.046 → −0.036 |
| TE | +0.081 → +0.071 [−0.007,+0.153] | +0.073 → +0.048 | −0.016 → +0.001 |
| QB (descriptive, closed) | −0.125 → −0.151 | −0.210 → −0.208 | −0.241 → −0.275 |

Registered falsification rule: *"RB fails to improve on BOTH co-primaries vs V5 AND the RB
consensus gap does not narrow by ≥ 0.02."* All three conditions met: Δτ_b 0.057→0.054 (down),
ΔVBD 0.032→0.018 (down), gap −0.110→−0.112 (unmoved; per-season 2021–2024: −0.123/−0.236/
−0.063/−0.027 vs V5's −0.100/−0.234/−0.077/−0.027). The WR contradiction guard did not fire
(WR Δ = +0.008, within the registered ≤0.02 band). Long arm, for completeness: RB τ_b
+0.036→+0.046, VBD flat, gap −0.114→−0.108 — a small tau movement in the predicted direction,
short of every registered threshold, and reported as exactly that.

**Verdict: rookie-driven situation change, as expressible through same-position draft
capital, is ELIMINATED as the explanation of the RB consensus gap.** V7 does not replace V5
as the carry candidate (decision rule: improved on neither co-primary). Audit posture: no §8
trigger — mean season R² per position all inside bands (RB 0.184 / WR 0.300 usage); the one
single-fold excursion (2022 WR 0.540) pre-exists in V5 (0.534) and is not V7-induced.

## What this elimination means

Two mechanisms are now tested and eliminated as the gap's explanation: vacated opportunity
(V5) and rookie arrivals via draft capital (V7) — the two channels the ranking-design review
ranked highest on residual-mispricing × feasibility. Remaining, per the registration's own
list, in rough order of testability: (a) rookie *inclusion* — rookies themselves as
mispriced universe members (C3's arm, reserved for the return-week registration; note it
answers a different question — expanding who we rank — rather than fixing veteran ranks);
(b) ECR's non-box-score information (camp/beat/injury timing) — not a feature family at all,
partially the T-series' job; (c) coaching/scheme change (R2, gated on data licensing);
(d) **no single channel** — ECR as an aggregate of many small edges. After two clean
eliminations, (d) is now the working favourite, and its product consequence is already
adopted: the consensus-anchored board with a labelled overlay (D7). Chasing the gap further
has visibly diminishing returns; the next registered spend should be the confirmatory
F-BOTTOMUP-CORE run on V5, not another gap hypothesis.

## Prediction scorecard update

The registered V7 RB prediction (gain +0.010..+0.030, gap narrowing 0.02–0.05) was wrong in
direction. Running count across sessions 3–4: four of five registered prediction sets
materially wrong, every miss on the side of over-crediting a situation story. The
registration discipline converted each miss into a clean elimination instead of a shipped
overfit — and the pattern is now strong enough to state as a standing prior: **in this
project, situation narratives should be priced at half their intuitive weight before
registration.**
