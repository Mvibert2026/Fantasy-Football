# Factor batch 2 — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`factor-batch-1-precommit.md` (`d546cff`). If a number in the results document is not predicted by
an endpoint declared here, it is post-hoc and must be labelled so.

**Scope.** The two `docs/test-registry.md` rows behind the founder's own two examples of what a
bottom-up ranking should be able to *say*
(`docs/founder-requests/FR-2026-07-30-bottom-up-must-produce-causal-insights-new-oc-de.md`):

> "So and so has a new OC and we expect routes run to increase. Or the starter from last year left."

| his example | registry row | why it is testable now and was not before |
|---|---|---|
| the starter from last year left | **#28 vacated targets & carries**, High edge | batch 1 had to run it on a Week-1 **depth chart**; `rosters_weekly` (2002–2025, with status codes) is now in `nfl.db` |
| new OC → routes up | **#29 coordinator continuity**, High edge | `play_callers` held **end-of-season** staff only, which is post-cutoff. A pre-Week-1 revision read is built this session (§6) |

**Exploratory, not confirmatory of a shipped change.** The sealed 2025 holdout is not touched and no
holdout spend is requested. Promotion of any arm into the shipped model is a `strategist`
registration plus a `backend` handoff, not a decision this pass may make.

---

## 1. The question batch 2 exists to answer, stated before the answer is known

Batch 1 graded **#28 HARMFUL at RB (+0.203 carries MAE) and at TE, NULL at WR**, and reported it as
**blocked, not as a null**, because the vacancy had to be measured from a Week-1 depth chart and the
harm sat entirely in the high-measured-vacancy bucket that proxy is known to contaminate
(`factor-batch-1-results.md` §4).

**Three outcomes are possible and all three are publishable.** This is written down now so that
whichever one lands cannot be presented as the one that was expected:

1. **Proxy artifact.** V2 (real rosters) is materially better than V1 (depth chart) and the harm
   goes away. Batch 1's caution was right.
2. **Second null.** V2 is null or harmful too. The factor is genuinely uninformative in this model,
   and the registry row moves from BLOCKED to measured-and-dead.
3. **Split.** The team-level magnitude stays harmful while a player-level construction (V4, M1)
   does something. Batch 1 §4 already logged this as an untested hypothesis.

### The measured contamination, established before any arm was fitted

Target seasons 2014–2024, players with ≥50 carries or ≥50 targets in season N−1 (n = 2,166):

| | roster says still under contract | roster says gone |
|---|---|---|
| **depth chart says still here** | 1,486 | 15 |
| **depth chart says gone** | **91** | 574 |

**91 of 2,166 (4.2%) prior-season producers are called departed by the depth chart while still under
contract** — 40 on reserve/injured, 5 on PUP, 13 active, 1 inactive. That is the leak channel batch 1
§4 hypothesised, now counted rather than argued.

---

## 2. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`.

| | |
|---|---|
| Target seasons | 2014–2024 (11). ADP board exists 2018–2024 (7). |
| Features | seasons ≤ N−1, plus the declared season-N `proxy`-tagged reads below |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1 |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened.** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from its position's primary by exactly the feature block it declares.** No arm
changes the availability sub-model, the bonus machinery, the universe or the scoring.

---

## 3. Endpoints, fixed now — and one deliberate change from batch 1

**E1b — THE GATE. Out-of-sample MAE of the one declared component, restricted to players on the
consensus ADP board.** Arm − primary, paired by season, 11 seasons, season-block bootstrap.
Negative = better. **This is the FDR family.**

*Why this and not batch 1's endpoint.* Batch 1's own §1(3) found the gate it had committed was blind
to **where** a gain sits: two arms cleared it on movement among players nobody drafts. The fix that
report demanded — "any future E1-style gate should require the gain to hold on the decision-relevant
subset, not merely on average" — is adopted here, in advance, as the primary endpoint. The metric is
new (`adpsub_mae_*`, added to `pos_eval._season_metrics` this session, purely additive).

**E1a — reported, not the gate. The same MAE on the full universe**, so every batch-2 number stays
directly comparable to the batch-1 table.

