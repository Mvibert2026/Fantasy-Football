# Factor batch C3 — candidate definitions (not registered, not run)

**backend, 2026-08-02.** Definitions only, dispatched to be "ready to run the moment the new
instrument lands." **Nothing in this file has been fitted, graded, or registered into the campaign
manifest** — that is `ranker`'s call, at the point one of these is actually about to be tested, per
this batch's own dispatch instruction.

---

## 0. NEXT STEP / blocking dependency — read before anything else

The dispatch named `experiments/bottomup/v2/factors_c1.py` and `factors_c2.py` as "the contract,
follow it exactly." **Neither file exists in this checkout.** Verified three ways before writing
anything: `find` across the whole repo, `git ls-tree -r origin/main` after `git fetch`, and a text
grep of every file under `docs/` for `bottomup/v2`, `factors_c1`, `factors_c2`, `batch-C1`, `batch-C2`
(capital-C naming, distinct from the existing lowercase `factor-batch-N` docs for batches 1–7). Zero
hits anywhere, on `main`, `origin/main`, or this worktree.

**Most likely explanation:** a concurrent `ranker` session is building the v2 rewrite (ADR-069,
"independent of consensus," `CLAUDE.md` §2a) in a sibling worktree that has not merged. Worktrees
are isolated from each other (`docs/environment.md`), so this session cannot see it even if it
exists on disk elsewhere right now.

**What was done instead of stopping:** `experiments/bottomup/v2/factors_c3.py` is written against
the closest interface that does exist and is verified — `experiments/bottomup/components/pos_data.py`'s
`SeasonPanel` / `HOLDOUT_SEASON` / `HoldoutViolation` / `CutoffViolation` / `feature_gate` machinery,
which every v1 factor batch (1–7) already builds on, and the "own local Sources pack with its own
gate, appending to `panel.access_log`" pattern is copied structurally from
`experiments/bottomup/factors/factor_features7.py::Batch7Sources`, the newest such pack in the repo.

**When `factors_c1.py`/`factors_c2.py` land:** diff `factors_c3.py`'s `BatchC3Sources` and its six
`attach_*` builder signatures against theirs. If the real v2 harness uses a different panel object,
naming convention, or `*_known` pattern, this file's *shape* — one Sources pack, one loader per
source, one builder per factor, mandatory `*_known` — should still port; only plumbing should need
to change. Flagged to `ranker`/`pm` via a handoff thread this session (see reply log below), not
silently assumed compatible.

**All six loaders and `attach_*` functions were smoke-tested against the real `data/nfl.db`** (copied
into this worktree per `docs/environment.md` §4, never hardlinked) — every block runs end to end and
produces plausible values. This is a runtime smoke test, not a unit-test file and not a fit; no
number below has been measured for predictive power.

---

## 1. Scope decisions that deviate from the dispatch's own priority order

The dispatch's priority list puts `odds_snapshots` first. **No odds-based factor is defined here.**
On a closer read of `docs/factor-ledger.md`:

- **T0-11** ("Vegas win totals & implied team totals") — `blocked`. Reason given: *"No odds table
  exists in `nfl.db`... Historical odds require a paid source."*
- **N12** ("Game total / team spread as player-model features") — `blocked`, same reason, plus:
  *"the whole team-environment channel is oracle-bounded at ≤ +0.055 τ_b"* (`bottom-up-research-pass-1`).

`odds_snapshots` (2018–2024) now exists in `nfl.db` — the data-availability half of that exclusion is
stale. But this batch's dispatch is explicit: *"Rows excluded for data availability or licensing
still stand — do not resurrect them."* The row's second reason (an oracle ceiling of ≤+0.055 τ_b) is
a substantive null finding, not a data-availability one, and it is not obviously a "measured NULL
under the old consensus-derived frame" either — that phrase in the dispatch describes results biased
by scoring against a consensus-derived board, and the oracle-ceiling number does not obviously have
that defect.

