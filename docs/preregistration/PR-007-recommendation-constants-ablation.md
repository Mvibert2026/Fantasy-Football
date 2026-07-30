---
id: PR-007
test_registry_id: FR-059
family: F-RECOMMENDATION-CONSTANTS
mode: confirmatory
question: The draft-room recommendation adds four hand-picked constants on top of VBD (+8 if the
  position is an unfilled starter slot, +18 for a tier-1 TE, -25 for a QB before round 6, and an
  unreachable DEF term). None was fitted to anything and the module's own docstring calls itself a
  stopgap. Under full draft simulation against real historical outcomes, does the recommendation
  with these constants build better ROSTERS than plain VBD, and does each individual constant earn
  its place in the formula?
metric: Paired mean roster points. For arms A and B sharing a common random-number board
  realisation, margin(A,B,s,sigma) = mean over simulated drafts i of [points_A(s,sigma,i) -
  points_B(s,sigma,i)], where points are the season total under a weekly-optimal legal lineup
  scored against ACTUAL historical weekly outcomes under this league's half-PPR-with-bonuses rules
  (draft_sim.weekly_optimal_points). Season statistic is the unweighted mean of the per-season
  margins. Uncertainty comes from two sources reported separately and never combined - a
  season-level bootstrap (draft_sim.paired_season_bootstrap, B=10000, the only one that bounds a
  claim) and the paired Monte Carlo SE across simulated drafts (which shrinks with more sims and
  bounds nothing). Secondary metric, sign-gated only, paired change in P(user roster finishes top-4
  of 10 by total points) - the league's actual objective under a 4-team playoff (CLAUDE.md section
  7). Rank correlation is NOT used and the reason is section 3.
threshold: Materiality floor M = +20 roster points, INHERITED VERBATIM from PR-003 rather than
  chosen for this test. KEEP(constant c) requires ALL of (a) mean leave-one-out margin FULL minus
  LOO(c) at sigma=10 >= +20 points; (b) that margin positive in ALL NINE season-by-sigma cells; (c)
  season-level bootstrap 95 percent CI at sigma=10 excluding 0; (d) sign agreement with the
  standalone contrast ONLY(c) minus PLAIN; (e) sign agreement on the paired change in P(top-4); (f)
  the regime gate - not strictly decreasing across 2022-2023-2024 with the most recent season below
  +20; (g) cross-process determinism and the common-random-number identity assertion both passing.
  DELETE(c) in every other case, including every null, and deletion means the term is removed from
  frontend/ui/data/recommendation.ts. Criteria (d) (e) (f) (g) are conjunctions that can only
  reduce KEEPs and are therefore outside the FDR denominator. Any KEEP is PROVISIONAL - at n=3
  seasons this design cannot supply confirmatory-grade evidence for retention and says so in
  advance (see power_note). The DEF term is DELETED unconditionally with no arm run - it cannot
  fire on any board this project has (ADR-039, no DST ingested) or in the simulator (draft_sim
  assumption 5), so no measurement can license keeping it.
