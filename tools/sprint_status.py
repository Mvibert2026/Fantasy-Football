#!/usr/bin/env python3
"""
Sprint status — a cheap, local view of what a running sprint has actually done.

Two purposes, and the split matters:

  1. `watch` prints a live dashboard in your terminal. Costs nothing — no model, no tokens.
     Leave it running in a second window while a sprint works.

  2. every run also writes `docs/handoffs/SPRINT-STATUS.md`, a deliberately tiny summary
     (well under 1 KB) that the Cowork PM can read for a few hundred tokens instead of
     listing the whole repo for several thousand. Ask it to "read SPRINT-STATUS" rather
     than "check the repo" and the same question costs an order of magnitude less.

Usage
-----
    python tools/sprint_status.py            # print once, write the status file
    python tools/sprint_status.py watch      # refresh every 30s until Ctrl-C
    python tools/sprint_status.py watch 10   # refresh every 10s
    python tools/sprint_status.py --since 3ea391b   # count commits from a specific mark

Reads only. Never modifies anything except SPRINT-STATUS.md.
"""

from __future__ import annotations
import datetime as dt
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "docs" / "handoffs"
STATUS_OUT = HANDOFFS / "SPRINT-STATUS.md"
MARK_FILE = ROOT / ".sprint-mark"

WATCHED = [
    "docs/CURRENT-STATE.md",
    "docs/status.md",
    "docs/decisions-needed.md",
    "docs/founder-requests.md",
    "docs/decisions.md",
]

OPEN_STATUSES = {"OPEN", "BLOCKED-ON-YOU", "BLOCKED-EXTERNAL"}


def sh(*args: str) -> str:
    """Run a git command, return stdout stripped. Empty string on any failure."""
    try:
        r = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, timeout=20, check=False
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def baseline() -> str:
    """The commit the sprint started from. Set once, reused, so counts stay stable."""
    if MARK_FILE.exists():
        m = MARK_FILE.read_text(encoding="utf-8").strip()
        if m:
            return m
    head = sh("git", "rev-parse", "--short", "HEAD")
    if head:
        MARK_FILE.write_text(head + "\n", encoding="utf-8")
    return head


def ago(ts: float) -> str:
    s = max(0, int(time.time() - ts))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d"


def threads() -> tuple[int, int, dict[str, int], list[str]]:
    """Return (open, resolved, per-role waiting counts, recently-replied thread ids)."""
    if not HANDOFFS.exists():
        return 0, 0, {}, []
    op = res = 0
    waiting: dict[str, int] = {}
    recent: list[str] = []
    cutoff = time.time() - 3600
    for p in sorted(HANDOFFS.glob("*.md")):
        if not re.match(r"^\d{3}-", p.name):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        fm = txt.split("---", 2)[1] if txt.startswith("---") else ""
        get = lambda k: (re.search(rf"^{k}:\s*(.*)$", fm, re.M) or [None, ""])[1].strip()
        status = (get("STATUS") or "OPEN").upper()
        tid = get("ID") or p.stem[:3]
        if status in OPEN_STATUSES:
            op += 1
            who = get("FROM").lower() if status == "BLOCKED-ON-YOU" else get("TO").lower()
            for r in re.split(r"[,/]| and ", who.split(" via:")[0]):
                r = r.strip()
                if r:
                    waiting[r] = waiting.get(r, 0) + 1
        else:
            res += 1
        # a reply is a "### role · date" heading in the body
        if re.search(r"^###\s+\S+\s+·", txt, re.M) and p.stat().st_mtime > cutoff:
            recent.append(tid)
    return op, res, waiting, recent


