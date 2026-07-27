"""
Pre-registration, the persistent test counter, and FDR correction (Task 7).

THE PROBLEM THIS SOLVES. statistical-guardrails.md §3 requires that the
multiple-comparisons correction apply across every test actually run, not
across whichever subset looked interesting afterwards. That is unenforceable by
memory: the tests that get forgotten are exactly the ones that failed, and
forgetting them is what turns a 1-in-20 fluke into a "finding".

So three mechanisms:

1. PRE-REGISTRATION FILES. One markdown file per factor test in
   docs/preregistration/, stating the hypothesis, the exact metric, and the
   threshold that would count as confirmation -- written BEFORE the test runs.
   `require_preregistration()` refuses to execute a test with no file.
   The point is to make "we predicted this" checkable rather than remembered.

2. A PERSISTENT, APPEND-ONLY RUN LOG. Every executed test appends to
   docs/preregistration/test_run_log.jsonl. That file is tracked in git
   deliberately: the count must survive a database rebuild, because a counter
   living in a gitignored .db would silently reset and the FDR denominator
   would quietly shrink to whatever was run most recently. Which is precisely
   the failure mode being defended against.

3. BENJAMINI-HOCHBERG over the true total.

`preregistration_id` is the join key across all three.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

PREREG_DIR = Path(__file__).resolve().parent.parent / "docs" / "preregistration"
RUN_LOG_PATH = PREREG_DIR / "test_run_log.jsonl"

REQUIRED_FIELDS = ("id", "title", "hypothesis", "metric", "confirmation_threshold", "status")


class PreRegistrationMissing(Exception):
    """Raised when a test tries to run without a pre-registration file."""


class PreRegistrationInvalid(Exception):
    """Raised when a pre-registration file is missing required fields."""


@dataclass(frozen=True)
class PreRegistration:
    id: str
    title: str
    hypothesis: str
    metric: str
    confirmation_threshold: str
    status: str
    path: Path
    fields: Dict[str, str] = field(default_factory=dict)


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Parse a leading `---` delimited key: value block.

    Hand-rolled rather than pulling in a YAML dependency: the format is a flat
    key/value map and the values are prose.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4 :]
    fields: Dict[str, str] = {}
    current_key: Optional[str] = None
    for line in block.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            fields[current_key] = m.group(2).strip()
        elif current_key:  # continuation line
            fields[current_key] = (fields[current_key] + " " + line.strip()).strip()
    return fields, body


def load_preregistration(test_id: str, directory: Path = PREREG_DIR) -> PreRegistration:
    """Load and validate the pre-registration for `test_id`.

    Raises rather than returning None: a missing pre-registration must stop the
    test, not degrade to a warning that gets scrolled past.
    """
    if not directory.exists():
        raise PreRegistrationMissing(
            f"no pre-registration directory at {directory}; create it and add {test_id}.md "
            "before running any factor test"
        )
    matches = sorted(directory.glob(f"{test_id}*.md"))
    if not matches:
        raise PreRegistrationMissing(
            f"no pre-registration file for test id {test_id!r} in {directory}. "
            "Write the hypothesis, metric and confirmation threshold BEFORE running the "
            "test (statistical-guardrails.md §3.4)."
        )
    path = matches[0]
    fields, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise PreRegistrationInvalid(
            f"pre-registration {path.name} is missing required field(s): {missing}"
        )
    return PreRegistration(
        id=fields["id"],
        title=fields["title"],
        hypothesis=fields["hypothesis"],
        metric=fields["metric"],
        confirmation_threshold=fields["confirmation_threshold"],
        status=fields["status"],
        path=path,
        fields=fields,
    )


def require_preregistration(test_id: str, directory: Path = PREREG_DIR) -> PreRegistration:
    """Guard to call at the top of any factor test."""
    return load_preregistration(test_id, directory)


# ------------------------------------------------------------------ run log


def record_test_run(
    test_id: str,
    metric: str,
    p_value: Optional[float],
    effect_size: Optional[float],
    seasons_used: Sequence[int],
    notes: str = "",
    log_path: Path = RUN_LOG_PATH,
) -> dict:
    """Append one executed test to the permanent run log.

    Call this for EVERY run, including ones that produced nothing. A test that
    is run and not recorded shrinks the FDR denominator and inflates every
    surviving result.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "test_id": test_id,
        "metric": metric,
        "p_value": p_value,
        "effect_size": effect_size,
        "seasons_used": list(seasons_used),
        "notes": notes,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def all_test_runs(log_path: Path = RUN_LOG_PATH) -> List[dict]:
    if not log_path.exists():
        return []
    with log_path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def total_tests_run(log_path: Path = RUN_LOG_PATH) -> int:
    return len(all_test_runs(log_path))


