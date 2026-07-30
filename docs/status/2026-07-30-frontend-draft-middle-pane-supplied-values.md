# 2026-07-30 — frontend: draft middle pane tabs + supplied-values colour fix

Two design specs ported in order, per dispatch: `docs/design/DRAFT-MIDDLE-PANE.md` (priority 1),
then `docs/design/SUPPLIED-VALUES.md` (priority 2). Grid (FR-044) explicitly excluded per the
dispatch — design's colour rule for it is unpicked and waiting on reference captures. Worktree
`agent-a160788e8e9ccc925`.

## 1 · Draft middle pane (`docs/design/DRAFT-MIDDLE-PANE.md`)

The middle pane's old fixed stack (RECOMMENDED-when-on-clock, else POSITION SCARCITY + Queue/Watch
+ NEXT DECISION, all in one column) is now one tab set — **Recommend · Scarcity · Queue ·
Insights** — inside the existing Board/Opponents/Predictions hub, with NEXT DECISION as a
persistent footer under the tab content, never behind a tab. `frontend/ui/views/DraftRoom.tsx`.

- **FR-049 (tabs + recommendations before my pick).** Recommend is the default tab. A look-ahead
  toggle inside it (not a second tab, per the spec) switches between "this pick" (on the clock,
  exactly the pre-existing RECOMMENDED card, byte-for-byte) and a look-ahead computed at the
  user's next real turn — `roundOfPick`-aware (e.g. the early-QB penalty relaxes past round 6),
  honestly labelled "computed on today's board — does not account for players taken between now
  and then" since there is no model here for who else will be gone by then. Off the clock,
  look-ahead is the only content (no toggle rendered — nothing to switch away from). The give-up/
  VBD-override reasoning is deliberately not generalised into the look-ahead branch (documented
  scope limit, `recommendationDetailLookAhead`'s own comment).
- **FR-051 (next-pick reference point).** "Show the reference point, do not do the arithmetic" —
  CONSIDERING / LIKELY THERE AT `<pick>`, two plain name+VBD figures, no subtraction. Scoped to the
  base on-clock "this pick" state only. "Likely there" = highest-VBD available player (excluding
  the one being considered) with ≥50% live-adjusted survival odds — `findLikelyThereCandidate`,
  same convention `scarcity.ts`'s `under50ByNext` already uses. **Divergence from the mock,
  disclosed:** the mock's "VBD 54.1 · 48.9–58.2 across σ" looks like an illustrative placeholder —
  VBD is a static per-player field, not sigma-dependent. Built the range as a survival-probability
  spread (sigma 5/10/20) instead, reusing `Predictions.tsx`'s own `RangeCell` idiom
  (`ReferenceSurvivalRange`). Display only, not fed into the recommendation, per the ticket.
- **FR-045 (pace suppression).** `positionScarcity` gained `hasAutoFillPlaceholders`; when true,
  `pace` is null and a new `paceSuppressedReason` explains why (auto-filled picks are unknown
  players, so `gone` and `expected` are drawn from different populations). `paceLabel()` renders
  the reason in place of the direction phrase. `under50ByNext`/`depletionWarning`/`tierDepletionLine`
  confirmed unaffected (keyed to `nextUserPick`, not `currentPick`).
- **FR-048 (Insights tab).** Built the tab shell, honestly empty: "Not built yet" naming the
  missing `findings.json` artifact (`status`/`applies_to.pick_range`) rather than approximating
  from `nulls.json`'s unscoped findings or the assistant's retrieval corpus, neither of which
  carries pick-range attribution. No change to FR-048's own STATUS — the substantive ask is
  unbuilt.
- **FR-044 (grid)** confirmed out of scope per the dispatch and design's own manifest — not
  touched.

Screenshots (`frontend/e2e/artifacts/`, script `frontend/e2e/verify-draft-middle-pane-tabs.mjs`):
`middle-pane-1-recommend-this-pick.png`, `-2-recommend-look-ahead.png`, `-3-scarcity.png`,
`-4-scarcity-pace-suppressed.png`, `-5-queue.png`, `-6-insights.png`. Looked at directly, not just
captured — confirmed the reference point renders on-clock and disappears under look-ahead, the
pace-suppression text renders for every position with zero stale "ahead/behind of pace" phrases
after Auto-fill, and the tab bar + NEXT DECISION footer persist across all four tabs.

Tests: `frontend/ui/__tests__/draft-room-middle-pane-tabs.test.tsx` (new, 8), plus 2 new unit tests
in `formulas.test.ts` and updates to `draft-room-scarcity-and-sort.test.tsx` (7 tests now click
into the relevant pane tab first, matching the new interaction model — was pre-existing content
in the default off-clock view).

**Opportunistic, not in either spec: thread 093 (contract 1.15.0) closed.** It was already the one
pre-existing red test in the 251-test baseline (`trace-fields.test.ts`, confirmed via `git stash`
before touching anything). Bumped `EXPECTED_CONTRACT`/`TRACE_CONTRACT` to `1.15.0`, added a
`TRACE_CHANGELOG` entry. No UI surfacing of `scoring_ruleset_note` this session — replied to the
thread with "no UI change, version check updated," its own stated alternative. `STATUS: RESOLVED`.

**Found and fixed a real, pre-existing bug in `docs/design-reference/fidelity.py`** while trying to
run it per this session's brief: an off-by-one `.parent.parent` computed `REPO_ROOT` one directory
too shallow (the script lives at `docs/design-reference/fidelity.py`, two levels deep, not one).
Fixed. Even fixed, the harness cannot check this build today — `screens.json` names routes
(`/draft/board` etc.) the app doesn't have (no router; tab switching is component state), and no
per-screen reference HTML is committed (only one old monolithic `prototype.dc.html` plus PNGs
under `reference/` that aren't wired as harness input). Did not attempt the larger fix — real
architecture decision, not mine to make unilaterally. Used direct Playwright screenshots instead,
matching `docs/design-fidelity.md`'s own stated fallback. Full detail in `docs/ideas-inbox.md`.

## 2 · Supplied values (`docs/design/SUPPLIED-VALUES.md`)

Both named controls used `--acc` (the board's delta/"good" colour) to mark a value the founder
supplied himself. Fixed per the spec's rule: a supplied value now carries a dotted underline (the
one and only "you put this here" signal in this app) plus a lowercase marker naming how it got
there — never a semantic accent.

- **Typed opponent name** (`frontend/ui/views/Opponents.tsx`, FR-036). Name renders in `--txt` with
  a dotted underline instead of `--acc`; the bordered uppercase `TYPED` badge is now a plain
  lowercase `typed` label (monospace, no border). The "×" clear-to-sourced control was already
  neutral-coloured, unchanged.
- **TopBar SLOT override** (`frontend/ui/components/shell/TopBar.tsx`, FR-034). Border, `SLOT`
  label and value no longer switch to `--acc` when overridden; the value carries a dotted
  underline; "· sourced N" became "· set by you, league file says N" (same field, clearer
  wording, keeps the sourced value visible per the spec's disclosure rule); the clear button lost
  its accent border/colour.
- **Third instance, not named in the spec but the same defect and the same value:**
  `Predictions.tsx`'s own "predicting under" line shows the identical overridden slot in the
  identical `--acc`. Fixed the colour and added the dotted underline; kept the existing
  "overridden, sourced N" wording (a `predictions.test.tsx` assertion pins that exact phrase, and
  design didn't specify new copy for this spot).

Screenshots (`frontend/e2e/artifacts/`, script `frontend/e2e/verify-supplied-values.mjs`):
`supplied-1-topbar-slot-overridden.png`, `supplied-2-opponents-typed-name.png`. Looked at directly.

Tests: `frontend/ui/__tests__/topbar-supplied-slot.test.tsx` (new, 2 — asserts no `--acc` anywhere
on the overridden control and the exact dotted-underline style, plus the "no marker when not
overridden" case), and one new test each in `opponents.test.tsx` and `predictions.test.tsx`.

## Verification

`npx tsc -b --noEmit`: clean. Full suite: **265 passed, 0 failed** (251 baseline + 14 new:
8 in `draft-room-middle-pane-tabs.test.tsx`, 2 in `formulas.test.ts`, 2 in
`topbar-supplied-slot.test.tsx`, 1 each in `opponents.test.tsx`/`predictions.test.tsx`). One
full-suite run hit a flaky timeout in `draft-room-typeahead.test.tsx`; re-ran that file alone —
25/25 passed clean, matching the exact container-CPU-contention flake pattern already documented
in `docs/CURRENT-STATE.md` for this repo (reproduced against unmodified code before, not a
regression here — did not re-verify against unmodified code this session, relying on the prior
session's documented finding plus this file's own clean isolated re-run).

## Commits

See git log for this worktree branch — one commit per spec plus a closing docs/status commit, per
the task's instruction to commit after each spec.
