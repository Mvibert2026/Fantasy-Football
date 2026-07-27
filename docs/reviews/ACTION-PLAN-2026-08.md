# One-week action plan — 2026-08

**Written 2026-07-27 by Fable (session 3), before any further analysis, per mandate 4.**
**Fable is absent until approximately 2026-08-03. This document is what carries the week.**
**Audience: the founder first, then the PM and agents. Written to be actionable without Fable.**

Status of this document: LIVE — updated at the end of Fable session 3 with the session's
results (see the dated amendment at the bottom). If anything here conflicts with the PM's
framing of the same work, this document states Fable's independent view; the founder decides.

---

## The one sentence for midnight

**If T1 (half-PPR consensus) does not land this week, the draft board's player order is wrong
for this league's scoring — everything else is refinement; land T1, then the freshness tripwire
(T5), then the suspension list (T4-interim), then verify the scoring page once (T2), and take
the ten-minute backup (W8) before any of it.**

That order is the pre-mortem's own ranking of certain-to-likely failures
(`fable-draft-day-premortem-2026-07-27.md`, failures 1–4 and 10). Nothing in the modelling
workstream is draft-blocking. The draft is in late August; this week is for the board's
correctness floor, not its cleverness.

---

## Ground rules for the week (collision constraints, measured not guessed)

1. **One DB-writing session at a time.** `nfl.db` is one 814 MB SQLite file; concurrent agent
   writers take locks and have already nearly collided. T1, T6, and R4 are the DB writers this
   week — run them in separate serialized slots, never in parallel with each other.
2. **Code agents work in worktrees** (the harness default). Doc-writing sessions keep to ≤2–3
   concurrent until W1/W3 land, because every session serializes through `status.md`,
   `CURRENT-STATE.md`, and `OPEN.md` — the documented contention point.
3. **Thread IDs collide under concurrency** (4 incidents in one day, two namespaces; the ≥100
   range rule is broken on arrival — workflow review §0.3). Until W1 lands: create new threads
   from one session at a time, or accept slug-named files and renumber at sync.
4. **The holdout stays sealed.** No 2025 reads for any reason. H1's tripwire (built, on the
   fable branch) fails the suite on any unregistered access — that is by design, not a bug to
   silence.
5. **No confirmatory F-BOTTOMUP-CORE run this week.** It requires H3 (gate wiring) + a frozen
   registration (C3, R5) + Fable's review of the session-3 experiment results. Running it early
   burns the only clean shot at it.

---

## Day-by-day sequence

Owners: **founder**, **PM**, **backend** (sonnet), **frontend** (sonnet), **data-ops** (sonnet),
**researcher** (sonnet), **strategist** (opus), **integrator** (any code-capable session).
Costs are rough sonnet-session units unless marked opus. Every T/W/R/N item has a full
sonnet-executable spec in its source review — pointers in the index at the bottom.

### Day 1 (Mon 07-28) — safety and unblocking. Nothing else starts until W8 is done.

