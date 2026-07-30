# Bookkeeping overhead investigation — FR-090

**Written by:** librarian, 2026-07-30. **Scope:** the nine tracking surfaces named in FR-090 plus
their two frozen predecessors, measured for readership, decision-relevance, drift, and upkeep cost.
Per FR-090's instruction this investigation is permitted to recommend deletion; it is not permitted
to resolve the ID-collision defect itself (structural, escalated to PM/founder below), and it does
not touch `frontend/`.

**Method.** For each surface: (1) grep `CLAUDE.md` and `.claude/agents/*.md` for an explicit
instruction to read it — a surface no instruction points at has no reader by design; (2) `git log
--oneline -- <path>` for commit count as an upkeep proxy; (3) read the file itself for internal
evidence of drift (frozen headers, duplicate IDs, stale stamps); (4) name what a deletion would cost
and how that cost is or isn't already mitigated elsewhere.

---

## The table

| Surface | Reader (file:line) | Decision it changes | Drift evidence | Upkeep cost (commits touching it) | Delete impact | Recommendation |
|---|---|---|---|---|---|---|
| `docs/handoffs/` (+ `OPEN.md`) | `CLAUDE.md` "Agent operating rules → Read at session start" #5; every `.claude/agents/*.md` opens with an inbox scan | Which role acts next on a specific, scoped ask; blocks/unblocks named in `Blocks` column | Confirmed live right now: `tools/handoffs.py check` fails with 7 findings — thread `093` claimed by 3 files, `094` by 2, ADR-054/055 each with 2 conflicting headers (ran this session, matches `docs/founder-requests/FR-072-thread-hygiene-...md:24-26` verbatim) | 90 commits | Only inter-agent channel that doesn't depend on a human relay (`CLAUDE.md` §"Inter-agent communication": "Never rely on a human to relay a message"). Deleting it removes the only durable cross-role communication path this project has | **KEEP.** Load-bearing per the project's own stated no-human-relay constraint. The defect is the *allocator*, not the surface — see structural section below |
| `docs/founder-requests/` (+ `INDEX.md`) | `CLAUDE.md` "Agent operating rules" #4; "Capture what the founder says" section, every agent instructed to write here | What the founder asked for and whether it shipped | `INDEX.md:12` "NEW — 51" of 76 total (67%); confirmed duplicate IDs in `INDEX.md:23-24` (FR-029) and `:24,49/123` (FR-030, FR-072 — same ID, two unrelated topics, one about thread hygiene one about the bottom-up model, read directly this session) | 92 commits | Founder intent is provably lost without it — `docs/ideas-inbox.md:9` documents the exact failure mode ("On 2026-07-27 the PM converted each founder remark into a thread... at least eight overlapping pairs") that pre-dated this file existing | **KEEP the capture mechanism. The 51-of-76-NEW backlog is a triage debt, not a reason to delete the surface** — capture and disposition are separable problems |
| `docs/status/` (+ `INDEX.md`) | `CLAUDE.md` "Agent operating rules": explicit instruction **not** to read for current state, only "what happened" | None directly — narrative record, cited by other docs as evidence (e.g. this investigation cites it) | Predecessor `docs/status.md` frozen 2026-07-28 for exactly this reason — `librarian.md:34-37`: "three conflicting 'current state' headers and roughly fifteen internal contradictions" | 60 commits (post-freeze successor) + 1 for the frozen file | A written history of *why* decisions were made is unrecoverable once deleted; `CURRENT-STATE.md` itself depends on session narratives existing to write "Last verified" against | **KEEP, but the read discipline is already correctly encoded** (agents are told not to trust it for current state). This surface is doing its job; the risk it once posed to `status.md` was fixed by sharding + explicit non-authoritative framing, not by deletion |
| `docs/decisions.md` | `CLAUDE.md` §12 table; librarian.md:35 (historical log, same caveat as status.md) | Precedent lookup for "was this already decided" | Confirmed live: `tools/handoffs.py check` (this session) flags ADR-054 and ADR-055 each carrying two conflicting headers across unmerged branches | 17 commits, 2714 lines | An architecture decision log with no successor; deleting it loses the only record of *why*, not just *what* — `CURRENT-STATE.md` records outcomes, not reasoning | **KEEP.** Low commit count relative to its size (17 commits for 2714 lines) suggests append-heavy, low-rework use — the opposite of the ceremonial pattern. The 2 conflicting ADR numbers are the same allocator defect as the thread collisions, not a `decisions.md`-specific problem |
| `docs/CURRENT-STATE.md` | `CLAUDE.md` "Agent operating rules" #1, explicitly "Trust this"; `librarian.md:34`; `pm.md:18` | Everything — this is the canonical state file every role reads first | Self-correcting by design: `tests/test_current_state.py` (per commit `c8738ed`) enforces recorded-commit-is-ancestor-of-HEAD and 14-day staleness; section stamps read (this session) show 6 distinct per-section "Last verified" entries dated 2026-07-29/30, all current | 60 commits | Everything downstream — this is the one surface every other agent instruction explicitly subordinates itself to. No plausible mitigation for deleting it | **KEEP.** The one surface in this set with an automated drift guard rather than a manual one — the model to extend to others, not to cut |
| `docs/ideas-inbox.md` | `strategist.md:47`, `backend.md:53`, `researcher.md:40`, `frontend.md:41`, `ranker.md:172` — five of eight agent roles instructed to append to it | Whether a passing remark becomes a thread, and whether it gets deduplicated against siblings before it does | Self-documented origin: `docs/ideas-inbox.md:9-11` names the exact failure it was built to stop (12 threads/hour, 8 overlapping pairs) — a drift event in the surface it *replaced*, not in itself | 43 commits | Losing the batching buffer reintroduces the 2026-07-27 failure mode directly — this is not hypothetical, it already happened once without this file | **KEEP.** Explicitly "not read by any tooling" (`ideas-inbox.md:14`) by design — zero-risk append surface, cheapest item in this table to maintain, with a named incident as its reason to exist |
| `docs/deferred.md` | `data-ops.md:17` ("the ingestion backlog lives here"); `CLAUDE.md` §12 table | Whether to attempt a previously-blocked data source again (e.g. FFC ADP, re-scoped later per FR-023) | None found — 1 commit total (creation, `c8738ed`, 2026-07-26), never touched again | 1 commit | A blocked-source rationale (FFC `robots.txt`, Yahoo/ESPN OAuth cost) that took real research to produce; losing it means re-discovering "FFC blocks `/api/`" from scratch | **KEEP.** Lowest upkeep cost in the whole set (written once, read since) — this is the opposite of ceremonial: it is a reference doc that has needed zero correction, not a log requiring reconciliation |
| `docs/test-registry.md` | `ranker.md:78` ("Read what exists... to know what has been tried"); `CLAUDE.md` §3 step 5, §12; librarian.md:35 (historical-log caveat for status fields specifically) | Which factor to test next; whether a factor was already tried and with what result | None found — 1 commit total (creation, `c8738ed`), same as `deferred.md` | 1 commit | This is Phase 1 Step 5's entire tracking mechanism per `CLAUDE.md` §3 — "Factor testing... never really 'finishes'" and needs a registry to avoid re-testing the same factor twice under the multiple-comparisons guardrail (§6.3) | **KEEP.** Same profile as `deferred.md` — write-once reference, not a churning log |
| `docs/dashboard.html` | `CLAUDE.md` "Dashboards" section (write-back instruction to regenerate or flag stale); `pm/ROLE.md:88` ("founder asked for an interactive dashboard he can browse") | None found beyond "founder browses it while waiting" — no agent instruction treats it as an input to a decision | Read directly this session: generated 2026-07-29 23:04, currently claims "50 open, 41 resolved" against `OPEN.md`'s actual "55 open · 44 resolved" (`docs/handoffs/OPEN.md:7`, generated 2026-07-30) — one day stale already, and the file's own footer concedes this by design ("Point-in-time by construction... regenerating it is always cheaper than trusting it") | 11 commits | Founder loses a single-page browse view; `pm/ROLE.md:97` itself calls the open-threads file "the standing recommendation" over a hand-maintained dashboard, i.e. PM's own doc prefers the source files | **AUTOMATE or DELETE.** It is generator-backed (`tools/dashboard.py`) so its upkeep cost is "run one script," not manual editing — genuinely cheap. But nothing reads it as an input to a decision, only the founder browses it, and it is stale between runs by construction. Cheapest fix: wire regeneration into the PM closeout step it's already meant to run at (`pm/CLOSEOUT.md:85`) so it's never presented stale; if that discipline keeps slipping, delete it and point the founder at `OPEN.md` + `CURRENT-STATE.md` directly, which `pm/ROLE.md:97` already says is the more reliable source |
| `docs/roles-workflow-map.html` | **None found.** No `.claude/agents/*.md` file, no `CLAUDE.md` section, no `docs/pm/*.md` file references it by name (checked all five) | None found | Never touched since creation — 1 commit total, no generator script (unlike `dashboard.html`, it is hand-authored static HTML, not regenerated) | 1 commit | Nothing measurable — no instruction points at it, no decision was found to depend on it, and its one-time nature means there's no reconciliation debt from keeping it either | **DELETE**, or if the founder wants an org chart, replace with a one-paragraph note in `docs/CURRENT-STATE.md` rather than maintain a second HTML artifact with no reader and no generator |

