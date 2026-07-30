---
ID: FR-072
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Thread hygiene process is failing: 24 of 38 threads needed no action

Founder's own words, on being shown the 2026-07-30 backlog triage:

> "sounds like we need to update some processes and procedures if we are looking at so many done
> and never closed or superseeded or stale tickets"

## Why it matters

He is right, and the diagnosis is worse than "we were sloppy": **the guard that catches this
already exists, is already wired into the test suite, and is red right now.**

`tools/handoffs.py check` fails on duplicate IDs, RESOLVED-without-reply, threads addressed to
nobody, and stale OPEN threads. `tests/test_handoffs.py::test_mailbox_health` asserts it exits 0.
Run on 2026-07-30 it fails with 7 findings — three files claiming thread `093`, two claiming `094`,
and two ADR numbers (`054`, `055`) carrying conflicting headers across branches.

So this is not a missing-process problem. It is a **the-alarm-is-ringing-and-nobody-is-in-the-room**
problem. Agents have been reporting "N tests passing" all session while this specific test was red.
That is a reporting failure as much as a hygiene one.

## Initial read

Not the founder's own words — PM's read. Each triage bucket has a different cause, and only one of
them is discipline.

### Bucket 1 — "Done, never closed" (10 threads). Cause: a missing state.

The protocol says only the `TO:` role may set `STATUS: RESOLVED`. That rule is correct — it stops a
doer from marking their own work accepted. But there is no state for *"work is done, awaiting your
confirmation."* So the doer finishes, appends a resolution section, and moves on; the thread stays
`OPEN` forever because the `TO:` role never returns to it. Ten threads sat in exactly this position.

**Proposed fix:** add a `DONE-PENDING-CONFIRM` status the *doer* is permitted to set. The thread
leaves the open queue immediately and visibly, and the `TO:` role's only remaining job is to confirm
or reject. Preserves the correctness reason the original rule exists for; removes the gap it
created. Small change to `handoffs.py` and `docs/handoffs/README.md`.

### Bucket 2 — "Superseded" (7) + "stale premise" (3). Cause: nothing links forward.

When an ADR supersedes a decision, or a design change invalidates a premise, threads resting on that
premise are not swept. All three stale-premise threads (026, 040, 072) hang off the six-state
Settings editor that FR-069 proposes replacing — one design decision silently orphaned three
threads.

Some machinery for this already exists: `handoffs.py` has stale-decision-reference detection
(`test_flag_stale_decision_refs_detects_reference_to_decided_d_number`). **Extend that rather than
build something new** — an ADR that supersedes another should cause `check` to name the threads
that cite the superseded one.

### Bucket 3 — ID collisions (093 ×3, 094 ×2, ADR-054/055). Cause: concurrency, and it is PM's.

The allocator is not being ignored. It tries to widen past the local tree via git refs
(`test_next_free_id_widens_past_local_tree_via_refs`). It collides anyway because **parallel agents
in separate worktrees allocate the same number simultaneously** — neither branch exists yet when the
other reads. This has now happened four times (043, 049, 053, ADR-048, and again today).

This is not an agent discipline problem. It is a direct consequence of how PM dispatches: several
worktree-isolated agents at once, each allocating its own IDs.

**Proposed fix, and it costs nothing: PM allocates thread and ADR numbers *before* dispatch and
hands each agent its number in the dispatch prompt.** Serialises allocation through the one place
that is already serial. No tooling change required — a change to how PM works.

### Bucket 4 — the meta-failure. Cause: nobody runs the alarm.

`test_mailbox_health` is red and every agent report this session said tests passed. Either agents
are running subsets, or the failure is being seen and not escalated.

**Proposed fix:** the mailbox check runs at session start (it is already `handoffs.py check`, one
command) and its result appears in the PM's own report, not an agent's. A guard nobody reads is
indistinguishable from a guard that does not exist.

### What NOT to do

Do not add prose to `CLAUDE.md`. The rule this failure violates is *already written there* — "Touched
a thread? Append a reply and update its `STATUS:`, even if the reply is 'no action taken, because
X.'" It was ignored because remembering is not a mechanism. Adding a second, more emphatic sentence
would be the same mistake with more words, and Red-team's mandate explicitly covers flagging
process built for its own sake.

Three of the four fixes above are mechanical. The fourth is a change to PM's dispatch habit. None of
them is a new document.

## Sequencing

Not urgent against the 7 September draft, and explicitly below the bottom-up model. But bucket 3 is
actively corrupting numbering *today* and bucket 3's fix is free — PM should adopt pre-allocation
immediately rather than waiting for this ticket to be scheduled.