| # | Item | Owner | Cost | Depends on |
|---|---|---|---|---|
| 1.1 | **W8 backup**: `git bundle --all` to a second medium + copies of `nfl.db`, `data/raw/`, `data/real_drafts/`. Also copy the **untracked** `docs/reviews/` directory — all six Fable review docs and this plan exist in exactly one uncommitted copy each. Verify one restore. | data-ops (founder picks medium, D1 below; default = bundle + external drive, no decision needed) | 0.25 | nothing |
| 1.2 | **Founder, ~15 min total**: (a) confirm the exact draft date — the whole checklist anchors to it; (b) screenshot the platform's live scoring-settings page including bonus behaviour (T2's input; only he has access); (c) read decision list D1–D6 below. | founder | — | nothing |
| 1.3 | **Merge `fable/ext-2026-07-27`** per the per-item assessment in `FABLE-EXT-2026-07-27.md` ("Merge assessment"). Everything is additive except `src/holdout.py` (safe rename, zero callers) and `frontend/package.json` (one devDependency, needs one frontend look). T3 arrives red **by design** — it documents the live bye defect; do not "fix" the test. | integrator, after founder D2 | 0.5 | D2 |
| 1.4 | **Merge or discard `a246696`** (worktree branch, thread 018 FantasyPros backfill + the escalated half-PPR switch — finished work invisible since before session 1; W9's named first action). Merging it is the head start on T1. | integrator | 0.25 | 1.3 |
| 1.5 | **T7**: one query — `SELECT MAX(dt) FROM depth_charts` — settle the CURRENT-STATE contradiction; delete the wrong line. | data-ops | minutes | nothing |

### Day 2 (Tue 07-29) — the format fix. The week's most important day.

| # | Item | Owner | Cost | Depends on |
|---|---|---|---|---|
| 2.1 | **T1 — half-PPR consensus** [DB-writer slot]: pull FantasyPros live API `type=ST&scoring=HALF`; add `scoring_format` + `as_of_date` columns; rebuild the board; add the test that the board builder **raises** on any non-HALF row. Full spec: table-stakes review, T1. | data-ops (pull) + backend (check) | 1 | 1.4 helps, not required |
| 2.2 | **063 fix** (parallel, frontend tree, no DB): clicking the already-autofocused pick field must open the suggester — the harness's first run caught the live miss (15/16). Fix the cause, run `npm run smoke` to 16/16, attach the screenshot. | frontend | 0.5 | branch merged (1.3) for the harness |
| 2.3 | **T2 fixture** (parallel): transcribe the founder's scoring screenshot into `tests/fixtures/league_scoring_live.json` + test vs `scoring.LEAGUE`, **including whether bonuses stack or replace**. Record the verification date in `decisions.md`. Four seasons of §7's "verify before relying" caveat end here. | backend | 0.25 | 1.2(b) |

### Day 3 (Wed 07-30) — board correctness.

| # | Item | Owner | Cost | Depends on |
|---|---|---|---|---|
| 3.1 | **T9 — team-code crosswalk** (canonical franchise table, era + variant mapping: JAC/JAX, OAK/LV, SD/LAC, STL/LA). This is the durable fix that turns T3 green and restores byes to the 22 LAR/JAC board players. Run after 2.1's rebuild to avoid board-build contention. | backend | 0.5 | 2.1 |
| 3.2 | **T5 — freshness tripwire**: board build fails if the ECR snapshot is older than N days (suggest N=3 during draft prep, founder-tunable). Kills pre-mortem failure #2 permanently. | backend | 0.25 | 2.1 (`as_of_date` column) |
| 3.3 | **T4-interim research**: curate the 2026 suspension / retirement / holdout / season-ending-injury list from news sources, with dates and sources per row. No repo contention — pure web research. | researcher | 0.5 | nothing |

### Day 4 (Thu 07-31) — roster truth and workflow hardening.

| # | Item | Owner | Cost | Depends on |
|---|---|---|---|---|
| 4.1 | **T4-interim fixture**: researcher's list → fixture + test asserting every listed player is flagged on the board (or consciously absent). The check exists now; thread 057's automated feed replaces its data source later. | backend | 0.25 | 3.3, founder eyeball (D5) |
| 4.2 | **T6 — NFL roster-status ingest** [DB-writer slot]: active / IR / PS / not-rostered for the live season; board players resolve against it; non-active players flagged. Covers retirements, IR, and the cross-check half of team changes. | data-ops | 1 | serialized after 2.1 |
| 4.3 | **W1 — slug allocation + PM outbox** (parallel, worktree, touches only `tools/handoffs.py` + docs): kills the demonstrated ID-collision class and the PM's destructive write path. Full spec: workflow review W1. | backend | 1 | nothing |

### Day 5 (Fri 08-01) — follow-through.

| # | Item | Owner | Cost | Depends on |
|---|---|---|---|---|
| 5.1 | **T8 — position cross-check** (ECR position vs roster position; mismatches quarantined, never silently resolved). | backend | 0.25 | 4.2 |
| 5.2 | **N1 — empty `league_matchups` / `league_transactions` tables** (with `league_id`, `as_of_date` from day one). Cheap now, painful mid-season. | backend | 0.25 | nothing |
| 5.3 | **N3 — week-leverage utility** with the interim default (uniform 1.0 weeks 1–15, hand-set 2.0 on 16–17, labelled unvalidated). Spec: in-season review §4. | backend | 0.25 | R3 shape helps (D4) but interim form does not require it |
| 5.4 | **H3 — prereg gate wiring** (optional this week; mandatory before any confirmatory run): route season reads through the registration; already specified in thread 020's deferred items. If it slips, it waits for Fable — do not half-wire it. | backend | 1 | nothing |

### Weekend (08-02/03) — buffer and checklist.

- Slips from the week land here first. Protect T1/T5/T4/T2 above all.
- **R4 — red-zone/goal-line ingest** [DB-writer slot] if capacity remains: it blocks ADR-E's
  own TD-rate spec and feeds Fable's return work; it is not draft-blocking.
- Founder dry run (pre-mortem checklist "T-7 days" items) any time after the board is rebuilt:
  10 picks in DraftRoom, one undo, reload-restore, clear. Early practice catches what tests
  cannot.

---

## Founder decision list

Plain language, one decision each, with the trade-off and Fable's recommendation. These are
yours alone; the PM should not pre-filter them.

**D1 — Backup medium (W8): private remote or local bundle?** A private GitHub remote survives
the machine dying and enables CI later; nothing-leaves-the-machine is a legitimate preference
and a scheduled `git bundle` to an external drive gets 90% of the safety. *Recommendation:
private remote if you're comfortable; otherwise bundle — but decide in minutes, not days, and
let 1.1 default to the bundle if you're busy.*

**D2 — Merge `fable/ext-2026-07-27`?** Everything on it is additive or zero-caller; the one
red test (T3) is red because the live board has a real defect, and merging it red is the honest
option. Not merging repeats the silent-non-delivery failure the project already named.
*Recommendation: merge Day 1, per the item-by-item assessment in the session-2 log.*

**D3 — Ten minutes on the platform scoring page (T2).** Only you have league access. Every
projection number in the product rests on an unverified reconstruction, specifically on whether
yardage bonuses **stack or replace** at thresholds. *Recommendation: do it Day 1; it is the
cheapest high-leverage act available to anyone this week.*

**D4 — Spend one opus (strategist) session this week on R3, or hold everything for Fable?**
R3 redefines the projection's output as a week-indexed vector — suspension valuation (T4's
games-adjustment), bye cost, and N3's leverage weights all want its shape. Holding it costs
nothing functional this week (interim forms exist) but delays the ADR-E amendment queue.
*Recommendation: spend it — R3 is a small, well-scoped amendment (ranking-design review, R3)
and it unblocks three consumers. Hold R5 and C3 for Fable's return; they belong inside the
registration discussion.*

