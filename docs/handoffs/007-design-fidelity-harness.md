---
ID: 007
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Build an automated visual-fidelity harness. This is the highest-value thread I have open, because
it attacks the failure mode that has actually cost this project time.

**Structure**

1. `docs/design-reference/` — commit the reference HTML prototype Design produces, one file per
   screen, named for the screen (`board.html`, `opponents.html`, `player-detail.html`, …).
   This is the only artifact Design has to hand over, and it is one it already produces.
2. `tools/fidelity.py` — a Playwright script that, for each screen:
   - renders the reference HTML at a fixed viewport (1440×900 and 390×844), screenshots it
   - navigates the running app to the matching route, same viewports, screenshots it
   - writes `side-by-side.png` and a pixel `diff.png` to `artifacts/fidelity/<screen>/`
   - emits a JSON summary: per-screen diff percentage, plus a hard `MISSING` verdict when the route
     404s, renders empty, or the diff exceeds a gross threshold
3. Wire `MISSING` and any diff above threshold to a non-zero exit, so it can gate a session the way
   a failing test does.

Playwright and Chromium are already available; do not download browsers.

## Why

The Opponents and Predictions tabs were reported as "folded into a single pane" and were in fact
absent — no tabs, no fallback, nothing. Every test passed throughout, because no test asserted the
screens existed. It was caught only because a human manually screenshotted the app beside the
mockups and compared them by eye.

Nothing structural has changed since. The same failure can recur tomorrow, and the current mitigation
is founder attention, which does not scale and is the resource we are trying to spend less of.

This harness converts that manual comparison into a check that runs unattended. Note the specific
property that matters here: **a missing screen produces the largest possible diff.** Pixel comparison
catches absence far more reliably than it catches subtle drift — which is exactly the right bias,
because absence is the failure that actually happened.

It also solves a problem `/design-sync` cannot. Sync covers the design system — tokens and
components. It does not cover screens, and it would not have caught the missing tab. This does.

## Constraints

- Diff threshold must be tunable per screen. Data-dense screens carry live numbers that change
  between runs; do not let legitimate data variance produce red every run, or the harness gets
  ignored inside a week — which is a worse outcome than not building it.
- Consider masking numeric cells for the comparison and asserting layout only. Layout drift and
  missing screens are what this is for; number correctness is the test suite's job.
- Reference HTML goes in the repo. Do not fetch it live from Claude Design at check time — the
  check must work offline and must diff against a *pinned* design, not a moving one.

## Done looks like

Harness runs, produces artifacts for at least the Board screen, and correctly reports `MISSING`
for Opponents (which should currently fail — that is the proof it works). Reply with the JSON
summary and the side-by-side for Board.
