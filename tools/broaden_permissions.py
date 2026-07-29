#!/usr/bin/env python
"""Broaden Claude Code command permissions, moving enforcement to the hook.

Rationale, recorded 2026-07-29 at the founder's direction:

  Approval prompts that are always approved are not a safety control. Their
  only real effect is keeping the founder at the keyboard. Enumerating safe
  commands can never be complete - every new verb (Format-List, Measure-Object,
  ...) produces another prompt.

  So: allow commands broadly, and let enforcement live where it actually
  binds -

    * the PreToolUse hook - blocks recursive/forced deletes, force pushes,
      history rewriting, credential access, sudo, and database damage. Exit 2,
      which holds even under bypassPermissions. Cannot be argued out of it.
    * the `ask` rules - these BEAT allow rules, so rm, force-push, .env and
      credentials still prompt.

This script only ADDS allow entries. It never removes an ask or deny rule.
It reads whatever is on disk, so any rules accumulated since last time survive.
"""
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
STAMP = time.strftime("%Y%m%d-%H%M%S")

BROAD = [
    "Bash(*)",
    "PowerShell(*)",
    "Read(**)",
    "Edit(**)",
    "Write(**)",
    "Glob(**)",
    "Grep(**)",
    "WebSearch",
]


def main():
    if not os.path.exists(SETTINGS):
        sys.exit("No .claude/settings.json found at %s" % SETTINGS)

    with open(SETTINGS, encoding="utf-8") as f:
        cfg = json.load(f)

    perms = cfg.setdefault("permissions", {})
    allow = perms.setdefault("allow", [])
    ask = perms.get("ask", [])
    deny = perms.get("deny", [])

    before = len(allow)
    added = []
    for rule in BROAD:
        if rule not in allow:
            allow.append(rule)
            added.append(rule)

    if not added:
        print("  Broad rules already present - nothing to change.")
    else:
        shutil.copy2(SETTINGS, SETTINGS + ".bak-" + STAMP)
        print("  Backed up to settings.json.bak-" + STAMP)
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print("  Added: " + ", ".join(added))

    # re-read to verify
    with open(SETTINGS, encoding="utf-8") as f:
        chk = json.load(f)["permissions"]

    print()
    print("  allow rules : %d  (was %d)" % (len(chk.get("allow", [])), before))
    print("  ask rules   : %d  <- these still prompt; ask beats allow" % len(chk.get("ask", [])))
    print("  deny rules  : %d" % len(chk.get("deny", [])))
    print("  hook wired  : %s" % ("yes" if "hooks" in cfg else "NO - PROBLEM"))

    if len(chk.get("ask", [])) != len(ask) or len(chk.get("deny", [])) != len(deny):
        print()
        print("  WARNING: ask/deny counts changed. Restore the .bak file.")
        return 1

    print()
    print("  Still prompting, by design:")
    for r in chk.get("ask", [])[:6]:
        print("    " + r)
    if len(chk.get("ask", [])) > 6:
        print("    ... and %d more" % (len(chk.get("ask", [])) - 6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
