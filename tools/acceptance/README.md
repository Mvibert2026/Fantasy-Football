# Acceptance harness (content assertions)

Starts the real frontend dev server, drives it headlessly, exercises the main screens
(Board, Draft/DraftRoom, Opponents, Player detail), and cross-checks what's rendered
against the real `data/export/*.json` files -- not against a stored screenshot. Writes
`artifacts/evidence.json` and one screenshot per screen, and exits non-zero on any
failed check.

## Run it

```
npm install
node harness.mjs
```

Optional: `--port 5199` (default) to avoid colliding with another session's dev
server on 5173.

## What it checks, and why it isn't a pixel diff

Five things, each because it actually happened in this project's history:

1. **Board header player count** -- the "N of TOTAL players loaded" line's TOTAL must
   equal the real row count in `board.json`. (Board.tsx currently hardcodes this
   denominator to `378`; the real export has 511 players today. See the standing
   finding below.)
2. **Status banner truth** -- the freshness banner's STALE/fresh claim and its day
   counts must match `board.json:snapshot_stale` / `snapshot_age_days` /
   `snapshot_max_age_days`.
3. **League name** -- the top-bar league switcher's shown name must equal
   `league.json:league_name`, not a hardcoded placeholder.
4. **Mode switcher present** -- the Prep/Draft/Season switcher must exist, with
   exactly one mode marked active, once the app has finished loading.
5. **Non-zero board rows** -- the default, unfiltered Board view must render real
   rows (not the "Nothing matches these filters" empty state) when the export has
   real players.

A pixel/screenshot diff (which is what `docs/handoffs/068-...md`'s design-fidelity
proposal describes) catches drift from a stored baseline, not falsehood against
ground truth -- a wrong number that was already wrong when the baseline was captured
would pass forever, and these screens render live data that changes daily, which
would make a screen-level pixel baseline thrash on every legitimate data refresh.
This harness instead re-reads the real export files on every run and compares
text/DOM content directly. It does not touch `frontend/e2e/smoke.mjs` or resolve
thread 068 -- that thread's design-fidelity question is still open and is a
different, complementary concern (visual regression on the design system itself).

## Standing finding (not fixed here -- this tool doesn't touch frontend source)

`frontend/ui/views/Board.tsx`'s provenance line hardcodes `378` as the denominator
in "N of 378 players loaded". The real `data/export/board.json` currently has 511
players. Check #1 above fails against the unmodified app for exactly this reason --
this is a live defect, not a false positive in the harness. See the session's
fault-proof report for the run that demonstrated this.

## Relationship to `frontend/e2e/smoke.mjs`

That harness (thread 063's regression-trigger suite) and this one both start a dev
server, use Playwright, and write a JSON report + screenshots -- structurally
similar, but checking different things (interaction-regression triggers vs.
content/data-correctness). Whether these should eventually merge into one tool is
a real question, flagged for a follow-up decision rather than settled here -- see
the session report.