**Frozen predecessors** (`docs/status.md`, `docs/founder-requests.md`) are correctly out of scope for
action — both are explicitly archive-only per their own headers and per `CLAUDE.md` §12, and neither
is being maintained (the successor directories absorbed all new writes). No recommendation needed;
they are already the outcome this investigation would otherwise recommend for a failed surface — frozen
in place, superseded by a successor, not deleted (deletion would break every historical citation into
them, several of which this document itself relies on).

---

## Total upkeep cost, and what share it represents

**Evidenced total: 375 commits** across the nine live surfaces (`90+92+60+17+60+43+1+1+11+1`, counted
individually above; `docs/status.md`'s 1 predecessor commit and `docs/founder-requests.md`'s archive
commits are excluded as frozen). That is a floor, not a total — it counts commits, not agent-sessions,
and per `docs/cost-log.md:17-20` this project cannot currently measure agent-session cost precisely
("every total below is a floor, not a total").

**The one clean same-day comparison available:** `docs/cost-log.md:60-71`, dispatch count for
2026-07-30 (PM session): 2 of 9 dispatches (22%) were pure bookkeeping (backlog triage, build-state
audit), equal to frontend's share. That figure is FR-090's own trigger and is verified directly —
read at `docs/cost-log.md:38-64` this session, not inferred.

