---
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: whether anything from FR-085/FR-086 is registered; whether CLAUDE.md §7's ceiling claim stands
OPENED: 2026-07-30
---

## Ask

Three decisions. Two are "should this be registered", one is a change to `CLAUDE.md` and therefore
explicitly not mine.

Reports: `docs/ranking/fr085-zero-rb.md`, `docs/ranking/fr086-volatility.md`.
Pre-commitment (written and committed **before** the simulation ran, `a9e3b2b`):
`docs/ranking/fr085-strategy-sim-precommit.md`.
Code: `experiments/strategy/`, `experiments/volatility/`. Raw output under `data/qa/fr08*.json`.

**695 interval tests across the two reports** (347 FR-085, 348 FR-086). At 5% that is ~35 false
"clears zero" results expected by chance. Every result is graded SURVIVES / MARGINAL / NULL on
pass-1 §0's scale. The sealed 2025 holdout was never opened — it is excluded in code
(`season_vbd()` and `load_player_seasons()` raise at ≥2025), not by convention.

---

### (1) I recommend NOT registering Zero RB. Please confirm or overrule.

The draft simulation returns a null with intervals tight enough that I do not think a holdout
season would tell us anything we do not already know.

FFC, 7 seasons, 300 sims per cell, primary σ (per-player measured FFC `std_dev`), paired by season,
resampling seasons:

| Zero RB vs VBD | margin | 95% CI | grade |
|---|---|---|---|
| realistic season points | +0.9 | [−19.8, +21.1] | NULL |
| best-ball season points | +11.0 | [−12.7, +35.7] | NULL |
| P(make playoffs) | +0.000 | [−0.042, +0.041] | NULL |
| P(win title) | +0.001 | [−0.020, +0.023] | NULL |

ECR, 4 seasons: +3.1 realistic points [−13.0, +19.3] NULL; P(playoff) +0.033 [−0.028, +0.093] NULL.
Ban-length sweep (3/4/5/6 rounds, all declared in advance, none selected on): nothing moves.

Power ceiling stated in the output, not a footnote: minimum attainable two-sided sign-test p is
**0.0156** at n=7 and **0.125** at n=4 — no ECR result can reach conventional significance at the
season level regardless of effect size.

**What I want from you:** a ruling that this is closed, or a specific registrable form if you
disagree. I do not think spending 2025 on it is defensible.

### (1b) Related, and it is the only cell in the residual work that moved over time.

The founder separately recalls the RB dead zone "used to be a thing but now is not." **That finding
is not in this repo** — `docs/test-registry.md:210` test 43 has never been run — and the direct
early-era vs late-era contrast (2018–20 vs 2022–24) does not support it: **RB13–24 is NULL and points
the wrong way (−13.4 [−45.7, +21.6]), RB25–36 is NULL (+7.5).**

What *did* move is the far end: **RB37+ improved by +48.3 [+21.6, +75.1] SURVIVES against the WR band
drafted alongside it** (mean overall pick 123.0 vs 119.9, so well controlled). That is one SURVIVES
among 151 tests in that module and I am reporting it as a hypothesis. Flagging it here because it is
close enough to the founder's recollection to be mistaken for it, and the correct statement —
"late-round RB got better relative to late-round WR" — implies different draft behaviour from "the
dead zone went away." If you think that one is registrable I would take the form from you.

### (2) The one candidate I think might be worth registering: RB25–36 relative pricing.

`fr085-zero-rb.md` §3. With draft cost held roughly constant by comparing each RB band against the
matching WR band:

| comparison | margin (VBD pts) | 95% CI | grade | mean overall pick RB vs WR |
|---|---|---|---|---|
| RB1–6 − WR1–6 | −58.2 | [−80.2, −33.9] | SURVIVES | **4.6 vs 11.1 — poorly matched** |
| RB13–24 − WR13–24 | −16.9 | [−47.5, +18.1] | NULL | 39.9 vs 43.7 |
| **RB25–36 − WR25–36** | **−26.0** | [−39.1, −12.5] | **SURVIVES** | 76.8 vs 73.5 — well matched |

The last row is the only cell that is both significant and well controlled for curve position.
Note it is **not** the classic dead zone (RB13–24 is NULL) and **not** what backend's report
emphasised (rounds 1–3).

**Two reasons I am not registering it myself.** It is one of 141 interval tests in that module. And
per-season trend is NULL in every band with intervals of ±8 to ±25 VBD points per year — so the
design cannot tell whether this is a stable structural feature or a 2018–2024 artifact. If you
think it is registrable, I would want the form written by you.

### (3) `CLAUDE.md` §7's ceiling claim — a change to the standing spec, so yours not mine.

§7 says the yardage bonuses "reward ceiling outcomes over floor, which should influence how variance
is valued in rankings." The first clause is a fact about the rulebook. **The second is now measured
at zero through FOUR independent instruments, at increasing resolution:**

