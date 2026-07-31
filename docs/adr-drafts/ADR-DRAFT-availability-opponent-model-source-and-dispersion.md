# ADR-DRAFT — Availability opponent model: ADP as the base, fitted dispersion, unchanged noise structure

**Status: DRAFT, number unallocated.** Allocate with `python tools/handoffs.py adr next` before
landing in `docs/decisions.md`. Never hand-type the number — that scheme collided at ADR-048.

**Author:** `strategist`, 2026-07-30. **Thread:** 119. **Requests:** FR-131 (founder),
FR-066 / thread 104, FR-128.
**Full pre-registration:** `docs/ranking/availability-opponent-model-precommit.md`.

---

## Context

`src/availability.py:simulate_availability` runs its opponent model **and** the user's own BPA arm
off `rankings WHERE source='fantasypros_ecr'` (408 players, `as_of` 2026-07-24). The shipped board
runs off `fantasypros_csv_2026draft` (538 players, 2026-07-27). 73 of the top 80 players are in a
different order between the two — an accident nobody chose, discovered by frontend while trying to
build FR-066 (thread 104).

The module's own exported metadata states that its dispersion parameter *"is a guess, not fitted to
observed drafts."* `ffc_adp_snapshots` holds this league's exact format (half-PPR, 10 teams, 180
players, fresher than either ranking source) with a measured per-player `std_dev`.

The founder's position: *"availability is probably more related to ADP than consensus."*

## Decision

**Three changes, decided separately so a null on one does not carry the others.**

**A. The opponent model's base rank moves to `ffc_half_ppr_10team`, on a corrected pick axis.**
Not as a mixture with expert consensus. ADP is already the aggregate over drafter types; blending
consensus back in double-counts the population ADP integrates over. Expert consensus survives only
as a **coverage patch** past FFC's ~145-skill-player tail, joined through a fitted monotone
calibration, never spliced.

**B. Dispersion becomes `sigma_i = lambda · s_i`,** where `s_i` is a fitted, monotone
ADP-position curve normalised to mean 1 and `lambda` remains the swept global scale in picks. FFC's
raw per-player `std_dev` is **not** adopted directly. A per-player *residual* multiplier ships only
if empirical-Bayes `tau_hat^2` is bounded away from zero (H2), EB-shrunk, with the shrinkage factor
reported per player.

**C. The user's own arm is split off the opponents' array and pointed at `board.json`.**
This is a defect fix: `client_simulation_parameters.algorithm_note` already claims the user drafts
best-available off the board and the code does not.

**The room-noise structure is unchanged.** Per-player sigma **rescales the existing shared draw**;
it does not introduce a second, per-team draw.

```
z_i                  ~ N(0, 1)      # once per PLAYER per simulated draft, shared by all teams
s_i                   = ghat(adp_i) / mean(ghat)
effective_rank[t][i]  = adp_i + lambda * s_i * z_i
```

Invariant, to be asserted by test: `Corr(effective_rank[t1][i], effective_rank[t2][i]) = 1` for
every team pair, before the need penalty — exactly as today.

## Pre-committed decision rules

| Rule | Gate |
|---|---|
| **M0 gates B.** FFC's `times_drafted` and `total_drafts_in_sample` do not reconcile (`total = 1254` on every row; Bijan Robinson, an every-draft pick-2, shows 90; Ja'Marr Chase's count *fell* 189→175 while the total *rose* 1187→1254). Until FFC's documented semantics are cited and an internal consistency check passes, there is no defensible per-player `n`. | If M0 fails, **B does not proceed**; A and C may. |
| **H1 gates claims, not adoption.** ADP beats expert consensus on realised-pick MAE in all three logged mocks with a mean gap ≥ 2.0 picks. | If NULL, adoption still proceeds on estimand grounds, but **no export field, tooltip, glossary entry or founder-facing sentence may state or imply the ADP model is more accurate.** |
| **H2 decides the residual.** Ship per-player residual dispersion iff the lower bound of `tau_hat^2`'s 95% player-bootstrap CI exceeds 0. | If NULL, ship the curve alone and say so on screen: *"per-player dispersion beyond the ADP-position effect was tested and found indistinguishable from sampling noise."* |
| **H3 blocks on a sanity check.** `lambda_hat` must come out **below** the mean observed pick sd, because the simulator's own mechanics add variance on top of the latent noise. | If `lambda_hat ≥` mean observed sd, **nothing ships** — that is a bug report, not a calibration. |
| **H4 is an acceptance test.** The simulator's unconditional marginals must reproduce the closed form `P(available at p) = 1 − F_i(p)` to mean ≤ 0.02 / max ≤ 0.05. | A failure localises a mechanics bug. Do not widen the tolerance. |

**Directional pre-commitment, recorded before the run:** `lambda_hat < 10`. Current availability
probabilities for top-80 players are expected to be systematically too close to 0.5 — the model is
more uncertain than the market is. Basis: over ADP 1–90 the typical FFC `std_dev` is ~4–5, not the
~9.7 median quoted over all 180 rows including kickers and the tail; and the 10-team Yahoo mock's
implied per-round dispersion is 1.40 / 4.59 / 10.30 picks across rounds 1–3, against the ~8 picks a
flat sigma = 10 implies in every round.

## Why — the argument that survives every empirical result

**ADP is not a better ranking; it is a measurement of the quantity the model needs.** Availability
asks where players actually go. ADP measures that, in picks, with an uncertainty attached. Expert
consensus measures analyst opinion, ordinally, with no uncertainty at all. Even if the orderings
correlate at 0.95, only one of the two can be checked against reality.

