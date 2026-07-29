# Overnight integration — 2026-07-29

**The founder is asleep. Do not ask questions. Decide, log, continue.**

---

## READ THIS FIRST — what already happened

**This file was written by the PM, not by another agent session.** An earlier integrator found it
untracked on disk mid-session and reasonably flagged it as evidence of a concurrent run. It is not.
It is written to disk rather than pasted because a long paste failed to arrive once.

**Two of the four branches are already merged and pushed:**

| Branch | Commit |
|---|---|
| frontend top-bar fixes | `cc638ba` |
| acceptance harness | `870750d` |
| founder decisions D-025 / D-026 recorded | `1a264a0` |

**Do not merge those two again. Do not re-record those decisions.** Phase 5 below is already done.

**Verified state at that point:** frontend 202/202 pass · backend 620/620 pass · both pushed.

### One thing needs fixing, and it is the check, not the code

The acceptance harness reported 8 of 9. The failing one is the player-count check, and **the check is
wrong, not the fix.**

The old header read `"N of 378 players loaded"` with 378 hardcoded. The frontend fix did not correct
the number — it **removed the denominator entirely**, so the header now reads `"511 players loaded"`.
Its own test asserts the old `of \d+` phrasing is absent. But the harness still looks for
`"N of TOTAL players loaded"` and compares TOTAL against 511, so it fails on a string that no longer
exists.

**Fix `tools/acceptance/lib/checks.mjs` so the check matches ground truth rather than the old
phrasing** — assert the rendered count equals the real row count in the export, without requiring a
denominator. Then re-run and confirm 9 of 9. Add this to Phase 3.

### Two pre-existing problems, worth clearing while you are here

- **A stale duplicate `frontend/tests/` directory** breaks a plain `pytest` from the repo root with
  module-name collisions. Scoping to `pytest.ini`'s own `testpaths` avoids it. It is leftover from an
  old merge and unrelated to tonight — **delete it if nothing imports it, and say so if anything does.**
- Some uncommitted files were already in the tree at session start: `.claude/hooks/block_dangerous.py`,
  `.claude/settings.json`, and a few `tools/` scripts. **Those are the founder's permission tooling,
  applied deliberately. Commit them; do not revert them.**

---

## Standing rules — these govern everything below

- **Challenge the premise before acting.** If an instruction here contradicts something recorded in
  the repo, halt and say so rather than complying. This has caught four bad instructions already.
- **Never reconstruct a missing artifact.** If a file you need is absent, HALT and report. Do not
  infer, rebuild, or write a stand-in. An agent did this on 2026-07-27 and wrote 113 lines of fiction
  to stand in for a real 248-line file.
- **Decide and log; do not ask.** Make the call, append a line to the session log, continue. Halt only
  if the action is irreversible, contradicts a written rule, or would lose work.
- **Stop on red.** Cannot produce evidence for a step → do not start the next one. Report and halt.
- **No multi-command blocks.** `&&`, `;`, `||` and newline-separated command blocks are all gated and
  will stop and wait for a human who is asleep. One command per call. Use `git -C <path>`.
- **Worktrees do not inherit `data/nfl.db`.** If you create one and run the backend suite, copy the
  database in first or ~21 tests fail for reasons unrelated to the work.
- **Never run a dev server from a worktree.** A merged worktree serves a stale build that is
  indistinguishable from the real thing at a glance. This wasted an hour on 2026-07-28.

---

## PHASE 1 — Find out what is actually true

Two branches are already in (see the top of this file). Verify that rather than trusting it — a
previous integrator may have gone further than reported.

1. `git -C . status --porcelain` — report anything uncommitted.
2. `git -C . log --oneline -20`
3. Confirm whether `main` matches `origin/main`.
4. List every branch ahead of `main` with its subject line.

