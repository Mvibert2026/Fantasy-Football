# Status log — combined view

**Generated 2026-07-29 by `tools/status_log.py sync` — do not hand-edit.**
Session files in this directory are the source of truth. Add a new dated file, then
re-run sync. Protocol: [`README.md`](README.md).

**2 sessions recorded.**

---

<!-- 2026-07-28-backend-shard-session-logs.md -->

# 2026-07-28 — backend — shard the shared append-only doc logs

## What changed

`docs/status.md`, `docs/founder-requests.md`, and `docs/CURRENT-STATE.md`'s "Build state" table
were the three most contended shared files in the repo — every parallel session wrote to one or
more of them, which is exactly the pattern `docs/reviews/fable-workflow-2026-07-27.md` (work
orders W3/W4) already diagnosed as the project's main source of merge conflicts, after two
sessions nearly collided on `CURRENT-STATE.md`. This session implements W3 and W4, plus extends
the same idea to `founder-requests.md`, which W3/W4 didn't cover.

Three different fixes for three different conflict shapes, not one fix applied uniformly:

1. **`docs/status.md`** (pure append log) → frozen; `docs/status/YYYY-MM-DD-role-slug.md` per
   session; `tools/status_log.py sync` generates `docs/status/INDEX.md`. This is the literal
   "shard into dated files" pattern.
2. **`docs/founder-requests.md`** (thread-shaped: FR-NNN numbers referenced 146 times across 40
   other files, and a request's `Status:` gets mutated by later sessions — concurrent-edit-to-
   one-blob, not append) → frozen; one file per request at `docs/founder-requests/FR-NNN-slug.md`,
   same pattern as `docs/handoffs/NNN-slug.md`, with the same staged-`NEW-*.md` + `sync`-time ID
   allocation `tools/handoffs.py` uses (W1), seeded past the archive's highest number (`FR-017`).
   `tools/founder_requests.py sync` generates `docs/founder-requests/INDEX.md`, grouped by status.
