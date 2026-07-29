# Ideas inbox

**Append-only. PM-owned. Not a thread, not read by any tooling.**

Raw founder ideas land here the moment they are said, unprocessed, in his words. Nothing is shaped,
scoped or converted at capture time — that happens in batch at a session reset
(`docs/session-reset-protocol.md`).

**Why this file exists.** On 2026-07-27 the PM converted each founder remark into a thread on arrival
and produced twelve threads in an hour with at least eight overlapping pairs. The cause was not a
missing check — it was converting immediately, so no idea was ever seen next to its siblings. Batching
is the fix. You cannot deduplicate an idea against nothing.

**Safety by construction.** No IDs. No frontmatter. No cross-references. Nothing here is parsed by
`tools/handoffs.py` or read by any agent. Appending to this file cannot collide with an agent, cannot
break the mailbox, and cannot corrupt the index. That is deliberate — the capture step must be
zero-risk or the PM will hesitate to use it.

**Exception — defects bypass this file.** A bug the founder observes in the running app goes straight
to a thread. It is time-sensitive, self-contained, and there is no deduplication value in holding it.
Ideas buffer; defects go through.

## Status vocabulary

| Tag | Meaning |
|---|---|
| `RAW` | Captured, not yet reviewed. |
| `→ NNN` | Converted to thread NNN. |
| `FOLDED INTO NNN` | Merged into an existing thread rather than given its own. |
| `DECLINED — <reason>` | Considered and not doing it. **The reason is mandatory.** Without it the idea gets silently dropped and re-raised weeks later as though it were new. |
| `PARKED — <condition>` | Good, blocked on something. Name the unblocking condition. |

---

## 2026-07-27

*(Ideas from this session were converted directly to threads before this file existed. Recorded here
for continuity — see `docs/handoffs/RECONCILIATION-2026-07.md` for their dispositions.)*

- Follow news hype and ADP movement toward draft date — `→ 059`, `→ 057`
- Injury duration, recovery ramp-up in rankings — `→ 057`, Fable mandate Addendum 2
- Off-field issues and suspension probability — `→ 057`; probability modelling `DECLINED — single-digit
  positive cases per season, no validation set possible; known suspensions handled deterministically
  instead`
- Bye weeks in roster-aware recommendations — `→ 059`
- Pre-pick recommendations reviewable ahead of the clock — `→ 059` (FR-008)
- Draft-time strategy chatbot — `PARKED — depends on 059 and 049`  (FR-006)
- Every pick triggers recomputation — `→ 060`
- FantasyPros recommendation percentages — `→ 061`
- Table stakes must all be covered — `→ FR-007`, Fable mandate Priority 2A

## PM review-item log

Answered agent questions that did not change the plan. One line each,
newest at the bottom.

- 2026-07-27 · Screenshot filenames in untracked cleanup. Agent asked
  whether to rename. Answer: no — existing names already describe
  contents and are cited ~15 times in decisions.md / ADR-052. PM's
  "name by contents" instruction withdrawn as already satisfied.
- 2026-07-27 · 067 multi-league files flagged as live, not clutter.
  Agent asked whether to archive. Answer: no — commit all five. PM had
  conflated "untracked" with "unclaimed"; the correct filter is whether
  anything references the file, which the agent applied and the PM had
  not. Consequence for planning: the second league's scoring is already
  under way in thread 067, so multi-league is partly started rather
  than unstarted.
- 2026-07-27 · Untracked cleanup landed as 7b45274 / cb3f8fe /
  fa2c52a. Nothing archived; docs/archive/untracked-2026-07-27/
  never created. Screenshots kept their names (~15 live citations).
  CSV folder gitignored. Design-inbox zip deleted after diff — 3
  files byte-identical to committed, 2 superseded snapshots.
  League IDs confirmed from screenshots: Westwood 154693 (primary),
  Ethan's Expert 834236 (10 teams, not the platform's 12).
  tests/test_scoring.py 19 passed after landing.
- 2026-07-28 · (069/073 frontend chain) Registered `roster_status` in the
  trace registry alongside the mandated 069/073 fields, because the
  red-by-design tripwire test names it explicitly — the tests cannot go
  green without it. Thread 066's fuller UI-treatment ask is NOT done and
  066 stays OPEN; a no-action-on-UI note appended there.