**This is a genuine tension between two written instructions in the same dispatch and is flagged,
not resolved unilaterally.** No odds factor is defined in `factors_c3.py`. Recommend `ranker`/
`strategist` decide explicitly whether T0-11/N12 reopen now that the table exists, and whether the
oracle-ceiling number should be re-derived under the v2 (independent-of-consensus) frame before that
decision is made either way.

**Also not resurrected, same logic, both already dispositioned in the ledger:**
- **T1-22** "PROE" — `blocked`, reason given was "no PBP table in `nfl.db`," also now stale (`pbp`
  exists, 2009–2025) but not resurrected here. **N20** "Neutral-situation pass rate" is used instead
  (Factor G below) — it is `untested` (not `blocked`) and the ledger itself describes it as *"distinct
  from T1-22 — a situational filter, not a model residual."*
- **T1-25** "NFL draft capital" — `included`, already a built feature (`pos_features.py:222-227`,
  `draft_round`/`draft_pick`/`log_draft_pick`/`undrafted`). Factor F below is deliberately **athletic
  testing only**, not draft capital, so as not to re-propose something already in the model.

`snap_counts` is also not used — the dispatch's do-not-duplicate list names "snap share" as already
built in C1/C2, and `snap_counts` is the only source for that construction, so a second cut of it
risks being the same feature under a different name without the real interface available to check.

---

## 2. The seven-source priority, and where each factor sits in it

| priority | source | used? | factor(s) |
|---|---|---|---|
| 1 | `odds_snapshots` | **no** — see §1 | — |
| 2 | `injuries` + practice participation | yes | C, D |
| 3 | `depth_charts_weekly` | yes | E |
| 4 | `combine` | yes | F |
| 5 | `pbp` | yes | G |
| 6 | `ff_opportunity` | yes | H |
| 7 | `snap_counts` | no — see §1 | — |

---

## 3. Factor definitions

Grading is declared at **S=12, tier 2 (2013–2024)**. Every factor states its own usable span inside
that window and whether/how it truncates it, per the dispatch's explicit requirement.

### C — Injury report-week burden

- **Mechanism.** A player who appeared repeatedly on the injury report in the prior season, weighted
  by how severe the listed status was, carries elevated re-injury/chronic-issue risk into the new
  season — durability is not i.i.d. year to year. Leading/persistence signal, distinct from
  `pos_features.py` arm B (`inj_missed_share_1`), which explains games *already* missed in the
  season being scored rather than risk carried forward.
- **Source.** `injuries.report_status`, per (player, season, week). Measured floor: 2009 has 17 rows
  (not real coverage); 2010 has 4,429.
- **Usable span.** Feature seasons 2010+, so first predictable target season is **2011** — full
  coverage of the 2013–2024 grading window, no truncation.
- **Control.** `injury_known` = 1 iff the player has ≥1 lag season with `gsis_id`-matched coverage in
  `injuries` (2010+); a not-listed week within a covered season is a true zero, not unknown.
- **Columns.** `injury_burden_prior_w`, `injury_known`.

### D — Practice-participation severity

- **Mechanism.** How much practice time a player missed (Limited / Did Not Participate vs. Full)
  captures underlying severity independent of whether he ultimately suited up — a more granular
  signal than game-day status alone, and distinct from Factor C: C counts *how often* he was listed
  and how severely; D measures, *conditional on being listed*, how much practice he actually missed.
- **Source.** `injuries.practice_status`, same table, same 2010 floor as C.
- **Usable span.** 2010+, first predictable target season **2011** — full grading-window coverage.
- **Control.** `practice_known` = 1 iff ≥1 lag season had ≥1 week with a recognised practice status
  (the `'\n    '` and `'Note'` values are data artifacts, treated as unknown, not a status).
- **Columns.** `practice_severity_prior_w` (empirical-Bayes shrunk, k0=8 weeks, fixed a priori),
  `practice_known`.

