# Batch D1 — Amendment 1: the availability model's missing quality channel

**Registered by `strategist`, 2026-08-01, before any arm was fitted.** Written at `ranker`'s request
(thread `2026-08-01-three-rulings-needed-the-endpoint-is-the-bottlen`, R3), because the finding was
discovered in batch D1's own output and the agent who found it correctly refused to register and run
it in the same breath.

**Reference this file from `batch-D1.md`'s header. It is deliberately a separate file** — the
manifest directory is sharded one file per batch precisely so concurrent agents cannot clobber each
other, and an amendment written by a different agent is exactly that case.

Binding: ADR-070 (the replacement inclusion rule), ADR-069 (absolute quality, no consensus input).

---

## 1. The finding this amendment tests

`ranker`, batch D1: **the games model is unbiased on the population it is fitted on and 2.41 games
low on the population it is used on.**

| population | n | realised games | projected | bias |
|---|---|---|---|---|
| full veteran universe — **fitted on** | 1,945 | 8.41 | 8.27 | −0.14 |
| board (M-panel) veterans — **used on** | 597 | 13.53 | 11.12 | **−2.41** |

Calibration on the fit population is near-perfect (slope 0.976, intercept 0.35), so this is a
**population mismatch**, not a mis-calibrated curve. At **matched** projected games (9–13) and
matched prior availability, board and non-board players differ by 4.2 realised games and are
separated by **prior-season production** (`pts_1` 181.9 vs 87.8) at equal `gshare_1` and equal age.

The games model's feature list — `gshare_w, gshare_1, present_1, age, age2, evidence` — **contains
no measure of how good the player is**, only of how available he has been. The hypothesis is that
**availability is partly job security**, and nothing in v2 models it.

---

## 2. Three arms. The one `ranker` did not propose runs first.

| arm | what it adds | why |
|---|---|---|
| **Q0 — population refit** | **no new features.** The incumbent feature list, refit with the veteran training population restricted to the board (M-panel) population, and a second variant weighting toward it | **The trivial explanation, tested before the interesting one.** "A plain recalibration cannot fix it" is correct and does not cover this: a refit on a different population is not a recalibration, it is a different fit, and it is untested. If Q0 captures most of the 2.41 games, the finding is "we fit on the wrong population" — simpler, cheaper, and it transfers to every other component. This is batch 7's `*_known` lesson applied in advance |
| **Q1 — quality block, full** | `ppg_w, tshare_w, cshare_w, depth_first_share_1, log_draft_pick, undrafted, experience` appended to the veteran availability spec | `ranker`'s proposal as written |
| **Q2 — quality block, `ppg_w`-free** | Q1 minus `ppg_w` — role and draft-capital terms only | Settles the double-count concern on evidence rather than argument (§4) |

**Positions:** QB, RB, WR, TE. **`m_b` = 12** (3 arms × 4 cells).
**Campaign M: 130 (C1) + 88 (D1) = 218 → 230.** The lag-weight decay profile adds 4 if it runs.

**Every arm differs from its matched control by exactly one thing.** Volume specs, rate specs, bonus
curves, scoring, ordering path and evaluation population are inherited unchanged. Q0 changes the fit
population and nothing else; Q1/Q2 change the availability feature list and nothing else.

**ADR-069 compliance, asserted not assumed:** no column is an expert ranking, a market ranking, a
consensus rank or an ADP value. `log_draft_pick`/`undrafted` are NFL draft position — an observable
league fact predating the season by years, not a fantasy-market opinion. Every arm asserts
`n_preseason_proxy_reads == 0`. **The 2025 holdout is not opened and nothing here would warrant
opening it.**

---

## 3. Span, universe and control — tier 2, and why this amendment can have it immediately

Per the tier ruling (ADR-070 §4.8): **grading panel `m_panel_ppr12`, targets 2013–2024, S = 12 at
all four positions**, with a matched control at an identical provenance key. Every cell carries the
four-part key `universe / targets / S / first_feature_season` and its `S_pos`.

**This amendment is eligible for tier 2 now, unlike the rest of D1**, and the reason must be
asserted per column rather than assumed: **no column here needs `rosters_weekly`**, whose end-of-
season reserve capture is unusable before 2018 (prevalence 0.012–0.045 for 2012–2016 vs 0.17–0.28
from 2017) and which is what pins the rest of D1 to CTRL-D. `ppg_w`, `tshare_w`, `cshare_w`,
`experience` come from core stat lines (no gaps 1999–2025); `depth_first_share_1` from
`depth_charts_weekly` (2001+); `log_draft_pick`/`undrafted` from draft picks. **2013–2024 is also
entirely clear of the 2003–2008 targets hole**, so `tshare_w` is clean at every target season.

