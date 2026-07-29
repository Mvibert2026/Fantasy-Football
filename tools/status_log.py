#!/usr/bin/env python3
"""
Session log tool — regenerates the combined status view from per-session files.

docs/status.md was a single append-only log every session wrote to; under parallel worktrees
that made it the most common source of merge conflicts in the project (see
docs/reviews/fable-workflow-2026-07-27.md, work order W3). It is now frozen. New session
narratives live in docs/status/ as one dated file per session; docs/status/INDEX.md is the
generated combined view and is never hand-edited.

Usage
-----
    python tools/status_log.py new --role backend --slug short-slug   # scaffold a session file
    python tools/status_log.py sync                                   # regenerate INDEX.md
"""

from __future__ import annotations
import argparse, datetime, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATUS_DIR = ROOT / "docs" / "status"
INDEX = STATUS_DIR / "INDEX.md"

FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$")


def _rel(path: pathlib.Path) -> str:
    """Best-effort path-for-humans. Falls back to the absolute path when the given
    path isn't under ROOT (e.g. a test pointed the module at a scratch tmp_path)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "session"


def session_files() -> list[pathlib.Path]:
    """All dated session files, sorted chronologically by filename. Excludes README.md and
    INDEX.md itself, which live in the same directory but aren't session entries."""
    if not STATUS_DIR.exists():
        return []
    return sorted(p for p in STATUS_DIR.glob("*.md") if FILENAME_RE.match(p.name))


def cmd_new(args) -> int:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = _slugify(args.slug)
    role = args.role.lower()
    path = STATUS_DIR / f"{today}-{role}-{slug}.md"
    if path.exists():
        raise SystemExit(f"status_log new: {_rel(path)} already exists")
    path.write_text(
        f"# {today} — {role} — {args.slug}\n\n",
        encoding="utf-8",
    )
    print(f"created {_rel(path)}")
    return 0


def cmd_sync(_args) -> int:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    files = session_files()
    today = datetime.date.today().isoformat()
    out = [
        "# Status log — combined view",
        "",
        f"**Generated {today} by `tools/status_log.py sync` — do not hand-edit.**",
        "Session files in this directory are the source of truth. Add a new dated file, then",
        "re-run sync. Protocol: [`README.md`](README.md).",
        "",
        f"**{len(files)} sessions recorded.**",
        "",
        "---",
        "",
    ]
    for p in files:
        text = p.read_text(encoding="utf-8").rstrip("\n")
        out += [f"<!-- {p.name} -->", "", text, "", "---", ""]
    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"sync: {len(files)} session files -> {_rel(INDEX)}")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="scaffold a new session file")
    p_new.add_argument("--role", required=True)
    p_new.add_argument("--slug", required=True)
    sub.add_parser("sync", help="regenerate docs/status/INDEX.md from session files")
    args = ap.parse_args()
    return {"new": cmd_new, "sync": cmd_sync}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
