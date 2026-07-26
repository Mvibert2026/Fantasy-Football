#!/usr/bin/env python3
"""Automated visual-fidelity checking for the fantasy football draft assistant.

What this does
--------------
For every screen listed in ``docs/design-reference/screens.json`` (or discovered
by convention from ``docs/design-reference/*.html``) this harness:

1. Renders the *pinned* design reference HTML from ``file://`` and screenshots it
   full-page.
2. Navigates the *running* app to the mapped route and screenshots it full-page.
3. Optionally masks numeric content on both sides so the comparison asserts
   LAYOUT, not VALUES.
4. Computes a pixel diff and emits ``reference.png``, ``actual.png``,
   ``diff.png`` and ``sidebyside.png`` under
   ``artifacts/fidelity/<screen>/<viewport>/``.

Verdicts (evaluated in this priority order)
-------------------------------------------
``MISSING``  The screen is not really there: the route 404s, the page threw an
             uncaught error, the body rendered effectively empty, or the diff is
             so large that "this screen was never built" is the only honest
             reading. **Never suppressible by per-screen thresholds.**
``FAIL``     Diff above the screen's configured threshold.
``PASS``     Diff at or below the screen's configured threshold.
``ERROR``    The *harness* broke (timeout, browser crash, unreadable file).
             Deliberately distinct from MISSING: MISSING is a statement about
             the product, ERROR is a statement about this script.

Exit codes (highest severity present wins)
------------------------------------------
``0``  every checked screen/viewport PASSed
``1``  at least one FAIL (and no MISSING/ERROR)
``2``  at least one MISSING (and no ERROR)
``3``  at least one ERROR

Dependencies: ``playwright`` (sync API) and ``Pillow``. ``numpy`` is used when
importable purely as a speed-up; the harness degrades gracefully without it.

Chromium is expected to be preinstalled at ``PLAYWRIGHT_BROWSERS_PATH``
(``/opt/pw-browsers``). This script never runs ``playwright install``.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw

try:  # numpy is an optional accelerator, never a requirement.
    import numpy as _np  # type: ignore

    HAVE_NUMPY = True
except ImportError:  # pragma: no cover - exercised only on numpy-less machines
    _np = None  # type: ignore
    HAVE_NUMPY = False

try:
    from playwright.sync_api import Browser, Error as PlaywrightError, Page
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover - environment problem, not logic
    sys.stderr.write(
        "fidelity: playwright is not importable (%s).\n"
        "Install it with `pip install playwright`. Do NOT run "
        "`playwright install` in this environment: Chromium is preinstalled at "
        "PLAYWRIGHT_BROWSERS_PATH (/opt/pw-browsers).\n" % exc
    )
    raise SystemExit(3)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
REFERENCE_DIR: Path = REPO_ROOT / "docs" / "design-reference"
SCREENS_JSON: Path = REFERENCE_DIR / "screens.json"
BASELINE_DIR: Path = REFERENCE_DIR / "baselines"
ARTIFACT_DIR: Path = REPO_ROOT / "artifacts" / "fidelity"
SUMMARY_PATH: Path = ARTIFACT_DIR / "summary.json"

DEFAULT_BASE_URL: str = "http://localhost:5173"
DEFAULT_THRESHOLD: float = 0.05

# --- MISSING floors: HARDCODED ON PURPOSE ---------------------------------- #
# These are module constants and are deliberately NOT read from screens.json.
#
# Why: a per-screen threshold exists so a team can say "this screen is 6% off and
# we accept that for now". It must never be able to say "this screen does not
# exist and we accept that". If MISSING were tunable, the first response to an
# unbuilt or crashing screen would be to raise its threshold to 1.0, the harness
# would go green, and the board would report fidelity on a screen that renders a
# white rectangle. A harness that can be configured into agreeing with you is not
# a check, it is a rubber stamp. So: thresholds gate FAIL/PASS only. The MISSING
# path below reads these constants and nothing else.
GROSS_DIFF_CEILING: float = 0.60  # diff >= 60% => the screen isn't the screen
MIN_BODY_TEXT_BYTES: int = 40  # rendered innerText shorter than this => empty
MIN_PIXEL_STDDEV: float = 1.5  # grayscale stddev below this => blank canvas
# --------------------------------------------------------------------------- #

# Per-channel delta below which two pixels are considered equal. Absorbs
# subpixel antialiasing and GPU-free rasterisation noise without hiding real
# colour or position changes.
PIXEL_TOLERANCE: int = 12

PAD_COLOR: Tuple[int, int, int] = (255, 0, 255)  # magenta; loud on purpose
DIFF_HIGHLIGHT: Tuple[int, int, int] = (255, 32, 64)

VIEWPORTS: Dict[str, Tuple[int, int]] = {
    "desktop": (1440, 900),
    "mobile": (390, 844),
}

DEFAULT_MASK_SELECTOR: str = "[data-numeric], .tabular-nums, .font-mono, .stat-value"

NAV_TIMEOUT_MS: int = 30_000
SETTLE_MS: int = 450  # post-networkidle quiet period for late layout/fonts
FROZEN_EPOCH_MS: int = 1_735_689_600_000  # 2025-01-01T00:00:00Z

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_MISSING = "MISSING"
VERDICT_ERROR = "ERROR"
VERDICT_UPDATED = "UPDATED"  # --update-baseline only; never affects exit code

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_MISSING = 2
EXIT_ERROR = 3

_EXIT_FOR_VERDICT: Dict[str, int] = {
    VERDICT_UPDATED: EXIT_OK,
    VERDICT_PASS: EXIT_OK,
    VERDICT_FAIL: EXIT_FAIL,
    VERDICT_MISSING: EXIT_MISSING,
    VERDICT_ERROR: EXIT_ERROR,
}


# --------------------------------------------------------------------------- #
# Browser-side injected scripts
# --------------------------------------------------------------------------- #

# Determinism: freeze the clock and de-randomise Math.random before any app code
# runs. A draft board that renders "3s ago" or shuffles tie-breaks randomly would
# otherwise produce a nonzero diff on every single run.
DETERMINISM_INIT_JS: str = """
(() => {
  const FROZEN = %d;
  const RealDate = Date;
  class FrozenDate extends RealDate {
    constructor(...args) {
      if (args.length === 0) { super(FROZEN); } else { super(...args); }
    }
    static now() { return FROZEN; }
  }
  // eslint-disable-next-line no-global-assign
  window.Date = FrozenDate;
  let seed = 0x2f6e2b1;
  Math.random = () => {
    seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
    return ((seed >>> 0) %% 1000000) / 1000000;
  };
  try {
    window.performance.now = () => 0;
  } catch (err) { /* read-only in some builds; harmless */ }
})();
""" % FROZEN_EPOCH_MS

STILLNESS_CSS: str = """
*, *::before, *::after {
  animation-duration: 0s !important;
  animation-delay: 0s !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0s !important;
  transition-delay: 0s !important;
  scroll-behavior: auto !important;
}
html { caret-color: transparent !important; }
::-webkit-scrollbar { display: none !important; }
"""

# Numeric masking. See mask_numeric_content() for the rationale comment.
MASK_JS: str = """
(config) => {
  const { selector, blockColor } = config;
  const DIGIT = /[0-9]/;
  const MAX_TEXT = 240;
  let masked = 0;

  const isNumericFont = (cs) => {
    const fam = (cs.fontFamily || '').toLowerCase();
    if (fam.includes('mono') || fam.includes('courier') || fam.includes('consolas')) {
      return true;
    }
    const fvn = (cs.fontVariantNumeric || '') + ' ' + (cs.fontFeatureSettings || '');
    return fvn.toLowerCase().includes('tabular');
  };

  let explicit = [];
  if (selector) {
    try { explicit = Array.from(document.querySelectorAll(selector)); }
    catch (err) { explicit = []; }
  }
  const explicitSet = new Set(explicit);

  const candidates = new Set(explicit);
  for (const el of document.querySelectorAll('body *')) {
    if (candidates.has(el)) continue;
    if (el.childElementCount > 0) continue;      // leaf text nodes only
    const text = (el.textContent || '').trim();
    if (!text || text.length > MAX_TEXT || !DIGIT.test(text)) continue;
    const cs = window.getComputedStyle(el);
    if (isNumericFont(cs)) candidates.add(el);
  }

  for (const el of candidates) {
    const text = (el.textContent || '').trim();
    if (!explicitSet.has(el)) {
      if (!text || !DIGIT.test(text) || text.length > MAX_TEXT) continue;
    }
    const rect = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) continue;
    el.style.setProperty('color', 'transparent', 'important');
    el.style.setProperty('text-shadow', 'none', 'important');
    el.style.setProperty('background-image', 'none', 'important');
    el.style.setProperty('background-color', blockColor, 'important');
    el.setAttribute('data-fidelity-masked', '1');
    masked += 1;
  }
  return masked;
}
"""

BODY_TEXT_JS: str = """
() => {
  const b = document.body;
  if (!b) return '';
  return (b.innerText || b.textContent || '').replace(/\\s+/g, ' ').trim();
}
"""


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ScreenConfig:
    """One screen under test."""

    name: str
    route: str
    threshold: float
    reference_html: Path
    mask_selector: str = DEFAULT_MASK_SELECTOR

    def artifact_dir(self, viewport: str) -> Path:
        """Return the artifact directory for this screen at ``viewport``."""
        return ARTIFACT_DIR / self.name / viewport


@dataclass
class Capture:
    """One rendered page: its PNG bytes plus the health signals we sampled."""

    png: bytes
    status: Optional[int]
    body_text_len: int
    page_errors: List[str] = field(default_factory=list)
    masked_elements: int = 0


@dataclass
class DiffResult:
    """Outcome of comparing two PNGs."""

    diff_ratio: float
    changed_pixels: int
    total_pixels: int
    ref_size: Tuple[int, int]
    actual_size: Tuple[int, int]
    padded: bool
    diff_image: Image.Image


@dataclass
class CheckResult:
    """Verdict for one (screen, viewport) pair."""

    screen: str
    viewport: str
    route: str
    verdict: str
    diff_ratio: Optional[float]
    threshold: float
    reason: str = ""
    artifacts: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        """Serialise to a plain dict for ``summary.json``."""
        return {
            "screen": self.screen,
            "viewport": self.viewport,
            "route": self.route,
            "verdict": self.verdict,
            "diffPercent": (
                None if self.diff_ratio is None else round(self.diff_ratio * 100.0, 4)
            ),
            "diffRatio": (
                None if self.diff_ratio is None else round(self.diff_ratio, 6)
            ),
            "thresholdPercent": round(self.threshold * 100.0, 4),
            "thresholdRatio": self.threshold,
            "reason": self.reason,
            "artifacts": self.artifacts,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------- #
# Configuration loading
# --------------------------------------------------------------------------- #


def _route_by_convention(name: str) -> str:
    """Derive a route from a screen name when screens.json is absent.

    ``board`` -> ``/draft/board``; anything else -> ``/<name>``. The draft-scoped
    guess covers the app's primary surfaces; everything else falls back to a flat
    route. This is a guess and the caller announces it as such.
    """
    draft_scoped = {"board", "opponents", "predictions", "queue", "roster"}
    slug = name.strip().strip("/").replace("_", "-")
    if slug in draft_scoped:
        return "/draft/%s" % slug
    return "/%s" % slug


def load_screens(
    reference_dir: Path,
    screens_json: Path,
    default_threshold: float,
    mask_selector: str,
) -> Tuple[List[ScreenConfig], List[str]]:
    """Build the screen list from ``screens.json`` or by convention.

    Returns the screens plus a list of human-readable notices to print (for
    example, announcing that routes were guessed).

    Raises:
        FileNotFoundError: if ``reference_dir`` holds no ``*.html`` files.
        ValueError: if ``screens.json`` exists but is malformed.
    """
    notices: List[str] = []
    html_files = sorted(p for p in reference_dir.glob("*.html") if p.is_file())
    if not html_files:
        raise FileNotFoundError(
            "No reference HTML found in %s. Reference files must be pinned and "
            "committed; see %s/README.md." % (reference_dir, reference_dir)
        )
    by_name = {p.stem: p for p in html_files}

    config: Dict[str, Any] = {}
    if screens_json.is_file():
        try:
            raw = json.loads(screens_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Could not parse %s: %s" % (screens_json, exc)) from exc
        if not isinstance(raw, dict):
            raise ValueError(
                "%s must be a JSON object mapping screen name -> config."
                % screens_json
            )
        config = raw
    else:
        notices.append(
            "screens.json not found at %s - deriving routes by convention "
            "(board -> /draft/board, other -> /<name>) and using the default "
            "threshold of %.1f%% for every screen." % (screens_json, default_threshold * 100)
        )

    screens: List[ScreenConfig] = []
    for name in sorted(set(by_name) | set(config)):
        entry = config.get(name, {})
        if not isinstance(entry, dict):
            raise ValueError(
                "screens.json entry for %r must be an object, got %s"
                % (name, type(entry).__name__)
            )
        html = by_name.get(name)
        if html is None:
            notices.append(
                "screens.json lists %r but %s/%s.html does not exist - skipping. "
                "A screen without a pinned reference cannot be checked."
                % (name, reference_dir.name, name)
            )
            continue
        threshold = entry.get("threshold", default_threshold)
        try:
            threshold = float(threshold)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "screens.json threshold for %r is not a number: %r" % (name, threshold)
            ) from exc
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "screens.json threshold for %r must be a ratio in [0, 1], got %r"
                % (name, threshold)
            )
        if threshold >= GROSS_DIFF_CEILING:
            notices.append(
                "screen %r has threshold %.0f%% at or above the hardcoded gross "
                "ceiling of %.0f%% - the ceiling wins and this screen will be "
                "reported MISSING, not PASS."
                % (name, threshold * 100, GROSS_DIFF_CEILING * 100)
            )
        route = entry.get("route")
        if route is None:
            route = _route_by_convention(name)
            if config:
                notices.append(
                    "screens.json entry %r has no route - guessed %s."
                    % (name, route)
                )
        if not isinstance(route, str) or not route.startswith("/"):
            raise ValueError(
                "screens.json route for %r must be an absolute path starting with "
                "'/', got %r" % (name, route)
            )
        screens.append(
            ScreenConfig(
                name=name,
                route=route,
                threshold=threshold,
                reference_html=html,
                mask_selector=str(entry.get("maskSelector", mask_selector)),
            )
        )
    return screens, notices


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _prepare_page(page: "Page") -> None:
    """Apply determinism settings that must be in place before navigation."""
    page.set_default_timeout(NAV_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
    page.add_init_script(DETERMINISM_INIT_JS)


def mask_numeric_content(page: "Page", selector: str, verbose: bool) -> int:
    """Overlay numeric content with solid blocks so the diff tests layout.

    Data-dense screens (a draft board, a projections table, an opponent-needs
    grid) carry live numbers that legitimately change between runs: VOR ticks,
    ADP updates, a clock. Diffing those raw means the harness shows red on every
    single run for reasons nobody needs to act on.

    That is worse than having no harness at all. A check that is always red gets
    muted within a week, and a muted check still sits in CI looking like
    coverage: it produces false assurance that somebody is watching the UI while
    in fact nobody is. So by default we mask the numbers and assert the thing
    that actually should be stable - the LAYOUT - and let VALUES be verified by
    unit tests, where they belong.

    Caveat worth knowing: masking hides glyphs, not geometry. If a value grows
    from ``9.1`` to ``149.1`` and pushes its column wider, the mask block widens
    too and the diff still fires. That is intentional. A number that reflows its
    container is a layout bug, not data noise.

    Args:
        page: the loaded page.
        selector: CSS selector for explicitly-tagged numeric elements.
        verbose: print the number of masked elements.

    Returns:
        Count of elements masked.
    """
    masked = page.evaluate(
        MASK_JS, {"selector": selector, "blockColor": "#1b1f24"}
    )
    count = int(masked or 0)
    if verbose:
        print("      masked %d numeric element(s) with %r" % (count, selector))
    return count


def capture(
    page: "Page",
    url: str,
    *,
    mask: bool,
    mask_selector: str,
    verbose: bool,
) -> Capture:
    """Navigate to ``url``, settle the page, and screenshot it full-page.

    Raises:
        PlaywrightTimeoutError: navigation or screenshot exceeded the timeout.
        PlaywrightError: the browser or page failed (crash, protocol error).
    """
    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    if verbose:
        print("      GET %s" % url)
    response = page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    status = response.status if response is not None else None

    # networkidle is best-effort: an app holding a websocket open will never
    # reach it, and that must not be reported as a harness ERROR.
    try:
        page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT_MS // 2)
    except PlaywrightTimeoutError:
        if verbose:
            print("      networkidle not reached; continuing after settle delay")

    page.add_style_tag(content=STILLNESS_CSS)
    try:
        page.evaluate(
            "() => document.fonts ? document.fonts.ready.then(() => true) : true"
        )
    except PlaywrightError:
        pass  # font loading API unavailable; the settle delay covers us
    page.wait_for_timeout(SETTLE_MS)

    if mask:
        masked_count = mask_numeric_content(page, mask_selector, verbose)
        page.wait_for_timeout(80)  # let the style writes paint
    else:
        masked_count = 0

    body_text = str(page.evaluate(BODY_TEXT_JS) or "")
    png = page.screenshot(full_page=True, animations="disabled", caret="hide")

    return Capture(
        png=png,
        status=status,
        body_text_len=len(body_text),
        page_errors=page_errors,
        masked_elements=masked_count,
    )


# --------------------------------------------------------------------------- #
# Image diffing (Pillow required, numpy optional)
# --------------------------------------------------------------------------- #


def _load_png(data: bytes) -> Image.Image:
    """Decode PNG bytes into an RGB image."""
    with Image.open(io.BytesIO(data)) as img:
        return img.convert("RGB")


def _pad_to(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Return ``img`` pasted top-left onto a ``size`` canvas of ``PAD_COLOR``."""
    if img.size == size:
        return img
    canvas = Image.new("RGB", size, PAD_COLOR)
    canvas.paste(img, (0, 0))
    return canvas


