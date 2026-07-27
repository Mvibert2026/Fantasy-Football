---
ID: 048
FROM: pm
TO: strategist
STATUS: OPEN
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