**E2 — the bar that matters, NOT in the FDR family. ADP-board Spearman, arm − primary.** 7 seasons.
`CLAUDE.md` §6.5. **Known underpowered before it is run** at WR and TE
(`component-model-rb-qb-te-pass-1.md` §1); only RB resolves anything. Stated here so it cannot be
produced afterwards as a caveat.

**Exactly one E1 component per cell**, declared in §4. Reporting the best of several components per
cell would be selection on the outcome, which is what this document exists to stop.

---

## 4. The arms — declared in full, m = 15

| # | factor | arm | block | positions | E1 component |
|---|---|---|---|---|---|
| V2 | #28 | **departure share (team)** | `vac2_tshare` / `vac2_cshare` | WR, TE, RB | WR/TE `targets`, RB `carries` |
| V3 | #28 | **absence share (team)** | `vac3_tshare` / `vac3_cshare` | WR, TE, RB | same |
| V4 | #28 | **opportunity vacated AHEAD of this player (player level)** | `vac_ahead_t` / `vac_ahead_c` | WR, TE, RB | same |
| M1 | #28 | **this player moved clubs (player level)** | `moved_club`, `move_known` | WR, TE, RB | same |
| C1 | #29 | **this player's club has a new OC (player level)** | `new_oc`, `oc_known` | WR, TE, RB | same |

**m = 15. Benjamini–Hochberg at q = 0.10 across all 15 E1b p-values, and the denominator is 15
regardless of how many arms turn out to be computable.** Also reported at q = 0.05.

Feature definitions are in `experiments/bottomup/factors/factor_features2.py` and were written
before any arm was fitted.

**V3 is not a robustness check on V2.** "Left the club" and "cannot play in Week 1" are different
questions; both are registered as first-class tests and both count in m.

**V4 is the one genuinely player-level vacancy construction.** Every vacancy feature this project has
tested is team-level — every player on a club gets the same number, which is exactly the property
that makes a ranking unable to hold a player-level opinion. V4 gives two players on the same club
different values by counting only the departed opportunity that sat **above** them.

> **Amendment, 2026-07-30, made BEFORE any arm was fitted and recorded rather than quietly applied.**
> The V4 definition above is ambiguous for a player who **moved clubs**: "ahead of me" would be
> computed on the club he left, which says nothing about his season-N opportunity. Resolved as
> follows, on the football rather than on any result: a player arriving at a new club has no prior
> claim on its touches, so **every** departed team-mate is ahead of him — his value is that club's
> full vacated share (numerically V2 for his new club). Stayers get the ahead-of-me quantity;
> movers and players with no N−1 club get the new club's total. This was decided while the
> coordinator ingest was still running and before `run_factors2` had been executed once.

### Reference arm, outside the family and NOT re-graded

**V1 — batch 1's Week-1 depth-chart proxy**, re-run unchanged at WR, TE, RB. Its only purpose is the
head-to-head **V2 − V1** that answers §1's question. It carries its batch-1 grade; it is not a
fifteenth-plus-one test and no new claim may be attached to it.

---

## 5. Decision rules, fixed now

| grade | rule |
|---|---|
| **SURVIVES** | BH-significant on **E1b** at q=0.10, direction better, **and** E2 > 0 |
| **PROJECTION-ONLY** | BH-significant better on E1b, E2 ≤ 0 |
| **HARMFUL** | BH-significant on E1b, direction worse |
| **MARGINAL / MARGINAL-HARMFUL** | E1b 95% CI excludes zero but not BH-significant |
| **NULL** | otherwise |

**Stopping condition.** All 15 arms run **once**. No arm is re-specified, re-parameterised or
re-scoped after any result is seen. Anything discovered afterwards is labelled post-hoc and carries
a lower evidential standard, as in batch 1 §4.

**C1 coverage gate, committed before the coordinator table is complete.** C1 is a *test* only if
`oc_known` averages **≥ 0.80** across the eleven walk-forward seasons at that position. Below 0.80 it
is reported as a **data finding, not a test**, its cell is marked NO DATA, and it still counts in
m = 15 (the conservative direction).

**Look-ahead escape hatch, committed now.** If any arm's result is large enough to look surprising —
concretely, an E1b improvement exceeding **2% of the primary's own error** — it is treated as a
suspected leak and escalated before it is written up, per `CLAUDE.md` §8. A result that looks too
good is a finding to escalate, not to celebrate.

