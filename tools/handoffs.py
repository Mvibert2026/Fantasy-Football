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
import argparse, datetime, itertools, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "docs" / "handoffs"
INDEX = HANDOFFS / "OPEN.md"
PM_OUTBOX = ROOT / "docs" / "pm-outbox"
DECISIONS_NEEDED = ROOT / "docs" / "decisions-needed.md"
DECISIONS_LOG = ROOT / "docs" / "decisions.md"
ADR_DRAFTS = ROOT / "docs" / "adr-drafts"

ROLES = ["pm", "backend", "frontend", "data-ops", "strategist", "researcher", "librarian", "design", "founder", "fable", "ranker"]
OPEN_STATUSES = {"OPEN", "BLOCKED-ON-YOU", "BLOCKED-EXTERNAL"}
STALE_DAYS = 14
NEW_STALE_DAYS = 1  # W1(d): an unfiled NEW-*.md thread older than this is a problem

# Design cannot read this repo. Threads to it need a human hop, so they are surfaced separately
# rather than sitting in a queue nothing will ever poll.
UNREACHABLE = {"design"}

FIELD = re.compile(r"^([A-Z-]+):\s*(.*)$")
REPLY = re.compile(r"^###\s+(\S+)\s+·", re.M)

# W3 (ADR-see docs/decisions.md, 2026-07-30): new threads are named
# docs/handoffs/YYYY-MM-DD-slug.md, not NNN-slug.md. The old NNN- scheme required a
# shared "highest number so far" view to allocate the next one -- correct in a single
# worktree, structurally unable to see what a sibling worktree allocated in the same
# window (thread 076; collisions on 043/049/053, commit 1140586 for ADR-048's twin).
# date+slug needs no shared counter at all: two agents naming different things on the
# same day get different filenames for free, and the rare same-day-same-slug case
# becomes an ordinary git filename conflict at merge (loud, blocks the merge) instead
# of the old failure mode (two different filenames silently carrying the same ID:,
# which merges cleanly and only surfaces if someone happens to notice).
# Existing NNN-slug.md threads are NEVER renamed -- old numeric IDs keep resolving.
LEGACY_ID_RE = re.compile(r"^\d{3}-")
DATE_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


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
        if DATE_ID_RE.match(stem):
            slug = stem[len("YYYY-MM-DD-"):]
        elif "-" in stem:
            slug = stem.split("-", 1)[1]
        else:
            slug = stem
        return slug.replace("-", " ").capitalize()

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
    files = sorted(
        p for p in HANDOFFS.glob("*.md")
        if LEGACY_ID_RE.match(p.name) or DATE_ID_RE.match(p.name)
    )
    return [Thread(p) for p in files]


def next_id(threads: list[Thread]) -> str:
    """Back-compat helper some callers may still use. Prefer next_free_id()."""
    nums = [int(t.id) for t in threads if t.id.isdigit()]
    return f"{max(nums) + 1 if nums else 1:03d}"


def _git_ref_names() -> list[str]:
    """Local branches + remote-tracking branches, so allocation sees IDs claimed on
    parallel branches this working tree hasn't checked out. Degrades loudly: if git
    is unavailable or errors, fall back to working-tree-only scanning rather than
    silently allocating a number that may collide (five prior collisions -- see
    CLAUDE.md and docs/handoffs/README.md -- all came from scanning one tree only)."""
    try:
        out = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            print(f"handoffs: git ref scan failed ({out.stderr.strip()}); "
                  f"falling back to working-tree-only allocation", file=sys.stderr)
            return []
        return [r for r in out.stdout.splitlines() if r.strip() and not r.endswith("/HEAD")]
    except Exception as e:
        print(f"handoffs: git unavailable ({e}); falling back to working-tree-only allocation",
              file=sys.stderr)
        return []


