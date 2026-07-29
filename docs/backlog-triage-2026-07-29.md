# Backlog triage — 2026-07-29

Read against `docs/pm/MEMORY.md`, `docs/CURRENT-STATE.md`, and the 2026-07-29 status log, plus the
full text of all 47 open threads in `docs/handoffs/`. Two things checked directly in the repo rather
than trusted from a reply: whether ADP actually shows on screen (it does not), and whether
`strategies.json` is still stale (it is).

## Summary — what's actually left, in plain English

Most of the 47 open items are not abandoned work — they're either waiting on something (a founder
screenshot, a design decision, another thread), or they're finished and nobody flipped the status.
Real net-new work is a much smaller list than "47 open" suggests.

**Two real bugs jump the queue** — small, cheap, and currently making the app say something false:

1. **The ADP you asked to see on the board isn't actually there yet.** Backend built it (the numbers
   exist in the data file), but no screen displays it. A session summary claimed it's "now on the
   board" — checked directly in the frontend code, it isn't. This is a few hours of frontend work,
   not a redesign.
2. **The strategies file is stamped with an old version number** and the app's own "is this stale"
   banner is correctly telling you so. One command re-generates it. Nobody's run it.

**What you can mostly forget about:**
- A cluster of "who owns which spec thread" bookkeeping items (037, 076, 081) — these are about the
  numbering system used to track tickets, not the product. Worth one policy decision, not urgent.
- Several threads that are already done in substance but never got marked closed (043's weekly
  stats export, 079's rescued mock-draft files, most of 049's draft-room panel). No action needed
  besides someone eventually flipping a status flag.
- A pile of design-fidelity and Settings-screen work that's correctly on hold until closer to your
  draft (7 September) — that's a deliberate decision already on record, not a gap.

