---
ID: 087
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: FR-039 reaching the board
OPENED: 2026-07-29
---

## Ask

FR-039 pass 2 is complete and **exploratory** — `docs/ranking/bottom-up-research-pass-2.md`,
code at `experiments/bottomup/pass2_te_adp.py`. No result in it is claimed as significant, no
correction for multiplicity was applied, and nothing from it goes near the board until you rule.
Three things from you, in order of how much they block.

### 1. Register (or reject) the one confirmatory test worth running

**Claim to test.** *In this league, the TE consensus window `TE7-10` (overall ECR ~75-113,
rounds 8-11) is the value-maximising place to take the position — it is VBD-neutral against the
best alternative at the same cost, and it dominates any number of late-round TE darts.*

**Pre-specified design, which I have NOT run:**

| | |
|---|---|
| Universe | Every TE on the pre-draft consensus list, `rankings` where `source='fantasypros_ecr' AND is_preseason_final=1`. Frozen pre-season by construction. Never-played TEs score 0 and are retained. |
| Target seasons | The sealed **2025** holdout, touched once, plus FFC half-PPR seasons if thread 055/084 land any |
| Primary statistic | Mean realised VBD (10-team, QB10/RB30/WR40/TE10) of the TE at consensus positional rank 7-10, minus mean realised VBD of the best-ECR non-TE available in the same overall-rank window |
| Secondary | P(realised top-6 TE) for one TE7-10 pick vs. P(≥1 top-6 TE) from k=2,3 darts at ECR 111-150 |
| **Stopping condition, committed in advance** | **One evaluation on 2025. No re-fit, no band re-cut, no alternative threshold after seeing it.** If the TE7-10 mean-VBD advantage over the same-cost alternative is not ≥ 0 on 2025, the claim is reported as FAILED and the window recommendation does not ship. |
| Pre-declared exclusion | I will not substitute TE6-11 or TE8-12 after the fact. The band is TE7-10 because that is where the exploratory pass put it; moving it post hoc is the failure mode this registration exists to prevent. |

**What I need from you:** either register this as written with an ID, amend the design, or tell
me the n=1-holdout-season power makes it not worth burning the holdout on. That last answer is a
real answer and I would rather have it than a test that cannot resolve.

### 2. Rule on a look-ahead judgment call I already made, so it is on the record

The founder's motivating example is Tucker Kraft, whose breakout is the **2025 sealed holdout**.
I did not read any 2025 outcome. I **did** read two pre-draft rows: the 2025 preseason ECR list
for TEs, which shows Kraft at **TE11, overall 105**, and his 2023/2024 outcomes (both unsealed).

My reasoning: a pre-draft ranking is a *feature*, not an outcome, and carries zero information
about what happened in 2025. It let me answer the founder's actual question — how expensive was
Kraft really — without spending the holdout. **I believe this is clean. You should confirm or
overrule it**, because if reading 2025 pre-draft features counts as contaminating the holdout
then the confirmatory test in §1 is already compromised and I need to know now, not after.

### 3. Rule on a multiplicity posture

Pass 2 reports well over 100 descriptive quantities (6 TE bands × 3 statistics, 16 position ×
overall-band cells, 11 forecastability signals × 3 configurations, 4 Kraft-pattern contrasts).
None is corrected. Two survive at face value with intervals excluding the null — and both are
restatements of the market (consensus ECR rank itself, AUC 0.649 [0.56,0.74]; and the single
most optimistic expert's rank, 0.692 [0.61,0.78]). Everything genuinely new is a coin flip.

I read that as a **clean negative that needs no correction to interpret** — nothing new survived
even uncorrected, so correction can only strengthen the conclusion. Confirm that reading, or
tell me the negative itself needs a formal treatment before it can be cited.

## Why

FR-039 is a founder directive with a decision attached, and the exploratory answer **contradicts
the strategy he proposed** on the specific point that matters (see the thread reply / the pass).
That is exactly the situation where an agent grading its own homework does the most damage. I am
not going to tell the founder his instinct is wrong on the strength of an unregistered pass.

The blocking risk is the opposite of the usual one: not that I ship something too weak, but that
a *negative* result gets treated as settled when it rests on 4 consensus seasons and 24 top-6 TE
outcomes total.

## Done looks like

1. A registration ID for the §1 test with the stopping condition as written, an amended design,
   or a reasoned "do not burn the holdout on this".
2. A yes/no on §2 — is reading a sealed season's *pre-draft* ranking a holdout violation.
3. A yes/no on §3 — is the uncorrected negative citable as a negative.
