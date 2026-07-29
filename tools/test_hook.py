#!/usr/bin/env python
"""Self-test for .claude/hooks/block_dangerous.py. Exit 0 if all pass."""
import json
import os
import subprocess
import sys

HOOK = os.path.join(".claude", "hooks", "block_dangerous.py")

CASES = [
    ("git status", 0, "plain command"),
    ("pytest -q", 0, "plain command"),
    ("git log --oneline | head -20", 0, "pipe allowed"),
    ("Get-NetTCPConnection -State Listen | Select-Object LocalPort", 0, "pipe allowed"),
    ('git commit -m "document what .env handling does"', 0, "quoted term not blocked"),
    ('python -c "import json; print(1)"', 0, "semicolon inside quotes"),
    ("cd frontend && npm test", 2, "chained command blocked"),
    ("echo a; echo b", 2, "chained command blocked"),
    ('git -C "/repo" log --oneline -1\necho "---"\ngit -C "/repo" status', 2,
     "newline-separated block blocked"),
    ("rm -rf build", 2, "recursive rm blocked"),
    ("git push --force origin main", 2, "force push blocked"),
    ("cat .env", 2, "credentials blocked"),
    ("git stash drop", 2, "stash drop blocked"),
    ("sudo apt install jq", 2, "sudo blocked"),
    ("rm nfl.db", 2, "database blocked"),
]


def main():
    if not os.path.exists(HOOK):
        print("  hook not found at", HOOK)
        return 1
    bad = 0
    for cmd, expected, note in CASES:
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({"tool_input": {"command": cmd}}),
            capture_output=True, text=True)
        ok = r.returncode == expected
        bad += not ok
        print("  %-4s exit=%s expected=%s  %-28s %s"
              % ("ok" if ok else "FAIL", r.returncode, expected, note, cmd[:44]))
    print()
    print("  failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
