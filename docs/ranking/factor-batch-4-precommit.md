# Factor batch 4 — pre-commitment (RB workload hangover, and the gate-vs-weight question)

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted. NOT YET RUN.**

Registers `FR-2026-07-30-rb-workload-hangover-decline-after-350-375-400-c.md` as its own family,
separate from batch 3's — batch 3 was pre-registered and running when this arrived, and adding an arm
mid-flight is precisely the multiplicity failure a pre-commitment exists to prevent.

> Founder, verbatim: *"If we don't have it, running backs coming off of high carry years
> (350/375/400)."*

**Blocked on `strategist` before it runs.** §2 contains a measurement that makes the founder's own
thresholds untestable as stated, and §4 contains an identification problem I do not think I should
resolve on my own authority. Both go to `strategist` first.

---

## 1. What this is, and the one thing that makes it worth a slot

The "Curse of 370" in its classic form. `CLAUDE.md` §11: *"Everyone knows X" is a hypothesis to test.*

The FR's own framing is the reason it earns a slot over any remaining sweep row: **every factor this
project has tested is a continuous weight. This is a gate.** If a threshold works where a smooth
weight does not, that is a finding about *model shape*, and it is worth more than the factor. The
only other gate on the list — N29's team passing-volume floor — is also untested, so batch 4 tests
**two gates at two positions**, each against its own continuous counterpart, and the gate-vs-weight
contrast is the headline rather than a by-product.

---

## 2. THE MEASUREMENT THAT COMES FIRST, because it changes the question

Counted before any arm was designed, `player_weekly_stats`, REG, position RB:

| lag-1 season carries | player-seasons **1999–2024** | player-seasons in the harness's **lag-1 window, 2013–2023** |
|---|---|---|
| ≥ 300 | 129 | **17** |
| ≥ 325 | 71 | **6** |
| **≥ 350** | **26** | **2** |
| **≥ 375** | **9** | **2** |
| **≥ 400** | **2** | **0** |

By era, ≥350: **1999–2007: 20 · 2008–2012: 4 · 2013–2018: 1 · 2019–2024: 1.**

**The founder's three thresholds cannot be tested on the modern sample. Two of them have n = 2
treated player-seasons and one has n = 0.** That is not underpowered; it is undefined.

**This is itself the first finding of batch 4 and it must be reported as one:** the workload the
hypothesis is about has been coached out of the league. A 350-carry season is a 1999–2007 artefact.
`CLAUDE.md` §6.4's regime-change warning applies to the *treatment* here, not just to the
coefficients — the thing being asked about barely exists any more, which is a genuine answer to
*"should I fade a back coming off a huge year?"* even before any model is fitted.

**Consequence, decided before fitting:** the primary threshold is **≥ 300 carries**, the only one with
a usable modern n, with 325 and 350 as declared secondaries and 375/400 reported as **descriptive
only, never as tests**. The deep 1999+ sample is used for the descriptive arm, where the thresholds
do exist, and is labelled a different regime rather than pooled.

---

## 3. Endpoints

| | |
|---|---|
| **E4a** | Next-season **fantasy points under this league's rules**, full frozen universe, busts retained at 0. Arm − primary, paired by season, season-block bootstrap 4,000 reps |
| **E4b** | Next-season **games played** — the injury mechanism the hypothesis actually asserts, isolated from the volume one |
| **E4c** | The same on the ADP board (7 seasons), a required direction check, not the significance test |
| Holdout | 2025 sealed. Not opened |

Universe, survivorship and look-ahead are the existing harness's, unchanged. **The FR is right that
survivorship bites harder here than anywhere tested so far** — a back who takes 380 carries and is
finished is a back who *earned* 380 carries — and the frozen-universe-with-busts-at-0 construction is
exactly the guard for it. **No arm may restrict to backs who played season N.**

---

## 4. THE IDENTIFICATION PROBLEM, stated rather than papered over

Season-total carries is *per-game carries × games played*. The model already holds both
(`carries_pg_w`, `gshare_w`). **So there is no variation in season-total workload that is independent
of the rate and the availability the model already prices**, and "match on age and talent, compare
high-carry to low-carry" cannot be done without matching away the treatment.

