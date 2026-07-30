---
ID: FR-066
STATUS: IN PROGRESS
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Availability picks do not change when the draft slot changes

Founder's own words:

> "When slot selection happens on the availability, it doesn't change the picks shown"

## This is the known gap, now confirmed on the live site

**Diagnosed 2026-07-29 and recorded in FR-057** — the founder has now hit it himself, which upgrades
it from a predicted consequence to an observed defect.

`data/export/availability.json`'s `by_player` is keyed by **one slot's pick numbers** — `3, 18, 23,
38, 43, 58` for the slot the export was generated at. Change the slot to 5 and the picks become `5,
16, 25, 36, 45, 56`; **none of those keys exist**, so the screen keeps showing the original slot's
picks rather than recomputing.

The selector moves everything else — board, round grid, Predictions, the draft room — because those
derive from `league.json:pick_sequence`. Availability alone cannot, because its numbers come from a
Monte Carlo simulation run in Python against a single slot.

## Status: the fix was started and then paused, by the founder

FR-057 part 1 (export every slot) ran for hours on 3,000 simulations per slot without finishing and
was **stopped at his instruction** to conserve tokens. Nothing is lost; there are simply no results.

**That pause changed the recommendation.** If a full sweep takes hours it must re-run whenever the
board changes, which is often. Browser-side recomputation — his stated preference all along — costs
once and then covers any slot, any team count, any roster shape. `client_simulation_parameters` is
already in the export and nothing consumes it.

**So: resume FR-057, and consider doing part 2 first.** That is the opposite of the original order
and it is what the measured cost argues for.

**Until then the screen should say so.** Showing another slot's picks without a word is the failure
this project treats as worst — a number that is confidently wrong. An honest "availability is
computed for slot N and has not been recomputed for your selection" is correct today and cheap.

His follow-up, when told the browser-side fix computes one slot at a time rather than the backend
precomputing all ten:

> "is the browser side fix faster cause it computes one at a time instead of all of them? yeah we
> probably should implement that"

## Resolution (2026-07-30, frontend)

**Two things happened this session: a real investigation into the browser-side recompute the
founder approved, and a shipped fix for the actual defect he reported.** They are not the same
scope, and the gap between them is the substance of this writeup.

### What was investigated: browser-side Monte Carlo re-simulation — not built, and here's why

The founder-approved direction is real and was taken seriously: `src/availability.py`'s
`simulate_availability` was read in full, and `client_simulation_parameters` (already exported,
unconsumed) does carry the opponent-model knobs a client-side port would need —
`mechanical_need_targets`, `max_at_position`, `need_penalty_per_surplus`, `ranking_sources`. A full
prototype port was written and benchmarked
(`/tmp/.../scratchpad/bench.mjs`, not committed — throwaway): pick-order/snake logic reused from
`ui/data/draft.ts`'s existing `teamSlotAtPick`/`pickNumbersForSlot`, the opponent need-penalty and
legal-mask logic reimplemented from `src/draft_sim.py`'s `DraftEngine`, room noise via a seeded
Box-Muller generator. **Performance was never the blocker** — a 3-sigma sweep at N=500 simulated
drafts per setting ran in under 5 seconds in Node for either the sourced or an arbitrary slot,
comfortably fast enough for an on-demand, one-slot-at-a-time recompute exactly as the founder asked.

**Parity was the blocker, and it is a real, measured, non-approximation-shaped gap, not a
performance one.** The prototype's sourced-slot (3) output was checked against the real
`availability.json` and diverged well outside Monte Carlo noise — e.g. Ja'Marr Chase reads 0.0%
survival to pick 18 at every sigma setting across 3,000 real sims (data/export/availability.json),
the prototype showed ~6.8% at N=500. Root-caused, not hand-waved: ran
`src/run_availability.py --sims 500 --league primary` directly (read-only, for comparison; see
"housekeeping" below) and diffed its own `consensus_rank` column against `board.json:consensus_rank`
for the same 80 players — **73 of 80 differ.** `board.json`'s own `consensus_source_note` explains
why: the board is scored off `fantasypros_csv_2026draft` (538 players, DB `as_of_date` 2026-07-27,
the founder's own newer FantasyPros export, per thread 053/067), while
`draft_sim.load_season()` — what `simulate_availability` actually runs its opponent model AND the
user's own BPA strategy against — still queries `WHERE source='fantasypros_ecr'` (408 players,
`as_of_date` 2026-07-24, the older DynastyProcess-mirrored source `board.json`'s own note says was
superseded). Confirmed directly against the DB (`SELECT source, COUNT(*), MAX(as_of_date) FROM
rankings WHERE season=2026 GROUP BY source`): both sources are live and current, genuinely
different, not a stale leftover.

