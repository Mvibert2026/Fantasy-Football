# Factor batch 1 — results

**Ranker, 2026-07-30.** Runs registry **#19** (TD-rate regression), **#20** (opportunity share),
**#28** (vacated targets and carries), **#13** (target-share stability YoY).

Design fixed in `docs/ranking/factor-batch-1-precommit.md`, committed **`d546cff` before any arm was
fitted**. 23 pre-registered tests, BH at q = 0.10 across all 23. Sealed 2025 holdout **not opened**;
no holdout spend requested.

Reproduce:

```
.venv/bin/python -m experiments.bottomup.factors.run_factors     # the 23 registered tests
.venv/bin/python -m experiments.bottomup.factors.diagnostics     # the post-hoc splits
```

---

## 1. Conclusion first

**Twenty-three tests, zero wins.** Nothing in this batch improves the ranking against consensus ADP
at any position, and nothing is recommended for the shipped model.

| grade | n | |
|---|---|---|
| NULL | 10 | |
| **HARMFUL** | 7 | six of them are the same arm at four positions — see (1) |
| PROJECTION-ONLY | 2 | improve a component, do not touch the ranking |
| SURVIVES *(by the committed rule)* | 2 | **and both are killed by a post-hoc diagnostic — see (3)** |
| MARGINAL / MARGINAL-HARMFUL | 2 | |

**Four findings worth keeping. Three of them are negative and one of them is about my own method.**

**(1) Registry #19's headline claim is wrong in its strong form, and this is the cleanest result in
the batch.** "TD-rate regression, best-known regression signal, HIGH edge" implies a player's own TD
rate is mostly noise. Arm **T2** tests that directly — discard the player's own TD rate entirely and
give everyone the pooled positional mean — and it is **worse at all four positions**, BH-significant
at three, and at q=0.05 at WR and QB.

| | T2 − primary, MAE of the position's TD component | as % of the primary's own error |
|---|---|---|
| WR `rec_tds` | **+0.0251** [+0.0133, +0.0377] | +1.6% |
| TE `rec_tds` | **+0.0180** [+0.0061, +0.0315] | +1.3% |
| RB `rush_tds` | **+0.0182** [+0.0052, +0.0307] | +1.0% |
| QB `pass_tds` | **+0.2295** [+0.1256, +0.3253] | **+4.0%** |

**A player's past TD rate carries real out-of-sample signal, and the model's existing empirical-Bayes
shrinkage is already extracting it.** The registry's "HIGH edge" reads as an unbuilt opportunity; it
is in fact a solved problem inside the current model, and the marginal return on doing more of it is
what the rest of §2 measures.

**(2) #28 is not closed. It is BLOCKED, and the reason is a named, already-commissioned data gap.**
`nfl.db` has **no pre-season roster table** — `depth_charts_weekly` begins at REG week 1,
`depth_charts_snapshots` is a single 2026-03-14 snapshot, there is no `rosters` table. So "who left
this team" had to run on a Week-1 depth-chart **PROXY**, declared as such in the pre-commitment
before it was run. The vacancy arm is harmful at RB and TE and null at WR — **and the harm is
concentrated in exactly the bucket where the proxy is known to be contaminated** (§4). This
experiment cannot separate "vacated opportunity is uninformative" from "our proxy for it is bad."
**Reported as blocked, not as a null.**

**(3) My own pre-registered grading rule passed two arms it should not have, and the diagnostic that
caught it is the most transferable thing here.** The rule graded on out-of-sample MAE across the
whole universe. Two arms cleared it on gains that live **entirely among players nobody drafts**:

| arm | pre-registered grade | full-universe gain | **on the ADP board** |
|---|---|---|---|
| **QB T1** volume-conditional TD prior | **SURVIVES** | −0.045 pass TDs MAE (−0.8%) | **+0.0045 — worse.** Whole gain is in the bottom tercile of projected attempts (−0.114) |
| **WR S1** stability-weighted share | PROJECTION-ONLY | −0.035 targets MAE | **−0.0065 of 31.4 — 0.02%** |