def tests() -> str:
    """Most recent test count mentioned in CURRENT-STATE.md, if any."""
    p = ROOT / "docs" / "CURRENT-STATE.md"
    if not p.exists():
        return "—"
    m = re.search(r"\*\*(\d{2,5})\s+passing\*\*", p.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else "—"


def collect() -> dict:
    base = baseline()
    head = sh("git", "rev-parse", "--short", "HEAD")
    log = sh("git", "log", "--oneline", f"{base}..HEAD") if base and head else ""
    commits = [l for l in log.splitlines() if l.strip()]
    dirty = [l for l in sh("git", "status", "--porcelain").splitlines() if l.strip()]
    op, res, waiting, recent = threads()

    touched = []
    for rel in WATCHED:
        f = ROOT / rel
        if f.exists():
            touched.append((rel.split("/")[-1], ago(f.stat().st_mtime)))

    return {
        "base": base or "?",
        "head": head or "?",
        "commits": commits,
        "dirty": dirty,
        "open": op,
        "resolved": res,
        "waiting": waiting,
        "recent": recent,
        "tests": tests(),
        "touched": touched,
    }


def render(d: dict) -> str:
    L = []
    L.append("=" * 66)
    L.append(f"  SPRINT STATUS   {dt.datetime.now().strftime('%H:%M:%S')}")
    L.append("=" * 66)
    L.append(f"  baseline {d['base']}  ->  head {d['head']}")
    L.append(f"  commits this sprint : {len(d['commits'])}")
    for c in d["commits"][-6:]:
        L.append(f"      {c[:72]}")
    L.append(f"  uncommitted changes : {len(d['dirty'])}")
    L.append(f"  tests (CURRENT-STATE): {d['tests']}")
    L.append("")
    L.append(f"  threads  open {d['open']}   resolved {d['resolved']}")
    if d["waiting"]:
        row = "  ".join(f"{k}:{v}" for k, v in sorted(d["waiting"].items()))
        L.append(f"  waiting on           {row}")
    if d["recent"]:
        L.append(f"  replied in last hour {', '.join(d['recent'])}")
    L.append("")
    L.append("  last touched")
    for name, when in d["touched"]:
        L.append(f"      {name:<24} {when} ago")
    L.append("=" * 66)
    if not d["commits"] and not d["dirty"]:
        L.append("  Nothing written yet. A session reads for a while before it writes —")
        L.append("  that leaves no trace. Worry after ~15 min of nothing at all.")
        L.append("=" * 66)
    return "\n".join(L)


def write_status(d: dict) -> None:
    """Tiny file for the Cowork PM to read cheaply. Keep it small on purpose."""
    lines = [
        "# Sprint status (generated — do not edit)",
        "",
        f"generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"baseline: {d['base']} -> head: {d['head']}",
        f"commits: {len(d['commits'])} | uncommitted: {len(d['dirty'])} | tests: {d['tests']}",
        f"threads: {d['open']} open, {d['resolved']} resolved",
    ]
    if d["waiting"]:
        lines.append("waiting: " + ", ".join(f"{k}={v}" for k, v in sorted(d["waiting"].items())))
    if d["recent"]:
        lines.append("replied recently: " + ", ".join(d["recent"]))
    if d["commits"]:
        lines.append("")
        lines.append("recent commits:")
        lines += [f"- {c[:80]}" for c in d["commits"][-8:]]
    try:
        HANDOFFS.mkdir(parents=True, exist_ok=True)
        STATUS_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"(could not write status file: {e})", file=sys.stderr)


def main() -> int:
    args = sys.argv[1:]
    if "--since" in args:
        i = args.index("--since")
        if i + 1 < len(args):
            MARK_FILE.write_text(args[i + 1] + "\n", encoding="utf-8")
            print(f"baseline set to {args[i + 1]}")
            args = args[:i] + args[i + 2:]

    if args and args[0] == "watch":
        every = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        try:
            while True:
                d = collect()
                write_status(d)
                os.system("cls" if os.name == "nt" else "clear")
                print(render(d))
                print(f"\n  refreshing every {every}s — Ctrl-C to stop")
                time.sleep(every)
        except KeyboardInterrupt:
            print("\nstopped.")
        return 0

    d = collect()
    write_status(d)
    print(render(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
