# Discovery pass 1 — reverse-identification hypothesis generation on v2 residuals

FR-2026-07-31-reverse-discovery, dispatched 2026-08-01. **This is a search instrument, not a
finding.** Nothing here is tested, graded, registered, or adopted. Every row in the candidate
table below is a hypothesis for a future registered confirmatory batch, exactly as `batch-C1`'s
`F3`/`F6` near-misses were handled — not a result.

---

## Conclusion first

**The single most useful thing in this pass is not a new factor — it is a description of the
shape of v2's error, and it is the same shape at every level of resolution tried.**

v2 systematically **overprojects players coming off a fully healthy, high-usage prior season**
and **underprojects players coming off a season with missed time**, especially *unexpected*
missed time (injury/role loss, not a bye-adjacent rest game). This is visible as:

- a raw correlation between the projection itself and the residual (mechanical — see caveat
  below, but real and worth naming),
- the single strongest non-mechanical slice in the whole pass: players with a **heavy** share of
  unexpected missed games last season (n=1,004) beat their (correspondingly discounted)
  projection by **+0.20 SD** on average (t=10.6); players with a **light** share (n=703) miss
  their projection by **−0.29 SD** (t=−8.9),
- the **prior-season games-played bucket** slicing the same way even more strongly: 0–4 games
  last year → **+0.23 SD** (t=9.3, n=595); 14–17 games last year → **−0.29 SD** (t=−8.8, n=707),
- and a genuinely new, nonlinear finding from the tree-based generator (Section 3): **Week-1
  depth-chart starter status shifts the residual upward by a similar amount at every level of
  prior-season games**, i.e. it is not just re-describing recency of usage — a player secured as
  this year's Week-1 starter beats projection more than his own lag-1 history alone would predict,
  and this holds within each prior-games bucket, not just across them.

**Named plainly, because it is the actionable part:** v2's games/points channel treats a healthy,
high-workload prior season as more predictive of a repeat than it actually is, and treats an
unhealthy or role-uncertain prior season as more predictive of a repeat than it actually is, in
the pessimistic direction. Both are the same regression-to-the-mean underestimate, and it is
large — multiple SD-tenths at n in the hundreds, dwarfing the noise-control comparison bar
established below. This is consistent with, and sharpens, the open games-channel defect already
named in `docs/fable/v2-build-log.md` (Burrow/Hill-class M2-1 pathology) and with **F6** (steeper
recency weighting, QB near-miss) in `batch-C1`: this pass finds the same under-reversion pattern
at RB/WR/TE, at a much larger effective n, using a completely different method (residual slicing
and a flexible-model generator rather than a single registered arm).

---

## Screening denominator — reported prominently, per instructions

| section | what was screened | count |
|---|---|---|
| §2 systematic screening | 62 real candidate columns + 1 seeded-noise control, × 2 residual targets (signed, abs), × 5 slices (pooled + 4 positions) | **630 tests** |
| §1 residual slicing | 10 slice variables → 30 real cells (n≥15) + 30 noise-control cells (n≥15) | **60 cells** (30 real + 30 negative-control) |
| §3 GBM generator | 6 models fit (pooled full-feature, pooled reduced, ×4 positions reduced), each screening 39–63 features via permutation importance — same underlying columns as §2, not independently counted | 6 model fits over the same 63-column universe |

**Combined correlational denominator this pass: 630 (§2) + 30 (§1 real cells) = 660.** The GBM
section reuses the same 62-column universe as an instrument, not a new independent test count.
None of these 690 numbers is a confirmatory p-value; every one of them is discovery-sample-only
(2018–2021) and none has been checked against 2022–2024, which was loaded but never analyzed here
(see `experiments/bottomup/discovery_pass1.py`, asserted structurally, not by convention).

---

## Negative control — what noise looks like in this screen

A seeded `N(0,1)` column (`NOISE_CONTROL`, seed 20260801) was screened identically to every real
candidate, in every section.

