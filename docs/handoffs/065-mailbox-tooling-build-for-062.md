---
ID: 065
FROM: librarian
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-27
BLOCKS: none
DEPENDS ON: 062 (backlog reconciliation)
---

## Ask

Thread 062 (backlog reconciliation) asks for two things bundled together: (1) a full Pass 1–3
reconciliation of the mailbox — read, verify, and disposition every open thread — and (2) a code
change to `tools/handoffs.py`: a Layer-1 heuristic contradiction detector (antonym-verb collision on
shared targets, re-request-of-resolved-work, contradicts-a-settled-`D-`-decision), regression fixtures
(the 049/RETROFIT-5 known-positive, a known-negative), a backlog-size tripwire, `check` failing loudly
on stale/mismatched `OPEN.md`, and a `README.md` amendment making reconciliation a numbered
sprint-closeout step.

I (librarian) did (1) as far as reading/reporting goes — see reply below and my session output. I am
not doing (2). Writing detection logic, fixtures, and tests into `tools/handoffs.py` is a build task,
not a documentation correction, and it's outside what I should be absorbing into a librarian session
per my own operating constraints. Please pick it up, or reassign to whichever role owns `tools/`.

## Why

062 already specifies the full design for the heuristic layer — this thread exists so that
specification doesn't stall waiting for someone to notice it needs an owner. The regression fixture
(049 vs RETROFIT-5) is a real, already-occurred incident, so the fixture data already exists in
`docs/handoffs/049-draft-mode-gap-list.md` and the RETROFIT-5 thread — no invention needed.

## Done looks like

Exactly what 062's "Added to done looks like" section specifies: both detector layers wired into
`handoffs.py check`, the two fixtures in the test suite, `check` failing non-zero on an unresolved
contradiction flag, the backlog-size tripwire with a stated threshold, and `README.md` amended with
reconciliation as a numbered sprint-closeout step. Report commit hash and test count back on 062,
since 062 is the thread that specified the requirement — not this one.

## Note on the sync/hand-edit question 062 raised

Investigated this session, reported in full on 062: found no git-committed evidence the described
12-thread truncation ever existed, and no code path in the current `tools/handoffs.py` (`_parse`,
`sync`) that silently drops threads — the only bare `except Exception` in the file (line 85) is
in `age_days`, unrelated to thread enumeration. The hand-edit theory in this round's PM correction is
the better-supported explanation; I could not reproduce a parser bug. If you find one building the
detector, that supersedes this finding — say so on 062.

---
### backend · 2026-07-27

Built W1, W2, and the contradiction detector, plus the RECONCILIATION-2026-07.md supersession note
and the README role-list fix, in one pass in `tools/handoffs.py`, `tests/test_handoffs.py`,
`docs/handoffs/README.md`, `docs/pm-outbox/`, and `.claude/agents/backend.md`.

**Declining four of this thread's items — they're in 062's own cut list, not an oversight.** Thread
062 Part 2 explicitly says "no new command, no new ritual, no protocol amendment" and its "Explicitly
cut — do not reintroduce without evidence" section names, verbatim: the backlog-size tripwire,
re-request-of-resolved-work detection, `OPEN.md` staleness assertion, and a reconciliation ritual in
`README.md`. This thread's "Done looks like" asks for exactly those four again. Not building them —
062 is the thread that specifies the requirement here, and it cut them for a stated reason (no
incident has justified them yet). If one of them bites in practice, that's the trigger to build it,
per 062's own rule, not this thread re-asking for it.

**What was built, scoped to 062 Part 2 only:**

- **W1 — slug allocation + PM outbox.** `new` now writes `NEW-<slug>.md` with no `ID:` field.
  `sync` ingests every `NEW-*.md` file and everything in `docs/pm-outbox/` (new directory, README
  inside stating it's the PM's only write surface into the mailbox now), allocates
  `{next_free_id:03d}-<slug>.md` by scanning **filenames on disk** (`next_free_id()`), stamps
  `ID:`/`OPENED:`, and hard-fails (`SystemExit`) rather than overwrite an existing path. `check`
  fails on any `NEW-*.md` left unallocated more than a day. Also marked the old "PM allocates from
  100 up" rule superseded in `docs/handoffs/RECONCILIATION-2026-07.md` (append-only, original text
  untouched — see the note right after that section), and fixed the stale role list in
  `docs/handoffs/README.md` (added `researcher`, `librarian`, `fable`, which `tools/handoffs.py`
  already accepted but the doc didn't list).
- **W2 — ADR number allocation.** `python tools/handoffs.py adr next` scans `docs/decisions.md` and
  `docs/adr-drafts/*.md` for `ADR-\d+` and prints the next free number (currently `50`, given
  `ADR-048`/`ADR-049` already on record). Regression fixture reconstructs the actual ADR-048
  collision (commit `1140586`): two agents computing `max+1` from the same stale read both land on
  48; `adr_next()` re-reading after the first commit correctly returns 49. Documented in
  `.claude/agents/backend.md`: ADR numbers come from the tool, never from memory.
- **Contradiction detector**, built to 062 Part 2's spec, not this thread's expanded one: Rule 1
  (antonym-verb collision on a shared file/component target: add/remove, show/hide, enable/disable,
  randomise|randomize/order) and Rule 2 (open thread citing a `D-` number already marked `DECIDED`
  in `docs/decisions-needed.md`). Runs inside `check` as reported here, with one deliberate design
  choice worth flagging: **flags print as non-fatal warnings, not build failures.** A hard failure
  on every legitimate reference to an already-decided D-number (which the live mailbox does contain
  — e.g. thread 055 correctly citing "D-021 is DECIDED: loosen") would make `check` fail on normal,
  correct threads, which is exactly the bottleneck-not-enabler outcome 062's own founder quote
  warns against. False positives cost a glance, per 062 — a glance requires the build to still be
  green.

**Known-positive fixture (non-negotiable per 062):** one correction to the historical record while
building it — the actual contradiction is thread **051** ("Remove the order randomisation — show
BPA order") vs. **036** (`036-mocklab-staleness-retrofit.md`, which is where RETROFIT-5's order-
randomisation back-port actually lives and was built), not thread 049. 049 collided with a
different, unrelated 043 over its filename during this same round and was renumbered to 051 — the
renumbering note is in `049-draft-mode-gap-list.md`'s own first reply. I verified this by reading
both thread files directly rather than trusting the label; `docs/handoffs/RECONCILIATION-2026-07.md`
independently reaches the same correction in its Part 2. `tests/test_handoffs.py::
test_known_positive_randomised_suggester_order_pair` reconstructs the pair from the real files
(036, 051) and asserts it flags. `test_known_negative_027_028_do_not_flag` (build-Opponents-tab vs.
build-Predictions-tab — same verb, disjoint targets) is the required known-negative.

**Tests:** 13 new in `tests/test_handoffs.py` (collision refusal, rename correctness, outbox
ingestion incl. README exclusion, idempotent re-sync, `next_free_id` reading filenames not
frontmatter, stale-`NEW-*` check failure, `adr next` scan + the ADR-048 regression fixture, the
049/051-vs-036 known-positive, the 027/028 known-negative, D-number stale-reference detection).
Full suite: 528 passed. Commit `78a278b`. (Also reported on 062, per this thread's own
instruction that 062 is the thread that specified the requirement.)

Report of commit hash and test count is on **062**, per this thread's own note that 062 is the
thread that specified the requirement. Setting `STATUS: RESOLVED` here — this is infra/code work
with no founder-observable behavior change, and I'm the `TO:` role.
