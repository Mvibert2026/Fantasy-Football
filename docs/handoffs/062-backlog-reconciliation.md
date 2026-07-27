---
ID: 062
FROM: pm
TO: librarian
STATUS: OPEN
OPENED: 2026-07-27
---

## RETRACTION — read first

An earlier committed version of this thread claimed `tools/handoffs.py sync` was silently truncating
`OPEN.md` to 12 of 63 threads. **That was false and is withdrawn.** The PM read a stale cached copy
over the device bridge and treated it as current. The founder verified directly: 64 threads, `check`
clean, `sync` clean. **There is no sync bug. Do not investigate one.**

---

## Scope discipline for this thread

Founder instruction, and it governs everything below:

> "These systems are supposed to be enablers, not bottlenecks, and take effort away from product
> work."

An earlier draft of this thread asked for eight new checks, a protocol amendment, a frontmatter policy
and a cadence ritual. **That was process for its own sake and it has been cut.**

**The test every item here had to pass:** name a failure that has *actually occurred* in this project,
and cost less to prevent than the failure cost. Two items passed. Everything else was dropped and is
listed at the bottom so it is not silently reintroduced.

---

## Part 1 — the one-off pass (do this once, then it is done)

Reconcile the backlog. Timebox it; a good-enough pass today beats a perfect one next week.

**Suspected overlaps — verify, do not trust.** Written by the PM, who created most of them:

| Threads | Overlap |
|---|---|
| **044** / **059** | 059's addendum absorbs 044's intent. |
| **045** / **059** / **060** | Forward simulation, split three ways — legitimately, or not. |
| **049** / **058** | Two draft-board gap lists against the same design. **Highest risk.** |
| **051** / **058** / **063** | Same screen; 063 reopens 051. |
| **027** / **028** / **059** | 059 lives inside 028's unbuilt tab. |
| **046** / **048** / Fable mandate Pt 3 | Mandate may supersede 048. |
| **054** / **055** / **057** | Same data-source questions, written an hour apart. |
| **021** / Fable mandate B3 | Same rank-correlation defect. |

Also cross-check open threads against the **nine decisions settled 2026-07-27**
(`docs/decisions-needed.md`). Threads predating them may describe work that should no longer happen.

**Output:** one disposition per open thread — `KEEP` / `MERGE INTO <id>` / `CLOSE — done` /
`CLOSE — superseded` / `ESCALATE — contradiction`. **Recommend; do not execute.** Contradictions go to
the PM.

## Part 2 — the one check worth keeping

**Contradiction detection, and nothing else.**

It earns its place because it is the only failure here that destroys work rather than wasting it: one
agent removing what another just built, both correctly following instructions. It has already happened
— 049 asked to remove randomised suggester order while RETROFIT-5 asked to add it, same round. Caught
by luck.

Implementation, deliberately crude:

- Flag two open threads naming the same file or component with opposing verbs — add/remove, show/hide,
  enable/disable, randomise/order.
- Flag an open thread referencing a `D-` number already DECIDED.

False positives are fine. A false positive costs a glance; a false negative costs a round.

**One fixture, non-negotiable:** the 049 / RETROFIT-5 pair, as a known-positive test. Without it there
is no way to tell a working detector from one that silently flags nothing, and "the check passed"
becomes the most dangerous string in the tooling.

Runs inside existing `check`. **No new command, no new ritual, no protocol amendment.**

## Explicitly cut — do not reintroduce without evidence

Dropped because no failure has occurred to justify them: file-boundary overlap matrix, duplicate
detection by title similarity, re-request-of-resolved detection, `OPEN.md` staleness assertion,
backlog-size tripwire, frontmatter policy enforcement, and a reconciliation step in `README.md`.

Several are good ideas. None has cost anything yet. If one of them bites, it gets built then, with the
incident as its justification.

**The PM will stop inventing frontmatter keys** (`DEPENDS ON:`, `REOPENS:`, `BLOCKED ON:`). That is a
behaviour change costing nothing, and it removes the need for the policy that was cut.

## Done looks like

`docs/handoffs/RECONCILIATION-2026-07.md` with a disposition per thread and a short contradiction list
for the PM. The contradiction check inside `check`, with its fixture. Nothing else.

Report open-thread count before and after.

**File boundary:** `docs/handoffs/`, `tools/handoffs.py`.

---

## Part 3 — `docs/` is cluttered, and most of it is mine from today

Added 2026-07-27 after a directory review. Same owner, same boundary, so it belongs here rather
than in a new thread.

**Seven Fable files exist; one is current.**

| File | Disposition |
|---|---|
| `fable-mandate-extended-2026-07-27.md` | **CURRENT** — the one that ran. |
| `fable-mandate-2026-07-27.md` | Superseded (session 1 ran it; keep as the historical record of what was asked). |
| `fable-mandate-2-rankings-2026-07-27.md` | **Never ran.** Its questions were answered by session 1. Delete or mark superseded. |
| `fable-mandate-3-ranking-design.md` | **Never ran standalone** — folded into the extended mandate. Delete or mark superseded. |
| `fable-scope-2026-07-27.md` | Superseded twice over. |
| `fable-briefing.md`, `fable-prompt.md` | Pre-date all of the above. |

