# Fable B1 — v2 build log

Mandate: `docs/fable-mandate-B1-2026-08-01.md` (build mandate, not review). Branch
`claude/pm-agent-setup-gobxa0`. Run started 2026-08-01, the end-of-week slot before the Monday
11:00 reset — same slot as M2 earlier today, second dispatch of the day, founder-authorised.

## WHERE THIS STANDS

Registration committed before any evaluative number. Environment verified (DB copied per
`docs/environment.md` §4; coverage measured: `rosters_weekly` wk1 2002–2025, weekly stats 1999+,
injuries 2009–2024). Architecture finding recorded (log §A1): the component model already emits
stat lines and `score_components()` already re-scores without refit — Priority A is an ordering-path
and packaging problem, not a rebuild. The deficit is `pos_model._availability`: one OLS on arm-A
features with no resolved-vs-ongoing signal. Registered arms G0/GN/G1/G2 in
`docs/ranking/factor-campaign-manifest/batch-B1.md` (m_b = 12). No code built yet.

## NEXT STEP

Build `experiments/bottomup/v2/`: (1) `weekshape.py` — gated loader for within-season timing of
N−1 (last week played, late-4 share), following `pos_data.py`'s loader pattern (SQL `season < ?`
param + HoldoutViolation check + a `V2Panel(SeasonPanel)` accessor `weekshape_before(cutoff)` that
appends to the access log); (2) `features_v2.py` — wrap `build_features`, add the registered G1
feature block (frozen list in batch-B1.md §3) and the G2 proxy block from
`panel.preseason_roster(N)`; (3) `games_model.py` — binomial GLM (existing `binom_glm`) of
(games, season_len) on the G1 features, per position, veterans; (4) model subclasses overriding
`_availability`; (5) `run_v2.py` — WalkForward subclass (override `_make_model`) running arms
G0/G1/G2, targets 2018–2024, M-panel universe, writing
`experiments/bottomup/results/ranking_v2_<arm>_players.csv`. Then evaluate exactly the batch-B1
endpoints, grade, and only then the portability demo (`rescore_demo.py`, three configs, zero
refit). Commit after each file if the pool is tight.

## TOKENS USED

~120k context consumed at registration commit (estimate from context size; no meter; ±20%).

---

## LOG

### 2026-08-01 · B1 start — mandate constraints restated

Scope: bottom-up rankings only; draft-availability and recommender out of scope. Bar: absolute
quality against realised outcomes (ADR-069) — consensus is neither input nor steering signal;
§6.5 is a release gate run later by someone else. Holdout 2025 sealed; seasons through 2024 only.
Standing conflict acknowledged: I am builder and gate in one; `strategist` reviews before anything
ships, and nothing merges on my sign-off. My own default constraint ("produce documents, modify
nothing") is superseded for this session by the founder-authorised build mandate; everything I
touch stays in `experiments/bottomup/`, `docs/fable/`, `docs/ranking/factor-campaign-manifest/`,
and `ranking_versions/` — no `src/`, no PR-007 files, no recommender, no exports.

### 2026-08-01 · A1 — architecture audit before building (Priority A is smaller than billed)

Verified in code, not docs: `pos_model.py` component models **already output stat lines**
(`proj_targets/receptions/rec_yards/rec_tds/carries/rush_yards/...` per player-season) and
`score_components()` **already re-scores a stored projection under a different ruleset without
refitting**, including stacking bonuses via stored per-game exceedance columns `p_<fam>_<t>`
(evaluable at any threshold already modelled; an unmodelled threshold needs its own GLM — a stat
fit, not a league fit; limitation stated, not hidden). What v1 lacked was not stat lines; it was
an ordering path independent of consensus: `ranking_v1.v1_scores()` starts from the crowd's
rank column and pins rookies to crowd slots. **v2's ordering path = sort by points computed from
stat lines under the league config. No consensus column is read anywhere in it.** Priority A is
therefore: (a) the independent orderer, (b) a versioned stat-line artifact + scoring layer,
(c) the portability demonstration. The heavy build goes to Priority B, where the mandate put it.

### 2026-08-01 · A2 — where the games deficit mechanically lives

`pos_model.BaseComponentModel._availability`: `clip(OLS(arm features), 0, 1) × season_len`, arm A
= `[gshare_w, gshare_1, present_1, age, age2, evidence]`. Nothing in any arm (A–E) distinguishes
an absence that **resolved before season end** (player returned, played late) from one **ongoing
at season end** (IR into January) — the Burrow/Hill class M2-1 measured at 86–131% of the market
excess. The injury table cannot fix this (covers 2.5–4.8% of ≥9-game absences,
`pos_data.load_depth_seasons` docstring, measured); the *weekly box score itself* carries the
timing signal (which weeks of N−1 were played), and `rosters_weekly` wk-1 status (2002+,
RES/PUP/SUS/ACT) carries the entering-N state, at the documented as-of caveat (late-August
cutdown ≈ draft date, not strictly before). Hence arms G1 (end-of-N−1 timing only) and G2
(+ wk-1 status, proxy-tagged, adoption conditional on a strategist as-of ruling).

### 2026-08-01 · Registration committed (this commit)

`batch-B1.md`: m_b = 12 graded cells (C-A games-ordering G1−GN ×4 positions; C-B downstream
absolute quality G1−G0 ×4; C-C G2−G1 ×4), thresholds, adoption rules, and predictions frozen
before any arm is fitted. `ranking_versions/v2.json` written with `"status": "registered"`;
every knob the runner will read lives there. Seed 20260801, reps 4000, season-block bootstrap,
paired per cell. Evaluation universe: M-panel (FFC ADP membership defines the subset; the column
is never a feature, never an ordering input), **veterans only** for all graded cells; rookies and
full universe descriptive. 2025 never read; targets 2018–2024.
