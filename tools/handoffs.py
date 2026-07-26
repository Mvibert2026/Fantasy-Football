#!/usr/bin/env python3
"""
Handoff mailbox tool — regenerates the inter-agent message index from the thread files themselves.

The index is never hand-edited. Threads are the source of truth; OPEN.md is a view.

Usage
-----
    python tools/handoffs.py sync                 # regenerate docs/handoffs/OPEN.md
    python tools/handoffs.py inbox backend        # print one role's inbox (start every session here)
    python tools/handoffs.py new --from pm --to backend --subject "Fix the thing"
    python tools/handoffs.py check                # non-zero exit if the mailbox is unhealthy

`check` is the one that keeps this honest. It fails on: threads addressed to nobody, a thread
whose STATUS is RESOLVED but which never received a reply, stale OPEN threads past the age
threshold, and duplicate IDs. Wire it into the test suite so a neglected mailbox breaks the build
rather than quietly rotting.
"""

from __future__ import annotations
import argparse, datetime, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "docs" / "handoffs"
INDEX = HANDOFFS / "OPEN.md"

ROLES = ["pm", "backend", "frontend", "data-ops", "strategist", "researcher", "librarian", "design", "founder", "fable"]
OPEN_STATUSES = {"OPEN", "BLOCKED-ON-YOU", "BLOCKED-EXTERNAL"}
STALE_DAYS = 14

# Design cannot read this repo. Threads to it need a human hop, so they are surfaced separately
# rather than sitting in a queue nothing will ever poll.
UNREACHABLE = {"design"}

FIELD = re.compile(r"^([A-Z-]+):\s*(.*)$")
REPLY = re.compile(r"^###\s+(\S+)\s+·", re.M)


class Thread:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.meta: dict[str, str] = {}
        self.replies: list[str] = []
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
        self.replies = REPLY.findall(body)

    @property
    def id(self) -> str: return self.meta.get("ID", "???")
    @property
    def frm(self) -> str: return self.meta.get("FROM", "?").lower()
    @property
    def status(self) -> str: return self.meta.get("STATUS", "OPEN").upper()
    @property
    def opened(self) -> str: return self.meta.get("OPENED", "")
    @property
    def blocks(self) -> str: return self.meta.get("BLOCKS", "none")

    @property
    def to(self) -> list[str]:
        raw = self.meta.get("TO", "").lower()
        raw = raw.split(" via:")[0]
        return [r.strip() for r in re.split(r"[,/]| and ", raw) if r.strip()]

    @property
    def subject(self) -> str:
        stem = self.path.stem
        return stem.split("-", 1)[1].replace("-", " ").capitalize() if "-" in stem else stem

    @property
    def age_days(self) -> int | None:
        try:
            d = datetime.date.fromisoformat(self.opened)
            return (datetime.date.today() - d).days
        except Exception:
            return None

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES

    def waiting_on(self) -> list[str]:
        """Who actually needs to act — not the same as TO once a thread bounces back."""
        if self.status == "BLOCKED-ON-YOU":
            return [self.frm]
        if self.status == "BLOCKED-EXTERNAL":
            return []
        return self.to


def load() -> list[Thread]:
    if not HANDOFFS.exists():
        return []
    files = sorted(p for p in HANDOFFS.glob("*.md") if re.match(r"^\d{3}-", p.name))
    return [Thread(p) for p in files]


def next_id(threads: list[Thread]) -> str:
    nums = [int(t.id) for t in threads if t.id.isdigit()]
    return f"{max(nums) + 1 if nums else 1:03d}"


def cmd_sync(_args) -> int:
    threads = load()
    now = datetime.date.today().isoformat()
    out = [
        "# Open handoffs",
        "",
        f"**Generated {now} by `tools/handoffs.py sync` — do not hand-edit.**",
        "Threads are the source of truth. Change a thread's `STATUS:`, then re-run sync.",
        "Protocol: [`README.md`](README.md).",
        "",
    ]

    open_threads = [t for t in threads if t.is_open]
    stale = [t for t in open_threads if (t.age_days or 0) >= STALE_DAYS]

    out += [
        f"**{len(open_threads)} open** · {len(threads) - len(open_threads)} resolved"
        + (f" · **{len(stale)} stale (≥{STALE_DAYS}d)**" if stale else ""),
        "",
        "---",
        "",
        "## Inboxes",
        "",
        "Every role gets a section, including empty ones — an empty inbox is a fact worth stating,",
        "not an omission. Start your session at your own heading.",
        "",
    ]

    for role in ROLES:
        mine = [t for t in open_threads if role in t.waiting_on()]
        flag = "  ⚠️ *cannot read this repo — needs a human hop via pm*" if role in UNREACHABLE else ""
        out += [f"### `{role}` — {len(mine)} waiting{flag}", ""]
        if not mine:
            out += ["_Nothing waiting on you._", ""]
            continue
        out += ["| ID | Subject | From | Status | Age | Blocks |", "|---|---|---|---|---|---|"]
        for t in sorted(mine, key=lambda x: x.id):
            age = f"{t.age_days}d" if t.age_days is not None else "—"
            if t.age_days is not None and t.age_days >= STALE_DAYS:
                age = f"**{age}** ⚠️"
            out.append(
                f"| [{t.id}]({t.path.name}) | {t.subject} | `{t.frm}` | {t.status} | {age} | {t.blocks} |"
            )
        out.append("")

    external = [t for t in open_threads if t.status == "BLOCKED-EXTERNAL"]
    if external:
        out += ["---", "", "## Blocked externally — nobody can act", ""]
        out += ["| ID | Subject | Opened |", "|---|---|---|"]
        for t in sorted(external, key=lambda x: x.id):
            out.append(f"| [{t.id}]({t.path.name}) | {t.subject} | {t.opened} |")
        out.append("")

    resolved = [t for t in threads if not t.is_open]
    if resolved:
        out += ["---", "", "## Resolved", "", "| ID | Subject | From → To |", "|---|---|---|"]
        for t in sorted(resolved, key=lambda x: x.id):
            out.append(f"| [{t.id}]({t.path.name}) | {t.subject} | `{t.frm}` → `{', '.join(t.to)}` |")
        out.append("")

    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"sync: {len(threads)} threads, {len(open_threads)} open -> {INDEX.relative_to(ROOT)}")
    return 0


