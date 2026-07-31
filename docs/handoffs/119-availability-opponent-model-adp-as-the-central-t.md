---
ID: 119
FROM: pm
TO: strategist
STATUS: RESOLVED
BLOCKS: FR-066 (browser-side availability recompute), thread 104, FR-131
OPENED: 2026-07-30
---

## Ask

**Should the availability opponent model draft from ADP rather than expert consensus, and should its
sigma be per-player rather than one global guess?**

Founder's words: *"Availability is probably more related to ADP than consensus."* Full write-up and
the measurements: `docs/founder-requests/FR-131-*.md`. Do not re-derive them.

Three decisions, in dependency order. Answer all three; the third is the one most likely to be got
wrong quietly.

### 1 · Central tendency — ADP or expert consensus?

`simulate_availability` runs its opponent model, **and the user's own BPA strategy**, off
`rankings WHERE source='fantasypros_ecr'` (408 players, `as_of` 2026-07-24). The board runs off
`fantasypros_csv_2026draft` (538, 2026-07-27). **73 of the 80 players in `availability.json` have a
different consensus rank between the two.**

`ffc_adp_snapshots` holds `half-ppr`, `10 teams`, `as_of 2026-07-29` — this league's exact format,
180 players, and fresher than either ranking source.

The founder's argument, which I think is correct and want you to attack rather than ratify:
availability asks what drafters *do*; consensus describes what analysts *think*. Modelling opponents
off consensus models them as drafting correctly.

**What I need:** a recommendation with the failure mode named. Specifically — is FFC's drafting
population representative of a Yahoo room? The founder's two Yahoo mock drafts are logged
(`data/mock-drafts/yahoo-{10team-slot4,12team-slot2}-2026-07-30.json`, 291 resolved picks) and are a
real, if small, check available to you.

### 2 · Dispersion — per-player `std_dev` or one global sigma?

Not asked for by the founder; it fell out of checking whether (1) was feasible, and it may be the
larger win.

The exported metadata states plainly that sigma *"is a guess, not fitted to observed drafts."*
`ffc_adp_snapshots` carries a measured per-player `std_dev`. In this league's format:

| min | median | max |
|---|---|---|
| 0.4 | 9.7 | 39.2 |

Median ≈ the default guess of 10, which is a point in the guess's favour. The **spread** is the
finding: Bijan Robinson sd 0.7, Alvin Kamara sd 26.2. A single global sigma treats them as equally
unpredictable, by a factor of forty.

This bites hardest on the exact question the founder uses the number for — *will he last until my
next pick* — which is dominated by dispersion, not central tendency.

**What I need:** does per-player dispersion transfer from FFC to a Yahoo room, in absolute terms or
only in shape? A relative-dispersion mapping that preserves ordering may be defensible where absolute
values are not.

### 3 · How per-player sigma composes with the shared room-noise draw

The model currently draws **one** Gaussian(0, sigma) per player, **shared by the whole room** for a
single simulated draft — deliberately, per `client_simulation_parameters.room_noise_note`: this
models *"the room collectively valued him a round higher this year"*, not nine independently confused
teams.

**Per-player sigma must compose with that, not silently replace it.** Substituting a per-player
sigma into the shared draw changes the correlation structure across the room, and I do not want that
happening as an implementation side effect. State explicitly what the intended generative model is.

## Why

Three things are blocked on this and all three are the founder's own asks:

- **FR-066 / thread 104** — browser-side availability recompute when he changes draft slot. A working
  prototype ran in under 5 seconds; it was **not shipped** because the frontend has no honest source
  for the rank the model runs on. If the answer here is ADP, the export needed changes, and thread
  104's ask should be reformulated before backend builds the wrong field.
- **FR-131** — this.
- **FR-128** — availability is empty for all 24 non-primary leagues. Re-running it there costs
  compute; nobody should pay that cost for a model that is about to change its inputs.

