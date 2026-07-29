#!/usr/bin/env python3
"""
Founder request tool — regenerates the backlog index from per-request files.

docs/founder-requests.md was a single file every session appended new requests to *and* later
sessions edited in place to update an existing request's Status:. Unlike docs/status.md (a pure
append log, fixed by tools/status_log.py), FR numbers are referenced by number throughout the
repo and get mutated over their lifetime -- the same concurrent-edit-to-one-blob conflict shape
as docs/CURRENT-STATE.md, not an append shape. So this follows docs/handoffs/ instead: one file
per FR (docs/founder-requests/FR-NNN-slug.md), an index generated from those files, and ID
allocation via a staged NEW-*.md file so nobody hand-types a number.

docs/founder-requests.md is frozen (existing FR-001..FR-017 stay there, unmodified, as archive).
This tool's allocator seeds past whatever's highest there so new numbers never collide with the
archive.

Usage
-----
    python tools/founder_requests.py new --raised-by "cowork chat" --subject "..."
    python tools/founder_requests.py sync                 # regenerate docs/founder-requests/INDEX.md
"""

from __future__ import annotations
import argparse, datetime, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FR_DIR = ROOT / "docs" / "founder-requests"
INDEX = FR_DIR / "INDEX.md"
ARCHIVE = ROOT / "docs" / "founder-requests.md"

FIELD = re.compile(r"^([A-Z_]+):\s*(.*)$")
STATUS_VALUES = ["NEW", "SCOPING", "SPECCED", "IN PROGRESS", "SHIPPED", "DECLINED", "DEFERRED"]


def _rel(path: pathlib.Path) -> str:
    """Best-effort path-for-humans. Falls back to the absolute path when the given
    path isn't under ROOT (e.g. a test pointed the module at a scratch tmp_path)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class Request:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.meta: dict[str, str] = {}
        self.body = ""
        self._parse()

    def _parse(self):
        text = self.path.read_text(encoding="utf-8")
        if text.startswith("---"):
            _, fm, body = text.split("---", 2)
            for line in fm.strip().splitlines():
                m = FIELD.match(line.strip())
                if m:
                    self.meta[m.group(1)] = m.group(2).strip()
        else:
            body = text
        self.body = body

    @property
    def id(self) -> str: return self.meta.get("ID", "???")
    @property
    def status(self) -> str: return self.meta.get("STATUS", "NEW").upper()
    @property
    def raised(self) -> str: return self.meta.get("RAISED", "")
    @property
    def source(self) -> str: return self.meta.get("SOURCE", "?")
    @property
    def subject(self) -> str:
        # stem is "FR-NNN-slug"; strip the "FR-NNN-" prefix, not just the first hyphen.
        m = re.match(r"^FR-\d{3}-(.+)$", self.path.stem)
        slug = m.group(1) if m else self.path.stem
        return slug.replace("-", " ").capitalize()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "request"


def load() -> list[Request]:
    if not FR_DIR.exists():
        return []
    files = sorted(p for p in FR_DIR.glob("FR-*.md") if re.match(r"^FR-\d{3}-", p.name))
    return [Request(p) for p in files]


def _archive_max() -> int:
    """Highest FR-NNN referenced in the frozen archive file, so new allocations never collide
    with it. Deliberately scans the whole file, not just headers, since the archive is known to
    contain at least one duplicate heading (FR-015 appears twice) -- the max is still correct
    even if the archive's own numbering has a bug in it."""
    if not ARCHIVE.exists():
        return 0
    nums = [int(n) for n in re.findall(r"FR-(\d{3})", ARCHIVE.read_text(encoding="utf-8"))]
    return max(nums) if nums else 0


def next_free_id() -> int:
    """W1-style allocation (see tools/handoffs.py): scan filenames on disk, never frontmatter --
    a file's own ID: field can be wrong or missing. Floor is the archive's highest number so new
    FRs never collide with the frozen file."""
    nums = [_archive_max()]
    if FR_DIR.exists():
        nums += [int(m.group(1)) for p in FR_DIR.glob("FR-*.md") if (m := re.match(r"^FR-(\d{3})-", p.name))]
    return max(nums) + 1


def _pending_new_files() -> list[pathlib.Path]:
    if not FR_DIR.exists():
        return []
    return sorted(FR_DIR.glob("NEW-*.md"))


