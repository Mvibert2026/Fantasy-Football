# Batch B1 — Fable build mandate: v2 games model + independent ordering path

**Registered by `fable`, 2026-08-01, before any arm was fitted or any evaluative number
computed.** Mandate: `docs/fable-mandate-B1-2026-08-01.md` (build mandate; ADR-069 binds: steer by
absolute quality against realised outcomes, consensus is neither input nor development signal).
Config: `experiments/bottomup/ranking_versions/v2.json`. Runner: `experiments/bottomup/v2/`
(built after this registration).

## m_b = 12

### Arms (each differs from its comparator by exactly one thing)

| arm | definition |
|---|---|
| **G0** (control) | v1's availability exactly: OLS of games-share on arm-A features (`gshare_w, gshare_1, present_1, age, age2, evidence`), clip [0,1] × season_len. Everything else identical to G1's pipeline. |
| **GN** (baseline) | Naive persistence: `proj_games = games_1` (0 where no N−1 season). Component-level bar only; not a candidate. |
| **G1** (primary) | Binomial GLM (logit, ridged IRLS — existing `binom_glm`) of (games, season_len) on the frozen feature block in §3, fitted on veteran training rows per position, walk-forward. End-of-N−1 information only; no proxy reads (audit-asserted). |
| **G2** (secondary) | G1 + two week-1-of-N roster-status indicators from `panel.preseason_roster(N)` (`wk1_available`, `wk1_reserve`; reference = on no week-1 roster). Proxy-tagged reads; carries the documented as-of caveat (week-1 status ≈ late-August cutdown, not strictly pre-draft). |

### §3 — G1 feature block, frozen now

From the new week-shape loader (weekly box score of seasons ≤ N−1; ordinary feature reads):
`late4_share_1` (share of the final 4 scheduled weeks of N−1 played), `endgap_share_1`
((season_len₁ − last_week_played₁)/season_len₁; 1.0 if absent all of N−1), `played_thru_1`
(last_week_played₁ ≥ season_len₁ − 1). From existing features: `gshare_w`, `gshare_max3`,
`present_1`, `evidence`, `age`, `age2`, `chronic_missed_share` (mean of (1 − gshare_k) over lags
1–3 where present). Interactions (the repair itself): `miss1_x_endgap` = missed_share_1 ×
endgap_share_1, `miss1_x_resolved` = missed_share_1 × late4_share_1. Features standardised on
training rows. No injury-report columns (measured coverage 2.5–4.8% on long absences); no
depth-chart columns (arms D/E are post-hoc per `pos_features.py` and stay out).

### Graded cells (all: paired season-block bootstrap, 4,000 reps, seed 20260801, 95% CI;
### WIN = CI > 0, HARM = CI < 0, else NULL; BH at the campaign denominator per README)

| # | contrast | endpoint | population |
|---|---|---|---|
| 1–4 | **C-A**: G1 − GN | Spearman(proj_games, realised games), per season, per position | M-panel veterans (FFC-ADP-covered rows; ADP defines membership only, never a feature or ordering input), targets 2018–2024 |
| 5–8 | **C-B**: G1 − G0 | Spearman(v2 points order, realised points), per season, per position — the ADR-069 steering metric | same |
| 9–12 | **C-C**: G2 − G1 | same as C-B | same |

## Decision rules, fixed now

- **C-A is the mandate's bar** ("a projected-games component that beats naive persistence on
  ordering skill — the bar v1 failed"): claimed per cell only where the CI clears 0.