The founder has been told repeatedly that availability is the project's most reliable output —
because it never passes through the projection curve. **That claim is doing real work in how much he
trusts the number, and it is only as good as the opponent model underneath it.** If the model is
running on a superseded ranking and a guessed dispersion, the claim is weaker than it has been
stated, and he should hear that from us rather than discover it.

## Done looks like

A written recommendation on all three questions, with:

- The failure mode named for whichever option you recommend — not just the case for it.
- An explicit statement of the generative model for (3).
- A pre-registered test, if you believe the change should be validated before shipping rather than
  argued. `docs/statistical-guardrails.md` and the PR-00x series are the pattern.
- Whether ADR-035's binding constraint — a proxy ADP must **never** be presented as this league's
  own ADP — extends to FFC half-PPR 10-team, which is materially closer to Westwood than MFL but
  still not his draft room.

**Note on ADR-018**, so it is not re-litigated from the old text: it concluded no market ADP was
legally obtainable, FFC included, under a redistribution framing the founder corrected today.
Nothing here is redistributed, the site is password-gated, personal use is the posture, and FFC data
is already captured on a schedule. The licensing question is closed; the methodology question is
yours.

---

### strategist · 2026-07-30

**No database access, by design.** Everything numeric below is computed by hand from committed
artifacts — `data/adp-snapshots-ffc/2026-07-{29,30}_half_ppr.csv` and
`data/mock-drafts/yahoo-10team-slot4-2026-07-30.json`. Nothing here re-derives FR-131's figures;
where I quote them I quote them to attack them. Every number is reproducible by reading those three
files. Guardrails applied and named per-claim in §6.

#### Verdict

| Q | Answer | The failure mode I am accepting |
|---|---|---|
| **1 · central tendency** | **Yes — switch the opponent model to `ffc_half_ppr_10team`.** But *not* for the reason given, and not as a mixture. | **Staleness under news shock.** FFC ADP is a 5-day trailing mean of completed drafts (`sample_window` in the CSV: "July 25, 2026 to July 30, 2026"). An injury three days before the draft is fully priced in ECR and only ~40% priced into ADP. Mitigation is mandatory, spec'd in §2. |
| **2 · dispersion** | **Yes to per-player dispersion — no to FFC's raw `std_dev`.** Ship `sigma_i = λ · ĝ(adp_i)`, a fitted monotone curve normalised to mean 1, with `λ` staying on the existing sweep. Per-player *residual* dispersion ships only if it survives an EB test with a pre-committed null-accepting rule. | **The shape is real, the level is not transferable, and the residual is probably nothing.** If I am wrong it is because I under-credited genuine per-player disagreement; the EB test in §3 is what catches that. |
| **3 · composition** | **Scale the existing shared draw. Do not add a second draw.** `effective_rank[t][i] = base_i + λ · s_i · z_i`, `z_i ~ N(0,1)` drawn **once per player per draft, shared by all teams**. Cross-team correlation stays exactly 1. Generative model written out in §4. | **The model still asserts zero manager-idiosyncratic dispersion.** That is an unmeasured assumption, not a finding, and I am recommending it be kept *by decision* with a named future test — not by inertia. |

Plus a fourth thing you did not ask and should have: **switching to ADP makes the Prep-mode
unconditional marginals nearly closed-form.** See §5. That bears directly on FR-128.

---

#### 1 · Where the PM/founder argument is right, and where it is wrong

**Right, and stronger than stated.** ADP is not "a better ranking." It is a *measurement of the
quantity the model needs* — realised pick position — on the correct scale (picks), carrying an
uncertainty. ECR is a measurement of a different quantity (analyst opinion) on an ordinal scale
carrying no uncertainty at all. Even if the two orderings correlate at 0.95, only one of them can
ever be checked against reality. That is an **estimand** argument and it survives every empirical
result below. Use it; it is the durable one.

**Wrong, and it matters.** The thread frames this as "is FFC's drafting population representative of
a Yahoo room?" That question cannot be answered and is not the bar.

- **It cannot be answered from what exists.** Two logged Yahoo mocks is **n = 2 rooms**. The correct
  resampling unit here is the *room*, not the pick — 291 picks inside two rooms is two observations
  with 291 correlated coordinates. No confidence interval is claimable at n=2, and I will not
  produce one. The mocks can **falsify** (a terrible fit would have been decisive against FFC) but
  they cannot confirm.