def grayscale_stddev(img: Image.Image) -> float:
    """Population standard deviation of the image's grayscale histogram.

    Used as the "did anything render at all" floor. A blank white body, a solid
    error page, or a spinner-only shell all sit near zero.
    """
    hist = img.convert("L").histogram()
    total = sum(hist)
    if total == 0:
        return 0.0
    mean = sum(value * count for value, count in enumerate(hist)) / total
    variance = sum(count * (value - mean) ** 2 for value, count in enumerate(hist)) / total
    return math.sqrt(variance)


def _max_channel_delta(ref: Image.Image, actual: Image.Image) -> Image.Image:
    """Per-pixel max absolute channel delta, as an ``L`` image."""
    delta = ImageChops.difference(ref, actual)
    r, g, b = delta.split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b)


def diff_images(
    ref_png: bytes, actual_png: bytes, tolerance: int = PIXEL_TOLERANCE
) -> DiffResult:
    """Compare two PNGs and build a highlighted diff image.

    Images of differing dimensions are padded to the larger canvas in both axes.
    Padding is deliberately counted as difference (a page that is 400px taller
    than its reference *is* different) and flagged via ``DiffResult.padded``.
    """
    ref = _load_png(ref_png)
    actual = _load_png(actual_png)
    ref_size, actual_size = ref.size, actual.size
    canvas = (max(ref_size[0], actual_size[0]), max(ref_size[1], actual_size[1]))
    padded = ref_size != actual_size
    ref_p = _pad_to(ref, canvas)
    actual_p = _pad_to(actual, canvas)
    total = canvas[0] * canvas[1]

    if HAVE_NUMPY:
        ref_a = _np.asarray(ref_p, dtype=_np.int16)
        act_a = _np.asarray(actual_p, dtype=_np.int16)
        delta = _np.abs(ref_a - act_a).max(axis=2)
        mask_a = delta > tolerance
        changed = int(mask_a.sum())
        mask = Image.fromarray((mask_a * 255).astype("uint8"), mode="L")
    else:
        delta_img = _max_channel_delta(ref_p, actual_p)
        mask = delta_img.point(lambda v: 255 if v > tolerance else 0, mode="L")
        changed = sum(
            count for value, count in enumerate(mask.histogram()) if value > 0
        )

    ratio = (changed / total) if total else 0.0

    base = ref_p.convert("L").convert("RGB")
    base = Image.blend(base, Image.new("RGB", canvas, (255, 255, 255)), 0.55)
    overlay = Image.new("RGB", canvas, DIFF_HIGHLIGHT)
    diff_image = Image.composite(overlay, base, mask)

    return DiffResult(
        diff_ratio=ratio,
        changed_pixels=changed,
        total_pixels=total,
        ref_size=ref_size,
        actual_size=actual_size,
        padded=padded,
        diff_image=diff_image,
    )


