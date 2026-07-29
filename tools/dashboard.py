#!/usr/bin/env python
"""Regenerate `docs/dashboard.html` from the repo's own sources of truth.

CLAUDE.md's "Dashboards" rule asks for exactly this: a generator that reads
`docs/CURRENT-STATE.md` and `docs/handoffs/OPEN.md` so the dashboard cannot
drift from them. The previous `docs/dashboard.html` was a hand-written
point-in-time snapshot carrying no date at all, which made staleness
undetectable rather than merely likely.

Everything rendered here is either read from those files or measured from git
at run time. Nothing is hand-typed into this script.

Usage:
    python tools/dashboard.py            # write docs/dashboard.html
    python tools/dashboard.py --check    # exit 1 if the file is stale
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO / "docs" / "CURRENT-STATE.md"
OPEN_MD = REPO / "docs" / "handoffs" / "OPEN.md"
OUT = REPO / "docs" / "dashboard.html"


def git(*args: str) -> str:
    p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return p.stdout.strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def build_state_rows(text: str) -> list[tuple[str, str]]:
    """The machine-measured block between the BUILD-STATE markers."""
    m = re.search(r"BUILD-STATE:START.*?-->(.*?)<!--\s*BUILD-STATE:END", text, re.S)
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("- "):
            rows.append((cells[0], cells[1]))
    return rows


def open_counts(text: str) -> tuple[str, str, list[tuple[str, str]]]:
    """Totals and per-role waiting counts, as OPEN.md itself states them."""
    m = re.search(r"\*\*(\d+)\s+open\*\*.*?(\d+)\s+resolved", text, re.S)
    total_open, total_res = (m.group(1), m.group(2)) if m else ("?", "?")
    roles = re.findall(r"###\s+`([a-z-]+)`[^\d]*?(\d+)\s+waiting", text)
    return total_open, total_res, roles


def top_open_items(text: str) -> list[str]:
    """First sentence of each numbered entry under '## Top open items'."""
    m = re.search(r"##\s+Top open items\s*(.*?)(?=\n##\s|\Z)", text, re.S)
    if not m:
        return []
    items = []
    for num, body in re.findall(r"^(\d+)\.\s+(.*?)(?=^\d+\.\s|\Z)", m.group(1), re.S | re.M):
        flat = " ".join(body.split())
        cut = re.split(r"(?<=[.!?])\s", flat)[0]
        items.append("%s. %s" % (num, cut[:240]))
    return items


def last_verified(text: str) -> str:
    m = re.search(r"\*\*Last verified:\*\*\s*(.+?)(?:\.\s|\n\n)", text, re.S)
    return " ".join(m.group(1).split())[:300] if m else "not stated in CURRENT-STATE.md"


def render() -> str:
    cs, om = read(CURRENT_STATE), read(OPEN_MD)
    gen = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    head = git("rev-parse", "--short", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    # Exclude this page from its own dirty count: writing the dashboard would
    # otherwise change the number the dashboard reports, so a freshly written
    # file never matches a fresh render and `--check` is permanently red.
    dirty = git("status", "--porcelain")
    n_dirty = len([
        l for l in dirty.splitlines()
        if l.strip() and "docs/dashboard.html" not in l.replace("\\", "/")
    ])
    total_open, total_res, roles = open_counts(om)
    e = html.escape

    rows = "".join(
        "<tr><th>%s</th><td>%s</td></tr>" % (e(k), e(v)) for k, v in build_state_rows(cs)
    )
    role_cards = "".join(
        '<div class="card"><span class="n">%s</span><span class="l">%s</span></div>' % (e(n), e(r))
        for r, n in roles
    )
    items = "".join("<li>%s</li>" % e(i) for i in top_open_items(cs))

    return f"""<!doctype html>