---

## 6. What the coordinator data actually is, and where it is still a proxy

`play_callers` (607 rows, 2015–2024, from `src/ingest_coordinators_wikipedia.py`) stores the
`{{NFL final staff}}` template, which names **whoever held the role at the END of that season**.
`docs/handoffs/101-*` flagged this as a look-ahead hazard for #29 and handed the fix onward without
building it.

**Using final-staff rows for #29 would manufacture signal, not merely blur it.** A club that entered
season N with continuity and fired its OC in November reads as "changed" — and that firing is
*caused by* the season going badly. The contamination points the same way as the hypothesis.

So batch 2 does not use `play_callers`. It uses
`experiments/bottomup/factors/coord_preseason.py`, built this session, which makes two
revision-dated Wikipedia reads per club-season — the season article as it stood before Week 1 (to
learn which live staff navbox it pointed at) and **that navbox's own revision before the same
kickoff**. Table `play_callers_preseason`, one row per (team, season, OC|DC), `as_of_date` = the
navbox revision timestamp.

*The obvious version of this does not work and the failure is recorded here rather than discovered
later:* re-running the `{{NFL final staff}}` parser against pre-Week-1 article revisions returns
**0 of 32** team-seasons in a 2018 probe, because "final staff" is a static block editors substitute
in after the season ends.

**Still a proxy, named:** the navbox revision is dated days-to-weeks before Week 1 — around a real
late-August draft rather than strictly before it. Coordinator hires are January–March events so the
practical exposure is small, but it is not zero, `as_of_date` states the truth on every row, and
nothing is backdated.

**Head coach as play-caller.** A club with no OC line in the navbox is one where the head coach
called plays — real and common (LA 2018, McVay). The continuity key is
`COALESCE(oc, 'HC:' || head_coach)`. **That substitution lives in feature code, not in the stored
table**, so it is visible, switchable, and does not contaminate the source.

---

## 7. The insight-string rule — committed before any result exists

The founder wants the model to say *"new OC, expect routes up."* The recommendation card was just
caught telling him a reason the code did not implement. **That must not be repeated one layer down.**

**A sentence for a factor may render only when BOTH hold:**

1. the factor graded **SURVIVES or PROJECTION-ONLY** on E1b in this campaign, **and**
2. the underlying feature is **measured and non-null for that specific player** (`oc_known == 1`,
   `move_known == 1`, `vac_club_known == 1` respectively).

Neither is sufficient alone. **If nothing grades, nothing renders**, and the correct deliverable is
the negative result. A sentence asserting a mechanism the model does not price is a false claim
about our own product regardless of whether the football is right.

**Directional wording is a separate claim and is not licensed by this campaign.** "Expect routes to
increase" asserts a *sign*. Nothing in batch 2 measures routes — route participation is not in
`nfl.db` at all (`CLAUDE.md` §5) — and no arm here estimates a signed per-player effect. The most a
surviving factor licenses is *"his club has a new offensive coordinator"* plus whatever the model's
own projection delta already says.

---

## 8. Guardrails (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` gate; separate `outcomes()` accessor; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target |
| **The season-N reads, isolated** | `preseason_roster()` and `preseason_coordinators()` log under the **same `proxy` tag** as batch 1's `week1_roster()`. Every arm that did not declare them must show `n_preseason_proxy_reads == 0`, enforced as a `RuntimeError` |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0 |
| **Multiple comparisons** (§6.3) | BH across all m = 15, q = 0.10 and 0.05, denominator fixed regardless of outcome |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate. Not opened |
| **Effect size** | every E1b reported as a % of the primary's own error |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Reproduction** | batch 1 must reproduce **bit-for-bit** under the extended feature builder; asserted, not assumed |

---

## 9. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| this design and its decision rules | **`strategist`** — thread opened this session, before results are read |
| the result once it exists | **`fable`**, at maximum effort, separate budget |
| the coordinator source's look-ahead semantics and whether it should be productionised | **`data-ops`** — thread opened this session |
| shipping anything that grades | **`backend`** — a handoff, never a self-merge |
