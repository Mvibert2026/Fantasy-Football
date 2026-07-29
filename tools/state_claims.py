"""Claim checker: fail when a live document asserts something the repository contradicts.

Why this exists
---------------
On 2026-07-29 five separate false claims in this project's own documents were found *by
accident* while doing unrelated work, and the founder personally caught six more the same day.
The detection ratio was roughly 6:1 in his favour and did not improve. `docs/pm/CHARTER.md`
records the threshold for him stepping back as "zero interruptions **plus a detector that has
caught planted faults**". This is that detector; `tests/test_state_claims.py` is the
planted-fault proof.

Design, and what it deliberately is not
---------------------------------------
It does **not** try to understand prose. Natural-language understanding of a whole document
produces exactly the failure mode this project cannot afford: a checker that flags fifty
things nobody acts on, teaching everyone to ignore it. Instead:

* A **closed registry** (`docs/state-claims.toml`) names the handful of facts that have
  actually gone wrong, each with a machine verification and a small vocabulary of the
  phrasings that assert or deny it.
* A **closed set of live documents** is scanned. Append-only logs (`docs/status/`,
  `docs/status.md`, `docs/decisions.md`, `docs/handoffs/NNN-*.md`, `docs/founder-requests/`)
  are *never* scanned: they are records of what was believed then, and flagging a document
  for correctly recording history is the false-alarm pattern that kills a checker.
* Retracted text (`~~struck through~~`), explicitly marked history blocks
  (`<!-- state-claims: ignore-block ... -->` ... `<!-- state-claims: end-ignore -->`) and
  named per-document suppressions are masked before scanning, so a live document may narrate
  a superseded belief — as long as it marks it as superseded.

Every check here would have caught one of the five real 2026-07-29 failures. Nothing else is
in scope. The cost of registering a claim falls on whoever writes the claim, which is where
it belongs.

Checks
------
`artifact`  — a live doc asserts a registered thing is absent/not built while its file exists
              on disk; or a live doc backtick-references a code path under a real source
              directory that does not exist.
`constant`  — a version or constant quoted in prose disagrees with the source file that
              defines it.
`status`    — a named source or capability is described with a polarity ("blocked" /
              "unblocked", "cannot read" / "can read") that contradicts the registered truth.
              **With no truth registered, disagreement between two live docs is itself the
              violation** — that is the cross-document-contradiction class, and detecting it
              needs no ground truth at all.
`count`     — a count stated in prose disagrees with what is on disk. Skipped, never failed,
              when the artifact is absent: `data/` is largely gitignored and a fresh clone
              must not go red for that.
`registry`  — the registry itself has rotted: a claimed path no longer matches reality, an
              authority document is gone, or a suppression/allowance no longer matches
              anything. A suppression that outlives its reason is how this kind of tool
              quietly stops working.

Usage
-----
    python tools/state_claims.py            # human-readable report, exit 1 on violations
    python tools/state_claims.py --list     # show what is registered
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "docs" / "state-claims.toml"

# How far either side of a named alias a polarity/absence phrase must sit to count as being
# about that alias. Small on purpose: these documents wrap at ~95 columns, so this is roughly
# "the same sentence", not "the same paragraph".
WINDOW = 110

IGNORE_BLOCK = re.compile(
    r"<!--\s*state-claims:\s*ignore-block.*?-->.*?<!--\s*state-claims:\s*end-ignore\s*-->",
    re.DOTALL,
)
# Bounded on purpose: an unbalanced `~~` in a document must not blank out the rest of it.
RETRACTED = re.compile(r"~~[^~]{1,600}~~")

ABSENCE_PHRASES = [
    "absent from",
    "does not exist",
    "doesn't exist",
    "is not built",
    "are not built",
    "not built",
    "never built",
    "unbuilt",
    "is missing",
    "no such file",
    "no such screen",
    "no such tab",
    "no such view",
    "has not been built",
    "is not in the repo",
    "is not in the shipped app",
    "not shipped",
]


def _phrase_re(phrases: Iterable[str]) -> re.Pattern[str]:
    r"""Literal phrases, whitespace-flexible.

    These documents are hard-wrapped and indented inside list items, so the real text is
    "FFC remains\n   blocked". Matching a fixed single space instead of `\s+` silently misses
    exactly the claims worth catching — that bug was in the first draft of this file and it
    hid a live false claim in CURRENT-STATE.md until the flexible form found it.
    """
    parts = [r"[^\S\n]+".join(re.escape(w) for w in p.split()) for p in phrases]
    return re.compile("|".join(parts), re.IGNORECASE)


ABSENCE_RE = _phrase_re(ABSENCE_PHRASES)


@dataclass(frozen=True)
class Violation:
    kind: str
    claim_id: str
    doc: str
    line: int
    message: str

    def render(self) -> str:
        where = f"{self.doc}:{self.line}" if self.line else self.doc
        return f"[{self.kind}/{self.claim_id}] {where}\n    {self.message}"


# --------------------------------------------------------------------------------------
# text preparation
# --------------------------------------------------------------------------------------


def _mask(text: str, pattern: re.Pattern[str]) -> str:
    """Blank out every match, preserving length so offsets still map to line numbers."""
    out = list(text)
    for m in pattern.finditer(text):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def prepare(text: str, suppressions: Iterable[str] = ()) -> str:
    r"""Mask retracted / history-marked / suppressed spans, then flatten newlines.

    Flattening matters: one of the five real failures ("`CONTRACT_VERSION`\nis **1.13.0**")
    straddled a line break. Masking preserves length, so a match still reports its true line.
    """
    masked = _mask(text, IGNORE_BLOCK)
    masked = _mask(masked, RETRACTED)
    for phrase in suppressions:
        masked = _mask(masked, _phrase_re([phrase]))

    # Soft-wrap newlines become spaces so a claim can straddle a line break. Paragraph and
    # heading boundaries stay as "\n" and act as barriers: nothing here may match across them.
    # Without that barrier a section heading ("## Not built") sits inside the proximity window
    # of the first sentence under it and manufactures a false positive — which it did, on the
    # corrected fixture, before this was added.
    lines = masked.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if i == len(lines) - 1:
            break
        nxt = lines[i + 1]
        barrier = (
            not line.strip()
            or not nxt.strip()
            or line.lstrip().startswith("#")
            or nxt.lstrip().startswith("#")
        )
        out.append("\n" if barrier else " ")
    return "".join(out)


def _clip(flow: str, start: int, end: int) -> tuple[int, int]:
    """Widen [start, end) by WINDOW, stopping at the nearest paragraph/heading barrier."""
    lo = flow.rfind("\n", 0, start)
    lo = max(start - WINDOW, 0 if lo == -1 else lo + 1)
    hi = flow.find("\n", end)
    hi = min(end + WINDOW, len(flow) if hi == -1 else hi)
    return lo, hi


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# --------------------------------------------------------------------------------------
# registry + document loading
# --------------------------------------------------------------------------------------


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def live_doc_names(registry: dict) -> list[str]:
    return list(registry.get("scope", {}).get("live_docs", []))


def load_docs(registry: dict, root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in live_doc_names(registry):
        path = root / name
        if path.exists():
            out[name] = path.read_text(encoding="utf-8")
    return out


def _suppressions_for(registry: dict, doc: str) -> list[str]:
    return [e["contains"] for e in registry.get("ignore", []) if e["doc"] == doc]


def _flows(registry: dict, docs: Mapping[str, str]) -> dict[str, str]:
    return {
        name: prepare(raw, _suppressions_for(registry, name))
        for name, raw in docs.items()
    }


# --------------------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------------------


def _check_registry_health(registry: dict, root: Path, docs: Mapping[str, str]) -> list[Violation]:
    """The registry is a claim too. Keep it from rotting into a rubber stamp."""
    out: list[Violation] = []
    reg = "docs/state-claims.toml"

    for art in registry.get("artifact", []):
        real = (root / art["path"]).exists()
        if real != art["exists"]:
            out.append(
                Violation(
                    "registry", art["id"], reg, 0,
                    f"registry says {art['path']} exists={art['exists']}; on disk it is "
                    f"exists={real}. Update the registry and whatever prose depends on it.",
                )
            )

    for claim in registry.get("status", []):
        authority = claim.get("authority")
        if authority and not (root / authority).exists():
            out.append(
                Violation(
                    "registry", claim["id"], reg, 0,
                    f"authority document {authority} is gone — the registered truth for this "
                    f"claim has no evidence behind it any more.",
                )
            )

    for entry in registry.get("ignore", []):
        target = root / entry["doc"]
        if not target.exists():
            out.append(
                Violation("registry", entry["id"], reg, 0,
                          f"suppression targets {entry['doc']}, which does not exist.")
            )
            continue
        if entry["contains"].lower() not in target.read_text(encoding="utf-8").lower():
            out.append(
                Violation(
                    "registry", entry["id"], reg, 0,
                    f"suppression for {entry['doc']} matches nothing any more "
                    f"({entry['contains']!r}). A stale suppression hides real faults — "
                    f"delete it.",
                )
            )

    all_text = " ".join(docs.values())
    for allowed in registry.get("paths", {}).get("allow", []):
        ref = allowed["path"]
        if (root / ref).exists():
            out.append(
                Violation(
                    "registry", "path-allow", reg, 0,
                    f"`{ref}` is allow-listed as a path that legitimately does not exist, but "
                    f"it exists now. Remove the allowance.",
                )
            )
        elif ref not in all_text:
            out.append(
                Violation(
                    "registry", "path-allow", reg, 0,
                    f"`{ref}` is allow-listed but no live document mentions it any more. "
                    f"Remove the allowance.",
                )
            )
    return out


def _check_artifacts(registry: dict, root: Path, docs: Mapping[str, str],
                     flows: Mapping[str, str]) -> list[Violation]:
    """Class 1: "X is absent / not built" while X's file plainly exists.

    Only this direction is inferred from prose. The inverse — a document claiming something
    exists that does not — is handled exactly by `_check_path_references`; inferring a
    *presence* claim from free prose is not exact, and guessing there is how a checker
    starts producing noise.
    """
    out: list[Violation] = []
    for art in registry.get("artifact", []):
        if not art["exists"]:
            continue  # nothing to contradict: the thing really is absent
        alias_re = _phrase_re(list(art.get("aliases", [])) + [art["path"]])
        for name, raw in docs.items():
            flow = flows[name]
            for m in alias_re.finditer(flow):
                lo, hi = _clip(flow, m.start(), m.end())
                hit = ABSENCE_RE.search(flow[lo:hi])
                if hit:
                    out.append(
                        Violation(
                            "artifact", art["id"], name, line_of(raw, m.start()),
                            f"says {' '.join(m.group(0).split())!r} is "
                            f"{' '.join(hit.group(0).split())!r}, but {art['path']} exists in "
                            f"the working tree.",
                        )
                    )
    return out


PATH_TOKEN = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9_]{1,5})`")


def _check_path_references(registry: dict, root: Path, docs: Mapping[str, str],
                           flows: Mapping[str, str]) -> list[Violation]:
    """Class 1, inverse: a live doc names a code path that is gone.

    Restricted to backticked tokens under directories that really exist and that these
    documents cite constantly. Anything outside those prefixes is not checked — docs
    legitimately name planned, external, and other-branch paths, and guessing which is which
    is the road to false alarms. Genuine exceptions go in `[[paths.allow]]` with a reason,
    and are themselves checked for staleness above.
    """
    cfg = registry.get("paths", {})
    prefixes = tuple(cfg.get("prefixes", []))
    if not prefixes:
        return []
    allow = {a["path"] for a in cfg.get("allow", [])}
    out: list[Violation] = []
    for name, raw in docs.items():
        for m in PATH_TOKEN.finditer(flows[name]):
            ref = m.group(1)
            if not ref.startswith(prefixes) or ref in allow or (root / ref).exists():
                continue
            out.append(
                Violation(
                    "artifact", "path-reference", name, line_of(raw, m.start()),
                    f"references `{ref}`, which does not exist. Either it moved and the prose "
                    f"is stale, or it was never created.",
                )
            )
    return out


def _extract_constant(root: Path, spec: dict) -> str | None:
    src = root / spec["source"]
    if not src.exists():
        return None
    m = re.search(spec["extract"], src.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _check_constants(registry: dict, root: Path, docs: Mapping[str, str],
                     flows: Mapping[str, str]) -> list[Violation]:
    """Class 2: a version/constant quoted in prose against the source that defines it."""
    out: list[Violation] = []
    for spec in registry.get("constant", []):
        actual = _extract_constant(root, spec)
        if actual is None:
            out.append(
                Violation(
                    "registry", spec["id"], "docs/state-claims.toml", 0,
                    f"cannot read {spec['id']} out of {spec['source']} with the registered "
                    f"pattern — the constant moved or was renamed.",
                )
            )
            continue
        patterns = [re.compile(p, re.IGNORECASE) for p in spec["prose"]]
        for name, raw in docs.items():
            for pat in patterns:
                for m in pat.finditer(flows[name]):
                    if m.group(1) != actual:
                        out.append(
                            Violation(
                                "constant", spec["id"], name, line_of(raw, m.start()),
                                f"states {spec['id']} is {m.group(1)}; {spec['source']} says "
                                f"{actual}.",
                            )
                        )
    return out


def _check_statuses(registry: dict, root: Path, docs: Mapping[str, str],
                    flows: Mapping[str, str]) -> list[Violation]:
    """Class 3 (source/capability status) and class 5 (cross-document contradiction).

    With a registered `truth`, any live doc asserting the other polarity is a violation.
    Without one, two live docs asserting opposite polarities is itself the violation — no
    ground truth required, which is the only honest way to flag a fact nobody has settled.
    """
    out: list[Violation] = []
    for claim in registry.get("status", []):
        alias_re = _phrase_re(claim["aliases"])
        vocab = {pol: _phrase_re(ph) for pol, ph in claim["vocab"].items()}
        truth = claim.get("truth")
        found: dict[str, list[tuple[str, int, str]]] = {pol: [] for pol in vocab}
        for name, raw in docs.items():
            flow = flows[name]
            for m in alias_re.finditer(flow):
                lo, hi = _clip(flow, m.start(), m.end())
                context = flow[lo:hi]
                for pol, pat in vocab.items():
                    hit = pat.search(context)
                    if not hit:
                        continue
                    entry = (name, line_of(raw, m.start()), " ".join(hit.group(0).split()))
                    if entry not in found[pol]:
                        found[pol].append(entry)
        if truth:
            for pol, hits in found.items():
                if pol == truth:
                    continue
                for name, line, phrase in hits:
                    out.append(
                        Violation(
                            "status", claim["id"], name, line,
                            f"describes {claim['aliases'][0]} as {phrase!r} (polarity "
                            f"{pol!r}); the registered truth is {truth!r}, per "
                            f"{claim.get('authority', 'the registry')}.",
                        )
                    )
        else:
            present = {p: h for p, h in found.items() if h}
            if len(present) > 1:
                detail = "; ".join(
                    f"{p} at " + ", ".join(f"{d}:{ln}" for d, ln, _ in hits)
                    for p, hits in present.items()
                )
                name, line, _ = next(iter(present.values()))[0]
                out.append(
                    Violation(
                        "status", claim["id"], name, line,
                        f"{claim['aliases'][0]} is asserted two opposite ways across live "
                        f"documents and no truth is registered — {detail}. Settle it and "
                        f"record `truth` in docs/state-claims.toml.",
                    )
                )
    return out


def _measure(root: Path, spec: dict) -> int | None:
    path = root / spec["path"]
    if not path.exists():
        return None
    kind = spec["measure"]
    if kind == "json_array_len":
        return len(json.loads(path.read_text(encoding="utf-8"))[spec["key"]])
    if kind == "glob_count":
        return len(list(path.glob(spec["pattern"])))
    raise ValueError(f"unknown measure {kind!r}")


def _check_counts(registry: dict, root: Path, docs: Mapping[str, str],
                  flows: Mapping[str, str]) -> list[Violation]:
    """Class 4: a count in prose against what is on disk."""
    out: list[Violation] = []
    for spec in registry.get("count", []):
        actual = _measure(root, spec)
        if actual is None:
            continue  # artifact absent in a fresh clone; not a documentation fault
        patterns = [re.compile(p, re.IGNORECASE) for p in spec["prose"]]
        for name, raw in docs.items():
            for pat in patterns:
                for m in pat.finditer(flows[name]):
                    if int(m.group(1)) != actual:
                        out.append(
                            Violation(
                                "count", spec["id"], name, line_of(raw, m.start()),
                                f"states {m.group(1)} where {spec['path']} currently holds "
                                f"{actual} ({spec['id']}).",
                            )
                        )
    return out


def check(registry: dict, root: Path = REPO_ROOT,
          docs: Mapping[str, str] | None = None) -> list[Violation]:
    """Run every check. `docs` maps document name -> raw text; omit to read the live set.

    Passing `docs` explicitly is what lets `tests/test_state_claims.py` run the real registry
    against planted-fault fixtures while file-existence checks still resolve against the real
    working tree.
    """
    doc_map = dict(docs) if docs is not None else load_docs(registry, root)
    flows = _flows(registry, doc_map)
    violations: list[Violation] = []
    violations += _check_registry_health(registry, root, doc_map)
    violations += _check_artifacts(registry, root, doc_map, flows)
    violations += _check_path_references(registry, root, doc_map, flows)
    violations += _check_constants(registry, root, doc_map, flows)
    violations += _check_statuses(registry, root, doc_map, flows)
    violations += _check_counts(registry, root, doc_map, flows)

    # Two aliases of one claim can land on the same line ("`design` cannot read this repo.
    # A thread addressed to `design` ..."). One line, one violation.
    seen: set[tuple[str, str, str, int]] = set()
    unique: list[Violation] = []
    for v in violations:
        key = (v.kind, v.claim_id, v.doc, v.line)
        if key not in seen:
            seen.add(key)
            unique.append(v)
    return unique


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--list", action="store_true", help="show what is registered and exit")
    args = ap.parse_args(argv)

    registry = load_registry(args.registry)
    if args.list:
        names = live_doc_names(registry)
        print(f"live documents scanned ({len(names)}):")
        for n in names:
            print(f"  {n}")
        for section in ("artifact", "constant", "status", "count", "ignore"):
            entries = registry.get(section, [])
            print(f"\n{section} claims ({len(entries)}):")
            for e in entries:
                print(f"  {e.get('id', e.get('doc'))}")
        return 0

    violations = check(registry, args.root)
    if not violations:
        print(
            f"state-claims: OK — {len(live_doc_names(registry))} live documents, "
            f"no contradicted claims."
        )
        return 0
    print(f"state-claims: {len(violations)} contradicted claim(s)\n")
    for v in violations:
        print(v.render())
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
