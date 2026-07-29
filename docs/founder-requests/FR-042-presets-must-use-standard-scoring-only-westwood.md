---
ID: FR-042
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
SUPERSEDES-PART-OF: ADR-047
---

## Request
Presets must use standard scoring; only Westwood carries the custom ruleset — two tracks

Founder's own words:

> "All the other pre sets should be standard scoring (with different por) not Westwood custom. Only
> Westwood should have the custom.
>
> Westwood is a unique custom case. The original. The others should be variable. Westwood should
> still allow custom knowledge of the opponents.
>
> The others don't need to. Almost two separate tracks."

("por" read as "PPR".)

## Why it matters

**This is a correction to shipped behaviour, not a feature request.** It is also a decision, not a
question — it does not need re-litigating, it needs implementing.

`src/generate_config_matrix.py:71-74` builds every one of the 24 presets as
`copy.deepcopy(LEAGUE)` with the reception value swapped. `LEAGUE` is **Westwood's ruleset**. So all
24 presets currently carry Westwood's stacking yardage bonuses (+1/+1.5/+2 at 100/150/200 rushing
and receiving, 300/350/400 passing), Westwood's TD values and Westwood's defensive scoring. The only
thing that varies across them is receptions.

The consequence is that a preset labelled *"ESPN-default, 12 teams, half scoring"* is not an
ESPN default. It is Westwood with a different PPR value and a different roster shape, and it says
otherwise on screen. That is the app misrepresenting what it is showing.

**The docstring in that file also contradicts itself**, which is probably how this survived:

- Lines 6-11 claim the ruleset *"happens to match ESPN's confirmed platform defaults exactly (same
  +1/+1.5/+2 bonus tiers at the same 100/150/200/300/350/400 thresholds)"*.
- Lines 52-53, twelve lines later: *"ESPN scoring unverified (bot-detection blocked the fetch)"*.

Both cannot be true. One of them is a confident claim about a thing the same file says was never
verified. The founder's instruction resolves it without needing the fetch to succeed.

## Initial read

Not the founder's own words — PM's read.

**Two tracks, and they should be structurally separate rather than two settings on one object.**

| | **Westwood (primary)** | **Everything else** |
|---|---|---|
| Scoring | The full custom ruleset — stacking bonuses, verified against the live platform 2026-07-27 | Standard scoring, varying PPR only (0 / 0.5 / 1.0) |
| Opponents | Named, modelled, custom knowledge of who drafts how | Generic. No opponent identity, no tendency modelling |
| Roster | Verified exact | Platform-shaped or user-specified |
| Purpose | The real draft | Rehearsal and portability |

This sharpens FR-027 ("two tiers this season") from a scope note into a structural rule, and it is
the right structure: the modelling that makes Westwood good is precisely the modelling that cannot
be honestly applied to a league whose members we know nothing about.

**Open definitional question, and it needs answering before the regenerate, not after.** "Standard
scoring" has to become a concrete ruleset in code. The conventional default is: passing 25 yd/pt,
4 pt passing TD, −2 INT, 10 yd/pt rushing and receiving, 6 pt TD, −2 fumble lost, **no yardage
bonuses**, with receptions varying 0 / 0.5 / 1.0. That is my read of what the founder means by
"standard", and it is what distinguishes it from Westwood. **State the assumption on the screen**
rather than presenting it as verified platform truth — the existing file already shows what happens
when an unverified default gets described as confirmed.

**Consequence to plan for:** this invalidates the projections in all 24 preset exports. They must be
regenerated, not edited. Anything downstream that compared a preset to Westwood is comparing
different things and needs re-checking.

**Interaction with FR-040 (custom league option):** these fit together. Standard presets become the
sane starting point, and "custom" becomes the escape hatch for a league that is neither standard nor
Westwood. Sequence FR-042 first — a custom builder that starts from Westwood's rules by default
would propagate this same bug into every league the founder creates.
