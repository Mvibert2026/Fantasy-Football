You are running unattended for several hours. The founder is not at the screen.

## Standing rules — these govern everything below

- **Decide and log; do not ask.** Make the call, append one line to
  `docs/ideas-inbox.md` under "## PM review-item log", continue. Escalate only
  if the action is irreversible, contradicts a written rule, or spends money.
  A question answerable from a rule means the rule is missing — write the rule.
- **Never reconstruct a missing artifact.** If a file a task depends on is
  absent, HALT and report. Do not infer, rebuild, or write a stand-in. A
  workstream did exactly this today: it could not see thread 067 (untracked, so
  invisible to a worktree built from git history) and wrote a 113-line
  reconstruction standing in for a real 248-line file containing verified
  league-2 scoring. It was caught by a line-count comparison and nothing else.
  A plausible fabrication is more dangerous than any crash.
- **Stop on red.** Cannot produce evidence for step N → do not start step N+1.
  Report and halt.
- **No compound Bash commands.** `cd x && y` defeats permission matching. Use
  `git -C <path>` and absolute paths.
- **Escalate, don't reconcile.** Merge conflicts and thread contradictions stop
  and get reported.
- **Never hand-type a thread ID.** Write `NEW-<slug>.md`; the tooling allocates
  at sync. Two workstreams both allocated 073 today because each read
  "next free = 73" from an isolated worktree.
- Nothing touches `data/nfl.db` destructively. It is ~853 MB, single copy, and
  the ADP snapshots inside it cannot be re-fetched for a past date.
- If a permission prompt appears at any point, note the exact command in your
  final report. Those are now defects, not normal operation.

---

# PHASE 1 — Integrate and land (serial, one agent, no parallelism)

Git-state work. Do not split this across agents.

1. Push the integration branch to origin FIRST, as a backup ref, before
   mutating `main`:
   `git -C .claude/worktrees/integration push -u origin integration-2026-07-27`
2. Fast-forward `main` to it, then push `main`. If it is not a fast-forward,
   HALT and report.
3. `git stash list` must be empty. If not, report the contents and HALT — do
   not resolve it.
4. `git status --porcelain` must be empty. **Any untracked file is a dispatch
   blocker**, because worktrees cannot see untracked files. Report anything
   left and HALT.
5. `tools/handoffs.py sync` then `check`. Report thread count and any flags.

# PHASE 2 — Compressed closeout

Not the full protocol. These five only.

1. **Register two defects** from today's round:
   - *Fabricated reconstruction.* Workstream D invented thread content rather
     than halting. Root cause: untracked files are invisible to worktrees.
     Fix landed: the never-reconstruct rule above, plus the clean-tree
     precondition in Phase 1 step 4. Record whether it had occurred before.
   - *Allocator race.* Two worktrees allocated ID 073 simultaneously. Atomic
     allocation only protects a single working tree. Record as an open
     structural gap; do not attempt a fix tonight.
2. **Interrupt count for the round**, split three ways: permission prompts,
   judgment questions, genuine escalations. Include that workstream B required
   three nudges and returned two vague non-answers while real uncommitted work
   sat in its tree — classify it and say what would prevent it.
3. **Unmerged branches.** `git branch -a`. Every branch merged, deleted, or
   given a named reason to exist.
4. **Update `docs/CURRENT-STATE.md`** in place. Measured figures only, with
   provenance. Note contract 1.11.0 → 1.12.0 and that the freshness result is
   computed but not yet exported to `board.json`.
5. **Do not** drain the ideas inbox, regenerate the dashboard, or rewrite agent
   definitions tonight. Those are batched to the weekly pass.

Re-confirm the tree is clean and pushed before Phase 3.

# PHASE 3 — Two chains, isolated worktrees, sequential within each

Create a fresh worktree per chain. Do not share a directory.

## Chain 1 — backend, strictly sequential, stop on red

**1.1 — ADP snapshot capture is broken and losing unrecoverable data.
Highest priority in this file.**

The scheduled snapshot for 2026-07-27 failed: it ran unattended, hit a WebFetch
provenance/permission prompt with nobody present, and captured nothing. A given
day's ADP cannot be re-fetched later. We are 34 days from the draft, in the
window where ADP moves most, and every further missed day is a permanent hole.

- Replace the WebFetch mechanism with a plain Python `requests` script driven by
  a local scheduled job. No interactive permission layer in the path.
- Persist to the database, not only a markdown file: `fetched_at`, `source`,
  `format`, `teams`, plus the player rows.
- **Backfill today's snapshot immediately** if the source still serves current
  ADP — today is not lost yet, only un-captured.
- Honour existing source constraints: ≤1 request/sec, honest User-Agent, no
  `/adp/csv/` (robots-disallowed), private use only.
- MFL's sample is ~50 hobbyist mocks. Store it; never present it as this
  league's own draft tendency.
- Test: a run with the network stubbed must fail loudly and never write a
  silent empty row.

**1.2 — Export the freshness result to `board.json`.**
Frontend found T5's freshness is computed server-side but never exported, and
correctly shipped an honest gap banner rather than faking it client-side. Close
the gap: add the field, bump the contract, update the trace/provenance footer.

**1.3 — Per-league `consensus_input_source` export tag.**
Workstream D's unbuilt item 4. Three leagues, different scoring and team counts;
each board must state which consensus input produced it.

Land each step with the four landing checks — push, empty stash, thread status
flipped and synced, test counts with red-by-design named — before starting the
next.

## Chain 2 — documentation, separate worktree, independent of Chain 1

**2.1 — Rewrite `CLAUDE.md` §2, §3 and §8.**
They still describe a phantom Builder / Verifier / Statistician / Red-team tier
that does not exist. Workstream A added the allocator pointer but left this.
Replace with the actual agent roster and the actual workflow. An onboarding
document describing agents that were never built is worse than no document.

Same landing checks at close.

---

# Report when you finish or halt

Per chain: commit hashes, test counts with red-by-design named, what is
unfinished and why, every permission prompt you hit, and any rule you had to
invent. That last one is the most useful line in the report.

Do not push to `main` from a chain worktree. Push branches; integration is a
separate serial step.
