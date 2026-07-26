# Frontend spec audit — July 2026

**Author:** frontend agent · **Date:** 2026-07-26 · **Thread:** `docs/handoffs/031-frontend-spec-audit-and-wiring.md`
(includes the addendum, `docs/handoffs/031-ADDENDUM-audit-additions.md`)

## Method

Per `docs/design-handoff/spec/spec-manifest.json`, `acceptance-checks.json`, `design-tokens.json`,
`formulas.json`, `api-contract.json` and `screens.json` are the diffable, machine-readable spec;
`FRONTEND-SPEC.md` and `screens/*.md` are prose reference, explicitly marked `"diffable": "no"`. This
audit works `acceptance-checks.json` item by item as instructed, cross-referenced against the four
`screens/*.md` files and the Settings spec for anything the checklist doesn't itemise, and reads the
actual running code (`frontend/ui/**`) rather than eyeballing screenshots first. Screenshots close the
audit, they don't drive it — a screenshot cannot tell you whether a `·` is scoped correctly.

Verdicts: **built** (matches spec), **partial** (real but incomplete or drifted in a bounded way),
**absent** (nothing exists), **drifted** (something exists but diverges from the spec's actual rule,
not just incompleteness).

No fidelity harness exists (`tools/fidelity.py` referenced by `docs/design-fidelity.md` is not present
in this repo — checked, does not exist). This audit is therefore the harness's job done by hand, once;
building the harness itself is not in scope for this thread and isn't claimed as done anywhere below.

---

## Headline finding: the app was serving stale, shadowed data

