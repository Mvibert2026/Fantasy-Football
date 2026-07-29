---
ID: FR-035
STATUS: SHIPPED
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Predictions in prep must be scoped to the selected league

Founder's own words:

> "Predictions in prep should be based on league selected."

## Why it matters

The founder has at least three leagues (FR-027) and the league switcher in the top bar is the
control he uses to move between them. A prediction that silently keeps using a previous league's
teams, rounds or draft slot is the app showing a confident number that is wrong for the league on
screen — the failure mode this project treats as worse than showing nothing.

## Initial read

Not the founder's own words — PM's read.

`Predictions.tsx` already receives a `league: LeagueConfig` prop and derives `leagueId` from
`data.manifest.artifacts.board.league_id`, with a `useEffect` that reloads draft state when
`leagueId` changes. So the plumbing exists. Two possibilities, and they need distinguishing before
anything is built:

1. It works and the founder could not tell, because nothing on the Predictions screen names the
   league it is predicting for. That is a labelling defect, not a logic defect.
2. Something downstream of the props — availability, the pick model, a cached derived value — is
   not re-deriving on league change.

Verify which before changing behaviour. Whichever it is, the screen should state the league,
team count, round count and draft slot it is predicting under, so the answer is visible rather
than inferred.

## Update (2026-07-29, frontend)

**Diagnosis: (1), not (2).** Switched leagues live in a real running app (Westwood, 10T/16
rounds/slot 3, vs. Ethan's Expert League, 10T/15 rounds/slot 1) and confirmed by screenshot that
the re-derivation was already correct — the header line ("Live availability at pick N" /
"You're on the clock at pick N"), every row's BASELINE and the empty-vs-populated LIVE column all
changed to match the newly selected league. There was no stale closure, no memoization bug, no
downstream re-derivation failure. The screen was computing the right thing and giving the founder
no way to see that it was.

Fix: a `Predicting for <league> · N teams · M rounds · your slot S` line directly under the
"Predictions" heading (`ui/views/Predictions.tsx`'s new `PredictingUnder` component). League name
falls back to the raw `league_id` when `league.json:league_name` is absent (never blank or
invented). The slot clause marks itself `(overridden, sourced M)` in accent colour when FR-034's
slot override is active for this league — an override is local state, not a backend field, and
Principle #1/#2 require it to stay visually distinct rather than rendered through the same path as
a real export value.

**One related, separate bug found and fixed along the way, not part of this request:**
`App.tsx`'s league-load effect had no guard against out-of-order async resolution — switching
leagues repeatedly (not fast-clicking; real waits between switches) could leave `data` pointing at
a stale league while every visible control reported the new one selected. This is exactly the
class of failure this FR was watching for, just triggered by a different pattern than a single
switch. Fixed with a standard effect-cancellation guard; regression test at
`ui/__tests__/league-switch-race.test.tsx`, confirmed to actually fail without the fix by
temporarily disabling the guard and re-running.

Screenshots: `frontend/e2e/artifacts/fr035-predictions-westwood.png`,
`fr035-predictions-ethans.png`. Tests: `ui/__tests__/predictions.test.tsx` (+4),
`ui/__tests__/league-switch-race.test.tsx` (1). Commits `e54b83f`..`1775ac6` on branch
`worktree-agent-ad3fc0f6ee64497b5`.
