# ADR-DRAFT — Disposition of the oracle ladder

**Status:** Proposed (ruling issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-30
**Owner:** Strategist (ruling) / Ranker (correction to the artifact)
**Answers:** `docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md` item 4
**Subject:** `docs/ranking/fr136-q1-bottom-up-assessment.md` §4

---

## 0. The ruling

**REJECTED as a pre-registration.** It is not registered, not promoted, and no build effort may cite
it as a justification.

**RETAINED as a permanently-labelled exploratory artifact, with two mandatory corrections to the
artifact itself** (§3). The ranker was right to run it and right to flag it against itself; the
number is worth having on file. It is not worth having in a denominator.

**A narrow successor question is drafted in §5** — the *forecastable* share of the durability
channel, with a **predicted NULL** and a hard stopping condition. It converts to a numbered
pre-registration once the `PR-0NN` allocator gap
(`docs/handoffs/2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration.md`) is closed. It is
**not** registered by this ADR and no run may proceed under it.

---

## 1. Why reject, in three reasons of increasing weight

### 1.1 A pre-registration is a commitment to a test whose result can change a decision. This one cannot.

Both arms are evaluated at **target-season realised values**. Neither bounds a *forecastable*
quantity, and no achievable model is bounded by either. Knowing a player's realised per-game rate in
August is not a hard forecasting problem, it is clairvoyance about injuries, trades, coordinator
changes and in-season role. There is no configuration of the ladder whose outcome changes what gets
built.

### 1.2 Registering it would put twelve inert tests into the FDR denominator

Benjamini–Hochberg across the *true* total is a discipline that runs in both directions: real tests
must not be omitted from the denominator, and tests that cannot produce an action must not be added
to it. Twelve uncorrected oracle comparisons on 7 seasons, registered, would dilute every real test
in the family for no possible gain. That is a worse outcome than leaving them exploratory.

### 1.3 Registration would confer confirmatory status on a number certain to be quoted

"+0.35 to +0.44 ρ of room at every position" is exactly the kind of figure that survives into a
summary with its caveats stripped, and it points at a large build. The ranker's §4.1 disclaimer is
correct and thorough — and disclaimers travel worse than numbers do. Withholding registration is the
only mechanism that actually stops the figure being cited as established.

---

## 2. The defect the ranker did not catch on itself, and it is in the startling claim

The ranker flagged the **rate** oracle for sharing its numerator with the outcome (PPG = points ÷
games), and that flag is correct. It did **not** apply the equivalent scrutiny to the **games** oracle
— which is the arm carrying the claim the thread singles out as startling:

> *"perfect availability foresight alone, knowing nothing about talent, beats the entire expert
> consensus at all four positions."*

**`games = 0 ⟹ points = 0` is a deterministic identity.** The universe is an ADP board with busts
retained, so it contains a block of drafted players who never played, or played once or twice. Every
one of those is simultaneously at the bottom of the games ordering and at the bottom of the points
ordering **by arithmetic, carrying no information at all.** The games oracle scores those pairs
correct for free. Consensus, by contrast, has to *predict* who they will be.

So the comparison is not "the durability channel versus the talent channel." It is **"being told the
outcome's zero set versus having to guess it."** ρ(games, points) on this universe is inflated by the
mechanical zero mass, and the size of the inflation is a direct function of how many drafted players
recorded no season — a quantity nobody has reported.

The claim is therefore **priced down**, and the standing calibration prior applies to it directly:
"availability is the real driver" is a situation story, and four of five registered prediction sets
across sessions 3–4 were materially wrong with **every** miss over-crediting a situation story
(`docs/reviews/FABLE-EXT3-2026-07-27.md`). Half weight before registration, per standing discipline.
Half of "startling" is "interesting, and probably mostly an identity."

### 2.1 The decomposition diagnostic that settles it — and why it is permitted here

Re-run the games-played oracle restricted to players with **≥ 1 game played**, and separately report
**the fraction of each season's board universe that recorded zero games**, per position.

- If ρ collapses on the ≥1-game subset, claim (b) is mostly the identity.
- If it survives, the durability channel has real content and §5 is worth running.

**This looks like a forbidden filter and it is not, and the distinction must be stated or someone
will correctly cite ADR-B:54 at it.** ADR-B:54 forbids a minimum-games filter **in model
evaluation**, because it deletes the outcomes the model failed to anticipate and inflates measured
performance. Here the filter is applied to an **oracle arm**, purely to decompose that oracle's own
upper bound into an identity component and an information component. Conditions, all binding:

1. Permitted **only** on oracle arms, never on any model-evaluation arm.
2. Reported **alongside** the unrestricted number, never replacing it.
3. Labelled as a decomposition of an upper bound, never as a performance figure.

---

## 3. Two mandatory corrections to `fr136-q1-bottom-up-assessment.md` §4

### 3.1 The exploratory table carries confidence intervals it is not entitled to

§4 is declared exploratory in §7 (*"must not be quoted as a finding"*), and
`src/preregistration.py::validate_exploratory_artifact` exists specifically to forbid an exploratory
result carrying a CI, p-value or significance flag. The §4 tables carry **4,000-rep bootstrap 95%
CIs on all twelve comparisons.** That is an internal contradiction in the artifact, and CIs are the
single most effective way for an exploratory number to acquire the *appearance* of a finding.

> **Required: drop the intervals from §4's tables. Keep the point estimates. Keep the seven-season
> n. Add the §2 identity caveat to the games-oracle column.**

### 3.2 Two different things are both called "availability" and they are about to be confused

| Sense | Meaning | Where it lives |
|---|---|---|
| **Draft availability** | will this player still be on the board at my next pick | `availability.json`, the Monte Carlo sweep, the founder's Q2, thread `2026-07-30-availability-adp-measurements-m0-m5` |
| **Player durability** | how many games will this player actually play | assessment §4's games oracle, `component-model-rb-qb-te-pass-1.md` §5.1 |

The founder's dependency chain — bottom-up → availability → recommender — means sense 1. The oracle
ladder's startling claim is about sense 2. They are unrelated questions with unrelated data and
unrelated failure modes, and a sentence like "availability beats consensus at all four positions" is
one careless read away from being cited as a result about the draft-availability model.

> **Required: §4 and everything downstream of it say "durability" or "games played," never
> "availability," for sense 2.**

---

## 4. What is *not* rejected

The ranker's own reading of §4 — *"it bounds the room, not the reachable"* — is correct and this
ruling does not overturn it. Specifically retained as legitimate exploratory context:

- The rate-oracle result is a fair upper bound on *something*, and the fact that it sits at +0.35 to
  +0.44 against a component model delivering +0.051 at WR is a fair statement that projection is not
  a solved problem.
- The gap between the two oracles is a fair *descriptive* decomposition of season points into rate
  and games, which is a true identity and a reasonable way to look at the problem.

What is rejected is only: registration, confirmatory status, quotation as a finding, and the
inflated games-oracle reading in §2.

---

## 5. Successor registration text — NOT registered, pending a `PR-0NN` id

Drafted here rather than in `docs/preregistration/` because **no allocator exists for `PR-0NN` ids**
(three sessions have now hit this; thread
`2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration.md` is open). Hand-numbering it would
repeat the collision class that already hit threads 043/049/053 and ADR-048. It moves into
`docs/preregistration/` verbatim, with an allocated id and a computed `content_hash`, once that
thread closes.

**Status: DRAFTED, NOT REGISTERED. No run may proceed under it. It is in no FDR denominator today.**

| Field | Value |
|---|---|
| **family** | `F-DURABILITY` (new; manifest `m = 4`, one per position) |
| **mode** | confirmatory |
| **question** | Does adding a **pre-season-observable** durability feature set to the board's ranking improve the realised roster value of the resulting board, at QB/RB/WR/TE independently? |
| **feature set (frozen before any run)** | Prior-3-season games played, prior-season games missed, and games-missed trend — **all computable strictly before Week 1 of the target season.** No in-season information. No injury designation from the target season. Nothing else may be added without a new id |
| **metric** | Primary: paired `top_k_starter_vbd` (durability-adjusted board − incumbent board), per season, season-level bootstrap 95% CI. Diagnostic: per-position τ_b delta |
| **threshold** | ADOPT at position `p` iff paired mean > 0 **and** the season-bootstrap 95% CI excludes 0 **and** per-position τ_b degrades by ≤ 0.02, with bootstrap p surviving BH at α = 0.05 across m = 4 |
| **data scope** | 2018–2024. **2025 sealed; `holdout_unsealed: false`; this registration does not authorise an unseal** |
| **resampling unit** | season |
| **blocked on** | the primary-metric ruling's preconditions A and B. **This test is graded on `top_k_starter_vbd` and precondition A's defect is precisely a durability defect** — a never-played player scored at 0 VBD instead of −replacement. Running a durability test on the unfixed metric would be a closed loop |

### 5.1 Registered prediction, before the run

> **NULL at all four positions.**

Reasons, stated so a positive result has to argue against them: every availability arm already tried
measured null on ranking (`component-model-rb-qb-te-pass-1.md` §5.1); the durability oracle's
apparent size is substantially the §2 identity; and the standing calibration prior discounts
situation stories by half, of which "durability is undervalued by the market" is a clean example.

**Stopping condition:** if no position clears, the durability channel is closed as a 2026 product
input, the family is set to `closed`, and the finding is written as a null. **No re-run with a
different feature set before 7 September** — that would be a new id, incrementing `m` and
re-triggering BH across the family.

### 5.2 Coordination note

`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md` already carries an in-flight
registration in the **draft-availability** sense (§3.2 above). `F-DURABILITY` is a distinct family
measuring a distinct quantity and must not be folded into it. If a future session finds the two
families overlapping in any shared test, they merge into one family with one denominator — double
counting across families is the same error as omitting from one.