# ------------------------------------------------------------------ FDR


@dataclass(frozen=True)
class FDRResult:
    p_values: List[float]
    adjusted: List[float]
    rejected: List[bool]
    alpha: float
    n_tested: int
    n_total_considered: int
    note: str


def benjamini_hochberg(
    p_values: Sequence[float],
    alpha: float = 0.05,
    n_total: Optional[int] = None,
) -> FDRResult:
    """Benjamini-Hochberg FDR correction.

    `n_total` lets the correction apply across the TRUE number of tests run
    (from the persistent log) even when only a subset is being reported here.
    Passing the reported subset alone is the error this argument exists to
    prevent: correcting 5 hand-picked p-values as though 5 tests were run, when
    30 were, understates the false-discovery rate roughly six-fold.
    """
    p = np.asarray(list(p_values), dtype=float)
    m_reported = len(p)
    if m_reported == 0:
        return FDRResult([], [], [], alpha, 0, n_total or 0, "no p-values supplied")
    m = int(n_total) if n_total is not None else m_reported
    if m < m_reported:
        raise ValueError(
            f"n_total ({m}) is smaller than the number of p-values supplied ({m_reported})"
        )

    order = np.argsort(p)
    ranked = p[order]
    ranks = np.arange(1, m_reported + 1)
    adj_sorted = np.minimum.accumulate((ranked * m / ranks)[::-1])[::-1]
    adj_sorted = np.clip(adj_sorted, 0.0, 1.0)

    adjusted = np.empty_like(adj_sorted)
    adjusted[order] = adj_sorted
    rejected = adjusted <= alpha

    note = ""
    if n_total is not None and n_total > m_reported:
        note = (
            f"corrected across the full run log ({m} tests), not just the "
            f"{m_reported} reported here"
        )
    return FDRResult(
        p_values=[float(x) for x in p],
        adjusted=[float(x) for x in adjusted],
        rejected=[bool(x) for x in rejected],
        alpha=alpha,
        n_tested=m_reported,
        n_total_considered=m,
        note=note,
    )


def correct_against_full_log(
    p_values: Sequence[float], alpha: float = 0.05, log_path: Path = RUN_LOG_PATH
) -> FDRResult:
    """BH correction whose denominator is the persistent run-log total."""
    total = max(total_tests_run(log_path), len(p_values))
    return benjamini_hochberg(p_values, alpha=alpha, n_total=total)


# =====================================================================
# ADR-C: the pre-registration CONVENTION (format, enforcement, amendments)
#
# Everything above this line is the original mechanism (Task 7): one flat
# front-matter file per test, a run log, BH. ADR-C
# (docs/adr-drafts/ADR-C-preregistration.md, thread 020) extends that same
# docs/preregistration/ tree rather than replacing it: PR-001..003 keep their
# filenames and numbering, the two existing .jsonl logs keep their schemas
# (extended, not replaced), and the new PR-004+ format adds nine typed
# front-matter fields, a family manifest that fixes the BH denominator, and an
# amendment mechanism whose one rule with teeth is: an amendment made after
# seeing data ("data_seen: true") irreversibly demotes the registration to
# `mode: exploratory`, with no override flag and no judgment call available to
# the person with the incentive to relitigate it.
#
# Scope note (thread 020): the ADR also specifies a `prereg` CLI (scaffolding,
# `prereg check` as a pre-commit hook) and a full retrofit of PR-001..003 into
# this format. Both are deferred -- this session is restricted to
# src/preregistration.py and the holdout guard (src/holdout.py) while other
# agents work other files in parallel. The retrofit and CLI are tracked as
# follow-up in docs/decisions.md / the thread-020 reply, not silently dropped.
# =====================================================================

FAMILIES_DIR = PREREG_DIR / "families"
UNSEAL_LOG_PATH = PREREG_DIR / "UNSEAL_LOG.md"

FORBIDDEN_EXPLORATORY_KEYS = ("p_value", "ci_lower", "ci_upper", "significant")