**If it were my call, I'd do these three first:**
1. Wire ADP onto the three screens you asked for it on (backend's half is done; this finishes it).
2. Re-run the one command that fixes the stale `strategies.json` stamp.
3. Decide the one open call on Mock Lab / undo semantics that's blocking real mock-draft collection
   from starting (thread 002 — see below) — this is the thing standing between you and validating
   whether the model's predictions are any good at all.

---

## Real bugs (jump the queue)

| Thread | What's wrong | Fix size |
|---|---|---|
| **082** | ADP fields exist in `board.json` (backend done, contract 1.14.0) but no frontend screen renders `adp`/`adp_source`. Verified by grep — zero matches in `frontend/ui`. A session log claimed this was "on the board"; it is not. | Small — frontend wiring only |
| **042** | `data/export/strategies.json` still reads `contract_version: 1.7.0` against a live contract of 1.14.0 — verified directly. The app's own freshness banner correctly flags it. | Trivial — re-run `src/export_strategies.py` |

## STILL LIVE — real, wanted, not done

| Thread | In plain English |
|---|---|
| 002 | Draft-state needs to be recorded pick-by-pick (not just final results) before real mock drafts get logged, or the collected mocks can't validate the model's "run" behavior. Blocks real calibration data collection. |
| 021 | The model's accuracy score is currently computed by mixing all positions together, which fakes a good number. Needs to be split per position (QB vs RB vs...). |
| 026 | Loading spinner for "recompute my rankings" needs real stage names instead of a spinning bar — blocked on Settings screen existing first. |
| 032/033 | An AI assistant to ask questions about your rankings — paused by your own decision, don't restart. |
| 036 | Mock Lab (the tool for logging practice drafts) needs a "this practice draft used old scoring rules" flag before it's built, so old data doesn't corrupt new calibration. Not built yet at all. |
| 037 (items 3-4) | A testing tool (`fidelity.py`) is sitting in the wrong folder; and the Board screen and the Draft-room screen show availability info differently — needs a decision on which is "right." Items 1-2 already fixed. |
| 040 (item 1) | Real "create your own league" editor (Settings screen) — backend machinery exists, no screen to use it yet. |
| 045/059/060 | The "what should I draft next, thinking several picks ahead" feature — fully speced by the statistician, backend feasibility review still pending. Real and valuable, not urgent before the draft. |
| 046 | Ingest more player-usage data (targets, snap shares, etc.) to build our own from-scratch rankings instead of just adjusting the market consensus. Tier 1 data already pulled; framework spec still needed. |
| 047 | Let you manually type in your draft slot/opponents if a mock lobby doesn't auto-sync — not built. |
| 049 (items 1, 6, 7) | Draft room screen: tabs aren't fully wired, no "draft is live" indicator, and one specific "not yet" text label is missing. Most of this thread (recommendation panel, roster chips, pick list, auto-fill) is already done. |
| 053 | The half-PPR rankings file you exported by hand needs to actually feed the board-builder — it doesn't yet. |
| 054/055 | Check what your FTN subscription actually gives you, and whether Sleeper's mock-draft data can be harvested at scale. FFC (a similar ADP source) already got unblocked and built separately. |
| 056 | Two of your own hunches about draft behavior ("need matters more in rounds 4-7," "runs fizzle out after 5-7 picks") need to be formally registered as testable predictions before we have data — not enough draft data exists yet to actually test them. |
| 057/070 | Recurring (not one-time) injury and suspension tracking. Partially done — injuries table exists, suspensions list is empty (nothing to report yet, correctly, not a bug) and no auto-refresh job exists. |
| 062 (parts 1/3) | A backlog cleanup pass and a docs-folder tidy — this is literally this document's job; parts 2/4 of that same thread are already done. |
| 066 | A "roster status" data field now exists (active/no contract on file) but no screen shows it yet — needs a design decision on how to display a rough proxy honestly. |
| 067 | Your second league's board is built. Your ESPN league is still waiting on you (you said "not ready yet") — correctly not touched. |
| 071/072 | Two small "does the design mockup's fancy grouping feature deserve real backend work" questions — low priority, tied to deferred design-fidelity work. |
| 068 | A screenshot-comparison testing tool — three of seven screens can be captured today; the other four need screens that don't exist yet (Settings, Mock Lab UI). |

## BLOCKED

| Thread | Blocked on |
|---|---|
| 003, 006, 007, 012, 029 (screenshot only), 030, 031, 035, 050 | Various frontend work items, several already substantially done — genuinely blocked on the design-fidelity pause you and the PM agreed to, or minor loose ends. Not urgent before the draft. |
| 027, 028 | Opponents and Predictions tabs — both are actually built and tested, blocked only on a screenshot. **This may now be unblocked**: the app went live on the internet today and a cloud session captured real screenshots for the first time (per `docs/status/2026-07-29-pm-cloud-migration-and-deploy.md`). Worth a quick re-check rather than treating as still stuck. |
| 041 | Same screenshot limitation as above — everything else this thread asked for is already done. |
| 076, 081 | The ticket-numbering system itself has a structural flaw (parallel sessions can grab the same ticket number). This has now happened four times. Needs a founder/PM-level decision on a real fix, not another patch. |

## DONE ALREADY — thread never closed

| Thread | Evidence |
|---|---|
| 043 | `weekly_finishes.json`/`season_stats.json` built and wired into the player detail screen. Commit `de6e257`, 154/154 frontend tests passing. A reply says "STATUS: RESOLVED" but the file's own header still reads OPEN, and the mailbox index still lists it open — a bookkeeping gap, not real work outstanding. |
| 079 | The uncommitted "mock draft capture" work was rescued and committed as `backend/mock-calibration-kickers` (commit `11c794a`, confirmed in this session) per ADR-054. **Not yet reviewed or merged** — the founder's later kicker-exclusion decision may make part of it moot; do not merge blind. |
| 037 (items 1-2) | The `<1%` display bug and the duplicate-thread-ID bug are both fixed and tested. Items 3-4 remain (see STILL LIVE above). |
| 040 (items 2-3) | Backend's half — mock-draft undo and "any draft slot" support — is built and tested. Item 1 (the actual Settings screen) is not. |
| 077 | Local scheduled task and CSV archive both built and tested. Superseded in practice by the GitHub Actions workflow, which per `CURRENT-STATE.md` has fired once by hand but never yet on its own schedule — recheck 2026-07-30. |

## OBSOLETE

None of the 47 found a premise that's cleanly false today — the closest candidates (multi-league
work, the FFC block) were already updated in place by later replies on the same threads rather than
left stale, which is why they show up above as STILL LIVE or DONE rather than OBSOLETE.

## Contradictions found between threads / docs

- **082's own status conflicts with `docs/status/2026-07-29-pm-cloud-migration-and-deploy.md`**, which
  states ADP is "now on the board" — verified false by direct grep of the frontend code. Flagging
  rather than fixing; not mine to silently correct a session narrative.
- **079 and `docs/CURRENT-STATE.md`'s ADR-054 note both describe the same rescued branch**, but
  `docs/pm/MEMORY.md` separately flags that `docs/decisions.md` already has an unrelated ADR-054 (the
  FFC ingester) — a second collision waiting for that branch to merge. Not something to fix here;
  escalating by naming it in this document per the standing rule.

## What I did not reach

All 47 open threads were read in full this session. Nothing was skipped. Effort was spent reading
thread bodies rather than re-verifying every code claim inside them — the two items above (082, 042)
were checked directly because they were cheap to check and looked likely to be wrong; the rest are
reported as the threads themselves describe, not independently re-verified line by line.