### E — End-of-prior-season depth-chart ordinal rank

- **Mechanism.** A team's own coach-stated depth-chart order at the *close* of the prior season is a
  direct, explicit statement of role, and captures late-breaking role changes (a rookie who passed a
  veteran in November, an injury-forced promotion that stuck) that lag stat features average away
  across a whole season.
- **NOT week-1-of-target-season data.** `depth_charts_weekly` has no true preseason rows — `game_type`
  is only REG/WC/DIV/CON/SB/SBBYE, and the earliest REG-season row for a season is its Week-1 chart.
  Strategist ruled Week-1-of-target-season data out as kickoff-dated (after the founder's 7 September
  draft). This factor sidesteps that entirely by using the **last REG week of season N−1** — strictly
  "data through the end of season N−1" per `CLAUDE.md` §6.1, with no judgment call about whether a
  given Week-1 chart predates a given year's draft date.
- **Limitation, stated plainly.** This is a role-*continuity* signal for returning players. It says
  nothing new for a player who changes teams in the offseason — that gap is what Factor F (combine,
  for rookies) and the existing `load_preseason_rosters` proxy (club membership, not depth position)
  are for.
- **Overlap declared, not claimed away**, vs. `pos_features.py` T0-5 arms (`depth_first_share_1`,
  `rostered_absent_share_1`, `offroster_share_1`): those measure *share of weeks* listed
  first/on-roster/off-roster *during* the scored season, to explain availability. This factor is a
  single ordinal *snapshot* at season N−1's close, used as an opportunity signal for season N. Same
  table, different construction, different question — no independence claimed.
- **Source.** `depth_charts_weekly`, 2001–2024 (measured floor). `gsis_id` populated on every row (0
  nulls, checked).
- **Usable span.** 2001+, first predictable target season **2002** — full grading-window coverage, no
  truncation.
- **Control.** `depth_end_known` = 1 iff the player has a resolved depth-chart row in the immediately
  prior season (lag-1 only — a 2–3-year-old snapshot has been superseded by definition, no
  recency-weighting question here).
- **Columns.** `depth_end_rank_prior1`, `depth_end_known`. Unknown players filled with rank 4 (a
  fixed worst-of-typical value, not `_median_fill` — deliberate deviation, documented inline).

### F — Combine athletic-testing composite (the rookie-relevant factor)

- **Mechanism.** Per `CLAUDE.md` §2a's rookie ruling: every lag feature a veteran projection rests on
  is *structurally absent* for a rookie. Combine testing (40-yard, vertical, broad jump, 3-cone,
  shuttle, bench) is the one pre-Week-1 signal that exists for every drafted player regardless of NFL
  experience, and stands in for the missing lag features specifically for athletic ceiling — not for
  role, which is draft capital (already built, T1-25) plus depth chart (Factor E, veterans only).
  **Must be fit as a full interaction with a rookie indicator, never a shared slope with veteran
  features**, per the ruling — flagged here for whoever fits it; not enforced by this definitions-only
  file.
- **Why not registry N34's named formulas (Speed Score/Burst/Agility).** N34 is `untested`, "no
  predictive evidence published for any of them." This factor is a simpler position-relative z-score
  composite instead, so as not to inherit an unvalidated external formula uncritically.
- **`combine` is read by no projection model** — verified this session via `grep -rl "FROM combine\|
  load_combine" src/ experiments/`, zero hits outside side-experiments.