# The one rule with teeth (ADR-C "Amendments"): a family status value meaning
# "this family unsealed the 2025 holdout and is closed forever" -- distinct
# from an ordinary "closed" family, which DOES reopen when a new confirmatory
# test is added to it. Nothing reopens this one.
FAMILY_STATUS_CLOSED_UNSEALED = "closed-unsealed"


class RegistrationMissing(Exception):
    """No PR-file found for the given id (ADR-C format)."""


class RegistrationInvalid(Exception):
    """A PR-file exists but violates the ADR-C required-field or CI rules."""


class FamilyMissing(Exception):
    """No family manifest found for the given family id."""


class FamilyClosed(Exception):
    """The family is closed-unsealed (permanent) and may not accept a new test."""


# --------------------------------------------------------- tiny flow parser
#
# Hand-rolled rather than a YAML dependency (none is installed in this env,
# and the ADR's own reasoning for hand-rolling the original parser --
# "the format is a flat key/value map and the values are prose" -- extends
# here: the nested values this format needs (data_scope, frozen, one
# amendment) are deliberately restricted to single-line YAML *flow* style
# (`{k: v, k2: [a, b]}`), so a small recursive-descent-free parser suffices
# and there is no multi-line YAML block-mapping case to get subtly wrong.


def _split_top_level(s: str) -> List[str]:
    """Split on commas that are not nested inside [], {}, or quotes."""
    parts: List[str] = []
    depth = 0
    in_quotes = False
    cur = ""
    for ch in s:
        if ch == '"' and (not cur or cur[-1] != "\\"):
            in_quotes = not in_quotes
        if not in_quotes:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
        if ch == "," and depth == 0 and not in_quotes:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _parse_flow(value: str):
    """Parse one YAML-flow scalar/list/dict: `{...}`, `[...]`, bool/int/str."""
    value = value.strip()
    if value.startswith("{") and value.endswith("}"):
        d: Dict = {}
        for part in _split_top_level(value[1:-1]):
            if ":" not in part:
                continue
            k, v = part.split(":", 1)
            d[k.strip()] = _parse_flow(v)
        return d
    if value.startswith("[") and value.endswith("]"):
        return [_parse_flow(x) for x in _split_top_level(value[1:-1]) if x.strip()]
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    low = value.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _parse_v2_frontmatter(text: str) -> Tuple[Dict, str]:
    """Parse the ADR-C front matter: flat scalars, prose continuation lines
    (joined, same convention as the original parser), single-line flow dicts
    for `data_scope:`/`frozen:`, and a block list of single-line flow dicts
    for `amendments:`.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4 :]
    lines = block.splitlines()
    fields: Dict = {}
    i = 0
    n = len(lines)
    current_key: Optional[str] = None
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith(" ") and current_key == "amendments":
            m = re.match(r"^\s*-\s+(\{.*\})\s*$", line)
            if m:
                fields.setdefault("amendments", []).append(_parse_flow(m.group(1)))
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            key, rest = m.group(1), m.group(2).strip()
            current_key = key
            if key == "amendments" and not rest:
                fields.setdefault("amendments", [])
            elif rest.startswith("{") or rest.startswith("["):
                fields[key] = _parse_flow(rest)
            else:
                fields[key] = rest
        elif current_key and current_key != "amendments":
            # prose continuation line
            prev = fields.get(current_key, "")
            fields[current_key] = (str(prev) + " " + line.strip()).strip()
        i += 1
    return fields, body


V2_CONFIRMATORY_FIELDS = (
    "id",
    "test_registry_id",
    "family",
    "mode",
    "question",
    "metric",
    "threshold",
    "data_scope",
    "frozen",
)
V2_EXPLORATORY_FIELDS = ("id", "mode", "question", "frozen")


@dataclass(frozen=True)
class Registration:
    id: str
    mode: str  # declared mode, before any data_seen demotion
    question: str
    test_registry_id: Optional[str]
    family: Optional[str]
    metric: Optional[str]
    threshold: Optional[str]
    data_scope: Dict
    frozen: Dict
    secondary: Optional[str]
    resampling_unit: str
    power_note: Optional[str]
    amendments: List[Dict]
    path: Path
    raw_fields: Dict = field(default_factory=dict)

    @property
    def effective_mode(self) -> str:
        """mode after the one irreversible rule: any `data_seen: true`
        amendment demotes the registration to exploratory, permanently,
        regardless of what the front matter still says `mode:` is."""
        if any(a.get("data_seen") is True for a in self.amendments):
            return "exploratory"
        return self.mode

    @property
    def is_confirmatory(self) -> bool:
        return self.effective_mode == "confirmatory"


def _find_pr_file(prereg_id: str, directory: Path) -> Path:
    if not directory.exists():
        raise RegistrationMissing(
            f"no pre-registration directory at {directory}; run `prereg new` (or write "
            f"{prereg_id}.md by hand) before running any confirmatory test."
        )
    matches = sorted(directory.glob(f"{prereg_id}*.md"))
    if not matches:
        raise RegistrationMissing(
            f"no ADR-C registration for {prereg_id!r} in {directory}. A result without a "
            f"matching PR- id and content hash is not a finding (ADR-C pre-committed rule)."
        )
    return matches[0]


def load_registration(prereg_id: str, directory: Path = PREREG_DIR) -> Registration:
    """Load and validate an ADR-C (PR-004+ format) registration.

    Raises RegistrationMissing/RegistrationInvalid rather than returning None
    or a best-effort partial object -- same reasoning as the original
    `load_preregistration`: a missing or malformed registration must stop the
    analysis, not degrade to a warning.
    """
    path = _find_pr_file(prereg_id, directory)
    fields, _ = _parse_v2_frontmatter(path.read_text(encoding="utf-8"))
    mode = fields.get("mode", "")
    if mode not in ("confirmatory", "exploratory"):
        raise RegistrationInvalid(
            f"{path.name}: `mode` must be 'confirmatory' or 'exploratory', got {mode!r}"
        )
    required = V2_CONFIRMATORY_FIELDS if mode == "confirmatory" else V2_EXPLORATORY_FIELDS
    missing = [f for f in required if not fields.get(f)]
    if missing:
        raise RegistrationInvalid(
            f"{path.name} ({mode}) is missing required field(s): {missing}"
        )
    resampling_unit = fields.get("resampling_unit") or ("season" if mode == "confirmatory" else "")
    power_note = fields.get("power_note")
    if mode == "confirmatory" and resampling_unit != "season" and not power_note:
        raise RegistrationInvalid(
            f"{path.name}: resampling_unit={resampling_unit!r} requires a non-empty "
            f"power_note (the default of 'season' is the guardrail; deviating from it "
            f"must be justified in writing, not silently)."
        )
    amendments = fields.get("amendments") or []
    return Registration(
        id=fields["id"],
        mode=mode,
        question=fields["question"],
        test_registry_id=fields.get("test_registry_id"),
        family=fields.get("family"),
        metric=fields.get("metric"),
        threshold=fields.get("threshold"),
        data_scope=fields.get("data_scope") or {},
        frozen=fields.get("frozen") or {},
        secondary=fields.get("secondary"),
        resampling_unit=resampling_unit,
        power_note=power_note,
        amendments=amendments,
        path=path,
        raw_fields=fields,
    )


def require_confirmatory(prereg_id: str, directory: Path = PREREG_DIR) -> Registration:
    """The entrypoint guard: 'analysis entrypoints refuse to run without
    --prereg PR-...' (ADR-C). Call this at the top of any confirmatory
    analysis. Raises if the registration is missing, invalid, or has been
    demoted to exploratory (by declaration or by a data_seen amendment)."""
    reg = load_registration(prereg_id, directory=directory)
    if not reg.is_confirmatory:
        raise RegistrationInvalid(
            f"{prereg_id} is not confirmatory (effective_mode={reg.effective_mode!r}). "
            f"A demoted or exploratory registration may not gate a confirmatory run; "
            f"register a new PR- id instead of reusing this one."
        )
    return reg


def validate_exploratory_artifact(mode: str, result: Dict) -> None:
    """CI enforces: an exploratory result artifact may never carry a
    p-value, a CI, or a significance flag (ADR-C). Point estimates and plots
    only -- exploratory tests generate hypotheses, they do not confirm them."""
    if mode != "exploratory":
        return
    present = [k for k in FORBIDDEN_EXPLORATORY_KEYS if k in result]
    if present:
        raise RegistrationInvalid(
            f"exploratory result artifact carries forbidden key(s) {present}. "
            f"Exploratory mode may report point estimates and plots only."
        )


# ------------------------------------------------------------- content hash


def _redact_content_hash(text: str) -> str:
    """Blank the `content_hash` value inside a flow dict so the hash is
    computed over everything else -- a hash that includes itself cannot
    ever match."""
    return re.sub(r"(content_hash:\s*)[^,}\s]+", r"\1REDACTED", text)


def compute_content_hash(path: Path) -> str:
    text = _redact_content_hash(path.read_text(encoding="utf-8"))
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_content_hash(reg: Registration) -> bool:
    """True iff the file's current hash matches the hash pinned at
    registration (or, if amendments exist, the hash pinned by the most
    recent amendment) -- i.e. no silent edit since the last recorded event."""
    expected = reg.frozen.get("content_hash")
    if reg.amendments:
        expected = reg.amendments[-1].get("new_content_hash", expected)
    if not expected:
        return False
    return compute_content_hash(reg.path) == expected


def check_registration(prereg_id: str, directory: Path = PREREG_DIR) -> List[str]:
    """`prereg check` equivalent: returns a list of violations (empty = clean).
    Mismatch without a matching new amendment is the core one -- git history
    alone is insufficient because a silent edit is a valid commit and nobody
    re-reads history (ADR-C)."""
    violations: List[str] = []
    reg = load_registration(prereg_id, directory=directory)
    if not verify_content_hash(reg):
        violations.append(
            f"{prereg_id}: content hash mismatch with no matching amendment recorded -- "
            f"the file changed since it was frozen (or since its last amendment) without "
            f"an `amendments:` entry."
        )
    for a in reg.amendments:
        if a.get("data_seen") and reg.mode != "exploratory":
            violations.append(
                f"{prereg_id}: has a data_seen=true amendment but `mode:` in the file "
                f"still reads {reg.mode!r}; record_amendment() should have rewritten it."
            )
    return violations


# ------------------------------------------------------------- amendments


def record_amendment(
    prereg_id: str,
    fields_changed: Sequence[str],
    reason: str,
    data_seen: bool,
    directory: Path = PREREG_DIR,
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
) -> Registration:
    """Append a visible amendment to a registration file and rewrite its
    `mode:` to exploratory if `data_seen` is true.

    This is the one rule with teeth (ADR-C): there is no override flag and no
    exception path for `data_seen=True`. The whole point is to make amending
    after a peek costly in exactly the way that keeps it honest, and to make
    that cost automatic rather than a judgment call made by the person with
    the incentive to call the peek harmless.
    """
    if not reason or not reason.strip():
        raise ValueError("record_amendment requires a non-empty reason for the audit trail")
    path = _find_pr_file(prereg_id, directory)
    reg = load_registration(prereg_id, directory=directory)

    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    block = text[3:end]
    body = text[end + 4 :]

    if data_seen and reg.mode != "exploratory":
        block = re.sub(r"(?m)^mode:\s*.*$", "mode: exploratory", block)

    amendment_line = "  - {at: %s, fields_changed: [%s], reason: \"%s\", data_seen: %s}" % (
        dt.datetime.now(dt.timezone.utc).isoformat(),
        ", ".join(fields_changed),
        reason.replace('"', "'"),
        "true" if data_seen else "false",
    )
    # new_content_hash is appended to the SAME line after this text is
    # written once, then the file is rehashed and the placeholder replaced --
    # a hash that includes itself can never match, so it is computed in two
    # passes: write with a placeholder, hash, rewrite with the real value.
    amendment_line_with_placeholder = amendment_line[:-1] + ", new_content_hash: PENDING}"

    if re.search(r"(?m)^amendments:\s*$", block):
        block = re.sub(
            r"(?m)^(amendments:\s*)$", r"\1\n" + amendment_line_with_placeholder, block
        )
    elif "amendments:" in block:
        block = block.rstrip("\n") + "\n" + amendment_line_with_placeholder
    else:
        block = block.rstrip("\n") + "\namendments:\n" + amendment_line_with_placeholder

    path.write_text("---" + block + "\n---" + body, encoding="utf-8")
    new_hash = compute_content_hash(path)
    final_text = path.read_text(encoding="utf-8").replace("PENDING}", f"{new_hash}}}")
    path.write_text(final_text, encoding="utf-8")

    return load_registration(prereg_id, directory=directory)


# ------------------------------------------------------------- families
#
# "The denominator is fixed at the family manifest, not at analysis time."
# One YAML-flow file per family: `id`, `m` (planned confirmatory-test count),
# `status` (open | closed | closed-unsealed). BH is applied within family over
# the declared `m`.


@dataclass(frozen=True)
class Family:
    id: str
    m: int
    status: str
    path: Path


def _family_path(family_id: str, directory: Path) -> Path:
    return directory / f"{family_id}.yaml"


def _write_family(path: Path, family_id: str, m: int, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"id: {family_id}\nm: {m}\nstatus: {status}\n", encoding="utf-8")


def load_family(family_id: str, directory: Path = FAMILIES_DIR) -> Family:
    path = _family_path(family_id, directory)
    if not path.exists():
        raise FamilyMissing(
            f"no family manifest for {family_id!r} at {path}; a registration's `family:` "
            f"field must name a family that exists (ADR-C)."
        )
    fields, _ = _parse_v2_frontmatter("---\n" + path.read_text(encoding="utf-8") + "\n---\n")
    return Family(id=fields["id"], m=int(fields["m"]), status=fields["status"], path=path)


def open_family(family_id: str, m: int, directory: Path = FAMILIES_DIR) -> Family:
    """Declare a new family with its planned confirmatory-test count `m`,
    BEFORE any of its tests run -- the count is written down, not
    reconstructed afterward."""
    path = _family_path(family_id, directory)
    if path.exists():
        raise RegistrationInvalid(f"family {family_id!r} already exists at {path}")
    _write_family(path, family_id, m, "open")
    return load_family(family_id, directory=directory)


def register_confirmatory_test(family_id: str, directory: Path = FAMILIES_DIR) -> Family:
    """Adding a confirmatory test to a family increments its `m`. Adding one
    to a `closed` family reopens it (every prior BH adjustment in the family
    must then be recomputed and republished -- a manual follow-up this
    function does not itself perform, only makes necessary and visible).

    A `closed-unsealed` family (the 2025 holdout was read under it) never
    reopens -- "one look is one look" -- and this raises FamilyClosed."""
    family = load_family(family_id, directory=directory)
    if family.status == FAMILY_STATUS_CLOSED_UNSEALED:
        raise FamilyClosed(
            f"family {family_id!r} unsealed the holdout and is closed permanently -- "
            f"no further confirmatory tests, no amendments, no re-runs (ADR-C)."
        )
    new_status = "open"
    _write_family(family.path, family.id, family.m + 1, new_status)
    return load_family(family_id, directory=directory)


def close_family_after_unseal(family_id: str, directory: Path = FAMILIES_DIR) -> Family:
    """Mark a family permanently closed after it unseals the 2025 holdout.
    Called from the holdout guard's unseal path (src/holdout.py), never by
    hand -- this is what makes 'one look is one look' mechanical."""
    family = load_family(family_id, directory=directory)
    _write_family(family.path, family.id, family.m, FAMILY_STATUS_CLOSED_UNSEALED)
    return load_family(family_id, directory=directory)


# ------------------------------------------------------------- unseal log


def unseal_is_logged(prereg_id: str, log_path: Path = UNSEAL_LOG_PATH) -> bool:
    """Whether `prereg_id` has a recorded, signed unseal entry. Checked by
    the holdout guard (src/holdout.py) as defense-in-depth on top of the
    registration's own `holdout_unsealed` flag -- the flag alone is just a
    front-matter value anyone could flip; the log entry is the audit trail."""
    if not log_path.exists():
        return False
    return prereg_id in log_path.read_text(encoding="utf-8")


def append_unseal_log(
    prereg_id: str,
    family: str,
    reason: str,
    approver: str,
    log_path: Path = UNSEAL_LOG_PATH,
) -> None:
    """Append a signed, one-shot unseal event. Never called automatically --
    unsealing is a human decision with a named approver, not a side effect
    of running an analysis."""
    if not reason or not reason.strip():
        raise ValueError("append_unseal_log requires a non-empty reason")
    if not approver or not approver.strip():
        raise ValueError("append_unseal_log requires a named approver")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not log_path.exists()
    with log_path.open("a", encoding="utf-8") as f:
        if is_new:
            f.write("# Unseal log\n\nAppend-only. One line per holdout unseal event.\n\n")
        f.write(
            f"- {dt.datetime.now(dt.timezone.utc).isoformat()} | {prereg_id} | "
            f"family={family} | approver={approver} | {reason}\n"
        )