def build_side_by_side(
    ref_png: bytes, actual_png: bytes, diff_image: Image.Image
) -> Image.Image:
    """Compose a labelled reference | actual | diff contact sheet."""
    panels = [
        ("reference", _load_png(ref_png)),
        ("actual", _load_png(actual_png)),
        ("diff", diff_image),
    ]
    gutter, header, pad = 12, 22, 8
    width = sum(p.width for _, p in panels) + gutter * (len(panels) - 1) + pad * 2
    height = max(p.height for _, p in panels) + header + pad * 2
    sheet = Image.new("RGB", (width, height), (24, 26, 30))
    draw = ImageDraw.Draw(sheet)

    x = pad
    for label, panel in panels:
        draw.text((x + 2, pad + 4), label.upper(), fill=(235, 235, 235))
        sheet.paste(panel, (x, pad + header))
        draw.rectangle(
            [x, pad + header, x + panel.width - 1, pad + header + panel.height - 1],
            outline=(80, 84, 92),
        )
        x += panel.width + gutter
    return sheet


# --------------------------------------------------------------------------- #
# Verdict logic
# --------------------------------------------------------------------------- #


def classify(
    *,
    actual: Capture,
    actual_image: Image.Image,
    diff: DiffResult,
    threshold: float,
) -> Tuple[str, str]:
    """Return ``(verdict, reason)`` for a completed comparison.

    Priority is MISSING, then FAIL, then PASS. Every MISSING branch reads the
    module-level hardcoded floors only - ``threshold`` is not consulted until
    after all MISSING checks have been cleared, which is what makes MISSING
    untunable.
    """
    if actual.status is not None and actual.status >= 400:
        return VERDICT_MISSING, "route returned HTTP %d" % actual.status
    if actual.page_errors:
        return (
            VERDICT_MISSING,
            "uncaught page error: %s" % actual.page_errors[0][:160],
        )
    if actual.body_text_len < MIN_BODY_TEXT_BYTES:
        return (
            VERDICT_MISSING,
            "body rendered %d chars of text, floor is %d"
            % (actual.body_text_len, MIN_BODY_TEXT_BYTES),
        )
    stddev = grayscale_stddev(actual_image)
    if stddev < MIN_PIXEL_STDDEV:
        return (
            VERDICT_MISSING,
            "rendered canvas is effectively blank (grayscale stddev %.2f < %.2f)"
            % (stddev, MIN_PIXEL_STDDEV),
        )
    if diff.diff_ratio >= GROSS_DIFF_CEILING:
        return (
            VERDICT_MISSING,
            "diff %.1f%% at/above hardcoded gross ceiling %.0f%% - not a "
            "threshold-tunable condition"
            % (diff.diff_ratio * 100, GROSS_DIFF_CEILING * 100),
        )

    # Only now does per-screen tuning get a vote.
    if diff.diff_ratio > threshold:
        return (
            VERDICT_FAIL,
            "diff %.2f%% exceeds threshold %.2f%%"
            % (diff.diff_ratio * 100, threshold * 100),
        )
    return (
        VERDICT_PASS,
        "diff %.2f%% within threshold %.2f%%"
        % (diff.diff_ratio * 100, threshold * 100),
    )