**The committed rule was not sensitive to where in the distribution a gain sits.** That is a defect
in the rule I wrote, found afterwards, reported rather than retro-fitted — the grades above stand as
recorded. Any future E1-style gate should require the gain to hold **on the decision-relevant
subset**, not merely on average. Thread opened to `strategist`.

**(4) Target share is worth something at WR and nothing at RB — the reverse of what the registry
says.** Registry #20 calls opportunity share "single best RB metric." Ablating the share term from
the model that already contains it:

| removing team-relative share | full universe | **ADP board only** |
|---|---|---|
| **WR** | +0.0796 targets MAE [+0.0132, +0.1547], p=0.061 | **+0.196 of 31.4 (+0.6%)** |
| TE | +0.0092 [−0.0284, +0.0449] **NULL** | — |
| **RB** | −0.0168 carries MAE [−0.0498, +0.0029] **NULL** | — |

At RB, deleting carry share entirely costs nothing measurable, and the share-based
reparameterisation (O1) is null too (−0.086 [−0.272, +0.068]). **Neither instrument can find the
"single best RB metric" doing anything at RB.**

---

## 2. The registered table — all 23

E1 = out-of-sample MAE of the **one** component declared per cell in advance, arm − primary, paired
by season, 11 seasons, season-block bootstrap 4,000 reps. **Negative = better.**
E2 = ADP-board Spearman, arm − primary, 7 seasons. **Positive = better.**

| # | pos | arm | E1 (component) | 95% CI | p | BH q=.10 | E2 | grade |
|---|---|---|---|---|---|---|---|---|
| 1 | WR | #19 T1 volume-conditional prior | −0.0126 `rec_tds` | [−0.0165, −0.0092] | 0.0001 | **Y** | −0.0022 | PROJECTION-ONLY |
| 2 | WR | #19 T2 full regression | +0.0251 | [+0.0133, +0.0377] | 0.0036 | **Y** | −0.0084 | **HARMFUL** |
| 3 | TE | #19 T1 volume-conditional prior | +0.0046 | [+0.0022, +0.0080] | 0.0170 | **Y** | −0.0010 | **HARMFUL** |
| 4 | TE | #19 T2 full regression | +0.0180 | [+0.0061, +0.0315] | 0.0257 | **Y** | +0.0149 | **HARMFUL** |
| 5 | RB | #19 T1 volume-conditional prior | −0.0062 `rush_tds` | [−0.0130, −0.0001] | 0.0987 | n | +0.0014 | MARGINAL |
| 6 | RB | #19 T2 full regression | +0.0182 | [+0.0052, +0.0307] | 0.0242 | **Y** | −0.0059 | **HARMFUL** |
| 7 | QB | #19 T1 volume-conditional prior | −0.0450 `pass_tds` | [−0.0773, −0.0138] | 0.0261 | **Y** | +0.0042 | SURVIVES † |
| 8 | QB | #19 T2 full regression | +0.2295 | [+0.1256, +0.3253] | 0.0020 | **Y** | +0.0019 | **HARMFUL** |
| 9 | WR | #20 O1 share × pace | +0.0491 `targets` | [−0.0098, +0.1230] | 0.209 | n | −0.0002 | NULL |
| 10 | WR | #20 O2 share ablation | +0.0796 | [+0.0132, +0.1547] | 0.061 | n | −0.0057 | MARGINAL-HARMFUL |
| 11 | TE | #20 O1 share × pace | −0.0360 | [−0.0625, −0.0097] | 0.0304 | **Y** | +0.0022 | SURVIVES † |
| 12 | TE | #20 O2 share ablation | +0.0092 | [−0.0284, +0.0449] | 0.660 | n | −0.0025 | NULL |
| 13 | RB | #20 O1 share × pace | −0.0863 `carries` | [−0.2724, +0.0683] | 0.376 | n | −0.0176 | NULL |
| 14 | RB | #20 O2 share ablation | −0.0168 | [−0.0498, +0.0029] | 0.308 | n | +0.0024 | NULL |
| 15 | WR | #28 V1 vacated share **(PROXY)** | +0.0818 `targets` | [−0.0075, +0.1795] | 0.126 | n | −0.0007 | NULL |
| 16 | WR | #28 V0c free control | +0.0553 | [−0.0091, +0.1276] | 0.170 | n | −0.0008 | NULL |
| 17 | TE | #28 V1 vacated share **(PROXY)** | +0.0448 | [+0.0106, +0.0773] | 0.0327 | **Y** | +0.0057 | **HARMFUL** |
| 18 | TE | #28 V0c free control | −0.0182 | [−0.0364, +0.0003] | 0.095 | n | −0.0057 | NULL |
| 19 | RB | #28 V1 vacated share **(PROXY)** | +0.2031 `carries` | [+0.1150, +0.2963] | 0.0020 | **Y** | −0.0010 | **HARMFUL** |
| 20 | RB | #28 V0c free control | −0.0955 | [−0.2237, +0.0206] | 0.179 | n | −0.0056 | NULL |
| 21 | WR | #13 S1 stability-weighted share | −0.0348 `targets` | [−0.0585, −0.0139] | 0.0160 | **Y** | −0.0017 | PROJECTION-ONLY |
| 22 | TE | #13 S1 stability-weighted share | −0.0447 | [−0.0976, +0.0058] | 0.137 | n | +0.0015 | NULL |
| 23 | RB | #13 S1 stability-weighted share | +0.0434 | [−0.0117, +0.1088] | 0.219 | n | −0.0004 | NULL |

