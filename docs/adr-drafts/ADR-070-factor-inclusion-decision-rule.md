# ADR-070 — the factor inclusion decision rule for ranking v2

**Author:** `strategist`, 2026-08-01.
**Status:** Accepted as **ADR-070**, 2026-08-01. Number allocated via `tools/handoffs.py adr next`.
**Lands in:** `docs/decisions.md` as ADR-070.
**Supersedes, for the per-season rank-correlation endpoint only:** the WIN/HARM rule registered in
`docs/ranking/factor-campaign-manifest/batch-B1.md` and `batch-C1.md` ("paired season-block
bootstrap, 4,000 reps, 95% CI; WIN = CI > 0").
**Trigger:** batch C1's registered placebo — a column of seeded noise — returned a BH-robust WIN at
TE (+0.0303, p = 0.0002) and the registered rule graded it `INCLUDE`. Replication across 34
independent noise draws measured the harness's false-positive rate at **9.6% of cells against a
nominal 2.5%**. Thread `2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi`.

**Reading order if you are implementing this:** §4 is the rule. §5 is what it costs. §6 is how the
next batch proves it works. Everything before §4 is why.

---

## 1. What is actually broken

Ranker named two mechanisms. Both are real. **There is a third, and it points the opposite way, and
it is the more expensive one for this project.**

### 1.1 Confirmed — the percentile bootstrap is degenerate at S = 7 with a discrete statistic

Spearman on a graded population of 10–19 players moves in quanta of `12/(n³ − n)` — 4.4 × 10⁻³ at
n = 14, 9.6 × 10⁻⁵ at n = 50. A perturbation too small to flip any adjacent pair produces an **exact
zero**, and at QB a mean of 3.75 of 7 seasons do exactly that. Resampling a 7-vector whose non-zero
entries all share a sign puts the bootstrap mean above zero on all but `(n_zero/7)⁷` of resamples —
1.4 × 10⁻⁴ at QB. The 2.5th percentile is then positive **by construction, at any effect size**.
This is not the bootstrap failing to converge; it is the percentile bootstrap being used as if it
inverted a test of `H₀: μ = 0`, which it does not.

### 1.2 Confirmed — the null is not centred at zero

Mean placebo Δ̄: QB +0.0030, RB +0.0006, WR −0.0004, TE +0.0062 against per-season graded
populations of 19, 43, 50, 14. The ordering tracks `1/n`. A factor must therefore clear a *positive*
bar, and the bar is position-specific.

**The mechanism has not been established, only named** ("a noise column damps an ill-conditioned
small-sample fit"). That matters, because the size of the bias should scale with the **number of
columns added**, and the placebo adds **one** while F3 and F5 add **three**. §7 M-2 turns this into
a measurement instead of an explanation.

### 1.3 New, and not in ranker's diagnosis — the same defect *destroys power* on mixed-sign vectors

Ranker's argument for C1's NULLs is that miscalibration inflates false positives, so it cannot have
manufactured an inclusion. **True for what it covers, and it does not cover the other half.** The
same discreteness that manufactures a false WIN on a sign-degenerate vector makes the interval
absurdly *wide* when two or three non-zero seasons disagree, because the resampling distribution is
then dominated by which of those few seasons get drawn. In that regime the test is **conservative**
and a real effect is invisible.

C1 shows this directly. At RB the placebo's Δ̄ has sd ≈ 0.003 across 34 draws; F3's RB cell was
handed a bootstrap CI of [−0.0003, +0.0404], **half-width ≈ 0.020, roughly seven times** that. At QB
the placebo sd ≈ 0.005 and F6's CI half-width is ≈ 0.041, **roughly eight times**. Those two
quantities measure different things (§4.2) and are not required to match — but a decision instrument
whose interval is an order of magnitude wider than the observed spread of the statistic under a null
intervention has no usable power, and its NULLs are not measurements of absence.

**Consequence, and it reframes the whole ruling.** The campaign's realised type-I exposure is
**nil**: across ~130 registered tests it has made **zero inclusions**, so there are no discoveries
whose validity is in question. Its live exposure is **type II** — roughly ninety factors written off
and two model arms (G1, G1a) rejected, on an instrument of unmeasured and position-varying power.
The replacement rule must therefore be judged on *both* error rates, and "tighten it until nothing
gets through" is not a fix.

---

## 2. What was considered and rejected

| Candidate | Rejected because |
|---|---|
| Keep the bootstrap, widen to 99% | Does not touch either mechanism. The CI excludes zero by construction at *any* confidence level when the sign is degenerate. |
| **Plain** sign test / Wilcoxon on the 7 season deltas, as the *primary* test | Immune to §1.1, and rejected in that role for two reasons: it is **not** immune to §1.2 — the null sign probability is ≈ 0.77 at QB, not 0.5, so its stated p is wrong in the anticonservative direction — and its p-floor of 2⁻⁷ = 0.0078 cannot clear a BH threshold of q/M ≈ 7.7 × 10⁻⁴. **But the underlying idea is right and is adopted in calibrated form — see §4.4a.** |
| Fit a Gaussian (or GPD) tail to the placebo draws and read p off it | This is the **same error in new clothes.** The bootstrap failed because it extrapolated smoothness it had not earned; extrapolating a Gaussian tail from 34 draws out to p = 7.7 × 10⁻⁴ earns it no better. Note what it would have done: a normal-tail fit to the published placebo moments puts F3-RB and F6-QB *over* the BH bar and the placebo *under* it — a rule that flatters exactly the two arms in question, on an assumption nothing validates. Refused. |
| Change the endpoint to something continuous | Fixes §1.1 at the source, but changes the ADR-069 steering metric mid-campaign and makes B1/C1 non-comparable. **Kept as a required secondary diagnostic** (§4.6), not as the decision endpoint. |
| Shrink the campaign denominator M — e.g. "batches 1–7 tested a consensus-derived primary and are not evidence about v2" | The argument is coherent and it is also the textbook error: shrinking a denominator after seeing which arms nearly won. C1 re-tested factors that batches 3/5/7 had already tested; that is a second shot at the same goal and it counts. **M stays cumulative** (§4.5). |

---

## 3. The estimand stays the same

Δ̄ = mean over target seasons of `ρ(v2 proj_points order, realised points)_arm − (…)_ctrl`, Spearman
within (position, season), M-panel veterans, arm differenced against its matched control window.
**Unchanged from B1 and C1**, deliberately: every graded cell already on disk carries its per-season
deltas, so everything below re-grades from `factor_c1_contrasts.csv` / `factor_c1_cells.csv` with no
model refits. Changing the estimand after seeing which arms nearly won would be tuning.

What changes is **how its uncertainty is established**.

---

## 4. THE RULE

### 4.1 Null construction — a matched null ensemble, per cell

For every graded cell (arm × position), build an ensemble of Δ̄ values under an intervention that
provably carries no player-level information but is **matched to the arm in every other respect**.

**Primary construction — joint within-season permutation of the arm's own column block.** For draw
`k`, permute the *rows* of `FACTOR_COLS[arm]` jointly (one permutation vector, all columns of the
block) within each feature frame, in every season the walk-forward builds, training and target
alike. Seed `= sha256(f"{arm}|{position}|{season}|{k}")` — never builtin `hash()`
(guardrails §11.1); the season, not the call, keys the permutation so a season's null column is a
fixed property of that draw.

This matches, automatically and without a tuning knob: the number of added columns, each column's
marginal distribution, the within-block correlation, and the `*_known` indicator's coverage rate.
The one-column Gaussian placebo matches none of those for a three-column arm.

**Known limitation, stated rather than buried.** Permutation destroys the block's correlation with
the existing design, so this is a null of *exchangeability*, not the conditional null "adds nothing
beyond X". The expected direction of the error is **conservative**: a real column collinear with the
existing design carries more variance inflation than a permuted one, so the permuted reference sits
*above* the true conditional null and the threshold is if anything too high. That is an argument,
not a measurement — §7 M-2 measures it.

**Secondary construction — dimension-matched Gaussian placebo.** `d` seeded N(0,1) columns, `d` =
`len(FACTOR_COLS[arm])`. Cheaper and shareable across arms with the same `d` at the same
(position, control). Admissible as the null **only** for arms where §6.2's agreement check passes.
`d = 1` reproduces C1's F0 byte-for-byte.

**Arms that add no column are not covered by either construction.** F6 changes a constant. Neither a
permutation nor a placebo column is a null for it; §7 M-6 and the separate F6 pre-registration
handle it. **Any statement that F6 "clears the placebo null" is withdrawn** — it was never the right
null for that arm.

### 4.2 What the null does and does not certify

The ensemble holds the seasons fixed and randomises the intervention. Clearing it certifies **"this
is not an artifact of perturbing the fit"**. It does *not* certify that the improvement generalises
to a season not in the sample — that is season-level uncertainty, S = 7, and no test can conjure it.
§4.4a's consistency condition is the cheapest available proxy; the real answer is more target seasons
(§7 M-4) and the §6.5 release gate. **An `INCLUDE` under this rule means "earns a place in the
design matrix", not "has demonstrated out-of-sample edge."** Nothing may be reported as the latter.

### 4.3 p-value — sequential Monte Carlo, no parametric tail

One-sided counts from the ensemble in the observed direction; two-sided `p = min(1, 2 × p_one)`,
direction recorded. One p per cell, so `m_b` still counts cells and the denominator's construction
is unchanged.

Use the **Besag–Clifford sequential Monte Carlo test** (1991), which is exactly valid and makes this
affordable: draw until either `h = 20` null draws have reached or exceeded Δ̄_obs, or `L` draws are
exhausted.

```
if h exceedances reached at draw n:   p_one = h / n
else (l < h exceedances in L draws):  p_one = (l + 1) / (L + 1)
```

**Hard floor, and it is the point of the whole design: no p may be reported below `2/(L+1)`. No
Gaussian, GPD, kernel or any other tail extrapolation is admissible.** Resolution is bought with
draws. Set

```
L  =  ceil(2 * M_campaign / q)  - 1        # M = 130 today, q = 0.10  ->  L = 2,599
```

and in practice **L = 3,000**, which covers the denominator growing to M = 150.

Why this is cheap: a cell with a true p near 0.5 stops after ~40 draws; integrating over a uniform
null gives ≈ `h·(1 + ln(L/h))` ≈ **120 draws for a typical null cell**. Only a genuinely extreme
cell runs to L.

### 4.4 Verdicts — fixed now, before the next batch runs

| verdict | rule | authorises |
|---|---|---|
| **INCLUDE** | BH-robust at campaign M, q = 0.10, direction = WIN; **and** CONSISTENT (§4.4a); **and** not VOID; **and** coverage ≥ 0.80 | the factor's columns enter v2 at that position |
| **RE-SPECIFY** | BH-robust, direction = HARM, **and** CONSISTENT | **the factor is not dead.** One registered re-specification attempt (§4.4b) |
| **EXCLUDE (variance)** | BH-robust, direction = HARM, **and not** CONSISTENT | dead for v2 at that position: it costs parameters and buys nothing |
| **FRAGILE** | BH-robust in either direction but fails CONSISTENT *and* the harm/win is carried by one or two seasons | nothing. Reported with the per-season vector so the reader sees why |
| **HYPOTHESIS** | `p ≤ 0.05` but not BH-robust | **nothing.** A ledger row, a named live hypothesis, and no more |
| **NULL (calibrated)** | `p > 0.05`, ensemble ran to its stopping rule | measured no effect **at a stated power** — the null band `[q2.5, q97.5]` must be quoted with it |
| **NO DATA** | coverage < 0.80, or no ensemble | nothing |
| **UNCALIBRATED** | graded on the retired bootstrap and not re-graded | **nothing, in either direction.** Not citable as evidence of absence or of presence |

**VOID rule retained**, restated on the calibrated p: a treatment WIN is VOID where the paired
`*k` coverage-indicator control at the same position has `p_win ≤ 0.05` — the loose bar for voiding,
the BH bar for claiming, exactly as Amendment 1 registered it and for the same reason (batch 7
measured a coverage flag at 215% of the treatment it was controlling).

### 4.4a CONSISTENCY — the sign criterion, calibrated

**Added 2026-08-01 in response to the founder, verbatim: *"Yes a rule pointing the other way is a
signal. Probably just needs to be included differently. Any consistent signal is usable."*** He is
right, and the statistical reason he is right is worth stating: **a column carrying no information
cannot consistently degrade ordering.** Under the null the sign of Δ_s is near-symmetric about the
small positive bias of §1.2; a run of same-signed seasons is not something noise produces. Direction
consistency is therefore genuine, separable evidence — and it is exactly the property the degenerate
bootstrap was accidentally rewarding (§1.1), which is why it must now be measured honestly instead
of arriving as a side effect.

**Statistic.** With the derived per-season tolerance of §4.7, let `W⁺ = #{s : Δ_s > tol_s}`,
`W⁻ = #{s : Δ_s < −tol_s}`, and the directional consistency `C = W⁺ − W⁻` for a WIN claim,
`W⁻ − W⁺` for a HARM claim. Integers, computable by hand from seven numbers, no resampling anywhere
in the definition.

**Calibration.** `C` is computed for the cell **and for every draw in the same null ensemble**. A
cell is **CONSISTENT** iff its `C` exceeds the ensemble's 95th percentile of `C`. This costs no
extra draws and it fixes the objection that sank the plain sign test: the ensemble's own `C`
distribution embeds the measured null sign probability (≈ 0.77 at QB, not 0.5) and the exact-zero
mass, so no `π₀ = 0.5` assumption is made anywhere. It requires only that the ensemble store
per-season deltas rather than summary counts — §7 M-1.

**Role: a required condition, not a second discovery route.** `C` never grants a verdict on its own.
Adding it as an alternative route would be a second test statistic on the same data and would need
its own multiplicity slot; as a condition it can only *remove* rejections, so it costs no
multiplicity and cannot inflate the rates registered in §6.1.

**Also report, as a descriptive honesty line and explicitly not as a decision input:** `k of S
seasons in the claimed direction`, the exact binomial p at π = 0.5, and the ensemble's own measured
`π̂₀`. The gap between those last two is the single clearest picture of §1.2 anyone will get, and it
is hand-auditable — a property worth having in a rule replacing one that failed inside a resampler.

**A consequence I would rather state than have discovered later: this will probably make INCLUDE
unreachable at QB, and at S = 7 that is the correct answer, not a defect.** With a mean of 3.75 of 7
QB seasons contributing an exact zero, `C` cannot exceed ~3 and the ensemble's own q95 will sit
close to it. The evidence at that position genuinely cannot support an inclusion. The fix is §7 M-4
(more target seasons), not a weaker condition.

**Registered prediction, testable from M-1(B) alone and written before that data exists:** no
placebo draw in the 34 already run produced a *consistent* harm — i.e. the ensemble's `C`
distribution in the harm direction will be tightly concentrated near zero at every position, and
placebo HARM verdicts (2.9–5.9% per position under the old rule) will turn out to be single-season
artifacts. If that is wrong — if noise routinely produces `C ≥ 4` — then §4.4b's whole premise is
wrong and RE-SPECIFY must be withdrawn. That is the falsification condition and it is cheap.

### 4.4b RE-SPECIFY — what a consistent HARM buys, and what it does not

A BH-robust, CONSISTENT harm is evidence that **the column carries information the model is using
badly**, not that the column is empty. Four mechanisms produce it and they are distinguishable:

| | mechanism | the distinguishing evidence |
|---|---|---|
| (a) | coefficient fitted with the wrong sign under collinearity | fitted sign vs. the column's marginal sign against the outcome |
| (b) | the relationship is non-linear or conditional on role, and a flat linear term mis-specifies it | harm concentrates in an identifiable sub-population |
| (c) | the column is a time-varying proxy (batch 7's time-dummy geometry) | the paired `*_known` control carries it — already handled by the VOID rule |
| (d) | genuine variance inflation: no information, just an extra parameter | **inconsistent** sign across seasons — which is what separates EXCLUDE (variance) from RE-SPECIFY |

**What RE-SPECIFY authorises: exactly one pre-registered re-specification attempt, whose form is
chosen from a menu fixed before it is run, and whose arms enter the campaign denominator as new
tests.** The founder's "include it differently" is correct and it is one step from an unregistered
search; the menu is what keeps it one step away. Registered menu, fixed now:

1. the column entered with a **shrunk or sign-constrained** coefficient (ridge, or a registered sign
   restriction where theory fixes the sign — C1's own F3 luck-residual downside is this case);
2. an **interaction** with that position's primary volume feature;
3. **conditioning on role** — the column entered only within a pre-declared sub-population;
4. a registered **monotone transform** (log, rank, or a two-knot spline).

One menu item per factor per position. A second attempt requires a new registration with the first
attempt's result already published. **No item may be selected after seeing which one would work** —
the item is named in the registration, before the run, with the mechanism it is meant to fix.

**Live case: C1's F1 snap share, HARM at TE (−0.0285).** Currently `UNCALIBRATED`; on re-grade it is
the first candidate for this route. The structural observation that makes it a real candidate rather
than a story is *inside the model, not received wisdom*: the TE volume spec already contains
`tshare_w`, so the incremental content of snap share at TE is **snaps that produced no target**, and
entering that flat as a positive-ordering feature is a specific, checkable mis-specification. Menu
item 2 (interaction with `tshare_w`) or item 3 is the registered attempt. Per the standing
calibration prior I am pricing that narrative at half weight and predicting the re-specification
**fails**; it is registered anyway, because a consistent harm that nobody follows up is exactly the
signal the founder is pointing at.

### 4.5 Multiplicity — BH stays, on top, at the cumulative campaign denominator

Ranker asked whether stacking BH on a calibrated threshold double-counts. **It does not, and
dropping either leaves a hole.** They correct different things: the ensemble fixes the *per-test*
error rate, which was running ~4× nominal; BH bounds the *family* false-discovery rate across cells.
A calibrated test applied 150 times still yields ~7 nominal-α false positives.

- `M_campaign` stays **cumulative and is not shrunk**: 130 today, plus the next batch's `m_b`.
- q = 0.10, BH, ranked among the campaign's accumulated p-values — the existing convention.
- **BH, not Benjamini–Yekutieli.** Cells sharing an arm or a control are positively dependent; BH
  controls FDR under positive regression dependence, which is the plausible structure here. BY at
  M = 130 divides by Σ1/i ≈ 5.6 and would make discovery impossible at this power. **This is an
  assumption, logged as one**, and it is unchanged from the campaign's existing practice — this ADR
  is not the place to re-open it, but it is the place to write it down.

### 4.6 Reporting — what every graded cell must carry

1. Δ̄ and **the full per-season delta vector** (7 numbers). At S = 7 with a discrete statistic this
   is the single most honest uncertainty statement available and it costs nothing; the reader sees
   the degeneracy directly.
2. The ensemble's `n_draws, mean, sd, min, q05, q25, median, q75, q95, max` — **both tails.**
   C1 published the upper tail only, which leaves every HARM cell in B1 and C1 ungradeable against
   its own null.
3. `p`, `p_floor = 2/(L+1)`, the stopping reason (`h_reached` / `L_exhausted`), the seed, `h`, `L`.
4. `W⁺`, `W⁻`, `C`, the ensemble's q95 of `C`, the exact binomial p at π = 0.5, and the ensemble's
   measured `π̂₀` (§4.4a).
5. **A secondary continuous diagnostic**: the same delta computed on within-season *Pearson*
   correlation between `proj_points` and realised points. Continuous in the predictions, so it
   cannot produce exact zeros. It is **not** a decision endpoint and no verdict may be read off it —
   it exists so the project can see how much of the noise is the rank statistic's discreteness.
6. The season-block bootstrap CI **may still be printed**, relabelled `descriptive_spread`, with a
   standing note that it is not a decision instrument for this endpoint. It must never again appear
   as `lo`/`hi` next to a verdict.

Guardrails §7 requires a CI on every metric and specifies season-level resampling. **That
requirement is narrowed here for this endpoint only**: at S = 7 with a discrete per-season
statistic, the season percentile bootstrap has been measured to be anticonservative in one regime
and to have no power in the other, and items 1–4 above are its replacement. Guardrails §7 is
untouched for continuous endpoints on large populations (component MAE and similar), where nothing
in this ADR applies.

### 4.7 Numerical hygiene — the 1e-9 snap is accepted, with a correction

Ranker's `|Δ| < 1e-9 → 0` snap in `boot_diff` was **theirs to make and it stands**: it can only
remove a WIN, it changes no estimand, and it caught a BH-robust win on a mean delta of
3.97 × 10⁻¹⁷. Two corrections:

- **The tolerance should be derived, not chosen.** Spearman's smallest attainable non-zero change on
  `n` players is `12/(n³ − n)`. Snap per season, per cell: `|Δ_s| < 6/(n_s³ − n_s) → 0`. That is
  half the quantum — anything below it is definitionally arithmetic, and at n = 50 it is 4.8 × 10⁻⁵,
  eleven orders of magnitude above float64 noise on numbers of order 0.5. A single global 1e-9
  leaves a band between 1e-9 and the quantum where representation noise still survives.
- **Fix the cause too.** Arm and control rhos taking different code paths for an identical design is
  a defect in its own right. Add a test asserting that an arm whose added block is a constant column
  reproduces the control's per-season rhos **exactly**.

---

### 4.8 Universe and span provenance — added 2026-08-01 with the tier ruling

The C1 defect was an estimator failure. This clause pre-empts the *other* way this endpoint produces
two numbers for one quantity: computing them on different populations or different spans and putting
them in the same column.

**Every ρ and every Δρ, in every CSV and every published table, carries a four-part provenance key:**

```
universe   ∈ {m_panel_halfppr12, m_panel_ppr12, m_panel_nonppr12, full_veteran_roster}
targets    = "YYYY-YYYY"      S = <int>      first_feature_season = <int>
```

plus **`S_pos` per position** wherever a position's usable span differs from the headline.

1. **No cross-universe or cross-span delta may ever be computed.** An arm differences only against a
   control carrying an *identical* key — the existing CTRL-A/B/C matched-control discipline extended
   to two more dimensions.
2. **Two ρ values with different `universe` tags may not share a column.** Separate tables, or the
   tag in the header.
3. **A number without the key is `UNLABELLED` and is not citable**, the same standing as
   `UNCALIBRATED` in §4.4.
4. **Enforced structurally: the grading code raises when asked to join cells whose keys differ.**
   `CLAUDE.md` §6.1 requires a layer that refuses; a warning is not one.
5. **Backfill, do not restate.** Every published B1/C1 number is
   `m_panel_halfppr12 / 2018-2024 / S=7 / ff=2012`. Add the key; do not re-derive the numbers.

**`S` is a per-position property and is published as one.** Any document stating a span states it
per position and, for any position whose span is shorter, names the binding source. **The bare claim
"21 seasons" is forbidden project-wide unless all four positions have 21.** Today they do not: the
2003–2008 targets hole makes the deepest tier a QB/RB extension, and the WR/TE decline measured at
deep spans (`docs/ranking/season-span-M4.md` §3.1, WR −0.0338 at span 2002) is **that data defect,
not a regime finding**, and may not be reported as evidence that older seasons mislead.

**The grading panel.** Ruled 2026-08-01, thread
`2026-08-01-three-rulings-needed-the-endpoint-is-the-bottlen`: **tier 2 — `m_panel_ppr12`, targets
2013–2024, S = 12 at all four positions** — is the grading panel from the next batch forward, with
the **deepest clean training window** adopted separately (`first_feature_season` 2002 at QB/RB;
`season-span-M4.md` §3.1 measured the training-window curve as flat, with QB's deepest span its best
cell). `full_veteran_roster` is **mandatory co-reporting on every cell** and is the **primary
instrument for estimator-calibration work** (§6.2's checks, placebo ensembles, discreteness
diagnostics), where its per-season n of ~250 is a genuine advantage.

**It is not the grading panel, and the reason is a measurement rather than a preference.** Batches 5
and 7 found, across **three batches, three positions and four sources**, that *every arm improving
the full universe degraded the ADP board* — rank **reversal** between populations, not a level
shift. The mechanism: Spearman over ~250 rostered players is dominated by separating starters from
non-players, which is mostly the availability channel; Spearman over the draftable ~20–50 is
dominated by ordering players who all play. **They measure different skills**, so an endpoint
rewarding the first selects arms that lose the second.

**Survivorship is not the objection and was never a valid one** (founder's ruling, 2026-08-01): a
Week-1 active roster is observable before any outcome and `CLAUDE.md` §6.2 names it explicitly, so
the wide tier is sound on that axis. One asymmetry for the record, pointing the other way from the
usual framing: week-1 rows are **kickoff-dated** (G2a ruling), so a roster-defined universe silently
excludes players cut or IR'd in the final preseason week — the bust class — while an ADP-defined
universe is dated strictly pre-draft. §6.2 sanctions both.

**Conflict rule, pre-committed:** improves both → normal grading; improves the wide universe and
**harms** the panel → **not adopted**, reported as a finding about the arm; improves the panel and
harms the wide universe → eligible, flagged narrow-population-specific, re-checked at §6.5.

**One registered escalation:** if tier-2 QB proves structurally undecidable — §4.4a's consistency
q95 saturating on exact-zero mass — a **QB-only `full_veteran_roster` primary** is admissible under
the pre-committed condition that the arm's tier-2 delta is **non-negative**. Nothing else uses it.

**ADR-069 is not at risk.** ADP membership decides *which players are scored*, never what they are
scored against; the ADP column is not a feature and not an ordering input. §6.5's four-baseline
comparison is necessarily restricted to seasons where those baselines exist (market ADP 2018–2024,
ECR 2021–2024, per PR-009) and fires **once at the end** — a restricted release gate is not an
argument for a restricted development panel, and is not an argument for abandoning a draft-relevant
grading universe either. Those are separate questions and this clause answers the second on its own
evidence.

### 4.9 The continuous residual endpoint — admitted, paired, never substituted

Ruled 2026-08-01, same thread. A continuous residual endpoint (`z(realised) − z(projected)`,
standardised within position-season) is admitted for the class of claim ordering cannot address —
**bias and calibration** — and is barred from replacing the ordering endpoint.

- **Ordering keeps primacy.** An arm improving the residual while harming ordering is **not
  adopted**, and is reported as a calibration gain with an ordering cost. Batch D1's A5 arm is
  exactly that shape: it improves the residual and is directionally harmful on ordering at all four
  positions.
- **No separate multiplicity family.** A residual cell counts in campaign M exactly as an ordering
  cell does, or it is a second bite at the same data.
- **Continuity is not calibration, and `n` is not reassurance.** The resampling unit is still the
  **season**, clustered by player — guardrails §0 puts effective N "closer to 5 than 5,100," and
  2,000 player-seasons with recurring players is that trap exactly. A residual endpoint gets the
  **same matched null ensemble and the same §6.2(a) leave-one-out check** before it grades anything.
  D1's own seeded-noise arm returned +0.070 and +0.122 **BH-robust** on its continuous E2 endpoint —
  a contrast-form failure rather than a discreteness one, which is the point: a different endpoint
  fails differently, and none is calibrated by assumption.

## 5. What it costs, and what happens if that is unaffordable

Per §4.3, a 20-cell batch is ≈ 20 × 120 = **2,400 null runs** for the cells that stop early, plus up
to 3,000 for each cell that goes the distance — which, on C1's evidence, is one or two.

At the one wall-clock figure this repo records (a G0 single-position run at 5–6 s) that is roughly
**4 hours for the batch plus ~5 hours per surviving candidate**, embarrassingly parallel across
draws. §7 M-3 replaces that estimate with a measurement before anything is budgeted on it.

**If L is unaffordable for a given cell, the cell is graded `HYPOTHESIS`, never `INCLUDE`.** There
is no reduced-L inclusion, and no parametric shortcut. A batch that cannot afford the confirmatory
ensemble reports hypotheses and says so plainly — which is a legitimate output of this project
(guardrails §5) and is what C1 already did correctly.

---

## 6. Pre-committed error rates, and how the next batch verifies them

Stated **before** the next batch runs, so they can be checked rather than asserted.

### 6.1 The rates this rule is expected to deliver

| event, on a cell whose null is true | expected rate | why |
|---|---|---|
| `HYPOTHESIS` (p ≤ 0.05) | **≤ 5.0%**, exactly | Besag–Clifford is an exactly valid Monte Carlo test |
| `INCLUDE` or `EXCLUDE`, any cell of an all-null 20-cell batch at M = 150 | **≤ 1.3%** | under the global null BH's FDR is its FWER: ≤ q·m/M = 0.10 × 20/150 |
| `INCLUDE` on any single all-null cell | **≤ 6.7 × 10⁻⁴** | q/M |

Against C1's measured 9.6% WIN rate on pure noise at a nominal 2.5%.

### 6.2 The verification protocol, registered now

**(a) Implementation check — leave-one-out calibration, cheap and exact.** Build one ensemble of
K = 200 draws per (position, `d`). For each draw `i`, treat Δ̄ᵢ as the observation and the other 199
as its ensemble; compute the two-sided MC p. Under exchangeability those 200 p-values are exactly
uniform. **Pass:** the `p ≤ 0.05` rate is **≤ 19/200 (9.5%) at every position** and **≤ 53/800
(6.6%) pooled** (one-sided binomial, ~2% each). Cost: 200 runs per position, not 200 × 120.

This check verifies the *implementation*. It will pass whenever the code is right, and it says
nothing about whether the null construction is the right null. That is (b).

**(b) Substantive check — permutation vs. placebo agreement.** For at least one real arm per
position, build **both** nulls at K ≥ 200 and compare. **Pass:** the two ensembles' means agree
within 0.5 permutation-null sd **and** their q95s agree within 0.5 permutation-null sd. **Fail:**
the Gaussian placebo is recorded non-substitutable for that arm class and only the permutation null
may be used there — this is a scope restriction, not a blocker.

**(c) End-to-end placebo, retained.** The next batch keeps a registered placebo arm, graded through
the full replacement rule exactly as C1 did. Registered prediction: **0 INCLUDE, 0 EXCLUDE**, and at
most one `HYPOTHESIS` across all its cells. **A single `INCLUDE` on a placebo re-opens this ADR**,
the same way F0 re-opened its predecessor. That instrument worked; it stays.

### 6.3 Registry accounting

Null ensembles, LOO calibration checks and the agreement check are **calibration, not hypotheses.
They contribute 0 tests to the campaign family and never enter the FDR denominator.** They are
exploratory-registry items. A number produced by any of them that is later quoted as a finding needs
its own registration first.

---

## 7. Measurements this rule depends on, none of which `strategist` can run

Named here so they are commissioned rather than assumed. Full specification and decision rules are
in the staged handoff body accompanying this draft.

| id | measurement | who | blocks |
|---|---|---|---|
| **M-1** | Publish the placebo ensemble's **both tails** (`min, q05, q25, median, q75, q95, max`) and **per-season deltas per draw**, not just Δ̄ and counts | `ranker` | the §4.4a CONSISTENCY condition; the RE-SPECIFY/EXCLUDE split; every HARM cell in B1/C1 |
| **M-2** | Dimension-matched null ensembles, `d ∈ {1,2,3}`, K ≥ 200, CTRL-A, all four positions | `ranker` | whether F3's RB near-miss survives at all (§8) |
| **M-3** | Measured wall-clock per null draw per position | `ranker` | budgeting L |
| **M-4** | Earliest feasible `first_target` for `first_feature_season ∈ {2009, 2010, 2012}`, naming the binding constraint (`min_train_seasons`, `N_LAGS`, source start) | `ranker` | the only structural fix for S = 7 |
| **M-5** | Which prior batches graded a **per-season rank-correlation** endpoint on the season-block bootstrap, versus a continuous MAE endpoint on a large population | `ranker` | the scope of §8's withdrawal |
| **M-6** | The lag-weight decay profile (separate pre-registration) | `ranker` | F6 |

---

## 8. Scope of the withdrawal

**Withdrawn as an error-control claim, effective immediately:** the `BH-robust` flag on every cell
graded with the season-block-bootstrap CI on a per-season rank-correlation endpoint. Those cells
become **`UNCALIBRATED`** in the taxonomy of §4.4 — the grades stay on the record, annotated, and
are not citable in either direction until re-graded.

**Not withdrawn, and this is the honest good news:** the campaign has made **zero inclusions in ~130
tests**, so no discovery's validity is in question and the campaign's realised false-discovery count
is zero by construction. FDR is a property of claims; there are none.

**Batch C1 is the exception and is re-graded in full — all 38 cells.** Its grading was *suspended*,
not completed, so those cells were never validly graded and they get the new instrument. Note what
that costs and what it does not: **the treatment arms do not re-run.** Their per-season deltas are
on disk in `factor_c1_cells.csv` and are estimator-independent. What must be built is the *null
ensembles*, which is new compute, and the §6.2 calibration checks. The output is worth more than
what is on disk today: each NULL comes back with a quoted null band, converting "we detected
nothing" into "we can rule out an effect larger than X at this position" — which is precisely what
§1.3 says the current NULLs cannot support. **Where that band turns out to be wide (QB and TE are
the candidates), the honest disposition is that the factor is *not dispositioned* at that position
and must not enter the ledger as dead.**

**For batches 1–7, re-grade exactly the cells that carried a decision**, not the ninety that carried
none:

| cell | why it is load-bearing |
|---|---|
| B1 `G2a` RB +0.072, WR +0.048, QB +0.019 | the only arm beating naive games MAE; its adoption is live (thread `2026-08-01-g2a-week-1-status-as-of-ruling…`). RB and WR sit far outside anything the placebo produced; **QB +0.019 is the weak one** — QB is where noise wins 14.7% of the time and n = 19 |
| B1 WR HARM −0.0125 | **two arms (G1, G1a) were rejected on it**, and one placebo draw in 34 produced a WR HARM on the same harness. It cannot be assessed at all until M-1 publishes the lower tail |
| C1 F1 TE HARM −0.0285 | the batch's only HARM verdict, at the position with the largest null bias — and the first live candidate for **RE-SPECIFY** rather than EXCLUDE (§4.4b) |

B1 is `fable`'s registered batch. This ADR supplies the instrument and the scope; **it does not
re-grade B1**, and no session should re-grade another agent's registered batch on this draft alone.

**Do not re-grade the ~90 NULLs, and do not treat them as settled either.** They are `UNCALIBRATED`.
Per §1.3 the instrument's power was never measured, so those nulls are not evidence of absence; per
§1.1 they are also not at risk of being hidden discoveries, because a conservative rule cannot
reject where an anticonservative one did not. The correct disposition is a ledger annotation, not a
re-run.

---

## 9. Applying it to C1's two survivors — the arithmetic, so nobody has to re-derive it

Neither is included, and neither becomes a finding under this rule.

| cell | Δ̄ | `p` on the existing 34-draw ensemble | verdict under §4.4 |
|---|---|---|---|
| F3 xFP at **RB** | +0.0186 | ensemble max +0.0085, so 0 exceedances → `p_two = 2/35 = 0.057` | **HYPOTHESIS at best** — and see below |
| F6 steeper recency at **QB** | +0.0266 | ensemble max +0.0151 → `p_two = 2/35 = 0.057` | **not gradeable** — the placebo is not F6's null |

Both sit at the resolution floor of a 34-draw ensemble, which is exactly what §4.3's floor rule is
for: with 34 draws you cannot report a p below 0.057, so neither cell is close to the BH threshold
of 7.7 × 10⁻⁴, and no arithmetic on the existing ensemble can make it so.

**F3-RB carries a specific, cheap risk of dying outright.** Its "survives the placebo" claim
compares a **three-column** arm to a **one-column** null, and the batch's own diagnosed mechanism is
that the null's centre scales with the number of added parameters. M-2 settles it. **My registered
prediction, written before that run:** the null mean rises approximately linearly in `d`, steepest at
TE and QB, near-flat at WR; and there is a real chance the `d = 3` null's q95 at RB reaches +0.0186,
in which case F3-RB is dead with no confirmatory test needed.

**F6-QB is not eligible for this instrument at all** (§4.1). Its question is the value of a
constant, and the null for a constant is other constants. Ruled separately.
