# Handoff backlog triage — the 38 threads opened 2026-07-26/27

**Written by:** librarian, 2026-07-30. **Scope:** the 38 open/`BLOCKED-ON-YOU` threads that predate
this session's work (opened 2026-07-26 or 2026-07-27, per `docs/handoffs/OPEN.md`'s age column at
the time of dispatch). The 15 threads opened 2026-07-29/30 are this session's own live work and are
not re-triaged here.

**Nothing in this pass changes any thread's `STATUS:`.** Per `docs/handoffs/README.md`, only the
`TO:` role may set `RESOLVED`, and this is a disposition list for the roles to act on, not an
execution. No file was moved, deleted, or stamped.

**A prior pass already exists** — `docs/handoffs/RECONCILIATION-2026-07.md`, written 2026-07-27/28
by a previous librarian session, and it did real, careful work: it verified the PM's seed
dispositions thread-by-thread against actual file contents rather than trusting them, found real
errors in the PM's framing (e.g. 051 was already `RESOLVED`, not something to close; 045/060 should
not merge), and produced a full disposition table for threads 001–065. **This pass does not repeat
that work — it re-verifies each of its calls against what has happened since**, because four days
and a great deal of shipped work separate that pass from this one, and several of its "KEEP" calls
are now stale on their own premise.

---

## Headline numbers

**53 threads are open. 38 of them predate this session. Of those 38:**

