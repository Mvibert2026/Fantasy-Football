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
import argparse, datetime, itertools, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "docs" / "handoffs"
INDEX = HANDOFFS / "OPEN.md"
PM_OUTBOX = ROOT / "docs" / "pm-outbox"
DECISIONS_NEEDED = ROOT / "docs" / "decisions-needed.md"
DECISIONS_LOG = ROOT / "docs" / "decisions.md"
ADR_DRAFTS = ROOT / "docs" / "adr-drafts"

ROLES = ["pm", "backend", "frontend", "data-ops", "strategist", "researcher", "librarian", "design", "founder", "fable"]
OPEN_STATUSES = {"OPEN", "BLOCKED-ON-YOU", "BLOCKED-EXTERNAL"}
STALE_DAYS = 14
NEW_STALE_DAYS = 1  # W1(d): an unfiled NEW-*.md thread older than this is a problem

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
        self.body: str = ""
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
    """Back-compat helper some callers may still use. Prefer next_free_id()."""
    nums = [int(t.id) for t in threads if t.id.isdigit()]
    return f"{max(nums) + 1 if nums else 1:03d}"


def next_free_id() -> int:
    """W1(c): allocate from filenames on disk, never from parsed frontmatter --
    a thread's own ID: field can be wrong, missing, or (pre-sync) not exist at all.
    Scanning the directory listing is the one thing that can't lie."""
    if not HANDOFFS.exists():
        return 1
    nums = [int(m.group(1)) for p in HANDOFFS.glob("*.md") if (m := re.match(r"^(\d{3})-", p.name))]
    return (max(nums) + 1) if nums else 1


def _rel(path: pathlib.Path) -> str:
    """Best-effort path-for-humans. Falls back to the absolute path when the given
    path isn't under ROOT (e.g. a test pointed the module at a scratch tmp_path)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "thread"


def _stamp_frontmatter(text: str, nid: int, today: str) -> str:
    """Insert/overwrite ID: and OPENED: in a thread's frontmatter block. Refuses to
    proceed on a file with no frontmatter at all -- that is a malformed thread, not
    something to paper over with a guessed block."""
    if not text.startswith("---"):
        raise SystemExit(f"handoffs sync: file has no frontmatter block, refusing to stamp it")
    _, fm, body = text.split("---", 2)
    lines = fm.strip("\n").splitlines()
    out_lines: list[str] = []
    has_id = has_opened = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("ID:"):
            out_lines.append(f"ID: {nid:03d}")
            has_id = True
        elif stripped.upper().startswith("OPENED:"):
            out_lines.append(f"OPENED: {today}")
            has_opened = True
        else:
            out_lines.append(line)
    if not has_id:
        out_lines.insert(0, f"ID: {nid:03d}")
    if not has_opened:
        out_lines.append(f"OPENED: {today}")
    return "---\n" + "\n".join(out_lines) + "\n---" + body


def _pending_new_files() -> list[pathlib.Path]:
    """Files awaiting ID allocation: NEW-*.md in docs/handoffs/, and anything the PM
    dropped in docs/pm-outbox/ (its only write surface into the mailbox, per W1)."""
    pending = []
    if HANDOFFS.exists():
        pending += sorted(HANDOFFS.glob("NEW-*.md"))
    if PM_OUTBOX.exists():
        pending += sorted(p for p in PM_OUTBOX.glob("*.md") if p.name.upper() != "README.MD")
    return pending


def _ingest_one(src: pathlib.Path, nid: int, today: str) -> pathlib.Path:
    """Allocate a single pending file to a specific ID. Split out from ingest_pending()
    so the hard-fail-on-collision behaviour is testable as a defense-in-depth property in
    its own right, independent of whether next_free_id() ever actually produces a
    colliding number in practice."""
    stem = src.stem
    raw_slug = stem[4:] if stem.upper().startswith("NEW-") else stem
    slug = _slugify(raw_slug)
    dest = HANDOFFS / f"{nid:03d}-{slug}.md"
    if dest.exists():
        raise SystemExit(
            f"handoffs sync: refusing to overwrite existing {_rel(dest)} "
            f"while ingesting {_rel(src)}"
        )
    text = src.read_text(encoding="utf-8")
    dest.write_text(_stamp_frontmatter(text, nid, today), encoding="utf-8")
    src.unlink()
    return dest


def ingest_pending(today: str | None = None) -> list[pathlib.Path]:
    """W1(b): rename every pending file to {next_free_id:03d}-<slug>.md, stamp ID/OPENED,
    hard-fail rather than overwrite an existing path. Idempotent: running with nothing
    pending is a no-op."""
    today = today or datetime.date.today().isoformat()
    ingested: list[pathlib.Path] = []
    for src in _pending_new_files():
        nid = next_free_id()
        ingested.append(_ingest_one(src, nid, today))
    return ingested


def cmd_sync(_args) -> int:
    now = datetime.date.today().isoformat()
    ingested = ingest_pending(now)
    for p in ingested:
        print(f"sync: allocated {_rel(p)}")
    threads = load()
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
    print(f"sync: {len(threads)} threads, {len(open_threads)} open -> {_rel(INDEX)}")
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
    """W1(a): write NEW-<slug>.md with no ID: field. Nobody types a number, so nobody
    can collide on one. sync (called at the end of this command) allocates the real ID."""
    slug = _slugify(args.subject)
    path = HANDOFFS / f"NEW-{slug}.md"
    if path.exists():
        raise SystemExit(f"handoffs new: {_rel(path)} already pending allocation")
    path.write_text(
        f"""---