**† Read the † rows with §1(3).** Both cleared the committed rule; both are undone by the post-hoc
volume split. Neither is an edge and neither is recommended.

**At BH q = 0.05 only four survive: #1, #2, #8, #19** — one PROJECTION-ONLY and three HARMFUL.
**Not one arm in this batch is a win at the stricter threshold.**

**Full-universe rank correlation (secondary, 11 seasons):** every arm sits between −0.0032 and
+0.0007. The largest movement in either direction is smaller than the width of its own interval at
15 of 23 cells. **No arm changes the ranking anywhere, on any universe.**

---

## 3. Factor #13, the descriptive half — usage share is about as persistent as role

Requested in comparable terms to the archetype persistence already measured. Consecutive-season
pairs, 2009–2024, minimum volume applied to the first season of each pair.

| | pairs | seasons | Pearson r | 95% CI | Spearman |
|---|---|---|---|---|---|
| **WR** target share | 1,824 | 15 | **+0.652** | [+0.624, +0.680] | +0.629 |
| **TE** target share | 858 | 15 | **+0.632** | [+0.584, +0.675] | +0.606 |
| **RB** target share | 1,083 | 15 | **+0.548** | [+0.496, +0.597] | +0.518 |
| **RB** carry share | 1,155 | 15 | **+0.575** | [+0.532, +0.620] | +0.564 |

Against the existing scale: **snap share +0.707, mean PPG ≈ +0.72, yards per carry +0.175, player
volatility ≈ +0.10.**

**Usage share sits with the role variables, not the skill variables — and slightly below snap
share.** So the registry's rationale for #13 ("separates real role from one-year noise") is
directionally right about *what kind of quantity it is* and gives no reason to expect it to add
anything on top of the role features already in the model. It does not: S1 buys 0.02% of the
model's own error on the ADP board at WR, and nothing at TE or RB.

---

## 4. Where the #28 harm lives — and why this is a data problem, not an answer

Post-hoc splits (`diagnostics.py`). **Post-hoc, lower evidential standard.**