- **The sample is contaminated in an unknown proportion.** Yahoo mock-draft lobbies fill unclaimed
  seats with autopick bots drafting off *Yahoo's own preseason ranking* — which is an expert
  consensus, not an ADP. The 10-team file records ten manager handles and gives no way to tell
  which were human. If most seats were bots, a high mock↔FFC-ADP correlation partly measures
  "Yahoo's expert list ≈ FFC's ADP", which if anything argues the two inputs are near-substitutes
  at the ordering level and weakens the case rather than strengthening it. Nobody has established
  the human fraction; nobody currently can.
- **Neither source is "representative" of Westwood.** The founder's room is nine specific people and
  we have zero drafts from it. There is no representative source, only a choice among proxies. The
  choice should be made on estimand and measurability — which ADP wins outright — not on a
  representativeness claim no one can support.

**And the decisive comparison has never been run.** `docs/analysis/founder-mocks-2026-07-30.md`
reports the mocks against FFC ADP at ρ = 0.9485 (half-PPR) and **against no ranking source at all**.
A candidate reported without its incumbent baseline is exactly what guardrails §5 forbids. ρ = 0.95
against ADP is meaningless until you know that ECR scores 0.91 or 0.96 on the same picks. That is
measurement **M1** in the backend thread.

**What the mocks *can* tell you, and do.** Round-by-round mean absolute deviation of realised pick
from FFC half-PPR ADP, 10-team mock, all 30 picks of rounds 1–3, hand-computed:

| Round | mean \|pick − ADP\| | implied σ̂ = MAD/0.798 | mean FFC `std_dev`, same 10 players |
|---|---|---|---|
| 1 | **1.12** | 1.40 | 1.38 |
| 2 | **3.66** | 4.59 | 3.16 |
| 3 | **8.22** | 10.30 | 4.79 |

Two independent populations, and the **shape agrees**: dispersion rises steeply with ADP position in
the Yahoo room exactly as it does in the FFC market. The **level diverges progressively** — the
Yahoo room is ~1.0× / 1.45× / 2.15× FFC's dispersion by round. That is the answer to your "absolute
terms or only in shape" question, measured rather than asserted.

Caveat I will not hide: within one draft the deviations must roughly cancel inside a round (ten
players whose ADPs average ~6 must occupy picks 1–10), which biases MAD *down*, hardest in round 1.
So the R1 figure is partly artefactual. **The robust claim is the gradient: R3/R1 = 7.3×**, and the
cancellation bias makes that an underestimate. A global sigma is unambiguously wrong, in the
direction you suspected.

**Recommendation: full switch on the covered range, not a mixture.** ADR-034's `source_weights`
machinery invites a blend and the blend is wrong here. ADP *is already* the aggregate over drafter
types — some managers draft off a site list, some off ADP, some off their own board. Layering ECR
back in as a mixture component double-counts the population ADP already integrates over. ECR appears
only as a **coverage patch** in the tail (§2 of the backend thread), which is a different thing and
must be labelled as one.

**Three things the switch must carry with it, or it introduces new defects:**

1. **The user's own arm must split off.** `simulate_availability` currently runs *both* the opponent
   model and `strategy_bpa` off the same `data.consensus_rank`. Post-switch, opponents ← ADP, and
   the **user ← the board** (`fantasypros_csv_2026draft`). Thread 104 already caught that
   `algorithm_note` claims the user drafts off `board.json` and the code does not. The correct
   resolution of FR-131 is what finally makes that sentence true. Do not let one array quietly
   become the ADP array for both arms.