def _stamp(text: str, nid: int, today: str) -> str:
    if not text.startswith("---"):
        raise SystemExit("founder_requests sync: file has no frontmatter block, refusing to stamp it")
    _, fm, body = text.split("---", 2)
    lines = fm.strip("\n").splitlines()
    out_lines: list[str] = []
    has_id = has_raised = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("ID:"):
            out_lines.append(f"ID: FR-{nid:03d}")
            has_id = True
        elif stripped.upper().startswith("RAISED:"):
            out_lines.append(f"RAISED: {today}")
            has_raised = True
        else:
            out_lines.append(line)
    if not has_id:
        out_lines.insert(0, f"ID: FR-{nid:03d}")
    if not has_raised:
        out_lines.append(f"RAISED: {today}")
    return "---\n" + "\n".join(out_lines) + "\n---" + body


def _ingest_one(src: pathlib.Path, nid: int, today: str) -> pathlib.Path:
    """Allocate a single pending file to a specific ID. Split out from ingest_pending() so the
    hard-fail-on-collision behaviour is testable as a defense-in-depth property in its own
    right (mirrors tools/handoffs.py's _ingest_one, same reasoning: thread 076 -- two
    worktrees can each compute a locally-valid "next free" number that collides at merge)."""
    stem = src.stem
    raw_slug = stem[4:] if stem.upper().startswith("NEW-") else stem
    slug = _slugify(raw_slug)
    dest = FR_DIR / f"FR-{nid:03d}-{slug}.md"
    if dest.exists():
        raise SystemExit(
            f"founder_requests sync: refusing to overwrite existing "
            f"{_rel(dest)} while ingesting {_rel(src)}"
        )
    text = src.read_text(encoding="utf-8")
    dest.write_text(_stamp(text, nid, today), encoding="utf-8")
    src.unlink()
    return dest


def ingest_pending(today: str | None = None) -> list[pathlib.Path]:
    today = today or datetime.date.today().isoformat()
    ingested = []
    for src in _pending_new_files():
        nid = next_free_id()
        ingested.append(_ingest_one(src, nid, today))
    return ingested


def cmd_new(args) -> int:
    FR_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(args.subject)
    path = FR_DIR / f"NEW-{slug}.md"
    if path.exists():
        raise SystemExit(f"founder_requests new: {_rel(path)} already pending allocation")
    path.write_text(
        f"""---
STATUS: NEW
SOURCE: {args.raised_by}
---

## Request
{args.subject}

<Founder's own words where possible -- paraphrase only when necessary, and say so.>

## Why it matters

## Initial read
<Not the founder's own words -- your read on scope, constraints, sequencing.>
""",
        encoding="utf-8",
    )
    print(f"created {_rel(path)} (unallocated -- sync will assign the ID)")
    return cmd_sync(args)


def cmd_sync(_args) -> int:
    FR_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.date.today().isoformat()
    ingested = ingest_pending(now)
    for p in ingested:
        print(f"sync: allocated {_rel(p)}")

    requests = load()
    out = [
        "# Founder requests — combined view",
        "",
        f"**Generated {now} by `tools/founder_requests.py sync` — do not hand-edit.**",
        "Per-request files in this directory are the source of truth. Edit a request's own file's",
        "`STATUS:` line, then re-run sync. Protocol: [`README.md`](README.md).",
        "Archive (FR-001..FR-017, frozen): [`../founder-requests.md`](../founder-requests.md).",
        "",
        f"**{len(requests)} requests since freeze.**",
        "",
        "---",
        "",
    ]
    for status in STATUS_VALUES:
        mine = [r for r in requests if r.status == status]
        out += [f"## {status} — {len(mine)}", ""]
        if not mine:
            out += ["_None._", ""]
            continue
        out += ["| ID | Subject | Raised | Source |", "|---|---|---|---|"]
        for r in sorted(mine, key=lambda x: x.id):
            out.append(f"| [{r.id}]({r.path.name}) | {r.subject} | {r.raised} | {r.source} |")
        out.append("")

    unknown = [r for r in requests if r.status not in STATUS_VALUES]
    if unknown:
        out += ["## Unknown status — check these", ""]
        out += ["| ID | Subject | Status |", "|---|---|---|"]
        for r in sorted(unknown, key=lambda x: x.id):
            out.append(f"| [{r.id}]({r.path.name}) | {r.subject} | `{r.status}` |")
        out.append("")

    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"sync: {len(requests)} requests -> {_rel(INDEX)}")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="open a new founder request")
    p_new.add_argument("--raised-by", required=True, help="e.g. 'cowork chat', 'claude code session'")
    p_new.add_argument("--subject", required=True)
    sub.add_parser("sync", help="regenerate docs/founder-requests/INDEX.md from request files")
    args = ap.parse_args()
    return {"new": cmd_new, "sync": cmd_sync}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
