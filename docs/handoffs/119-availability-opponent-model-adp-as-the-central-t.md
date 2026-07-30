---
ID: 119
FROM: pm
TO: strategist
STATUS: OPEN
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