2. **Unit conversion is not optional.** FFC's `average_pick` counts kickers and defenses (Brandon
   Aubrey ADP 132.0, Evan McPherson 162.7); `draft_sim`'s universe is QB/RB/WR/TE only, and Westwood
   has no kicker slot. Raw FFC pick numbers are on a different axis from Westwood pick numbers before
   any population question arises. Also: FFC `low_pick` values reach 17.05 / 17.12 / 18.03, so the
   sample includes drafts deeper than Westwood's 16 rounds — which stretches the tail and inflates
   late-round `std_dev` relative to a shorter draft. Both corrections are spec'd as **M4**.
3. **Staleness mitigation.** Export `sample_window`, `as_of_date` and `times_drafted` per player, and
   surface any player whose board rank and ADP rank diverge beyond a threshold as *"the market has
   not moved on this yet"* rather than silently trusting ADP. This turns the switch's main failure
   mode into a visible feature.

---

#### 2 · Dispersion: adopt the shape, refuse the raw numbers

FR-131 presents `std_dev` as a measurement replacing a guess. It is a measurement, but it is
presented **without an n and without a standard error**, which the evidence-standards table
forbids for a statistical constant. Three findings from the committed CSVs.

**(a) The per-player n is small, varies ~20-fold, and its meaning is not established.**
`times_drafted` in the 2026-07-30 half-PPR file ranges from **7 to 256** with a typical value around
60–90. Sampling error on a standard deviation is ≈ `s/√(2(n−1))`: at n = 12 that is a 21% relative
error, at n = 28 it is 14%. None of that appears in FR-131.

Worse, **the field's semantics do not reconcile.** Every row carries
`total_drafts_in_sample = 1254`, yet Bijan Robinson — who goes at pick 2.0 in essentially every
draft — shows `times_drafted = 90`, while kicker Brandon Aubrey shows 212 and Brock Bowers 225.
Those cannot be per-draft counts on a shared denominator. Between 07-29 and 07-30 Ja'Marr Chase's
count went **down** (189 → 175) while `total_drafts_in_sample` went **up** (1187 → 1254). Until
someone reconciles what these two columns mean against FFC's own documentation, **every per-player
n, every standard error, and every weight in a shrinkage scheme is unfounded.** This is a hard gate
(**M0**), not a caveat.

**(b) The day-over-day instability is concentrated in exactly FR-131's four headline players.**
Same source, same format, one day apart:

| player | `std_dev` 07-29 | `std_dev` 07-30 | Δ | n (07-30) |
|---|---|---|---|---|
| Jahmyr Gibbs | 0.6 | 0.6 | 0% | 158 |
| Bijan Robinson | 0.7 | 0.7 | 0% | 90 |
| Ja'Marr Chase | 1.5 | 1.5 | 0% | 175 |
| Brock Bowers | 10.1 | 10.4 | +3% | 225 |
| George Kittle | 26.9 | 24.9 | −7% | 56 |
| Evan McPherson | 39.2 | 36.4 | −7% | 12 |
| Hunter Henry | 28.0 | 24.8 | −11% | 12 |
| **Alvin Kamara** | **26.2** | **19.0** | **−27%** | **28** |

FR-131's "the room does not agree" exhibit — Kamara, Kittle, Hunter Henry, McPherson — is precisely
the set that moved most, and the set with the smallest n. The "factor of forty" headline is, one day
later, a factor of twenty-seven. The mandate's own summary row (min 0.4 / median 9.7 / max 39.2) is a
07-29 vintage; the 07-30 file has min ≤ 0.3 and max 36.4. **These are not stable constants to hardcode.**

**(c) The spread is mostly a deterministic function of ADP position, not player-specific
disagreement.** From the same file, `average_pick → std_dev`: Bijan 2.0→0.7, CMC 5.0→1.5,
Henry 10.6→2.1, Breece 28.7→2.9, Bowers 44.5→10.4, Sutton 66.8→8.8, Caleb Williams 96.9→15.7,
Kittle 117.0→24.9, Strange 145.8→26.9, Kamara 156.1→19.0 — near-monotone, then compressing at the
extreme tail through censoring (Christian Kirk 194.7→7.7, drafted only in drafts that run that
deep). Bijan's dispersion *cannot* be large: pick 1 is a hard floor. Almost all of the
Bijan-vs-Kamara contrast is "ADP 2 vs ADP 156", not "the room is confused about Kamara."

