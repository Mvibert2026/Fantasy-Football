# Draft-day pre-mortem — 2026-07-27 (Extended mandate, Priority 3)

Premise: it is the evening after the 2026 draft and it went badly. Working backwards, every
failure below is grounded in this repository's measured state (not hypotheticals): file, line,
or measurement cited. Ranked by likelihood × damage. **The morning-of checklist at the bottom is
the deliverable; everything above it is the derivation.**

Facts measured this session that the ranking rests on: `nfl.db` = 814 MB, one copy, **no git
remote configured** (`git remote -v`: empty); the 2026 ECR snapshot is `as_of 2026-07-24`,
`is_preseason_final=0`; export artifacts last built 2026-07-26; `strategies.json` still at
contract 1.7.0 vs 1.9.0 everywhere else; draft picks persist to per-league `localStorage` with
no backend write (`frontend/ui/data/draft.ts:6-7,128`); suspension/roster-status handling: zero
matches in `src/` and `tests/` (table-stakes review items 4–7); the half-PPR fix still sits on
unmerged worktree branch `a246696`.

## Ranked failure modes

| # | Failure (what the founder sees at the draft) | Likelihood | Damage | Cheapest prevention / detection |
|---|---|---|---|---|
| 1 | **Board order is subtly wrong everywhere** — the consensus input is standard-scoring, not half-PPR (`ingest_rankings.py:25-36`; fix unmerged in `a246696`). Pass-catcher order inherits the wrong reception weight; every VBD number downstream follows. This is not a risk, it is the current state. | **Certain** (unless T1 lands) | High, systemic | Land T1 before the draft: half-PPR pull + `scoring_format='HALF'` assertion in the board builder. Detection on the day: the checklist verifies the format stamp in the app's Methodology/version surface. |
| 2 | **The board is a July snapshot in an late-August draft** — nothing records or bounds snapshot age (T5 not built); the current snapshot predates every camp battle, holdout, August injury and depth-chart settlement. A manual re-pull is the only mechanism and nothing reminds anyone. | High | High | T5 freshness tripwire (build refuses a snapshot older than N days). Until then: checklist item — re-pull ECR the morning of, rebuild, confirm `as_of_date` = draft day. |
| 3 | **A suspended / retired / IR player sits in the top 60 as a full-season starter** — no suspension table, no NFL roster-status ingest, no retirement check (T4/T6, both NOT BUILT; the exact case FR-007 was coined over). The August-suspension news cycle happens every year. | High | Severe per-row, and it torches trust in all 300 rows | T4's interim fixture: hand-curated list of known 2026 suspensions/retirements asserted against board flags (10-minute founder/researcher task + trivial test). Morning-of: eyeball the top-100 against a news site for names the board cannot know about. |
| 4 | **Scoring settings are subtly wrong for this league** — CLAUDE.md §7 is "reconstructed… verify against the live league settings before relying," and that verification has never happened (T2). Bonus *stacking* at thresholds (+4.5 at 400 pass yds) is an assumption (`scoring.py:61-63` `>=` loop). If the platform replaces rather than stacks, every projection and VBD number shifts. | Moderate | High | T2: founder screenshots the platform scoring page (10 min); transcribe to a fixture asserted against `scoring.LEAGUE`. One-time, permanent. |
| 5 | **The app breaks at T-0 because something rebuilt at T-1h** — 814 MB SQLite takes writer locks from concurrent agent sessions; a mid-rebuild export or mid-migration DB at draft time produces missing/partial artifacts. The version banner already flags one live drift (`strategies.json` 1.7.0). | Moderate | High | Freeze: no agent sessions, no rebuilds, no pulls after T-2h (checklist). Rebuild exports at T-2h, then verify the manifest and the version banner shows zero mismatches. |
| 6 | **Machine or browser dies mid-draft** — picks live in per-league `localStorage` only (`draft.ts:128`: "a failed write just means state resets next load"); recovery works only in the same browser+profile; a stale pre-seeded draft state from testing can also load on open (the RETROFIT-5 note names old localStorage records). No remote, no second machine, no paper fallback unless printed. | Low–Moderate | Severe under a clock | Pre-draft: open DraftRoom, enter 2 test picks, reload, confirm restore, then clear to a clean state. Print the board CSV (make_board writes one) as the dead-machine fallback. Know the platform's own draft screen is authoritative for what happened. |
| 7 | **Wrong league config drives the session** — 25 config dirs in the matrix; the hazard model is not rerun per config; drafting with a neighbouring config's board/availability quietly mis-weights everything. | Low–Moderate | High | Checklist: the app header's league name/id and the platform's league page are confirmed to match before the first pick. |
| 8 | **Pick-entry errors under the clock** — digits 1–5 commit a shortlisted candidate instantly; Backspace undoes only the last pick; an error noticed three picks later means manual reconstruction while on the clock. | Moderate | Moderate (recoverable, costs clock) | A 10-pick dry run the day before (the Priority 4 harness script doubles as this). During the draft: fix mis-picks at the next gap, not immediately. |
| 9 | **`strategies.json` stale content on the strategy tab** — known drift (1.7.0), open with backend (thread 042). The banner catches the version; it does not re-export the file. | Certain until fixed | Low–Moderate | Re-export before the freeze; banner check is the detection. |
| 10 | **Disk loss before the draft** — one copy of an 814 MB DB containing unrecoverable ADP snapshots; no git remote; finished work already sits invisible on unmerged branches. | Low | Catastrophic, unrecoverable | W8 now: `git bundle` + a DB file copy to any second medium (external drive / cloud folder). Minutes. |
| 11 | **A last-minute "fix" edited a dead shadow copy** — `frontend/src/` holds a byte-identical dead copy of the backend Python tree (26 files, subtree residue, imported by nothing); three agent worktrees also carry stale copies. An urgent T-1d edit in the wrong tree silently does nothing. | Low | Moderate–High (invisible non-fix) | Delete or README-stamp `frontend/src/` (one commit); freeze covers the rest. Checklist verifies fixes by *observed app behaviour*, never by "the edit is in." |
| 12 | **Dev-server won't start at T-5min** — vite + npm + port state, untested that morning. | Low | High if discovered at T-0 | Checklist: full cold start at T-2h, not T-5min. |

