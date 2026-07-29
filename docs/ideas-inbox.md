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

- 2026-07-29 · (founder, via pm — RAW, needs capture as a formal request) **"Once bottom-up
  exists, compare it against consensus and see which is better"**, and separately he **likes
  consensus acting as an adjustment rather than a rival** — i.e. the product shape is
  consensus-adjusted-by-bottom-up, not bottom-up-versus-consensus. Recorded as a **successor
  question, PR-006, unwritten**; deliberately NOT folded into PR-004/PR-005, which it would
  contaminate. n-limited until January 2027 at the earliest (needs more consensus seasons or
  P-2026's prospective result). **Escalation attached: this conflicts with `CLAUDE.md` §4,
  "Ranking sources stay separate, never blended."** Measuring a blend descriptively is fine and
  is registered as PR-004 §11; *shipping* one needs a §4 amendment, which is a founder decision.
  Middle path suggested: consensus adjusts display/confidence (labelled overlay, disagreement
  flags) rather than being averaged into a score. Also raised by him and folded in: **"test our
  bottom up r squared against consensus and consensus adjusted for what we do have for now."**
  Should be captured properly via `python tools/founder_requests.py new --raised-by "pm relay,
  2026-07-29" --subject "Consensus as an adjustment to bottom-up, not a rival"` — the strategist
  session had no shell to run it.

- 2026-07-29 · (strategist, PR-004 revision) **Founder challenged the premise and was right;
  registration revised in place before freeze.** (a) Accepted "ADP is not consensus" — no
  baseline swap to ADP for depth, because depth bought by measuring a different quantity is not
  depth. (b) Accepted "we have 25 years of data independent of consensus" — the first draft let
  the n=4 question cap the deep one. (c) **Found the constraint that actually binds:**
  `experiments/bottomup/data.py:60`, targets missing 2003–2008 and air yards 2009+ only, so the
  usage model cannot be built deep. **The deep sample buys power; the deep model is the weak
  one.** Split into PR-004 (box-score, deep, m=4) and PR-005 (V5 usage, n=13, m=4) with separate
  family manifests so the winning arm cannot be picked after the fact. (d) **Declined to
  recompute the +0.04 materiality floor against the new n** — power and materiality are
  different quantities; what changed is the *meaning* of the ≥75% fold rule, now tabulated
  (sign p≈0.092 at n=13, ≈0.007 at n=25). (e) **Declined to report a positional-tier heuristic
  as a third baseline** — it is a monotone transform within position and tau-b is invariant, so
  it would be reporting B1 twice; substituted a three-season average as B2. (f) Predicted on the
  record that the census will return n≈25 folds (~2000–2024), because `run.py:10`'s 2002 start
  is a walk-forward warm-up artifact and embargoed LOSO has no warm-up cost. Pre-committed:
  **n < 15 ⇒ STOP without running.** Still no unseal authorised. Still no shell, so thread 083's
  revised reply is staged, not appended.


- **2026-07-29, backend (ADR-057).** `make_board.fit_rank_curves()` pools all training seasons with
  EQUAL weight. Measured: the QB rank->points slope ran -67, -73, -59, -45, -4 across 2021-2025 —
  a monotone collapse — while RB moved the other way (-35 to -78). Flat pooling averages over a
  regime change CLAUDE.md §6.4 explicitly warns about, and it is the sole reason the shipped board
  carries a QB premium. Needs a recency-weighting experiment (and the `season_weight` field the
  schema principles already call for), gated by Statistician + Red-team.
- **2026-07-29, backend (ADR-057).** The `points ~ a + b*ln(rank)` estimator is misspecified
  ASYMMETRICALLY across positions: RB/WR are concave in log-rank (deep-rank slope 2-2.6x the
  shallow-rank slope), QB is not (0.9x). Since the board ranks positions against each other, this
  is an ordering risk, not just a fit-quality issue. Candidate fixes: piecewise/segmented fit, or
  fit on the rank range each position's replacement level actually sits in.
- **2026-07-29, backend (ADR-057).** The board reports `vbd` alongside `vbd_lo`/`vbd_hi` but the
  point estimate is what gets read. Josh Allen's CI [57.0, 155.2] overlaps 29 of the top 40
  players. Consider surfacing "not distinguishable from ranks X-Y" in the export/UI so a +20 delta
  cannot be read as a signal when the interval says otherwise. (Frontend-facing; needs a thread.)
- **2026-07-29, backend.** `scripts/rebuild_database.py` step 4 (`ingest_rankings.py`) 403s in a
  Claude cloud session as documented. The committed `data/rankings-history/rankings_2021_2025.csv`
  IS a byte-exact dump of what it writes, so a session can restore it — see
  `experiments/restore_rankings_from_committed_csv.py`. Worth deciding whether that restore belongs
  in `scripts/` as an explicit `--from-committed` flag rather than living in experiments/.

- 2026-07-29 · (researcher, historical ADP) **Decided, not escalated — three calls.** (a) Wrote the
  findings to `docs/research/historical-adp-availability-2026-07-29.md` and replied on **thread 055**
  rather than opening a new thread: this session had no Bash, so no allocator access, and hand-typing
  an ID is refused (043/049/053, ADR-048). 055 is exactly on-topic and was left OPEN — only data-ops
  may resolve it. (b) Reported three defects in `src/ingest_ffc_adp.py` rather than fixing them —
  research-only mandate; the load-bearing one is that a `--teams 10 --period 2021` pull would tag
  12-team data as `ffc_half_ppr_10team`, because FFC serves the 12-team page for archive requests at
  any other team size with HTTP 200 and no signal outside the `<h1>`. (c) Left row-depth per archived
  season as an explicit `[GAP]` instead of quoting a number — WebFetch's markdown conversion
  demonstrably drops rows (a 2010 full dump returned 25 rows containing no running backs), and a
  plausible count is exactly the contamination this project has been burned by.
  **NOT touched, escalating instead:** this file currently contains unresolved merge-conflict markers
  (`<<<<<<< HEAD` / `=======` / `>>>>>>> c191f45...`) around the strategist PR-004 entry and the
  backend ADR-057 entries. Both sides look like real work. Appended below them without altering
  either side.
  **Also escalating:** every FFC/FantasyPros authorisation (FR-023, D-020, D-021) is scoped "private
  use by one person, void if the product reaches a second human", and `CURRENT-STATE.md` now records
  the app as publicly reachable on the open internet by founder choice. Fetching is authorised;
  redistribution is a `[GAP]` — FFC's ToS was unretrievable for the third time today.
  **Also, stale line:** `CURRENT-STATE.md` still says "FFC is blocked by robots.txt regardless" and
  "FFC remains blocked" while MEMORY §4 and FR-023 record it unblocked and say they supersede.

- **2026-07-29, ranker (research pass 1, `docs/ranking/bottom-up-research-pass-1.md`).** Four calls
  made without escalating, logged here.
  (a) **Did not fund the coaching-data sourcing decision.** Two independent bounds — a
  perfect-foresight team-volume oracle (delta <= +0.055 tau_b, and that version carries a known
  self-inclusion leak so it is generous) and a team fixed-effect ANOVA on residuals (excess share
  over chance -0.042 to -0.002, i.e. none at any position) — put the whole team-environment channel,
  of which coaching is a strict subset, near zero. The same argument deprioritises Vegas implied team
  totals. Recorded so the decision is not silently re-litigated later as a fresh idea.
  (b) **Quantified the yardage-bonus channel for the first time, and it is small.** Realised
  within-position reordering is a mean 0.19-0.60 positional ranks (tau_b 0.93-0.98 with vs without
  bonuses); ex ante it is smaller still, because PR-002 already returned NULL on whether the
  reorder-driving shape residual persists. The bonuses act **across** positions instead: +9.4 / +7.4
  / +5.7 / +2.7 points of top-3 VBD at WR / RB / QB / TE, a ~6.8-point WR-vs-TE differential. Keep
  the bonuses in the scoring engine; stop calling this the structural edge.
  (c) **Contested ADR-057's QB mechanism rather than building its fix.** The realised finish-rank
  value curve at QB is at an era high (-72.9 in 2021-2024 vs -57 to -59 before) while the
  consensus-fitted slope fell, and the two R-squareds are 0.91-0.98 vs 0.15-0.41. TE shows the same
  pattern; RB and WR do not. Recency-weighting the pooled consensus curve may therefore make the
  board track market noise faster, not slower. **Not acted on — thread 085 to strategist**, because
  ruling on my own analysis is exactly what the role structure forbids.
  (d) **Added `ranker` to `tools/handoffs.py:31` ROLES.** `.claude/agents/ranker.md` existed but the
  role did not, so this agent could not open a correctly attributed thread. One line.
  **Flagging for whoever picks the model up next, as the cheapest real lead in the document:**
  `snap_counts` (2013-2025, 324,611 rows), `ngs_receiving` (2016-2025), `ngs_rushing` and `injuries`
  are all already in `data/nfl.db`, and **none of them is read by `experiments/bottomup/data.py`**,
  which touches only `player_weekly_stats`, `draft_picks` and `ff_playerids`. Twelve-plus seasons of
  role data, zero acquisition cost, no licensing question.
  **Third session to report it:** this file still carries unresolved merge-conflict markers further
  up, around the PR-004 / ADR-057 entries. Appended below them without touching either side.