**"Is FFC representative of a Yahoo room?" is not the bar, and cannot be answered.** Two logged
Yahoo mocks is n = 2 rooms; the correct resampling unit is the room, so no interval is claimable.
Yahoo mock lobbies fill unclaimed seats with autopick bots drafting off Yahoo's own *consensus*
ranking, in an unknown proportion. And neither source is representative of Westwood, which is nine
specific people from whom we hold zero drafts. There is no representative source — only a choice
among proxies, and it should turn on estimand and measurability.

**What the mocks do establish: the shape of dispersion transfers, the level does not.** Round-by-round
mean absolute deviation from FFC ADP in the 10-team mock (1.12 / 3.66 / 8.22 picks, rounds 1–3;
implied `sigma_hat` 1.40 / 4.59 / 10.30) against the mean FFC `std_dev` of the same players
(1.38 / 3.16 / 4.79). The gradient agrees across two independent populations; the Yahoo room is
~1.0× / 1.45× / 2.15× more dispersed by round. Hence: adopt the shape, keep the level on a swept
scale.

**Why not raw `std_dev`.** It carries no stated n and no standard error; the per-player n varies
~20-fold and its semantics are unreconciled (M0); and it is unstable day to day exactly where
FR-131 leans hardest on it. Same source, same format, one day apart: Kamara 26.2 → 19.0 (−27%,
n = 28), Hunter Henry 28.0 → 24.8 (−11%, n = 12), Kittle 26.9 → 24.9, McPherson 39.2 → 36.4 —
while Gibbs, Bijan and Chase did not move at all. The four unstable values are precisely FR-131's
four "the room does not agree" exhibits.

**And most of the spread is not disagreement.** `std_dev` rises near-monotonically with
`average_pick` (Bijan 2.0→0.7, Breece 28.7→2.9, Bowers 44.5→10.4, Kittle 117.0→24.9), compressing
at the extreme tail through censoring (Christian Kirk 194.7→7.7). Bijan's dispersion cannot be
large — pick 1 is a hard floor. The "factor of forty between Bijan and Kamara" is essentially
"ADP 2 versus ADP 156." The residual, player-specific part is the only real finding on offer, it is
small, and it is exactly where the sampling error lives — which is why H2 exists and why its null
branch is written out in advance.

## Consequences

**Accepted failure mode: staleness under news shock.** FFC ADP is a 5-day trailing mean of completed
drafts (`sample_window` = "July 25, 2026 to July 30, 2026"). An injury three days before the draft
is fully priced into expert consensus and only partly into ADP. **Mitigation is part of the
decision, not optional:** export `sample_window` / `as_of_date` / `times_drafted` per player, and
surface a player whose board rank and ADP rank diverge beyond a threshold as *"the market has not
moved on this yet."* That converts the failure mode into a visible signal.

**ADR-035's binding constraint extends to FFC half-PPR 10-team.** It is materially closer to
Westwood than MFL — same scoring family, same team count, 1,254 drafts against MFL's 50 — and that
closeness makes mislabelling *more* likely, not less. Measured differences that move pick position:
FFC's default lobby rosters kickers and defenses (Westwood has neither); FFC `low_pick` values reach
round 18 against Westwood's 16; and the drafting population is self-selected and unmeasured.
**The label test, applied literally: could the founder read this number and come away believing it
describes his nine leaguemates? If yes, the label fails.** Required wording carries source, format,
window and n. One clause ADR-035 did not need: FFC pick numbers include kickers and defenses and
Westwood's do not, so the two are not comparable even before the population question.

**A consequence nobody asked for, which changes two other requests.** With opponents drafting from
ADP with per-player dispersion, the **unconditional** Prep-mode marginals are nearly closed-form:
`P(available at pick p) = 1 − F_i(p)`, computable from `average_pick` and `std_dev` on the corrected
axis with no Monte Carlo. This collapses ADR-061's 628-seconds-per-league sweep for the
unconditional case (**FR-128**), and makes the browser-side recompute (**FR-066 / thread 104**) a
per-player `(adp_pick, sigma_pick, coverage_flag)` export rather than the raw ECR rank array thread
104 currently asks for. **Thread 104's ask should be reformulated before backend builds the wrong
field.** The simulator keeps earning its keep where the closed form cannot go: conditioned on live
draft state.

**What the founder should be told about the "most reliable output" claim.** Availability does not
inherit the projection model's error — that part was always true. But it has its own error, and
until now that error came from an admitted guess and a superseded ranking, so the claim was doing
more work than it had earned. After this change it gets *stronger*, for the first time on evidence
rather than architecture.

## What this ADR does not decide

- **Manager-idiosyncratic dispersion.** The shared-noise structure asserts it is zero. That is
  unmeasured, kept **by decision** rather than inertia, and the instrument that could test it is the
  founder's ~30-mock programme (`mock_picks` stores per-slot sequences). Separate family, separate
  denominator, opened when the mock count supports it.
- **Whether the user's arm should draft our VBD board rather than a consensus rank.** C makes the
  existing claim true with the minimal move. "The user drafts our board's VBD order" is a larger,
  separate question, and its effect on availability is second-order — the user is one seat of ten
  and the board is snapshotted before his own pick.
- **Anything fitted to the logged mocks.** n = 2 rooms, unknown human/bot fraction, neither matching
  Westwood's roster shape. Any `lambda`, mixture weight or shrinkage factor fitted on that would be
  a fabricated constant. The mocks are admissible as a falsification check and a shape-transfer
  check, and nothing more.