| instrument | noise result | real candidates for comparison |
|---|---|---|
| §2 pooled Spearman, signed_resid | rank 57 of 63, ρ = −0.015 | top real: ρ = −0.47 (`proj_interceptions`, QB-only) |
| §2 pooled Spearman, abs_resid | rank 63 of 63 (last), ρ = −0.002 | top real: ρ = +0.30 |
| §2 per-position (8 screens) | noise never ranks above 39th of 63 | top real ρ ≥ 0.20 in every position/target pair |
| §1 slice mean, |t| | max |t| = 1.90 (an unremarkable position-level cell), **0 of 30 noise cells exceed |t| = 2** | 13 of 30 real cells exceed |t| = 2; top real cells reach |t| ≈ 8.6–10.6 |
| §3 GBM permutation importance, pooled reduced | rank 16 of 39, importance 0.0030 | top real: 0.31–0.32 (two orders of magnitude larger) |
| §3 GBM permutation importance, per-position | rank 7–16 of 39 depending on position, importance 0.007–0.011 | top real: 0.10–0.32 |

**Reading this correctly:** the real top candidates are not "barely above noise" — they are one to
two orders of magnitude larger than anything the seeded-noise column produced anywhere in the
screen, at n in the hundreds to low thousands. That is a different situation from `batch-C1`'s F0
placebo, which triggered on a *bootstrap-CI* WIN rule at n=7 seasons and exposed a harness defect
at small n. This pass uses plain correlation/slice-mean/permutation-importance magnitude
comparisons at n=300–2,000, which do not share that small-n discreteness problem — but the
comparison is still informal (no multiple-comparison correction applied to any of the 690 raw
numbers), and every candidate below is reported as a hypothesis, not a tested effect.

---

## Candidate factors, ranked

Ranked by effect size and mechanism plausibility, not p-value (none of these p-values is
interpretable — see above). "Constructible pre-Week-1" is checked explicitly for every entry.

| rank | candidate | pattern | seasons / slice | effect size | mechanism | pre-Week-1? | vs. noise |
|---|---|---|---|---|---|---|---|
| 1 | **Prior-season games-played level (regression-to-mean under-modeled)** | Low games_1 → v2 underprojects (beats proj); high games_1 → v2 overprojects | discovery 2018–2021, pooled all positions | 0–4 games: **+0.23 SD** (t=9.3, n=595); 14–17 games: **−0.29 SD** (t=−8.8, n=707) | Durability/health status is less persistent year-to-year than the games-projection model assumes; a full healthy season doesn't predict as strongly as modeled, and a shortened season doesn't predict absence as strongly as modeled | Yes — `games_1` is lag-1, known before Week 1 | Noise max |t|=1.90; this candidate's |t| is 4.4–5.9× the noise ceiling |
| 2 | **Unexpected-missed-games share (same family, more specific)** | Heavy unexpected-absence share last year → underprojected this year; light share → overprojected | discovery 2018–2021, pooled | heavy: **+0.20 SD** (t=10.6, n=1,004); light: **−0.29 SD** (t=−8.9, n=703) | Same mechanism as #1, isolated to the *unexpected* (injury/role, not scheduled-rest) component of missed time — the founder's Burrow/Hill mechanism, generalized to a population-level pattern rather than two anecdotes | Yes — `unexp_missed_share_1` is lag-1 | Largest |t| of the whole pass; ~5.6× the noise ceiling |
| 3 | **Week-1 depth-chart starter status, as an interaction with prior usage** | Within every prior-games_1 bucket, being named this year's Week-1 starter shifts the residual up relative to non-starters at the same games_1 level (e.g. 0–4 games_1: starter +0.83 SD vs. non-starter +0.22 SD; 14–17 games_1: starter −0.24 SD vs. non-starter −0.53 SD) | discovery 2018–2021, GBM-surfaced, confirmed by manual two-way slice | see two-way table below | Role security at Week 1 carries information beyond what a player's own lag-1 stat line encodes — likely a depth-chart change (new starter, injury ahead of him resolved, competition lost/won) that the lag-1-only feature set cannot see | Yes — depth chart is set before kickoff; flagged as a proxy signal quality caveat below | GBM importance 0.31–0.32 (pooled/QB), 4–46× the GBM noise-control importance in every position fit |
| 4 | **QB regression-to-mean via projected volume** (`proj_interceptions`, `proj_attempts`, `proj_pass_yards`, `proj_pass_tds`) | Higher-projected QBs (more attempts/INTs projected) systematically overproject; lower-projected QBs underproject | discovery 2018–2021, QB only, n=313 | ρ = −0.42 to −0.47 | This is the strongest linear correlation in the whole pass but is **substantially mechanical**: these columns feed `proj_points` directly, and `signed_resid = z_actual − z_proj` by construction regresses toward the mean whenever the underlying predictor is noisy. It restates F6's QB near-miss (steeper recency weighting) from `batch-C1` rather than adding new information — listed for completeness, not as a fresh candidate | Yes, but see mechanism caveat | ρ magnitude ~30× the noise ρ, but discount for construction-mechanical component |
| 5 | **Heavy prior-season injury share (`inj_missed_share_1` ≥ 30%)** | Small but sharp positive residual | discovery 2018–2021, pooled, n=47 | +0.45 SD (t=3.58) | Same family as #1/#2; small n makes this the weakest-evidenced entry that still clears the noise bar with room | Yes | |t| ~1.9× the noise ceiling, but n=47 — thin |
| 6 | **`ppg_w`, `pts_1` and other pure usage-volume lag features driving `abs_resid`** | Higher recent points-per-game predicts *larger* absolute error, not directional error | discovery 2018–2021, all positions | ρ = 0.23–0.31 on `abs_resid` | Heteroscedasticity: high-usage players simply have wider outcome ranges (more games to accumulate variance, more exposure to role/injury change). Not a missing-feature hypothesis so much as a case for **position- and usage-tier-varying uncertainty bands** rather than a single MAE number, which the model does not currently report | Yes | Consistently 15–150× the noise ρ on `abs_resid` |