Two structural observations the ranking makes visible:

- **The top four failures are all "the board silently doesn't know something," and none of them
  is a model problem.** They are ingestion/verification gaps (format, freshness, roster status,
  scoring rules) — precisely the table-stakes review's conclusion, now with a date attached.
  The single highest-leverage pre-draft workstream is T1+T5+T4-interim+T2, in that order.
- **Everything after #5 is mitigated by process, not code** — a freeze window, a dry run, a
  printout, a backup. The checklist is genuinely the cheapest prevention layer available.

## The checklist

Print this. Times relative to the draft clock.

### T-7 days
- [ ] T1 landed: board build asserts `scoring_format='HALF'`; a re-pull of the live half-PPR ECR
      succeeds. (If not landed: escalate — this outranks every other item.)
- [ ] T2 done once: platform scoring page screenshot matches `scoring.LEAGUE`, including bonus
      stacking behaviour, fixture test green.
- [ ] T4 interim: hand-curated 2026 suspension/retirement/holdout list checked against the
      board; every affected player flagged or consciously accepted.
- [ ] W8: git bundle + `nfl.db` copy exist on a second medium, dated this week.
- [ ] Dry run: 10 picks entered in DraftRoom against the clock, one undo exercised, reload
      restores state, then state cleared.

### T-1 day
- [ ] Re-pull ECR/ADP; rebuild exports; `as_of_date` is today's or yesterday's.
- [ ] Version banner: zero contract mismatches (strategies.json included).
- [ ] Top-100 eyeball against a news site: no name the board cannot know about (fresh injury,
      suspension ruling, retirement, holdout escalation).
- [ ] Print the board CSV (dead-machine fallback).
- [ ] **Freeze begins: no agent sessions, no rebuilds, no schema or config edits from now on.**

### Morning of (T-2h)
- [ ] Cold start: `npm run dev` from scratch; app loads; sync manifest timestamp is current.
- [ ] League check: app header league name/id == the platform league being drafted, and the
      platform's scoring page still matches (leagues get edited in August).
- [ ] Snapshot age visible and ≤ 1 day; board row count ≈ expected (~378); spot-check 3 known
      players' teams/byes against the platform.
- [ ] DraftRoom: clean state (zero picks), test pick + undo + reload-restore, then clear.
- [ ] Browser: same machine + browser + profile as the dry run; laptop on power; platform draft
      room open in a second window — it is the authoritative record if this app dies.

### During the draft (taped next to the keyboard)
- Platform is truth for what happened; this app is advice, not the record.
- Mis-entered pick: keep drafting, repair at the next gap between your picks.
- App dies: keep drafting from the printout; reconstruct the log afterwards.
- A recommendation that looks insane probably reflects a data gap from the list above — trust
  your read of the room over a row you can't explain (the model's own docs say the availability
  numbers are honest estimates, not calibrated probabilities, at n=1 mock).

---

## PM NOTE (2026-07-27) — dates anchored, and this checklist is now single-league among three

**Dates, per founder confirmation (`docs/founder-requests.md` FR-011):** T-7 days = **2026-08-23**,
T-1 day = **2026-08-29**, T-0 = **2026-08-30**. 2026-08-30 is a deliberate readiness-buffer
target, not the Westwood/primary league's real draft date (that's 2026-09-07, confirmed from
`docs/screenshots/League Settings 2.png`) — the founder chose to build to the earlier date on
purpose. Treat both as true; they are not in conflict.

**Gap this checklist doesn't yet cover:** it was written against one league. The founder now has
three (`docs/founder-requests.md` FR-012) — Westwood (Yahoo, primary, covered above), a second
Yahoo league, and an ESPN league — the latter two with different scoring, different team counts,
and **no draft dates confirmed yet**. This checklist's items (T1 format assertion, T2 scoring
fixture, T4 suspension list, the dry run) are all Westwood-scoped as written. Whoever runs this
checklist for leagues 2/3 needs either a per-league copy or an explicit read that every item here
means "for Westwood" until thread 067 (T1 re-scope) and the founder's league-2/3 data land. Not
resolving that gap here — flagging it so it isn't discovered at T-1 day.