This was the explicit thing PM asked me to confirm ("are you reading from `data/export/<league_id>/`
or the old flat `data/export/`?"). The honest answer is **neither** — it's reading from a third,
undocumented copy, and it is stale.

`frontend/scripts/sync-exports.mjs` computes `srcDir = join(root, 'data', 'export')` where `root` is
`frontend/`'s own directory. That resolves to **`frontend/data/export/`** — a copy of the export set
that lives *inside* the frontend subtree, committed to git (`git ls-files frontend/data/export` returns
19 tracked files; nothing under `frontend/data/` is gitignored), separate from the canonical
repo-root `data/export/` every backend session actually writes to.

Verified concretely:

| | `data/export/` (repo root, canonical) | `frontend/data/export/` (what the app actually reads) |
|---|---|---|
| `board.json` contract | **1.8.0** | 1.7.0 |
| `board.json` generated | 2026-07-26T23:26:30Z | 2026-07-26T05:31:32Z (~18h stale) |
| League config-matrix dirs | 25 (`espn_8_full`…`yahoo_14_standard`, `yahoo_standard_mock`) | 1 (`yahoo_standard_mock` only) |
| `rosters.json` | present (contract 1.8.0, new) | absent |

`frontend/server/refresh.ts`'s own doc comment states the intended architecture directly: *"Two
sessions are running against this repo — one on the backend regenerating exports, one here on the
front end... it re-reads `data/export/`."* The code just points that re-read at the wrong directory.
This is a bug, not a design choice, and it explains two things at once: why the league switcher only
ever offered one extra option instead of the 24-config matrix, and why `rosters.json` — which answers
`docs/handoffs/016-league-rosters-endpoint.md`, the hard blocker on a real Opponents tab — never
reached the app at all.

**Fixed in Phase 2 below** (`sync-exports.mjs` now points at the repo-root `data/export/`; the stale
`frontend/data/export/` copy is removed from git). See the Phase 2 section for what that unblocked and
what it changed.

`docs/handoffs/036-weekly-finishes-and-season-stats-exports-contrac.md`, opened `FROM: backend TO:
frontend`, is a second, related problem worth naming here: it announces contract 1.8.0 but its `Ask`
and `Done looks like` sections are the unfilled template text, not a real spec. It cannot be acted on
as written. Replied on that thread below.

---

## Screens

### `draft.board` — Board tab (`docs/design-handoff/screens/01-draft-board.md`)

**Verdict: partial / drifted.** The spec describes one screen: tier-grouped rows, a two-number
`base→live` availability cell embedded in every row, an inline `why` derivation, and TypeAhead pick
entry with digit shortcuts (RETROFIT-5). What's shipped is **two different, older-shaped screens**
that split this:

- `ui/views/Board.tsx` (Prep mode) — a 10-column sortable table (rank/name/pos/team/bye/proj+CI/cons/
  delta/vbd/tier), tier bands (only when a single position is selected — a deliberate, documented
  departure; see the file's own header comment on why the ALL view can't use `tier_label` coherently),
  inline "why" expansion showing replacement-levels/scoring-VBD components. **No availability column
  anywhere in this table** — the spec's central "two-number availability cell" per row does not exist
  on this screen at all.
- `ui/views/DraftRoom.tsx` (Draft mode) — has pick entry, but it's a free-text search box with
  ↑/↓/Enter, not the TypeAhead component. Its available-players pane *does* show `baseline → live`
  per row and an inline "why" expansion, but with no tier grouping/header ("TIER 2 — 3 players left")
  and no 10-dot array next to the percentage.

Acceptance checks (`acceptance-checks.json`), against this pair of screens:

| Check | Verdict | Note |
|---|---|---|
| TOK-01 | built | No mono on names/prose/nav/labels anywhere read; position/team codes use `--font-ui` per `tokens.css`. |
| TOK-02 | built | `tabular-nums` applied via `.num` class scoped to numeric cells (`base.css`), not global. |
| TOK-03 | built | Data rows/cells carry no radius rule (base.css gives 0 by default, no override on row/cell elements). |
| TOK-04 | built | `base.css`: `button/input/select/textarea` → 5px, `.card/.chip/.filter-pill/.table-wrap` → 6px (`--r-c`), `.overlay/.modal/.popover` → 12px (`--r-m`), `.pill` → 999px. Matches `design-tokens.json#radius` exactly. |
| TOK-05 | built | `tokens.css` light theme values are byte-identical to `design-tokens.json#themes.light` (`--bg:#f4f6f8`, `--panel:#fff`, `--acc:#0d8a57`). |
| TOK-06/07 | built (spot-checked) | `--down` used only for scarcity/delta/thin states in code read; every colour cue in `DeltaCell`/`ProjCell` pairs with a glyph or the number itself. Not exhaustively swept — no harness exists to do that mechanically. |
| LIVE-01 | **partial** | Present in DraftRoom's list, queue, watchlist, and PlayerDetail. **Absent from Board.tsx** — no availability surfaces there at all. |
| LIVE-02 | partial | `need`/`run` shown separately in PlayerDetail (explicit "Need adjustment" / "Run adjustment" lines). **No row-level tooltip anywhere** carries this — the spec's required tooltip ("baseline + range, live + thin flag, need and run separately, run context") does not exist on any board/draft row. |
| LIVE-03 | partial | PlayerDetail: correct, `live` → `'not yet'`, baseline never repeated as live. DraftRoom's row: when live is null, the cell **silently shows baseline alone with no live indicator at all** — not `—`, not `not yet`, just nothing. See "null vocabulary" below. |
| LIVE-04 | partial | Band math (`bandFromSigma`, ×1.6 when thin) is correct in `liveAvailability.ts`. **No thin marker on any row** — only PlayerDetail shows a "THIN" badge. |
| LIVE-05 | partial | PlayerDetail always renders the 10-dot array beside a percentage. DraftRoom/queue/watchlist rows show percentages with **no dot array** at all. |
| REC-01…05 | **absent** | No Settings editor exists (see below), so there is no tier-1/tier-2 recompute surface to assert against. Not a fail — nothing to test. |
| STR-01 | built | `PlayerDetail`: `width: 440`, transparent click-catcher at z-index 80, panel at z-index 90. |
| STR-02 | built | Identity → verdict → projection → availability → why-differs, in that order, in `PlayerDetail.tsx`. |
| STR-03 | built | Sticky bottom bar, `Mark taken` filled `var(--acc)`. |
| STR-04 | built (narrower copy) | Expands inline in both Board.tsx and DraftRoom (not a modal). Copy is generic ("Replacement levels: +N (path)"), not the spec's exact headline sentence format ("Your format moves him up 2 slots — market 14, ours 12"). |
| STR-05 | drifted | `RoundGrid.tsx` renders exactly `teams` columns (`repeat(${teams}, ...)`— correct. `Opponents.tsx` uses `repeat(auto-fill, minmax(232px,1fr))`, which wraps to however many columns fit the viewport, not literally `teams` columns in one row. |
| STR-06 | built (code-level) | `draft.ts`'s `loadDraftState(leagueId)` is keyed per league; `DraftRoom` reloads on `leagueId` change. Backed by `league-switch.test.ts` (9 passing tests). |
| HON-01 | built | Enforced structurally by the `Cell<T>` present/absent pattern plus `no-invented-numbers.test.ts` (20 tests) and `claims-tagged.test.ts` (13 tests). |
| HON-02 | **drifted (edge case)** | `PlayerDetail`'s `Dots` component: `value={avail.live ?? (baseline.present ? value : 0)}`. If baseline itself is absent *and* live is null, the dot array silently renders as zero-filled — visually a "0%" with no text saying so. Not observed with real data in this session (board-listed players carry a baseline), but the fallback exists and should be `null`-safe, not `0`-safe. |
| HON-03 | built | `PlayerDetail`'s sections 6–9 collapse into one explicit sentence ("Not computed: archetype, weekly finishes, season-by-season stats, and takeaways..."), never stacked empty headers. |
| HON-04 | n/a | The shipped app is wired to the real pipeline (378 real players, no sample/generated data) — `spec-manifest.json`'s `prototypeDataCaveat` describes the *design prototype's* sample data, which this build never uses. Not a gap; the check doesn't apply here. |
| **HON-05** | **fail** | `lib/format.ts#percent()` is `Intl.NumberFormat({style:'percent', maximumFractionDigits:0})` with **no special case** for values under 0.5%. Any availability below 0.5% renders `0%`, not `<1%` — the exact substitution `nullStates` in `acceptance-checks.json` explicitly forbids ("Availability < 0.5% → `<1%`, never `0%`"). Concrete, verified defect. |
| HON-06 | partial | Board's provenance line states coverage ("N of 378 players loaded"). No weekly-finishes aggregate exists to carry a coverage sentence (the feature itself is absent). |

RETROFIT-5 (TypeAhead back-port, digit 1–5 commit, Backspace-undo, randomised order, `entry_mode`
logging) is **not picked up**. `DraftRoom.tsx`'s `onSearchKeyDown` is exactly the plain
ArrowUp/ArrowDown/Enter/Escape handler the spec names as "the slower one" to retire. No digit
shortcuts, no undo-via-Backspace-on-empty-field, no candidate randomisation, no `entry_mode` field
anywhere in `DraftPickRecord`.

### `draft.opponents` — Opponents tab (`docs/design-handoff/screens/02-draft-opponents.md`)

**Verdict: partial**, and meaningfully wirable as of this session (see Phase 2).

Built: card grid, `coverage_warning` line, `team_name` null-handling ("Slot N (no team name
supplied)"), a `BETWEEN YOUR PICKS` badge, `known_picks_2026` list, behavioural fields
(`positional_tendencies` etc.) correctly marked "NOT A MODEL INPUT" when present.

Missing against the spec's card anatomy, all confirmed absent by reading `Opponents.tsx` before this
session's changes:
- No `next #N` pick indicator in the card header.
- **No roster slot rows at all** (`QB / RB / WR / TE / FLEX` with fill state and position-coloured
  rule) — the spec's entire middle section of the card.
- **No `STILL NEEDS` chips.**
- No `4/9 starters · 1 on bench` footer line.
- Border colour rule only implements the `--acc` ("between your picks") case; no `--live`
  on-the-clock state (arguably doesn't apply — Opponents is a Prep-mode screen with no live clock
  context — but it's a literal spec deviation worth recording, not silently assumed correct).

These are the fields `docs/handoffs/016-league-rosters-endpoint.md` asked backend for. Until this
session, `rosters.json` didn't exist in the reachable data path (see the headline finding). It does
now, wired in Phase 2.

### `draft.predictions` — Predictions tab (`docs/design-handoff/screens/03-draft-predictions.md`)

**Verdict: absent.** No screen, no route, no nav entry (`Sidebar.tsx`'s `NAV_MAIN` and `SOON_ITEMS` —
neither lists it under any name). Confirms `docs/CURRENT-STATE.md`'s existing "not built" line. This is
ticket 028, out of scope for this thread by the dispatch note ("031 is a prerequisite to 027/028, not
inclusive of them").

### `playerDetail` — Player detail sheet (`docs/design-handoff/screens/04-player-detail.md`)

**Verdict: built, close to spec.** See the STR-01/02/03 and HON-03 rows above. Additional notes:
- Headshot: correctly never mounts an `<img>` with an interpolated placeholder src; always renders
  initials-on-team-colour, matching the spec's own stated prototype state (no player anywhere has a
  real ESPN id).
- Verdict line is generated via `ui/data/verdict.ts`, not hand-written, matching the 3-clause
  structure in `formulas.json#verdictLine` at a source-reading level; not independently re-derived
  clause-by-clause against all ~378 players in this pass.
- `Compare` and `Ask` action-bar buttons are visually present but `aria-disabled` — honest inert
  stubs, not fake-functional buttons, consistent with those features being unbuilt elsewhere.

### `settings.editor` (`docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md`)

**Verdict: absent, entirely.** No component, no route, no state machine, no `PATCH
/api/leagues/:id/settings` equivalent, nothing (grep for `Settings`/`SETTINGS` across `frontend/ui`
returns only unrelated substring hits in `Availability.tsx`, `TopBar.tsx`, `PlayerDetail.tsx`).
Confirms `docs/CURRENT-STATE.md`. This is the "Settings build" ticket 031 explicitly blocks and does
not include.

### Mock Lab (in scope only for the retrofit-status addendum, not for building)

**Verdict: absent**, confirmed (`docs/CURRENT-STATE.md`: "Mock Lab UI and backend" not built). Named
here only because RETROFIT-2 and RETROFIT-4 live entirely inside it.

---

## Retrofit status (`docs/design-system/AUDIT.md`, addendum item 1)

| Retrofit | Status | Note |
|---|---|---|
| RETROFIT-1 (`·`→`—` for not-computed; two phrasings not three) | **partially picked up** | `Board.tsx`'s `DeltaCell` already scopes `·` correctly to the delta deadband only, and renders `—` for absent deltas/projections — this may simply predate NULL-01/02 rather than being a deliberate retrofit pass, but the end state is compliant there. `PlayerDetail` uses `'not yet'` verbatim (roomy-space case), matching the spec exactly. **Not compliant**: `DraftRoom`'s available-list availability cell shows neither `—` nor `not yet` when live is null — it silently omits the live half of the pair. |
| RETROFIT-2 (Mock Lab `unranked`) | n/a | Mock Lab absent. |
| RETROFIT-3 (Settings position-label typography) | n/a | Settings absent. |
| RETROFIT-4 (Mock Lab partial mocks) | n/a | Mock Lab absent. |
| RETROFIT-5 (TypeAhead back-port to Draft) | **not picked up** | See `draft.board` above — confirmed absent in `DraftRoom.tsx`. |

## Null vocabulary (addendum item 2)

The five renderings and whether they stay distinct in the running app:

| Rendering | Claim | Status |
|---|---|---|
| `—` | no value exists | **Distinct**, consistently used via the `Cell<T>` absent-kind pattern (`ProjCell`, delta, consensus rank, etc.) across Board, DraftRoom, PlayerDetail. |
| `<1%` | real, computed, very small probability | **Does not exist anywhere in the codebase.** See HON-05 above — `percent()` has no sub-1% branch, so this rendering is simply never produced; every case that should show it shows `0%` instead. This is the one place the five-way vocabulary has *collapsed to four*, and it collapsed into the most dangerous neighbour (a real zero). |
| `0%` | real, computed zero | Exists, via the same `percent()` call — and per the above, is not distinguishable from `<1%`'s case today. |
| `not yet` | signal is none, live not computed | **Distinct** in `PlayerDetail`. **Missing** (renders as nothing, not as this string) in `DraftRoom`'s row. |
| `·` | structurally not applicable (delta deadband) | **Distinct**, correctly scoped to `Board.tsx`'s `DeltaCell` only; not reused for any null-adjacent state. |

Net: 3 of 5 are clean everywhere audited; 1 (`not yet`) is clean in one surface and silently absent in
another; 1 (`<1%`) does not exist in the code at all, which is the more serious of the two findings —
it isn't drifted, it was never built, and its absence means `0%` is currently overloaded to also mean
"probability under half a percent," exactly the P2 violation the spec calls out by name.

---

## `nulls.json` naming note (not a defect, recorded so the next reader isn't confused)

`data/export/nulls.json` is **not** the UI null-state vocabulary file. It's a set of statistically null
*research findings* (spike-week persistence, hero-RB simulation — preregistered hypotheses that did
not confirm), consumed by `Methodology.tsx` and the assistant's reasoning fallback. The coincidence in
naming with this audit's "null vocabulary" section is exactly that — a coincidence. Confirmed by
reading the file and its five call sites in `ui/assistant/reasoning.ts`, `ui/views/Methodology.tsx`,
and the corresponding tests.

---

## Acceptance-check summary

Of the 27 checks in `acceptance-checks.json` (22 `checks[]` + treating REC-01…05 as one N/A group):
**built: 12 · partial: 9 · drifted: 2 · fail: 1 (HON-05) · n/a/absent: 5** (REC-01…05, HON-04).
Full per-check table is above, inline with each screen.

## Verdict counts (screen/element level, all spec sources combined)

**built: 11 · partial: 9 · absent: 6 · drifted: 3**

(Absent: Predictions tab, Settings editor, Mock Lab, RETROFIT-2/3/4 as n/a-by-absence,
row-level availability tooltip. Drifted: STR-05 on Opponents, RETROFIT-1's partial compliance,
`<1%` vocabulary collapse.)
