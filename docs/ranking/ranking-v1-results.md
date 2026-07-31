# Ranking version v1 — assembled, and tested end to end

**Ranker, 2026-07-31.** Pre-commitment: `docs/ranking/ranking-v1-precommit.md`, committed at
`5ffbbef` **before** the runner existed and before any v1 number was computed. Config blob:
`experiments/bottomup/ranking_versions/v1.json`, **sha256 `ab15cb93467b4f3f…`**.

Reproduce: `.venv/bin/python -m experiments.bottomup.ranking_v1` then
`… -m experiments.bottomup.ranking_v1_sensitivity`. Main checkout, branch
`claude/pm-agent-setup-gobxa0`.

**This is the first time a ranking version has been assembled or tested in this project.** Across
~90 registered tests in batches 1–7 every arm was a single feature inside one component of an
unshipped model. The proposition "our model does not beat consensus" had never been tested with a
model. It has now.

**Holdout:** 2025 was never read. `CLAUDE.md` §6.3 as ruled today — the holdout does not open until
`fable` has run, and `fable` has not run. Nothing below asks for it.

**Nothing here is judged by me.** Independent checks named in §8.

---

## 1. What v1 contains

| | |
|---|---|
| **Engine** | `pos_eval.WalkForward`, availability **arm A** (the pre-committed primary), `calibrate_bonus=True`, unmodified. Emits `proj_points` — full season points under this league's ruleset including stacking bonuses |
| **Positions** | QB · RB · WR · TE |
| **DEF** | **blank, with a note.** Zero coverage in `nfl.db`. No fabricated number |
| **Rookies** | **pinned to consensus and labelled.** Rank-space assembly: rookies hold their consensus positional slot, veterans fill the rest ordered by `proj_points`. On rookie rows v1 *is* the crowd it is compared against |
| **Table stakes IN** | **#7 age** (`age`, `age2`) · **#8 prior-year target/touch share** (`tshare_w`, `cshare_w`) |
| **Table stakes in the secondary arm only** | **#6 injury designations** (`inj_missed_share_1`, `unexp_missed_share_1`) → reported as `v1b` |
| **Table stakes OUT** | **#5 depth-chart role.** Arms D/E are **post-hoc by their own source comment** (`pos_features.py:37-41`) and measured NULL. Shipping a post-hoc configuration is the failure this work exists to avoid |
| **Lagged-YPC → RB volume** | **EXCLUDED.** I searched all of `docs/preregistration/` including `families/*.yaml`: **no registration exists.** It was batch 6's largest `C2` movement and it is a post-hoc winner. Out, per the dispatch |
| **Cross-positional revaluation** | in the config, **untested by this design** — the per-position endpoint is blind to it. Not claimed |

### 1.1 v1 is the first object in this project that holds a player-level opinion

The shipped board's within-position order is **identical** to consensus (`fr136` §1.1) and correlates
with it at **ρ 0.972 across the top 100**. v1 does not:

| universe | ρ(v1, consensus) | mean \|Δrank\| | max Δrank | share of rows pinned (rookies) |
|---|---|---|---|---|
| market board, QB | **0.537** | 4.2 | 17 | 6.2% |
| market board, RB | **0.680** | 8.0 | 50 | 15.8% |
| market board, WR | **0.712** | 8.8 | 53 | 10.3% |
| market board, TE | **0.674** | 2.4 | 12 | 6.3% |
| expert board, RB | 0.840 | 16.1 | 94 | 18.0% |
| expert board, WR | 0.857 | 18.8 | 139 | 17.0% |

**This is a real independent ranking, not consensus with a tilt.** That matters for reading §3:
what follows is not a null produced by an object too similar to consensus to differ.

---

## 2. The bar, as pre-registered (§2.6 of the pre-commitment)

| outcome | rule |
|---|---|
| **EDGE** | Δρ 95% CI lower bound > 0 against **both** crowds |
| **SPLIT** | clears zero against one crowd, not the other — reported as exactly that, never the flattering half |
| **PARITY** | CI contains 0 **and** Δρ ≥ **−0.02**. *Not edge*, and may not be reported as one |
| **LOSES** | CI upper bound < 0, or Δρ < −0.02 with the CI containing 0 |
| **CANNOT ANSWER** | MDE > **0.10 ρ** at that position |