This is my standing calibration prior biting exactly where it is supposed to: the intuitive story
("the market genuinely disagrees more about some players") is a situation narrative and should be
priced at half weight before it becomes a pre-registration. The half-weight version is: **most of the
spread is a smooth heteroskedasticity curve; the player-specific residual is small and may be zero.**
The project has been here before — FR-086's empirical-Bayes τ̂² for per-player scoring shape came out
at exactly zero. Use the same estimator.

**(d) The median-9.7-validates-sigma-10 argument does not hold.** That median is taken over all 180
rows including PK, DEF and the entire tail. Availability only tracks the **top 80**. Over the
players in roughly ADP 1–90 the typical `std_dev` is ~4–5, not ~10. Combined with the mock evidence
in §1, my directional pre-commitment is: **the fitted global scale λ̂ will come out below 10 for the
range the model actually reports** — i.e. current availability probabilities for top-80 players are
systematically too close to 50%, the model is more uncertain than the market is, and the honest sweep
may be nearer 2 / 5 / 10 than 5 / 10 / 20. Registered before the run, in
`docs/ranking/availability-opponent-model-precommit.md`. Noting for the record that this is an
*arithmetic* prediction, not a situation story — the category that has held up in my prior sessions.

**What to ship.** `sigma_i = λ · s_i` where `s_i = ĝ(adp_i) / mean(ĝ)` is a fitted monotone curve
normalised to mean 1, and `λ` stays the swept global scale in picks — so the founder's existing
"every number at three settings" honesty device survives intact and λ̂ is directly comparable to
today's 10. Per-player residual multipliers ship **only** if empirical-Bayes τ̂² is bounded away from
zero, EB-shrunk, with the shrinkage factor reported per player. If τ̂² is not, the export says so
explicitly: *"per-player dispersion beyond the ADP-position effect was tested and found
indistinguishable from sampling noise."* Decision rules pre-committed in the precommit doc.

**Do not substitute observed `std_dev` into the noise term.** This is the quiet error I most expect.
FFC's `std_dev` is the dispersion of a player's *realised* pick across drafts — an **output**. The
simulator's sigma is a **latent board perturbation**, and the simulator's own sequential mechanics
(need penalties, players being taken, snake order) add variance on top of it. Setting
`sigma_i = std_dev_i` will over-disperse, and it will look plausible while doing so, because
availability probabilities pushed toward 0.5 read as admirable humility. The correct procedure is
method-of-moments *through the simulator* (**M3**): pick λ so that the simulated distribution of
realised picks reproduces the observed `std_dev`. A pre-registered sanity check: λ̂ **must** come out
below the observed pick sd. If it does not, the mechanics are wrong and nothing ships.

---

#### 3 · The generative model, written out

This is the one you flagged as most likely to be got wrong quietly, so it is stated as equations,
not prose.

**Today (unchanged behaviour):**

```
z_i             ~ N(0, 1)          # once per PLAYER per simulated draft
room_noise_i     = sigma * z_i     # sigma: one global scalar
effective_rank[t][i] = base_rank[source(t)][i] + room_noise_i     # same z_i for every team t
```

**Intended, after this change:**

```
z_i             ~ N(0, 1)          # STILL once per player per draft, STILL shared by all teams
s_i              = ghat(adp_i) / mean(ghat)      # per-player relative dispersion, mean 1
room_noise_i     = lambda * s_i * z_i            # lambda: the swept global scale, in picks
effective_rank[t][i] = adp_i + room_noise_i      # opponents
user_board                       = board.json consensus_rank      # the USER's arm, separately
```

**The invariant that must hold and must be tested:**
`Corr(effective_rank[t1][i], effective_rank[t2][i]) = 1` for every pair of teams `t1, t2`, before
the need penalty — exactly as today. Per-player sigma **rescales the marginal** of an existing
shared draw. It does **not** introduce a second, per-team draw.

