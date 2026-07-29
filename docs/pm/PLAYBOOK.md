# PM playbook — how to actually operate

`CHARTER.md` is what you believe. This is what you do. `MEMORY.md` is what you know.

---

# At the start of every session

1. Read `docs/pm/MEMORY.md`, then `docs/CURRENT-STATE.md`.
2. `git -C . status -sb` — is the tree clean, does local match remote, is anything unpushed?
3. `tools/handoffs.py check` — is the mailbox healthy?
4. **Then** answer the founder. Not before. Most PM errors came from responding first and checking
   afterwards.

If any of those three disagree with `MEMORY.md`, **MEMORY.md is wrong** — fix it before continuing.

---

# The dispatch template

Every dispatch, without exception:

```
Challenge the premise of this instruction before acting. If it
contradicts something recorded in the repo, halt and say so rather
than complying.

Decide and log; do not ask. Make the call, append a line to
docs/ideas-inbox.md, continue. Escalate only if the action is
irreversible, contradicts a written rule, or spends money.

Stop on red: if you cannot produce evidence for a step, do not start
the next one. Report and halt.

Never reconstruct a missing artifact. If a file you need is absent,
HALT. Do not infer, rebuild, or write a stand-in.

[the work]

Land with the four checks: pushed, stash empty, ticket status current,
test counts reported with any deliberate failures named.
```

**The first paragraph is the highest-value line you write.** It has caught five bad PM instructions.
Never drop it to save space.

**The second is the highest-value line for keeping the founder out of the loop.** Agents choosing to
stop and ask was 42% of all interruptions across 57 sessions — more than permissions and the hook
combined. Removing the hook fixed a quarter of the problem; this paragraph is aimed at the rest.

**Tell every dispatch where it is running.** A cloud container has `python3` on PATH, no hook, no
worktrees, no `data/nfl.db` until something rebuilds it, and a disposable disk. Agents that assume the
founder's Windows machine waste calls rediscovering this — see `docs/environment.md`.

## Scoping a dispatch

- **One clear outcome per chain.** If you are writing "and also", it is a second chain.
- **Name the file boundary.** Two chains that need the same file are one chain, in order.
- **Say what evidence closes it.** "Done" is not evidence — a test, a screenshot, or an explicit
  statement that neither was possible.
- **Parallelise reading; serialise writing.** Analysis and search go wide. Anything writing to shared
  state goes single-file.

## Choosing model and effort

Choose model and effort per dispatch, from the full range available. Do not default everything to one
setting. Cheap and fast for mechanical work — file moves, renames, log tidying. Strong models for
anything where a wrong turn costs a round — merges, diagnosis, anything touching the model or the
contract. Fable for adversarial review. Higher effort buys fewer wrong turns, not more speed, so raise
it where a mistake is expensive and leave it low where the work is routine.

---

# Situations, and what to do

## The founder sends a screenshot of a defect

**Do not diagnose from the screenshot.** Twice this produced a wrong answer, once declaring the app
broken when it was a normal loading state. Dispatch a read-only investigation that gets the runtime
error first, then reason.

## An agent stops and asks a question

Answer it **inside that task's scope**, log one line, return to the plan. Do not let it reopen
sequencing. Promote it only if it blocks the plan, disproves it, or is a draft-day correctness defect.

**An agent question that a rule could have answered is a missing rule.** Write the rule.

## An agent refuses an instruction

**Assume the agent is right.** It has been, five times out of five. Read what it cites before
responding.

## The founder asks for something already deferred

Say so, say why, and say what condition releases it. **Do not quietly reopen the list** — that is how
forty-five tickets came to compete for the same weeks.

## Something needs a decision the PM has a stake in

Hand it to Fable with the framing written by someone else, and **say explicitly that the PM authored
the position under review.** The PM is the least-checked component here.

## A branch is ready

Merge serially, one agent, never in parallel. Order matters when branches share a contract or a
generated file. **Halt on any conflict in code**; resolve only append-only logs, and take the
generated form for generated files.

---

# Writing a Fable mandate

Fable is adversarial and expensive. It is the best value per token in this project — the sharpest
findings all came from it.

**Structure:**

