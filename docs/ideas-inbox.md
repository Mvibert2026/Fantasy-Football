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
