# Fable B1 — v2 build log

Mandate: `docs/fable-mandate-B1-2026-08-01.md` (build mandate, not review). Branch
`claude/pm-agent-setup-gobxa0`. Run started 2026-08-01, the end-of-week slot before the Monday
11:00 reset — same slot as M2 earlier today, second dispatch of the day, founder-authorised.

## WHERE THIS STANDS

Package built and committed (`experiments/bottomup/v2/`): gated weekshape loader + `V2Panel`,
feature builders, `GamesGLM`, model subclasses, runner, scoring layer, portability demo. Pipeline
verified end-to-end under this container's pandas 3.0.5 (the harness had only ever run under the
repo's conda pandas 2.x — only PerformanceWarnings, no API breaks). Smoke test (TE+RB 2018–2019)
exposed a real specification gap in the registered G1 block — logged verbatim in batch-B1
Amendment 1 before any amended arm ran; G1a (= G1 + `gshare_1`) and G2a registered, m_b 12→20,
campaign M = 92. **The full run (arms G0, G1, G1a, G2a × QB/RB/WR/TE × 2018–2024) is executing in
the background now.** No full-span number has been seen yet.

## NEXT STEP

When the background run finishes: (1) read `experiments/bottomup/results/ranking_v2_contrasts.csv`
and the per-arm `ranking_v2_<arm>_cells.csv`; (2) grade cells 1–20 exactly per batch-B1 +
Amendment 1 (WIN/HARM/NULL by 95% CI, BH at campaign M=92, adoption rules as registered — G1a
adopted iff C-B′ ≥2 WIN 0 HARM; G2a conditional additionally on a strategist as-of ruling);
(3) run `python3 -m experiments.bottomup.v2.rescore_demo --arm <adopted-or-G1a>` for the
portability demonstration (descriptive); (4) write results + honest-statement sections here and
in a results doc; commit; (5) update `ranking_versions/v2.json` status registered→ran, with the
adopted arm named. If the session dies mid-run: the run command is
`python3 -m experiments.bottomup.v2.run_v2 --arms G0,G1,G1a,G2a` from the worktree root (~1 h);
everything it needs is committed; the grading rules live in batch-B1.md and are not to be
re-derived.

## TOKENS USED

~165k context consumed at full-run launch (estimate from context size; no meter; ±20%).

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

### 2026-08-01 · Smoke test and Amendment 1 (peek recorded, then registered, then coded)

Smoke: TE 2018–2019 then RB 2018–2019, arms G0/G1 only. Three facts. (1) **G0 faithfully
reproduces the v1 games pathology** (TE ρ_games 0.104/−0.080 vs naive 0.295/0.658) — the control
is honest. (2) **G1-as-registered does not fix it** (TE pooled 0.073 vs naive 0.477; RB 0.287 vs
0.277 — parity at best), and both arms carry a −2.6-game level bias with compressed spread on
board veterans (project median ~12, realised median 15 — the full-universe-vs-board pathology at
the *fitting* level, the same geometry F4 named). (3) The mechanism is expressible in one
sentence: **the registered block cannot represent "resolved absence still carries moderate
risk"** — healthy veterans collapse to a single point (both interactions vanish at miss1=0) and a
resolved-miss veteran's persistence information survives only through `miss1_x_resolved`'s
coefficient, while naive `games_1` keeps it directly. Amendment 1 (batch-B1) adds the standalone
lag-1 level: G1a = G1 + `gshare_1`, G2a = G1a + week-1 status; G2-on-G1 withdrawn never-run;
m_b 12→20; predictions amended and the G1 cells kept — they will be reported at full span as a
mechanism check, not buried. TE is pre-declared as likely unresolvable (n≈10/season).

### 2026-08-01 · Registration committed (earlier commit)

`batch-B1.md`: m_b = 12 graded cells (C-A games-ordering G1−GN ×4 positions; C-B downstream
absolute quality G1−G0 ×4; C-C G2−G1 ×4), thresholds, adoption rules, and predictions frozen
before any arm is fitted. `ranking_versions/v2.json` written with `"status": "registered"`;
every knob the runner will read lives there. Seed 20260801, reps 4000, season-block bootstrap,
paired per cell. Evaluation universe: M-panel (FFC ADP membership defines the subset; the column
is never a feature, never an ordering input), **veterans only** for all graded cells; rookies and
full universe descriptive. 2025 never read; targets 2018–2024.
