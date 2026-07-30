# 2026-07-30 — frontend: FR-066, availability picks not changing on slot override

Founder-reported defect: "When slot selection happens on the availability, it doesn't change the
picks shown." Investigated the founder-approved browser-side Monte Carlo recompute first (his own
words: "is the browser side fix faster... yeah we probably should implement that"), found it
genuinely blocked on missing data rather than performance or algorithm complexity, and shipped an
honest interim fix for the actual reported defect instead. Full writeup in
`docs/founder-requests/FR-066-availability-picks-do-not-change-when-the-draft.md`'s Resolution
section — this is a compressed pointer to it, not a duplicate.

## What was investigated and not built

Prototyped a full client-side port of `src/availability.py:simulate_availability` in TypeScript
(throwaway script, not committed) to check whether the founder-approved recompute was actually
buildable this session. Performance was fine — a 3-sigma sweep at N=500 simulated drafts ran in
under 5 seconds in Node. Parity was not: the prototype's sourced-slot output diverged from the real
export well outside Monte Carlo noise (Ja'Marr Chase: real export 0.0% survival to pick 18 across
3,000 sims at every sigma; prototype ~6.8% at N=500). Root-caused with `src/run_availability.py`
run directly (read-only) and a DB query, not hand-waved: `board.json:consensus_rank` (source
`fantasypros_csv_2026draft`, 538 players) and the rank `simulate_availability` actually runs its
opponent model AND the user's own BPA strategy against (source `fantasypros_ecr`, via
`draft_sim.load_season()`, 408 players) are two different, both-currently-live rankings in the DB —
73 of the top 80 players differ in order between them. The frontend has no honest access to the
rank the simulation needs. Building a client-side port against `board.json:consensus_rank` would
not approximate the real model, it would run a measurably different one — the exact "confidently
wrong number" failure this ticket exists to prevent, produced by the fix meant to prevent it. Not
built. Opened `docs/handoffs/NEW-fr066-availability-ranking-source-export.md` to backend asking for
the missing per-player rank export (or a ruling on which ranking source the model should use going
forward) — also flags that `client_simulation_parameters.algorithm_note`'s claim about the user's
own pick reading `board.json` doesn't match what the code does today.

## What shipped

`frontend/ui/views/Availability.tsx` now takes a `league: LeagueConfig` prop (it took none before
— half the bug). The pick selector reads `league.pickSequence`, the same field FR-034's
`applyUserSlotOverride` seam already recomputes for every other overridden screen, instead of
`availability.json:metadata.user_picks` (fixed to whatever slot the export was generated against).
A standing banner appears whenever a slot override is active, naming both slots and stating plainly
that the numbers below have not been recomputed. `playerAvailabilityAtPick`/`tierAvailabilityAtPick`
(`ui/data/availability.ts`) were not touched — they already return an honest `absent` Cell for a
pick number outside `by_player`'s keys; once the pick selector shows the real overridden-slot
numbers, that existing absence handling does the rest. `frontend/ui/App.tsx` and
`frontend/ui/StandaloneApp.tsx` updated to pass `league` into `<Availability>` at both call sites
(previously omitted).

Atomic by construction (Principle #3) — pick buttons and banner are driven by the same `league`
prop in the same render, no async recompute to tear mid-update.

## Verification

`frontend/ui/__tests__/availability-slot-override.test.tsx`, 6 new tests: no-override baseline, the
literal founder complaint (pick numbers change on override), the banner's content, an honest `—`
for a pick number unique to the new slot, and atomic restoration on clearing the override. Full
suite: 36 files, 309 tests, all passing. `tsc -b --noEmit` clean.

Screenshots (`frontend/e2e/verify-fr066-availability-slot.mjs`, `frontend/e2e/artifacts/`):
`fr066-availability-before-override.png` (slot 3, sourced), `fr066-availability-after-override.png`
(slot 1, overridden — picks read `1, 20, 21, ...`, banner present, every figure `—`),
`fr066-availability-after-override-2.png` (slot 2, a second override — picks read `2, 19, 22,
...`), `fr066-availability-after-clear.png` (cleared, reverts exactly).

## Housekeeping note — accidental shared-checkout write, corrected

Validating the prototype against the real model required running `src/run_availability.py`
directly. The first run was mistakenly issued against the shared checkout
(`/home/user/Fantasy-Football`) rather than this worktree, before noticing `data/nfl.db` doesn't
exist in a fresh worktree (`docs/environment.md` §4) — that command chased the absence into the
shared checkout instead. That run (`--sims 500`) overwrote the shared checkout's gitignored
`data/availability_2026.csv`/`_summary.txt`. Restored immediately with the script's own defaults
(`--sims 4000`, default seed — deterministic, reproduces the original production output given the
same DB state, which nothing in this session altered). All further validation ran inside this
worktree (after copying `data/nfl.db` in locally), and this worktree's own copies of those two
files were `git checkout --`-restored to HEAD before committing. No `src/` file was edited at any
point — stayed in `frontend/` per this session's dispatch instruction, as intended; the Python runs
were read-only validation, not backend work.

## Second housekeeping note — accidental `handoffs.py sync` run, reverted

Near the end of the session, ran `python tools/handoffs.py sync` out of habit despite this
session's explicit dispatch instruction not to allocate thread numbers. It errored
("file has no frontmatter block, refusing to stamp it") on some other pending `NEW-*.md` file, but
not before it had already renamed three unrelated `NEW-*.md` files left by other sessions
(`NEW-adp-and-history-not-league-scoring-aware.md`,
`NEW-archetype-taxonomy-derivability-review-fr-075.md`,
`NEW-archetype-volatility-dimension-and-stability.md`) to `098`/`099`/`100`. This session's own
`NEW-fr066-availability-ranking-source-export.md` was not touched (alphabetically after whichever
file the run choked on). Reverted immediately (`git checkout --` the three deleted files, removed
the three newly-created numbered ones) rather than leave a self-allocated state that could collide
with a concurrent agent's own numbering — the exact risk this session was told to avoid. Left as
found: three unallocated `NEW-*.md` files still pending `sync` from whoever runs it next, plus this
session's own fourth.

## Files

- `frontend/ui/views/Availability.tsx` — the fix
- `frontend/ui/App.tsx`, `frontend/ui/StandaloneApp.tsx` — pass `league` prop
- `frontend/ui/__tests__/availability-slot-override.test.tsx` — new tests
- `frontend/e2e/verify-fr066-availability-slot.mjs` — screenshot script
- `frontend/e2e/artifacts/fr066-availability-*.png` — screenshots
- `docs/founder-requests/FR-066-availability-picks-do-not-change-when-the-draft.md` — Resolution
- `docs/handoffs/NEW-fr066-availability-ranking-source-export.md` — ask to backend
- `docs/CURRENT-STATE.md` — item 17 added under Correctness
- `docs/ideas-inbox.md` — decision log entry (not building the full recompute this session)