- **Source.** `combine`, keyed on `pfr_id`, crosswalked to `gsis_id` via `player_ids` (same crosswalk
  pattern as batch 7's snap-count join). 8,968 rows, draft years 2000–2026.
- **Usable span.** A player's combine year is fixed at his `draft_year` and used identically in every
  season of his career — **no truncation at all** inside 2013–2024; every drafted player in the
  window either has a combine row or `combine_known=0` (a real zero-information case for
  UDFA/combine-skippers, not a data gap).
- **Control.** `combine_known` = 1 iff ≥1 of the five tests is non-null for that player.
- **Columns.** `combine_z` (mean of available position-×-draft-class z-scores, time events sign-flipped
  so higher is always better), `combine_known`.

### G — Neutral-situation team pass rate

- **Mechanism.** A team's pass rate when the score is close and it is not the two-minute drill is the
  cleanest available read of that team's own offensive identity (pass-funnel vs. run-funnel), net of
  the confound that trailing teams pass more and leading teams run more regardless of scheme.
- **Why not T1-22 (PROE), which is `blocked` in the ledger for data availability and not resurrected
  per §1.** N20 is `untested`, and the ledger itself calls it "distinct from T1-22 — a situational
  filter, not a model residual" — it does not depend on any play-calling expectation model's
  specification the way a PROE residual would.
- **Neutral defined, fixed a priori.** `|score_differential| ≤ 7`, `down ∈ {1,2,3}` (4th down is
  overwhelmingly punt/FG, not a play-calling choice in the same sense), `half_seconds_remaining >
  120` (excludes two-minute-drill plays in both halves). REG season only.
- **Source.** `pbp`, 2009–2025 — `score_differential`/`down`/`half_seconds_remaining` all present
  from the table's start (measured, not assumed).
- **Usable span.** 2009+, first predictable target season **2010** — full grading-window coverage, no
  truncation.
- **Control.** `neutral_pass_known` = 1 iff the lag team-season has ≥50 qualifying neutral plays
  (below that, treated as unknown rather than a noisy rate). Team-level, not player-level; requires
  the caller to resolve a per-lag `team` column (team of record for that player-season) before
  calling `attach_neutral_pass_rate` — enforced with an explicit `ValueError`, not a silent no-op.
- **Columns.** `neutral_pass_rate_prior_w`, `neutral_pass_known`.

### H — Efficiency-over-expected rate

- **Mechanism.** Separates skill from volume. `ff_opportunity` already ships
  `total_fantasy_points_diff` (actual − xFP), which is almost certainly what the already-built xFP
  factor (T1-18, in C1/C2 per the do-not-duplicate list) uses — an *aggregate*, volume-scaled number
  where a high-volume merely-average player and a low-volume elite one can post the same total. This
  factor instead rate-normalizes by opportunity count (targets + carries + pass attempts) to isolate
  "was he more efficient than the model expected *given his role*" — a persistence-of-skill signal,
  not a persistence-of-role one.
- **Overlap declared, not claimed away.** Same source table, adjacent construction to the existing
  xFP factor; no independence from that arm is claimed here.
- **Source.** `ff_opportunity`, 2006–2025 (table's own measured floor; note `season` is stored as
  TEXT, cast to INTEGER on read).
- **Usable span.** 2006+, first predictable target season **2007** — full grading-window coverage, no
  truncation.
- **Control.** `yoe_known` = 1 iff ≥1 lag season has a positive opportunity count in `ff_opportunity`
  (zero opportunities is absence, not a zero rate, and must not silently become 0.0).
- **Columns.** `yoe_rate_prior_w` (empirical-Bayes shrunk, k0=40 opportunities, fixed a priori),
  `yoe_known`.

---

## 4. What was NOT done in this pass

- No factor was registered into `docs/ranking/factor-campaign-manifest/` — that is `ranker`'s call,
  at the point one of these is about to be fitted, per the dispatch.
- No factor was run, fit, or graded. §0's smoke test confirms the code executes against real data and
  produces plausible values; it is not evidence of predictive power.
- No ADR was opened — this batch adds no new decision, only candidate definitions.
- `factors_c1.py`/`factors_c2.py` were not touched (they do not exist to touch), and
  `docs/ranking/batch-C1-results.md`/`batch-C2-results.md` were not touched (same).