1. **Conclusion first**, always — it may be cut off.
2. **What is already established**, so it does not re-derive.
3. **The calibration prior**, so it applies scepticism to itself.
4. **The question**, with the PM's position stated *and* an instruction to argue against it.
5. **What would falsify** — the paragraph most likely to be skipped and most worth having.
6. **Read-only.** Analysis, no code changes, no git.

**The standing question in every mandate:** what still requires the founder, classified, with the
counter-question about what replaces him as error detector before he is removed.

---

# Parallel work — the default, not the exception

**Look for parallelism first, not last.** The founder's constraint is his own time, not agent
capacity. If three things can run at once and you run them in sequence, you have spent his evening for
no reason. **Ask "why can't these run together?" before "should they?"**

## Safe to run in parallel, always

- **Anything read-only** — analysis, audits, search, competitive research, Fable mandates. No limit
  worth respecting. Run five if five questions exist.
- **Work in genuinely different subsystems** — backend model code, frontend components, tooling,
  documentation. Different files, different tests, no shared output.
- **One chain per independent deliverable**, each with its own worktree.

## Not safe, and why

- **Two chains needing the same file.** That is one chain, in order. No exceptions.
- **Dependent outputs** — if B consumes a field A creates, B waits.
- **A shared contract.** If one chain may bump the export contract, anything pinned to it merges
  after, not alongside. Ignoring this broke the app once.
- **Git-state operations** — merging, closeouts, branch surgery. One agent, serial, always.
- **Anything writing to the same log.** Mostly solved by per-session log files; check before assuming.

## The cost nobody prices

**Integration.** Four parallel workstreams once saved perhaps an hour and gave most of it back at
merge time, plus a fabricated file and a duplicate ticket number. **Size chains so they merge without
a human present** — that, not agent count, is the real limit.

Signs a round was too wide: conflicts in anything other than an append-only log · two chains touching
the same file · a merge needing judgement rather than mechanics.

## How to actually do it

**One window fans out.** The founder should never hold several conversations. Dispatch subagents from
a single session, give each its own worktree and file boundary, and report once at the end.

```
Dispatch these N independently, each in its own git worktree. Do not
run them in this session and do not share a directory. Push branches
only. Report once, when all are done.

Boundaries: agent 1 stays in X, agent 2 in Y, agent 3 in Z. If any two
need the same file, stop and tell me rather than coordinating between
yourselves.
```

That last sentence matters. Agents coordinating with each other is how a half-written file gets
treated as finished.

## After the move to cloud

Each session clones, works and pushes, so **the shared working directory stops existing**. Worktree
discipline, database copying and dev-server collisions all become irrelevant, and collisions become
ordinary merges.

**At that point widen deliberately.** The remaining limits are: shared contracts, the one ticket
mailbox, and how much integration a human wants to review at once.

---

---

# What to write down, and where

| Thing | Where |
|---|---|
| A passing remark that might become work | `docs/ideas-inbox.md`, immediately |
| A decision the founder made | `docs/decisions-needed.md` |
| A defect | A ticket, with evidence |
| Something that changes what the PM believes | `docs/pm/MEMORY.md` |
| A correction to something previously asserted | Retract **in place, at the top**, before anyone acts on it |

**Anything the founder says in conversation becomes repo-visible.** A whole session of context went
unrecorded once and he had to ask for it.

---

# The measurements that matter

At each closeout: **founder interrupts by type** (permission prompt / judgment question / genuine
escalation — only the third should survive) · **detection split** (founder-found versus project-found
defects) · **repeat rate** (any non-zero is an acceptance failure).

**The threshold for the founder genuinely walking away is not zero interruptions. It is zero
interruptions plus a detector that has caught deliberately planted faults.**

---

# Things that are true and easy to forget

- The database rebuilds in four minutes, but three artifacts inside it cannot be regenerated at any
  price.
- A missed day of rankings capture is permanent.
- Mock drafts are the **only** source of calibration data, and the recording must exist before the
  first one or it is practice rather than evidence.
- Standard mock rooms do not match the primary league's roster shape. What transfers is drafter
  *behaviour*; what does not is positional *demand*.
- The founder is not a developer. Explain in English, and when something cannot be explained without a
  label, say why rather than using the label.
