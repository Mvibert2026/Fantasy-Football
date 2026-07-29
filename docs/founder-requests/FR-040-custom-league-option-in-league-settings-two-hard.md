---
ID: FR-040
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Custom league option in League settings

Founder's own words:

> "League settings is important. Let's do that soon. Maybe that's a 'custom' league option. I have
> two hardwired. And all reasonable options. Just need the custom option."

Reading of the shorthand: "two hardwired" = `primary` (Westwood) and `ethans_expert_league`. "All
reasonable options" = the 24-config preset matrix (ADR-047: espn/yahoo roster shape × 8/10/12/14
teams × standard/half/full reception value). What is absent is any way to define a league that is
not one of those 26.

## Why it matters

The League settings control already exists in the top bar and is inert
(`frontend/ui/components/shell/TopBar.tsx:195`, one of the six inert controls inventoried in
FR-037). The founder has now named it as important, which changes it from cosmetic debt to a
prioritised build.

It also matters more than it appears. **The preset matrix varies reception value only.** Every one
of the 24 configs carries this project's own bonus structure, TD values, interception value and
defensive scoring — held at Westwood's ruleset, which happens to match ESPN's confirmed defaults.
So a founder whose third league has different TD values or no yardage bonuses currently has no
correct option at all, and the closest preset would be quietly wrong rather than visibly absent.

## Initial read

Not the founder's own words — PM's read. Two findings, one good and one constraining.

**The backend for this already exists and nobody has said so.** `src/league_builder.py` provides
`create_league(name, teams, ppr, roster, scoring_overrides, platform, playoff_teams, ...)` and
`create_and_export_league(...)`, producing a saved, loadable `LeagueConfig` and a full export
directory. Custom leagues are a solved problem in Python. **What is missing is the UI and the path
from a browser form to a generated export** — not the modelling.

**The constraint is the static deploy, and it splits "custom" cleanly in two.** `draft.maplerock.net`
serves files with no Python behind it. `board.json` carries `projected_points` and `vbd` per player
but **no component stats** (no passing yards, receptions, touchdowns). So:

| Custom dimension | Changes what | Feasible in the browser today |
|---|---|---|
| Team count | Replacement level, VBD, pick sequence | **Yes** — derivable from `projected_points` already shipped |
| Roster shape (starters, flex, bench) | Replacement level, VBD | **Yes** — same |
| Draft slot, playoff weeks/teams | Pick sequence, strategy framing | **Yes** — already being built (FR-034) |
| Reception value (PPR) | `projected_points` itself | **No** — needs re-scoring from components |
| TD values, yardage bonuses, INT, fumbles | `projected_points` itself | **No** — same |
| Defensive scoring | DEF projections | **No** — same |

So roughly half of "custom" can ship on the hosted site with no backend at all, and half cannot
without either (a) shipping component-level projections in the contract so the browser can re-score,
or (b) a real server-side generate step. Option (a) is a contract change with a real size to it;
option (b) contradicts the current no-backend hosting decision.

**Recommended sequencing:**

1. Build the League settings screen with the dimensions that work client-side. That is a genuine,
   honest "custom league" for team count, roster shape, draft slot and playoff structure, and it is
   unblocked today.
2. For scoring, the screen states plainly that changing it requires a rebuild rather than silently
   offering a control that produces wrong numbers. Absent-not-inert, per the standing rule.
3. Separately cost option (a) — component projections in the contract — because it is the thing that
   makes full custom scoring possible on a hosted site, and it is also what a multi-user version of
   this product would need eventually (`CLAUDE.md` §1).

Do not build (1) as a fake version of (3). A settings screen that lets the founder type a TD value
and then shows him numbers computed under a different TD value is the worst outcome available here.
