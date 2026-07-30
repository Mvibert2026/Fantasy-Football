---
ID: FR-128
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat with screenshots
RAISED: 2026-07-30
NEEDS: backend
---

## Request

Founder's words, looking at the Availability Explorer with `YAHOO-DEFAULT, 10 TEAMS, STANDARD SCORING`
selected:

> "availability isn't shown for other leagues?"

## Why it matters

**Correct — and the screen tells him two contradictory things at once.**

Measured across the export:

| League | `by_player` entries | `by_tier` |
|---|---|---|
| Primary (Westwood) | **80** | populated |
| `yahoo_10_standard` | **0** | 0 |
| `yahoo_10_half` | **0** | 0 |
| `espn_12_half` | **0** | 0 |
| `ethans_expert_league` | **0** | 0 |
| every other non-primary league | **0** | 0 |

Every non-primary league ships an `availability.json` that is a **shell**. The UI reads it, finds
nothing, and says *"Nobody at this position simulated"* and *"0 players simulated."* That part is the
never-fabricate rule working exactly as designed — the screen does not invent numbers.

**But the metadata block on the same file says this:**

    "simulations_per_setting": 3000,
    "sigma_values": [5.0, 10.0, 20.0],
    "user_picks": [5, 16, 25, 36, 45, ...],
    "reliability_note": "These probabilities never pass through the projection curve, so they are
                         the most reliable numbers in the project."

**Zero simulations ran, and the file asserts three thousand per setting.** It also ships a
reliability note describing the quality of probabilities that do not exist. That is a
never-fabricate violation at the export layer, and it is the part that makes this a defect rather
than a missing feature: the UI's honest empty state sits directly beside a metadata block claiming
the work was done.

The founder's own screenshot shows both — "0 players simulated" in one panel, the 3000-simulation
sigma explanation in the next.

## Initial read

**Root cause, `src/export_contract.py`:**

- Line 78: `avail_csv_for()` resolves the primary to `data/availability_2026.csv`, and every other
  league to `data/leagues/<league_id>/availability.csv`.
- **Those per-league CSVs have never been generated.** `data/leagues/` contains 25 `<id>.json` config
  files and exactly one subdirectory (`yahoo_standard_mock`). No `availability.csv` anywhere but the
  primary's.
- Line 123: `_load_availability_csv` returns `{"by_player": {}, "by_tier": {}}` when the file is
  absent — **silently**. No warning, no flag on the output.
- The metadata block is then written unconditionally, from configuration rather than from what the
  run produced.

So the plumbing for per-league availability was built and the simulation was never run through it.

**Two fixes, and the second one is not optional even if the first is deferred.**

**1 · Run the simulation per league.** Availability is the project's most defensible output — it
depends only on how a draft room behaves, never on predicting football, which is exactly what the
`reliability_note` says. Extending it to the other leagues is real value. Cost needs measuring first:
3,000 sims × 3 sigma settings × ~25 leagues is not obviously cheap, and the answer may be to run it
for the leagues the founder actually uses rather than all 25 generated presets.

**2 · Make the metadata honest when the run did not happen.** This holds regardless of whether (1) is
done, and it is cheap. An export whose payload is empty must not claim 3,000 simulations and must not
carry a reliability note about numbers it does not contain. It should state that availability was not
computed for this league, and why — the same standard every other absence in this app already meets.
`_load_availability_csv`'s silent empty return is the specific line that lets a missing input become a
confident-looking file.

**Priority:** fix 2 is small and closes a live honesty defect. Fix 1 is a genuine feature with a
measurable cost that should be measured before it is committed to.