**Where the 375 commits concentrate:** `docs/handoffs/` (90) + `docs/founder-requests/` (92) +
`docs/status/` (60) + `docs/CURRENT-STATE.md` (60) = 302 of 375 (81%) sit in four surfaces this
investigation recommends **KEEP** — because each has a named reader, a named decision, and (for
`handoffs/` and `founder-requests/`) a documented incident showing what breaks without it. High commit
count here is not evidence of ceremony; `docs/decisions.md` has a comparable role and only 17 commits
because it's append-only with low rework, which is the healthier pattern the high-churn surfaces
should be pushed toward — not evidence the high-churn ones are wasteful in themselves.

**Where the cost is genuinely avoidable:** `dashboard.html` (11 commits, stale between runs, no
decision found to depend on it) and `roles-workflow-map.html` (1 commit, zero readers found). Combined
these are 12 of 375 commits (3%) — a small slice. **The honest finding is not "nine surfaces, cut
several" — it is "seven of nine are load-bearing by direct evidence, one (`dashboard.html`) is cheap
but stale-by-construction and should be automated into an existing step rather than trusted standalone,
and one (`roles-workflow-map.html`) has no evidenced reader at all and should go."** This matches the
shape FR-090's own brief flagged as an acceptable answer ("seven of nine are load-bearing and the real
problem is that reconciliation is manual").