**If any column turns out to need a later-starting source, it gets its own matched control at its
own window** — the existing CTRL-A/B/C discipline — and the cell is reported at its own `S`, never
merged with a differently-spanned one (§4.8 rule 1, enforced by a raise).

---

## 4. Endpoint — games, not points, and that dissolves the double-count problem rather than testing it

`ranker` asked how the sceptical version of "`ppg_w` also feeds the rate channel, so quality
multiplies twice into projected points" gets tested. **It does not need testing. Grade the games
block on games, and points never enters the endpoint, so the double count cannot flatter it.**

| | endpoint | population | role |
|---|---|---|---|
| **primary** | games MAE vs the incumbent, and vs naive persistence | **M-panel board veterans — the population it is used on** | decides the arm |
| **secondary, mandatory** | games MAE | full veteran universe — the population it is fitted on | must not degrade |
| **co-reported** | `ρ(games)` ordering | both | ADR-070 §4.8 co-reporting |
| **reported only, never graded** | `ρ(points)` ordering and the continuous points residual | both | the downstream consequence; **cannot promote an arm** |

This inverts the mismatch that produced the finding: the model is graded first on the population it
is used on, and the population it was fitted on becomes the guardrail rather than the target.

**Statistics:** ADR-070 §4 in full — matched null ensembles (§4.1), Besag–Clifford sequential p
(§4.3, `h = 20`, `L = ceil(2M/q) − 1 = 4,599` at M = 230), the §4.4 verdict taxonomy, the §4.4a
CONSISTENCY condition, the §4.4b RE-SPECIFY/EXCLUDE split on harm, BH at campaign M, q = 0.10.
Games MAE is continuous on n ≈ 600 (panel) and ≈ 1,945 (full), so §1.1's discreteness does not
apply — **but §4.9 binds: continuity is not calibration.** Season-block resampling clustered by
player, and the §6.2(a) leave-one-out check on this endpoint **before** any arm is graded.

---

## 5. Decision rules, fixed now

| outcome | reading |
|---|---|
| **Q0 alone recovers ≥ 0.6 of the 2.41-game level** | the finding is a **fit-population error**, not a missing channel. Q1/Q2 are reported but do not enter the model on that evidence, and the same audit is owed on every other v2 component fitted on the full universe and used on the board |
| **Q0 recovers < 0.3 and Q1 or Q2 is a BH-robust WIN** | the quality channel is real. Adopt the **narrower** of Q1/Q2 that wins — Q2 if both win, since it is the one that cannot double-count |
| **Q1 wins and Q2 does not** | the effect is carried by `ppg_w` specifically. **Do not adopt on the primary endpoint alone**; report it and escalate, because that is the exact cell where the two-channel concern lives |
| **Nothing wins** | report plainly (guardrails §5). The −2.41 stands as a named open defect of v2's games channel, unexplained |
| **Q0's restricted-population variant improves the panel and degrades the full universe** | expected, and it is the §4.8 conflict rule's third row: eligible, flagged narrow-population-specific, re-checked at §6.5 |

---

## 6. Registered predictions, so this can be wrong in public

Written before any arm is fitted. Priced against the standing calibration prior that four of five
registered prediction sets in sessions 3–4 over-credited a plausible mechanism story.

1. **Q0 recovers a substantial part of the level — I put it above even money.** The mechanism story
   ("availability is job security") is the attractive one and I am discounting it by half; the dull
   explanation is that a model fitted on a population averaging 8.41 games and applied to one
   averaging 13.53 will be biased low regardless of which features it holds.
2. **Q2 ≈ Q1.** If a quality channel exists, role and draft capital carry most of it and `ppg_w`
   adds little — which would also retire the double-count question.
3. **Games MAE improves and `ρ(games)` ordering barely moves.** This is a **level** defect; removing
   a constant bias does not reorder anyone. If ordering moves a lot, look for a bug before
   celebrating.
4. **`ρ(points)` improves less than the games improvement implies**, because the points channel is
   dominated by the rate and volume models.
5. **QB is the cell most likely to be undecidable** even at S = 12, per ADR-070 §4.4a.

---

## 7. What this amendment does not do

It does not adopt anything, it does not touch `ranking_versions/v2.json`, and it does not re-open
D1's graded cells. It does not fit a decay profile (that is
`PR-DRAFT-lag-weight-decay-profile.md`). It does not address rookies — `ROOKIE_COLS =
["log_draft_pick", "age"]` being the entire rookie model is a real and separate finding needing its
own registration, and folding it in here silently would be exactly the scope creep this file's
`m_b` accounting exists to prevent.
