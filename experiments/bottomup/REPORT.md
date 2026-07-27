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
