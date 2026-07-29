# Closeout — two tiers

**The dividing principle: does deferring this destroy information, or only delay it?**

Unpushed work means the next session branches off a stale base. A stash is anonymous a day later. A
ticket left open gets re-requested as new work. Those decay, so they are paid every session.

A duplicate ticket, a stale dashboard, an undrained ideas inbox only cost tokens, and get *cheaper* in
batch.

---

## What changes when sessions run in the cloud

The database rebuilds from public sources in about four minutes, so cloud sessions are viable once the
three unreproducible artifacts are committed (see `docs/can-we-rebuild-the-database.md`).

**Most of what made closeout painful was the shared working directory.** In cloud, each session
clones, works and pushes — those collisions become ordinary merges.

| Step | In cloud |
|---|---|
| Resolve stashes, both-ways divergence, dev-server sprawl, worktree database copying | **Mostly disappears** |
| Verify that "done" claims are true | **Unchanged — this is the part that matters** |
| Register defects, keep state honest, ticket hygiene | **Unchanged** |

**As collision-handling drops out, this should get shorter, not find new work.** If it stays the same
length after the move, something was added that did not earn its place. **Name what was cut, every
time.**

---

# Tier 1 · The landing check

**Every session, run by the agent itself as its last action.** In the dispatch template, not a founder
question. Five minutes.

1. **Push.** Ahead → push. Behind → pull. Diverged → stop and escalate.
2. **Stash empty.** If not, report and halt — do not resolve it.
3. **Ticket status current**, then sync.
4. **Test counts reported**, with any deliberate failures named. A red test with no note becomes "was
   that always red?" within a day.

---

# Tier 2 · The full closeout

**At a milestone, or roughly weekly.** One agent, serial. Only safe split: the two test suites
concurrently.

**Clean point:** no agents running · nothing uncommitted · local and remote agree · ideas inbox
drained or explicitly deferred.

**1 · Resolve any stash** *(local only)*. Never drop or apply on instinct. Diff each file against
current state — present already means redundant, absent means unique and dropping destroys it. If
applying conflicts, stop and escalate. Report which files were which.

**2 · Unmerged branches.** Every branch merged, discarded, or with a named reason. **Invisible
finished work is a named failure** — a whole session's output once sat uncommitted in a worktree
overnight.

**3 · Verify rather than accept.** Full suites with counts. **Run the acceptance harness** — it caught
a real defect on its first unmodified run. UI work needs a green run, a screenshot, or a written
statement that neither was possible. Spot-check one claimed change against the tree.

**4 · Mailbox check.** Duplicate numbers, unaddressed tickets, resolved-without-reply, staleness,
contradictions. Contradictions go to the PM.

**5 · Defect register and interrupt count.** Every defect the founder personally reported: what,
whether verified fixed, **and whether it had been reported before**. Track **repeat rate** (any
non-zero is an acceptance failure) and **detection split** (founder-found versus project-found).

Then interrupts per session: **permission prompt** (fix in command style or the hook — *not* the
allow-list, which is a wildcard) · **judgment question** (a missing rule) · **genuine escalation**
(correct, leave it). **Only the third should survive.**

**6 · Self-audit, in writing.** What did the founder catch that the project should have? **What did I
assert last round that turned out to be wrong?** What is stale or superseded? Which tickets are older
than two rounds? *The second question is the one with value.*

**7 · Drain the ideas inbox.** Read the whole raw block at once, group, dedupe, write a small number of
well-scoped tickets. Tag every entry — converted, folded, declined with a reason, parked with a
condition. Nothing left untagged.

**8 · Update state, then the dashboard.** `docs/CURRENT-STATE.md` in place, **measured figures only,
never copied from a report including the PM's**. Provenance on every claim. **Date every
measurement** — a stale figure there read as current for two days. Then regenerate the dashboard; it
is a view of state, not a second source.

**9 · Update the agent definitions and `docs/pm/MEMORY.md`.** When a correction has been made twice,
or a process changed, amend the definition so the next session inherits it rather than rediscovering
it.

**10 · Pre-dispatch check.** Re-read every new ticket against the open and recently-closed sets. Five
minutes; it would have caught two duplicate pairs in one session.

---

## Cost discipline

**If closeout starts taking longer than the round it follows, cut it — and name what was cut**, so the
deletion is visible rather than quiet.

---

# The standing Fable brief

**Above the week's specific questions, every mandate:**

> The goal is to set work running and walk away. Every interruption is a defect in the system, not a
> property of the work. Audit the last week for every point at which the founder had to be at a
> screen, classify each, and propose the removal.

Categories: permission prompts · judgment questions · routing · sensing · genuine escalation.

**Weekly deliverable:** count by category, the largest, and **one** concrete change with the best
ratio.

**The counter-question, and it stands:** the founder personally caught a false tooling-bug claim, two
wrongly-ordered closures, an over-broad archive instruction, and a wrong league size. He is still the
most reliable error detector here. **Say what replaces him before recommending his removal.** The
threshold is not zero interruptions — it is zero interruptions plus a detector that has caught planted
faults.