**The alternative that must not be adopted as an implementation side effect:** drawing
`z_{t,i} ~ N(0,1)` independently per team. That sets cross-team correlation to 0, which is a
different model with different predictions in both directions — it *lowers* the variance of the
realised pick (nine independent opinions average out, so the earliest-reacher determines the pick
with less draft-to-draft swing) while *raising* the entropy of which team takes him. Those are not
near-equivalent parameterisations and the difference is not an implementation detail.

**What the shared-only structure is actually asserting.** Observed across-draft dispersion has two
components: a **room-level** part (this week the market moved on him) and a **manager-level** part
(manager A loves him, manager B does not). The current model contains only the first. FFC's aggregate
feed can never separate them — it never exposes within-draft variation across seats. **The founder's
~30-mock programme is exactly the instrument that can**, because `mock_picks` stores per-`team_slot`
sequences. Until then the shared-only structure stays, **by decision with a named future test**, not
by inertia. Registered as the deferred arm in the precommit doc; not in this change's BH family.

---

#### 4 · ADR-035's constraint: yes, it extends, and it needs one extra clause

**FFC half-PPR 10-team must never be presented as Westwood's ADP.** It is materially closer than MFL
— same scoring family, same team count, 1,254 drafts against MFL's 50 — and that closeness makes the
mislabelling *more* likely, not less. Measured differences that change pick position, all from the
committed files:

- **Roster shape.** FFC's default 10-team lobby rosters kickers and defenses; Westwood has neither a
  kicker slot nor 15 rounds of that shape. Removing K/DEF demand pushes ~10–15 picks of skill-position
  demand into the late rounds. Every FFC pick number past ~100 is on a different axis.
- **Round count.** FFC `low_pick` reaches 18.03. Westwood's sim is 16 rounds. The tail is not comparable.
- **Population.** FFC drafters are self-selected and high-engagement; Westwood is nine specific
  people. Unmeasured and unmeasurable from here.

**The label test, which I want applied literally:** *could the founder read this number and come away
believing it describes his nine leaguemates?* If yes, the label fails. Required wording carries the
source, format, window and n — e.g. *"market ADP · Fantasy Football Calculator · 10-team half-PPR ·
1,254 drafts, 25–30 Jul 2026 · not Westwood's own draft room."* And one clause ADR-035 did not need
but this does: **FFC pick numbers include kickers and defenses; Westwood's do not, so an FFC pick
number is not comparable to a Westwood pick number even before the population question.**

**On the "most reliable output" claim.** PM is right that the founder should hear this from us.
The precise honest statement, which I would put in his hands: *availability does not inherit the
projection model's error — that part was always true — but it has its own error, and until now that
error came from an admitted guess and a superseded ranking, so the claim was doing more work than it
had earned.* After this change it gets **stronger**, for the first time on evidence rather than
architecture: the dispersion has a measurement behind it. That is a better thing to tell him than
either the old overclaim or a retraction.

---

#### 5 · The thing nobody asked, which changes the shape of FR-066 and FR-128

If opponents draft from ADP with per-player dispersion, then for the **unconditional Prep-mode
marginals** the simulator is an expensive way to reproduce something FFC already publishes:

```
P(player i still on the board at pick p)  =  P(his realised pick > p)  =  1 - F_i(p)
```

and FFC hands you `average_pick`, `std_dev`, `high_pick`, `low_pick` per player. A fitted parametric
(or better, a bounded/skewed) CDF gives `by_player` in closed form, on the corrected no-K/DEF pick
axis, with no Monte Carlo at all.

Three consequences, all of them things the founder has already asked for:

