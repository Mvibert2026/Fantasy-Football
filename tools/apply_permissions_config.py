#!/usr/bin/env python
"""Apply the Claude Code permission configuration. Run once, from the repo root:

    python tools/apply_permissions_config.py

Writes .claude/settings.json, creates .claude/hooks/block_dangerous.py, and
changes exactly one value in .claude/settings.local.json (defaultMode ->
"auto"), leaving its 458 allow entries and 4 deny entries untouched.

Backs up anything it overwrites to <name>.bak-YYYYmmdd-HHMMSS first.
Idempotent: safe to run twice.
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(ROOT, ".claude")
STAMP = time.strftime("%Y%m%d-%H%M%S")

SETTINGS = '{\n  "model": "sonnet",\n  "effortLevel": "medium",\n  "permissions": {\n    "allow": [\n      "Read(**)",\n      "Edit(**)",\n      "Write(**)",\n      "Glob(**)",\n      "Grep(**)",\n      "Bash(git *)",\n      "PowerShell(git *)",\n      "Bash(npm *)",\n      "PowerShell(npm *)",\n      "Bash(pytest *)",\n      "PowerShell(pytest *)",\n      "Bash(\\"C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\" *)",\n      "Bash(C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe *)",\n      "Bash(\\"/c/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\" *)",\n      "Bash(/c/Users/matth/miniconda3/envs/fantasyfootball/python.exe *)",\n      "Bash(\\"C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\")",\n      "Bash(/c/Users/matth/miniconda3/envs/fantasyfootball/python.exe)",\n      "Bash(PYTHONIOENCODING=utf-8 \\"C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\" *)",\n      "Bash(PYTHONIOENCODING=utf-8 C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe *)",\n      "Bash(PYTHONIOENCODING=utf-8 \\"/c/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\" *)",\n      "Bash(PYTHONIOENCODING=utf-8 /c/Users/matth/miniconda3/envs/fantasyfootball/python.exe *)",\n      "PowerShell(& \\"C:\\\\Users\\\\matth\\\\miniconda3\\\\envs\\\\fantasyfootball\\\\python.exe\\" *)",\n      "PowerShell(C:\\\\Users\\\\matth\\\\miniconda3\\\\envs\\\\fantasyfootball\\\\python.exe *)",\n      "WebFetch",\n      "WebSearch",\n      "Bash(python *)",\n      "Bash(python3 *)",\n      "Bash(py *)",\n      "Bash(pip *)",\n      "Bash(conda *)",\n      "Bash(node *)",\n      "Bash(npx *)",\n      "Bash(ls *)",\n      "Bash(cat *)",\n      "Bash(head *)",\n      "Bash(tail *)",\n      "Bash(grep *)",\n      "Bash(rg *)",\n      "Bash(find *)",\n      "Bash(wc *)",\n      "Bash(echo *)",\n      "Bash(printf *)",\n      "Bash(sed *)",\n      "Bash(awk *)",\n      "Bash(jq *)",\n      "Bash(sort *)",\n      "Bash(uniq *)",\n      "Bash(diff *)",\n      "Bash(mkdir *)",\n      "Bash(touch *)",\n      "Bash(cp *)",\n      "Bash(mv *)",\n      "Bash(test *)",\n      "Bash(which *)",\n      "Bash(pwd)",\n      "Bash(date *)",\n      "Bash(vitest *)",\n      "Bash(tsc *)",\n      "Bash(eslint *)",\n      "Bash(tools/handoffs.py *)",\n      "PowerShell(python *)",\n      "PowerShell(pip *)",\n      "PowerShell(conda *)",\n      "PowerShell(Get-* *)",\n      "PowerShell(Test-Path *)",\n      "PowerShell(Select-* *)",\n      "WebFetch(domain:api.myfantasyleague.com)",\n      "WebFetch(domain:fantasyfootballcalculator.com)",\n      "WebFetch(domain:www.fantasyfootballcalculator.com)",\n      "WebFetch(domain:github.com)",\n      "WebFetch(domain:raw.githubusercontent.com)",\n      "WebFetch(domain:code.claude.com)",\n      "WebFetch(domain:docs.claude.com)"\n    ],\n    "ask": [\n      "Bash(rm *)",\n      "PowerShell(rm *)",\n      "PowerShell(Remove-Item *)",\n      "Bash(git push --force *)",\n      "Bash(git push -f *)",\n      "Bash(git push --force-with-lease *)",\n      "PowerShell(git push --force *)",\n      "PowerShell(git push -f *)",\n      "PowerShell(git push --force-with-lease *)",\n      "Read(.env)",\n      "Read(.env.*)",\n      "Read(**/.env)",\n      "Read(**/.env.*)",\n      "Edit(.env)",\n      "Edit(.env.*)",\n      "Edit(**/.env)",\n      "Edit(**/.env.*)",\n      "Write(.env)",\n      "Write(.env.*)",\n      "Write(**/.env)",\n      "Write(**/.env.*)",\n      "Read(**/credentials*)",\n      "Edit(**/credentials*)",\n      "Write(**/credentials*)"\n    ]\n  },\n  "hooks": {\n    "PreToolUse": [\n      {\n        "matcher": "Bash|PowerShell",\n        "hooks": [\n          {\n            "type": "command",\n            "command": "\\"C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe\\" \\"$CLAUDE_PROJECT_DIR/.claude/hooks/block_dangerous.py\\""\n          }\n        ]\n      }\n    ]\n  }\n}'

HOOK = '#!/usr/bin/env python\n"""PreToolUse hook. Cross-platform (Windows-safe) replacement for a bash hook.\n\nExit 2  -> blocks the command, even under bypassPermissions. This is the only\n           guaranteed backstop; settings-level deny rules may not survive\n           bypass mode (docs ambiguous as of 2026-07-27).\nExit 0  -> no opinion; normal permission flow continues.\n\nFails OPEN by design: if this script itself errors, it exits 0 rather than\nwedging every command in an unattended run. The `ask` rules in settings.json\nremain the second line of defence.\n"""\nimport json\nimport re\nimport sys\n\nPATTERNS = [\n    (r"(?:^|[;&|]\\s*)rm\\s+(?:-\\w*\\s+)*-\\w*[rRf]", "recursive or forced rm"),\n    (r"(?:^|[;&|]\\s*)(?:rmdir|shred|srm)\\s",       "destructive delete"),\n    (r"Remove-Item[^\\n]*-(?:Recurse|Force)",       "PowerShell recursive/forced delete"),\n    (r"git\\s+.*push\\s+.*(?:--force|-f)(?:[\\s=]|$)", "force push"),\n    (r"git\\s+.*(?:reset\\s+--hard|clean\\s+-\\w*[fdx]|filter-branch|reflog\\s+expire)",\n                                                    "history or worktree destruction"),\n    (r"git\\s+.*(?:branch\\s+-D|update-ref\\s+-d|stash\\s+(?:drop|clear))",\n                                                    "irreversible git ref or stash deletion"),\n    (r"(?:^|[^\\w./-])\\.env(?:[^\\w-]|$)",           "touches .env"),\n    (r"(?:credentials|\\.pem\\b|id_rsa|\\.netrc|\\.aws[/\\\\]|\\.ssh[/\\\\])",\n                                                    "touches credentials"),\n    (r">\\s*/(?:etc|usr|bin|sbin|var|opt)/",         "write outside repo"),\n    (r"(?:^|[;&|]\\s*)sudo\\s",                       "sudo"),\n]\n\n# The database is ~853 MB, single copy. ADP snapshots inside it cannot be\n# re-fetched for a past date.\nDB = (r"nfl\\.db", r"(?:^|[;&|]\\s*)(?:rm|mv|truncate)\\s|>\\s*\\S*nfl\\.db")\n\n\ndef main() -> int:\n    try:\n        payload = json.load(sys.stdin)\n    except Exception:\n        return 0\n\n    ti = payload.get("tool_input") or {}\n    cmd = ti.get("command") or ti.get("script") or ""\n    if not isinstance(cmd, str) or not cmd.strip():\n        return 0\n\n    for pat, why in PATTERNS:\n        if re.search(pat, cmd, re.IGNORECASE):\n            print(f"BLOCKED by .claude/hooks/block_dangerous.py: {why}", file=sys.stderr)\n            return 2\n\n    if re.search(DB[0], cmd, re.I) and re.search(DB[1], cmd, re.I):\n        print("BLOCKED by .claude/hooks/block_dangerous.py: nfl.db mutation", file=sys.stderr)\n        return 2\n\n    return 0\n\n\nif __name__ == "__main__":\n    try:\n        sys.exit(main())\n    except Exception:\n        sys.exit(0)   # fail open\n'


def backup(path):
    if os.path.exists(path):
        dst = path + ".bak-" + STAMP
        shutil.copy2(path, dst)
        print("  backed up ->", os.path.basename(dst))


def main():
    if not os.path.isdir(CLAUDE):
        sys.exit("No .claude directory at %s — run this from the repo." % ROOT)

    # 1. settings.json
    p = os.path.join(CLAUDE, "settings.json")
    print("settings.json")
    backup(p)
    with open(p, "w", encoding="utf-8") as f:
        f.write(SETTINGS)
    d = json.load(open(p, encoding="utf-8"))
    print("  %d allow, %d ask, hooks=%s"
          % (len(d["permissions"]["allow"]), len(d["permissions"]["ask"]), "hooks" in d))

    # 2. hook
    hd = os.path.join(CLAUDE, "hooks")
    os.makedirs(hd, exist_ok=True)
    hp = os.path.join(hd, "block_dangerous.py")
    print("hooks/block_dangerous.py")
    backup(hp)
    with open(hp, "w", encoding="utf-8") as f:
        f.write(HOOK)
    print("  written")

    # 3. one surgical value change in settings.local.json
    lp = os.path.join(CLAUDE, "settings.local.json")
    print("settings.local.json")
    if not os.path.exists(lp):
        print("  absent - skipped")
    else:
        raw = open(lp, encoding="utf-8").read()
        local = json.loads(raw)
        before = local.get("permissions", {}).get("defaultMode")
        n_allow = len(local.get("permissions", {}).get("allow", []))
        n_deny = len(local.get("permissions", {}).get("deny", []))
        if before == "auto":
            print("  already auto - unchanged")
        else:
            backup(lp)
            if '"defaultMode"' in raw:
                new = raw.replace('"defaultMode": "%s"' % before,
                                  '"defaultMode": "auto"', 1)
                if new == raw:   # spacing differs; fall back to a reparse+dump
                    local["permissions"]["defaultMode"] = "auto"
                    new = json.dumps(local, indent=2)
            else:
                local.setdefault("permissions", {})["defaultMode"] = "auto"
                new = json.dumps(local, indent=2)
            with open(lp, "w", encoding="utf-8") as f:
                f.write(new)
            chk = json.load(open(lp, encoding="utf-8"))["permissions"]
            assert chk["defaultMode"] == "auto"
            assert len(chk.get("allow", [])) == n_allow, "allow list changed - restore the .bak"
            assert len(chk.get("deny", [])) == n_deny, "deny list changed - restore the .bak"
            print("  defaultMode %s -> auto (%d allow, %d deny preserved)"
                  % (before, n_allow, n_deny))

    # 4. verify the hook behaves
    print("hook self-test")
    cases = [("git status", 0), ("pytest -q", 0), ("rm -rf build", 2),
             ("git push --force origin main", 2), ("cat .env", 2)]
    bad = 0
    for cmd, expected in cases:
        r = subprocess.run([sys.executable, hp],
                           input=json.dumps({"tool_input": {"command": cmd}}),
                           capture_output=True, text=True)
        ok = r.returncode == expected
        bad += not ok
        print("  %-4s exit=%s expected=%s  %s"
              % ("ok" if ok else "FAIL", r.returncode, expected, cmd))
    print("  failures:", bad)

    print("\ninterpreter this machine resolves to:")
    print("  ", sys.executable)
    print("interpreter baked into the hook command in settings.json:")
    print("   C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe")
    print("\nIf those two differ, tell Claude before relaunching - the hook")
    print("fails open and would silently protect nothing.")
    print("\nDone. Quit Claude Code and relaunch for the mode change to apply.")


if __name__ == "__main__":
    main()