Endpoint: Spearman ρ vs realised season fantasy points, per position, per season, on the
board-restricted (`C2`) universe — strategist's Ruling 1 item 5. Season-block bootstrap, 4,000 reps,
seed 20260731. Busts retained at zero: **73 zero-game player-seasons in the market panel, 182 in the
expert panel, all retained.** Universes frozen pre-season from board membership.

---

## 3. Result — v1 against all four §6.5 baselines, both crowds

### 3.1 The two crowds (the primary family `F-RANKING-V1`, BH q = 0.10)

| panel | crowd | pos | seasons | **Δρ (v1 − crowd)** | 95% CI | p | BH reject | **verdict** |
|---|---|---|---|---|---|---|---|---|
| M | market ADP | QB | 7 | **−0.065** | [−0.246, +0.095] | 0.49 | no | LOSES (pt est below parity floor) |
| M | market ADP | RB | 7 | **−0.044** | [−0.121, +0.044] | 0.31 | no | LOSES (pt est below parity floor) |
| M | market ADP | WR | 7 | **+0.031** | [−0.035, +0.110] | 0.44 | no | **PARITY (not edge)** |
| M | market ADP | TE | 7 | −0.011 | [−0.163, +0.133] | 0.93 | no | **CANNOT ANSWER (design)** |
| E | expert ECR | QB | 4 | **−0.138** | [−0.194, −0.072] | 0.0002 | **yes** | **LOSES** |
| E | expert ECR | RB | 4 | **−0.093** | [−0.128, −0.059] | 0.0002 | **yes** | **LOSES** |
| E | expert ECR | WR | 4 | **−0.065** | [−0.102, −0.041] | 0.0002 | **yes** | **LOSES** |
| E | expert ECR | TE | 4 | +0.005 | [−0.025, +0.059] | 0.64 | no | PARITY (not edge) |

**v1 beats neither crowd at any position.** There is no SPLIT to report and no flattering half to
choose: the two crowds agree.

### 3.2 The two non-crowd baselines (context, not in the FDR family)

Δρ, v1 − baseline, 95% season-block CI. **Positive = v1 better.**

| panel | pos | vs **B3 prior-season points** | vs **B4 positional-tier heuristic** | vs B3w weighted prior PPG *(informational)* |
|---|---|---|---|---|
| M | QB | −0.031 [−0.149, +0.091] | +0.019 [−0.096, +0.129] | −0.031 [−0.134, +0.077] |
| M | **RB** | **+0.116 [+0.037, +0.187]** | **+0.162 [+0.105, +0.215]** | **+0.088 [+0.007, +0.167]** |
| M | **WR** | **+0.110 [+0.067, +0.155]** | **+0.149 [+0.109, +0.193]** | **+0.074 [+0.003, +0.143]** |
| M | TE | +0.112 [−0.021, +0.270] | +0.183 [−0.007, +0.402] | +0.052 [−0.061, +0.162] |
| E | QB | +0.086 [−0.006, +0.189] | +0.097 [−0.005, +0.213] | **+0.095 [+0.029, +0.168]** |
| E | RB | **+0.136 [+0.084, +0.180]** | **+0.170 [+0.108, +0.228]** | **+0.152 [+0.120, +0.190]** |
| E | WR | **+0.134 [+0.111, +0.152]** | **+0.169 [+0.129, +0.198]** | **+0.154 [+0.144, +0.165]** |
| E | TE | **+0.141 [+0.094, +0.177]** | **+0.151 [+0.098, +0.186]** | **+0.136 [+0.083, +0.188]** |

**v1 clearly beats both trivial baselines at RB and WR on the market board, and at RB, WR and TE on
the expert board.** It does not beat them at QB on the market board.

### 3.3 Levels, for scale only — the comparison is the headline (§6.5)

Mean ρ across seasons. **Do not read a level as a result.**

