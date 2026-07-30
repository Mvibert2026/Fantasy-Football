# 2026-07-30 · frontend · INERT-CONTROLS + TWO-TRACK-EXPRESSION

**Role:** frontend (Sonnet, effort 4-5 per operating-model.md's fidelity-critical exception).
Cloud session, `docs/frontend-cloud-runbook.md` throughout. Worktree
`agent-ad095d79402a3a50d`.

## What was asked

Build two of design's specs from tonight's handoff (`docs/design/MANIFEST-2026-07-29.md`,
priorities 3 and 4):

1. `docs/design/INERT-CONTROLS.md` (FR-037) — one treatment for the six present-but-inert
   controls the founder has been clicking and finding dead.
2. `docs/design/TWO-TRACK-EXPRESSION.md` (FR-042, FR-027) — how a screen says "this league is
   the generic track" without reading as broken.

Explicitly out of scope: `views/DraftRoom.tsx` and the opponent-name/draft-slot controls, owned
by a sibling agent this same round.

## INERT-CONTROLS — built

Design's rule: "A control that cannot act is not a control. Render the fact instead of the dead
affordance." Applied to the real six from `docs/CURRENT-STATE.md`/FR-037's inventory (not the
same six named in design's own worked-example table, which lists Refresh data — already fixed
before this session — instead of League settings; see below):

- **Export CSV / Export PDF** (`ui/views/Board.tsx`) — both buttons removed; folded into the
  board's existing provenance line as one clause: `... 510 players loaded · export not built`.
- **Compare / Ask** (`ui/components/PlayerDetail.tsx`) — both removed from the sticky action row
  outright, no replacement text (design: "the row shrinks; it does not hold a gap"). The
  always-reachable assistant dock already does Ask's job.
- **Ask the assistant per glossary term** (`ui/views/Glossary.tsx`) — removed from every term
  card. The dock stays; the per-term button is gone.
- **League settings** (`ui/components/shell/TopBar.tsx`) — button removed, replaced with plain
  non-interactive text: "Settings — not built". Design's own INERT-CONTROLS.md table doesn't name
  this control (it has a separate, fuller spec, `docs/design/LEAGUE-SETTINGS-BOUNDARY.md`,
  priority 5, not built this pass) — decided to apply the general rule anyway rather than leave a
  dead button until that ships; logged in `docs/ideas-inbox.md` as the one real seam found between
  design's table and the task's own six-control list.

`docs/founder-requests/FR-037-*.md` updated to `STATUS: SHIPPED` with a `## Resolution` section.

## TWO-TRACK-EXPRESSION — built

Design's rule: split the old single "Not available for this league" string into three real
claims (primary / generic / not yet), and put the track on the league selector so the thinning is
expected before it's encountered.

- **New `LeagueTrack` type** (`ui/data/types.ts`): `isPrimary`, `scoringRulesetNote` (verbatim
  `league.json:scoring_ruleset_note`, contract 1.15.0), `opponentsModelledCount` (`teams - 1` for
  the primary league only — a real structural fact, never a claim about how many opponents carry
  behavioural data; `opponents.json`'s own `coverage_warning` stays the separate, honest source
  for that).
- **Computed once at sync time**, not client-side: `frontend/scripts/sync-exports.mjs` reads each
  league's own copied `league.json` (root and all 26 sub-leagues) and writes `track` into
  `_leagues.json` per league, plus a new top-level `primary` entry for the default league itself
  (previously `_leagues.json` said nothing about the primary league at all).