<meta charset="utf-8">
<title>Fantasy Draft Assistant — Project Dashboard</title>
<style>
 :root {{ color-scheme: light dark; --fg:#111; --bg:#fff; --mut:#666; --line:#e3e3e3; --acc:#0b6; }}
 @media (prefers-color-scheme: dark) {{
   :root {{ --fg:#e8e8e8; --bg:#141414; --mut:#9a9a9a; --line:#2c2c2c; }}
 }}
 body {{ font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif; color:var(--fg);
        background:var(--bg); margin:0; padding:2rem 1.25rem; }}
 .wrap {{ max-width:900px; margin:0 auto; }}
 h1 {{ font-size:1.5rem; margin:0 0 .25rem; }}
 h2 {{ font-size:1rem; text-transform:uppercase; letter-spacing:.07em; color:var(--mut);
       margin:2rem 0 .6rem; }}
 .meta {{ color:var(--mut); font-size:.85rem; margin-bottom:.4rem; }}
 .warn {{ background:#fde68a22; border-left:3px solid #f59e0b; padding:.5rem .75rem;
          font-size:.85rem; margin:.75rem 0; }}
 table {{ border-collapse:collapse; width:100%; }}
 th,td {{ text-align:left; padding:.45rem .6rem; border-bottom:1px solid var(--line);
          vertical-align:top; }}
 th {{ width:34%; font-weight:600; }}
 .cards {{ display:flex; flex-wrap:wrap; gap:.6rem; }}
 .card {{ border:1px solid var(--line); border-radius:8px; padding:.6rem .9rem; min-width:92px; }}
 .card .n {{ display:block; font-size:1.35rem; font-weight:650; }}
 .card .l {{ display:block; color:var(--mut); font-size:.78rem; }}
 ol {{ padding-left:1.2rem; }} li {{ margin:.35rem 0; }}
 code {{ background:var(--line); padding:.1rem .3rem; border-radius:4px; }}
 footer {{ margin-top:2.5rem; color:var(--mut); font-size:.8rem;
           border-top:1px solid var(--line); padding-top:.8rem; }}
</style>
<div class="wrap">
<h1>Fantasy Draft Assistant — Project Dashboard</h1>
<div class="meta">Generated {e(gen)} by <code>tools/dashboard.py</code> from
 <code>docs/CURRENT-STATE.md</code> and <code>docs/handoffs/OPEN.md</code>.
 Regenerate rather than edit — hand-edits are overwritten.</div>
<div class="meta">Working tree: <code>{e(branch)}</code> @ <code>{e(head)}</code>
 — {n_dirty} uncommitted file(s).</div>
{'<div class="warn">Working tree is dirty; figures below may not match the last commit.</div>' if n_dirty else ''}

<h2>Build state (machine-measured)</h2>
<table>{rows or '<tr><td>BUILD-STATE markers not found in CURRENT-STATE.md</td></tr>'}</table>

<h2>Handoffs — {e(total_open)} open, {e(total_res)} resolved</h2>
<div class="cards">{role_cards or '<div class="card"><span class="l">no role sections parsed</span></div>'}</div>

<h2>Top open items</h2>
<ol>{items or '<li>none parsed</li>'}</ol>

<h2>Last verified</h2>
<p>{e(last_verified(cs))}</p>

<footer>Point-in-time by construction: this page is only as current as its last run.
 The generator reads the canonical files, so re-running it is always cheaper than trusting it.</footer>
</div>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if docs/dashboard.html differs from a fresh render")
    args = ap.parse_args()

    new = render()
    if args.check:
        cur = read(OUT)
        # Ignore the generated-at line, which changes every run by design.
        strip = lambda s: re.sub(r"Generated [\d\-: ]+", "Generated", s)
        if strip(cur) != strip(new):
            print("dashboard.py --check: docs/dashboard.html is STALE; run tools/dashboard.py")
            return 1
        print("dashboard.py --check: up to date")
        return 0

    OUT.write_text(new, encoding="utf-8")
    print("dashboard.py: wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
