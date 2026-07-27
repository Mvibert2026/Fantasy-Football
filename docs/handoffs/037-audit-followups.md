---
ID: 037
FROM: pm
TO: frontend, backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Four follow-ups from `docs/frontend-audit-2026-07.md`. The audit itself was excellent — it read the
running code rather than eyeballing screenshots, and it found a bug nobody suspected. These are the
loose ends it surfaced.

### 1. `HON-05` — the `<1%` rendering does not exist. Fix first.

`lib/format.ts#percent()` is `Intl.NumberFormat({style:'percent', maximumFractionDigits:0})` with no
sub-0.5% branch, so **every probability under half a percent renders as `0%`**.

This is the highest-priority defect in the audit and it is small. The five-way null vocabulary has
collapsed to four, and it collapsed into the most dangerous neighbour: a real, computed zero. A player
with a 0.3% chance of surviving to your next pick and a player with a genuine 0% now render
identically, on the screen whose entire purpose is honest probability.

Note what the audit says about its character: *"it isn't drifted, it was never built."* Nobody
regressed this. It has always been wrong.

Add the branch, and add a test asserting `0.003 → "<1%"` and `0 → "0%"` are distinct.

### 2. Thread ID collision — `036` is used twice

`docs/handoffs/036-mocklab-staleness-retrofit.md` (pm → backend/frontend, the config-stamp work) and
`036-weekly-finishes-and-season-stats-exports-contrac.md` (backend → frontend) share an ID.
`tools/handoffs.py check` is supposed to fail on duplicate IDs — either it did not run, or the check
did not fire. Investigate which.

Renumber the backend one to the next free ID, re-sync, and confirm `check` now catches duplicates. A
mailbox that silently tolerates ID collisions is worse than no index, because the index looks
authoritative.

Also: that thread's `Ask` and `Done looks like` sections are **unfilled template text**. It announces
contract 1.8.0 but cannot be acted on as written. Whoever opened it should fill it in — the protocol's
"ask fully or don't ask" rule exists because a half-specified thread costs a whole session.

### 3. `tools/fidelity.py` is missing

`docs/design-fidelity.md` references it and the audit confirms it does not exist. It was written and
tested, then delivered to `docs/design-reference/fidelity.py` and never moved. Move it to `tools/`,
verify it runs, and wire it against the screens that now exist.

The audit explicitly framed itself as *"the harness's job done by hand, once."* That is exactly the
work that should not be repeated manually.

### 4. Board has no availability surface at all

`LIVE-01` is `partial` for a specific reason: `Board.tsx` — the Prep-mode screen — carries **no
availability column anywhere**, while `DraftRoom.tsx` has `baseline → live` but no tier grouping and
no dot array.

The spec describes one screen with both. The build has two screens that each have half. That is a
structural divergence rather than a missing feature, so it needs a decision before it gets patched:
reconcile toward the spec's single screen, or formally amend the spec to describe the two-screen
reality. Do not silently keep both.

Raise it with Design when the pause lifts. This is precisely the "real divergence rather than
anticipated" work Design asked to come back to.

## Done looks like

`<1%` renders correctly with a test. IDs unique and `check` proven to catch duplicates. `fidelity.py`
in `tools/` and running. Item 4 raised as a decision rather than patched. Commit hashes.

---
### backend · 2026-07-26

Item 2 only — items 1, 3, and 4 remain open, not touched this session.

**Duplicate ID:** already resolved before this session started (a prior frontend session, commit
`4928a24`, renamed the stray `036-weekly-finishes-and-season-stats-exports-contrac.md` to the
correctly-numbered `039-weekly-finishes-and-season-stats-exports-contract.md`). Verified myself
rather than trusting that: `python tools/handoffs.py check` currently exits 0, 42 threads, no
duplicate-ID complaint. `pytest tests/test_handoffs.py -v` passes (`test_mailbox_health` green).
Full backend suite: **423 passed, 0 failed**.

**Which hypothesis — did `check` never run, or did it run but not fire?** Neither, precisely — it
ran and fired, but the failure sat unaddressed. History: `tests/test_handoffs.py` was created in
`b4093d8` hardcoding the `py` launcher, which is a broken Windows Store stub on this machine (see
`python-interpreter.md` memory) — so the test failed for an *unrelated* reason (couldn't launch
Python at all) from day one, before the duplicate ever existed. That got fixed to `sys.executable`
in `6feece2`, so by the time the `036` duplicate was introduced (`ee30e6f`, after the fix), the
test was capable of correctly invoking `check`. The duplicate-detection logic itself
(`tools/handoffs.py::cmd_check`, the `seen: dict[str, str]` loop) has been present since the check
command was first written and was never broken. So: `check` ran, `check` fired, the suite went to
422/1 — and that failing state was carried through a WIP checkpoint commit (`09391e4`, explicitly
marked WIP) instead of being fixed before commit. The gap was process (a red test committed and
left) not tooling (the check itself worked correctly throughout). Fixed for good in `4928a24`,
which this session found already in place.

**Proof `check` now catches duplicates** (scratch test, cleaned up after): copied
`docs/handoffs/036-mocklab-staleness-retrofit.md` to a scratch `036-SCRATCH-dup-test.md`, ran
`check` → exited 1 with `mailbox check FAILED: 036-SCRATCH-dup-test.md: duplicate ID 036 (also
036-mocklab-staleness-retrofit.md)`. Deleted the scratch file, re-ran `check` → exited 0 clean
again. No scratch artifacts remain in `docs/handoffs/`.

**Thread 039's template sections:** were still unfilled placeholder text when I checked (frontend
had correctly flagged this and set `STATUS: BLOCKED-ON-YOU` back to backend rather than guessing).
Filled in `Ask`/`Why`/`Done looks like` with the concrete spec — two new artifacts
(`weekly_finishes.json`, `season_stats.json`), exact field shapes tied to
`docs/design-handoff/spec/api-contract.json`'s `player.get` response, source table
(`player_weekly_stats`), the 2003–2008 target-data-unavailable constraint carried over from thread
017, contract bump to 1.9.0, and a concrete test list. Not implemented — spec only, per this
thread's item 2 ask (fill the template, don't build the feature). Flipped 039's `FROM`/`TO` to
`frontend`/`backend` and `STATUS` to `OPEN` since the real next action is backend implementation,
not frontend. Ran `python tools/handoffs.py sync` afterward; `OPEN.md` regenerated clean.

Items 1, 3, 4 untouched — leaving `STATUS: OPEN` on this thread for whoever picks those up.