| RB `carries` MAE | n | primary | V1 | Δ |
|---|---|---|---|---|
| club unchanged (per proxy) | 1,269 | 48.62 | 48.91 | **+0.29** |
| **club changed** | 172 | 56.72 | 56.27 | **−0.46** |
| low measured vacancy | 476 | 49.42 | 49.39 | −0.03 |
| mid | 475 | 42.16 | 42.02 | −0.14 |
| **high measured vacancy** | 475 | 56.57 | 57.34 | **+0.77** |

WR `targets` shows the same shape: movers **−0.15**, high-vacancy bucket **+0.30**.

**The harm is entirely in the high-measured-vacancy bucket, which is precisely the bucket the
proxy's known leak inflates.** A player on IR or injured in Week 1 drops off the depth chart and is
counted as departed, so his club's measured vacancy is too high and the model raises his teammates'
projections for opportunity that never opened. That is a mechanism, not a story: it predicts harm
concentrated at high vacancy, and that is what the split shows.

**And the split generates a hypothesis worth its own test, which I am not running here:** the flag
"this player changed clubs" is *helpful* at both positions (−0.46 RB, −0.15 WR) while the vacancy
*magnitude* is harmful. **"He moved" may be worth more than "how much opened."** Both depend on the
same missing ingestion. Logged to `docs/ideas-inbox.md`, untested, not a finding.

---

## 5. Guardrails applied (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§1) | `SeasonPanel.before()` gate; separate `outcomes()` accessor; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target. **All 27 runs × 11 seasons passed.** |
| **The proxy, isolated** | The Week-1 depth-chart read has its own accessor and its own audit tag. **Every arm except the three V1 arms asserts `n_preseason_proxy_reads == 0` and the assertion is live** — a `RuntimeError`, not a comment. Measured: 0 for all 20 non-V1 arms and all 4 primaries; 88 for each V1 arm. |
| **Survivorship** (§2) | Universe frozen pre-season; busts retained at 0. 2,271 WR / 1,441 RB / 1,041 TE / 869 QB player-seasons, including the 15–30% per season who play no games. |
| **Multiple comparisons** (§3.2) | BH across all m = 23, q = 0.10 and q = 0.05. Denominator is 23 regardless of outcome. |
| **Holdout** (§3.1) | 2025 sealed at the SQL gate. **Not opened.** `holdout_access_log.jsonl` unchanged. |
| **Effect size, not just significance** (§3.5) | Every E1 reported as a % of the primary's own error, and every candidate re-checked on the ADP board. This is what killed the two SURVIVES. |
| **Autocorrelation** (§3) | Seasons are the bootstrap resampling unit and the t-test's n, never player-seasons. |
| **Pre-registration** (§3.4) | `factor-batch-1-precommit.md`, committed `d546cff`, before the first fit. |
| **Baseline rule** (`CLAUDE.md` §6.5) | E2 is arm − primary against a primary that already loses to consensus at every position. **No arm closes any part of that gap.** |
| **Reproduction** | The primary is bit-identical under the old and new feature builders — 30–34 metric columns, all four positions. Pass 1 still reproduces. |

**Power, stated in advance and confirmed:** E2 has 7 seasons and cannot resolve anything at WR, QB
or TE. That was written into the pre-commitment before it was run, so it is a design limit rather
than a discovered excuse.

---

## 6. What I am not claiming

- **Not claiming any factor here should be added to the model.** None should.
- **Not claiming #28 is dead.** It is blocked on `load_rosters_weekly()`. The measurement is
  confounded and says so.
- **Not claiming TD rate is unimportant.** The opposite: T2 shows it matters at every position. What
  is claimed is that the *existing* shrinkage already captures it and further conditioning does not
  pay where drafts happen.
- **Not claiming the two SURVIVES rows are edges.** They are the pre-registered grades and they are
  both undone in §1(3). Quoting either without that paragraph would be a misuse of this document.
- **Not claiming the #13 persistence numbers license a factor.** They are descriptive.
