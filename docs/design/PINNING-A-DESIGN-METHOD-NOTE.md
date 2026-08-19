# Pinning a design so it stays pinned

A method note from a project that did this the hard way. Written to be pasted to agents
working on a different codebase — no repo-specific paths, no framework assumptions beyond a
headless browser.

The problem this solves: you have design specs and a real app, they disagree, you throw agents
at it, and the app converges — then drifts back within a fortnight. The fix is not more agents
looking at screenshots. It is a guard that fails the build, and a guard that nobody mutes.

---

## 1. The one idea everything else depends on

**A pinned reference is a static, committed file. Never fetched live at check time.**

Not a design-tool export URL resolved during the run. Not a CDN pull. Inline the CSS, inline or
base64 the fonts and images, and load it from `file://`.

The reason is the entire point of the exercise. If the reference is fetched live, a red diff has
two possible causes — the app changed, or the reference changed — and you cannot tell which
without doing archaeology by hand. Worse, if the reference tracks the design file, the app can
rot for a month while the guard stays green, because both sides drifted together.

A pinned reference makes every diff mean exactly one thing: **the app moved away from what we
agreed to build.**

Two consequences worth stating explicitly to agents, because both get violated:

- Updating a reference is a deliberate, reviewed commit of its own. The diff on that commit *is*
  the record of the design decision. Don't fold it in with unrelated work.
- Never hand-edit a reference to make a failing screen go green. That inverts the guard: the
  reference stops being what you intended and becomes a transcript of what you shipped.

---

## 2. What the guard actually compares — three layers, each with a different job

Pixel diffing alone does not work. It is necessary and it is not sufficient, and the two failures
it cannot express are the ones that hurt.

### Layer 1 — Pixels: *does it look right?*

Full-page screenshot of the pinned reference and of the running app at the mapped route, at
fixed viewports (we used `1440×900` and `390×844`), then a per-pixel diff.

The detail that matters: **a per-channel tolerance before two pixels count as different.** We
used 12/255. Below that you are measuring subpixel antialiasing and GPU-free rasterisation
noise, not design drift. Without it, identical renders diff at 2–4% and every threshold has to
be inflated to absorb it, which destroys the signal you wanted.

When the two images differ in size, **pad rather than resize.** We pad the smaller onto a canvas
of the larger in loud magenta. Resizing silently rescales a layout bug into a small uniform blur
across the whole image; padding turns a height difference into an unmissable magenta band. Report
the size mismatch explicitly in the output too.

### Layer 2 — DOM: *is the screen even there?*

This is the layer people skip, and skipping it is what makes the whole harness dishonest.

A pixel diff cannot distinguish "this screen is 8% off spec" from "this route 404s and we are
diffing an error page" — both are just a number. So before any diff is scored, assert liveness
against the DOM and the response:

- HTTP status of the navigation
- uncaught page errors (`page.on("pageerror", …)`)
- rendered `innerText`, whitespace-collapsed, must exceed a minimum length (we used 40 bytes)
- grayscale standard deviation of the screenshot above a floor (we used 1.5) — catches a page
  that rendered a uniform rectangle
- diff ratio at or above a gross ceiling (we used 60%) — at that point "this was never built" is
  the only honest reading

Any of those fires ⇒ verdict `MISSING`, and **`MISSING` is not tunable.** See §3.

### Layer 3 — Computed styles: *which regions am I allowed to trust?*

This is the layer most people expect to be an assertion target — "assert `color` equals the
token" — and in our experience that is the weakest use of it. It's verbose, it duplicates the
stylesheet, and it passes while the layout is visibly broken.

What computed styles are genuinely good for is **finding the volatile regions automatically**.
Before diffing, walk the DOM and mask any leaf element that contains a digit *and* is rendered
in a monospace or `tabular-nums` face — read off `getComputedStyle().fontFamily`,
`fontVariantNumeric`, and `fontFeatureSettings`. That catches data cells nobody remembered to
tag, which is exactly the set that would otherwise make the guard flaky.

Pair it with an explicit escape hatch (`[data-numeric]`, `.stat-value`, …) for anything the
heuristic misses.

> If you *do* want token-level assertions, put them in unit tests against the stylesheet, not in
> the visual guard. Keep the guard about geometry.

---

## 3. The verdict ladder, and the one rule that keeps it honest

Four verdicts, evaluated in priority order, with distinct exit codes so CI can act on them:

| Verdict | Meaning | Exit |
|---|---|---|
| `MISSING` | The screen isn't really there — 404, threw, empty, or grossly different | 2 |
| `FAIL` | Diff above this screen's threshold | 1 |
| `PASS` | Diff at or below this screen's threshold | 0 |
| `ERROR` | *The harness* broke — timeout, browser crash, unreadable file | 3 |

Highest severity present wins.

**`ERROR` must be separate from `MISSING`.** `MISSING` is a statement about the product;
`ERROR` is a statement about your script. Collapsing them means a flaky browser launch reads as
a missing screen, everyone learns to ignore both, and you are back to nothing.

**`MISSING` floors are hardcoded and deliberately not readable from config.** This is the single
most important design decision in the harness and it will be argued with.

The reasoning: a per-screen threshold exists so a team can say *"this screen is 6% off and we
accept that for now."* That is a reasonable thing to say. It must never be able to say *"this
screen does not exist and we accept that."* The moment `MISSING` is suppressible, the cheapest
response to an unbuilt screen is a one-line config edit — CI goes green and the dashboard reports
fidelity on a blank rectangle.

A harness that can be configured into agreeing with you is not a check, it is a rubber stamp.

If a screen genuinely isn't built, remove it from the config. An honestly absent screen is fine.
A screen that is silently absent while claiming to pass is not.

---

