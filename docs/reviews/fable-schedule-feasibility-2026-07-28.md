# K-B — Does the remaining path actually fit before 30 August?

**Session:** 2026-07-28, Fable mandate K-B (`docs/fable-mandate-K-2026-07-28.md`). Read-only:
no code changed, no builds, no git operations. Writes restricted to this file and a
`docs/status.md` entry, per mandate rules.
**Evidence base:** `docs/CURRENT-STATE.md` (verified 2026-07-27, main @ `9d8e09b`),
`docs/reviews/ACTION-PLAN-2026-08.md` (the 40-work-order index + three amendments),
`docs/reviews/fable-bottomup-next-tests-2026-07-28.md` (F-A: the 22 Aug calendar stop and the
20-config budget), `docs/reviews/fable-lambda-sensitivity-2026-07-28.md` (G-A),
`docs/handoffs/OPEN.md` (49 open threads), `docs/founder-requests.md`, `src/` directory listing
(verifying what is actually built), `docs/status.md` recent entries.
**Caveat stated up front:** the mandate instructs reading `claude/session-record-2026-07-27-28.md`
first — **that file does not exist anywhere in this repo** (globbed and grepped; the only
reference to it is the mandate itself). Whatever corrections it carried could not be read. This
review rests on `CURRENT-STATE.md` and the dated review docs instead; if the session record
contradicts any premise below, that contradiction is invisible from here and should be checked
by whoever has the file.

---

## Conclusion (read this even if you read nothing else)

**The answer is split, and the split is the finding: the agent-side plan fits with about two
weeks of slack — but only if the confirmatory chain is promoted to the top of the backend queue
this week, which nothing currently in the mailbox does. The founder-side plan does not fit at
all at the stated mock target. Thirty conforming mocks between instrumentation-ready (~8 Aug at
best) and the 30 Aug readiness date is ~1.4 mocks per day, every day, at 45–60 minutes each —
roughly 22–30 hours of founder wall-clock in three weeks, alongside a job and a life, during the
exact window that also needs his dry runs, UI acceptance, and decisions. Cut the target, not the
estimates: 10–12 pre-draft mocks (keeping the blind-arm proportion), with n=30 reframed as a
season-long goal and the δ decision rule explicitly deferred.**

Five headlines:

1. **The critical path to 22 Aug is four serialized stages — H3 ∥ (N-1, N-2) → freeze →
   red-team → A0 — about 5–6 agent sessions of work, of which zero have started, 25 days out.**
   Started this week, that chain lands around 8–12 Aug and leaves real retry margin. The drift
   has already been a week: H3 was "Day 5, optional" in the 27 Jul plan and is still NOT
   STARTED while ~49 open threads compete for the same backend sessions with no calendar
   ordering among them. The schedule problem is not capacity; it is that nothing assigns the
   dated chain priority over the undated pile.

2. **The most likely failure is not the model chain — it is the mock chain, and its failure
   mode is uniquely non-recoverable.** F-A's calendar stop makes a late confirmatory run a
   *controlled* failure: consensus ships, by pre-commitment, no scramble. But if ADR-D
   instrumentation lands late and the founder — with the draft looming — starts mocking anyway
   through a non-conforming path, those mocks are permanently discarded by the project's own
   rule ("retrofitting discards mocks"), burning the scarcest resource on the schedule
   (founder hours) for zero calibration value. That is the slip to guard structurally, now.

3. **Checkpoint gates, working back from the 22 Aug freeze:** on **8 Aug** — H3 merged and
   green, N-1/N-2 registrations committed (FR-010: the registration is the deliverable), mock
   instrumentation built, one pilot mock logged, league-2 draft slot supplied. On **15 Aug** —
   N-1/N-2 run and interpreted, C3 resolved, freeze package drafted, red-team scheduled with a
   full week to fail once, ≥5 conforming mocks logged, league 3 declared in or out. **A miss at
   the 8 Aug gate means invoking F-A's calendar rule early** — consensus ships and the chain
   stops consuming sessions — rather than compressing the remaining stages and pretending.

4. **Two schedule risks larger than any slip cost nothing to close and are not on anyone's
   list.** W8 (backup) never ran: the git side is now covered by the origin push, but `nfl.db`
   (814 MB), `data/raw/`, `data/real_drafts/`, and the last four Fable review docs (untracked,
   per `git status`) each exist in exactly one copy on one disk. A disk failure between now and
   the draft outweighs every schedule question in this document. Second, the daily ADP snapshot
   — "unrecoverable if delayed," top-3 open item — hit a permission prompt on its first
   scheduled run and captured nothing; the wrapper landed at `8bdf996` but nothing verifies it
   is actually capturing. Both are sub-hour fixes.

