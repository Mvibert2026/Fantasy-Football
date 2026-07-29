---
ID: FR-036
STATUS: NEW
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
