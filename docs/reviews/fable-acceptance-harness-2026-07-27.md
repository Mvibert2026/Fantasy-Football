# The acceptance harness — 2026-07-27 (Extended mandate, Priority 4)

**Built, not just designed:** `frontend/e2e/smoke.mjs` on branch `fable/ext-2026-07-27` — a
scripted founder-loop smoke check that starts the dev server, loads the app, walks thread 063's
trigger table, commits five picks through the real typeahead, undoes one, leaves and re-enters
the Draft tab, reloads, and screenshots the board and draft room. Non-zero exit on any assertion
failure; machine-readable `e2e/artifacts/report.json`; screenshots written regardless of outcome.
Verification status of the build itself is reported in the session landing note
(`FABLE-EXT-2026-07-27.md`) — this document is the design and the wiring.

One correction to session 1's own claim first, per the refute-don't-confirm mandate: session 1
said every dependency "already exists in the repo or its permissions." **Wrong on the repo half:**
Playwright is not in `frontend/package.json` and `frontend/node_modules` has no trace of it
(checked this session). It is an install away, but the claim as stated was optimistic — the
harness adds `playwright` as a devDependency on the branch.

## 1 · The problem it solves, stated as the failure it interrupts

The project's most persistent failure pattern (threads 043 → 051 → 063, and the missing-screen
incident behind the "UI work is never done on your own report" rule): **the founder is the
regression sensor.** A behaviour is fixed, the unit suite is green, and the founder discovers in
use that it regressed — because the unit tests assert component internals in jsdom while the
regression lives in the composed app (an effect keyed on draft state, a programmatic focus, a
stale localStorage record). Thread 063 is explicit that a single "does not open unexpectedly"
test allowed the second regression; its fix is *enumerated* triggers, each pinned.

The harness is that enumeration, executed against the real running app, headlessly, at every
round closeout — so the founder's loop runs without the founder (FR-002).

## 2 · What it asserts (mapping to thread 063's trigger table)

| 063 trigger-table row | Automated? | How |
|---|---|---|
| Click into the field → opens | **Yes** | click, assert `[data-testid="suggester-dropdown"]` present |
| Typing → opens | **Yes** | `pressSequentially('a')`, assert present |
| A pick is committed → must NOT open | **Yes — the 063 regression row.** | five digit-shortcut commits; assert closed after each; reported as `n/5 reopened` |
| Board updates/recomputes → NOT open | Indirect | every commit recomputes availability; covered by the row above |
| Mount / page load / refresh → NOT open | **Yes** | asserted on first Draft-tab entry AND after `page.reload()` |
| League switch → NOT open | **Not yet** | needs a second league in the dev dataset; work order A3 |
| Return from another tab → NOT open | **Yes** | Prep → Draft round trip, assert closed |
| Undo → NOT open | **Yes** | Backspace-on-empty undo, assert closed + pick count decremented |
| Programmatic focus → NOT open | Partial | the post-commit autofocus is exactly this; covered by the commit row. A synthetic `.focus()` injection is possible but tests the browser more than the app. |
| Closes on Escape / blur / commit | Escape: **yes**. Blur/commit: indirect (commit row implies closed-after-commit) |

Plus, outside the table: app loads with content and no failure banner · pick counter readable
from the real placeholder · five commits advance the pick number by exactly five · picks persist
across reload (localStorage layer) · zero console errors across the whole loop · screenshots of
Board and DraftRoom for the round report (the visual half the repo's rules already require).

**Isolation guarantee worth naming:** the harness runs in a fresh Playwright context — empty
localStorage — so it cannot read or pollute the founder's real draft state (pre-mortem #6's
stale-test-picks hazard), and its own picks evaporate with the context.

## 3 · How failures report

- **Exit code** — non-zero on any assertion failure: CI-composable, scriptable, unambiguous.
- **`e2e/artifacts/report.json`** — one entry per assertion (`name`, `ok`, `detail`), timestamped;
  the diffable artifact a round reply links to.
- **Screenshots always** (`board.png`, `draftroom.png`) — pass or fail, because the standing rule
  is that UI work is never done without one, and because a *passing* run's screenshot is the
  round's visual evidence for free.
- Harness crashes (server won't start, selector missing) are themselves a reported failure row,
  not a silent skip — a harness that can't run must look red, not absent.

## 4 · Wiring into round closeout (standing, not ad hoc)

The mechanism must not depend on anyone remembering it:

1. **`npm run smoke`** (added to `frontend/package.json` scripts on the branch) — one command,
   starts its own server, self-contained.
2. **Frontend round closeout rule** (one line for `docs/operating-model.md`, PM lands it — this
   mandate cannot write outside `docs/reviews/`): *a frontend round's reply is incomplete without
   the smoke report and its two screenshots attached; a red smoke blocks closeout the way a red
   unit suite already does.* This is the same enforcement shape as `tools/handoffs.py check`
   living in the test suite.
3. **Pre-draft**: the pre-mortem checklist's T-7d dry-run item is this harness run; morning-of
   repeats it against the frozen build (`--no-server` mode attaches to the already-running one).
4. **Growth path**: new founder-reported UI regressions get a row here *first* (the executable
   trigger table), then the fix. The harness file is the accumulating enumeration 063 asked for.

## 5 · Work orders

- **A1** [frontend, small] — merge the harness from the branch; add `"smoke": "node e2e/smoke.mjs"`
  to scripts; `npm i -D playwright` + `npx playwright install chromium` documented in the
  frontend README.
- **A2** [PM, one line] — the closeout rule in `docs/operating-model.md` (§4.2 above).
- **A3** [frontend, small] — add a second league fixture to the dev dataset so the league-switch
  trigger row becomes automatable; then add the row to `smoke.mjs`.
- **A4** [frontend, later] — extend with an availability-recompute assertion (dot arrays change
  after a commit) once a stable testid exists on the availability cells; today that would pin
  style internals, which is how brittle E2E suites die.
