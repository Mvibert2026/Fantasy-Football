---
ID: FR-2026-07-30-rb-workload-hangover
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — a genuine gap, and a functional form the project has never tested
NEEDS: ranker (batch 4)
---

## Request

> "If we don't have it, running backs coming off of high carry years (350/375/400)"

## We do not have it. Checked, not assumed

Searched `docs/factor-ledger.md` (all 92 rows), `docs/test-registry.md` (all tiers including the
Tier 5 rejections), and every results CSV in `experiments/bottomup/results/`. **No row, no arm, no
measurement on prior-season carry volume as a predictor of decline.** The nearest neighbours are
different questions:

| Existing row | What it actually measures | Why it is not this |
|---|---|---|
| #20 Opportunity share | carries+targets ÷ team total, **same season** | A share, not an absolute volume, and contemporaneous rather than lagged |
| #28 Vacated opportunity | opportunity opening **elsewhere** | About teammates leaving, not about the player's own workload |
| N18 Snap-share persistence | P(≥60% snaps repeats) | Persistence of *role*, not the cost of *volume* |
| N32 Multi-year games-missed | injury-risk model | Overlaps the mechanism, but SIS publishes **no naive baseline**, and its features are largely paid charting |

## Why this is worth a real test rather than a citation

This is the **"Curse of 370"** hypothesis in its classic form, and it is exactly the kind of claim
`CLAUDE.md` §11 says to treat as a hypothesis: *"Everyone knows X" is a hypothesis to test.* It is
widely repeated, it has a plausible mechanism, and it has also been contested in public analysis for
twenty years. This project has the data to settle it for **its own scoring rules and its own league
shape**, which is not what any published version tests.

**Two things make it a good test rather than a fashionable one:**

1. **The data is already here.** Carries are in `player_weekly_stats`, 1999–2025 — 27 seasons, zero
   ingest. Same standing as QB rushing attempts: the cheapest class of test available.
2. **It is a functional form this project has never tried.** Every factor tested so far is a
   continuous weight. This is a **threshold/gate** — "above 350 carries, expect decline" — and the
   only other gate on the list (N29, team passing-volume floor) is also untested. If gates work where
   weights do not, that is a finding about *model shape*, worth more than any single factor.

## Specification notes for whoever runs it

- **The founder named three thresholds (350 / 375 / 400). Testing all three is three tests**, and the
  multiplicity budget is at campaign level (§6.3). Pre-commit either one primary threshold with the
  others as secondary, or a continuous form with the thresholds as a robustness check — but decide
  before fitting, not after seeing which one works.
- **Survivorship is the primary threat here, more than in any factor tested so far.** A back who takes
  380 carries and is finished is one who *earned* 380 carries — the population is defined by an
  outcome correlated with the treatment. Any analysis restricted to backs who played the following
  season silently deletes the strongest evidence for the hypothesis. §6.2 applies with unusual force.
- **Confounded with age and with talent.** High-carry seasons cluster in a back's prime and among good
  backs. A naive test will find decline that is regression to the mean plus aging, and attribute it to
  workload. The comparison must hold those constant or the result means nothing.
- Report against a baseline (§6.5), not as a raw decline rate. "Backs over 350 carries declined" is
  not a finding; "declined *more than comparable backs who did not*" is.
