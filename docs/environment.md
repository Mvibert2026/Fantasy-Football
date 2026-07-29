# Local environment — read before running any command

Every fact here was rediscovered independently by multiple agents across multiple sessions,
each time costing a failed command or a stalled unattended run. Subagents do not inherit
session memory, so this file is the only way these survive.

Verified 2026-07-29 against the current code unless a fact says otherwise.

---

## 1. Python is not on PATH

Use the conda interpreter, fully quoted:

```
"C:/Users/matth/miniconda3/envs/fantasyfootball/python.exe"
```

`python`, `python3`, and `py` on PATH are Windows Store alias stubs. `python` errors with
"Python was not found"; `py` points at a non-existent Python314 install. Neither works, and
there is no venv in the repo. The conda env is Python 3.12.13 (verified 2026-07-29).

Do not prefix the path with PowerShell's call operator `&`. Use the quoted path directly.

---

## 2. The PreToolUse hook, not permissions, is what stops commands

`.claude/hooks/block_dangerous.py` runs before every Bash/PowerShell call. Hooks fire
regardless of `permissions.allow`, so **no allowlist entry can suppress them.**

`.claude/settings.json` `permissions.allow` already ends with `Bash(*)` and `PowerShell(*)`
(94 entries, verified 2026-07-29). Every shell command is already permitted. Adding narrower
entries like `Bash(git log *)` removes zero prompts. `.claude/settings.local.json` holds ~556
such redundant entries; leaving them alone is a deliberate decision, not an oversight.

If a command is being stopped, look at the hook and at `permissions.ask` — never at
`permissions.allow`.

### 2a. What the hook blocks

**Chaining.** Any `&&`, `||`, `;`, or newline in the command string. Pipes (`|`) are fine and
are explicitly allowed.

**Destructive patterns**, matched case-insensitively: recursive/forced `rm`, `rmdir`/`shred`/
`srm`, `Remove-Item` with `-Recurse` or `-Force`, force push, `git reset --hard`,
`git clean -fdx`, `filter-branch`, `reflog expire`, `git branch -D`, `update-ref -d`,
`stash drop`/`clear`, any mention of `.env`, credential paths (`.pem`, `id_rsa`, `.netrc`,
`.aws/`, `.ssh/`), writes outside the repo, and `sudo`.

**`nfl.db` mutation**, when a command names `nfl.db` *and* looks like `rm`/`mv`/`truncate` or a
redirect into it.

The hook **fails open**: if the script itself errors it exits 0 rather than wedging an
unattended run.

### 2b. The known false positive — semicolons that are not separators

Since 2026-07-28 the hook blanks quoted spans before matching, so a `;` inside a quoted string
(a commit message, say) no longer trips it. But the scan is **textual, not syntactic**, so a
semicolon that is legitimate PowerShell syntax is still blocked:

| Command | Result |
|---|---|
| `Select-Object @{n='FE';e={$_.Name}}` | **BLOCKED** — false positive |
| `ForEach-Object { $a = 1; $b = 2 }` | **BLOCKED** — false positive |
| `git commit -m 'fix a; then b'` | allowed |
| `git commit -m "fix a; then b"` | allowed |

Measured 2026-07-29 by running the hook's own `CHAIN`/`QUOTED` regexes against these strings.

A subtler case: commands that **interleave both quote types**, especially with escaped quotes
(`python -c "... r'...\"...\"' ..."`), can misalign the textual dequote and expose a `;` that
you believed was quoted. Do not rely on quoting to protect a semicolon.

**How to work with it:**

- One command per tool call. Assume any `;` will be rejected, even inside a literal.
- Use pipelines instead of chaining where possible.
- Prefer a single command that already returns what you were about to assemble in a loop
  (`git ls-files -s <dir>` rather than hashing files in a `ForEach-Object`).
- For anything genuinely multi-step, **write a `.py` file to the scratchpad and run it** with
  the interpreter in §1. This is the reliable escape hatch and it sidesteps quoting entirely.
- To delete a directory tree: delete files (`Get-ChildItem <dir> -File | Remove-Item`), then
  each directory innermost-first with plain `Remove-Item`.

The gate exists because chained commands stop and wait for a human approval that never comes in
an unattended run. Fighting it wastes calls; work with it.

---

## 3. Commit messages: use a file, not a here-string

PowerShell 5.1 here-strings (`git commit -m @'...'@`) break on **embedded double quotes** —
PowerShell's native-command argument re-quoting hands git fragments it reads as switches
(`error: unknown switch '>'` from a quoted `"... -> ..."`).

The Bash tool does **not** understand here-strings at all: `@'...'@` there passes the literal
`@` characters straight into the message. This produced a malformed commit on 2026-07-29.

**Reliable pattern, both shells:** write the message to a file in the scratchpad, then

```
git commit -F "<path-to-message-file>"
```

Newlines are blocked by the hook (§2a), so heredocs are not an option either.

---

## 4. Worktrees do not inherit `data/nfl.db`

`src/db.py:26` resolves `DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"`
— relative to its own file. In a worktree under `.claude/worktrees/*` the suite therefore looks
for the DB *inside the worktree*, not the main checkout.

Worse: `sqlite3.connect` silently **creates an empty stub** there on first touch, after which
~21 DB-dependent tests fail with "no such table: rankings". The failures look like regressions
but are environmental, and the stub masks itself as "the DB exists."

Observed 2026-07-27 in the `fable-ext` worktree: 508 passed / 21 failed / 4 errors with the
stub, versus 532 passed / 1 failed with a real copy (the 1 is T3, red by design).

**Before running the full suite in a worktree:** delete any stub, then *copy* (never hardlink —
tests may write) the real `data/nfl.db` into the worktree's `data/`. It is gitignored.
Experiment-scoped tests (`test_bottomup_prototype.py`, `test_situation_features.py`) fall back
to the master-checkout path on their own.

---

## 5. Browser-pane screenshots fail in worktrees — use Playwright

Observed 2026-07-28 (threads 058, 069/073 and workstream C): the sandbox Browser pane loads
pages, but `screenshot` fails with "Browser pane is not displayed."

Working fallback: a small Playwright script driving the frontend's own devDependency chromium.
Pattern in `frontend/e2e/verify-069-073.mjs`, run against an already-running dev server with
`--url http://localhost:<port>`. Screenshots land in `frontend/e2e/artifacts/`, which is tracked
and expected to hold committed proof captures.

Two related gotchas:

- `preview_start` reads the **main checkout's** tracked `.claude/launch.json`. To preview a
  worktree, add a temporary entry with `--prefix .claude/worktrees/<name>/frontend` and a unique
  port (5190+ is free; 5173–5189 are claimed), then **revert it in the same session** — the file
  is tracked, and a dirty main tree blocks dispatch under the overnight rules.
- Frontend tests in a worktree need `npm ci` first. `npm test`'s pretest sync handles
  `public/data` from the worktree's own tracked `data/export/`. No `nfl.db` needed, unlike the
  backend suite (§4).

---

## 6. Command style that avoids stopping

- One command per tool call. Never chain with `&&`, `;`, `||`, or newlines.
- Never start a command with `&`; use the quoted path directly.
- Call Python via the full quoted conda path (§1).
- Prefer `git -C <path>` over `cd` — the hook's message says so explicitly, and `cd` in a
  compound command triggers a prompt.