5. **What gets cut** (schedule-level; K-D owns the full kill list): the pre-draft mock target
   (30 → 10–12, blind proportion kept), the Mock Lab UI (make the DraftRoom logging path ADR-D
   conforming instead — the backend store already exists), Settings editor, Predictions tab,
   FR-006/FR-008 conversational features, W2–W7/W10 workflow batch, N2 simulator, R4 unless a
   genuinely idle weekend slot exists, and League 3 (ESPN) automatically at 15 Aug if the
   founder's screenshots have not arrived. Every one of these is post-draft work wearing
   pre-draft clothes.

---

## 1. The dependency graph of what remains

Tally first: of the 40 work orders in `ACTION-PLAN-2026-08.md`'s index, I count **12–14
closed** (T2, T3, T4-interim, T5, T9, T10, H1, H2, H4, R1, 063, W9; T6-interim and R3's spec
are arguable halves) — consistent with the mandate's "roughly 13." What remains falls into four
chains that are mostly parallel with each other; the serialization is *within* chains.

### Chain A — the confirmatory run (hard stop: 22 Aug, F-A's own calendar rule)

```
H3 prereg gate wiring (backend, ~1 session, NO dependencies, NOT STARTED)
        │
N-1 register → run (1 config)  ┐  parallel with each other and with H3's build;
N-2 register → run (1 config)  ┘  both must precede the freeze (outcomes fold in)
        │
freeze: V5 exact + C3 universe (resolved BY N-2) + R5 family (strategist, small)
        │
red-team pass on the frozen package (opus, ~1 session)
        │
A0 confirmatory run (1 config, H3-gated, last)          ── hard stop 2026-08-22
        │
if clears: labelled overlay at RB/WR (frontend ~1) + founder acceptance   ── 23–30 Aug
if not:   consensus ships, zero further work            ── pre-committed, no scramble
P-2026 prospective registration (0 compute)             ── after board lock, before 30 Aug
```

**True critical path: 4 serialized stages, ~5–6 sessions of agent work.** N-1 and N-2 are
read-only LOSO on training seasons — no DB-writer slot needed, parallelizable. Budget check:
8 of 20 configs spent + 3 planned = 11; the cap binds only if N-1 refutes the two-stage
architecture (its own registered refutation condition) and forces a re-freeze — one such retry
still fits. The budget is not the binding constraint; the calendar and the queue are.

### Chain B — mock calibration (binding constraint: founder wall-clock)

```
per-pick draft-state logging (thread 002, backend ~1, OPEN since 26 Jul)
ADR-D contamination instrumentation (specified in thread 034; build ~1)
manual draft setup entry (thread 047, frontend ~1, OPEN)
entry_mode vocabulary reconciliation (DraftRoom's 3-value vs ADR-D's — flagged in thread 036 reply)
        │  all four BEFORE the first logged pick — retrofitting discards mocks
first conforming mock possible (~8 Aug at best)
        │
founder runs mocks: 45–60 min each, 10 of 30 blind, block-randomised
        │
n ≥ 30 conforming → δ decision rule fires;  n < 30 → δ stays 0.10 flagged, availability
                                             ships as honest estimate (already its status)
```

Agent-side: ~2–3 sessions. After that the chain is **pure founder time** — the only part of
the entire remaining plan that no agent can absorb. §2 does the arithmetic.

### Chain C — board floor (hard stop: draft day; FR-007 makes this unconditional)

