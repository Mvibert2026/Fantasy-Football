---
ID: 075
FROM: pm
TO: pm
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
Defect record (post-hoc, not a live ask): during the 2026-07-27 overnight round, workstream D
(data-ops, thread 067 T1 rescope) ran in a worktree built from git history. `docs/handoffs/067-
t1-multiformat-consensus-rescope.md` was real — 248 lines, containing the actual verified league-2
scoring transcription and the founder's 12->10 team-count correction — but had sat **untracked** in
the main checkout since an earlier session, so it was never part of any commit the worktree branched
from. The worktree could not see it and, instead of halting, generated a 113-line stand-in
(fabricated pm-opening/data-ops sections) to fill the perceived gap. Caught only by a line-count
comparison at merge time (`docs/status.md` 2026-07-27 entry, "T1 multiformat consensus rescope");
no automated check flagged it.

## Why
A plausible fabrication in a mailbox thread is worse than a crash — nothing downstream would have
caught wrong league-2 scoring silently substituted for the real, founder-verified transcription.
This is exactly the failure mode Principle #2 (never fill a gap with plausible-sounding invention)
exists to prevent, and it happened inside the project's own coordination infrastructure, not in
model output.

**Prior-occurrence check (this thread's only open question):** searched `docs/status.md`,
`docs/decisions.md`, and `git log --all --grep=fabricat -i` / `--grep=reconstruct -i` for any
earlier instance of an untracked file being invisible to a worktree and triggering a fabricated
stand-in. Found none — the only untracked-file/worktree issue on record before today
(`docs/status.md`, sprint-closeout section, "pile of untracked working-tree content") was flagged as
an uncommitted-cleanup item, not a fabrication incident. **This is the first documented occurrence
of this specific pattern.**

## Done looks like
Root cause identified and two structural fixes landed same-day, both in
`docs/RUN-2026-07-27-overnight.md`: (1) the standing rule "never reconstruct a missing artifact —
HALT and report" added to this runbook's governing rules; (2) Phase 1 step 4 makes a clean
`git status --porcelain` (zero untracked files) a hard precondition before any chain is dispatched
into a fresh worktree, closing the specific blind spot that let this happen. At merge time the real
248-line file was kept as the base of record; this session's actual new content (the Option 1/2/3
cost analysis) was appended as a dated reply on top of it; the fabricated stand-in sections were
discarded. Nothing measured or found by workstream D was lost. No code fix needed — this was a
process gap, and the process now closes it. Resolved by this record.

---
### pm · 2026-07-27

Resolution artifact: `docs/RUN-2026-07-27-overnight.md` standing rules ("Never reconstruct a
missing artifact... HALT and report") and Phase 1 step 4 (clean-tree precondition), both already
in place before this thread was opened — this thread exists to record the incident and the
prior-occurrence check, not to request new work. Prior-occurrence search: none found (see Why).
No commit needed; the fix is the runbook text itself, verified present at merge commit `9d8e09b`.