### Two-way slice backing candidate #3

| depth-chart Wk-1 role | games_1 bucket | mean signed_resid | n |
|---|---|---|---|
| non-starter/unlisted | 0–4 | +0.22 | 207 |
| **starter** | 0–4 | **+0.83** | 36 |
| non-starter/unlisted | 5–9 | +0.10 | 279 |
| **starter** | 5–9 | **+0.59** | 95 |
| non-starter/unlisted | 10–13 | −0.27 | 272 |
| **starter** | 10–13 | +0.10 | 214 |
| non-starter/unlisted | 14–17 | −0.53 | 166 |
| **starter** | 14–17 | −0.24 | 381 |

The starter/non-starter gap is directionally consistent (starter always higher) across all four
games_1 buckets — this is what "the GBM found an interaction the linear screen missed" means
concretely: the pooled linear correlation of `depth_chart_starter_wk1` with `signed_resid` was
weak and not even monotone by position (QB +0.05 NS, RB +0.03 NS, WR ≈ 0 NS, TE +0.06 NS — none
individually significant at n~300-800), but the *conditional* effect within games_1 strata is
large and consistent everywhere.

### Candidate quality caveat — read before acting on #3

`depth_charts_weekly`'s `pos_rank`/`pos_slot` columns, which are named for exactly this purpose,
are **entirely unpopulated** (verified directly against the table, 2026-08-01) — `depth_team` was
used instead (the field that actually carries the first/second/third-team ordinal). This is
exactly the class of problem `CLAUDE.md`'s "a source swap is not a substitution" warns about: a
column that looks fit for purpose by name was empty, and the working field had to be found by
inspecting the data directly rather than trusting the schema. `depth_team` itself is populated for
1,391/2,054 discovery rows (68%); the remaining 32% are `NaN → 0` (treated as non-starter), which
could either mean "confirmed non-starter" or "not on a Week 1 depth-chart snapshot at all" — those
are different things and a registered version of this candidate should distinguish them.

### Dropped — not constructible pre-Week-1