## 4. Keeping it from going flaky — the five things that actually did it

A guard that is red every run gets muted inside a week. And a muted guard is **worse than no
guard**: it still sits in CI looking like coverage, producing false assurance that somebody is
watching the UI while nobody is. Treat flakiness as a correctness bug in the harness, not an
annoyance.

**1. Freeze time and randomness *before any app code runs*.** Inject an init script (Playwright:
`page.add_init_script`, before navigation) that replaces `Date` with a frozen subclass, `Date.now`
with a constant, `Math.random` with a seeded xorshift, and `performance.now` with `() => 0`. A UI
rendering "3s ago" or shuffling tie-breaks randomly produces a nonzero diff on every single run.
Timing matters: an `evaluate()` after load is too late, the app has already read the clock.

**2. Kill motion with CSS, not with sleeps.** Inject a stylesheet zeroing `animation-duration`,
`animation-delay`, `transition-duration`, `transition-delay`, forcing
`animation-iteration-count: 1` and `scroll-behavior: auto`, plus `caret-color: transparent` and
hiding `::-webkit-scrollbar`. The caret and the scrollbar are each worth a percent or two of
spurious diff on their own, and the scrollbar's presence flips with content height.

**3. Wait for three things, and don't trust any one of them.**
   - `networkidle`, **best-effort with a short timeout** — an app holding a websocket open never
     reaches it, and a hard wait here is itself a flake source. Log it and continue.
   - `document.fonts.ready` — a late webfont swap reflows text and is a top cause of
     intermittent diffs.
   - A fixed settle delay afterward (we used 450 ms) for late layout passes.

**4. Mask volatile content on BOTH sides.** Overlay live numbers with a solid block before
diffing, using the same selector and heuristic on the reference and the app. The comparison then
asserts **layout, not values**. Live data — clocks, recalculated stats, ticking figures —
legitimately changes between runs and there is no threshold that absorbs it without also
absorbing real regressions.

   The caveat is a feature, and say it out loud so nobody "fixes" it: masking hides **glyphs, not
   geometry**. If a value grows from `9.1` to `149.1` and pushes its column wider, the mask block
   widens too and the diff still fires — correctly, because a number that reflows its container
   *is* a layout bug. Verify the values themselves in unit tests, where they belong.

**5. Per-channel pixel tolerance.** Covered in §2; it belongs on this list because it is the
difference between a guard that idles at 0.1% and one that idles at 3%.

---

## 5. Threshold discipline — where these harnesses die

A threshold is a **budget for known, accepted, uninteresting difference**: font rasterisation
noise, a border-radius the reference draws slightly differently. It is not a place to park a
regression.

The procedure we gave agents, verbatim, because "raise it until green" is the default instinct:

1. Open the side-by-side and the diff image for the failing viewport. Look at **where** the red is.
2. Red spread thinly over text ⇒ antialiasing. Nudge the threshold, move on.
3. Red in a solid block, a shifted column, or a whole region ⇒ layout regression. **Fix the app.
   Do not raise the threshold.**
4. Raise in small steps and write down why in the commit message.
5. **Per screen, never globally.** A global number gets set to the worst screen and everything
   else becomes unguarded. A dense data table legitimately needs more headroom than a settings
   panel.

Rules of thumb that held up: under 2% is text noise; 2–10% is a real but bounded delta worth a
look; above 10% something structural is different.

**A threshold that only ever ratchets upward is a harness quietly retiring itself.** Worth
tracking the sum of all thresholds over time as its own signal — if it only grows, the guard is
dying and no single commit will look like the culprit.

---

## 6. Artifacts, and why agents need them

Every run writes, per screen per viewport: `reference.png`, `actual.png`, `diff.png`,
`sidebyside.png`, plus a machine-readable `summary.json` roll-up.

`sidebyside.png` is the one that does the work. An agent handed a diff percentage argues with the
number; an agent handed a side-by-side fixes the screen. The roll-up JSON is what lets you ask
"which screens regressed this week" without re-running anything.

Two process rules that mattered as much as the code:

- **Regenerate reference screenshots of every key surface on merge**, at both widths, in both
  themes, committed. Whoever is doing design work has no running app — this is how they see
  current reality instead of speccing against whatever capture someone happened to take.
- **UI work is never "done" on an agent's own report.** Require "built, pending screenshot
  verification" plus an attached screenshot. We had a fully green test suite coexist with an
  entirely missing screen, because no test asserted the screen existed. That is precisely the
  hole layer 2 (§2) closes.

---

## 7. What we'd tell you to skip

- **Don't start with token-level computed-style assertions.** High effort, high maintenance,
  and they pass while the page is visibly wrong.
- **Don't use a hosted visual-diff service as the first move.** The value is in the pinning
  discipline and the verdict ladder, and both are ~600 lines of Playwright + Pillow you fully
  control. Adopt a service later if you want the review UI.
- **Don't diff unmasked and "just live with" a noisy baseline.** That is the failure mode. Every
  team that does this mutes the check within two weeks.
- **Don't let one global threshold cover every screen.** See §5.

---

## 8. Suggested order of work

1. Build the harness with **layers 1 and 2** and the four-verdict ladder. No thresholds yet —
   run everything at a generous default.
2. Pin one reference screen end to end. Get it to a stable, repeatable diff number across three
   consecutive runs *before* pinning any others. If it isn't stable, fix §4 — do not proceed.
3. Add the remaining screens with realistic content. An empty table proves nothing.
4. Set per-screen thresholds from observed noise floors, and write down the reasoning.
5. Only now fan agents out on the failures, one screen per agent, each required to attach a
   side-by-side.
6. Wire it into CI on the `MISSING`/`ERROR` exit codes first — those are unambiguous — and turn
   on `FAIL` once thresholds have settled.