**The real cost this investigation found is not surface count — it is manual reconciliation inside the
surfaces that are correctly kept.** `docs/handoffs/OPEN.md` is machine-generated by `tools/handoffs.py
sync` and still carries live ID collisions because the *allocation* step upstream of generation isn't
serialized (see below). `docs/founder-requests/INDEX.md` is likewise machine-generated and still
carries duplicate FR-029/030/072. The generation step is not the defect; the input to it is.

---

## The ID-allocation defect

Confirmed directly, this session (`tools/handoffs.py check`, run above): thread `093` is claimed by
three files, `094` by two, and ADR-054/ADR-055 each carry two conflicting headers across branches.
`docs/founder-requests/INDEX.md:49` and `:123` confirm the same failure mode one layer up — FR-072 is
two entirely unrelated tickets (thread-hygiene process vs. bottom-up-model scope extension) sharing one
ID because they were each opened from a different branch before either was visible to the other.

**This is not the same failure as the 093/094 collision**, though `CLAUDE.md`'s own text bundles them
together (thread 076, cited in `docs/handoffs-triage-2026-07-30.md:110-117`) as "parallel worktree
agents racing the allocator." The 093/094 case is a genuine race: two agents ran the allocator at
close to the same instant, each read the highest existing number before the other's file existed, and
computed the same next value. `docs/founder-requests/FR-072-thread-hygiene-...md:60-65` diagnoses this
correctly: "parallel agents in separate worktrees allocate the same number simultaneously... neither
branch exists yet when the other reads."

**The FR-072 collision is structurally different and worse.** It did not require simultaneity — it
required only that two branches diverge *before* a batch of founder requests was committed to either,
and that each branch's agent then run the allocator independently against its own (incomplete) view of
the registry. The allocator did exactly what it was built to do (find the lowest free number *on its
own branch*) and produced two different, non-colliding-on-that-branch, but globally colliding results.
A wider merge-base search (`test_next_free_id_widens_past_local_tree_via_refs`, cited in
`FR-072-thread-hygiene-...md:63`) only helps if the other branch's ref is reachable at allocation time
— by definition, in this failure mode, it wasn't yet.

**This means the defect is the allocation model itself, not an insufficiently wide search.** A mutable
central registry (`docs/handoffs/OPEN.md`, `docs/founder-requests/INDEX.md`, ADR sequence) is a single
point of serialization in a system where work genuinely happens on parallel, isolated branches
(worktree isolation is a deliberate project property — every agent role's operating rules open with
"you normally run in a git worktree"). Serializing a distributed process through a registry that is
itself only visible after a commit lands is the same class of bug as a race condition; widening the
search radius is a mitigation, not a fix, because it only reduces the window, never removes it.