- **League selector** (`ui/components/shell/TopBar.tsx`): every `<option>` gets a ●/○ marker
  before the label (visible in the dropdown before a selection is made — confirmed via
  `page.locator('select option').allTextContents()`, native-select popups don't screenshot). The
  currently-loaded league gets a compact PRIMARY/GENERIC badge next to the switcher, `title`
  carrying the full sentence design's mockup shows plus the sourced field path. Kept the
  always-visible text short rather than the full sentence — measured that the top bar's existing
  freshness note and league-detail string already truncate with an ellipsis at this app's usual
  screenshot width before this badge existed, so a second full sentence had nowhere to go without
  a hard mid-word clip (see `inert-04b-topbar-wide.png`, the same bar at 2200px, unabbreviated —
  proof the content is correct, just too long for the bar's normal width).
- **`StrategyGuide.tsx`**: the null-state message now branches on
  `league.json:league_id === "primary"`. Generic-track leagues get a confident, track-named
  message ("Generic track — no strategy simulations... That is the track this league is on, not a
  step that was skipped"); the primary-league branch (not reachable against any current export,
  kept for correctness if it ever is) keeps the old, more provisional wording.
- **`Methodology.tsx`**: new "Scoring ruleset" section rendering `league.scoringRulesetNote` in
  full — the second surface thread 093 asked about, alongside the selector badge.
- **Contract pin bump**: `EXPECTED_CONTRACT`/`TRACE_CONTRACT` were still 1.14.0 against a real
  1.15.0 export (ADR-062, backend, earlier the same day) — this was the one pre-existing red test
  found before any of this session's own changes, and exactly what thread 093 asked frontend to
  confirm. Bumped both, added the `TRACE_CHANGELOG` entry, replied to thread 093 and set
  `STATUS: RESOLVED`.

**Scope decisions logged, not asked** (`docs/ideas-inbox.md`, 2026-07-29 frontend entry): left
`views/Opponents.tsx` untouched (sibling agent's file this round, even though the two-track story
fits it conceptually), and corrected a `docs/CURRENT-STATE.md` claim in passing — `weekly_finishes
.json`/`season_stats.json` are fetched from a genuinely shared, unprefixed path regardless of
league (`ui/data/playerHistory.ts`'s own doc comment), so they don't actually thin the PlayerDetail
history sections per-league the way `strategies.json` thins StrategyGuide; only one screen, not
three, is really affected by that specific artifact gap.

`docs/founder-requests/FR-027-*.md` (STATUS left `NEW` — this closes the UI-expression slice, not
the API-in/connected-settings direction) and `FR-042-*.md` (STATUS already `DONE` from backend)
both got an `## Update`/note pointing at this work.

## Evidence

- `npx tsc -b --noEmit`: clean.
- `npm test`: **261 passed** (251 baseline + 10 new, `ui/__tests__/inert-controls-and-two-track
  .test.tsx`), 0 failed, 28 test files.
- Screenshots, looked at directly, `frontend/e2e/artifacts/`:
  `inert-01-board-westwood.png` (no Export buttons, provenance line carries the fact),
  `inert-02-player-detail-action-row.png` (only Watchlist remains in the action row),
  `inert-03-glossary.png` (no per-term Ask button),
  `inert-04-topbar-westwood-primary-track.png` / `inert-04b-topbar-wide.png` (PRIMARY badge +
  "Settings — not built"),
  `inert-05-league-switch-generic-track-topbar.png` / `inert-06-league-switch-generic-board.png`
  (GENERIC badge after switching to `espn_10_half`; board shows Bijan Robinson 296.7 pts there
  against 303.2 on Westwood — the real ADR-062 split, confirmed on screen),
  `inert-07-strategy-guide-generic-track.png` (the split empty-state message).
- Capture script committed: `frontend/e2e/shot-inert-and-two-track.mjs` (reusable for the next
  session that touches either area).

## Not done this session

- `docs/design/LEAGUE-SETTINGS-BOUNDARY.md` (priority 5) and `docs/design/ADP-COLUMN-AND-CAPTURES
  .md` (priority 6) — not assigned this round.
- `docs/design-reference/fidelity.py` exists but its `screens.json` only registers `/draft/board`,
  `/draft/opponents`, `/draft/predictions` — Draft Room routes this session didn't touch (owned by
  the sibling agent this round). Not run; would not have exercised anything built here.
- The underlying data gap (`strategies.json` etc. absent for 26 leagues) is unchanged — this
  session made the app honest about it, not closed it.