**This means the frontend has no honest source for the one number a faithful client-side
re-simulation needs most: the per-player rank the opponent model and the user's own BPA pick
actually run on.** `board.json:consensus_rank` is not a stand-in for it — substituting one for the
other doesn't produce an approximation of the real model, it produces a measurably different one
(a top-5 WR by the real model's rank isn't even top-5 by the board's rank). Per this ticket's own
instruction — *"if any input to the availability math is slot-dependent and exists only for the
exported slot, STOP and report it rather than approximating"* — this is exactly that case,
generalized slightly: the input (the ECR-sourced rank) isn't slot-dependent, but it exists only
inside the backend's DB under a ranking source the frontend contract never exports, for any slot.
Shipping a port against `board.json:consensus_rank` anyway would have been the "confidently wrong
number" failure this whole ticket exists to prevent, produced by the fix meant to prevent it. Not
built. **Opened `docs/handoffs/NEW-fr066-availability-ranking-source-export.md` to backend** asking
for the one field this actually needs (the per-player rank `simulate_availability` runs on,
whichever source it ends up pinned to) — see that thread for the specific ask. It also separately
flags that `client_simulation_parameters.algorithm_note`'s claim ("the user is assumed to draft
best-available off the TRUE consensus board... see board.json") does not match what the code does
today (`ds.strategy_bpa` runs on the same ECR-sourced `data.consensus_rank` as the opponent model,
not on `board.json`), and that the availability model silently running on a superseded ranking
source may be worth its own look independent of this ticket.

**Also confirmed and worth stating plainly: this bench.mjs prototype touched `src/`-adjacent
generated files, not `src/` itself, but a housekeeping note belongs here.** Validating against the
real model required running `src/run_availability.py` directly. The first run was mistakenly issued
against the **shared checkout** (`/home/user/Fantasy-Football`, not this worktree) before catching
the mistake — `data/nfl.db` doesn't exist in a fresh worktree (`docs/environment.md` §4), and an
early command chased that absence into the shared checkout without noticing. That run (`--sims 500`)
overwrote the shared checkout's gitignored `data/availability_2026.csv`/`_summary.txt`. Restored
immediately by re-running with the script's own defaults (`--sims 4000`, default seed) — the RNG is
seeded deterministically from those defaults, so this reproduces the same output the original
production run would have, assuming the same DB state, which nothing in this session altered. All
further validation ran inside this worktree only (after copying `data/nfl.db` in), and those files
were `git checkout --`-restored to HEAD before this commit. No `src/` file was edited.

### What shipped: the actual reported defect, fixed

**The founder's words are the scope: "it doesn't change the picks shown."** That's fixed, honestly,
without needing the blocked recompute:

- `frontend/ui/views/Availability.tsx` now takes a `league: LeagueConfig` prop (it took none
  before — that alone was half the bug: the screen had no way to know a slot override was active).
  The "YOUR PICKS" row now reads `league.pickSequence` — the same field `applyUserSlotOverride`
  (FR-034's seam, `ui/data/league.ts`) already recomputes for every other overridden screen — instead
  of `availability.json:metadata.user_picks`, which is fixed to whatever slot the export was
  generated against. No second override path was added; this goes through the existing seam.
- When `league.userSlotOverridden` is true, a standing banner names both slots explicitly ("Showing
  slot 3's simulation, not slot 1's...") and states plainly that nothing below has been recomputed —
  matching the FR's own suggested interim wording almost verbatim.
- `playerAvailabilityAtPick`/`tierAvailabilityAtPick` (`ui/data/availability.ts`) were **not
  touched** — they already return an honest `absent` Cell (rendered as `—`) for a pick number
  outside `by_player`'s keys. Once the pick selector shows the overridden slot's *real* pick numbers
  instead of the sourced slot's, that existing absence-handling does the rest: every number under an
  override now honestly reads "not recorded," never a stale real-looking figure.
- This is atomic by construction (Principle #3), not an async recompute that could tear mid-update:
  the pick buttons and the banner are driven by the same `league` prop in the same render, no
  intermediate state to leave half-updated.
- `frontend/ui/App.tsx` and `frontend/ui/StandaloneApp.tsx` both updated to pass `league` into
  `<Availability>` (previously omitted at both call sites).

**Tests:** `frontend/ui/__tests__/availability-slot-override.test.tsx` (6 new tests) — no override
shows the sourced slot's real picks with no banner; overriding changes the pick numbers shown (the
literal founder complaint) and shows picks unique to the new slot while removing sourced-only ones;
the banner names both slots and cites FR-066; a pick number unique to the overridden slot renders
the honest `—`, never a stale number; clearing the override atomically restores the original picks
and removes the banner. Full suite: 36 files, 309 tests, all passing (`npx vitest run`, ~98s).
`npx tsc -b --noEmit` clean.

**Screenshots** (`frontend/e2e/verify-fr066-availability-slot.mjs`, run against a local dev server,
`frontend/e2e/artifacts/`):
- `fr066-availability-before-override.png` — slot 3 (sourced), real numbers, no banner.
- `fr066-availability-after-override.png` — slot 1 (overridden): pick buttons read
  `1, 20, 21, 40, 41, 60, ...`, banner present, every figure reads `—`.
- `fr066-availability-after-override-2.png` — slot 2 (a second, different override): pick buttons
  read `2, 19, 22, 39, 42, 59, ...` — side-by-side proof this isn't a one-off toggle.
- `fr066-availability-after-clear.png` — override cleared: picks and numbers revert exactly to the
  slot-3 screenshot, banner gone.

### What's still open

The real recompute the founder approved is blocked on the backend export change described above
(`docs/handoffs/NEW-fr066-availability-ranking-source-export.md`). Once that field exists, the
bench.mjs prototype's pick-order/opponent/legal-mask logic is close to ready to port properly (with
real tests against the export, not a throwaway script) — this was time well spent, not a dead end.