| panel | pos | v1 | market ADP | expert ECR | prior points | tier heuristic |
|---|---|---|---|---|---|---|
| M | QB | 0.265 | 0.330 | *0.470†* | 0.296 | 0.245 |
| M | RB | 0.488 | 0.532 | *0.549†* | 0.371 | 0.326 |
| M | WR | 0.537 | 0.506 | *0.540†* | 0.427 | 0.388 |
| M | TE | 0.389 | 0.400 | *0.368†* | 0.277 | 0.207 |
| E | QB | 0.609 | — | 0.747 | 0.522 | 0.512 |
| E | RB | 0.658 | — | 0.751 | 0.521 | 0.488 |
| E | WR | 0.677 | — | 0.742 | 0.543 | 0.522 |
| E | TE | 0.683 | — | 0.678 | 0.542 | 0.532 |

† ECR is only computable on the market panel for 2021–2024, so these four are a **4-season mean beside
7-season means** and are not comparable across the row. Shown because §6.5 asks for both crowds, not
because the comparison holds.

Panel E's levels are uniformly higher than panel M's because its universe is ~3× deeper — separating
ECR's WR180 from ECR's WR20 is an easy ordering problem that inflates every ranker's ρ. §5 quantifies
what happens when that depth is removed.

### 3.4 Decision-relevant (§6.6) — better rosters, not better lists

Rank correlation is a proxy. What the drafted top-k actually scored, v1 − crowd:

| panel | pos | k | top-k capture | mean actual points of the top-k |
|---|---|---|---|---|
| M | QB | 10 | −0.014 [−0.100, +0.071] | −13.4 [−33.9, +4.5] |
| M | RB | 20 | −0.036 [−0.079, +0.014] | −5.5 [−16.6, +5.9] |
| M | WR | 30 | +0.024 [−0.014, +0.062] | +1.7 [−2.5, +5.7] |
| M | TE | 10 | −0.000 [−0.057, +0.072] | −1.4 [−5.9, +3.1] |
| E | QB | 10 | **−0.125 [−0.175, −0.100]** | **−35.2 [−48.0, −23.6]** |
| E | RB | 20 | −0.050 [−0.100, +0.000] | **−9.6 [−14.5, −3.2]** |
| E | WR | 30 | +0.017 [−0.033, +0.067] | +1.3 [−5.6, +9.8] |
| E | TE | 10 | −0.050 [−0.100, +0.000] | −3.7 [−8.8, +1.3] |

Every market-panel interval is open. On the expert panel, **v1's top-10 QBs scored 35 fewer points
each than consensus's** — the largest single decision-relevant gap in the table, and it points the
wrong way.

### 3.5 `v1b` — adding table stakes #6 (injury designations) changes nothing

| pos | v1 Δρ vs market ADP | v1b Δρ vs market ADP |
|---|---|---|
| QB | −0.065 | −0.057 |
| RB | −0.044 | −0.046 |
| WR | +0.031 | +0.025 |
| TE | −0.011 | −0.039 |

Movement of 0.002–0.028 ρ, no verdict changes, no sign changes at RB or WR. **This is the fifth
independent measurement that the injury-designation block is inert at the ranking level.** Recorded
as a confirmation of a known null, not a new one.

---

## 4. Power — and the pre-registered rule was partly wrong, which I am reporting rather than quietly dropping

The rule (§2.5): MDE = half-width of the 95% CI on a **baseline-vs-baseline** contrast (B1−B3w in
panel M, B2−B3w in panel E). Above 0.10 → *the design cannot answer the question.*

| panel | pos | pre-registered MDE proxy | **direct half-width of the v1-vs-crowd CI** | proxy understates? |
|---|---|---|---|---|
| M | QB | 0.085 | **0.170** | **YES — by 2×** |
| M | RB | 0.091 | 0.083 | no |
| M | WR | 0.079 | 0.072 | no |
| M | TE | **0.147** | 0.148 | no |
| E | QB | 0.092 | 0.061 | no |
| E | RB | 0.063 | 0.035 | no |
| E | WR | 0.025 | 0.031 | no |
| E | TE | 0.041 | 0.042 | no |

