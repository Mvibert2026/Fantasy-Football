---
ID: FR-036
STATUS: SHIPPED
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Manual team-name entry for opponents in the draft UI

Founder's own words:

> "For opponents in draft I should have the option to put in team names manually in the UI/UX"

## Why it matters

`LiveOpponents.tsx` reads `opponents.json` for `team_name` only, and renders
`Slot N (no team name supplied)` in italics when a slot has none. That is honest, but during a live
draft the founder is looking at a real draft board with real team names on it, and matching a
manager to a slot from memory while the clock runs is exactly the friction the Opponents screen
exists to remove.

This also generalises past Westwood. For the ESPN and Yahoo leagues (FR-027) there is no opponents
artifact at all, so every slot is unnamed — manual entry is the only way those screens ever carry
names.

## Initial read

Not the founder's own words — PM's read.

Scope: names only. Nothing entered here may feed the model, the recommendation, or any inferred
opponent strategy — the Opponents screen is observable arithmetic from the pick log, and a typed
name is not evidence about anything.

Storage should be local and per-league, in the same shape as the existing draft state
(`prep.draft.<leagueId>`), so a name survives a reload and does not leak between leagues. A name
typed by hand should override `opponents.json` where both exist, and it should be visible that it
was typed rather than sourced.

## Update (2026-07-29, frontend)

**Correction: there is no `LiveOpponents.tsx` anywhere in this repo.** The screen this request
describes is `ui/views/Opponents.tsx` — confirmed by search, and confirmed live by screenshot that
it is the exact same component rendered both as its own Prep-mode sidebar screen *and* as Draft
mode's own internal "Opponents" hub tab (`DraftRoom.tsx`'s `AdaptedOpponentsPane` wraps
`Opponents.tsx` unmodified). One build covers both surfaces; nothing separate needed touching for
"usable during a live draft."

Built exactly to spec: click-to-edit inline (pencil icon, no modal — the card and the rest of the
board stay fully visible the whole time), names only (`ui/data/opponentNames.ts` has zero
dependency on the availability model, the recommendation, or opponent-strategy inference — the
storage layer is pure `localStorage` string I/O). Per-league key
`prep.opponentNames.<leagueId>`, matching `prep.draft.<leagueId>`'s shape/lifecycle exactly.
Screenshot-confirmed to survive a full page reload. A typed name renders in accent colour with a
`TYPED` tag and a clear ("×") control that reverts to the sourced `opponents.json` name where one
exists, or to the honest "Slot N (no team name supplied)" placeholder where it does not — never to
blank, per the request's own explicit rule. Works identically for a league with no `opponents.json`
at all (every ESPN/Yahoo config): every slot starts with the edit affordance, not a stub note.

Screenshots: `frontend/e2e/artifacts/fr036-opponents-prep-before.png`, `-prep-typed.png`,
`-prep-after-reload.png`, `-draft-mode.png`. Tests: `ui/__tests__/opponentNames.test.ts` (10),
`ui/__tests__/opponents.test.tsx` (+6). Commits `e54b83f`..`1775ac6` on branch
`worktree-agent-ad3fc0f6ee64497b5`.

## Update (2026-07-30, frontend) — colour fix per docs/design/SUPPLIED-VALUES.md

Design flagged that the typed name rendered in `--acc` green with a bordered `TYPED` badge — the
board's delta/"good" colour, which a typed name is not. Fixed: the name now renders in `--txt` with
a dotted underline (the app's one and only "you put this here" marker), and the badge is now a plain
lowercase `typed` label (monospace, no border/box), matching the "set by you"/"randomised" marker
vocabulary the same design spec establishes for future supplied controls. The clear ("×") reversion
to the sourced `opponents.json` name, or the honest "no team name supplied" placeholder, is
unchanged. Tests: `ui/__tests__/opponents.test.tsx` (+1, asserts no `--acc` on the name or marker
and the exact dotted-underline style). Screenshot:
`frontend/e2e/artifacts/supplied-2-opponents-typed-name.png`.
