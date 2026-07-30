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

**559 interval tests across the two reports** (337 FR-085, 222 FR-086). At 5% that is ~28 false
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
at zero through three independent instruments:**

| instrument | result |
|---|---|
| PR-002 — is "spike-week player" a persistent category? | 0 of 36 correlations survived BH |
| pass-1 §6.1 — does residual clearance rate persist? | excess ≈ 0 at WR rec, RB rush, TE rec |
| **NEW: FR-086 §3 — does a player's own measured yardage dispersion improve the exceedance curve beyond his mean?** | **NULL at every threshold in every family at every shrinkage; two of eleven results point the wrong way** |

The third is the founder's own suggested mechanism (*"the curve has a shape with tails that should
naturally figure this out for you"*) and it is the lowest-noise of the three: it uses the full
game-level yardage distribution rather than a count of threshold crossings. Walk-forward, prior-season
dispersion only, and — this is the part that makes it decisive — **both arms are given the player's
realised mean ypg**, which is the most favourable setting that exists. In production the mean is a
projection and noisier. If it does not help here it cannot help in the pipeline.

Expected-bonus-points MAE, walk-forward, per player-season: rec 0.8072 → 0.8093 (+0.0021, NULL);
rush 0.9679 → 0.9719 (+0.0040, NULL); pass 1.7694 → 1.7669 (−0.0025, NULL).

**Flagging one thing rather than reporting it:** the fitted dispersion coefficient in the passing
family is +0.135 [+0.108, +0.162], which looks like a strong SURVIVES. **That interval is invalid.**
It bootstraps across walk-forward target seasons whose training sets overlap almost completely, so
effective n ≈ 1, not 20. I am not standing behind it and the report says so. Please check that
reasoning — if I am wrong about the interval being invalid, that changes the conclusion.

**The decision I want:** should §7's second clause be amended to say the ceiling premium is real,
measured at under one point per season (FR-086 §4: high-volatility WRs earn +0.94 bonus points a
season more than low-volatility WRs at the same scoring level, SURVIVES), and **not exploitable
beyond what a mean-based projection already captures**? That is a `CLAUDE.md` edit and the operating
rules say I escalate rather than make it.

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