def cmd_inbox(args) -> int:
    role = args.role.lower()
    if role not in ROLES:
        print(f"unknown role '{role}'. known: {', '.join(ROLES)}", file=sys.stderr)
        return 2
    mine = [t for t in load() if t.is_open and role in t.waiting_on()]
    if not mine:
        print(f"[{role}] inbox empty — nothing is waiting on you.")
        return 0
    print(f"[{role}] {len(mine)} waiting:\n")
    for t in sorted(mine, key=lambda x: x.id):
        age = f", {t.age_days}d old" if t.age_days is not None else ""
        warn = "  ⚠️ STALE" if (t.age_days or 0) >= STALE_DAYS else ""
        print(f"  {t.id}  {t.subject}")
        print(f"       from {t.frm}, {t.status}{age}{warn}")
        print(f"       docs/handoffs/{t.path.name}\n")
    print("Reply in each thread and update its STATUS before you finish, then run: "
          "python tools/handoffs.py sync")
    return 0


def cmd_new(args) -> int:
    threads = load()
    nid = next_id(threads)
    slug = re.sub(r"[^a-z0-9]+", "-", args.subject.lower()).strip("-")[:48]
    path = HANDOFFS / f"{nid}-{slug}.md"
    path.write_text(
        f"""---
ID: {nid}
FROM: {args.frm}
TO: {args.to}
STATUS: OPEN
OPENED: {datetime.date.today().isoformat()}
BLOCKS: {args.blocks}
---

## Ask
{args.subject}

<Specify fully. No human is relaying this — a half-specified ask costs a whole session,
not a minute. Exact paths, exact field names, and what you will do with the answer.>

## Why
<The consequence of not doing it. This is how the other role prioritises against its own queue.>

## Done looks like
<The exact artifact that closes this thread. Commit hash, test count, screenshot, a yes/no.>
""",
        encoding="utf-8",
    )
    print(f"created {path.relative_to(ROOT)}")
    return cmd_sync(args)


def cmd_check(_args) -> int:
    threads = load()
    problems: list[str] = []

    seen: dict[str, str] = {}
    for t in threads:
        if t.id in seen:
            problems.append(f"{t.path.name}: duplicate ID {t.id} (also {seen[t.id]})")
        seen[t.id] = t.path.name

        if not t.to:
            problems.append(f"{t.path.name}: no TO: role — nobody will ever pick this up")
        for r in t.to:
            if r not in ROLES:
                problems.append(f"{t.path.name}: unknown role '{r}'")
        if t.status == "RESOLVED" and not t.replies:
            problems.append(
                f"{t.path.name}: RESOLVED with no reply — resolution must carry its artifact"
            )
        if t.is_open and (t.age_days or 0) >= STALE_DAYS:
            problems.append(
                f"{t.path.name}: open {t.age_days}d, waiting on {', '.join(t.waiting_on()) or 'nobody'}"
            )

    if problems:
        print("mailbox check FAILED:\n")
        for p in problems:
            print(f"  - {p}")
        print("\nA neglected mailbox is how this system dies quietly. Fix or explicitly re-status.")
        return 1
    print(f"mailbox check OK — {len(threads)} threads, none stale, all addressed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync", help="regenerate OPEN.md from thread files")
    p_in = sub.add_parser("inbox", help="print one role's inbox")
    p_in.add_argument("role")
    p_new = sub.add_parser("new", help="open a new thread")
    p_new.add_argument("--from", dest="frm", required=True, choices=ROLES)
    p_new.add_argument("--to", required=True)
    p_new.add_argument("--subject", required=True)
    p_new.add_argument("--blocks", default="none")
    sub.add_parser("check", help="fail if the mailbox is unhealthy (wire into CI)")
    args = ap.parse_args()
    return {"sync": cmd_sync, "inbox": cmd_inbox, "new": cmd_new, "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