# --------------------------------------------------------------------------- #
# Per-screen driver
# --------------------------------------------------------------------------- #


def _write_png(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _image_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _rel(path: Path) -> str:
    """Repo-relative POSIX path for the summary, falling back to absolute."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def check_screen_viewport(
    browser: "Browser",
    screen: ScreenConfig,
    viewport_name: str,
    base_url: str,
    *,
    mask: bool,
    update_baseline: bool,
    verbose: bool,
) -> CheckResult:
    """Render, diff and classify one screen at one viewport."""
    width, height = VIEWPORTS[viewport_name]
    route_url = base_url.rstrip("/") + screen.route
    out_dir = screen.artifact_dir(viewport_name)
    notes: List[str] = []
    if not HAVE_NUMPY:
        notes.append("numpy unavailable; used the pure-Pillow diff path")

    result = CheckResult(
        screen=screen.name,
        viewport=viewport_name,
        route=screen.route,
        verdict=VERDICT_ERROR,
        diff_ratio=None,
        threshold=screen.threshold,
        notes=notes,
    )

    context = None
    try:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            reduced_motion="reduce",
            color_scheme="light",
            locale="en-US",
            timezone_id="UTC",
        )
        page = context.new_page()
        _prepare_page(page)

        if verbose:
            print("    reference: %s" % screen.reference_html)
        ref_capture = capture(
            page,
            screen.reference_html.resolve().as_uri(),
            mask=mask,
            mask_selector=screen.mask_selector,
            verbose=verbose,
        )
        ref_path = out_dir / "reference.png"
        _write_png(ref_path, ref_capture.png)
        result.artifacts["reference"] = _rel(ref_path)

        if update_baseline:
            baseline = BASELINE_DIR / screen.name / ("%s.png" % viewport_name)
            _write_png(baseline, ref_capture.png)
            result.artifacts["baseline"] = _rel(baseline)
            result.verdict = VERDICT_UPDATED
            result.diff_ratio = None
            result.reason = (
                "baseline render refreshed from pinned HTML; app not compared"
            )
            return result

        page.close()
        page = context.new_page()
        _prepare_page(page)

        app_capture = capture(
            page,
            route_url,
            mask=mask,
            mask_selector=screen.mask_selector,
            verbose=verbose,
        )
        actual_path = out_dir / "actual.png"
        _write_png(actual_path, app_capture.png)
        result.artifacts["actual"] = _rel(actual_path)

        diff = diff_images(ref_capture.png, app_capture.png)
        diff_path = out_dir / "diff.png"
        _write_png(diff_path, _image_bytes(diff.diff_image))
        result.artifacts["diff"] = _rel(diff_path)

        sheet = build_side_by_side(ref_capture.png, app_capture.png, diff.diff_image)
        sheet_path = out_dir / "sidebyside.png"
        _write_png(sheet_path, _image_bytes(sheet))
        result.artifacts["sidebyside"] = _rel(sheet_path)

        if diff.padded:
            notes.append(
                "size mismatch: reference %dx%d vs actual %dx%d; padded to %dx%d "
                "and counted the padding as difference"
                % (
                    diff.ref_size[0],
                    diff.ref_size[1],
                    diff.actual_size[0],
                    diff.actual_size[1],
                    max(diff.ref_size[0], diff.actual_size[0]),
                    max(diff.ref_size[1], diff.actual_size[1]),
                )
            )
        if mask:
            notes.append(
                "numeric masking on: %d ref / %d app element(s) masked"
                % (ref_capture.masked_elements, app_capture.masked_elements)
            )
        else:
            notes.append("numeric masking OFF (--no-mask): values are being diffed")

        verdict, reason = classify(
            actual=app_capture,
            actual_image=_load_png(app_capture.png),
            diff=diff,
            threshold=screen.threshold,
        )
        result.verdict = verdict
        result.reason = reason
        result.diff_ratio = diff.diff_ratio
        return result

    except PlaywrightTimeoutError as exc:
        result.verdict = VERDICT_ERROR
        result.reason = "harness timeout after %dms: %s" % (
            NAV_TIMEOUT_MS,
            str(exc).splitlines()[0][:200],
        )
        return result
    except PlaywrightError as exc:
        result.verdict = VERDICT_ERROR
        result.reason = "browser failure: %s" % str(exc).splitlines()[0][:200]
        return result
    except (OSError, ValueError) as exc:
        result.verdict = VERDICT_ERROR
        result.reason = "harness I/O or decode failure: %s" % exc
        return result
    finally:
        if context is not None:
            try:
                context.close()
            except PlaywrightError:
                pass


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def render_table(results: Sequence[CheckResult]) -> str:
    """Render the results as a fixed-width stdout table."""
    headers = ("SCREEN", "VIEWPORT", "ROUTE", "VERDICT", "DIFF", "THRESH", "NOTE")
    rows: List[Tuple[str, ...]] = []
    for r in results:
        diff_s = "-" if r.diff_ratio is None else "%.2f%%" % (r.diff_ratio * 100)
        rows.append(
            (
                r.screen,
                r.viewport,
                r.route,
                r.verdict,
                diff_s,
                "%.2f%%" % (r.threshold * 100),
                r.reason[:72],
            )
        )
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(cells: Iterable[str]) -> str:
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)).rstrip()

    out = [line(headers), "  ".join("-" * w for w in widths)]
    out.extend(line(r) for r in rows)
    return "\n".join(out)


def write_summary(
    results: Sequence[CheckResult],
    base_url: str,
    mask: bool,
    notices: Sequence[str],
    exit_code: int,
) -> Path:
    """Write ``artifacts/fidelity/summary.json`` and return its path."""
    counts: Dict[str, int] = {}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    by_screen: Dict[str, Dict[str, Any]] = {}
    for r in results:
        by_screen.setdefault(r.screen, {})[r.viewport] = r.to_json()

    payload = {
        "baseUrl": base_url,
        "maskNumerics": mask,
        "pixelTolerance": PIXEL_TOLERANCE,
        "grossDiffCeilingPercent": GROSS_DIFF_CEILING * 100,
        "missingFloors": {
            "minBodyTextBytes": MIN_BODY_TEXT_BYTES,
            "minPixelStdDev": MIN_PIXEL_STDDEV,
            "note": "hardcoded; not overridable per screen",
        },
        "numpyAccelerated": HAVE_NUMPY,
        "notices": list(notices),
        "counts": counts,
        "exitCode": exit_code,
        "screens": by_screen,
        "results": [r.to_json() for r in results],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return SUMMARY_PATH


def compute_exit_code(results: Sequence[CheckResult]) -> int:
    """Highest-severity exit code across all results (see module docstring)."""
    return max((_EXIT_FOR_VERDICT[r.verdict] for r in results), default=EXIT_OK)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="fidelity",
        description=(
            "Compare the running draft assistant against pinned design "
            "reference HTML and report PASS / FAIL / MISSING / ERROR."
        ),
        epilog=(
            "Exit codes: 0 all PASS; 1 any FAIL; 2 any MISSING; 3 any ERROR "
            "(highest severity present wins)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--screens",
        default="",
        help="comma-separated screen names to check (default: all discovered)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FIDELITY_BASE_URL", DEFAULT_BASE_URL),
        help="base URL of the running app (env: FIDELITY_BASE_URL)",
    )
    parser.add_argument(
        "--viewport",
        choices=sorted(VIEWPORTS) + ["both"],
        default="both",
        help="viewport(s) to check",
    )
    parser.add_argument(
        "--no-mask",
        dest="mask",
        action="store_false",
        default=True,
        help="disable numeric masking and diff raw values (expect noise)",
    )
    parser.add_argument(
        "--mask-selector",
        default=DEFAULT_MASK_SELECTOR,
        help="CSS selector for explicitly numeric elements (screens.json "
        "'maskSelector' overrides this per screen)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="default diff threshold as a ratio, used when screens.json has none",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="re-render the pinned reference HTML into "
        "docs/design-reference/baselines/ and exit without comparing the app; "
        "never edits thresholds and never touches MISSING behaviour",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="chatty output")
    return parser


def _chromium_guidance(exc: BaseException) -> str:
    return (
        "fidelity: could not launch Chromium (%s).\n"
        "Chromium is preinstalled at PLAYWRIGHT_BROWSERS_PATH=%r. This harness "
        "must never run `playwright install`. Check that the env var is set and "
        "that a chromium-* directory exists under it; if it does not, the image "
        "is wrong and needs rebuilding - do not install browsers at runtime.\n"
        % (str(exc).splitlines()[0][:200], os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns the process exit code."""
    args = build_parser().parse_args(argv)

    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        sys.stderr.write(
            "fidelity: PLAYWRIGHT_BROWSERS_PATH is not set. Expected the "
            "preinstalled browsers at /opt/pw-browsers. Export it and re-run; "
            "do not run `playwright install`.\n"
        )
        return EXIT_ERROR

    try:
        screens, notices = load_screens(
            REFERENCE_DIR, SCREENS_JSON, args.threshold, args.mask_selector
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write("fidelity: %s\n" % exc)
        return EXIT_ERROR

    if args.screens:
        wanted = {s.strip() for s in args.screens.split(",") if s.strip()}
        known = {s.name for s in screens}
        unknown = sorted(wanted - known)
        if unknown:
            sys.stderr.write(
                "fidelity: unknown screen(s): %s. Known: %s\n"
                % (", ".join(unknown), ", ".join(sorted(known)))
            )
            return EXIT_ERROR
        screens = [s for s in screens if s.name in wanted]

    viewport_names = sorted(VIEWPORTS) if args.viewport == "both" else [args.viewport]

    for notice in notices:
        print("note: %s" % notice)
    if not HAVE_NUMPY:
        print("note: numpy not importable; using the slower pure-Pillow diff path.")
    print(
        "base URL: %s | screens: %d | viewports: %s | numeric masking: %s"
        % (
            args.base_url,
            len(screens),
            ", ".join(viewport_names),
            "on" if args.mask else "OFF (--no-mask)",
        )
    )
    if args.update_baseline:
        print("--update-baseline: refreshing reference renders; app not compared.")

    results: List[CheckResult] = []
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-lcd-text",
                        "--force-color-profile=srgb",
                        "--font-render-hinting=none",
                        "--hide-scrollbars",
                        "--disable-gpu",
                    ],
                )
            except PlaywrightError as exc:
                sys.stderr.write(_chromium_guidance(exc))
                return EXIT_ERROR
            try:
                for screen in screens:
                    for viewport_name in viewport_names:
                        if args.verbose:
                            print("  %s @ %s" % (screen.name, viewport_name))
                        results.append(
                            check_screen_viewport(
                                browser,
                                screen,
                                viewport_name,
                                args.base_url,
                                mask=args.mask,
                                update_baseline=args.update_baseline,
                                verbose=args.verbose,
                            )
                        )
            finally:
                try:
                    browser.close()
                except PlaywrightError:
                    pass
    except PlaywrightError as exc:
        sys.stderr.write(_chromium_guidance(exc))
        return EXIT_ERROR
    except KeyboardInterrupt:
        sys.stderr.write("fidelity: interrupted.\n")
        return EXIT_ERROR

    if not results:
        sys.stderr.write("fidelity: nothing to check.\n")
        return EXIT_ERROR

    print()
    print(render_table(results))
    print()

    exit_code = compute_exit_code(results)
    summary_path = write_summary(
        results, args.base_url, args.mask, notices, exit_code
    )
    counts: Dict[str, int] = {}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    print(
        "summary: %s"
        % (", ".join("%s=%d" % kv for kv in sorted(counts.items())) or "empty")
    )
    print("wrote %s" % _rel(summary_path))
    print("exit %d" % exit_code)
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - top-level guard, prints a real traceback
        traceback.print_exc()
        sys.stderr.write("fidelity: unhandled harness failure (see traceback).\n")
        sys.exit(EXIT_ERROR)