**In advance I predicted QB and TE would trip the rule in panel M. TE did; QB did not — and then QB
turned out to be the one position where the proxy is wrong.** The MDE proxy is contrast-specific: it
bounds the contrast it is computed on, not the contrast that matters. At panel-M QB the real
resolution is 0.170, so **QB on the market board should also be read as *the design cannot answer
it*,** on the direct measure. I am applying the pre-registered rule as written for the verdict column
and flagging the discrepancy here rather than silently switching to whichever measure reads better.

**Recommendation to `strategist`:** future pre-registrations should define MDE as the direct
half-width of the contrast under test, estimated from the baseline arms' own season-to-season
variance, not from a proxy contrast.

**Positions the design genuinely resolves:** RB and WR on both panels; QB and TE on the expert panel
only.

---

## 5. Sensitivity — post-hoc, labelled, and it does not rescue v1

`experiments/bottomup/ranking_v1_sensitivity.py`. Panel E's universe is the full ECR board
(147–202 players per position), roughly 3× the market board's draftable depth. Ruling 1 item 5 made
`C2` — the *draft-relevant* universe — the endpoint precisely because movement among undrafted
players is not decision-relevant. So Panel E was re-run at the depth **the market itself** declares
draftable (per season and position, the top *N* of ECR where *N* = the count of players FFC's ADP
board covers there that season — externally determined, not chosen by me).

| pos | depth | Δρ full ECR board | **Δρ depth-matched** | verdict, depth-matched |
|---|---|---|---|---|
| QB | 21 | −0.138 | **−0.108 [−0.186, −0.027]** | **LOSES** |
| RB | 55 | −0.093 | **−0.070 [−0.123, −0.021]** | **LOSES** |
| WR | 59 | −0.065 | **+0.050 [−0.065, +0.204]** | PARITY (not edge) |
| TE | 17 | +0.005 | −0.041 [−0.189, +0.066] | LOSES (pt est below parity floor) |

**Two things follow, and the second is the one that matters.**

1. **WR's expert-panel loss was partly a depth artifact.** At draftable depth WR flips from −0.065
   (significant loss) to +0.050 (parity, interval open). WR is the same position that reads PARITY on
   the market panel. That is the one consistent bright spot in this entire pass.
2. **QB and RB lose to expert consensus at draftable depth, with intervals excluding zero.** Depth
   matching shrinks both losses; it does not remove them.

---

## 6. Non-stationarity (§6.4) — per-season ρ, so a regime turn is visible

Panel M, v1 vs market ADP:

| season | QB v1 / ADP | RB v1 / ADP | WR v1 / ADP | TE v1 / ADP |
|---|---|---|---|---|
| 2018 | **−0.084** / 0.374 | 0.522 / 0.547 | 0.637 / 0.627 | 0.413 / 0.636 |
| 2019 | 0.395 / 0.147 | 0.541 / 0.760 | 0.547 / 0.538 | 0.582 / 0.582 |
| 2020 | 0.409 / 0.417 | 0.468 / 0.568 | 0.381 / 0.407 | 0.365 / 0.085 |
| 2021 | 0.257 / 0.623 | 0.626 / 0.711 | 0.412 / 0.521 | 0.375 / 0.354 |
| 2022 | 0.415 / 0.319 | 0.410 / 0.414 | **0.733** / 0.492 | 0.350 / 0.203 |
| 2023 | 0.109 / 0.117 | 0.422 / 0.244 | 0.621 / 0.583 | 0.312 / 0.261 |
| 2024 | 0.352 / 0.314 | 0.423 / 0.477 | 0.429 / 0.374 | 0.329 / 0.678 |

**No monotone trend at any position for either arm.** The season-to-season swing (QB v1 ranges −0.08
to +0.42; market ADP at TE ranges 0.085 to 0.678) is far larger than any mean difference in §3.1 —
which is the same fact the wide intervals report, seen directly. **v1 beats market ADP at WR in 5 of
7 seasons and at RB in 3 of 7.** No recency weighting was applied; whether it helps is a separate
registered question and is not answered here.

