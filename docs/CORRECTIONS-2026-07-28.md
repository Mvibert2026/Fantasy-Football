# Corrections — 2026-07-28

**Repo mirror of `claude/session-record-2026-07-27-28.md`, which lives in the Claude project and is
NOT readable from the repo.** Fable's K-B run failed to find it and correctly flagged the gap. Any
mandate referencing that path should reference this file instead.

Everything here is founder-stated or agent-reported. Nothing is PM-measured.

---

## 1 · λ does not drive the recommendation the founder sees

From Fable's G-A run, repo-grounded:

- The shipped RECOMMENDED card (`frontend/ui/data/recommendation.ts:16`) and the shipped survival
  number (`frontend/ui/data/liveAvailability.ts:30`) are **λ-free**.
- Both run on five hard-coded constants — **+8 / +18 / −25 and −0.62 / −1.25** — never fitted to
  anything.
- λ = 0.352 steers only sim-strategy comparisons and the unwired Mock Lab path.

No draft-day λ-flip exposure as shipped. The finding is that the measured parameter is disconnected
from the recommendation surface while unmeasured constants do the work.

**Consequence: the PM's product description was false.** "A hazard model with a measured need term" is
not what ships. That wording is in the charter, the explainer, the dashboard and every summary given
to the founder this week. Open decision, mandate K-A: wire λ in, or drop the claim.

Supporting numbers: top-1 flips in 4/160 replayed 2025 states (2.5%), top-3 reorders in 16/160,
concentrated in rounds 4–7. Flip boundaries λ ≈ 0.395–0.458. **The founder's own slot-3 states never
flip top-1.** Pairs-cluster bootstrap [0.229, 0.500] and LOCO jackknife [0.207, 0.496] both reproduce
the Wald interval — 10 clusters is not hiding variance; the uncertainty is population, not sample.

## 2 · League facts — founder-stated, several supersede earlier assumptions

| | Platform | Teams | Notes |
|---|---|---|---|
| **Westwood (154693) — primary** | **Yahoo** | **10** | Custom scoring: half-PPR, **stacking** yardage bonuses |
| Ethan's Expert (834236) | Yahoo | 10 | Could hold 12; only ever fills 10 |
| Third | ESPN | may be larger — **unknown** | No settings gathered at all |

- **Westwood is NOT a 12-team league and NOT a non-Yahoo platform.** Fable's F-C inferred playoff
  weeks 15–17 from the premise that it was a 12-team custom league. **That premise is falsified.** The
  verified Yahoo default (16, 17) may apply to both — still requires reading the live settings page.
- **The mock-draft team-count problem dissolves.** Both leagues that matter are 10-team, so any
  10-team room calibrates both.
- Two of three leagues share a platform, so the per-platform ADP concern is two populations, not three.

## 3 · The single logged draft is not real

Founder-confirmed. **The honest calibration count is 0 of ~30, not 1 of ~30.** `CURRENT-STATE.md`,
`status.md` and the dashboard all overstate it. Open question: was that record part of the data λ was
fitted on?

## 4 · Confirmed per-league constant defects

`TARGET` / `EPS` / `SHARE_BAR` / `POSITIONS` are hard-coded to primary-league-2025 in
`src/live_availability.py:50-66`. **League 2's kicker slot is literally unrepresentable.** Same
construction-error class as `playoff_weeks`. First confirmed instances for the G-B sweep.

`D-001` is decided but unimplemented — `NEED_ADJUSTMENT_SCALE = 10.0` still load-bearing at
`src/draft_sim.py:284`. Every G-A flip count scales with it.

## 5 · Data-source constraint reaffirmed

FFC pick-level draft-result scraping **declined**, 2026-07-28. D-021 authorised a *one-time*
historical ADP pull at ≤1 req/sec; a recurring daily scrape of draft-result pages is a materially
different activity and is not covered by it. MFL to be checked instead — already integrated,
ToS-clear. Caveat: ~50 hobbyist mocks/day likely leaves the velocity test underpowered, and **"we
cannot test this yet" is an acceptable answer.**

## 6 · Backup, resolved in principle — not implemented

The 853 MB of NFL history is public and rebuildable: a cache, not an asset. ADP snapshots are
~50–200 KB/day and **irreplaceable — a past date's ADP cannot be re-fetched from any source.** Write
each capture as a dated CSV under `data/adp-snapshots/`, tracked in git, so backup is a side effect of
the daily run.

**W8 has still never run.** Fable's K-B ranks this above any schedule slip.

## 7 · Mock drafts are calibration data, not rehearsal

Every mock does three jobs: trains the founder, produces the **only** calibration data the availability
model can get, and surfaces UI defects (he remains the only detector — roughly 5:1 founder-to-project).

Mocks start against the imperfect board. **Per-league settings are a prerequisite, not a parallel
task — a mock logged with the wrong roster shape is worse than no mock, because it looks like data.**

Capture schema, per draft: `league_id`, `provider`, `team_count`, `draft_type`, `our_draft_slot`,
roster shape, `scoring_format` plus a hash of the full rules, real-or-mock, platform, date. Per pick:
`pick_number`, `drafting_slot`, `player_id`, `position`, time on clock, and **the board's own survival
probabilities for the top candidates BEFORE the pick resolved.** That last field is unrecoverable
after the fact.
