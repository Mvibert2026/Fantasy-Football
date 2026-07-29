---
id: PR-005
test_registry_id: ADR-E-§9
family: F-BOTTOMUP-USAGE
mode: confirmatory
question: On the seasons where target and air-yards data exist, does the frozen V5 usage-feature
  bottom-up projection — the model that would actually ship — order draft-relevant veterans
  better than ranking them by prior-season fantasy points, by a margin large enough to change
  one real draft decision, at QB, RB, WR and TE independently?
metric: Identical to PR-004 section 7 in every respect except the fold set — mean paired Kendall
  tau-b difference vs B1 over embargoed-LOSO folds, within position, on the fold's pre-season
  frozen universe, with a season-level bootstrap 95 percent CI over fold-level paired
  differences. B2 gate, points-per-game artefact guard, and season-points R-squared gate as in
  PR-004.
threshold: Identical to PR-004 section 4, criteria (a)-(h), with two differences forced by the
  smaller fold count and stated in section 2 below — criterion (b) remains ADR-E's >= 75 percent
  but its equivalent sign-test p is weaker here (10/13 is p approx 0.092), and criterion (g)
  splits the fold set at 2018. Benjamini-Hochberg is applied within THIS family across its own
  declared m=4, never pooled with PR-004.
data_scope: {seasons: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020,
  2021, 2022, 2023, 2024], evaluation_folds: [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
  2020, 2021, 2022, 2023, 2024], holdout_unsealed: false}
frozen: {model: V5 exactly as carried out of session 4, registered_at: 2026-07-29,
  registered_by: strategist, seed: 20260729, bootstrap_draws: 10000,
  content_hash: PENDING-FREEZE}
secondary: Consensus ECR comparison is DESCRIPTIVE ONLY and lives in PR-004 section 11 — it is
  not duplicated here and must not be run twice under two ids.
resampling_unit: season
power_note: n=13 folds. The fold count is capped by target/air-yards availability
  (experiments/bottomup/data.py:60 — targets absent 2003-2008, air yards 2009+), NOT by
  consensus coverage. At n=13 criterion (b)'s >= 75 percent corresponds to sign-test p approx
  0.092, weaker than alpha=0.05; the bootstrap CI and BH criterion (c) therefore carry the
  inferential weight here, and the exact sign-test p is reported so the gap is visible.
amendments:
---

# PR-005 — F-BOTTOMUP-USAGE: the confirmatory run on the shipping model

**Registered 2026-07-29 by `strategist`, before any run.** This file deliberately does not
restate PR-004's protocol; it inherits it by reference. Read
`docs/preregistration/PR-004-bottomup-core-confirmatory.md` first.

## 1. Why this is a separate registration and not a second arm of PR-004

`experiments/bottomup/data.py:60` — `TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or
(s >= 2009)`, air yards 2009+ only — means the usage model **cannot be built across the deep
record**. PR-004 and PR-005 are therefore different models on different samples answering
different questions, and folding them into one family would either dilute the denominator to
m=8 or, worse, invite reporting whichever arm won.

**The split is the honest structure, and the trade should be read plainly:** PR-004 has the
power and the weak model; PR-005 has the strong model and the short sample. Neither alone
settles bottom-up. Registering both now, with separate fixed denominators, is what stops the
outcome being chosen after the fact.

**BH is applied within each family across its own declared m=4** (ADR-E §10: "BH is applied
within family"). Across-family familywise error is **not** controlled, and that is stated rather
than hidden — the compensating discipline is that the STOP condition in §3 requires *both*
registrations to fail before the program continues, which is conservative in the direction that
matters.

## 2. The two deviations from PR-004's rule, both forced by n=13

1. **Criterion (b)'s stringency.** ADR-E's ≥75% is kept unchanged, but at n=13 it corresponds
   to 10/13, sign-test p ≈ 0.092 — *weaker* than α=0.05, where at n≈25 it is stricter. The
   inferential weight here sits on criterion (c) (bootstrap CI excluding 0 and BH survival).
   The exact sign-test p is reported alongside so the difference is visible rather than implied.
2. **Criterion (g)'s era split** is at **2018** (the median of folds 2012–2024) rather than
   PR-004's median. Fixed here, in advance, so it cannot be chosen after seeing the series.

Everything else — the **+0.04 materiality floor** (unchanged: materiality is decision-relevance
arithmetic and does not move with n), the B2 gate, the ppg artefact guard, the §8 audit trigger,
cross-process determinism at seed 20260729, the frozen veterans-only universe, embargoed LOSO
excluding {N−1, N, N+1}, the sealed 2025 holdout, and the three closed exits — is identical to
PR-004 §4 and §7 and is not restated.

## 3. Stopping condition

**If neither RB nor WR reaches ADOPT-OVERLAY under PR-005 *and* neither does under PR-004,
bottom-up is dead as a 2026 product input**: consensus-only board, no overlay, both families
set to `closed`, finding written in ADR-E §9's pre-committed shelving language. If PR-005
clears at a position and PR-004 does not, the outcome is a **labelled overlay at that position
only**, with the sample limitation printed wherever the overlay is shown — never a claim about
the architecture in general, which is PR-004's question and would have failed.

## 4. Predictions

| Position | V5 usage exploratory dtau vs B1 | Prediction |
|---|---|---|
| **RB** | +0.057 [+0.018,+0.095], 10/13 | **The only live candidate.** Clears (b) and (c); ~55/45 on (a). LOSO plus embargo are both expected to shave the estimate. |
| **WR** | +0.036 [+0.007,+0.067], 9/13 | **Fails (a) and (b).** Point estimate below the floor; fold count below 10/13. |
| **TE** | +0.081 [−0.007,+0.160], 8/13 | **Fails (b), and the dR2 gate on season-points R² −0.85.** |
| **QB** | −0.125 [−0.218,−0.026] | **Fails, negatively.** Six configurations already failed. Included only to keep m=4 honest. |

Calibration prior applied: V5's advantage over V1 comes precisely from a situation feature
family, and four of five registered prediction sets in this project were wrong in exactly that
direction. **Modal outcome across both registrations is STOP.**

## 5. Selection contamination — worse here than in PR-004

V5 was selected from eight configurations evaluated on **these exact 13 folds**. PR-005
therefore does **not** measure V5 against data unseen by the selection process; it measures what
the effect looks like under a pre-registered rule with an honest CI, a fixed denominator, the
embargo, and a threshold that can fail. **It cannot establish out-of-sample skill for the V5
configuration choice.** A PASS must carry this sentence. Only the sealed 2025 unseal (n=1, one
shot, named human approver, **not authorised here**) or P-2026 could establish that.

## 6. Freeze

Same two-pass procedure as PR-004 §10 steps 3–6, against this filename. No census is needed —
the fold set is fixed by data availability and is written into `data_scope` above. Freeze both
registrations in the same commit.