---

## 7. The verdict, against the three outcomes the dispatch named

**Outcome 2: v1 loses to both crowds. Said plainly.**

> **v1 beats the two trivial §6.5 baselines — prior-season points and the positional-tier heuristic —
> decisively at RB and WR. It beats neither crowd at any position. Against expert consensus it loses
> at QB, RB and WR with BH-significant intervals, and the QB and RB losses survive depth-matching.
> Against market ADP it is at parity at WR and behind at QB and RB, with every interval open.**

**The one non-negative reading, stated at its true size and no larger.** WR is at parity with both
crowds — +0.031 [−0.035, +0.110] vs the market and +0.050 [−0.065, +0.204] vs depth-matched expert
consensus. **Parity is not edge.** §6.5 is explicit: a version that does not beat both crowds has no
edge. What WR shows is that an independent bottom-up ranking, correlating with consensus at only
ρ 0.712 and moving players a mean of 8.8 places, can *match* both crowds at one position. That is
evidence the approach is not hopeless. It is not a result to draft on.

**What this does NOT establish, stated before anyone quotes it.**

- **It does not establish that consensus is unbeatable.** It establishes that *this* version, from
  *these* features, does not beat it. Ruling 3.4 refuses the strong form and nothing here supports it.
- **It does not test the cross-positional channel** — the shipped board's *entire* current content.
  The per-position endpoint is blind to it by construction.
- **It does not answer QB or TE on the market board.** The design's resolution there is 0.170 and
  0.148 ρ against effects of plausible size ≤ 0.10.
- **It is a single version.** One feature set, one arm, no recency weighting, no snap counts, no NGS,
  no PBP-derived features — the four largest untouched blocks in the registry.

**Is the answer ambiguous, and does it need the holdout?** Partly ambiguous — at QB and TE on the
market board, and at WR everywhere. **It does not need the holdout, and I am not asking for it.**
What 2025 would settle is a *confirmatory* claim about a *frozen* model, and v1 is not frozen: it is
a first version with four named untested feature blocks. Spending a single-use holdout to confirm a
loss would buy nothing that the seven training seasons have not already said. Per `CLAUDE.md` §6.3 as
ruled today, it stays sealed until `fable` has run regardless.

---

## 8. Independent checks — named per claim, none of them mine

| claim | who checks it |
|---|---|
| the design, the bar, and the §4 admission that the pre-registered MDE rule was contrast-specific | **`strategist`** — including whether §5's depth-matched sensitivity is admissible at all or is post-hoc rescue |
| leakage, survivorship, the ECR pre-kickoff gate, and whether the §3.2 wins over B3/B4 are inflated by rookie rows carrying consensus information into v1 | **`fable`**, maximum effort |
| anything that ships | **`backend`** — nothing here is merged into `src/` and `projected_points` is unchanged |

**One thing I want attacked specifically.** In §3.2, rookie rows carry consensus information into v1
(they are pinned to the consensus slot) while B3 and B4 have no rookie information at all. Rookies are
10–18% of rows. **Part of v1's margin over B3/B4 is therefore borrowed from the crowd, not earned.**
I have not quantified how much. That is the weakest number in this document and it should be
attacked first.

## 9. A defect found and fixed mid-run, recorded because it nearly produced a fake null

The first execution returned an **entirely NaN expert-consensus panel** — all four positions,
`n = 0`, which would have read as "the design cannot answer the expert-crowd question." The cause was
`pd.DataFrame(columns=[...])` for the empty 2018–2020 ECR seasons: bare column lists get **object**
dtype, concatenating them promoted `season` to object, and every downstream merge then matched **zero
rows while looking healthy.** Fixed in `ecr_baseline.py` (typed empty frame) and guarded in
`ranking_v1.py` with an assertion that the join lands ≥ 10 rows for every season ECR covers.

**A silent zero-match join is indistinguishable from a null result.** Every merge in this campaign
that produces a headline number should carry that assertion.
