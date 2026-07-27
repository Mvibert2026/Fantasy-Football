# Session reset protocol

**Run at every clean point, in order. The status report is the LAST step, not the first.**

The PM has been updating status as a standalone act, which is why it has been wrong. A status report
is the *output* of a reset, not a substitute for one.

---

## What counts as a clean point

All three must hold. If any is false, it is not a clean point and the reset waits.

1. **No agents running.** Everything below is measured against the tree; a moving tree makes it
   fiction.
2. **No uncommitted bridge writes.** Files written over the device bridge exist on disk but are not
   staged. This has already produced six threads that existed, were indexed, and were never committed
   — a fresh checkout would have had broken links.
3. **The ideas inbox has been drained** — or is explicitly deferred with a note saying so.

---

## The sequence

### 1 · Quiesce and commit stragglers
Confirm nothing is running. Commit anything written over the bridge that git does not have.

### 2 · Get measured state — from an agent, never from a PM read
Commit hash, both test suite summaries, contract version. **The PM does not read these itself**
(`pm-operating-discipline.md` § M7 — staged files return cached content with fresh timestamps).
Once `tools/state.py` is wired this is one command.

### 3 · Drain the ideas inbox
Read the whole `RAW` block at once. Group related ideas, dedupe against open threads, and write a
**small number of well-scoped threads** rather than one per idea. Tag every entry —
`→ NNN`, `FOLDED INTO NNN`, `DECLINED — reason`, or `PARKED — condition`. **No entry left `RAW`
without a stated reason for deferring it.**

New threads use the PM's reserved range: **100 and up.** Agents own everything below 100.

### 4 · Reconcile threads
Dispositions for anything closed, superseded or duplicated since the last reset. Contradictions come
to the PM, never resolved by an agent. Run `handoffs.py check` and act on what it reports.

### 5 · Update the defect register
Every defect the founder personally reported this round: what it was, whether it was verified fixed,
and **whether he had reported it before.** Repeat rate and founder-versus-project detection split are
the two numbers that matter (§ M1).

### 6 · Self-audit — the step with the most value and the least comfort
Answer in writing, briefly:

- What did the founder catch that the project should have?
- **What did I assert last round that turned out to be wrong?**
- What is stale, contradictory, or superseded?
- Which threads are older than two rounds, and why?

### 7 · Now update the status report
`CURRENT-STATE.md` in place, from step 2's measured figures. Every claim labelled by provenance —
agent-reported, founder-reported, or unverified. Anything not re-verified says so rather than
carrying forward silently.

### 8 · Pre-dispatch check, then dispatch
Re-read every newly written thread against the open set and the recently closed set before anything
goes out. Five minutes; it would have caught 044/059 and 054/055/057.

---

## Cost discipline

This protocol is itself subject to the test in § M8: it must cost less than the failures it prevents.
Steps 1, 2, 4 and 8 are minutes. Step 3 replaces work the PM was doing anyway, worse. Steps 5 and 6
are short written answers.

**If a reset starts taking longer than the round it follows, cut it.** Report which step was cut and
why, so the deletion is visible rather than quiet.
