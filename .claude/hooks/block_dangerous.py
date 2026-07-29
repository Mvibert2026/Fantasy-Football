#!/usr/bin/env python
"""PreToolUse hook. Cross-platform (Windows-safe) replacement for a bash hook.

Exit 2  -> blocks the command, even under bypassPermissions. This is the only
           guaranteed backstop; settings-level deny rules may not survive
           bypass mode (docs ambiguous as of 2026-07-27).
Exit 0  -> no opinion; normal permission flow continues.

Fails OPEN by design: if this script itself errors, it exits 0 rather than
wedging every command in an unattended run. The `ask` rules in settings.json
remain the second line of defence.
"""
import json
import re
import sys

PATTERNS = [
    (r"(?:^|[;&|]\s*)rm\s+(?:-\w*\s+)*-\w*[rRf]", "recursive or forced rm"),
    (r"(?:^|[;&|]\s*)(?:rmdir|shred|srm)\s",       "destructive delete"),
    (r"Remove-Item[^\n]*-(?:Recurse|Force)",       "PowerShell recursive/forced delete"),
    (r"git\s+.*push\s+.*(?:--force|-f)(?:[\s=]|$)", "force push"),
    (r"git\s+.*(?:reset\s+--hard|clean\s+-\w*[fdx]|filter-branch|reflog\s+expire)",
                                                    "history or worktree destruction"),
    (r"git\s+.*(?:branch\s+-D|update-ref\s+-d|stash\s+(?:drop|clear))",
                                                    "irreversible git ref or stash deletion"),
    (r"(?:^|[^\w./-])\.env(?:[^\w-]|$)",           "touches .env"),
    (r"(?:credentials|\.pem\b|id_rsa|\.netrc|\.aws[/\\]|\.ssh[/\\])",
                                                    "touches credentials"),
    (r">\s*/(?:etc|usr|bin|sbin|var|opt)/",         "write outside repo"),
    (r"(?:^|[;&|]\s*)sudo\s",                       "sudo"),
]

# The database is ~853 MB, single copy. ADP snapshots inside it cannot be
# re-fetched for a past date.
DB = (r"nfl\.db", r"(?:^|[;&|]\s*)(?:rm|mv|truncate)\s|>\s*\S*nfl\.db")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    ti = payload.get("tool_input") or {}
    cmd = ti.get("command") or ti.get("script") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return 0

    for pat, why in PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            print(f"BLOCKED by .claude/hooks/block_dangerous.py: {why}", file=sys.stderr)
            return 2

    if re.search(DB[0], cmd, re.I) and re.search(DB[1], cmd, re.I):
        print("BLOCKED by .claude/hooks/block_dangerous.py: nfl.db mutation", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)   # fail open