None of the columns screened required in-season information; `average_pick` and `n_train_seasons`
were screened and ranked low (noise-adjacent) everywhere, so nothing needed to be dropped on
look-ahead grounds this pass. Worth stating explicitly since the dispatch asked for it: **the
screen as designed never touched a target-season-actual column as a candidate predictor** — those
columns (`games`, `points`, `targets`, ... ) were used only to build the residual/outcome, never
fed back in as a feature, which is enforced structurally in `discovery_pass1.py`'s `CANDIDATE_COLS`
list and its accompanying comment, not by convention.

`wk1_injury_report_flag` is also a proxy caveat worth restating: the `injuries` table has **no
`PRE` (preseason) game_type rows at all** — only REG/WC/DIV/CON/SB — so what was built is a
Week-1-of-season injury-report flag (published the week leading up to Week 1, still pre-kickoff)
rather than the originally intended preseason-report signal. It screened weakly everywhere (rank
39–52 of 63 on signed_resid) and is not promoted as a candidate on this evidence, but the
proxy-quality note stands regardless in case a later pass revisits it.

---

## What the residual structure says about where v2 is systematically wrong

This is the part of the dispatch explicitly flagged as most valuable, stated plainly and without
hedging into the individual candidate rows above:

**v2's games/points channel does not revert toward the mean enough.** A player who played a full,
healthy, high-workload season last year is not as likely to repeat it as the model's projection
implies; a player who missed time — especially unexpectedly — is not as likely to repeat that
absence as the model's projection implies. This single pattern explains the two largest-effect
slices in the pass (#1, #2 above) and is consistent with `batch-C1`'s already-registered F6 near
miss (steeper recency weighting helps QB, the position with the fewest games-played anchors per
player-season). It is a single, nameable, structural gap — not forty small mysteries — and it sits
squarely in the games/availability channel that `CLAUDE.md` §2a already named as v2's one measured
deficit relative to market parity.

**Layered on top of that is a role/depth-chart signal the lag-1-only feature set cannot see.**
Candidate #3 says the model is missing information that exists *before* Week 1 but is not derived
from a player's own prior-season stat line at all — it is a roster-status fact about the *current*
season. This is a different kind of gap than #1/#2 (a coefficient that needs to shrink less
aggressively) — it is a feature that does not exist in the current model at any weight.

**Both point the same direction as the founder's own by-eye findings** (Burrow availability, QB
tilt) that motivated this request — reverse identification from residuals reproduces what his eye
caught, at population scale (n in the hundreds, not two anecdotes), and adds one thing his eye
could not have caught without exactly this kind of systematic pass: the depth-chart interaction is
invisible in any single-player residual and only appears when the population is sliced two ways at
once.

---

## What this pass explicitly did not do

Per the dispatch's scope: no factor here was tested, graded, registered, or adopted; nothing in
`experiments/bottomup/v2/factors_c*.py` or the campaign manifest was touched; 2022–2024 was loaded
(for the confirmation-sample bookkeeping printed by `discovery_pass1.py`) but never analyzed;
2025 does not appear in `ranking_v2_G0_players.csv` at all and was never read. The natural next
step — pre-registering candidates #1–#3 as arms on 2022–2024 as the confirmation sample, then the
holdout only via the founder's standing rule — belongs to `strategist`, not to this pass.

---

## Reproduction

```
python3 experiments/bottomup/discovery_pass1.py         # base pipeline, residuals, DB joins, denominator
python3 -m experiments.bottomup.discovery_pass1_screen   # section 2, systematic screening + noise control
python3 experiments/bottomup/discovery_pass1_slices.py   # section 1, residual slicing + noise control
python3 -m experiments.bottomup.discovery_pass1_gbm      # section 3, GBM generator + noise control
```

All four scripts assert/print the discovery-vs-confirmation split and the screening denominator
on every run; none of them import or write anything under `experiments/bottomup/v2/`.

Source artifacts: `experiments/bottomup/results/discovery_pass1_*.csv` (not committed — regenerate
from the commands above plus a copy of `data/nfl.db`, per `docs/environment.md` §4).