**Do not delete silently.** Either move superseded mandates to `docs/archive/` or stamp a one-line
`SUPERSEDED BY <file>` header at the top of each. A future reader picking up
`fable-mandate-2-rankings` and running it would waste an entire budget on already-answered
questions — that is the concrete failure this prevents.

**Other structural items, in order of risk:**

1. **`frontend/src/` holds a byte-identical dead copy of the backend Python tree** — 26 files,
   subtree residue, imported by nothing (Fable, pre-mortem failure #11). An urgent edit in the wrong
   tree silently does nothing. **Delete it, or stamp a README in it.** This is the highest-risk item
   here and it is one commit.
2. **Three agent worktrees carry stale copies** under `.claude/worktrees/`. Audit which are live;
   `fable/ext-2026-07-27` is deliberate and must survive.
3. **Two decision documents** — `decisions.md` (112 KB) and `decisions-needed.md` (34 KB), plus
   `assistant-context.md` already warns that `decisions.md` is a reading hazard. State which is
   canonical in both files' headers.
4. **Two state documents** — `CURRENT-STATE.md` and `SNAPSHOT-2026-07-27.md`. `CURRENT-STATE.md` is
   canonical and says so; the snapshot should say it is a point-in-time capture, not a rival.
5. **Three process documents** — `operating-model.md`, `pm-operating-discipline.md`,
   `session-reset-protocol.md`. Not duplicates, but nothing says how they relate. One cross-reference
   line in each.

## Part 4 — withdraw the ≥100 ID rule

**The PM's "PM allocates from 100 up" rule is withdrawn.** Fable established it is structurally
broken: `tools/handoffs.py` allocates `max(all IDs) + 1`, so the first PM thread at 100 pushes every
subsequent agent thread into the PM's range. It would have made collisions worse.

Fable also found collisions ran **four deep in ~24 hours** across two namespaces (threads 043, 049,
053; ADR-048) — endemic, not the one-off the PM described.

**Until W1/W2 land** (slug-authored threads with IDs assigned at sync — authorized on Fable's branch,
not started), the interim rule is behavioural and unglamorous: **the PM lists the directory
immediately before writing, uses the next sequential ID, and never force-writes to a path it did not
create.** Report duplicate IDs found and name the surviving thread in each case.

---
### backend · 2026-07-27

W1, W2, and Part 2's contradiction detector are landed (thread 065 routed the build task here; full
reply with declined-scope detail is on that thread). Reporting per this thread's own note in 065
("Report open-thread count before and after" / commit hash and test count belong on 062).

**Commit `78a278b`. Full test suite: 528 passed** (13 new in `tests/test_handoffs.py`).

- **Part 1 (backlog reconciliation) and Part 3 (docs/ clutter) are not this reply's concern** —
  those are `docs/handoffs/` thread-content and doc-cleanup territory a librarian session is working
  concurrently (per this session's task boundary); not touched here.
- **Part 2, built to spec, nothing from 065's expanded ask:** antonym-verb collision on a shared
  file/component (`add/remove`, `show/hide`, `enable/disable`, `randomise|randomize/order`), and an
  open thread citing a `D-` number already marked `DECIDED`. The four items 065 additionally asked
  for — backlog-size tripwire, re-request-of-resolved detection, `OPEN.md` staleness failure,
  `README.md` ritual amendment — are this thread's own "Explicitly cut" list, verbatim, and were not
  built. Runs inside `check`, no new command.
- **One correction to the non-negotiable fixture's label, verified against the actual thread files
  rather than taken on trust:** the real 2026-07-27 randomised-suggester-order contradiction is
  thread **051** ("Remove the order randomisation — show BPA order") vs. thread **036**
  (`036-mocklab-staleness-retrofit.md`, where RETROFIT-5's order-randomisation back-port was
  actually built), not thread 049. 049 collided with an unrelated 043 over its filename this same
  round and was renumbered to 051 (see `049-draft-mode-gap-list.md`'s own first reply).
  `docs/handoffs/RECONCILIATION-2026-07.md` Part 2 reaches the same correction independently.
  `tests/test_handoffs.py::test_known_positive_randomised_suggester_order_pair` reconstructs 036 vs
  051 from the real files and asserts the pair flags — this is the required known-positive, run
  against actual thread content, not a synthetic fixture standing in for it.
  `test_known_negative_027_028_do_not_flag` is the required known-negative.
- **Design choice worth flagging:** contradiction flags print inside `check` as non-fatal warnings,
  not build failures. The live mailbox already contains open threads that correctly cite an
  already-`DECIDED` D-number (e.g. 055 citing "D-021 is DECIDED: loosen") — a hard failure there
  would fail the build on normal, correct threads, which is the opposite of "enablers, not
  bottlenecks." False positives cost a glance; a glance requires the suite to still be green.
- Also in this commit, since it was named as part of W1's scope in the review: the "PM allocates
  from 100 up" rule in `docs/handoffs/RECONCILIATION-2026-07.md` is marked superseded (append only,
  original text untouched), `docs/handoffs/README.md`'s role list is corrected to match
  `tools/handoffs.py`'s `ROLES`, and `docs/pm-outbox/` now exists as the PM's only write surface.

Not setting this thread's `STATUS:` — 062 is addressed `TO: librarian` and this reply doesn't change
that disposition; librarian's own pass stays authoritative for Parts 1/3.
