"""Generate the CURRENT-STATE.md "Build state" table from direct, measured commands.

Replaces manual re-derivation of this table by an agent every session. Prints a markdown table
to stdout; paste/replace the "## Build state" section in docs/CURRENT-STATE.md with it (still a
manual paste — this does not edit the doc in place, to keep the blast radius small and the tool
trivially auditable).

Usage:
    python tools/state.py            # skip test suites (fast: git/contract/file counts only)
    python tools/state.py --tests    # also run backend + frontend test suites (slow: ~4 min)

Backend tests use the project's conda interpreter, not whatever `python`/`py` resolve to on PATH.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PYTHON = r"C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe"


def run(cmd, cwd=REPO_ROOT, timeout=600):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str), timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr


def git_head():
    code, out, err = run(["git", "rev-parse", "HEAD"])
    if code != 0:
        return f"ERROR: {err.strip()}"
    return out.strip()


def contract_version():
    path = REPO_ROOT / "src" / "export_contract.py"
    if not path.exists():
        return "ERROR: src/export_contract.py not found"
    text = path.read_text(encoding="utf-8")
    match = re.search(r'CONTRACT_VERSION\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else "ERROR: CONTRACT_VERSION not found"


def module_count():
    return len(list((REPO_ROOT / "src").glob("*.py")))


def export_artifact_count():
    export_dir = REPO_ROOT / "data" / "export"
    if not export_dir.exists():
        return "ERROR: data/export not found"
    return len(list(export_dir.glob("*.json")))


def config_dir_count():
    export_dir = REPO_ROOT / "data" / "export"
    if not export_dir.exists():
        return 0
    return len([p for p in export_dir.iterdir() if p.is_dir()])


def backend_test_summary():
    code, out, err = run([BACKEND_PYTHON, "-m", "pytest", "-q"], timeout=900)
    lines = [ln for ln in (out + err).splitlines() if ln.strip()]
    # pytest's summary line is the last non-empty line, e.g. "512 passed in 200.97s"
    return lines[-1] if lines else f"ERROR (exit {code})"


def frontend_test_summary():
    frontend_dir = REPO_ROOT / "frontend"
    if not frontend_dir.exists():
        return "ERROR: frontend/ not found"
    code, out, err = run(["npx", "vitest", "run"], cwd=frontend_dir, timeout=600)
    text = out + err
    files_match = re.search(r"Test Files\s+(.+)", text)
    tests_match = re.search(r"Tests\s+(.+)", text)
    if files_match and tests_match:
        return f"{tests_match.group(1).strip()} ({files_match.group(1).strip()})"
    return f"ERROR (exit {code}) — could not parse summary"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tests", action="store_true", help="also run backend + frontend suites (slow, ~4 min)"
    )
    args = parser.parse_args()

    rows = [
        ("Backend branch / commit", f"`master`, `{git_head()}`"),
        ("Data contract", f"`{contract_version()}`"),
        ("Python modules", f"{module_count()} in `src/`"),
        ("Export artifacts", f"{export_artifact_count()} top-level files in `data/export/`"),
        ("Config matrix", f"{config_dir_count()} dirs under `data/export/`"),
    ]

    if args.tests:
        print("Running backend suite (this is slow)...", file=sys.stderr)
        rows.append(("Backend tests", backend_test_summary()))
        print("Running frontend suite (this is slow)...", file=sys.stderr)
        rows.append(("Frontend tests", frontend_test_summary()))
    else:
        rows.append(("Backend tests", "(skipped — pass --tests to run the suite)"))
        rows.append(("Frontend tests", "(skipped — pass --tests to run the suite)"))

    print("| | Value |")
    print("|---|---|")
    for label, value in rows:
        print(f"| {label} | {value} |")


if __name__ == "__main__":
    main()