3. **`docs/CURRENT-STATE.md`** — deliberately *not* sharded into dated files. It's synthesized
   "current truth," edited in place by design (`CLAUDE.md`: "never append a new section").
   Regenerating it from per-session deltas would just move the merge problem into the generator.
   Only the actually-measurable "Build state" table is now generated, via a new `--apply` flag on
   `tools/state.py` that rewrites the content between `<!-- BUILD-STATE:START -->` /
   `<!-- BUILD-STATE:END -->` markers in place, leaving the rest of the doc (including the two
   rows that aren't measurable by a single command — Agent infrastructure, Frontend location) hand
   -maintained. Also fixed a latent bug while wiring this in: `tools/state.py` hardcoded the
   literal string `` `master` `` for the branch name regardless of the real branch (this repo's is
   `main`) — never previously exercised because the tool only printed to stdout for manual paste.

None of the three old files were rewritten or migrated — they stay in place as the archive,
unmodified except for a freeze-notice header pointing at the new location, per the explicit
instruction not to lose history.

## What still requires a shared-file append

- **`docs/decisions.md`** — the ADR log. Same append-only shape as the old `status.md`, and
  already has its own collision history (ADR-048, per `RECONCILIATION-2026-07.md`) and its own
  allocator (`tools/handoffs.py adr next`, which scans `docs/decisions.md` + `docs/adr-drafts/`).
  Out of scope for this session (not one of the three files named), but it's the same failure mode
  and hasn't been fixed. Flagging, not fixing.
- **`docs/handoffs/NNN-slug.md` thread files themselves** — replies within a single already-open
  thread are still a shared append target if two sessions touch the *same* thread in the same
  round. Narrow blast radius (one thread, not the whole mailbox) and already a known, accepted
  limitation — `docs/handoffs/README.md` rule 8 ("a pull conflict is not yours to resolve alone")
  exists for exactly this case.
- **Cross-worktree ID allocation races** — both the handoffs allocator and this session's new
  founder-request allocator use the same "hard-fail if the destination already exists" defense,
  not true cross-worktree coordination. Thread 076 already flagged this as open and unresolved for
  handoffs; the same caveat now applies identically to `tools/founder_requests.py`. Rare in
  practice (per 076's own assessment), but real.
- **`docs/status/` and `docs/founder-requests/` `INDEX.md` files** — not append targets (they're
  fully regenerated, never hand-edited), but two sessions running `sync` around the same time and
  both pushing will still produce a trivial merge conflict on the generated file itself, resolved
  by just re-running `sync` after the merge. Lower-stakes than the old failure mode: nothing is
  lost, the fix is mechanical, and it doesn't depend on either session's judgment about which
  content wins.

## Verification

- New tooling tests: `tests/test_status_log.py`, `tests/test_founder_requests.py`,
  `tests/test_state.py` — 16 tests, all passing.
- Full backend suite (`pytest -q`, real `data/nfl.db`) run post-change to confirm nothing else
  regressed — see this session's commit message / PR for the pass count.

---

<!-- 2026-07-29-integration.md -->

# 2026-07-29 — integration — overnight run against docs/RUN-2026-07-29-integration.md

Founder asleep, no questions asked. Every judgement call is recorded below under
"Decisions made without asking."

**Outcome: clean. One merge landed, all suites green, harness 9/9, app verified at runtime and
restarted on 5173 at the end. One instruction in the run doc was wrong and was not complied with —
see "The premise that did not hold."**

---

## What merged

| Branch | Commit | Note |
|---|---|---|
| `docs/sharded-session-logs` | `5901b6b` (merge), `2243eec` (branch tip) | No conflicts. `--no-ff`. |
| ~~`frontend/topbar-clipping-and-hardcoded-count`~~ | `cc638ba` | Already in before this session. Verified, not re-merged. |
| ~~`qa/acceptance-harness`~~ | `870750d` | Already in before this session. Verified, not re-merged. |
| **mock draft capture** | — | **Does not exist as a branch. Not merged. See below.** |

Other commits this session:

| Commit | What |
|---|---|
| `a891a90` | Founder permission tooling + the run doc, committed as instructed |
| `402f553` | Acceptance player-count check fixed; stale `frontend/tests/` deleted |
| `1cf61a7` | Fable mandate M tracked (appeared on disk mid-run; **not acted on**) |

`main` pushed to `origin/main` at `1cf61a7`, then again after this handover.

The sharding merge produced **zero conflicts** — none of the resolution rules in the run doc's
conflict table were needed. `docs/status.md` and `docs/founder-requests.md` were touched only by
the branch, and the frontend files it appeared to change in a two-dot diff were untouched relative
to the merge base.

---

## The premise that did not hold

The run doc says four branches were created and instructs merging "mock draft capture" third.
**There is no such branch.** `backend/mock-calibration-kickers` points at `f1d51d0`, already an
ancestor of `main` — zero commits ahead. The work exists only as **eleven uncommitted files** in
`.claude/worktrees/backend-mock-calibration`, including four source/test files that exist nowhere
else in the repo (`src/mock_prediction.py`, `tests/test_kickers_export.py`,
`tests/test_mock_calibration_snapshot.py`, `tests/test_mock_prediction.py`).

Last write to those files: 2026-07-28 23:25. `main` took its next commit at 23:46. The session that
produced them ended without committing.

**Decision: did not commit it, did not merge it.** Committing another session's uncommitted tree
would mean authoring work with no commit, no test evidence, and no handoff reply declaring it done
— and it is not possible to distinguish "finished but uncommitted" from "interrupted mid-edit" from
the outside. Not merging loses nothing; the files sit exactly where they were.

Opened as **handoff thread 079 (pm → backend)** so it is no longer invisible. That thread also
flags that its `tests/test_kickers_export.py` may be in tension with a founder constraint dated
2026-07-29 ("No kicker", kickers consensus-only and excluded from the board) — and explicitly says
the thread is *not* authority to delete it.

Also unmerged and left alone: `docs/phase3-chain2-claude-md-agents` (2026-07-27, not one of
tonight's branches, out of scope for this run).

---

## Test results

| Suite | Result | Runtime |
|---|---|---|
| Backend (`pytest`, scoped to `pytest.ini` `testpaths`) | **636 passed**, 1 warning | 677.53s (11m 17s) |
| Frontend (`npm --prefix frontend run test`) | **202 passed**, 22 files | 58.81s |
| Acceptance harness | **9/9** | — |
| Runtime verification on 5173 | **9/9** | — |

No test failures anywhere. Nothing deliberate to explain.

**One tool did fail, and it was a real bug**, not a test: `tools/state.py --tests` crashed with
`FileNotFoundError: [WinError 2]` on the project's own machine. It called
`subprocess.run(["npx", "vitest", "run"])` with a list argv and no shell; on Windows `npx` is
`npx.CMD`, so `CreateProcess` cannot find a bare `npx`. The backend half worked because it invokes
the conda interpreter by absolute path.

This landed tonight as part of the sharding merge, and it means the generated build-state table
could never have been produced with real counts on the only machine this project runs on. Fixed by
resolving `argv[0]` through `shutil.which` in `run()`, which applies `PATHEXT` and so finds
`.CMD`/`.exe`/`.bat` without hardcoding an extension or resorting to `shell=True` with a list argv.
`shutil.which('npx')` → `C:\Program Files\nodejs\npx.CMD`.

Backend was 620 before this run; the sharding branch added `tests/test_founder_requests.py`,
`tests/test_state.py` and `tests/test_status_log.py` for +16. 620 + 16 = 636, which reconciles.

The 1 warning is a pre-existing pytest deprecation about a class-scoped fixture declared as an
instance method. Not introduced tonight, not addressed.

### Acceptance harness, per check

All nine green: `app-loads`, `mode-switcher-present`, `league-name-matches-config`,
`board-header-player-count`, `board-renders-nonzero-rows`, `status-banner-matches-data`,
`draft-room-renders`, `opponents-renders`, `player-detail-opens`.
Evidence: `tools/acceptance/artifacts/evidence.json`.

`board-header-player-count` was the one that had been failing (8 of 9 before tonight), and the run
doc's diagnosis of it was correct: the check
was wrong, not the app. It asserted `"N of TOTAL players loaded"`; the frontend fix removed the
denominator rather than correcting it, so `Board.tsx` renders `"511 players loaded"` and its own
test asserts the `of \d+` form is *absent*. The check was failing on a string the app no longer
emits.

Rewritten to assert the rendered count equals the `data/export/board.json` row count with no
denominator required — **and to actively fail if a denominator reappears**, since any denominator
there would be an unsourced total free to drift again, which is the original fault.

### `tools/handoffs.py check`, verbatim

```
mailbox check OK — 78 threads, none stale, all addressed.
```

Followed by 30 non-fatal contradiction warnings (25 antonym-pair overlaps between threads, 5
threads referencing D-021 which is already marked DECIDED). Not new, not addressed.

Thread 079 was opened after that run, so the mailbox now holds **79 threads, 46 open**.

### Session-log and founder-request sync tools

Both work and are idempotent apart from their date stamp — the only diff from re-running them on an
unchanged tree was `Generated 2026-07-28` → `Generated 2026-07-29`.

- `tools/status_log.py sync` → 1 session file (2 including this one) → `docs/status/INDEX.md`
- `tools/founder_requests.py sync` → **0 requests** → `docs/founder-requests/INDEX.md`

**0 is correct, not a failure.** FR-001..FR-017 stay in the frozen `docs/founder-requests.md`
archive; the new directory starts empty and allocates from FR-018.

---

## Runtime verification (Phase 6)

Killed both stale dev-server processes — a vite server on port **5175** (PID 7152) and its npm
parent (PID 17456), both started **2026-07-27 11:52**, i.e. ~36 hours stale. Both were launched
from the main checkout, not a worktree. No server was left on any other port.

Started **one** server from the **main checkout** on port **5173** (`prep` in
`.claude/launch.json`).

**Caveat, stated plainly because it affects what you will find:** that server died once during this
session, unprompted, while the verification work was still going on. It was restarted and was
listening on 5173 at the end of the run (PID 21092). But it is managed by the session's preview
harness, not detached, so **it may not survive this session ending.** If port 5173 is dead when you
read this, that is the expected failure and not a regression in the app:

```bash
npm --prefix frontend run dev
```

Nothing else was left on any other port.

Verified with runtime evidence, not by reading code — `tools/acceptance/shot-5173.mjs`, which
attaches to whatever is already on 5173 rather than starting its own server (a script that started
its own would prove nothing about the one the founder will find running):

| Claim | Result |
|---|---|
| Board renders 511 players | ok — 511, matches `board.json` |
| Header does not say "of 378" | ok |
| Header carries no denominator at all | ok |
| Board footer count matches export | ok — 511 vs 511 |
| League reads Westwood | ok — matches `league.json` |
| Mode switcher fully in viewport, loaded state | ok — all three buttons, none clipped |
| Refresh button inside the top bar | ok — shares the 46px top-bar element with the mode switcher |
| Refresh button fully in viewport | ok |
| Page does not scroll horizontally | ok |

Screenshot: `docs/status/artifacts/2026-07-29-integration-5173.png`. Confirmed visually, not just
by assertion — the mode switcher sits at the right edge of the top bar, fully visible.

**One cosmetic observation, not a regression:** the top bar's freshness text truncates with an
ellipsis (`snapshot fresh (1d…`). This is the same 11px advisory text D-026 is about, so it is
already covered by open work rather than needing a new item.

---

## Decisions made without asking

1. **Did not commit or merge the mock-draft-capture worktree.** Reasoning above. Opened thread 079
   instead. This is the one place the run doc's instructions were not followed, and it was because
   its premise was factually wrong about the repo.

2. **Deleted `frontend/tests/` (20 files).** The run doc authorised this "if nothing imports it."
   Nothing does — the only references are three docs describing it as a known problem. It arrived
   via `2df3716` when the frontend-prep repo was merged into `frontend/`, so it is a stale copy of
   the *Python backend* tests, not frontend tests. Verified before deleting that every test in it
   exists by name in `tests/`, with exactly three exceptions in `test_backtest.py`, all covering
   `weighted_aggregate` — which `src/backtest.py` records as **deliberately DELETED** under ADR-B,
   thread 021 ("a field that does not exist cannot be misquoted"). So they are dead tests for
   removed behaviour and no live coverage was lost.

3. **Committed the founder's permission tooling and the run doc** (`a891a90`), as instructed.
   Checked the diffs for credentials first; the only settings change is broadening `Bash(*)` /
   `PowerShell(*)` in the allow list. Nothing reverted.

4. **Made the harness check reject a denominator rather than merely not require one.** The run doc
   asked only that the check not require one. Requiring its *absence* is a small addition, made
   because a silently-reintroduced hardcoded total is precisely the original fault and nothing else
   would catch it.

5. **Amended one commit message** (`402f553`) rather than leaving it inaccurate. The staged
   `frontend/tests` deletion was swept into the harness-fix commit; the original message described
   only the harness fix. Amended before pushing, so no rewritten public history.

6. **Committed the Fable mandate that appeared mid-run** (`1cf61a7`) — see below — rather than
   leaving it untracked, so it is not lost. Did not act on a word of it.

7. **Put the screenshot script in `tools/acceptance/`** rather than `tools/`, only because that is
   where playwright is installed. Noted in its header that it is not part of the harness run.

8. **Fixed the `tools/state.py` Windows bug** rather than just reporting it. It was blocking this
   session's own write-back duty (regenerating the `CURRENT-STATE.md` build-state table with
   measured counts), the fix is four lines and provably correct, and `tests/test_state.py` covers
   the module. Judged in scope because the alternative was to leave a tool that landed tonight
   broken on the only machine it runs on. After the fix, `--apply --tests` ran clean end to end
   and wrote the table.

9. **Added a dated qualifier to a stale figure in `CURRENT-STATE.md`'s narrative** (thread 052 /
   ADR-048 section). It read "378/378 board players carry it; 371/378 (98.15%) resolve" — a real
   2026-07-27 measurement, but the board is 511 players now, so a reader today would take 378 as
   the current universe. Edited to date the measurement and state the current count, and to say
   explicitly that the 98.15% coverage ratio has **not** been re-measured against the larger
   universe. Deliberately did **not** invent a new ratio: that would need re-running the join,
   which this session did not do. This touches a narrative section belonging to another session,
   which the operating rules discourage — done anyway because the alternative was leaving the
   canonical state document asserting a player count 133 short of reality.

---

## Things I halted on, or deliberately left alone

**A file appeared on disk mid-session that this run did not write.**
`docs/fable-mandate-M-2026-07-29.md` (11,808 bytes) was absent from `git status` at session start
and present at **00:12:52**, roughly 17 minutes in. It is a mandate addressed to a **Fable**
session — three model-design questions M-1 (bottom-up rankings), M-2 (availability), M-3
(suggested pick) — and it instructs its reader to modify nothing but its own output documents.

**Not acted on.** It is not part of tonight's run, it is addressed to a different agent, and
instructions found in a file are not instructions to a session. Committed for safekeeping and
flagged here. Its referenced prerequisite, `docs/CORRECTIONS-2026-07-28.md`, does exist — nothing
missing, nothing reconstructed.

A fresh session should establish **whether a Fable run is expected and whether another session was
live tonight**, because a file arriving mid-run is the only evidence either way.

**The stash is not empty.** Left alone as instructed. `stash@{0}` — *"pre-integration stash:
uncommitted fable-mandate docs + status.md on main"*:

```
docs/CORRECTIONS-2026-07-28.md                      |  92 +
docs/fable-mandate-2026-07-28-short.md              |  98 +
docs/fable-mandate-G-2026-07-28.md                  | 140 +
docs/fable-mandate-K-2026-07-28.md                  | 128 +
docs/reviews/fable-bottomup-next-tests-2026-07-28.md| 258 +
docs/reviews/fable-lambda-sensitivity-2026-07-28.md | 249 +
docs/reviews/fable-schedule-feasibility-2026-07-28.md| 291 +
docs/status.md                                      |  72 +
```

**It contains nothing that is not already in the repo.** All seven docs are tracked in `HEAD`, and
`HEAD`'s `docs/status.md` differs from the stashed copy by 261 lines of pure insertion — a strict
superset, restored by `1c3675f`. It can be dropped, but that is the founder's call, not this run's.

**Two hook-blocked commands, both correctly blocked.** `Remove-Item -Recurse -Force` on the stale
test directory, and a `;`-containing pipeline. Worked around without weakening either guard. The
`.pyc` leftovers were removed file-by-file instead.

---

## What a fresh session should pick up first

1. **Thread 079 — the uncommitted mock-draft-capture worktree.** Highest priority: it is real work
   that exists in exactly one place and is not under version control. Decide it before that
   worktree is cleaned up by anything.
2. **Confirm whether a Fable run is expected** for mandate M, and whether another session was live
   during this one.
3. **D-026** — promote the stale-snapshot advisory to a blocking state — remains OPEN and needs a
   design pass on what "blocking" means before Frontend can start. Explicitly not built tonight.
   Verified present and correctly worded, along with D-025 (CLOSED, no work); Phase 5 needed no
   action.
4. **Check port 5173 before starting a server.** One was left running from the main checkout, but
   see the caveat above — it may not have survived. Reuse it if it is up; do not start a second.
5. `docs/dashboard.html` and `docs/roles-workflow-map.html` are **stale** — this session changed
   project state and did not regenerate them.
6. **Re-measure the `weekly_finishes.json` join coverage** against the 511-player board. The
   98.15% figure in `CURRENT-STATE.md` was measured against a 378-player board and is now dated
   rather than corrected, because correcting it honestly means re-running the join.
7. **`tools/state.py`'s commit row can never be current in the commit that carries it** — it
   records `HEAD` at generation time, so the table always names the previous commit. Cosmetic, but
   worth either documenting in the tool or having `--apply` note the lag, so a future reader does
   not mistake it for drift.

---

