# Fable B1 — v2 build log

Mandate: `docs/fable-mandate-B1-2026-08-01.md` (build mandate, not review). Branch
`claude/pm-agent-setup-gobxa0`. Run started 2026-08-01, the end-of-week slot before the Monday
11:00 reset — same slot as M2 earlier today, second dispatch of the day, founder-authorised.

## WHERE THIS STANDS

**Built, run at full span, graded, recorded.** v2 exists end to end: stat-line projections through
an ordering path with no consensus input anywhere, a swappable scoring layer demonstrated on three
league configs with zero refits, and a games component tested as four registered arms against the
naive-persistence bar. Grading (batch-B1 + Amendment 1, 20 cells, BH at campaign M=92):

- **G1a (end-of-N−1 timing repair) REJECTED by its own rule** — 0 WIN, 1 BH-robust HARM (WR
  −0.0125) on downstream absolute quality. The games *component* beats naive persistence at RB
  only (+0.084, BH-robust) — the mandate bar is earned at one position of four.
- **G2a (+ week-1 roster status) passes its numeric rule — 3 WIN, 0 HARM** (RB +0.072 and WR
  +0.048 BH-robust, QB +0.019 CI-level) and is the only arm that beats naive persistence on games
  MAE (3 of 4 positions). **Its adoption is conditional on the strategist as-of ruling** (wk-1
  status ≈ late-August cutdown: known by a Labor-Day draft, days late for a mid-August one) —
  handoff thread opened. Until that ruling, **v2's default games arm is G0** (v1's), per the
  registered fallback branch.
- The founder's one-sentence version: **the timing-of-absence repair alone did not fix games;
  who-is-on-the-roster-and-able-to-play at cutdown is where the real signal is, it is worth
  +0.05–0.07 rank correlation at RB/WR, and whether we may use it turns on a draft-date question
  now with strategist — not on model quality.**

## NEXT STEP

For my successor (or me, post-reset), in order: (1) **do not re-run anything** — results are
committed under `experiments/bottomup/results/ranking_v2_*`; grading is final in batch-B1.md.
(2) The open decision is the strategist thread on G2a's as-of alignment; if ruled acceptable
(possibly with a date-alignment condition, e.g. rebuilding the two indicators from a
cutdown-dated source), flip `ranking_versions/v2.json` games arm to G2a and re-emit the artifact;
if rejected, v2 ships with G0 games and the games deficit stays the named open defect.
(3) Candidate next registered arms, NOT run, NOT stacked: fit-population weighting for the
−2.6-game board-veteran level bias; a two-stage (participation × games|playing) split; suspension
lists as a dated source. Each is one arm, one change, registered into this manifest before
fitting. (4) The §6.5 four-baseline release gate against both crowds is deliberately UNRUN —
it belongs to a later session, run by someone other than fable, on the version that survives
strategist review.

## TOKENS USED

Final: ~215k context consumed across the build (estimate from context size; no meter; ±20%).
Commit ledger: registration `a80c2e3` · package `a9d7b75` · Amendment 1 `fba26a9` · scoring layer
+ demo `7cf5bb8` · full run + grading `86a5207` · closeout (this commit).

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

### 2026-08-01 · Full-span results and grading (after the background run, exit 0, audits clean)

The 20 graded cells, verbatim from `ranking_v2_contrasts.csv` (paired season-block bootstrap,
4,000 reps, seed 20260801, n=7 seasons/cell; BH at campaign M=92):

| contrast | QB | RB | WR | TE |
|---|---|---|---|---|
| C-A  G1−naive (ρ games) | −0.029 NULL | **+0.063 WIN** | +0.048 NULL | −0.077 NULL |
| C-B  G1−G0 (ρ points) | −0.003 NULL | −0.014 NULL | **−0.0134 HARM (BH)** | −0.012 NULL |
| C-A′ G1a−naive (ρ games) | −0.037 NULL | **+0.084 WIN (BH)** | +0.053 NULL | −0.109 NULL |
| C-B′ G1a−G0 (ρ points) | −0.009 NULL | +0.008 NULL | **−0.0125 HARM (BH)** | +0.002 NULL |
| C-C  G2a−G1a (ρ points) | **+0.019 WIN** | **+0.072 WIN (BH)** | **+0.048 WIN (BH)** | +0.049 NULL |

