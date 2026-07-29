---
ID: FR-045
STATUS: NEW
PRIORITY: MEDIUM-LOW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Position scarcity reads every position as behind pace when "Auto-fill to my pick" is used

Founder's own words, with a screenshot showing WR 12 behind, RB 11 behind, QB 2 behind and TE 2
behind — all four at once:

> "hard to understand how all can be behind pace.."

Then, having worked out the cause himself:

> "Draft has autopick and it's working... and I like having it, I can now mock draft myself"
> "'autofill to my pick'"
> "but I guess nobody is actually picking, too many great players available too late, let's put it on
> the list, it's a cool feature but not urgent"

**His diagnosis is correct and his priority call is recorded: on the list, not urgent.**

## Why it matters

Two reasons, and the second is the one that outlives the display bug.

**The panel presents an artifact as a market observation.** Not every position can be behind pace at
once — if some are going faster than expected, others must be going slower. Four simultaneous
"behind pace" readings are arithmetic noise, and the screen states them in the same voice it would
state a real signal.

**Auto-fill mocks are not realistic mocks.** The founder spotted this himself: *"too many great
players available too late."* Because auto-fill takes nobody, the board never depletes, so elite
players sit available at pick 39. That is fine for practising the interface and wrong for anything
measured — including position scarcity, availability, and any pick-recommendation judged against it.

## Initial read

Not the founder's own words — PM's read. Diagnosed 2026-07-29.

**Cause: two individually honest designs that are wrong together.**

`autoFillToMyPick` (`frontend/ui/views/DraftRoom.tsx:544-563`) advances the pick clock by writing
placeholder records:

```
playerId: null,
playerName: AUTO_FILL_PLACEHOLDER,   // '(auto-filled — unknown pick)'
```

Deliberate and correct — the tooltip says *"honest placeholder (not a real player)"*. It refuses to
invent who was taken.

`positionScarcity` (`frontend/ui/data/scarcity.ts:63-65, 89`) computes:

```
expected = players at this position whose consensusRank < currentPick
pace     = gone - expected
```

`gone` counts only real players (`takenPlayerIds` filters `playerId !== null`,
`frontend/ui/data/draft.ts:180`). `currentPick` counts **every** record, placeholders included. The
two sides of the subtraction are drawn from different populations. In the screenshot `currentPick`
is 39 while only 11 real players are gone — the other 27 placeholders took nobody.

**Anything keyed to `currentPick` inherits the skew.** `under50ByNext` and `depletionWarning` are
keyed to `nextUserPick` instead, so they are probably sound — **verify rather than assume**. The
same depletion warning fired for both QB and TE in the screenshot, which is worth checking on its
own merits.

**Options:**

1. **Suppress the pace line while placeholders are present**, and say why. Most consistent with the
   project's absent-not-inert rule, and honest that the information is genuinely unknown. Recommended
   as the immediate fix.
2. **Compare like with like** — scale `expected` by the share of picks that are real, or count only
   real picks in `currentPick` for this calculation. The considered fix; keeps a defensible number
   on screen.
3. **Attribute placeholders positionally using consensus order. Reject.** It invents who was taken,
   which is exactly what auto-fill exists to avoid.

**Separate question, and it is not a display issue — route it to `backend` with `strategist` on
admissibility.** A draft log produced this way is mostly placeholder records. **Nobody has checked
whether such a log is usable for λ calibration.** The measured `DEFAULT_LAMBDA = 0.352` came from
160 real picks transcribed from screenshots, every one a known player. The founder now has a
practical way to self-serve mocks, and mocks gate the core claim (0 of ~30 logged). If
placeholder-heavy logs are inadmissible he needs to know *before* running a batch, not after —
regardless of this ticket's priority.