**D5 — Sign off the suspension list (T4-interim).** The researcher drafts it; you know the
league's news cycle. Five minutes of eyeballing before it becomes a fixture. *Recommendation:
do it whenever 3.3 lands.*

**D6 — Draft date.** Confirm it. The entire pre-mortem checklist anchors to T-7d/T-1d/T-2h,
and "late August" is not a date. *No trade-off; just needed.*

*(A seventh decision — whether the 2026 board should be a position-hybrid: consensus at QB,
bottom-up at RB/WR/TE — is deliberately NOT asked this week. It depends on the session-3
experiment results; see the amendment at the bottom of this file. Do not let it be decided in
Fable's absence.)*

---

## Explicitly NOT this week

A plan that includes everything is not a plan. The following are deprioritized **with reasons**,
not forgotten:

- **W2–W7, W9 (beyond the two Day-1 merges), W10** — workflow hardening beyond W1/W8. Real,
  sequenced, not draft-blocking. The multi-agent scale-up they enable is next month's problem.
- **N2 (season simulator), N4, N5** — in-season build. Needs R3's vector and a strategist spec;
  the season starts after the draft, not before.
- **R2 (coach data)** — gated on licensing; the review ranks it last of the four mechanisms by
  residual mispricing × feasibility; estimates are noise-dominated at n≈32 teams/season.
- **R6, R7, C1, C2** — small, valuable, and strictly after the confirmatory-run design settles.
- **Rookie-inclusion arm (C3's build side)** — belongs inside the registration Fable reviews on
  return.
- **The assistant constrained-composition build** — session 2's Priority 5 verdict: only after
  ADR-F. Unchanged.
- **Any confirmatory F-BOTTOMUP-CORE run** — see ground rule 5. This is the one item where
  doing it early destroys value permanently: the modern-season folds get one clean confirmatory
  use, and spending them ungated (H3) or unregistered (C3/R5) wastes them.
- **Any holdout access** — sealed. The tripwire will catch it, and the founder should treat a
  tripped H1 as an incident, not noise.

---

## Failure branches

For the items most likely to go wrong, so nobody stalls waiting for Fable:

**T1's API pull fails** (auth, format, endpoint drift): the founder manually downloads the
half-PPR rankings CSV from FantasyPros in a browser; the founder-CSV ingestion path (thread
053) takes it from there. Worst case, the board stays standard-scoring **but gets a visible
wrong-format stamp** on the Methodology surface — mis-labelled is the failure; labelled is
survivable.

**Researcher can't confirm the suspension list confidently**: the founder does a 10-minute
news sweep of the top-100. An honest short list beats a comprehensive guess; an **empty**
fixture with a dated "checked, none found" row is a valid outcome. The check's existence is
the deliverable; its rows can grow.

**The Day-1 merge conflicts or breaks the suite**: cherry-pick the purely additive paths only
(`experiments/`, `tests/test_bottomup_prototype.py`, `tests/test_holdout_audit.py`,
`tests/test_floor_checks.py`) and leave `src/holdout.py` + `frontend/` for a review pass.
Nothing on the branch is load-bearing for the draft board; partial delivery is fine, silent
non-delivery is not.

**T6's 2026 roster data is gapped upstream**: fall back to T5 + T4-interim as the status layer
— bounded snapshot age plus a curated list covers the top-60 risk, which is where the damage
concentrates (pre-mortem failure 3). Note the gap in the round report and move on.

**W1 turns out bigger than one session**: stop at (a)+(b) (slug files + sync renames +
refuse-overwrite). The outbox and check extensions can trail. Do not ship a half-renamed
allocator — the current `max+1` is at least a *known* failure.

---

## What waits for Fable (~08-03), rather than being attempted badly without him

1. **Reading the session-3 experiment results** (R1 vacated-opportunity, QB arm) against their
   pre-registered predictions, and deciding the ADR-E amendment set. The registered-prediction
   discipline is the project's core asset; interpreting results against registrations is
   exactly the task the mandate reserves for the adversarial reviewer.
2. **The F-BOTTOMUP-CORE confirmatory registration** (with C3's rookie rule and R5's
   calibration family) and its red-team pass. Gated on H3.
3. **The hybrid-board recommendation** (QB provenance question) — evidence lands this session;
   the product decision and its traceability presentation need the full argument.
4. **Holdout governance** — the 2025-read exposure (session-2 finding 3) is carried honestly;
   any decision about unsealing, and any interpretation of numbers downstream of the historical
   read, waits.
5. **W-batch sequencing beyond W1/W8** — the 20-agent scale-up design.

---

## Work-order index (owner · cost · status · where the full spec lives)

| ID | One line | Owner | Cost | Status / this week? |
|---|---|---|---|---|
| T1 | Half-PPR consensus source + format assertion | data-ops+backend | 1 | **Day 2 — critical path #1** |
| T2 | Verify scoring vs live league page (stacking!) | founder+backend | 0.25 | **Day 1–2 — critical path #4** |
| T3 | Positive bye coverage | backend | — | Test built (red, on branch); fixed by T9 |
| T4 | Suspensions (interim fixture now, feed later) | researcher+backend | 0.75 | **Day 3–4 — critical path #3** |
| T5 | Snapshot freshness tripwire | backend | 0.25 | **Day 3 — critical path #2** |
| T6 | NFL roster-status ingest | data-ops | 1 | Day 4 |
| T7 | Depth-chart contradiction: one query | data-ops | min | Day 1 |
| T8 | Position cross-check | backend | 0.25 | Day 5 |
| T9 | Team-code canonicalisation | backend | 0.5 | Day 3 (un-reds T3) |
| T10 | Ranking uniqueness | backend | — | Built (clean, on branch) |
| W1 | Slug allocation + PM outbox | backend | 1 | Day 4 |
| W2 | ADR number allocation | backend | 0.25 | not this week |
| W3 | Shard status.md | librarian | 1 | not this week |
| W4 | CURRENT-STATE generated table | backend | 0.5 | not this week |
| W5 | Thread immutability protocol | librarian | 0.25 | not this week |
| W6 | DELIVERED/RESOLVED split | backend+librarian | 0.5 | not this week |
| W7 | CLAUDE.md truth pass | librarian | 1 | not this week |
| W8 | Backup: bundle/remote + data copies | data-ops+founder | 0.25 | **Day 1, first** |
| W9 | Worktree flow; merge stranded branches | integrator | 0.5 | Day 1 (merges only) |
| W10 | Reply-parser hardening | backend | 0.1 | not this week |
| R1 | Vacated-opportunity features | Fable | — | **This session (3)** |
| R2 | Coaching-staff table or strike feature | data-ops | gated | not this week |
| R3 | Week-indexed S1 output (ADR-E amendment) | strategist | 1 opus | Founder D4 |
| R4 | Red-zone/goal-line ingest | data-ops | 1 | weekend, if capacity |
| R5 | Register F-BOTTOMUP-CALIB | strategist | small | waits for Fable |
| R6 | ECR-error-vs-TD-excess check | backend | 0.25 | not this week |
| R7 | Correct edge-claim language | PM | min | not this week |
| N1 | Empty league standings/matchup tables | backend | 0.25 | Day 5 |
| N2 | Season/standings simulator | strategist→backend | 2+ | waits (needs R3) |
| N3 | Week-leverage utility (interim default) | backend | 0.25 | Day 5 |
| N4 | Roadmap: start/sit is not a prerequisite | PM | min | not this week |
| N5 | draft_sim refusal-comment pointer | librarian | min | not this week |
| H1 | Holdout audit tripwire | — | — | Built (on branch) |
| H2 | load_season rename | — | — | Built (on branch) |
| H3 | Prereg gate wiring | backend | 1 | Day 5, optional; gates confirmatory run |
| H4 | Structural read guard | — | — | Built (on branch) |
| C1 | Feature-manifest guard | backend | 0.25 | at ADR-E build time |
| C2 | Forbidden-language scope to product | librarian | 0.25 | not this week |
| C3 | Rookie-universe rule in registration | strategist | small | waits for Fable |
| 063 | Click-into-focused-field suggester fix | frontend | 0.5 | Day 2 (harness pins it) |

Full specs: T→`fable-table-stakes-2026-07-27.md` · W→`fable-workflow-2026-07-27.md` ·
R→`fable-ranking-design-2026-07-27.md` · N→`fable-in-season-2026-07-27.md` ·
H→`fable-overfitting-2026-07-27.md` · C→`fable-consensus-anchoring-2026-07-27.md` ·
pre-mortem checklist→`fable-draft-day-premortem-2026-07-27.md` (print it).

---

## AMENDMENT (2026-07-27, end of Fable session 3) — what the experiments changed

The R1 and QB experiments ran to completion (V3–V6, all registered before fitting; full
numbers in `experiments/bottomup/REPORT.md` session-3 appendix on the branch, narrative in
`FABLE-EXT2-2026-07-27.md`). Three things change in this plan; the day-by-day sequence,
decision list D1–D6, and critical path DO NOT change.

**1. The seventh founder decision is now a concrete recommendation (new D7).** The measured
answer to the hybrid-board question: consensus outranks or ties our best clean model at
every position (RB by −0.110 τ, QB by −0.241, WR/TE within noise, 2021–2024 descriptive).
*Recommendation: the 2026 board stays consensus-anchored; the bottom-up model ships as a
clearly LABELLED independent overlay at RB/WR/TE only — where it beats last-season-rank
with CIs clear of zero — and does not appear at QB. If you want mixed provenance in the
primary board anyway, every row must say where it came from, and the RB −0.110 gap gets
printed wherever the overlay is described.* This is a product-taste call and it is yours;
nothing else in the plan depends on it, and it can wait for Fable's return without cost.

**2. QB modelling is closed — add it to the do-NOT list.** Six registered configurations
across two sessions all lose to (or tie) ranking QBs by last season's points; the one
apparent win was a measured availability leak. Nobody should spend a session on QB model
variants this week or after. The only paths that could reopen QB are new information
sources (Vegas win totals / implied team totals — the missing `odds_snapshots` table), not
new estimators on existing data.

**3. The return-week registration package grows by one item.** The clean vacated/arrived
feature group (V5, self-exclusion mandatory) enters the ADR-E §4.1 amendment set alongside
R3/R5/C3 — it is the model's best measured improvement (RB Δτ +0.057 [+0.018,+0.095], VBD
+0.032, 10/13 folds). Also queued for the registration discussion, not for this week: the
rookie-situation channel via draft capital (the registered blind spot of V3/V5 and now the
leading remaining hypothesis for the RB consensus gap, since vacated-opportunity was
eliminated as the explanation).

Housekeeping note for the Day-1 integrator: the worktree now contains a local COPY of
`nfl.db` at `.claude/worktrees/fable-ext/data/nfl.db` (needed to run the full suite there;
gitignored, never committed). Delete it after merging if disk space matters.

---

## AMENDMENT 2 (2026-07-27, end of Fable session 4) — what the final session changed

Session log: `FABLE-EXT3-2026-07-27.md` on the branch (Job 1: ADR-E amendment E-A1;
Job 2: V7 registered → run → falsified). The day-by-day sequence and critical path
(T1 → T5 → T4 → T2, W8 first) DO NOT change. Five deltas:

**1. D4 is RESOLVED — spend nothing.** The R3 amendment the decision asked about was
written this session (ADR-E §A1, commit `324469d`, on the branch): week-indexed projection
object + N3 leverage weights, with sonnet work orders **R3-A** (`src/week_leverage.py`,
~0.25 session, no dependencies — this upgrades item 5.3's spec: mean-1 normalisation +
mandatory provenance label) and **R3-B** (`src/week_vector.py`, ~1 session, after the
T4-interim fixture lands). R3-B is a good weekend-slot item if capacity remains; neither
touches the critical path. The three consumers named as blocked (T4 games-adjustment, bye
cost, N3) now have their shapes.

**2. New one-minute founder check, fold into D3's platform visit:** while on the league
settings page for T2, also capture the **playoff week boundaries**. `league_config.py` says
`playoff_weeks=(16,17)`; the founder's own session-4 note says championships are weeks
15–17. One of these is wrong; every leverage-weighted number keys off the config value.

**3. The rookie-situation channel is OFF the return-week list — tested and falsified this
session.** V7 (registered `5af349e` before any code; results on the branch, REPORT.md
session-4 appendix): RB improved on neither co-primary and the consensus gap did not move
(−0.110→−0.112). Both top-ranked gap hypotheses (vacated opportunity, rookie arrivals) are
now clean eliminations. **Nobody should spend sessions on further RB-gap hypotheses**; the
return-week registration discussion is now exactly: F-BOTTOMUP-CORE on V5 (+ R5 calibration
family + C3 rookie-inclusion universe rule — C3 remains live because it answers "should we
rank rookies at all", not "why do our veteran ranks trail ECR"). H3 remains its gate and
remains NOT STARTED, clean.

**4. Merge note update for the Day-1 integrator (D2 unchanged: merge).** The branch now
also carries: the ADR-E draft + E-A1 amendment (`docs/adr-drafts/`), the V7 experiment
(additive, `experiments/` + `tests/`), and the session-4 landing note. Still nothing
touching production `src/` or `frontend/`. Two practical points: (a) `docs/adr-drafts/
ADR-E-bottom-up-projection-framework.md` and `docs/reviews/ACTION-PLAN-2026-08.md` are now
TRACKED on the branch while byte-identical UNTRACKED copies sit in the master working copy —
delete the untracked copies before merging or git will refuse the checkout; (b) suite
baseline on the branch is now **539 passed + 1 by-design failure (T3)**.

**5. Standing prior for anyone registering predictions in Fable's absence:** four of five
registered prediction sets across sessions 3–4 were materially wrong, every miss
over-crediting a situation story. Halve the intuitive weight of situation narratives before
freezing a prediction band. (This is a calibration note, not a rule change.)

---

## PM AMENDMENT (2026-07-27) — D3/D6 resolved, T1 re-scoped to three leagues

**D6 — RESOLVED.** Draft date target: **2026-08-30** (readiness buffer, provisional so it can
move). T-7d = 2026-08-23. This is a deliberate buffer, not the real date: the Westwood (Yahoo,
primary) league's actual scheduled draft is **2026-09-07**, confirmed from
`docs/screenshots/League Settings 2.png`. Founder's own words, asked directly: *"let's just use
August 30th to make sure everything is ready then."* The other two leagues (see below) have
draft dates not yet known. Full capture: `docs/founder-requests.md` FR-011.

**D3/T2 — RESOLVED.** Founder confirmed from the live platform that yardage bonuses **stack** at
thresholds (`scoring.py`'s existing `>=` loop is correct, no code change). Founder-supplied
Yahoo screenshots (`docs/screenshots/League Settings 2-5.png`) are the T2 fixture source,
dispatched to backend this session to land as `tests/fixtures/league_scoring_live.json` +
`decisions.md` ADR-052. Full capture: FR-013.

**Bonus resolution the screenshots weren't asked for but answered anyway:** Westwood turns out
to be the **primary league itself** (Yahoo-hosted), not a separate "Yahoo, different scoring"
league as originally framed. This closes CLAUDE.md §7's "league size not yet confirmed" gap —
**10 teams** — and supplies the roster shape (QB/3WR/2RB/TE/2 FLEX/DEF, 6 bench, 1 IR) for the
first time.

**T1 is now three leagues, not one — re-scoped, does not change the critical path order.**
Westwood needs no rework (T1 as originally scoped already targets its exact format). Two more
leagues exist: a second, distinct Yahoo league and an ESPN league (~12-14 teams, founder
unsure which), both with different scoring and team counts, **neither with data supplied yet**.
This is now thread 067 (`data-ops`, `backend`), blocked on the founder providing the same two
screenshots Westwood provided, for each of the other two leagues. Estimated added cost:
**+1 to +1.5 session-units** on top of T1's original 1, contingent on how far each league's
scoring sits from a FantasyPros STD/HALF/PPR preset (see thread 067 for the full cost argument).
Do not silently absorb this into T1's original 1-unit estimate — it was budgeted for one format,
not three.

**New work order, T4's `data feed` half formalized:** the founder additionally directed a
**recurring** injury pull (nflverse, weekly in-season) plus a hand-maintained suspension
watchlist with a **weekly researcher sweep** — explicitly not a probability model. Dispatched as
thread 070 (`data-ops`, `researcher`), feeding E[games_played] per ADR-E Amendment E-A1. This
formalizes and extends T4-interim/T4/T6 beyond this week's interim fixture into a standing,
dated cadence — see thread 070 for the full spec. Full capture: FR-014.