Adoption per the frozen rules: **G1 rejected, G1a rejected (0 WIN / 1 HARM each on C-B/C-B′);
G2a passes numerically (3 WIN / 0 HARM), adoption conditional on the strategist as-of ruling.**
The WR HARM in both B-contrasts is the registered downside mechanism (variance injected into
healthy-veteran games at the position where v1's games handling was already benign); recorded,
not re-tuned. Registered predictions vs outcomes, honestly: C-A′ predicted wins at RB/WR/QB —
delivered at RB only; C-B′ predicted wins at QB/RB — delivered nowhere; C-C's shape (wins where
end-of-N−1 is ambiguous) is consistent with what wk-1 status resolves. My registered story was
directionally right about the *class* of signal and wrong about how much of it end-of-N−1
information carries — that miss is the finding.

Descriptive levels (uncorrected): absolute steering metric mean ρ(points) G0 → G2a: QB
0.245→0.255, RB 0.440→0.519, WR 0.560→0.595, TE 0.397→0.447. Games MAE: only G2a beats naive
(RB 3.06 vs 3.64, WR 2.67 vs 3.07, TE 2.67 vs 2.95; QB 3.46 vs 3.10 — naive still ahead at QB).
Absolute games ordering ≤0.27 everywhere: **most of the D1 oracle gap is irreducible from
September-available information; wk-1 status buys the reachable slice.** Level bias on board
veterans (~−2.6 games, G0/G1/G1a) named and open; G2a shrinks it.

### 2026-08-01 · Portability demo — after catching a false-PASS defect in it

First run of the demo printed 0 rank changes across all 12 config-pairs — superficially "orders
identical", actually all-NaN points silently ordered by the player_id tie-break: the
multi-position artifact carries QB-only columns as present-but-NaN on other positions and
`score_components` propagated NaN. The per-position pipeline never hits this (absent columns
become zeros). Fixed in `scoring_layer.score_stat_lines` (explicit NaN→0 on the stat contract
plus a refuse-to-rank-on-non-finite guard), recorded because the broken version *looked like a
clean pass*. After the fix, real magnitudes: half-PPR→full-PPR reorders 15/23 top-24 RBs (max
5 slots), 12/23 WRs; standard-6pt moves QBs (12–14 changes); zero fitting calls by construction.
The consensus-derived board structurally cannot do this — which is ADR-069's point.

### 2026-08-01 · Closeout

Strategist thread opened (`docs/handoffs/2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie.md`)
carrying the one open decision (G2a as-of) and the ship review — nothing merges on my sign-off.
Session narrative `docs/status/2026-08-01-fable-b1-v2-build.md`; CURRENT-STATE updated in place;
OPEN.md and status INDEX regenerated. What v2 does NOT do, stated once more so no summary
inflates it: no DEF, no real rookie model, no cross-positional grading, no §6.5 comparison (that
gate runs later, on the post-review version, by someone else), and its games component — even at
its conditional best — captures a modest slice of an availability channel that is mostly
unknowable in September. The 2025 holdout was never read; the founder's "don't unlock 2025" was
never at risk. Mandate scope respected: no draft-availability work, no recommender work, no
PR-007 files touched, nothing in `src/`.

### 2026-08-01 · Registration committed (earlier commit)

`batch-B1.md`: m_b = 12 graded cells (C-A games-ordering G1−GN ×4 positions; C-B downstream
absolute quality G1−G0 ×4; C-C G2−G1 ×4), thresholds, adoption rules, and predictions frozen
before any arm is fitted. `ranking_versions/v2.json` written with `"status": "registered"`;
every knob the runner will read lives there. Seed 20260801, reps 4000, season-block bootstrap,
paired per cell. Evaluation universe: M-panel (FFC ADP membership defines the subset; the column
is never a feature, never an ordering input), **veterans only** for all graded cells; rookies and
full universe descriptive. 2025 never read; targets 2018–2024.
