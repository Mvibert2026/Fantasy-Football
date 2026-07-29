#!/usr/bin/env python
"""PreToolUse hook. Cross-platform (Windows-safe).

Two jobs:

  1. BLOCK genuinely destructive commands (exit 2). This survives
     bypassPermissions and is the only guaranteed backstop.
  2. BLOCK shell command chaining (&& ; ||) with an instruction to rewrite.
     Chained commands are hard-gated by Claude Code regardless of allow
     rules, so every one of them becomes a prompt the founder must answer.
     Turning that into an agent self-correction is the point.

Pipes (|) are NOT blocked — they are a single logical operation, awkward to
split, and CAN be pre-approved by allow rules.

Quoted spans are stripped before matching, so a commit message that merely
MENTIONS a blocked term no longer trips the hook. That was a real false
positive on 2026-07-28.

Fails OPEN by design: if this script errors, it exits 0 rather than wedging
every command in an unattended run. The `ask` rules in settings.json remain
the second line of defence.
"""
import json
import re
import sys

# --- destructive patterns, matched against the de-quoted command -------------
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

DB = (r"nfl\.db", r"(?:^|[;&|]\s*)(?:rm|mv|truncate)\s|>\s*\S*nfl\.db")

# --- chaining ---------------------------------------------------------------
CHAIN = re.compile(r"&&|\|\||;|\n")

CHAIN_MSG = (
    "BLOCKED: multi-command block. Claude Code hard-gates &&, ||, ; AND "
    "newline-separated commands "
    "regardless of permission settings, so this would stop and wait for a "
    "human. Run these as SEPARATE tool calls instead, and check each "
    "result before starting the next one. You are already in the repo "
    "root, so `cd` is unnecessary; use `git -C <path>` or absolute paths "
    "if you need a different directory. Pipes (|) are fine and need no "
    "change."
)

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def dequote(cmd: str) -> str:
    """Blank out quoted spans so their contents cannot trigger a match."""
    return QUOTED.sub(lambda m: " " * len(m.group(0)), cmd)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    ti = payload.get("tool_input") or {}
    cmd = ti.get("command") or ti.get("script") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return 0

    bare = dequote(cmd)

    for pat, why in PATTERNS:
        if re.search(pat, bare, re.IGNORECASE):
            print("BLOCKED by .claude/hooks/block_dangerous.py: %s" % why, file=sys.stderr)
            return 2

    if re.search(DB[0], bare, re.I) and re.search(DB[1], bare, re.I):
        print("BLOCKED by .claude/hooks/block_dangerous.py: nfl.db mutation", file=sys.stderr)
        return 2

    if CHAIN.search(bare):
        print(CHAIN_MSG, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)   # fail open