FROM: {args.frm}
TO: {args.to}
STATUS: OPEN
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
    print(f"created {_rel(path)} (unallocated -- sync will assign the ID)")
    return cmd_sync(args)


def adr_next() -> int:
    """W2: scan docs/decisions.md and docs/adr-drafts/ for ADR-\\d+ and return the next
    free number. Same failure as thread IDs (max+1 read from one place while another
    place is being written), same fix: one function, called instead of remembered.
    Regression case: ADR-048 collided (commit 1140586) because two agents each computed
    max+1 from a stale read of docs/decisions.md alone."""
    nums: list[int] = []
    if DECISIONS_LOG.exists():
        nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", DECISIONS_LOG.read_text(encoding="utf-8"))]
    if ADR_DRAFTS.exists():
        for p in ADR_DRAFTS.glob("*.md"):
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", p.read_text(encoding="utf-8"))]
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", p.name)]
    return (max(nums) + 1) if nums else 1


def cmd_adr(args) -> int:
    if args.adr_cmd == "next":
        print(adr_next())
        return 0
    print(f"unknown adr subcommand '{args.adr_cmd}'", file=sys.stderr)
    return 2


# --- Contradiction detection (062 Part 2 / RECONCILIATION-2026-07.md Part 2 design) ---
# Deliberately crude: false positives are fine, per the founder's stated tolerance.
# Exactly the two heuristics 062 authorized -- nothing from 065's expanded scope.

ANTONYM_PAIRS = [
    ("add", "remove"), ("show", "hide"), ("enable", "disable"),
    ("randomise", "order"), ("randomize", "order"),
]


# Paths/words so common across this repo's threads (every session touches CURRENT-STATE.md,
# most touch frontend/ or src/) that treating them as a shared "target" produces noise on
# nearly every pair rather than signal on the rare real collision. Crude detection still
# needs this floor, or "a glance" becomes "dozens of glances every run."
_GENERIC_TARGETS = {
    "frontend/", "src/", "docs/", "docs/handoffs/", "check", "open", "open.md",
    "current-state.md", "docs/current-state.md", "docs/decisions-needed.md",
    "backend", "strategist", "delta", "lambda", "docs/adr/",
}


