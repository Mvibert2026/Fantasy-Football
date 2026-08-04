# Batch D1 — the projected-games (player availability) component of ranking v2

**Registered by `ranker`, 2026-08-01, before any arm was fitted.**
Branch `claude/pm-agent-setup-gobxa0`. Campaign manifest: `README.md` (one file per batch).

> **m_b = 88.** Σ m_b across the campaign becomes **218** (56 from batches 5/6/7, 16 from M2,
> 20 from B1, 38 from C1, 88 here; PR-007's 4 sit in their own family and are excluded).
> `M_campaign = max(Σ m_b, 80) = 218`.

---

## 1. Why this batch exists

Fable's M2 located ranking v2's *entire* measured deficit against consensus in one channel:
**projected games**. v2's rate projections are at or better than market parity; its games estimate
has near-zero ordering skill (ρ 0.12–0.24 against realised games) and loses to naive persistence on
MAE at 3 of 4 positions. `CLAUDE.md` §2a names the consequence: independence from consensus stands
or falls on building our own answer to *who is going to play*.

Batch B1 tried to fix it from the **weekly box score alone** (arms G1 / G1a: when in season N−1 the
player's games happened). Both were rejected by their own registered rules. The one arm that worked,
G2a, used **week-1-of-season-N roster status**, which strategist has not admitted (it is
Week-1-kickoff-dated, days after the founder's 7 September draft; conditions C1–C5 unmet).

**This batch uses the data B1 never had, on the correct side of the cutoff.** Three tables are
ingested and read by no model: `injuries` (79,816 rows, 2009–2024, carrying **practice
participation** and **body part**), `rosters_weekly` (888,786 rows, 2002–2025, carrying **weekly
roster status**), `depth_charts_weekly` (865,329 rows, 2001–2024). Season N−1's rows from all three
are ordinary lagged information with no as-of question whatsoever.

---

## 2. Pre-registration hygiene, stated up front

**A descriptive recon was run before this document was written, and it is disclosed here rather
than being allowed to look like a prediction.** No model was fitted; the recon computed group means
and Spearman coefficients on a survivorship-safe panel (universe for season N = players with ≥1 game
in N−1, outcome = games in N with zero for absentees, outcome seasons ≤ 2024). It is the reason the
blocks below have the shape they do. What it found:

| finding | number |
|---|---|
| Among players who missed ≥40% of N−1, **being on reserve (IR) at the end of N−1 predicts MORE games in N**, not fewer | 5.96 vs 4.14 mean games; 26.7% vs 13.7% reach 12+ games; n = 562 / 3,079 |
| B1's box-score timing signal (played in the last 3 weeks of N−1) separates almost nothing in that same population | 4.56 vs 4.19 mean games; 16% vs 16% reach 12+ |
| Weeks on the injury report correlate **positively** with next-season games on the full population | ρ = +0.236 — an employment proxy, which is why the presence-control arms below exist |
| `depth_charts_weekly` is **eliminated** as a substitute source for end-of-season employment | its end-of-season-present-but-absent flag gives 4.26 vs 4.44 mean games, sign flipping season to season |
| Among players who played every game of N−1, practice DNP count separates nothing | 12.57 vs 12.58 mean games in N |

**Coverage, measured, and the window restriction it forces.** `rosters_weekly` carries RES rows from
2002, but end-of-season RES *capture* breaks hard: prevalence of `res_end` in the missed-≥40%
population is 0.012–0.045 for feature seasons 2012–2016 and 0.17–0.28 from 2017. Pre-2017 the
feature is a **time dummy in exactly batch 7 D2's geometry**. Batch 5's mistake was restricting the
target window only; the fix is to restrict the **training** window. Hence a second control whose
`first_feature_season` is 2018 (lag-1 = 2017), and the roster arms are graded only against it.

**Grading is suspended.** C1 measured the registered WIN rule awarding a WIN to seeded noise on
**9.6% of cells against a nominal 2.5%**; `strategist` owns the replacement rule (thread
`2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi`). **No arm in this batch may be graded
INCLUDE.** Arms run, record per-season deltas and CIs, and carry **two placebo arms** — one per
control window, because C1 showed the miscalibration is a function of n and the two windows have
n = 7 and n = 5. Re-grading under a replacement rule is mechanical and requires no refit.

---

## 3. Arms

Every arm is ranking v2 with **one thing changed**: the feature list the veteran projected-games
GLM consumes. Volumes, rates, bonus curves, scoring and the rookie availability path are inherited
bit-for-bit. No arm reads season N. No arm calls `week1_roster` / `preseason_roster`; every arm
asserts `n_preseason_proxy_reads == 0` and would crash on contact with the G2a proxy.

### Controls (matched, not graded cells)

| control | `first_feature_season` | targets | n | who uses it |
|---|---|---|---|---|
| **CTRL-A** | 2012 | 2018–2024 | 7 | full-window arms (`injuries` usable from 2010) |
| **CTRL-D** | 2018 | 2020–2024 | 5 | roster-status arms (`rosters_weekly` end-of-season capture from 2017) |

Both controls are **v2 with games arm G0** — the unmodified incumbent, `clip(OLS(AVAIL_A), 0, 1) ×
season_len` — pinned exactly as batch C1 pinned it. G2a's ruling is ADMIT-WITH-CONDITION with
conditions unsatisfied, so G0 stands.

### Feature blocks

```
B0  gshare_w, gshare_1, present_1, age, age2, evidence          (= pos_features.AVAIL_A)
P   prac_rep_share_1, prac_dnp_share_1, prac_lim_share_1, prac_out_share_1,
    prac_dnp_of_rep_1, prac_dnp_late3_1, miss1_x_dnp_share
C   inj_struct_share_1, inj_soft_share_1, inj_head_share_1, inj_rest_share_1,
    inj_nclass_1, inj_recur_1, inj_recur_known_1
R   res_share_1, res_end_1, res_resolved_1, act_share_1, miss1_x_res_end
```

Each block carries **one** interaction with lag-1 missed share and only where the recon motivated
it, because the GLM is linear in the logit and the hypothesis is conditional: an ongoing reserve
designation is informative *given* a lot of the season was missed and near-vacuous otherwise.

### The eleven arms

| arm | control | games feature list | what it isolates |
|---|---|---|---|
| **P0** | CTRL-A | B0 + seeded N(0,1) | PLACEBO — calibration at n = 7 |
| **P0d** | CTRL-D | B0 + seeded N(0,1) | PLACEBO — calibration at n = 5 |
| **B0** | CTRL-A | B0 | ESTIMATOR FORM ONLY (binomial GLM vs clipped OLS) |
| **B0d** | CTRL-D | B0 | the same at the short window, so A3/A5 can be read against form |
| **A1** | CTRL-A | B0 + P | practice participation |
| **A1k** | CTRL-A | B0 + `prac_present_1` | PAIRED CONTROL — bare "appeared on an injury report" |
| **A2** | CTRL-A | B0 + C | injury class and cross-season recurrence |
| **A3** | CTRL-D | B0 + R | roster status: resolved vs ongoing absence |
| **A3k** | CTRL-D | B0 + `ros_present_1` | PAIRED CONTROL — bare "has a roster row in N−1" |
| **A4** | CTRL-A | B0 + P + C | the full-window combination |
| **A5** | CTRL-D | B0 + P + C + R | everything |

A4 and A5 are registered **now**, not selected after seeing A1–A3, so the combination is not
post-hoc.

---

## 4. Endpoints and multiplicity

Two graded endpoints per arm per position. Populations follow the standing convention: the
**M-panel veterans** (FFC ADP membership defines the evaluation subset; the ADP column is never a
feature and never an ordering input), season cells with ≥10 graded players.

| id | endpoint | contrast |
|---|---|---|
| **E1** | ρ(proj_points, realised points) — the ADR-069 absolute steering metric | arm − matched G0 control |
| **E2** | ρ(proj_games, realised games) | arm − naive persistence (`games_1`) **within the same arm** |

**m_b = 11 arms × 2 endpoints × 4 positions = 88.**

Reported but **outside the family**, not corrected, and never quotable as if corrected: games MAE
(arm, G0 and naive persistence), the projected-games level bias on board veterans, per-arm coverage
of each source, the resolved-vs-ongoing subgroup table, and the two named case studies (Burrow,
Taysom Hill).

Estimator, unchanged from B1 and C1 so this batch extends one harness rather than inventing a
second: paired season-block bootstrap on per-season deltas, 4,000 reps, seed 20260801, |Δ| < 1e−9
snapped to zero (C1's numerical-hygiene fix). BH at `M_campaign = 218`, q = 0.10, reported but
**not decisive** while the WIN rule is suspended.

---

## 5. Registered predictions

Written to be wrong. Four of five registered prediction sets in this project were materially wrong
and every miss over-credited a situation story, so these are deliberately conservative.

1. **P0 and P0d: 0 WIN, 0 HARM.** Any WIN is a finding about the harness and invalidates this
   batch's WIN rate rather than adding to it. Given C1's measured 9.6%, I expect **1–2 placebo WIN
   cells out of 16** and will treat that as the calibration bar, not as a surprise.
2. **B0 (form only): NULL at every position on E1.** If the GLM alone moves absolute quality, the
   B1 grades that attributed G1a's failure to features were reading form.
3. **A3 is the arm most likely to carry signal, at RB and WR, on E2.** It is the only arm holding
   the instrument the recon says separates the defect population, and RB/WR are where games
   variance is largest and the graded n is biggest. I put **60%** on A3 clearing its window's
   placebo 95th percentile on E2 at ≥1 of RB/WR, and only **30%** on it doing so on E1 — a games
   improvement has to survive multiplication by a rate projection to reach points.
4. **A1 and A2 are more likely NULL than not.** Practice participation is measured on the wrong
   population (recon: it separates nothing among iron men and is confounded by employment among the
   absent), and injury class is a situation story of exactly the kind this project's calibration
   prior says to halve. I put **25%** on either clearing its placebo q95 anywhere.
5. **A1k / A3k are the arms I expect to be embarrassed by.** If a bare presence indicator matches
   its block, the block is an employment proxy. Batch 5 hit this at 1.06×–19.7×. I put **40%** on at
   least one presence control matching or beating its treatment.
6. **QB will not be fixed.** QB modelling was closed after six failed configurations, the graded
   population is ~19, and C1 measured the placebo winning 14.7% of QB cells. Any QB WIN here should
   be read as noise until replicated.
7. **The level bias will not close on its own.** B1 measured ~−2.6 games on board veterans (G0 /
   G1 / G1a). None of these arms changes the fitting population, so I expect it to persist, and
   fixing it is a separate registered arm this batch does not run.

## 6. Stopping and adoption

No arm is adopted on this batch's evidence. The batch ends by handing `strategist` the per-season
deltas, the two placebo nulls and the recommendation of at most **one** confirmatory arm. Shipping
into `src/` is `backend`'s, on a version `strategist` has reviewed. `2025 is never read`; the
outcome gate refuses to serve it and every arm asserts `players["season"].max() < 2025`.