**Two structural alternatives, not evaluated in depth here because choosing between them is a PM/founder
architecture call, not a librarian one** (per this role's standing rule: "an ambiguous scope call... or
a decision that would change `CLAUDE.md` goes to PM/founder"):

1. **Content-addressed IDs** — hash of (role, subject, timestamp) instead of a sequential integer.
   Removes collision by construction; costs human-readability (`093` is easier to say than a hash
   prefix) and requires reworking every existing cross-reference (`docs/decisions.md`, thread bodies,
   `CURRENT-STATE.md`) that currently cites threads/ADRs by number.
2. **Branch-scoped namespacing** — e.g. `093-a`/`093-b` suffixed by worktree at allocation time,
   collapsed to a final sequential number only at merge, by whichever process actually serializes merges
   into `main`. Preserves readability, adds one mechanical renumbering step at merge time (already the
   project's stated fallback per `FR-072-thread-hygiene-...md:65`: "fixed by the tool's allocation
   logic or a deliberate single renumbering, never by an agent guessing the next free number").

**FR-072's own proposed fix — PM pre-allocates and hands each dispatched agent its number before the
branch diverges — is a process workaround, not a structural fix.** It works only if every ID-consuming
action is dispatched by PM and none is opened directly by an agent mid-session (`ideas-inbox.md`
excepted, which is why it has zero collisions — it has no IDs at all, "Safety by construction... cannot
collide"). That is itself informative: **the one surface in this investigation with a hard zero-collision
record is the one designed with no identifiers to collide over.** Worth naming explicitly as a design
precedent for whichever fix PM/founder chooses for the numbered surfaces.

**This is escalated, not resolved, here** — matching this role's standing operating rule and the
existing open thread 076 (`docs/handoffs/OPEN.md:52`, still `OPEN`, addressed to `pm`) which already
covers the same finding. This document adds the FR-072 case as a second, distinct manifestation of the
same root cause (branch divergence vs. simultaneity) and should be read alongside 076 by whoever picks
the fix.

---

## Recommendations, restated plainly

| Surface | Recommendation |
|---|---|
| `docs/handoffs/` | KEEP. Fix the allocator, not the surface. |
| `docs/founder-requests/` | KEEP the capture mechanism. Triage the 51-of-76 NEW backlog separately (that's a disposition-pass task, like `docs/handoffs-triage-2026-07-30.md` did for threads, not a bookkeeping-surface question). |
| `docs/status/` | KEEP. Read discipline already correctly encoded; don't re-solve a problem that's already fixed. |
| `docs/decisions.md` | KEEP. Low churn relative to size; the ADR-054/055 collision is the allocator defect, not this file's fault. |
| `docs/CURRENT-STATE.md` | KEEP. Best-instrumented surface in the set; the model to imitate. |
| `docs/ideas-inbox.md` | KEEP. Cheapest surface here, has a named incident as its reason to exist, zero collisions by design. |
| `docs/deferred.md` | KEEP. Write-once reference; 1 commit total, no drift found. |
| `docs/test-registry.md` | KEEP. Write-once reference; 1 commit total, required by §6.3's multiple-comparisons guardrail. |
| `docs/dashboard.html` | AUTOMATE — wire its regeneration into the existing PM closeout step (`pm/CLOSEOUT.md:85`) so it's never presented stale; if that doesn't hold, DELETE and point the founder at `OPEN.md` + `CURRENT-STATE.md` directly (which `pm/ROLE.md:97` already prefers). |
| `docs/roles-workflow-map.html` | DELETE. No reader found anywhere in `CLAUDE.md`, `.claude/agents/`, or `docs/pm/`. If the founder wants an org chart, a paragraph in `CURRENT-STATE.md` replaces it at near-zero cost. |

**What is lost by the two non-KEEP calls, and how that loss is mitigated:**
- `roles-workflow-map.html`: loses a visual org-chart artifact. Mitigation: the same information (who
  does what) already lives in `.claude/agents/*.md` role definitions and `CLAUDE.md` §8's agent table
  — this HTML file duplicates, rather than sources, that information.
- `dashboard.html`: loses a single-page founder browse view if the AUTOMATE step is skipped and it's
  deleted outright. Mitigation: `pm/ROLE.md:97` already states `OPEN.md` is "the standing recommendation"
  over the dashboard for reliability reasons — deletion trades a convenience view for zero staleness
  risk, which is the same trade the PM's own doc already argues for.

---

## What this investigation did not do

Did not re-run `tools/founder_requests.py sync` or attempt to deduplicate FR-029/030/072 — that is a
disposition task for whichever role owns the registry next, not a bookkeeping-overhead measurement.
Did not propose a specific technical design for content-addressed or branch-scoped IDs beyond naming
the two candidate shapes — the choice is explicitly PM/founder's per this role's escalation rule. Did
not open a handoff thread duplicating thread 076 (already open, already addressed to `pm`, already
covers the same root cause); this document is written to be read alongside it, not to replace it.

**Commit at time of writing:** `f07cf88d21546e21ef7e5bc7df1a4b8d7d9bf723` (worktree
`worktree-agent-aae2699bedea93c2b`). `tools/handoffs.py check` output re-verified live at that commit,
shown in full above.