| instrument | question | result |
|---|---|---|
| PR-002 (`src/spike_persistence.py`) | is "spike-week player" a persistent *category*? | 0 of 36 correlations survived BH |
| component-model pass-1 §6.1 | does the *residual clearance rate* persist? | excess ≈ 0 at WR rec, RB rush, TE rec |
| **FR-086 §3.3** | does a player's own measured **dispersion** (2nd moment) improve the exceedance curve beyond his mean? | **NULL at every threshold, every family, every shrinkage; two of eleven point the wrong way** |
| **FR-086 §3.4 — the founder's actual question** | do **skewness and excess kurtosis** (3rd/4th moments)? | **NULL everywhere, plus an ORACLE BOUND** |

**Note the correction on the fourth row, because it matters for how much weight this carries.** The
founder's *"the curve has a shape with tails"* was relayed to me as dispersion; I tested the second
moment. He then clarified: **"for curve I was talking about skewness and kurtosis."** That is a
genuinely different covariate — two players can share a mean *and* an SD while one is symmetric and
the other has a long right tail, and a threshold bonus is paid on that tail. So §3.4 was run as a
separate test with separate arms (skew alone, kurtosis alone, both), not as a re-run.

**§3.4 is the strongest of the four and I would like the reasoning checked.**

- **Upstream, before any model is fitted:** a player's shape residual in season N−1 does not predict
  his shape residual in season N. Six of six NULL — rec skew +0.014, rec kurt −0.004, rush skew
  +0.049, rush kurt −0.031, pass skew +0.071, pass kurt −0.000. The *second* moment persists at
  r ≈ 0.08–0.11 (SURVIVES at RB/WR); the third and fourth persist **less** than that.
- **The empirical-Bayes shrinkage says it independently.** With τ² estimated from the data and no
  hand-picked constant, τ̂² for skewness is **exactly zero in two of five (family, position) cells**
  under G1/G2 and in **all five** under g1/g2 — the covariate becomes identically zero and the arm
  collapses onto base. The estimator, given every chance, concludes there is no between-player
  variance in true shape beyond sampling noise.
- **Downstream: NULL at every threshold in every family**, including at 200 rushing/receiving and
  400 passing where the effect was predicted to show first. Stable across the whole k ∈ {0, 8, 16,
  32} sweep and both estimator conventions.
- **The oracle bound is what makes it a closure rather than a shrug.** Given the *target season's
  own* shape — impossible foresight — log-loss improves by at most 0.0024 per game-trial and
  **bonus-point MAE gets worse at every family** (+0.023 rec, +0.020 rush, +0.087 pass).

**One thing that strengthens the null and that I want you to check.** The sampling variances `v_i`
are normal-theory, and per-game yardage is emphatically not normal — for heavy-tailed data the true
sampling variance of G1/G2 is *larger* than the normal-theory value. So `τ̂² = Var(resid) − mean(v_i)`
is over-estimated, weights are too high, and I am **under**-shrinking, which biases *toward* finding
an effect. It still finds none. Is that reasoning right?

**And one thing I flagged rather than reported, in both tests.** The fitted coefficients (dispersion
+0.135 in the passing family; skew +4.64 at rec ≥200) carry intervals that look like strong
SURVIVES. **I believe those intervals are invalid** — they bootstrap across walk-forward target
seasons whose training sets overlap almost completely, so effective n ≈ 1, not 20. The valid
instruments are the out-of-sample metrics, which are NULL. **If I am wrong about the interval being
invalid, that changes the conclusion**, so please check it rather than take my word.

**The decision I want:** should §7's second clause be amended to say the ceiling premium is real,
measured at under one point per season (FR-086 §4: high-volatility WRs earn +0.94 bonus points a
season more than low-volatility WRs at the same scoring level, SURVIVES), and **not exploitable
beyond what a mean-based projection already captures — not via variance, not via skew, not via
kurtosis, and bounded by oracle**? That is a `CLAUDE.md` edit and the operating rules say I escalate
rather than make it.

---

## What I will do with the answer

- (1) closed → I stop work on draft-strategy comparison entirely and say so in `docs/ideas-inbox.md`.
- (2) registrable → you write the form, I run it once, against the holdout if you say so.
- (3) → if you rule the §7 amendment is warranted, PM routes the edit; I do not touch `CLAUDE.md`.

## One methodology point I would like checked whether or not you rule on the above

`fr085-strategy-sim-precommit.md` §5 was amended after a 5-simulation smoke test and **before any
strategy comparison was computed**: unconstrained "always take the highest VBD" drafts 9 WR and 3 QB,
because WR value-over-replacement stays positive to WR40 while RB's crosses zero at RB30. I replaced
it with the project's existing positional-need penalty (`src/draft_sim.py`'s `NEED_TARGETS` /
`NEED_PENALTY_PER_SURPLUS`, in rank units, applied identically to user and to the nine opponents)
rather than inventing a constant. The amendment is recorded in the code comment at
`experiments/strategy/sim.py:need_penalty_vector` and in the pre-commitment itself.

**Is that an acceptable amendment, or does changing a pre-registered strategy definition after
seeing any output — even output that contains no outcome comparison — invalidate the pre-commitment?**
I believe it does not, because nothing about relative strategy performance had been computed. I would
rather have that checked than assumed.