def _git_tree_filenames(ref: str, subdir: str) -> list[str]:
    """Filenames (basenames) under subdir as committed on ref. Empty + a stderr note
    on any failure (ref deleted since listing, subdir absent on that ref, etc.) --
    never raises, since one bad ref shouldn't abort allocation for everyone else."""
    try:
        out = subprocess.run(
            ["git", "ls-tree", "--name-only", ref, "--", subdir],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            return []
        return [ln.rsplit("/", 1)[-1] for ln in out.stdout.splitlines() if ln.strip()]
    except Exception as e:
        print(f"handoffs: git ls-tree failed for {ref}:{subdir} ({e}); skipping this ref",
              file=sys.stderr)
        return []


def _git_show(ref: str, path: str) -> str | None:
    """Contents of path as committed on ref, or None on any failure (path absent on
    that ref, ref gone, etc.)."""
    try:
        out = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        return out.stdout if out.returncode == 0 else None
    except Exception as e:
        print(f"handoffs: git show failed for {ref}:{path} ({e}); skipping", file=sys.stderr)
        return None


def next_free_id() -> int:
    """LEGACY (W1(c), superseded by W3 -- see DATE_ID_RE comment above). Kept working
    and kept tested because it still answers one real question honestly -- 'what is the
    highest legacy NNN thread number anyone has claimed' -- but as of W3 it is NOT used
    to allocate new thread filenames. Even with the cross-branch widening below, this
    function reads a 'highest so far' view that two worktrees can each see identically
    stale at the same instant; that structural gap is exactly what W3 removes for new
    threads by not requiring a shared counter at all. Do not wire this back into
    cmd_new/ingest_pending.

    Widened (thread 079/081, FR-020 double-allocation, ADR-054 collision, 2026-07-29):
    also scans docs/handoffs/ as committed on every local + remote-tracking branch, so
    a number claimed on a parallel branch isn't reused here. Falls back to working-tree
    scan alone if git is unavailable (see _git_ref_names)."""
    nums: list[int] = []
    if HANDOFFS.exists():
        nums += [int(m.group(1)) for p in HANDOFFS.glob("*.md") if (m := re.match(r"^(\d{3})-", p.name))]
    for ref in _git_ref_names():
        for name in _git_tree_filenames(ref, "docs/handoffs"):
            if m := re.match(r"^(\d{3})-", name):
                nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def new_thread_filename(date: str, slug: str) -> pathlib.Path:
    """W3: claim docs/handoffs/{date}-{slug}[-N].md with no shared counter and no git
    ref scan. `os.O_CREAT | os.O_EXCL` makes the claim atomic within this working tree
    -- if the exact path is already taken (same date, same slug, most likely because
    this same tree already has a thread on the same subject today) the next integer
    suffix is tried instead, deterministically, until one is free. This is what 'W1'
    could never be for the old scheme: correctness here does not depend on seeing what
    another worktree is doing, because the two things that make the name (today's date
    and this thread's own subject) are already known locally, with nothing to race.

    The one case this can't disambiguate is two *separate* worktrees independently
    creating the identical date+slug with no shared filesystem between them -- there is
    no way to know about a sibling worktree's in-flight allocation without a network
    round trip, which this tool deliberately does not add. That case still can't
    silently collide the way the old scheme did: the destination path itself is the
    identifier, so both worktrees writing different content to the same path is an
    ordinary git file conflict at merge time -- loud, blocking, and forces a human/agent
    to resolve it -- not a same-number two-different-filenames collision that merges
    clean and hides until someone reads the ID: field."""
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    base = f"{date}-{slug}"
    n = 1
    while True:
        candidate = base if n == 1 else f"{base}-{n}"
        path = HANDOFFS / f"{candidate}.md"
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return path
        except FileExistsError:
            n += 1


def _rel(path: pathlib.Path) -> str:
    """Best-effort path-for-humans. Falls back to the absolute path when the given
    path isn't under ROOT (e.g. a test pointed the module at a scratch tmp_path)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "thread"


def _stamp_frontmatter(text: str, id_str: str, today: str) -> str:
    """Insert/overwrite ID: and OPENED: in a thread's frontmatter block. Refuses to
    proceed on a file with no frontmatter at all -- that is a malformed thread, not
    something to paper over with a guessed block. `id_str` is written verbatim so it
    works for both the legacy `NNN` shape and W3's `YYYY-MM-DD-slug` shape."""
    if not text.startswith("---"):
        raise SystemExit(f"handoffs sync: file has no frontmatter block, refusing to stamp it")
    _, fm, body = text.split("---", 2)
    lines = fm.strip("\n").splitlines()
    out_lines: list[str] = []
    has_id = has_opened = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("ID:"):
            out_lines.append(f"ID: {id_str}")
            has_id = True
        elif stripped.upper().startswith("OPENED:"):
            out_lines.append(f"OPENED: {today}")
            has_opened = True
        else:
            out_lines.append(line)
    if not has_id:
        out_lines.insert(0, f"ID: {id_str}")
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


def _ingest_one(src: pathlib.Path, today: str) -> pathlib.Path:
    """Allocate a single pending file to docs/handoffs/{today}-{slug}[-N].md via
    new_thread_filename() (W3) -- no nid, no counter, no collision to hard-fail on:
    new_thread_filename() itself cannot return an already-occupied path, so there is
    nothing left here that needs a defensive raise. Split out from ingest_pending() so
    the allocation-plus-stamp step is independently testable."""
    stem = src.stem
    raw_slug = stem[4:] if stem.upper().startswith("NEW-") else stem
    slug = _slugify(raw_slug)
    dest = new_thread_filename(today, slug)
    text = src.read_text(encoding="utf-8")
    dest.write_text(_stamp_frontmatter(text, dest.stem, today), encoding="utf-8")
    src.unlink()
    return dest


def ingest_pending(today: str | None = None) -> list[pathlib.Path]:
    """W3: rename every pending file to {today}-<slug>[-N].md via new_thread_filename(),
    stamp ID/OPENED. Idempotent: running with nothing pending is a no-op. Unlike the old
    W1(b), this never needs to hard-fail on a collision -- new_thread_filename() resolves
    same-day-same-slug deterministically within this working tree instead of raising."""
    today = today or datetime.date.today().isoformat()
    ingested: list[pathlib.Path] = []
    for src in _pending_new_files():
        ingested.append(_ingest_one(src, today))
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
    """W1(a)/W3: write NEW-<slug>.md with no ID: field. Nobody types a number (or a
    date -- ingest_pending() reads the system clock at allocation time, see comment on
    DATE_ID_RE), so nobody can collide on one. sync (called at the end of this command)
    allocates the real docs/handoffs/YYYY-MM-DD-slug.md filename."""
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
    max+1 from a stale read of docs/decisions.md alone.

    Widened (2026-07-29): also scans docs/decisions.md and docs/adr-drafts/ as committed
    on every local + remote-tracking branch, so an ADR number taken on an unmerged branch
    (e.g. ADR-054 on backend/mock-calibration-kickers) isn't handed out again here. This
    narrows the collision window; it does not close it -- see find_adr_collisions() for
    the hard backstop that catches what a two-sessions-allocate-before-either-pushes race
    still lets through."""
    nums: list[int] = []
    if DECISIONS_LOG.exists():
        nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", DECISIONS_LOG.read_text(encoding="utf-8"))]
    if ADR_DRAFTS.exists():
        for p in ADR_DRAFTS.glob("*.md"):
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", p.read_text(encoding="utf-8"))]
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", p.name)]
    for ref in _git_ref_names():
        text = _git_show(ref, "docs/decisions.md")
        if text:
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", text)]
        for name in _git_tree_filenames(ref, "docs/adr-drafts"):
            content = _git_show(ref, f"docs/adr-drafts/{name}")
            if content:
                nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", content)]
            nums += [int(n) for n in re.findall(r"ADR-(\d+)\b", name)]
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


ADR_HEADER = re.compile(r"^## (ADR-\d+)\s*—.*$", re.M)


def find_adr_collisions() -> list[str]:
    """Backstop for the widened adr_next(): even scanning every ref narrows the race,
    it can't close it (two sessions can each allocate before either pushes). This
    catches what got through -- the same ADR-NNN with a *different* header text on
    two branches -- so it fails loudly at `check` time instead of surviving to a merge
    unnoticed. Deliberately does not renumber anything; detection only."""
    by_num: dict[str, set[str]] = {}
    sources: list[tuple[str, str]] = []
    if DECISIONS_LOG.exists():
        sources.append(("HEAD", DECISIONS_LOG.read_text(encoding="utf-8")))
    for ref in _git_ref_names():
        text = _git_show(ref, "docs/decisions.md")
        if text:
            sources.append((ref, text))
    for label, text in sources:
        for m in ADR_HEADER.finditer(text):
            by_num.setdefault(m.group(1), set()).add(m.group(0).strip())
    problems = []
    for num in sorted(by_num, key=lambda n: int(n.split("-")[1])):
        headers = by_num[num]
        if len(headers) > 1:
            problems.append(
                f"{num} has {len(headers)} conflicting headers across branches: "
                + " | ".join(sorted(headers))
            )
    return problems


def find_thread_id_collisions() -> list[str]:
    """Same backstop shape as find_adr_collisions(), for thread IDs: a docs/handoffs/
    NNN-*.md filename claimed for different subjects on different branches.

    Legacy-only (`\\d{3}-`) on purpose. W3's YYYY-MM-DD-slug.md threads have no
    equivalent failure mode to backstop: the filename itself *is* the identifier there
    (not a separate ID: number that two different filenames could each carry), so two
    branches genuinely disagreeing about what YYYY-MM-DD-slug.md contains is an ordinary
    git same-path conflict that blocks the merge on its own -- nothing here needs to
    detect it after the fact."""
    by_id: dict[str, set[str]] = {}
    if HANDOFFS.exists():
        for p in HANDOFFS.glob("*.md"):
            if m := re.match(r"^(\d{3})-(.+)\.md$", p.name):
                by_id.setdefault(m.group(1), set()).add(m.group(2))
    for ref in _git_ref_names():
        for name in _git_tree_filenames(ref, "docs/handoffs"):
            if m := re.match(r"^(\d{3})-(.+)\.md$", name):
                by_id.setdefault(m.group(1), set()).add(m.group(2))
    problems = []
    for tid in sorted(by_id):
        slugs = by_id[tid]
        if len(slugs) > 1:
            problems.append(f"thread {tid} claimed for conflicting subjects across branches: "
                             + ", ".join(sorted(slugs)))
    return problems


# --- Pre-existing debt: legacy-scheme collisions frozen at 2026-07-30 (ADR-064) -------
# These predate W3 and are exactly the damage the old counter scheme did before this
# fix landed -- discovered by this same `check`, not created by it (verified by running
# `check` against HEAD before this change: it was already red). Policy forbids renaming
# or renumbering an existing file, so these numbers stay ambiguous forever; what this
# registry does is stop them from masking a *new* collision going forward, by naming
# exactly the pre-existing debt so `check` can tell "already known, already ambiguous"
# apart from "new, still preventable." Full account, including which files/headers are
# involved and why none can be safely reconciled without a content decision this tool
# has no authority to make: docs/known-id-collisions.md.
#
# Frozen. Never add to this set for a *new* collision -- a new collision under the
# legacy NNN scheme (still possible; old files are never renamed but nothing stops a
# human hand-typing a legacy-shaped filename) or the W3 date-slug scheme (should be
# structurally near-impossible, see DATE_ID_RE comment) must still fail `check` loudly.
# test_known_legacy_collisions_registry_is_frozen in tests/test_handoffs.py pins the
# exact contents so a silent addition doesn't slip through review.
KNOWN_LEGACY_ID_COLLISIONS = frozenset({"093", "094", "109", "110", "111", "112"})
KNOWN_LEGACY_ADR_COLLISIONS = frozenset({"ADR-054", "ADR-055"})


def _is_known_legacy_debt(problem: str) -> bool:
    """True if `problem` (one line from cmd_check's problem list) is exactly the
    pre-existing, frozen legacy-scheme debt above -- never a NEW collision, which this
    deliberately does not match (a new duplicate id/ADR number not already in the
    frozen sets above still fails `check`)."""
    for tid in KNOWN_LEGACY_ID_COLLISIONS:
        if f"duplicate ID {tid} " in problem or f"thread {tid} claimed" in problem:
            return True
    for adr in KNOWN_LEGACY_ADR_COLLISIONS:
        if problem.startswith(f"{adr} has"):
            return True
    return False


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

    problems += find_adr_collisions()
    problems += find_thread_id_collisions()

    hard_problems = [p for p in problems if not _is_known_legacy_debt(p)]
    known_debt = [p for p in problems if _is_known_legacy_debt(p)]

    if hard_problems:
        print("mailbox check FAILED:\n")
        for p in hard_problems:
            print(f"  - {p}")
        print("\nA neglected mailbox is how this system dies quietly. Fix or explicitly re-status.")
        return 1

    if known_debt:
        print(f"mailbox check OK ({len(known_debt)} known pre-existing legacy-ID collisions, "
              f"frozen 2026-07-30 / ADR-064, see docs/known-id-collisions.md -- not new):")
        for p in known_debt:
            print(f"  - {p}")

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
