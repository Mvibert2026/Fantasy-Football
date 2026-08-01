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

## Scope notes

v2's ordering path reads no consensus/ADP/ECR column anywhere (ADR-069; the replaced v1 assembly
started from the crowd's order and pinned rookies to it). Rookie rows use the existing rookie
sub-model (draft capital + age; April-of-N information); rookies are excluded from every graded
cell and reported descriptively. Holdout 2025 never read; feature/outcome access via
`SeasonPanel` gates and the WalkForward audit assertions, not hand-rolled cutoffs. The G2 proxy
read uses the panel's `proxy` audit tag; G0/G1 runs assert zero proxy reads.