data_scope: {seasons: [2022, 2023, 2024], expected_seasons: [2022, 2023, 2024], sigma_sweep: [5, 10, 20], holdout_unsealed: false}
frozen: {arms: as specified in section 2, sims_per_cell: 1000, seed: 20260729, bootstrap_draws: 10000, registered_at: 2026-07-29, registered_by: strategist, content_hash: sha256:bdcd090e4487aaf6032d9f6dbe3167254bb691ad76a6514795667413763f6a3c}
secondary: The arms vbd_te_window (the +18 moved from tier-1 to the consensus TE7-10 band from
  FR-039 pass 2), vbd_need_continuous (the +8 replaced by live_availability.n_need), bpa_consensus
  and balanced (PR-003's existing consensus-board strategies), the sigma=0 deterministic
  diagnostic, and every pick-flip-rate figure are DESCRIPTIVE ONLY - point estimates, no CI, no
  p-value, no significance flag, outside every FDR denominator, and none may promote a constant to
  KEEP or be reported as an edge. In particular vbd_plain versus bpa_consensus may NOT be reported
  as evidence our board beats expert consensus (PR-004 section 2 scope limit applies unchanged).
resampling_unit: season
power_note: n=3 seasons. The exact two-sided sign test's minimum attainable p is 0.25 and a
  bootstrap over 3 units is too lumpy for an admissible tail probability, which is why
  paired_season_bootstrap deliberately returns no p-value. NO ADMISSIBLE P-VALUE EXISTS AT THE
  REGISTERED RESAMPLING UNIT, so Benjamini-Hochberg cannot be applied and is not applied; section 5
  states the structural multiplicity control and the explicit false-KEEP bound that replaces it.
  The resampling unit is NOT moved to the simulated draft to manufacture power - that would inflate
  n a thousandfold using a unit that is not the argument. Consequence, stated before the run: this
  design is powered to DELETE and underpowered to KEEP, which is the correct alignment of power
  with the burden of proof (CLAUDE.md section 6.3 - every added parameter must earn its place).
amendments:
---

# PR-007 — F-RECOMMENDATION-CONSTANTS: do the four hand-picked constants beat plain VBD?

**Registered 2026-07-29 by `strategist`. Nothing has been run. `strategist` has no database
access by design and will not execute this; `ranker` (or `backend`) executes and reports.**

Founder, 2026-07-29 (FR-059): *"Those seem like random adjustments. And odd given our research
suggested vbd. We need to test those adjustments."*

He is right on both the fact and the framing. VBD is the researched quantity — it is what the
board is built on and what every ranking measurement in this project is scored against. Three
reachable constants override it on the one screen used under a draft clock, and none of them was
fitted to anything.

---

## 0. The asymmetry this design is built around — read this before the decision rule

An unfitted constant sitting in production is a **claim**, and `CLAUDE.md` §6.3 says every added
parameter must earn its place against a holdout rather than against training fit. So the two
possible verdicts do not carry equal evidential burdens:

| Verdict | What it needs | What this sample can supply |
|---|---|---|
| **DELETE** | The constant failed to demonstrate a material benefit | Available. No significance required — the null *is* the action. Deleting an unfitted number that did not show a benefit needs no multiplicity protection, because the simpler model is the default, not the alternative. |
| **KEEP** | Positive evidence of a material benefit | **Barely.** n=3 seasons, sign-test floor p=0.25. A KEEP here is "not deleted this pass," never "validated." |

**This design is therefore powered to delete and underpowered to keep, deliberately.** That is not
a defect to engineer away and it is not a rigged test — it is what "must earn its place" means when
the burden of proof is on the parameter. The alternative posture — keeping a constant because the
data could not prove it harmful — is precisely the failure mode `docs/statistical-guardrails.md`
exists to prevent.

**The expected outcome is that all three reachable constants are deleted and
`recommendationScore()` collapses to `row.vbd.value`. That outcome is a PASS of this test, not a
failure of it.** A simpler model that matches a tuned one is the better model.

---

## 1. What is actually being tested, stated in code terms

`frontend/ui/data/recommendation.ts:16-28`:

```
score = vbd
      + 8   if unfilledPositions.has(position)
      + 18  if position === 'TE' && tier === 1
      - 25  if position === 'QB' && round < 6
```

`round` is 1-indexed (`roundOfPick` = `Math.ceil(overallPick / teams)`, `frontend/ui/data/draft.ts:135`),
so `round < 6` means **the first five rounds**. `unfilledPositions` is the set of **starter** slot
positions with an empty slot (`DraftRoom.tsx:673-676` — `kind === 'starter'` only, so FLEX and
bench are excluded). The DEF term in the docstring is not implemented and could not fire if it
were.

**Port to the simulator, exact and mechanical, no judgement left to the implementer:**

| Frontend | Simulator equivalent |
|---|---|
| `row.vbd.value` | `make_board.build_board(conn, season, source='fantasypros_ecr')` → `BoardRow.vbd`, joined to `SeasonData` by `player_id` |
| board score direction | `_best_by` uses `argmin`, so `board = -(vbd + Σ terms)`; a `+8` bonus is `adj[mask] -= 8.0` |
| `unfilledPositions.has(pos)` | `state.my_counts.get(pos, 0) < draft_sim.STARTERS[pos]`, recomputed at every user pick |
| `tier === 1` (TE) | **Not available historically — see §6 census.** Surrogate: top-K TEs by consensus positional rank, K measured from the live 2026 board |
| `round < 6` | `state.round_number <= 4` (`round_number` is 0-indexed) |
| DEF term | Not implemented. Untestable. Deleted regardless — §4. |
| rows with no VBD sort last but stay pickable | Unjoined players get `vbd = (season board minimum) − 1e-6` |

Every arm additionally passes through `draft_sim._legal_mask(state, data)`, identically, exactly as
`strategy_bpa` does.

> **Interpretive guard, registered in advance.** `_legal_mask` forces mandatory starter positions
> once remaining picks equal remaining needs. That is a *need mechanism the simulator already has*.
> So the `+8` term is being measured **on top of an existing legality floor**, and a null on `+8`
> must be reported as "adds nothing beyond the legality floor," **not** as "roster need is
> worthless." Those are different claims and only the first one is licensed.

---

## 2. Arms

Twelve arms. Only four comparisons are confirmatory.

**VBD-board arms** (board = the season's VBD board, built look-ahead-free per §7):

| Arm | Definition |
|---|---|
| `vbd_plain` | **PLAIN.** Pure VBD, no constants. The comparator for everything. |
| `vbd_all4` | **FULL.** VBD + all three reachable constants (the shipped formula). |
| `vbd_loo_need` | FULL minus the `+8` |
| `vbd_loo_te` | FULL minus the `+18` |
| `vbd_loo_qb` | FULL minus the `−25` |
| `vbd_only_need` | PLAIN plus the `+8`, alone |
| `vbd_only_te` | PLAIN plus the `+18`, alone |
| `vbd_only_qb` | PLAIN plus the `−25`, alone |
| `vbd_te_window` | **DESCRIPTIVE.** PLAIN plus `+18` applied to consensus **TE7–TE10** instead of tier-1 |
| `vbd_need_continuous` | **DESCRIPTIVE.** PLAIN plus `NEED_ADJUSTMENT_SCALE × (n_need(pos) − 1)` in VBD points (`live_availability.n_need`, ADR-046) instead of the flat `+8` |

**Consensus-board arms**, unchanged from PR-003, required baselines and context:

| Arm | Role |
|---|---|
| `bpa_consensus` | Guardrails §5 baseline 3 (expert consensus preseason). **Descriptive.** |
| `balanced` | ADR-046's continuous need model as PR-003 defines it. **Descriptive.** |

**Why leave-one-out AND add-one-in, and why that is the whole interaction treatment.**
Leave-one-out (`FULL − LOO(c)`) measures a term's marginal contribution *in the presence of the
others* — which is the question "does it earn its place in the shipped formula." Add-one-in
(`ONLY(c) − PLAIN`) measures the term standalone. **If the two agree in sign the terms are
effectively additive; if they disagree, that disagreement IS the interaction finding** and is
reported as such. Running separate 2-way and 3-way interaction arms would triple the denominator to
buy inference this sample cannot support. Declining to run tests that cannot be interpreted is part
of the multiplicity control, not a gap in it.

**Baseline that is structurally unavailable, named rather than quietly omitted.** Guardrails §5
requires consensus **market ADP** as a baseline. No historical ADP exists for 2022–2024 in this
repo (ADR-018; the MFL/FFC captures in `data/adp-snapshots*` begin 2026-07-26). That baseline
therefore cannot be produced and its absence is a stated limitation, not an oversight. Baselines 1
(BPA by our VBD and replacement levels) and 3 (expert consensus) are both present, as `vbd_plain`
and `bpa_consensus`.

---

## 3. Why the metric is roster points and not rank correlation

`CLAUDE.md` §6.6 and guardrails §6 both say rank correlation is a proxy and the decision-relevant
question is whether a ranking builds better *rosters*. Here that is not a preference — **a
list-based metric is structurally incapable of scoring this object at all.**

Two of the three constants are functions of state that no static list has:

- `+8` depends on `unfilledPositions`, which is a function of **what you have already drafted**.
- `−25` depends on **which round it is**.

There is no ordered list to correlate: the recommendation produces a *different* order at every
pick. And the third constant, `+18`, is precisely a claim about opportunity cost under contention —
taking a TE earlier means not taking the receiver who will be gone by your next turn — which
`starter_vbd` and every list metric is blind to by construction (`draft_sim.py:6-11`).

The simulator scores rosters against real weekly outcomes under this league's real scoring rules.
It is the only instrument in the repo that can answer the question the founder asked.

**Secondary metric and why it is sign-gated rather than headline:** ΔP(top-4). CLAUDE.md §7 says
the league has a 4-team playoff, weeks 16–17, no reseeding, so finishing top-4 is the actual
objective and mean points is the proxy. But it is a binary outcome and much noisier, and gating on
two correlated metrics without correction inflates KEEPs. So it enters as a **sign-agreement
conjunction** (criterion (e)) and is reported in full. If it disagrees with mean points, the
disagreement is reported, not resolved by picking the friendlier one.

---

## 4. The decision rule — written before any result exists

Notation: `PLAIN` = `vbd_plain`, `FULL` = `vbd_all4`, `LOO(c)` = FULL without term c, `ONLY(c)` =
PLAIN with only term c. Materiality floor **M = +20 roster points**.

> **The floor is inherited from PR-003 verbatim, not chosen for this test.** Same simulator, same
> league, same units, same decision-relevance arithmetic (~1% of a ~2,145-point season roster
> total, the smallest margin that could plausibly change a draft decision). Re-deriving a floor for
> this test is the exact move by which a bar gets quietly lowered, so it is not made. Note also
> that precision and materiality are different quantities: the common-random-number design in §7
> makes small effects *detectable*, which is not the same as making them *matter*.

### Comparison 1 — the founder's question. Confirmatory.

**`FULL − PLAIN`.**

**RECOMMENDATION BEATS VBD** iff margin at σ=10 ≥ +20 **and** positive in all 9 season×sigma cells
**and** the season-level bootstrap 95% CI at σ=10 excludes 0. Otherwise **DOES NOT BEAT VBD**, and
that sentence is the headline reported to the founder, stated plainly, whichever way it lands.

### Comparisons 2–4 — one per reachable constant. Confirmatory.

For c ∈ {`need+8`, `te+18`, `qb−25`}, on **`FULL − LOO(c)`**:

| | Criterion | In the FDR denominator? |
|---|---|---|
| (a) | mean margin at σ=10 **≥ +20 points** | yes (the test) |
| (b) | margin **> 0 in all 9** season×sigma cells | yes (the test) |
| (c) | season-level bootstrap 95% CI at σ=10 **excludes 0** | yes (the test) |
| (d) | **sign agreement** with `ONLY(c) − PLAIN` at σ=10 | no — conjunction |
| (e) | **sign agreement** on ΔP(top-4) at σ=10 | no — conjunction |
| (f) | **regime gate** — per-season margins at σ=10 are not strictly decreasing across 2022→2023→2024 with the 2024 value below +20 | no — conjunction, one-way (can only delete) |
| (g) | cross-process determinism **and** the CRN identity assertion (§7) both pass | no — conjunction |

**KEEP(c)** iff all seven. **DELETE(c)** in every other case.

**Honest note on (b) and (c): at n=3 they are near-collinear.** A 3-unit bootstrap of the mean has
ten distinct values; a 95% CI excluding zero essentially requires all three seasons positive. They
are therefore **not two independent pieces of evidence**, and nobody may later count them as two.
They are both listed because they fail differently under the sigma sweep, not because they
compound.

### Pre-committed dispositions

| Outcome | Disposition, decided now |
|---|---|
| DELETE(c) | The term is removed from `frontend/ui/data/recommendation.ts`, its assertion removed from `frontend/ui/__tests__/recommendation.test.ts`, and FR-058's override panel correctly falls silent on it. |
| All three DELETE | `recommendationScore()` collapses to `row.vbd.value`; the module becomes a pass-through or is deleted and the panel sorts by VBD — the researched quantity. **Expected outcome. Reported as a success.** |
| Any KEEP | Labelled **PROVISIONAL** in every downstream document. Licenses "not deleted this pass," never "validated." Confirmation requires a separate registration that either unseals 2025 with named founder approval or waits for the 2026 prospective result. |
| Margin clears +20 at some σ and flips sign at another | **ASSUMPTION-DEPENDENT → DELETE.** PR-003's registered language, reused unchanged. |
| A constant's pick-flip rate < 1% of user picks | Reported as **UNEXERCISED**, not as evidence of harmlessness. Deletion still follows — a term that never fires cannot earn its place — but the *reason* is "never fires," which is a different and more actionable finding. |
| **DEF term** | **DELETE unconditionally. No arm is run.** No DST rows exist on any board (ADR-039) and DEF is auto-filled as a constant in the simulator (`draft_sim.py` assumption 5). **No instrument this project has or could build from this data can make the term fire.** Keeping an untestable term is a code-hygiene decision made on inspection, not a statistical one. Not in the denominator. |

### STOP conditions — do not run, reply on the thread

1. Census (§6) yields **fewer than 3 usable seasons** → stop.
2. Census shows **zero TEs carry `tier == 1`** on the live board → the `+18` term is already dead in
   production; run neither `vbd_all4`'s TE component nor the TE arms, delete the term as dead code,
   and report that instead.
3. More than **5%** of a season's simulator universe fails to join to a VBD row → the two boards
   are not the same object; stop.

### Three exits closed by name

1. **"It clears if we drop the +20 floor."** The floor is inherited, not fitted, and moving it
   after the fact is the move this section exists to prevent.
2. **"The descriptive arm looks better."** No descriptive arm may promote a constant to KEEP. They
   carry no CI and no p-value.
3. **"Re-run at a different sigma default / seed / roster-need setting / sims count."** Each is a
   different test needing a new PR id, which increments `m` and re-triggers the whole §5 accounting.

---

## 5. Multiple comparisons — what is being done, and what cannot be done

**m = 4**, fixed at `docs/preregistration/families/F-RECOMMENDATION-CONSTANTS.yaml` before the run:
`{FULL−PLAIN, FULL−LOO(need), FULL−LOO(te), FULL−LOO(qb)}`.

**Benjamini–Hochberg is not applied, and the reason is not convenience.** At n=3 seasons the exact
two-sided sign test's minimum attainable p is 0.25, and `paired_season_bootstrap` deliberately
returns no p-value because a 3-unit bootstrap's tail is an artifact of the resampling grid rather
than evidence (`draft_sim.py:436-447`). **There is no admissible p-value at the registered
resampling unit, so there is nothing for BH to correct.** Producing one by resampling simulated
drafts instead of seasons would inflate n by a factor of ~1000 using a unit that is not the
argument, and is refused.

What replaces it, all of it structural and stated in advance:

1. **m is fixed at 4 before the run**, and **all four are reported including failures**, each
   appended to `docs/preregistration/test_run_log.jsonl`. A test run and not recorded shrinks every
   future denominator.
2. **An explicit false-KEEP bound.** Criterion (b) requires all 3 seasons positive. Under the
   global null with the season as the independent unit, P(3/3 positive) = 0.125 per comparison, so
   **the expected number of false KEEPs across m=4 is ≤ 0.5 before the +20 materiality floor is
   applied at all.** That number is stated here so nobody has to infer it later, and it is exactly
   why every KEEP is labelled PROVISIONAL rather than treated as a finding.
3. **Conjunctive criteria are excluded from the denominator by construction** — (d)–(g) can only
   reduce the number of KEEPs, never increase it (same construction as PR-004 §4).
4. **Descriptive arms are excluded from every denominator** and may carry no CI, p-value, or
   significance flag (`preregistration.validate_exploratory_artifact`).
5. **Interactions are not tested as separate hypotheses** — §2 explains why LOO plus add-one-in
   already exposes any interaction, and why adding interaction arms would buy nothing this sample
   can interpret.

**A one-line summary a reader may quote:** the multiplicity risk here is controlled by fixing the
denominator, requiring unanimity across seasons *and* across the sigma sweep, refusing to
manufacture a p-value from the wrong resampling unit, and marking every retention provisional — not
by a correction procedure, because the sample cannot support one.

---

## 6. Census — run first, reply, then freeze

**A coverage census reveals nothing about any effect, so it may legitimately precede the freeze**
(PR-004 §3 precedent). `strategist` has no database access and will not assert any of these numbers.

| # | Query / check | Why it gates the run |
|---|---|---|
| 1 | `SELECT tier, COUNT(*) FROM rankings WHERE source='fantasypros_csv_2026draft' AND position='TE' AND tier IS NOT NULL GROUP BY tier` — and separately, the count of TE rows with `tier == 1` in the **live** `frontend/public/data/board.json` | Fixes **K**. **If K = 0 the `+18` never fires in production** — STOP condition 2. |
| 1b | Are the tier-1 TEs on the 2026 board *exactly* the top-K TEs by consensus positional rank? | Measures the fidelity loss in the surrogate. Report either way; the surrogate is used regardless, having been declared first. |
| 2 | `SELECT season, COUNT(*) FROM rankings WHERE source='fantasypros_ecr' AND is_preseason_final=1 AND position IN ('QB','RB','WR','TE') GROUP BY season ORDER BY season` | Which seasons have a usable pre-draft board. |
| 3 | For each candidate season s, confirm `make_board.fit_rank_curves(conn, s)` returns a curve for all four positions, and **print the training-season list it used** | 2021 is expected to fail — no prior consensus season exists to fit the rank→points curve, exactly as PR-003 noted. |
| 4 | Fraction of `draft_sim.load_season(conn, s)` player ids present in `make_board.build_board(conn, s, source='fantasypros_ecr')` | STOP condition 3. |
| 5 | Per season, the count of universe players finishing with **0 fantasy points** | Survivorship check — a universe with no zeros is a bug, not a clean dataset (guardrails §2). |

**Fold set, pre-committed as a formula rather than a list:**

> `SEASONS = { s : checks 2 and 3 both pass for s, and s ≠ 2025 }`

**Expected answer, stated in advance so the census can contradict me: {2022, 2023, 2024}, n = 3.**
If n < 3, **STOP and reply — do not run.**

**The TE tier surrogate, pre-committed as a formula:**

> **tier-1 TE in season s := the top-K TEs by consensus positional rank in s**, with K from census
> check 1.

`rankings` as created by `ingest_rankings.py:70-88` has **no tier column** — tiers arrive only with
`ingest_fantasypros_csv.py` on the single 2026 pull. So the production term cannot be ported
faithfully to any historical season, and this is a **declared fidelity limitation**: the historical
arm tests "a +18 bump on the top-K TEs," which is the closest construction the data admits. **No
other definition may be substituted after the run.** If check 1b shows FantasyPros' tier 1 is not
the top-K by rank, that discrepancy is reported alongside the result and the verdict stands as
registered.

---

## 7. Protocol

**Look-ahead (guardrails §1).** The VBD board for season N is `build_board(conn, N,
source='fantasypros_ecr')`; its rank→points curve is fitted by `fit_rank_curves`, which uses only
seasons **strictly before N** (its own docstring, `make_board.py:280-282`). The consensus input is
the `is_preseason_final` pre-draft board. Outcomes enter **only** through
`weekly_optimal_points`, never through any board. **Backend asserts programmatically and prints:**
`max(training_seasons) < N` for every fitted curve in every season. Every season read routes
through `holdout.load_season_registered(year, "PR-007")`.

**Survivorship (guardrails §2).** The universe is the entire pre-season consensus list; players who
never scored get 0 and are retained by construction (`load_season` seeds `pts` with zeros). Census
check 5 asserts the zeros are actually there.

**Common random numbers — mandatory, and a deliberate departure from PR-003.** Every arm within a
(season, sigma) cell uses the **identical seed**, so `simulate_one`'s single per-draft
`rng.normal(0, sigma, n)` board realisation is byte-identical across arms and the paired difference
isolates the constant rather than the room. Seed formula: `20260729 + int(sigma*1000) +
season_index*97`. **`run_draft_sim.py:68` adds `stable_offset(name)` and must NOT be copied** —
that gives each arm a different room and destroys the pairing. Consequence, stated so it is not
mistaken for a bug: **this run does not and is not meant to reproduce PR-003's numbers.**

Two hard requirements that make CRN real rather than assumed:

1. **No strategy may consume the RNG.** Ties break on lowest player index (`np.argmin` default),
   deterministically.
2. **CRN identity assertion:** record `zlib.crc32` of the first draft's `effective_rank` bytes per
   (arm, season, sigma) and **assert equality across all arms in the cell**. A mismatch voids the
   run — it is not a caveat.

**Sims.** 1000 per (arm, season, sigma). Pre-declared precision extension: compute the paired Monte
Carlo SE for the four confirmatory comparisons at σ=10 **before printing any margin**; if any
exceeds **3 points**, re-run the **entire grid** at 3000 sims (re-running a subset would break the
pairing). The trigger is Monte Carlo SE only — never an effect size — and the script must emit the
SE and the extension decision before any margin is displayed.

**Sigma sweep (§ answering "the simulator's own unfitted assumption").** `draft_sim.SIGMA_SWEEP`
verbatim: **{5, 10, 20}**. `draft_sim.py:17-23` is explicit that sigma is a guess with nothing
fitted behind it, so a result at one sigma is a property of the guess.

- **The sweep is combined as a conjunction, not an average.** The headline number is at σ=10 (the
  module default); the verdict additionally requires the same sign at σ=5 and σ=20. Nine cells
  (3 seasons × 3 sigmas), all nine must be positive for a KEEP.
- **Absolute roster totals are never compared across sigma** — they move sharply because sigma
  controls how badly the opponents draft (PR-003: BPA scores 2108.8 at σ=5 and 2279.1 at σ=20).
  Only within-sigma margins are meaningful.
- **σ = 0 is run as a deterministic descriptive diagnostic** (one draft per season per arm, no CI):
  it answers whether each constant changes the pick at all in a modal, noiseless room. **If a
  constant's pick-flip rate is 0 at σ=0 but positive at σ=20, its entire measured effect is an
  artifact of opponent noise and must be reported that way.**

**Pick-flip diagnostic (descriptive, required).** Per arm, per cell: the fraction of user picks
where the arm's selection differs from `vbd_plain`'s at the same pick under the same realisation,
and the mean VBD surrendered when it flips. This is what makes an UNEXERCISED verdict distinguishable
from a fires-and-fails verdict, and it is the single most useful number to hand the founder.

**Reproducibility (guardrails §11).** Integer seed **20260729**. Never builtin `hash()` — use
`zlib.crc32`/`config.stable_offset`. Determinism is proved by running twice **in separate
processes** and comparing byte-for-byte; that is criterion (g), not a footnote.

**Holdout.** **2025 stays sealed. This registration does not authorise an unseal and no agent may
perform one under it.** Reasons, all pre-committed: n=1 cannot resolve a +20 margin; an unseal is
irreversible and permanently closes the family; thread 087 has a live competing claim on the same
holdout; and the expected outcome here — deletion — needs no holdout at all, because nothing was
ever fitted to these seasons.

**On whether the development seasons are truly naive.** Nothing is fitted here, so there is no
train/test split to make and the run is a single evaluation. But the constants were chosen by an
agent that had read this project's prior findings on 2021–2024, so those seasons are **weakly
contaminated with respect to them.** That bias runs toward the constants looking *good*, which
strengthens a DELETE and weakens a KEEP — the direction that matters. Named here rather than
discovered later.

---

## 8. The two things the design was asked to be sceptical of — and my rulings

### 8.1 The `+18` points at the TOP of the position; FR-039 pass 2 found the free window is TE7–10

The contradiction is real. The constant rewards tier-1 TEs — the most expensive ones — while this
project's own exploratory pass located the mispricing at **TE7–TE10 (overall ECR ~75–113, rounds
8–11)**, and PR-003 measured `elite_te_early` at **−96.1 points, negative in 12 of 12 cells**. The
`+18` is pointing at the part of the position the evidence is most hostile to.

**Should the design test the TE bump as varying rather than fixed? No — not as a confirmatory arm,
and this is a refusal, not an omission.** Searching over *where* the bump belongs is model
**fitting**. Putting a fitted quantity inside a test whose job is to adjudicate an unfitted one
destroys the comparison: the fitted version would win on construction and the run would have
laundered a search into a validation. With 3 seasons and a simulator whose dominant parameter is
itself a guess, that fitted placement would have no out-of-sample support and would be **worse than
the status quo**, because it would carry false authority.

**What is done instead:** `vbd_te_window` runs the `+18` at the TE7–10 band **taken verbatim from
pass 2 with no re-cutting**, as a **descriptive** arm — point estimate only, no CI, no p-value,
outside every denominator, and it may never be reported as an edge or promote anything. If it looks
better than the tier-1 placement, that is a **hypothesis for a future confirmatory registration**,
not a licence to move the bump. The `+18`'s own disposition does not depend on it in either
direction.

### 8.2 The `−25` QB penalty is a flat constant in a market whose QB premium collapsed −67 → −4

This is the more serious of the two. `CURRENT-STATE.md` open item 12 records the QB rank-curve
slope collapsing monotonically 2021→2025 (−67, −73, −59, −45, **−4**). A flat penalty calibrated —
loosely, by hand — against a pooled regime is being applied to a 2026 draft whose regime has
changed by an order of magnitude.

**A flat constant must be tested flat, because flat is what ships.** Replacing it with a
time-varying version and testing *that* would be testing a model nobody has built, and would leave
this test with no out-of-sample left. **Fitting a season-varying QB penalty is a different question
and needs its own registration.** I am explicitly declining to fold it in.

**What the collapse changes is the interpretation, so it gets a pre-committed one-way gate:**
criterion **(f)**. A QB term whose per-season margin decays across 2022→2023→2024 and lands below
the floor in the most recent season is **REGIME-DEPENDENT and is deleted regardless of the pooled
mean**, because a pooled mean averages over a regime that no longer exists. The gate can only
delete, never retain, so it does not enter the denominator.

**Additional required reporting:** print the **fitted QB rank-curve slope for each season's board**
alongside that season's QB-term margin. The QB environment is non-stationary in two ways at once —
the market's QB premium *and* the VBD board that is fitted from it — and the two must be readable
together or the margin cannot be interpreted.

**One more scepticism the brief did not name, and it cuts the other way.** PR-003 found `qb_early`
(reaching for a QB) at **−115.4, negative in 12 of 12 cells** — so a *penalty* on early QBs pushes
in the direction the evidence already supports. But VBD is computed against a **QB10 replacement
baseline** in a 10-team 1-QB league, which mechanically suppresses QB VBD already (ADR-016 slot
values: RB1 168.5 > WR1 153.2 > **QB1 114.1**). **The `−25` is therefore most likely redundant
rather than wrong** — double-counting a correction plain VBD already makes. Redundancy fails
criterion (a) just as squarely as harm does, and the disposition is the same.

---

## 9. Predictions, registered before the run

**Calibration prior applied as a standing rule** (`docs/reviews/FABLE-EXT3-2026-07-27.md`): four of
five registered prediction sets across sessions 3–4 were materially wrong, **every miss
over-crediting a situation story.** The priors below come from *measurement* (PR-003, ADR-016), not
narrative, so they get more than half weight — but where I am reasoning from a story I say so.

| Term | Evidence it rests on | Prediction |
|---|---|---|
| `+8` unfilled | No direct measurement. ADR-046 replaced a flat `−8.0` need step with a continuous model in `balanced` on exactly the grounds that a flat step is crude. The simulator's `_legal_mask` already forces starters. | **DELETE.** Margin within ±10 of zero, cells split. Plausibly **UNEXERCISED** — low flip rate, because VBD already spreads positions. |
| `+18` tier-1 TE | PR-003 `elite_te_early` −96.1, **0/4 seasons, 12/12 cells negative**; ADR-016 TE1 slot value 73.1, lowest of the four. | **DELETE, most likely with a negative margin.** My strongest directional call. **Honest caveat:** PR-003's arm was a −45 *rank-point* bias across rounds 1–3, not an +18 *VBD-point* bump — different unit, smaller magnitude — so a large negative is not guaranteed and a small one would not surprise me. |
| `−25` early QB | PR-003 `qb_early` −115.4, 0/4, 12/12 negative (penalising early QB pushes the right way); but VBD vs a QB10 baseline already suppresses QB. | **DELETE on redundancy.** Margin positive but small, **0 to +15**, failing the +20 floor. This is the one I would least mind being wrong about. |
| `FULL − PLAIN` | The sum of the above | **DOES NOT BEAT VBD.** |
| **Overall** | | **All three deleted. `recommendationScore()` becomes `row.vbd.value`.** |

**If the run instead returns three KEEPs, read this table first.** It predicted otherwise, and a
clean sweep of KEEPs on three seasons should be treated as evidence of an **implementation bug** —
most likely broken CRN pairing or a VBD board that leaked outcomes — before it is treated as
evidence the constants are good. That is guardrails §8 item 7: an unusually strong result is
evidence of a bug more often than evidence of a good model.

---

## 10. What would falsify the registration itself

- **CRN pairing silently broken** (any arm consuming RNG, any per-arm seed offset). The §7 crc32
  assertion exists to catch it; a mismatch **voids the run** rather than caveating it.
- **The VBD board leaking target-season data** — the §7 assertion on `max(training_seasons) < N`
  must print, not merely be believed.
- **Universe drift**: if any season's universe is filtered on a post-season-N quantity, the run is
  void, not caveated.
- **The TE surrogate diverging materially from production tiers** (check 1b). Reported, not hidden;
  the verdict stands as registered but its transferability to the shipped term is reduced and must
  be said in the result.
- **Determinism failing** across processes (ADR-028's precedent: the same arm reported −92.9 and
  −98.6 with no code change).
- **Simulator assumptions 3, 6 and 7** (opponents do not adapt, lineups set with perfect hindsight,
  no in-season management) are unchanged, uncalibrated, and apply equally to all arms, so they
  cancel in margins but bound what any margin means. This measures the **draft** in isolation.

---

## 11. Reporting

One results section appended to this file. Required contents, none optional:

1. Census results — K, check 1b, the season list with per-season training seasons, join coverage,
   zero-scorer counts.
2. For each of the four confirmatory comparisons: margin at each sigma; the per-season margins; the
   season-level bootstrap 95% CI at σ=10; the paired Monte Carlo SE (separately, never combined);
   the 9-cell sign table; ΔP(top-4); and **the verdict against each of (a)–(g) individually — not a
   summary judgement.**
3. The pick-flip rate and mean VBD surrendered per arm, per cell (descriptive table, no CI).
4. The fitted QB rank-curve slope per season next to the QB-term margin (§8.2).
5. Descriptive arms in a separately marked table carrying no CI, no p-value, no significance flag,
   with the §2 scope limit restated: `vbd_plain` vs `bpa_consensus` is **not** an edge claim.
6. An explicit statement of which `docs/statistical-guardrails.md` checks were applied and how
   (that document's standing rule: a result reported without this is an unverified claim).
7. All four comparisons appended to `test_run_log.jsonl`, **including the failures.**
8. `status: RUN` in the front matter and the family status updated.
9. **One plain sentence answering the founder**, stated whichever way it comes out — e.g.
   *"The recommendation's constants do not build better rosters than plain VBD; all three are
   deleted and the panel now sorts by VBD."*

---

## 12. Freeze procedure — after the census, before the run

`frozen.content_hash` reads `PENDING-FREEZE` because the registering agent has no shell.
`compute_content_hash()` redacts the field before hashing, so writing the real value in afterwards
does not change it.

1. Run the §6 census. Reply on the thread with every figure. **If a STOP condition fires, stop here.**
2. Replace `seasons: MEASURED-BY-CENSUS-SEE-SECTION-6` in `data_scope` with the measured list, and
   `K` where §6 names it.
3. `python -c "import sys; sys.path.insert(0,'src'); import preregistration as p; from pathlib import Path; print(p.compute_content_hash(Path('docs/preregistration/PR-007-recommendation-constants-ablation.md')))"`
4. Replace `PENDING-FREEZE` with that value. Commit. **That commit is the freeze.**
5. `p.check_registration("PR-007")` must return `[]`. If not, stop and reply — do not run.
6. `p.require_confirmatory("PR-007")` at the top of the runner. Only then execute.

Any later edit without an `amendments:` entry is detectable and voids the registration. An
amendment made after seeing data irreversibly demotes this to `mode: exploratory`, with no override
and no judgement call available to whoever has the incentive to relitigate it.

---

## 13. Refusals, in writing

Stated so they are not later mistaken for things nobody thought of.

1. **A grid search over the constants' magnitudes** (find the best `+x / +y / −z` triple). Refused.
   With 3 seasons and a simulator whose dominant parameter is a guess, a search returns a fitted
   triple with no out-of-sample support and converts an *unfitted* guess into a *fitted* one that
   looks validated — strictly worse than the status quo, because it acquires false authority. If
   the constants die and a principled replacement is wanted, the replacement is a **model** (e.g.
   the continuous need model already sitting in `live_availability.n_need`), registered and tested
   on its own terms.
2. **Unsealing 2025** under this registration. Refused — §7.
3. **A DEF-term arm.** Refused as untestable; disposition decided on inspection (§4).
4. **Promoting any descriptive arm to a KEEP after the numbers are seen.** Refused in advance.
5. **Softening any threshold to make a pass more likely.** The floor is inherited from PR-003, the
   unanimity requirement is the same one PR-003 used to read its only non-noise result, and the
   expected verdict is deletion. None of it moves after the run.