**Four branches were created tonight:** frontend top-bar fixes, the acceptance harness, the mock draft
capture, and the session-log sharding. Some may already be in. **Report what you find before merging.
If you find more than four unmerged, stop and report.**

## PHASE 2 — Merge what remains

Order matters. **The first two are already merged — skip them.** Remaining:

1. ~~frontend top-bar fixes~~ — already in, `cc638ba`
2. ~~acceptance harness~~ — already in, `870750d`
3. **mock draft capture**
4. **session-log sharding — LAST**

**Why last:** the sharding branch freezes `docs/status.md` and `docs/founder-requests.md` and changes
how `CURRENT-STATE.md`'s build-state table is written. Merging it last lets the other branches' normal
appends land first.

**Expected conflicts, and how to resolve them:**

| File | Resolution |
|---|---|
| `docs/status.md`, `docs/founder-requests.md` | Append-only logs — **keep both sides**, in order |
| `docs/CURRENT-STATE.md` build-state table | Take the **generated** form, then re-run the generator |
| `docs/CURRENT-STATE.md` prose | Canonical single-value — **synthesise**, do not union |
| `docs/handoffs/OPEN.md` | Generated. Take either side, regenerate with `sync` |
| **Anything in code** | **HALT and report.** Do not resolve. |

## PHASE 3 — Verify, and report each result separately

1. **Fix the harness's player-count check first** (see the top of this file — the check encodes the
   old phrasing, the fix removed it). Assert the rendered count equals the real row count in the
   export, with no denominator required.
2. **Then run the acceptance harness** (`tools/acceptance/`) and confirm **9 of 9**. If any other
   check fails, report which and whether the fault is in the app or the check — do not silently
   "fix" either side.
3. Full backend suite, with counts and runtime. **Scope to `pytest.ini`'s `testpaths`** or the
   stale duplicate directory will break collection.
4. Full frontend suite, with counts.
5. `tools/handoffs.py check` — report verbatim.
6. The new session-log and founder-request sync tools.

**If any suite is red, halt.** Do not push a red tree.

## PHASE 4 — Land it

1. Push `main`.
2. Confirm working tree clean and stash empty. If the stash is not empty, **report its contents and
   leave it alone.**

## PHASE 5 — Founder decisions — ALREADY DONE, do not repeat

Recorded as D-025 and D-026 in `docs/decisions-needed.md`, commit `1a264a0`. Listed here only so you
can verify they are present and correctly worded:

**CLOSED, no work:** the data-loading and caching question. The multi-second delay is cold start on
first open, not navigation — in-app navigation was measured at zero network requests. Focus
revalidation, manifest diffing and progressive rendering are all dropped.

**NOT closed, now open as work:** the board already knows when its data is too old but shows it only
as small advisory text next to the refresh button. Promote it to an unmissable blocking state. File
under the standing priority *"the app does not lie about itself."* **Do not build it tonight.**

## PHASE 6 — Leave the app running and correct

1. **Kill every dev server currently running**, on every port, including any started from worktrees.
2. Start **one** server from the **main checkout** on port **5173**.
3. Confirm, with runtime evidence and not by reading code:
   - the board renders **511 players**
   - the header does **not** say "of 378"
   - the league reads **Westwood**
   - the **mode switcher is visible in the loaded state**, not clipped off-screen
   - the refresh button sits inside the top bar
4. Screenshot it and save the screenshot.

## PHASE 7 — Write the handover

Write `docs/status/2026-07-29-integration.md` containing:

- what merged, with commit hashes
- every test count, and any failure with whether it was deliberate
- the harness result, per check
- **every decision you made without asking, and why** — this is the most useful section
- anything you halted on
- what a fresh session should pick up first

Then run the log sync so it appears in the index, commit, and push.

---

## If you get stuck

Halt, push nothing red, and write what you know into the handover file. **A clean halt with a clear
note is a good outcome. Guessing is not.** The founder would rather find three merges and an honest
blocker than four merges and a surprise.
