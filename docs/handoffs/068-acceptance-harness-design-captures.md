---
ID: 068
FROM: design
TO: pm
STATUS: OPEN
BLOCKS: design drift being caught by a diff rather than by the founder
OPENED: 2026-07-27
---

## Ask

Decide what `frontend/e2e/smoke.mjs` captures, and commit the list. My recommendation is
below. I need a yes/no on it, plus a decision on the one item I cannot settle alone.

**Capture these seven, at a fixed 1440×900 viewport, both themes:**

| # | Surface | Why this one |
|---|---|---|
| 1 | Draft · Board, mid-draft | The densest composition in the product. Catches tier bands, positional rank, sort row, footers in one frame. |
| 2 | Draft · Board, empty position filter | The null vocabulary under a filter that matches nothing. |
| 3 | Settings · recompute in flight | The only surface where a job renders. Catches `Progress` and the pending-value rule together. |
| 4 | Settings · recompute failed | `--fail` must never share with `--live`. A diff catches that; a human rarely does. |
| 5 | Mock Lab · stale configuration | Reference state `08-stale-config`. The hatch treatment either renders or the screen is lying. |
| 6 | Mock Lab · all stale | `09-all-stale`. Whole-panel staleness reads differently from one stale cell. |
| 7 | Player detail | The only surface carrying `IdentityChip` and team colour. |

**Capture at component level too, not only screens.** Point the harness at
`docs/design-system/components/*.dc.html` — each opens standalone with every variant
visible. That is nine files today and it is the cheapest diff in the set: a token change
shows up as a component-level diff before it shows up as a screen-level one, and the
component files have no data dependency, so they cannot fail for reasons unrelated to
design.

**What I want the diff to fail on**, in priority order:

1. **Any null glyph changing.** `—`, `<1%`, `0%`, `not yet`, `·` are five different claims.
   A diff that swaps one for another is a correctness failure, not a visual one, and it is
   the one thing in this system that cannot be cheaply retrofitted.
2. **A number rendering where a null should be**, and the reverse.
3. **Stale treatment disappearing** — hatch, dagger, dimmed value.
4. **Radius on a data row becoming non-zero**, and pills becoming interactive.
5. Ordinary pixel drift, last. It is the least informative failure and it will be the
   loudest, so it should be the lowest-priority signal.

## Why

Fidelity is currently checked by the founder noticing a screen looks worse than the mock.
That produced 058 — eighteen items from two screenshots, four of which named components
that already existed. A diff would have caught the four immediately and would not have
generated the other fourteen as design work.

## Done looks like

The capture list committed into `frontend/e2e/smoke.mjs` or a config beside it, and a
decision on the open item below.

## The open item I cannot settle

**Where do the baseline images live, and who regenerates them?** If they live in the repo,
every intentional design change produces a large binary diff and someone has to approve it.
If frontend regenerates them, the baseline drifts toward whatever the app currently does and
the harness stops testing anything.

My view: **baselines for the component reference files are mine and regenerate when I change
a component; baselines for screens are frontend's.** That splits cleanly along the ownership
line in `docs/design-protocol.md`. But I cannot commit to this repo, so I cannot own a
regeneration step — which makes this your decision, not mine.

## Note

I have read access to this repo now. `docs/handoffs/README.md` still says design cannot read
it and instructs `TO: design VIA: pm`. The read half is stale; please correct it.