- 2026-07-28 · (069/073 frontend chain) Temporarily added a
  `frontend-069-073-worktree` entry (port 5190) to the main checkout's
  tracked `.claude/launch.json` for live browser verification of the
  worktree build, then reverted it in the same session; `git status` on
  the main tree confirmed byte-identical to its pre-session state.
- 2026-07-28 · (069/073 frontend chain) Defect noted, not fixed (out of
  mandate): Board.tsx's provenance line hardcodes "of 378 players
  loaded" while the live board now carries 511 rows — the header
  currently reads "511 of 378 players loaded". One-line fix for whoever
  next touches the Board header.
- 2026-07-29 · (data-ops, db-rebuild session) Decided, not escalated: built
  `scripts/rebuild_database.py` as a single entry point rather than adding
  a ninth ad hoc restore script; corrected the rehearsal-branch's documented
  step order (identity.py must run BEFORE the mock-draft restore, not after
  -- it is the only thing that creates `players_canonical`, which
  ingest_mock_drafts.py needs; measured directly, `no such table:
  players_canonical` otherwise). Closed the `adp_snapshots` CSV->DB loader
  gap (`ingest_mfl_adp.py --import-csv-dir`, 17 tests). Full rebuild
  measured end to end this session: 64.0s, all restored-artifact assertions
  pass. Did not commit the dynastyprocess-mirror monkeypatch used to verify
  network steps in this session's gated proxy -- session-local only, per
  explicit coordinator instruction; see docs/can-we-rebuild-the-database.md's
  "environment-specific finding" section.