- **FR-128** (availability empty for 24 non-primary leagues, and ADR-061's 628s-per-league sweep) —
  the unconditional case collapses to arithmetic. The compute objection largely evaporates.
- **FR-066 / thread 104** — a browser-side recompute of the *unconditional* numbers for an arbitrary
  slot needs no Monte Carlo port at all, only the per-player `(adp, sigma)` pair. **Thread 104 should
  be reformulated before backend builds the field it currently asks for:** the right export is
  `{adp_pick, sigma_pick, coverage_flag}` per player on the Westwood pick axis, not the raw ECR rank
  array it requests today.
- **A free acceptance test.** The simulator's unconditional marginals must reproduce the closed form
  within Monte Carlo error. If they do not, the mechanics are miscalibrated and the discrepancy
  localises the bug. Make this a required acceptance criterion, not an optional check.

The simulator keeps earning its keep exactly where the closed form cannot go: **conditioned on live
draft state** — who is already gone, what each team already rosters. Which is what
`marginals_note` already says the parameters are for.

---

#### 6 · What I am refusing, in writing

1. **Fitting any parameter to the two logged mocks.** n = 2 rooms, unknown human/bot fraction,
   neither matching Westwood's roster shape. λ, a mixture weight, or a shrinkage factor fitted on
   that is a fabricated constant. The mocks are admissible as a **falsification check and a
   shape-transfer check** — which is how I used them above — and nothing more.
2. **Any confidence interval computed at the pick level on the mock data.** The resampling unit is
   the room. With two rooms there is no interval to report and I will not manufacture one by
   resampling picks, which would produce a tight, confident, meaningless number.
3. **Raw per-player `std_dev` as the shipped sigma**, for the three reasons in §2 and because M0 is
   unresolved.
4. **Treating "FFC is representative of a Yahoo room" as a question with an answer.** It is not
   answerable from anything that exists. I have replaced it with a question that is (M1).
5. **Thread 114 stays OPEN and is not answered here.** Its Steiger/Hittner separability test on
   ρ = 0.9333 / 0.9485 / 0.9541 needs the paired per-pick vectors, which requires a query I cannot
   run. Partial read that does fall out and should not be lost: the three formats' ADP orderings are
   near-collinear by construction, so at n ≈ 130 the half-PPR-vs-PPR gap of 0.006 is very unlikely
   to be separable — but "unlikely" is not a test result and I will not report it as one. M1 in the
   backend thread produces the vectors that settle it; route 114 to whoever picks that up.

**Guardrails applied** (§ numbers from `docs/statistical-guardrails.md`): §5 baseline rule — the
missing ECR baseline is the single largest gap and is the first measurement requested. §7 uncertainty
— every FR-131 figure I attack, I attack for having no n and no SE; my own mock figures are stated
without CIs *and the reason is named*. §3 pre-registration and BH — the family is declared with its
denominator before any run. §3 autocorrelation — the resampling unit is the room/draft, stated
explicitly. §11 reproducibility — seed policy fixed in the precommit doc. §1 look-ahead — not
applicable, no outcome data is involved anywhere in this change, which is the same property that
makes availability trustworthy in the first place.

---

#### 7 · Artifacts produced this session

| File | What it is |
|---|---|
| `docs/ranking/availability-opponent-model-precommit.md` | Full pre-registration: measurements M0–M5, hypotheses, decision rules, BH family and denominator, seed policy, resampling units. **Written before any run.** |
| `docs/adr-drafts/ADR-DRAFT-availability-opponent-model-source-and-dispersion.md` | The ADR draft with pre-committed decision rules, for allocation via `python tools/handoffs.py adr next`. |
| `docs/handoffs/NEW-availability-adp-measurements-m0-m5.md` | Staged thread body to `backend` carrying M0–M5 as runnable specs. Needs `python tools/handoffs.py sync` to allocate. |

**I cannot commit and cannot allocate an ID — no Bash, by design.** PM: run
`python tools/handoffs.py sync` to land the backend thread, `python tools/handoffs.py adr next` for
the ADR number, and regenerate `OPEN.md` (I made the minimal hand-edit so it is not stale, but sync
is authoritative).

**Ordering for whoever picks this up: M0 gates everything.** If `times_drafted` /
`total_drafts_in_sample` do not reconcile, stop — the dispersion half of this change has no measured
foundation and only the central-tendency half should proceed.

**STATUS: RESOLVED.** All three questions answered, failure modes named, generative model stated,
pre-registration written, ADR-035 extension ruled on. What remains open is measurement, not
methodology, and it lives in the backend thread.
