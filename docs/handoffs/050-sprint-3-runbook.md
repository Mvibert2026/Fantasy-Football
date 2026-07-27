---
ID: 050
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: none
---

## Sprint 3 runbook — maximum-throughput multi-wave

Founder has budget and a closing window. Goal is volume without collisions or half-finished work.
**Assume no human is available. Do not stop to ask.**

Three waves. Each wave ends at a clean boundary, so a hard stop between waves loses nothing.

### First — establish real state, do not trust this document

Run `tools/handoffs.py sync` and read `OPEN.md`. Threads resolved since this was written must be
**skipped, not re-dispatched**. This runbook was authored over a file bridge with a stale cache; the
mailbox is authoritative and this is not.

Then report, in one line, which of the threads below are already done.

---

## Wave 1 — unblockers and quick wins. Six agents.

| Agent | Thread | Files it owns |
|---|---|---|
| `frontend` A | **049** suggester fixes, then **037 item 1** (`<1%`) | `DraftRoom.tsx`, `lib/format.ts` |
| `frontend` B | **027** Opponents card completion — roster slot rows, `STILL NEEDS` chips, `next #N`, starters footer | `Opponents.tsx` |
| `backend` A | **025** Mock Lab backend, if not complete | new mock-lab files |
| `backend` B | **020** pre-registration convention (ADR-C) | `src/preregistration.py`, holdout guard |
| `backend` C | **019** bootstrap CIs, **then 021** per-position correlation — same agent, sequential, same file | `src/backtest.py` |
| `data-ops` | **046** — inventory to `docs/research/` **first**, then ingest Tier 1 only | `src/ingest_*`, `data/` |

`strategist` runs alongside all of it on **048** then **045**. Both are ADR drafts in
`docs/adr-drafts/`, touch no code, and cannot collide with anyone. **048 is the most consequential
spec in the queue** — the bottom-up ranking framework.

**Collision warnings, do not ignore:** 019 and 021 edit the same file — never parallel. 023 and 046
both touch `src/ingest_*` — 023 is held to Wave 2. Frontend A and B must both avoid `Sidebar.tsx`;
if either needs a nav entry, note it and let Wave 2 do the routing.

---

## Wave 2 — product surface. Start only when Wave 1 is committed.

| Agent | Thread |
|---|---|
| `frontend` A | **043** — the `RECOMMENDED` panel with `WHAT YOU GIVE UP`. Highest-value frontend item in the whole queue. |
| `frontend` B | **028** Predictions tab — includes the `Sidebar.tsx` nav entry both Wave 1 frontend agents were told to avoid |
| `backend` A | **017** weekly finishes and season stats. 2003–08 target data marked unavailable, never zeroed |
| `backend` B | **026** recompute progress streaming — answers thread 015's stage-name question |
| `data-ops` | **023** two diagnosed defects, now that 046's ingestion work is done |

---

## Wave 3 — only if budget remains. Stop cleanly rather than starting this half-way.

**042** regenerate `strategies.json` (~13 min, stale at 1.4.0 against a 1.8.0 contract) ·
**007** move `fidelity.py` from `docs/design-reference/` to `tools/` and run it against the screens
that now exist · **044** roster-aware recommendation surfacing, building on the
`fills an open starting slot` line that already exists · **047** manual draft setup entry ·
**029** tier grouping headers in DraftRoom — **verify what is missing first, the dot arrays appear to
already be present**.

---

## Rules for the whole sprint

- **Dispatch, do not absorb.** Every thread goes to the agent named in its `TO:` field via the Task
  tool. Working threads in your own context discards the pinned model and effort, which is the entire
  point of having them.
- **Per-thread closeout, never batched.** Finish → reply with the artifact → set STATUS → commit. Two
  earlier sprints failed by leaving this to the end.
- **Do not run the full pytest suite per agent.** It takes 2m37s and concurrent runs contend on the
  database. Targeted tests during, full suite once at the end of each wave.
- **UI work is never "done" on your own report.** "Built, pending screenshot verification," with a
  screenshot.
- **Do not reverse a deferral.** The LLM prose renderer and closed alpha track are deliberate
  decisions with reasoning in the code. Threads 032 and 033 are explicitly **paused by the founder** —
  do not pick them up.
- **New decisions go to `docs/decisions-needed.md`** with the rigorous default stated, not decided
  silently and not asked in chat.
- If an agent fails or runs out, record it in its thread and continue. One failure does not end a wave.

## Done looks like

Each wave committed at a clean boundary. `tools/handoffs.py check` green. `CURRENT-STATE.md` updated
in place as you go, not at the end. Final report: threads resolved with commit hashes and test counts,
threads still open and what each waits on, and anything found that the founder should know.
