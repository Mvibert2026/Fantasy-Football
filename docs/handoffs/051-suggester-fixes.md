---
ID: 051
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: none
---

## Ask

Three fixes to the pick-entry suggester in the Draft room. Founder observed all three in the running
app.

### 1. It does not dismiss on click-outside

The suggester stays open. It should close on a click anywhere outside it, and on `Esc` (the help row
already advertises `esc clear`, so confirm that path works too). Standard popover behaviour and
currently absent.

### 2. It opens automatically on page load

It should not. The user has not asked for it, and it covers the board — which is the screen they came
to look at. Open it on focus of the pick-entry field, on `/`, or on typing. Not on arrival.

This is a density violation as much as an interaction one: an overlay obscuring roughly a third of the
available-players list, unrequested, on every page load.

### 3. Remove the order randomisation — show BPA order

**This one is my error and the founder is right to overrule it.**

I recommended randomising the top-five order as a free mitigation against shortcut bias: if position 1
always holds our top pick, a tired user pressing `1` repeatedly is logging our prediction rather than
the actual pick, which self-servingly inflates apparent calibration.

That reasoning is sound **for the Mock Lab**, where the entire purpose of the screen is generating
calibration data. It is wrong **here**. The Draft room is not collecting calibration data — the user is
trying to record a real draft quickly, under a clock. Randomising means they must read all five names
every single pick. Pure friction, mitigating a bias that is not being measured on this screen.

**The rule: randomise where calibration data is collected, order by BPA everywhere else.** Draft room
shows board-rank order, top of list first.

Note the header currently reads `TOP 5 BY BOARD RANK, STILL AVAILABLE — ORDER RANDOMISED`. The first
half stays; the second half goes.

**Check ADR-D before changing Mock Lab.** The Strategist's contamination-control ADR (thread 034) may
have superseded the randomisation recommendation there too. Do not apply this change to Mock Lab
without reading it — this thread governs the Draft room only.

## Two things worth keeping, noted so nobody "cleans them up"

- `RECOMMENDED (unvalidated stopgap score, not a backtested model)` — exactly right. Keep the
  qualifier until there is a backtested model behind it.
- `fills an open starting slot` on each recommendation — this is roster awareness already surfacing,
  and it partially satisfies thread 044. Build on it rather than replacing it.

## Done looks like

Click-outside and `Esc` both dismiss. No auto-open on load. BPA order in the Draft room, header text
updated. Mock Lab untouched pending ADR-D. Screenshot. Commit hash.