def normalize_target(text: str) -> set[str]:
    """Candidate 'target' tokens: short backticked identifiers, short quoted phrases,
    and CamelCase component names. Crude on purpose, but bounded on purpose too --
    an early version matched bare capitalized words (`The`, `Open`, `Status`, sentence
    starts) and whole boilerplate sentences repeated verbatim across unrelated threads
    (e.g. this repo's own screenshot-limitation disclaimer), which flagged nearly every
    thread pair and drowned the one signal this check exists for."""
    targets: set[str] = set()
    targets.update(m for m in re.findall(r"`([^`]{2,40})`", text) if " " not in m or "." in m)
    targets.update(m for m in re.findall(r'"([^"]{2,40})"', text) if len(m.split()) <= 4)
    targets.update(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+\b", text))  # CamelCase: DraftRoom, TypeAhead
    return {t.lower() for t in targets} - _GENERIC_TARGETS


def verb_hits(text: str) -> set[str]:
    hits = set()
    for pair in ANTONYM_PAIRS:
        for verb in pair:
            if re.search(rf"\b{re.escape(verb)}\b", text, re.IGNORECASE):
                hits.add(verb)
    return hits


def flag_antonym_collisions(threads: list[Thread]) -> list[tuple[Thread, Thread, str]]:
    """Rule 1: two threads naming the same file/component with opposing verbs."""
    flags = []
    for a, b in itertools.combinations(threads, 2):
        shared = normalize_target(a.body) & normalize_target(b.body)
        if not shared:
            continue
        verbs_a, verbs_b = verb_hits(a.body), verb_hits(b.body)
        for v1, v2 in ANTONYM_PAIRS:
            if (v1 in verbs_a and v2 in verbs_b) or (v2 in verbs_a and v1 in verbs_b):
                flags.append((a, b, f"shared target {sorted(shared)}, antonym pair ({v1}/{v2})"))
    return flags


def parse_decided_ids(path: pathlib.Path = DECISIONS_NEEDED) -> set[str]:
    """D-numbers explicitly marked DECIDED in docs/decisions-needed.md. Deliberately
    narrow: only the literal word DECIDED on the row, not CLOSED/MOOT/SUPERSEDED --
    matching 062's ask exactly ('a D- number already marked DECIDED')."""
    if not path.exists():
        return set()
    decided = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(D-\d+)\s*\|", line)
        if m and "DECIDED" in line:
            decided.add(m.group(1))
    return decided


def flag_stale_decision_refs(threads: list[Thread], decided_ids: set[str]) -> list[tuple[Thread, str]]:
    """Rule 2: an open thread referencing a D- number already marked DECIDED."""
    flags = []
    for t in threads:
        for d_id in sorted(set(re.findall(r"\bD-\d+\b", t.body))):
            if d_id in decided_ids:
                flags.append((t, d_id))
    return flags


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

    # W1(d): a NEW-*.md file (or an unfiled pm-outbox drop) that has sat unallocated
    # for more than a day is a thread nobody ran `sync` on.
    now_ts = datetime.datetime.now().timestamp()
    for p in _pending_new_files():
        age = (now_ts - p.stat().st_mtime) / 86400
        if age >= NEW_STALE_DAYS:
            problems.append(f"{_rel(p)}: unfiled {age:.1f}d — run `handoffs.py sync`")

    if problems:
        print("mailbox check FAILED:\n")
        for p in problems:
            print(f"  - {p}")
        print("\nA neglected mailbox is how this system dies quietly. Fix or explicitly re-status.")
        return 1

    # Contradiction detection (062 Part 2): runs inside `check`, but reported as
    # warnings rather than build failures. False positives are declared acceptable
    # ("a glance"); a hard failure on every legitimate reference to a decided D-number
    # would make the mailbox the bottleneck 062 explicitly said this must not become.
    open_threads = [t for t in threads if t.is_open]
    antonym_flags = flag_antonym_collisions(open_threads)
    decided = parse_decided_ids()
    decision_flags = flag_stale_decision_refs(open_threads, decided)
    if antonym_flags or decision_flags:
        print(f"mailbox check OK — {len(threads)} threads, none stale, all addressed.")
        print("\ncontradiction warnings (non-fatal, glance and disposition):")
        for a, b, why in antonym_flags:
            print(f"  - {a.path.name} <-> {b.path.name}: {why}")
        for t, d_id in decision_flags:
            print(f"  - {t.path.name}: references {d_id}, already marked DECIDED")
        return 0

    print(f"mailbox check OK — {len(threads)} threads, none stale, all addressed.")
    return 0


def main() -> int:
    # Some Windows terminals default stdout to cp1252, which cannot encode the
    # arrows/emoji this tool prints. Reconfigure rather than let a print() crash
    # the whole command over a cosmetic character.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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
    p_adr = sub.add_parser("adr", help="ADR number allocation (W2)")
    adr_sub = p_adr.add_subparsers(dest="adr_cmd", required=True)
    adr_sub.add_parser("next", help="print the next free ADR-NNN number")
    args = ap.parse_args()
    return {"sync": cmd_sync, "inbox": cmd_inbox, "new": cmd_new, "check": cmd_check, "adr": cmd_adr}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