Parallelizable, no internal hard dates: `make_board.py` rewire onto
`fantasypros_csv_2026draft` (FR-015 steps 2–3 — the crosswalk blocker is resolved, this is
ready now, backend ~0.5–1); league-2 board input honesty tagging (thread 067 backend piece);
League 3 blocked entirely on founder screenshots; T6 full roster-status ingest (DB-writer
slot, ~1); T7 (one query, minutes, still unrun after being "Day 1" twice); G-B per-league
constants sweep (named urgent — League 2's K slot unrepresentable); frontend contract
catch-up 069/073/074 (the trace tests are red-by-design at 1.9.0 vs 1.12.0 — every new real
red now hides inside an expected-red suite, itself a schedule hazard); D-001 implementation
(decided, unimplemented, load-bearing at `draft_sim.py:284` per G-A).

### Chain D — the analysis queue (no hard dates except one)

F-B/F-C/F-D repo-grounded, G-B/G-C/G-D/G-E, K-A/K-C/K-D: ~9–10 read-only sessions. All
parallel-safe. Only two have calendar leverage: **G-D (pre-mortem refresh at T-33)** decays in
value daily, and the **A0 red-team pass** (Chain A) shares the same opus/Fable slot. Sequence
those two ahead of the rest; the remainder can trail into September without cost.

## 2. Founder wall-clock — the honest arithmetic

The two facts the mandate states are both verified in the repo: mocks are the only calibration
source for availability (0 of ~30; the 1 logged draft is the real 2025 draft, `is_mock=0`), and
the founder is the only detector of UI defects (the screenshot-verification rule exists because
a green suite coexisted with a missing screen; FR-016 was founder-detected; the smoke harness
covers 16 flows, acceptance is still a human).

What the remaining plan asks of him:

| Item | Basis | Hours |
|---|---|---|
| 30 conforming mocks | 160-pick snake, 45–60 min each + logging overhead | **22–30** |
| Dry runs (pre-mortem T-7d items: 10 picks, undo, reload-restore, clear) | 2–3 × 30–45 min | 1–2 |
| UI acceptance passes (each new surface needs his eyes) | ~5 surfaces × 15–30 min | 1.5–2.5 |
| Decisions: D-023/D7 after A0, league-2 slot, league-3 in/out, kill-list sign-off | | 1–2 |
| League-3 screenshots (if in) + weekly suspension-watchlist sign-off | 5–15 min/wk | ~1 |
| **Total** | | **~27–37 hrs** |

The window: instrumentation cannot be ready before ~4–8 Aug (Chain B's build), so the mock
window is **~22–26 days**. Thirty mocks in that window is **1.2–1.4 per day, every single day,
zero misses** — an hour a day of a specific, attention-demanding activity, stacked on top of
the other founder items, which themselves concentrate in the final week (23–30 Aug: dry runs,
freeze verification, D-023 decision, P-2026 sign-off). At a *credible* cadence for a person
with a job — 3–4 mocks a week — the realistic pre-draft yield is **10–14 mocks**.

**So the answer to "does it fit alongside a job and a life" is no, and the plan should say so
rather than discovering it on 25 August.** Three consequences, all survivable if stated now:

- The δ pre-registered rule (≥30 conforming mocks) **cannot fire before the draft**. δ ships
  at 0.10, flagged unvalidated — which is exactly its current documented status. No new
  dishonesty is introduced by admitting the timeline; dishonesty would be keeping ±6 Wilson
  copy anywhere while knowing n will be ~12 (the realistic precision at 30 was already ±8–10).
- The blind arm shrinks proportionally (e.g. 4 of 12, block-randomised) — the absolute-
  calibration claim was always resting on the blind arm at ≈±14; at 4 it is directional only.
  Say that in the product copy.
- The one genuine relief valve is the **harvested pool** (thread 055, FFC ADP history; D-015/16
  keep it a separate population, never blended). It is agent-time, not founder-time, and it can
  calibrate the *market* side of availability even though it can never satisfy the personal-
  pool rule by design. It is currently sitting in the open pile with no date; it should be in
  the next two weeks of data-ops work.

## 3. Working backwards from the 22 Aug freeze

**Must be true on 15 August** (one week of margin to the stop, per F-A's own design):

1. N-1 and N-2 both run and interpreted; C3 thereby resolved; results folded into a drafted
   freeze package (V5 exact config, veteran-universe headline scope, R5 family attached).
2. H3 merged, green, and demonstrated — a season read outside a registration actually raises.
3. Red-team pass scheduled with a full week in hand, so it can fail once and the fix can land.
4. ≥5 conforming mocks logged — proving the pipeline end-to-end and measuring the founder's
   real cadence, which then sets the honest final-count expectation.
5. League 3 declared in or out for 2026. No screenshots by 15 Aug = out, recorded, no drama.
6. `make_board.py` rewired with rookies confirmed visible (FR-015 step 3) — board-floor work
   must not be competing for backend sessions inside the freeze week.

**Must be true on 8 August:**

1. **H3 done.** It is one session with no dependencies. If it is still NOT STARTED on 8 Aug,
   the 22 Aug date is already lost in expectation — declare it then, don't drift to the 21st.
2. N-1/N-2 registrations committed (registration-before-code; a registered, unexecuted
   experiment is a complete deliverable — FR-010).
3. Mock instrumentation (threads 002/034/047 + vocabulary reconciliation) built or in final
   review; the founder has run one pilot mock.
4. W8 actually done and the ADP scheduled task verified capturing (both sub-hour; both named
   in §Conclusion headline 4).
5. Founder inputs banked: league-2 draft slot (currently a placeholder), league-3 decision
   requested with a stated deadline.

**And the 23–30 Aug week is for integration only:** overlay display if A0 cleared, P-2026
registration, dry runs, honest-copy fixes. No methodology changes enter the board after the
22nd — that is what "freeze" means, and the week only exists if the gates above hold.

## 4. The realistic failure mode

The optimistic path assumes someone sequences the dated chain first. The realistic path, based
on how the last week actually went: the backend queue keeps servicing the loudest open threads
(23 waiting, none dated), H3 starts ~10–14 Aug, N-1 then refutes the two-stage architecture —
*its own registered refutation condition, a designed possible outcome, not a tail risk* —
forcing an ADR-E amendment and a re-freeze on the direct model; the red-team pass finds one
real issue; the retry lands 23–25 Aug; the calendar stop trips.

**What that cascades into: almost nothing — and that is F-A's design working.** Consensus
ships at every position, the overlay dies for 2026, D-023 becomes moot, P-2026 still runs
(it is free and unaffected). The confirmatory chain fails *closed*.

The cascade that actually hurts is the mock one, because it fails *open*: instrumentation
slips past mid-August → the founder, watching the draft approach, mocks anyway through the
DraftRoom path (which logs `entryMode` but is explicitly not ADR-D conforming — the thread 036
reply says the vocabularies were never reconciled) → ten founder-hours produce mocks the
calibration rule must discard → the product's signature claim enters the season at n≈0 *and*
the founder's trust in the process takes the hit, because from his chair he did the work and
the system threw it away. Nothing about this requires anyone to err; it only requires the
current queue ordering to persist. The structural guard is cheap: the DraftRoom logging path
refuses to mark a draft `is_mock=1`/conforming until the instrumentation flags exist, so
non-conforming mocks are impossible to log *accidentally*, and the founder is told before
spending an hour, not after.

Secondary failure modes, named so they are not discovered in week 4: **disk loss** (§Conclusion
headline 4 — strictly the largest expected-cost item in this document); **silent ADP gap**
(same headline; every missed day is unrecoverable and feeds draft-day ADP inputs); **red-suite
masking** (the frontend suite is expected-red at 2 tests — a third, real red joining them is
invisible without reading the failure text; closing 069/073 un-reds the suite and restores the
signal); **merge-window collisions** (the allocator race, thread 076, already cost a renumber;
four workstreams merging in freeze week is the same setup with higher stakes).

## 5. Verdict, and what gets cut

**Plainly: the plan as written does not fit, and the part that does not fit is founder time,
not agent time.** The agent-side remainder — roughly 14–16 sonnet sessions plus 2–3 opus gates
across Chains A–C — fits comfortably in 25 days *given ordering*: the project demonstrably runs
multiple worktree sessions per day, and the founder's standing autonomy grant (FR-002 addendum)
removes the permission bottleneck. What does not exist is 27–37 founder hours, and no estimate
compression changes that, so per the mandate's instruction the cut list is honest instead:

| Cut | What it saves | Revival condition |
|---|---|---|
| Mock target 30 → 10–12 pre-draft (blind arm 4, proportion kept) | ~15–20 founder hours | Founder demonstrates ≥5 mocks/week cadence by 15 Aug — then raise the target, don't re-plan |
| Mock Lab UI (backend store stays) | ~2–3 sessions + founder acceptance | Post-draft; DraftRoom path made ADR-D conforming is the 2026 instrument |
| Settings editor, Predictions tab, Compare tray | sessions + acceptance passes | Post-draft, unchanged from "Not built" list |
| FR-006 / FR-008 conversational features | design + build + the traceability fight | Post-draft; dependencies (045/049) unchanged |
| W2–W7, W10 workflow batch | ~4 sessions | The multi-agent scale-up that needs them |
| N2 season simulator, R4 red-zone ingest | ~3 sessions + a DB-writer slot | Season mode; R4 revives whenever a genuinely idle weekend slot exists |
| League 3 (ESPN) for the 2026 draft | an open-ended founder dependency | Screenshots arriving before 15 Aug — after that, 2027 |
| The analysis queue's tail (F-B/C/D, G-C/E, K-C beyond its own session) | opus slots in freeze week | 1 Sep — they lose nothing by waiting; G-D and the A0 red-team do not wait |

What is deliberately **not** cut: anything in Chain C's floor list (FR-007 is unconditional),
the ADP snapshot, G-B (a floor defect by G-A's finding), P-2026 (free, and the only path to a
future market claim), and the honest-copy fixes K-A will specify — a smaller product that is
right is the entire premise of this project; this schedule just makes it official.

---

## Checks applied

No backtest run; no statistical claims made beyond restating dated, sourced figures from prior
reviews. Guardrails relevance: the schedule above is itself a guardrail application — the 22 Aug
stop exists so that calendar pressure can never produce an ungated confirmatory run (§6.3), and
this document's only methodological act is refusing to compress the gates to fit the calendar.
Numbers I could not verify from the repo and have labelled as estimates: per-mock wall-clock
(45–60 min, from 160-pick draft structure, not measured), founder availability (~5 hrs/week,
assumed for the arithmetic and stated as such). The missing session record
(`claude/session-record-2026-07-27-28.md`) is flagged in the header; nothing in this document
knowingly contradicts `CURRENT-STATE.md` as of `9d8e09b`.