- 2026-07-29 · (data-ops, FFC ADP session) Decided, not escalated: gave FFC's three
  scoring formats (non-PPR/half-PPR/PPR, all 10-team) three distinct `adp_source`
  values rather than defaulting to half-PPR only, once the founder's mid-session
  follow-up asked for non-PPR too (public Yahoo mock rooms run standard scoring,
  Westwood runs half-PPR) -- lets the format correction be measured directly from
  same-day, same-site, same-drafter-pool data instead of assumed. Also decided a
  standalone `data/adp-snapshots-ffc/` directory rather than reusing MFL's
  `data/adp-snapshots/`, since three formats sharing one date would make
  `YYYY-MM-DD.csv` ambiguous; filenames instead carry the format tag. Chose an
  80% (not MFL's 90%) name-resolution floor for FFC's CI check, because
  `ff_playerids` carries zero team-defense rows at all -- a structural ceiling on
  match rate, not a join defect, verified by direct count rather than assumed.
  Historical FFC backfill (data going back to 2007, per the source's own claim)
  was left unbuilt this session -- FFC exposes no as-of date for past seasons, so
  a pull would need explicit `is_retrospective_aggregate` labelling and a decision
  about whether a retrospective aggregate is worth capturing at all before
  building it; flagging rather than building speculatively.

- 2026-07-29 (backend, ADR-055): live_availability.py's live-draft hazard model now takes an
  optional `cfg: LeagueConfig` end to end (positions_for/target_for/eps_for/share_bar_for, threaded
  through need_share/n_need/run_z_scores/run_multiplier/live_survival). No consumer passes a
  non-primary cfg yet -- there is no live-draft-time CLI/UI wired to this module at all currently,
  only draft_sim.DraftEngine's Prep-mode path (already config-aware, ADR-041). Wiring an actual
  live-draft consumer to pass a real league's cfg through is unbuilt; flagging rather than building
  speculatively since no caller needs it yet.

- 2026-07-29 (backend, ADR-056): `tools/handoffs.py check` now hard-fails on a real, live
  collision -- ADR-054 and ADR-055 each carry two different decisions across `main` and the
  unmerged `origin/backend/mock-calibration-kickers` branch. Not renumbered per explicit
  instruction. Whoever merges that branch needs to renumber one side's ADRs first, or `check`
  will keep failing after merge too. Also unresolved: `078-pick-level-adp-velocity-capture-
  blocked-mfl-has.md` is RESOLVED with no reply (pre-existing, not from this session) -- still
  the other thing keeping `test_mailbox_health` red.

- 2026-07-29 · (pm) **Three defects found by the founder on the live site**, recorded not fixed —
  budget exhausted. (a) **Per-league exports are incomplete**: `data/export/ethans_expert_league/`
  holds only availability/board/league/rosters — **no `nulls.json`** — so switching leagues in the
  app fails. Backend job: whatever generates per-league exports does not emit the full artifact set
  the frontend requires. (b) **The SPA fallback masks it confusingly**: `wrangler.jsonc` sets
  `not_found_handling: single-page-application`, so a missing `/data/**` file returns index.html
  with HTTP 200 and the app reports "non-JSON response" rather than "not found". The fallback is
  right for routes and wrong for data paths — exclude `/data/*` from it. PM's own change, PM's own
  defect. (c) **"Refresh data" is present-but-inert on the hosted build** — it calls a dev-server
  endpoint that cannot exist on a static deploy. Correct behaviour, wrong surface: the same
  present-but-inert problem Draft/Season were excluded from the standalone build to avoid. Hide or
  relabel it when not served by a dev server.
- 2026-07-29 · (pm) **Founder likes the dashboard format and wants it kept until told otherwise**,
  ideally made live against the repo rather than a hand-built snapshot. Format to preserve: honesty
  banner first, tile row, then filterable tabs (next / today / backlog / cost / leagues / gaps),
  dark terminal styling matching the app, figures absent rather than guessed where unverified.
- 2026-07-29 · (pm) **The founder challenged the QB delta and was right to.** His league pays 4 per
  passing TD, which should push QBs *down*, yet the board moves Josh Allen +20 and Lamar Jackson
  +19 against consensus. Most likely mechanism is the stacking passing-yardage bonuses widening the
  QB1-to-QB10 gap, but **this is unverified and a 20-rank jump in a QB-unfriendly league is exactly
  the "too good, suspect leakage" signal CLAUDE.md §8 says to escalate.** Cheap test: rebuild the
  board with yardage bonuses disabled and see whether the QBs fall back. Confirms a real edge or
  catches a bug.

- 2026-07-29 · (pm) **Two reply-heading conventions coexist and the tool only sees one.**
  `tools/handoffs.py`'s `REPLY` regex is `^###\s+(\S+)\s+·` — three hashes, role, middle dot. But
  many committed threads use `## Reply — <role>, <date>` (two hashes, em-dash), which the tool does
  not count as a reply at all. Consequence: a thread can carry a real, substantive reply and still
  fail `check` as "RESOLVED with no reply", which is exactly what happened to thread 078 today and
  is the single red test in the suite. `docs/handoffs/README.md` shows the frontmatter shape but
  never states the reply-heading format, so both spellings look correct to a human. **Fix is either
  a widened regex or a stated convention plus a one-off sweep — not another rule.** Same class as
  the ID allocator: the tool and the documents disagree, and the humans followed the documents.

- 2026-07-29 · (strategist, PR-004) **Decided, not escalated — four calls, all reasoned in the
  registration.** (a) Refused to make consensus the confirmatory baseline as the brief asked:
  n=4 seasons, exact sign-test floor p=0.125, unreachable at alpha=0.05 before any correction.
  Registered against prior-season points instead and wrote the weakening plainly — no PR-004
  outcome may be reported as an edge or as beating the market. (b) **Inverted F-A's ordering:**
  A0 runs *before* N-1/N-2, because picking the frozen candidate after seeing their results is a
  `data_seen` selection step that ADR-C would demote to exploratory. N-1/N-2 become post-hoc
  exploratory work that cannot change the verdict. (c) **Ran QB confirmatorily anyway**, keeping
  ADR-E's declared m=4, rather than F-A's "QB is closed, not run" — dropping the position we
  expect to fail shrinks the BH denominator by exactly the failing test. (d) **Set the
  materiality floor at +0.04 dtau_b**, above WR's exploratory estimate (+0.036), derived from
  the one-improved-pick-per-draft arithmetic rather than from the data. WR is predicted to fail
  on materiality even if it clears significance; that is the rule working. Registered prediction
  for the whole run is STOP. **Could not open the handoff thread** — no Bash in this role by
  design, so no allocator access; body staged unallocated at
  `docs/reviews/PR-004-handoff-body-unallocated-2026-07-29.md` with the exact
  `tools/handoffs.py new` command. Hand-typing an ID was refused (043/049/053, ADR-048).
  **Did not authorise a 2025 unseal** — irreversible, closes the family permanently, needs a
  named human approver; escalation, not an agent call.