| Disposition | Count | Threads |
|---|---|---|
| **STILL LIVE** | 13 | 001, 007, 036, 045, 054, 056, 060, 066, 067, 068, 070, 071, 076 |
| **DONE, NEVER CLOSED** | 10 | 002, 012, 021, 030, 043, 047, 050, 059, 064, 077 |
| **SUPERSEDED** | 7 | 003, 006, 031, 032, 033, 035, 046 |
| **STALE PREMISE** | 3 | 026, 040, 072 |
| **MIXED** (part done, part still live — see notes) | 4 | 037, 049, 053, 057 |
| **Special case** (deliverable exists, `TO:` role hasn't formally closed it) | 1 | 062 |

**The honest headline for the founder:** of the 38, **10 are fully done and simply never got a
closing reply**, and 4 more are done in the parts that mattered most (037's `<1%` fix, 049's
recommendation panel, 053's FantasyPros ingestion, 057's injury leak-test finding) with only a
smaller remainder genuinely open. **7 are superseded outright** — mostly the assistant-architecture
threads (032/033) and the frontend-unreachable threads (003/006/035), whose entire premise (frontend
in a separate repo, no LLM, no design-sync channel) stopped being true days ago. **3 are stale
premise** — all three tied to the six-state Settings editor spec, which FR-069 (2026-07-30, today)
now proposes replacing with a much simpler "Custom" pane.

**So: of 38, 24 need no further action from anyone** (10 done-unclosed + 7 superseded + 3 stale
premise + the 4 mixed threads' completed portions). **The real remaining backlog from this cohort is
closer to 14 fully-open threads, not 38** — and combined with the 15 threads from this session,
"backlog is ~35, not 53" underclaims it: **the true open count from this cohort alone is nearer 14,
plus whatever open remainder the 4 mixed threads carry.**

---

## STILL LIVE — the ask is real and unmet

**001** — Adopt CURRENT-STATE.md as canonical / demote status.md / fix the assistant-context.md
contract stamp. Items 1–2 are satisfied by four days of continuous practice (`CURRENT-STATE.md` is
now verified nearly every session; `docs/status.md` carries a frozen/no-longer-accepts-entries
header). **Item 3 is not.** Verified directly: `docs/assistant-context.md:14` still reads
`**1.6.0**`. The real contract is now **1.15.0** — the gap the thread flagged (three minor versions)
has grown to nine. Cheap, one-line fix, still nobody has made it.

**007** — Design fidelity harness. Verified directly: `tools/fidelity.py` still does not exist,
only `docs/design-reference/fidelity.py`. `CURRENT-STATE.md`'s 2026-07-30 entry confirms a real bug
in that file was fixed *this week* but "the harness cannot check this build — `screens.json` names
routes the app doesn't have (no router) and no per-screen reference HTML exists." Four sessions
after this thread opened, the harness still cannot run against the real app.

**036** (main body only — the TypeAhead sub-item is done, see below) — Mock Lab's three-state
staleness model and configuration-hash stamping. Verified: `src/mock_lab_store.py` has no hash or
staleness logic (`grep -n "hash\|stale"` returns nothing). Mock Lab's own UI still does not exist in
`frontend/ui/`. Blocking condition unchanged.

**045** — Simulation lookahead (VONA). Strategist's half (ADR-F) is done and thorough. **Backend's
feasibility/latency review, the only remaining step, has no reply on the thread.** Distinct from 060
(compute architecture) — confirmed by reading both; do not merge.

**054** — FTN subscription audit / Sleeper draft-harvest viability. No evidence either question was
answered. (Note: Sleeper *projections* were later ingested for a different purpose — thread 092/
FR-056 — that is season-long projection data, not the draft-pick-harvesting question this thread
asks. Do not conflate the two.)

**056** — Pre-registration of the two founder hypotheses (round-varying need, run saturation). No
pre-registration entry found in the store this thread specifies. Also gated on 054's Sleeper
harvest, which is itself still open.

**060** — Draft-time compute architecture (tiered/preemptible Monte Carlo). No evidence of the
four-tier, preemptible, anytime-algorithm design being implemented. Genuinely large, genuinely
unbuilt.

**066** — `roster_status` UI treatment. Frontend's own reply says the caveat wording is registered
in the trace registry but the actual UI decision was deliberately deferred as a product call. Still
undecided.

**067** — T1 multi-format consensus (leagues 2/3). League 2 (Ethan's) is built at the correct 10-team
shape; **ESPN (league 3) remains entirely unbuilt**, and the `consensus_input_source` per-league tag
data-ops recommended was never added — item 4 (board-builder format assertion) is explicitly
"left for backend, not attempted."

**068** — Design's fidelity-capture-list decision. PM did reply (2026-07-29) and made the ownership
call, but explicitly left it unscheduled pending the founder's own stated priority bar. Worth
flagging that FR-069 (2026-07-30) may change what four of the seven proposed capture surfaces even
are, since it proposes killing the Settings-editor/preset-matrix model this thread's capture list
partly depends on.

**070** — Recurring injury/suspension feed. Suspensions are interim-closed (ADR-053, hand-curated,
currently empty — a real, deliberate state, not an oversight). **The recurring injury pull for the
live 2026 season was not confirmed built** — the historical ingest exists, but a scheduled/repeating
job for in-season data was not found in this pass.

**076** — Thread-ID allocator race across worktrees. **This is not just still live, it is actively
manifesting right now.** `docs/handoffs/OPEN.md` currently lists three files claiming ID `093`
(`093-contract-1-15-0-scoring-ruleset-note-on-league-j.md`, `093-pass-3-the-qb-slope-collapse-is-not-established.md`,
`093-run-pr-007-recommendation-constants-vs-plain-vbd.md`) and two claiming `094`
(`094-register-the-wr-availability-fix-as-the-confirma.md`,
`094-sleeper-projection-ingest-landed-red-against-the.md`). **Do not renumber these by hand** — per
this thread's own point and per this session's own instructions, that is exactly how the allocator
race got worse before (ADR-048, threads 043/049/053). This is backend's or the founder's call.

---

## DONE, NEVER CLOSED — the work happened, the thread wasn't updated

**002** — Per-pick draft-state capture. `src/mock_lab_store.py` (ADR-046, built as part of thread
040's reply) makes the pick log itself the sole source of truth with full event-sourced replay —
this *is* per-pick state at every pick, arguably a cleaner answer than either candidate shape the
thread proposed. No reply was ever posted to thread 002 itself.

**012** — Sprint 1 runbook. Historical execution record; downstream evidence (dense ADR log, live
`.claude/agents/`, working mailbox tooling) shows the sprint ran as designed. No closing reply
needed beyond acknowledging it as historical.

**021** — Per-position rank correlation. Verified directly in `src/backtest.py`:
`_rank_correlation_by_position` exists, returns Kendall's τ_b as primary per ADR-B, has the
`unstable` demotion logic on τ_b/Spearman disagreement, and the "no minimum-games filter" rule is
present. Matches the ask precisely.

**030** — Inline "why our rank differs." FR-058 (2026-07-29) shipped the "WHY NOT HIGHEST VBD" panel
on the recommendation card — inline, traceable to named fields, exactly the shape this thread asked
for (moderate confidence; verified via `CURRENT-STATE.md`'s FR-058 entry, not by re-reading the
component itself).

**043** — Weekly finishes / season stats contract work. **The body of the thread ends with
`STATUS: RESOLVED.`, written by frontend, with commit `de6e257` and a 154/154 test count — but the
YAML frontmatter still reads `STATUS: OPEN`.** This is the exact bookkeeping bug thread 037 found
and fixed once already on thread 022 (body said resolved, frontmatter didn't). It has recurred here,
unfixed.

**047** — Manual draft setup entry. `CURRENT-STATE.md`'s 2026-07-30 entry confirms both a manual
draft-slot override ("TopBar draft-slot override") and typed opponent names are now live, each
marked with a `set by you` / `typed` indicator rather than a semantic accent color — this is exactly
the "enterable, visibly distinct from a fact" requirement the thread specified.

**050** — Sprint 3 runbook. Historical; downstream evidence across threads 026/042/047/043 etc.
progressing since confirms the waves ran.

**059** — On-deck recommendations. `CURRENT-STATE.md`'s 2026-07-30 entry: the Draft screen's
Recommend tab "gained FR-049's look-ahead toggle (recommendations computed at the user's next real
turn, not just the current pick)" — this is the on-deck surface this thread specified, built under a
different thread number (FR-049, not this thread 049).

**064** — CURRENT-STATE.md verification and staleness-detectability. Extensively confirmed: the file
is now verified essentially every session, has a `Last verified` line updated in place, and a
document-claim detector (`tools/state_claims.py`, ADR-059) now catches false claims in ten live
documents automatically — beyond what the thread asked for. No reply was ever appended to the
thread file itself.

**077** — ADP backfill / scheduled task. Root cause found, backfill run, Windows Scheduled Task
registered — all in-thread with commit hashes. **The mechanism itself was later superseded**: the
project moved to a GitHub Actions workflow (`.github/workflows/adp-snapshot.yml`) rather than the
Windows task this thread built, per `CURRENT-STATE.md`'s "Top open items" #1, which also notes the
Windows task should not be retired until the GH Actions *schedule* trigger (not just manual dispatch)
has actually fired — first opportunity was 2026-07-30 09:15 UTC, today. Worth a status check by
whoever owns this next, but the thread's own ask is fulfilled.

---

## SUPERSEDED — a later decision overtook the ask

**003** — Frontend reconnect (test count, export path, tab confirmation). Superseded by thread 035's
decision to merge frontend into this repo (`frontend/`) — frontend has since been the most active
area of the project for days, with test counts recorded in nearly every session narrative.

**006** — Design-sync pilot (`/design-sync` component round-trip). No evidence it was ever run.
Superseded by the channel the project actually settled on: dated spec files in `docs/design/` and
`docs/design-handoff/`, authored by design (which now has direct repo read access — see 068) and
implemented by frontend directly. That is the working pattern behind the "nine specs" referenced in
this triage's brief; the component-sync bridge was never adopted.

**031** — Frontend spec audit and wiring. Phase 1 (the audit, `docs/frontend-audit-2026-07.md`) is
done and is cited repeatedly by later threads. Phase 2 ("wire everything, once") as a discrete
project no longer matches how the work has actually proceeded — wiring has continued as a rolling,
FR-driven process across dozens of sessions since, not a single closeout pass.

**032** — Assistant dev mode (Haiku tier, hidden dev flag). Superseded by what was actually built:
`worker/index.js` and `frontend/ui/assistant/` ship a **Sonnet**-tier, retrieval-grounded assistant,
publicly reachable behind the site's Basic-auth gate — not a hidden developer-only flag. The
founder's own later call ("the assistant can start as a sonnet high") directly overrides this
thread's Haiku-tier scoping.

**033** — Assistant query architecture (spec-first, ADR, then build). Superseded the same way: no
ADR matching this thread's ask exists under `docs/adr-drafts/`, and the founder's own 2026-07-28
reaffirmation to keep 032/033 paused (recorded on thread 050) was later overridden by direct build
work (FR-048's retrieval layer, the Worker LLM endpoint) that does not trace back to this thread's
process. Worth a note to PM: the spec-first gate this thread called for was skipped, not satisfied.

**035** — Frontend catchup runbook. Entirely premised on frontend being unreachable in a separate
repo with zero built states. That premise has been false for days.

**046** — Bottom-up ranking data (Tier 1/2/3 inventory). data-ops's Tier 1 inventory is done. The
strategist half (the framework ADR) and everything past it has been absorbed into the `ranker`
role's ongoing, much deeper bottom-up research program (ADR-E, "bottom-up-research-pass-2/3" per
`CURRENT-STATE.md` item 12) — this thread's scope has been overtaken by that program rather than
completed on its own terms.

---

## STALE PREMISE — written against something no longer true

**026** — Recompute progress streaming, scoped to unblock "Settings editor build." That build is the
six-state spec in `docs/design-handoff/settings/`. **FR-069 (2026-07-30, today, `STATUS: NEW`)** asks
the founder's own directive to kill that model — a 24-preset matrix and a separate Settings button —
in favor of a four-entry league dropdown (three real leagues plus "Custom," which opens a pane
instead of a separate screen). The stage-name/progress-feedback need may still apply to whatever
FR-069 becomes, but the spec this thread names as its blocker is being replaced under it.

**040** (the remaining Settings-editor-UI portion only — the backend capability, undo architecture,
and slot-acceptance pieces are done, see backend's own replies in-thread) — same reasoning as 026:
the six-state Settings editor this piece was waiting on is what FR-069 proposes replacing.

**072** — Sim staleness fields (`sim_generated_at`/`sim_settings_hash`) for the league-identity chip.
Correctly deferred by frontend pending the Settings editor's existence — and that Settings editor is
exactly what FR-069 now proposes not building in its speced six-state form. Same underlying premise
shift as 026/040.

---

## MIXED — meaningfully done in part, meaningfully open in part

**037** — Audit followups. Item 1 (`<1%` rendering) done. Item 2 (duplicate thread ID) done. **Item 3
(`fidelity.py` move) still not done** — confirmed above under thread 007, same underlying gap. Item
4 (Board vs. DraftRoom availability-surface divergence) was not independently re-verified this pass;
flagging as unconfirmed rather than asserting either way.

**049** — Draft-mode gap list. Items 2–5 (recommendation panel with "WHAT YOU GIVE UP," roster chips,
full pick sequence, auto-fill) are done per the thread's own frontend reply, commit `a424a0d`. Items
1/6/7 (full tab shell, live-draft indicator, richer league selector) remain open and — per the prior
librarian pass's already-flagged judgment call to PM — overlap with thread 058's scope. That judgment
call (which thread is system-of-record for board-surface work) was never resolved and still isn't;
re-flagging rather than re-deciding it.

**053** — Founder CSV ingestion. File 2 (FantasyPros ALL Rankings) is fully ingested, crosswalk-fixed,
and wired into the live board (ADR-051). **Files 1 (Underdog best-ball ADP) and 3 (three-analyst
disagreement) were explicitly not attempted**, per data-ops's own reprioritization reply. Note: the
later FFC ADP history backfill (2,467 rows, 2013–2024) is a *different* source and does not close
this gap — it doesn't carry the best-ball caveat or the per-analyst disagreement signal this thread
specifically asked for.

**057** — Timeseries data audit. Researcher's half is thorough and done, and its single most
important finding (injury data is point-in-time, not retroactively revised — safe for backtesting)
stands. Data-ops's half has been substantially answered by follow-on threads rather than this one
directly: the forward ADP snapshot is running (GH Actions), and suspensions are interim-closed
(ADR-053). The one item with no clear follow-on: the return-from-injury usage-history case counts
researcher's own doc left as `[GAP]` queries for data-ops to run. Minor remainder, not re-verified
this pass whether it was ever run.

---

## Special case

**062** — Backlog reconciliation (the prior librarian pass). The deliverable
(`docs/handoffs/RECONCILIATION-2026-07.md`) exists and is real, careful work — this triage leaned on
it heavily. The thread's own text withholds `RESOLVED` authority from that pass by design ("Report;
do not execute" was the brief), so it correctly remains open pending a `librarian`-role closing
reply. This new triage document is, functionally, the second half of that same standing task and
does not replace 062 — whoever next holds the `librarian` role should read both together and can
close 062 with a pointer to this file plus its own.

---

## ID collisions — do not renumber by hand

Confirmed in `docs/handoffs/OPEN.md` as of this session: **`093` is claimed by three files**, **`094`
by two.** Per thread 076 (still open, see above) and per this project's own established precedent
(ADR-048, threads 043/049/053 — all previously collided and were fixed by the *tool's* allocation
logic or a deliberate single renumbering, never by an agent guessing the next free number), this is
not this session's call to fix. Flagging for backend or the founder to resolve via
`tools/handoffs.py`'s allocator, not by hand.

---

## What this triage did not do

It did not re-run every test suite, re-screenshot every screen, or re-read every source file behind
every claim in this project's history — that would be a multi-day pass on its own. Where a
disposition rests on a document's own prose (a session narrative, `CURRENT-STATE.md`'s "Top open
items," a thread's own reply) rather than something read directly this session, that is stated as
such above. Two items are flagged explicitly as **not independently re-verified**: 037 item 4 and
057's return-from-injury case-count query. Treat those two as lower-confidence than the rest of this
document.
