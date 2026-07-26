# Design reference

This directory holds the **pinned** design references that `tools/fidelity.py`
diffs the running app against, plus the screen→route map in `screens.json`.

## References are pinned and committed. Always.

Every `*.html` file here is a static, self-contained snapshot committed to the
repo. It is never fetched live at check time — no CDN pulls, no
`<script src="https://…">`, no design-tool export URL resolved during the run.

The reason is the whole point of the harness: **drift is only measurable against
something that does not move.** If the reference is fetched live, a red diff has
two possible causes — the app changed, or the reference changed — and you cannot
tell which without doing the archaeology by hand. Worse, if the reference tracks
the design file, the app can rot for a month while the harness stays green
because both sides drifted together. A pinned reference makes every diff mean
exactly one thing: *the app moved away from what we agreed to build.*

Practical consequences:

- Inline the CSS. Inline or base64 the fonts and images. `file://` is the only
  origin the reference is ever loaded from.
- Updating a reference is a **deliberate, reviewed commit**. The diff on that
  commit is the record of the design decision. Do not amend it in with unrelated
  work.
- Do not hand-edit a reference to make a failing screen go green. That inverts
  the harness: the reference stops being what we intended and becomes a
  transcript of what we shipped.

## Adding a new screen

1. Export or write the reference as `docs/design-reference/<screen>.html`, fully
   self-contained. Use realistic content — an empty table proves nothing.
2. Mark data-dense numbers so masking finds them reliably: add `data-numeric` to
   the element, or render them with a monospace / `tabular-nums` font (the
   harness auto-detects both). Do this on the **app** side too; the two sides
   must mask the same regions.
3. Add an entry to `screens.json`:

   ```json
   {
     "board":       { "route": "/draft/board",       "threshold": 0.08 },
     "opponents":   { "route": "/draft/opponents",   "threshold": 0.05 },
     "predictions": { "route": "/draft/predictions", "threshold": 0.05 },
     "player-detail": {
       "route": "/players/4242",
       "threshold": 0.06,
       "maskSelector": "[data-numeric], .stat-value, .proj-cell"
     }
   }
   ```

   `threshold` is a ratio in `[0, 1]` (0.08 = 8% of pixels may differ).
   `maskSelector` is optional and overrides the default per screen.

4. Run it and look at the artifacts before you trust the number:

   ```bash
   python tools/fidelity.py --screens player-detail --verbose
   open artifacts/fidelity/player-detail/desktop/sidebyside.png
   ```

If `screens.json` is absent entirely, the harness derives routes by convention
(`board` → `/draft/board`, anything else → `/<name>`), uses the default
threshold for every screen, and says so in its output. That is a bootstrap
convenience, not a configuration strategy — commit a real `screens.json`.

## Tuning a threshold

A threshold is a **budget for known, accepted, uninteresting difference** —
font-rasterisation noise, a scrollbar, a 1px border-radius the reference draws
differently. It is not a place to park a real regression.

Procedure:

1. Open `sidebyside.png` and `diff.png` for the failing viewport. Look at *where*
   the red is.
2. If the red is spread thinly over text — antialiasing. Raise the threshold a
   little and move on.
3. If the red is a solid block, a shifted column, or a whole region — that is a
   layout regression. Fix the app. Do not raise the threshold.
4. Raise in small steps and write down why in the commit message. A threshold
   that only ever ratchets upward is a harness quietly retiring itself.
5. Set the threshold per screen, never globally. A dense board legitimately needs
   more headroom than a settings panel; a global number gets set to the worst
   screen and then everything else is unguarded.

Rules of thumb: under 2% is text noise, 2–10% is a real but bounded visual
delta worth a look, above 10% something structural is different.

## MISSING is not tunable

`MISSING` means the screen isn't really there: the route 404s, the page threw an
uncaught error, the body rendered effectively empty, or the diff is so large
(≥ 60%) that "this was never built" is the only honest reading.

Those floors are **hardcoded in `tools/fidelity.py`** and are deliberately not
readable from `screens.json`. Setting `"threshold": 1.0` will not turn a MISSING
into a PASS — the MISSING checks run first and never consult the threshold. If
you set a threshold at or above the 60% ceiling, the harness prints a notice
telling you the ceiling wins.

This is intentional. A threshold lets the team say *"this screen is 6% off and we
accept that for now"* — a reasonable thing to say. It must never be able to say
*"this screen does not exist and we accept that."* The moment MISSING is
suppressible, the cheapest response to an unbuilt screen is a config edit, CI
goes green, and the dashboard reports fidelity on a blank rectangle.

If a screen is legitimately not built yet, remove it from `screens.json` (or
don't add it). An honestly absent screen is fine. A screen that is silently
absent while claiming to pass is not.

`ERROR` is separate and also not tunable: it means the harness itself broke
(timeout, browser crash). Never treat an ERROR as a soft PASS — fix the harness
or the environment.

## Running

```bash
python tools/fidelity.py                       # all screens, both viewports
python tools/fidelity.py --screens board,opponents
python tools/fidelity.py --base-url http://localhost:4173
python tools/fidelity.py --viewport mobile --verbose
python tools/fidelity.py --no-mask             # diff raw values; expect noise
python tools/fidelity.py --update-baseline     # re-render refs to baselines/
```

Exit codes: `0` all PASS, `1` any FAIL, `2` any MISSING, `3` any ERROR (highest
severity present wins). Artifacts land in `artifacts/fidelity/<screen>/<viewport>/`
and a machine-readable roll-up in `artifacts/fidelity/summary.json`.

Chromium is preinstalled at `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`. Never
run `playwright install` — if the browser is missing, the image is wrong.

### Numeric masking

On by default. Before diffing, the harness overlays numeric content (elements
matching `maskSelector`, plus leaf elements rendered in a monospace or
`tabular-nums` font that contain digits) with a solid block, on **both** sides.
The comparison then asserts layout, not values.

This exists because live numbers — ADP ticks, VOR recalcs, a draft clock —
legitimately change between runs. A harness that shows red every run gets muted
within a week, and a muted harness is worse than no harness: it still sits in CI
looking like coverage, creating false assurance that someone is watching the UI.

Masking hides glyphs, not geometry. If a value grows wide enough to reflow its
column, the diff still fires — correctly, because that's a layout bug. Verify
the values themselves in unit tests, where they belong.
