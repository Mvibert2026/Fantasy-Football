---
ID: FR-035
STATUS: NEW
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