**The well-posed version of the founder's question is therefore a functional-form question, and that
is how it is registered:**

> Does a **threshold indicator** on lag-1 season-total carries add anything **beyond a smooth
> function of the same quantity**?

That is answerable, it needs no matching, and it is the same question as "do gates work where weights
do not." **I believe this is the right reformulation and I also think it is exactly the kind of
decision that should not be mine.** `strategist` rules before any arm is fitted.

---

## 5. The arms — declared in full, m = 8

Each is one feature block added to the named volume spec; everything else in the pipeline is
untouched, exactly as batches 1–3.

| # | id | hypothesis | pos | block | spec | endpoint |
|---|---|---|---|---|---|---|
| 1 | **W0** | the **WEIGHT**: smooth lag-1 season-total workload | RB | `car_tot_1`, `car_tot_1²` | `carries_pg` | E4a |
| 2 | **W1** | the **GATE**, primary threshold | RB | `hi300_1` **on top of W0's smooth terms** | `carries_pg` | E4a |
| 3 | **W2** | gate, secondary | RB | `hi325_1` on top of W0 | `carries_pg` | E4a |
| 4 | **W3** | gate, secondary | RB | `hi350_1` on top of W0 | `carries_pg` | E4a |
| 5 | **W4** | **cumulative wear** — a different mechanism, not a robustness check | RB | `car_tot_1 + car_tot_2` smooth | `carries_pg` | E4a |
| 6 | **W5** | the **injury** mechanism, isolated | RB | `hi300_1` added to availability arm A | availability | **E4b** |
| 7 | **G1** | N29 **gate**: club passing-volume floor | WR | `low_pass_team_1` (club lag-1 passing yards/game ≤ **225**) | `tpg` | E4a |
| 8 | **G2** | N29 **weight**: the same quantity, continuous | WR | `team_passyds_pg_1` | `tpg` | E4a |

**W1–W3 are tested ON TOP OF W0's smooth terms.** A gate that only beats a model with no workload
term at all would be answering a question nobody asked. This is the entire design.

**The 225 yards/game floor is fixed now and is measured, not chosen for effect:** club passing yards
per game, 2013–2023, has percentiles 5th = 199.2, 10th = 205.5, **25th = 223.2**, 50th = 248.6. The
gate is set at the 25th percentile, rounded.

**m = 8, BH at q = 0.10 across all 8, denominator fixed regardless of how many compute.** This is a
separate family from batch 3's 24 and is not pooled with it.

Reported **outside the family, descriptive, carrying no claim**: the 1999–2024 deep-sample
threshold table at 350/375/400, and the era decomposition in §2.

---

## 6. Decision rules

Batch 3's vocabulary unchanged (SURVIVES / PROJECTION-ONLY / BOARD-NEUTRAL / HARMFUL / MARGINAL /
NULL), plus the one this batch exists to produce:

| grade | rule |
|---|---|
| **GATE BEATS WEIGHT** | W1 (or G1) BH-significant better **while W0 (or G2) is not** — the threshold carries information the smooth term cannot |
| **WEIGHT BEATS GATE** | the reverse |
| **BOTH / NEITHER** | as measured |

**Stated before measurement, and this is the one that costs me something:** if W0 and W1–W3 are all
null, the answer to the founder's question is *"no, and the workload you are asking about no longer
happens"* — and **batch 4 does not get a second specification**, exactly as #29 did not get a third.

**Coverage/leak discipline carries over unchanged from batch 3:** any `*_known` companion flag is
registered as its own control arm in the family, the 50% VOID rule applies, and the 2%-of-primary-error
too-good trigger is armed.

---

## 7. Who checks this before it runs

| item | who |
|---|---|
| §2 — the thresholds are untestable as stated; is ≥300-as-primary the right substitution? | **`strategist`** |
| §4 — the reformulation from "matched comparison" to "gate on top of a smooth term" | **`strategist`** |
| whether the deep 1999+ sample may carry a *test* rather than only a description | **`strategist`** |
| the result once it exists | **`fable`** |
| shipping anything that grades | **`backend`** |