- **G1 is adopted into v2 iff C-B has ≥ 2 WIN and 0 HARM** (same shape as M2 Amendment 1's rule).
  If C-B fails but C-A passes, the honest report is "component improved, ranking unchanged";
  v2 still ships its architecture (stat lines + independent ordering) with G0 games, and the games
  deficit stays an open, named defect. This branch is registered now so the outcome cannot be
  renarrated.
- **G2 is adopted over G1 iff C-C has ≥ 2 WIN and 0 HARM AND `strategist` rules the week-1 as-of
  alignment acceptable** (M2-1-REC's caveat; outside fable's authority). Otherwise G2 is reported,
  not adopted.
- MAE vs GN, the returning-absent class diagnostics (`pos_eval.availability_metrics`), the full
  universe, rookie rows, and the portability demonstration are **descriptive — 0 tests
  contributed** and may not be quoted as corrected.

## Registered predictions (so the result can surprise)

C-A: G1 wins at all four positions (naive persistence is tie-heavy on board veterans). C-B: wins
concentrate at QB/RB; WR/TE smaller or NULL; per-player gains concentrate in the
missed-≥4-weeks-in-N−1 class everywhere. C-C: small positive or NULL at all four; any G2 gain
concentrates where end-of-N−1 was ambiguous (long endgap). Downside registered: if G1 *harms*
C-B anywhere, the likeliest mechanism is variance added to healthy-veteran games projections —
report it as such, do not re-tune post hoc.

## Amendment 1, 2026-08-01 — registered after a two-position smoke of G1, before any amended arm ran

**What had been seen when this was written (the peek, recorded verbatim):** G0/G1 cells for TE
2018–2019 (n≈10/season) and RB 2018–2019 only. TE: G1 ρ_games 0.073 vs naive 0.477 (HARM on 2
seasons). RB: G1 0.287 vs naive 0.277 (NULL), C-B −0.013 (NULL). Both arms project board veterans
at median ~12 games against a realised median of 15 (level bias ≈ −2.6, spread compressed).
Nothing else was computed; 2020–2024 unseen everywhere; QB/WR unseen entirely.

**Mechanism, stated before the fix is run:** the §3 block cannot express "resolved absence still
carries moderate risk." For a healthy veteran every timing feature collapses to the same point
(miss1 = 0 kills both interactions), so within-healthy ordering is age noise; and a resolved-miss
veteran's risk enters *only* through `miss1_x_resolved`, so if that coefficient is small his
persistence information is discarded entirely — while naive `games_1` keeps it, which is exactly
how naive wins ordering. The block lacks the standalone lag-1 availability level.

**G1a (amended primary) = G1 + `gshare_1`. One added feature, nothing else changes.**
**G2a = G1a + the §4 week-1 indicators** (replaces G2-on-G1, which is withdrawn *never having
been run*; its 4 registered cells are re-pointed, not deleted).

**m_b: 12 → 20.** Cells 1–8 (C-A, C-B on G1) stand and will be run and reported at full span —
the registered-then-amended arm does not vanish. Cells 9–12 (C-C) become G2a − G1a. New cells
13–16 (**C-A′**: G1a − GN, games ordering ×4 positions) and 17–20 (**C-B′**: G1a − G0, absolute
quality ×4). Same bootstrap, same seed, same BH-at-campaign-M convention (M_campaign becomes 92
with this batch's 20).

**Amended predictions:** C-A′ wins at RB/WR/QB; TE likely unresolvable at n≈10/season. C-B′ wins
at QB/RB. C-A (unamended G1) expected NULL-to-HARM — recorded so that outcome is a *confirmation
of the stated mechanism*, not a surprise to be explained away. The board-veteran level bias
(−2.6 games) is a named descriptive defect; its candidate fix (fit-population weighting) is NOT
stacked into G1a and would be its own registered arm if pursued.

## Outcomes, recorded 2026-08-01 after the full run (code at `7cf5bb8` + BH-column rename; no grade changes to any other batch)

Full span 2018–2024, all four positions, arms G0/G1/G1a/G2a; audits clean (zero proxy reads on
G0/G1/G1a; 2025 never read; exit asserts all passed). Artifacts:
`experiments/bottomup/results/ranking_v2_{G0,G1,G1a,G2a}_{players,cells}.csv`,
`ranking_v2_contrasts.csv`.

**C-A (G1 − naive, games ordering):** RB WIN (+0.063, CI-level, not BH), QB/WR/TE NULL — the
amended prediction ("NULL-to-HARM") was mildly beaten. **C-B (G1 − G0, absolute quality): 0 WIN,
1 HARM — WR −0.0134 (p=0.0002, BH-robust). G1 rejected by its rule**, confirming Amendment 1's
mechanism. **C-A′ (G1a − naive):** RB WIN (+0.084, p=0.0002, BH-robust); QB/WR/TE NULL (TE
unresolvable as pre-declared, CI half-width ≈ 0.29). **C-B′ (G1a − G0): 0 WIN, 1 HARM (WR
−0.0125, p=0.0005, BH-robust) — G1a REJECTED by the registered adoption rule.** The registered
downside mechanism (variance added to healthy-veteran projections) is the standing explanation;
no post-hoc re-tune performed. **C-C (G2a − G1a): 3 WIN, 0 HARM** — QB +0.019 (CI-level),
RB +0.072 (BH-robust), WR +0.048 (BH-robust), TE NULL. **G2a passes its numeric rule; its
adoption remains conditional on the strategist as-of ruling exactly as registered.**

Descriptive (uncorrected, stated as such): only G2a beats naive persistence on games MAE
(RB 3.06 vs 3.64, WR 2.67 vs 3.07, TE 2.67 vs 2.95; QB 3.46 vs naive 3.10 — naive still ahead);
absolute games-ordering skill remains modest everywhere (best arm ≤ 0.27 mean ρ — most of the
oracle gap is irreducible from September information); the returning-absent class bias flips
−1.02 → +0.97 under G2a (single qualifying cell, ~9 players — thin); the board-veteran level bias
(~−2.6 games) persists in G0/G1/G1a and shrinks under G2a. The G2a magnitudes are exactly the
size that warrants an as-of challenge before belief: the mechanism is transparent (wk-1 IR/PUP/SUS
mechanically implies missed games) and the direction of the residual skew is known (a few days
optimistic vs a real late-August draft; cutdown-day placements are known by a Labor-Day draft).
Portability demo (descriptive): after fixing a NaN-propagation defect whose signature was a
false "0 rank changes" (all-NaN points ordered by the player_id tie-break — recorded because a
plausible-looking PASS table was one careless read away from the write-up), the same G0 stat
lines under half-PPR / full-PPR / standard-6pt reorder 15/23 top-24 RBs (max move 5–8 slots) with
zero fitting calls.

## Scope notes

v2's ordering path reads no consensus/ADP/ECR column anywhere (ADR-069; the replaced v1 assembly
started from the crowd's order and pinned rookies to it). Rookie rows use the existing rookie
sub-model (draft capital + age; April-of-N information); rookies are excluded from every graded
cell and reported descriptively. Holdout 2025 never read; feature/outcome access via
`SeasonPanel` gates and the WalkForward audit assertions, not hand-rolled cutoffs. The G2 proxy
read uses the panel's `proxy` audit tag; G0/G1 runs assert zero proxy reads.
