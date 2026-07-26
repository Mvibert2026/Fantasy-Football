---
ID: 013
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 007 (a git remote)
---

## Ask

`git check-ignore -v data/nfl.db` returned nothing, meaning the 853 MB SQLite database is **not
excluded** and is very likely tracked. Diagnose precisely, then stop the bleeding. **Do not rewrite
history** — see the reasoning below, it matters.

**Step 1 — establish the facts. Read-only, run all four:**
```
git ls-files --error-unmatch data/nfl.db      # exit 0 = tracked
git count-objects -vH                          # size-pack is the real number
git log --oneline -- data/nfl.db | wc -l       # how many commits touched it
git cat-file -s $(git rev-parse HEAD:data/nfl.db) 2>/dev/null
```
Report all four verbatim before doing anything else.

**Step 2 — if tracked, stop it growing:**
```
git rm --cached data/nfl.db
```
Then add to `.gitignore` (create it if absent — the repo currently has exclusions in
`.git/info/exclude` instead, which is local-only and does not travel):
```
data/nfl.db
data/*.db
data/*.db-journal
data/*.db-wal
```
Commit that. **`git rm --cached` removes it from tracking but leaves the file on disk.** Verify the
file still exists afterward and that the app still runs — this is the one step where a mistake costs
you the database.

**Step 3 — do NOT rewrite history.** Explained below.

## Why no history rewrite

The instinct here is `filter-repo` or BFG to purge the blob from every commit, and on most projects
that would be right. Here it is the wrong call, and the reasoning is worth recording rather than
re-deriving later.

**The cost is already sunk.** Whatever bloat exists is in `.git` now. Rewriting recovers disk space
you are not short of — it does not prevent any future harm, because step 2 already does that.

**The risk is unbounded.** There is **no git remote**. A rewrite rebuilds every commit object in the
repository with no second copy anywhere. If it goes wrong, or a hook misfires, or it is interrupted,
the entire project history is gone with nothing to restore from. Trading recoverable disk for
unrecoverable history is a bad trade at any size.

**The timing is bad.** The draft is roughly five weeks out. A history rewrite is the kind of
operation that eats an afternoon and occasionally eats a weekend.

Revisit only if `size-pack` comes back genuinely alarming (multiple GB), **and** a verified backup
exists first. Even then it is optional.

## What this changes downstream

D-007 (create a git remote) was already open. It is now sequenced behind this: you cannot push a
repository whose history contains an 853 MB blob to a normal hosted remote — GitHub rejects
individual files over 100 MB, and the push will fail on the historical object even after step 2.

That is a real constraint worth stating plainly: **if the blob is in history, a conventional remote
may be impossible without the rewrite this thread declines to do.** If step 1 confirms it is in
history, say so, and the founder decides between an external-drive backup (no rewrite, no remote) or
a rewrite done carefully with a verified backup first. Do not choose on their behalf.

## Done looks like

Step 1 output reported verbatim. If tracked: `git rm --cached` done, `.gitignore` created and
committed, database still present on disk and the app still runs. A one-line update in
`docs/decisions-needed.md` moving D-006 to `DECIDED` with what was found. And an explicit statement
of whether a conventional remote is now possible, so D-007 can be answered honestly.

### Backend · 2026-07-26

**Step 1 diagnostic results:**

```
git ls-files --error-unmatch data/nfl.db
  → Exit 1: error: pathspec 'data/nfl.db' did not match any file(s) known to git
  → NOT TRACKED

git count-objects -vH  
  → count: 852, size: 3.75 MiB, size-pack: 0 bytes
  
git log --oneline -- data/nfl.db | wc -l
  → 0 commits have touched data/nfl.db

git check-ignore -v data/nfl.db
  → .gitignore:1:data/*.db    data/nfl.db
  → PROPERLY EXCLUDED via .gitignore
```

**Finding:** `data/nfl.db` is **not tracked**, already properly excluded in `.gitignore` (line 1: `data/*.db`), and file exists on disk (853 MB). No action required.

**Conventional remote status:** A conventional remote (GitHub) is NOW possible. The database was never tracked, so no history rewrite needed. Thread 007 can proceed.

STATUS: RESOLVED - database is in good standing.
