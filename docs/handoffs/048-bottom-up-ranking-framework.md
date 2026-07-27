---
ID: 048
FROM: pm
TO: strategist
STATUS: RESOLVED
OPENED: 2026-07-27
BLOCKS: bottom-up ranking build
---

## Ask

Specify the bottom-up projection framework. This is the methodology half of thread 046; that thread
gets the data, this one decides what to do with it. Founder wants the best ranking obtainable and as
much variance explained as honestly possible.

## The structural insight the framework should be built around

**Opportunity is predictable. Efficiency mostly is not.**

Year-over-year, usage measures — target share, carry share, route participation, snap share — are
fairly stable. Efficiency measures, and touchdown rate above all, are close to noise. This is why
professional projections work the way they do: **project volume carefully, then apply a
regressed-to-mean efficiency**, rather than projecting points directly.

The project has already discovered its own version of this. The spike-week persistence test ran on 26
seasons and returned **null** — whether a player clears yardage bonuses more often than his volume
predicts does not carry between seasons. The existing guidance in `assistant-context.md` says it
outright: *"project the yards; the bonuses follow automatically."*

So the framework should be explicitly two-stage, and the second stage should be deliberately humble.
A model that predicts touchdown rate confidently is not a better model; it is a model that has learned
noise.

## Be honest about the ceiling

The current rank-to-points curve explains **16–27% of variance** (R² 0.158–0.266). That is the bar.

But "explain as much variance as possible" has a real limit that is not a modelling failure. Injuries,
game script, coaching changes and touchdown variance are substantially irreducible at season level.
Published professional projections do not clear roughly 30–40% either. **A model reporting R² far above
that range on this data is almost certainly leaking or overfitting, and should be treated as a bug
report rather than a result.**

Specify the number you would consider suspicious *before* running anything, and what you would check
first if you saw it.

## Overfitting is the live risk, not sample size

Twenty-six seasons and a wide feature set is exactly the shape where a model fits beautifully and
predicts nothing. Specify:

- The cross-validation scheme, and why. Leave-one-season-out is the obvious candidate given the
  resampling-unit argument that has governed everything else here.
- How feature selection avoids peeking. Selecting features on the full dataset then cross-validating
  is the classic leak.
- The holdout. 2025 is sealed; say whether this framework needs its own additional holdout.
- A **baseline that must be beaten**: the existing rank-to-points curve. A bottom-up model that does
  not beat 16–27% out-of-sample is not worth shipping, and that comparison should be pre-registered.

## Regime — the founder's "zoom in and out"

The founder asked whether we can detect regime change year to year by varying the window. Yes, and it
is the right instinct. Specify:

- **Rolling-window fits.** Fit on windows of varying length ending in the present, and observe where
  coefficients move. Coefficient instability across windows *is* the regime signal.
- **Changepoint detection** on the key rates — pass rate, pace, target concentration — to find breaks
  empirically instead of assuming decades are comparable.
- How `src/regimes.py` already handles this and whether it should be extended rather than duplicated.

**On recency weighting — treat it as a hypothesis, not a given.** The founder notes we may already
weight late prior season more heavily. Late-season fantasy data has known contamination: eliminated
teams rest starters, playoff teams manage snaps, and weather skews passing. Whether late-season
weighting genuinely predicts better is **testable on 26 seasons** and should be tested rather than
assumed. Pre-register the comparison and the decision rule.

## Scope note

Two claims, kept apart. **Accuracy** — is the projection good? — is answerable now, on 26 seasons of
outcomes. **Beating consensus** — is it better than the market? — needs consensus history and remains
capped at n=4. Design the framework to establish the first and to leave the second cleanly testable
later. Do not let a good accuracy result get described as an edge over the market.

## Done looks like

An ADR draft: two-stage structure, feature set with the reasoning, CV scheme, leak controls,
pre-registered baseline comparison, the suspicious-R² threshold, the regime method, and the recency
weighting test with its decision rule. Then `backend` reviews for feasibility. Build after that.

---
### strategist · 2026-07-27

**Artifact:** `docs/adr-drafts/ADR-E-bottom-up-projection-framework.md` (next unused letter after
ADR-D). Status `Proposed`, awaiting `backend` feasibility review. Nothing was run — I have no DB
access by design, and §"Measurements needed from backend" lists the five numbers I need handed back.

**What it specifies,** against your list:

| Ask | Where | Short form |
|---|---|---|
| Two-stage structure | §1 | S1 volume (fitted, feature-rich) → S2 efficiency (**shrinkage only**, capped) → S3 scoring engine (arithmetic). No per-player TD-rate model at all; TD enters via goal-line/red-zone *opportunity share*, which is a volume measure. Bonus expectation integrates a position × volume-tier per-game distribution — the direct operational form of PR-002's null. |
| Suspicious-R² threshold | §8 | Per-quantity, not global. End-to-end season points: audit at **>0.40**, presumed bug at **>0.50**. S2 TD/opportunity: audit at **>0.08**. S1 volume: audit only at **>0.80** — high R² on usage is expected, and a single global threshold would discard our own signal. Seven-step audit order given; the first three catch nearly everything. |
| CV scheme | §3.1 | Leave-one-season-out **with a one-season embargo either side**. Season is the resampling unit because it is a block of shared conditions (one rule set, one pass-rate environment, largely one player set). The embargo closes a real channel: features for season N are built from N−1 outcomes, which are N−1's *targets*. Diagnostic: if un-embargoed exceeds embargoed by >0.03 R², that gap is itself a leakage signal. |
| Leak controls on selection | §3.2 | Everything estimated is estimated inside the fold, with the list **enumerated** (shrinkage constants, standardisation means, winsorisation, imputation, transform choice, volume-tier boundaries, window length, **and regime break locations**). Selection frequency across folds is a diagnostic, never a selector. Per-fold cutoff assertion, and an identity-alias check so one player-season can't appear in train and test under two ids. |
| Holdout | §3.3 | **2025 stays sealed, untouched during development.** No *additional retrospective* holdout — it would cost the scarcest thing here (modern seasons) to fix a problem better handled by a **capped, logged 20-configuration budget** on LOSO. Yes to one extra holdout that costs zero training data: **register the 2026 projections before Week 1 and score them after.** A prospective registration cannot leak. That has a September calendar dependency. |
| Pre-registered baseline | §7 | **Correction you will want to check me on:** 0.158–0.266 is an *in-sample* fit of a 2-parameter curve over 5 seasons, one sealed. Comparing our embargoed-LOSO R² to it is not a comparison. The baseline must be **refit under the identical protocol on the common window**. Decision-grade baselines are prior-season-points and the positional-mean heuristic (full window); the consensus-rank curve is **descriptive only, n=4, no p-value**. |
| Regime method | §5 | **Extend `src/regimes.py`, do not duplicate.** The changepoint half is already built — sup-Wald/Quandt-Andrews with binary segmentation, and `pass_rate`, `neutral_pass_rate`, `plays_per_game`, `rb_carry_top30_share`, `wr_target_top45_share` are already in `METRICS`. Add `rolling_coefficient_path(...)` for the founder's zoom, and re-run break detection **fold-locally** on the truncated series (using breaks found over all 27 seasons to set a test fold's window is a look-ahead leak; `detect_breaks` already takes arbitrary sequences, so it is a call-site discipline, not new code). Decision rule: coefficient instability is a hypothesis generator; only embargoed-LOSO performance under within-fold window selection is decision-grade. |
| Recency as hypothesis | §6 | Two questions separated (season-level vs within-season). 9 arms, **not** fully crossed, m=36 declared before the run; full crossing is exploratory and never enters the FDR denominator. Adopt a non-default arm only at ≥70% of folds *and* a season-level bootstrap CI on ΔR² excluding 0 after BH. Contamination-excluded arms (drop Wk 17–18) are in the grid specifically so that if they beat the recency arms, we report "removing contaminated weeks helped," not "recency helped." |
| Accuracy vs beating consensus | §7.3 | Permitted and forbidden sentences written out verbatim. The subtle trap is named: beating the ADR-016 curve out-of-sample *is* an accuracy comparison against a consensus-derived projection and *is not* a draft-day edge — close enough that a hurried summary will collapse them. If an artifact can't hold the distinction, it omits the consensus comparison rather than hedging it. |

**Three things in the ADR you did not ask for and should sanity-check:**

1. **"26 seasons" is only true of the box-score feature tier.** Snap counts, air yards and route data
   start later, and targets/air yards are unreliable 2003–2008. A model's eligible fold set is the
   *intersection* of its features' availability windows (§4.3) — a snap-share model gets ~13 folds, not
   26. Reporting it as 26-season-validated would be a false statement about power. No imputation across
   an availability boundary; that boundary is a regime boundary, not missing-at-random.
2. **`season_points = games_played × points_per_game_played` must be decomposed** (§2). A model can
   post a healthy season-points R² purely by predicting that last year's 17-game players play 17 again.
   Pre-committed: if ΔR² on season points isn't matched in sign by ΔR² on points-per-game-played, it is
   a games-played artefact and gets reported as one.
3. **Per-position adoption** (§9). If RB and WR clear the bar and QB and TE don't, the honest board is
   mixed-source with the source named per row. That needs a product call — filed as **D-023** in
   `docs/decisions-needed.md`.

**Refused, in writing:** a per-player efficiency-residual feature (PR-002 tested the nearest version on
26 seasons and it was null — reinstating it needs a new pre-registration, not a hunch); any latent
"coaching intent" or "team philosophy" variable (coach *continuity* is observable, coach *intent* is not
identifiable at this n — same standard as refusing to infer an opponent's draft strategy from their
opening picks); and extrapolating depth-chart role to 2026 from a source that ends in 2024 (that is
inventing data, and a model requiring it cannot be the shipping model).

**Registered as an acceptable outcome, in advance:** no position clears the bar, and the finding is
*"a bottom-up projection from usage features is not measurably more accurate out-of-sample than the
existing rank-derived curve."* That is a real result about this data's ceiling, and pre-committing to it
now is what stops it being reframed later as a failed sprint.

Marking RESOLVED — the methodology ask is fully specified. `backend`'s feasibility review is the next
step and does not need this thread reopened; the five measurements are itemised in the ADR.
