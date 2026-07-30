# ADP vs. Production: where is consensus ADP structurally wrong?

**Session:** backend, 2026-07-30. **Founder request (verbatim):** "so now we can also look at ADP
vs Production and try to establish patterns." **Dispatch's own framing, honored throughout:** not
"which players busted" (hindsight) — the deliverable is structural mispricings identifiable
*before* the draft.

**Script:** `analysis/adp_vs_production.py` (reproducible, no network calls, ~15s runtime against
a populated `data/nfl.db`). **Raw output:** `data/qa/adp-vs-production-2026-07-30.json`.

**This is a Sonnet/default-tier session, not a dispatched Opus/high-effort one.** Per
`docs/operating-model.md`, statistical-methodology work like this should arrive dispatched to
Opus at high effort; this dispatch did not specify that. Flagging this explicitly rather than
stopping to ask, per this session's own operating rules — the analysis below applied every
guardrail in `docs/statistical-guardrails.md` I could identify, but a second, Opus-tier read is
exactly the kind of check that document says Statistician + Red-team should still run before this
is trusted for a real model change (see the `strategist` handoff opened at the end).

---

## 0. Data source and its limits — read this before trusting any number below

The only ADP history in this database with a genuine pre-draft `as_of_date` is
`ffc_adp_snapshots` where `adp_source='ffc_half_ppr_12team'` — FanFootballCalculator mock-draft
ADP, 12-team, half-PPR, seasons 2018–2024 (`tools/backfill_ffc_adp_history.py`, thread 055). Two
structural limits this analysis cannot remove:

1. **12-team mock ADP, not this league's 10-team real-money ADP.** No verified 10-team historical
   ADP source exists in this project (only a single current-day 2026 `mfl_proxy` snapshot). "Round"
   below is 12-team math, illustrative of *when in the draft*, not this league's literal round.
2. **Mock drafts, not real drafts.** FFC's sample is mock-draft activity — the best available
   proxy for "market consensus at that pre-draft moment," not a guarantee of identity with it.

**A real finding, not a stale doc claim:** this worktree's own `data/nfl.db` did **not** have the
thread-055 backfill rows on session start, even though `docs/CURRENT-STATE.md` says the backfill
"landed" — `nfl.db` is gitignored and worktrees do not inherit it (`docs/environment.md` §4), and
that session's populated DB copy never reached this worktree's `data/`. Loaded directly from the
already-committed CSVs (`data/adp-snapshots-ffc/*_12team_period*.csv`, 2,467 rows, all 19
season-formats) into this worktree's copy of `nfl.db` before running anything — no re-fetch, no
network call, so §5's "verify a source swap actually delivers the properties you're relying on"
concern doesn't apply here (same rows, same `as_of_date`s, just re-loaded from the committed export
rather than the DB file).

**2025 is the project's locked holdout and is untouched by construction, not discipline** — the
backfill covers 2018–2024 only, so 2025 never enters this dataset. Of the seasons that *do* exist,
**2024 is held out as an internal holdout**: explored/tuned on 2018–2023 only, touched once at the
end (§5 below), reported even where it weakens a pattern.

---

## 1. Method

### 1.1 Universe / survivorship
For season *N*, the population is exactly the players in that season's FFC ADP snapshot — decided
before the season, no outcome information used. A bust who scored near-zero points stays in with
`actual_points = 0`; nothing is dropped for lacking a stats row (CLAUDE.md §6.2 — a bust falling
out of the data would be the single worst thing this analysis could do).

### 1.2 Residual definition — value over replacement, not raw points, and two false starts kept visible

Two design mistakes were made and caught before being reported, both left documented in the
script's own module docstring because they are exactly the failure mode this task exists to guard
against:

- **False start 1 — per-position value curve.** Building one points curve *per position* makes
  every position's mean residual trivially ≈0.00 by construction (a within-position curve is a
  permutation of that position's own players). Would have made "is one position priced worse than
  others" untestable by design, not merely non-significant.
- **False start 2 — overall raw-points curve.** Fixes the tautology, but produces "QB is
  underpriced by +146 pts/season," which is not a market inefficiency — it is this league's own
  1-QB roster rule. Comparing raw points across positions with no roster constraint manufactures a
  finding out of known roster mechanics.

**What's actually used:** value over replacement (VBD), via this project's own
`scoring.compute_vbd` / `ReplacementLevels` (ADR-029's measured RB30/WR40/TE10 flex-adjusted
baselines at this league's real 10-team, 1-QB shape) — the same machinery `backtest.py` already
uses to evaluate rankings. Replacement level is computed from the *full* season player universe
(every player with any weekly stats row, not just the ADP-listed subset), so the floor itself isn't
distorted by ADP's own survivorship cut. Then, per season:

1. Sort the ADP universe (all four positions together) by real ADP overall rank ascending.
2. Sort the same universe by realized VBD descending — the season's own realized value curve.
3. `expected_vbd(player) = value_curve[ordinal position of player's ADP rank]`.
4. `residual = actual_vbd − expected_vbd`.

**A third bug, also caught and fixed, not published wrong:** FFC's own `rank` column includes
kickers, which this analysis drops. That leaves gaps in `rank` within the filtered universe (season
2022: 114 raw rows, 2 PK, ranks run to 123). Indexing the value curve by `rank − 1` is therefore
*not* a valid index into a 112-element curve — every rank past the filtered length silently
clamped onto the same tail slot, which breaks "residual sums to ~0 within a season," the internal
consistency check this design is supposed to satisfy by construction. Caught by adding that check:
season 2022 alone summed to +1,465.76 points of residual before the fix, purely a bookkeeping
artifact. Fixed by indexing on each player's *ordinal* position after sorting the filtered
universe, not the raw `rank` value. Verified: every season now sums to residual ≈0 (float
rounding only).

### 1.3 Multiple comparisons
Six pre-registered families, in the dispatch's own order: position, ADP round bucket, age × 
position group, prior-season games missed, team change, prior-season volume-vs-efficiency split.
One p-value per family (a season-clustered permutation test — shuffle the group label *within*
each season, preserving that season's own residual distribution and group sizes). Benjamini–
Hochberg FDR correction applied across those six p-values, not per-bucket. Effect sizes (mean
residual VBD points) are reported with season-clustered bootstrap 95% CIs regardless of
significance (guardrails §7).

### 1.4 Non-stationarity
Every family is also reported per-era: 2018–2020 (16-game seasons) vs. 2021–2023 (17-game
seasons, train only — 2024 held out). The 2021 season-length expansion is a real discontinuity,
not a convenience split.

### 1.5 A caveat that matters more than any single p-value
**Rank-ordered residuals against a skewed value curve regress toward the mean even for a perfectly
calibrated market.** The top of any ADP board claims the highest slots on the realized value curve;
if the true predictor has *any* noise (it always does), the players who land there will, on
average, realize less than the very top of that curve, and the reverse at the bottom. This alone
predicts "early rounds negative residual, late rounds positive residual" with zero market skill or
bias required — it is closer to a statistical fact about ranking under uncertainty than a finding
about ADP. The round-bucket result below (§2) is reported for completeness and because it is the
scaffolding the position-conditional-on-round result (§2, position × round) depends on, but **it
is not, by itself, evidence of an exploitable market inefficiency.** What *would* be actionable is
a pre-draft-observable attribute that predicts *which* players deviate from the curve — that is
what families 3–6 test, and it's the position × round cross-tab (not pre-registered, added as a
diagnostic — see §2) that turned out to matter most.

---

## 2. Results, ranked by how much confidence they deserve

### Tier 1 — survived era-split and (partially) the holdout: RB is overpriced early, WR/TE underpriced

| Family | Train mean residual (VBD pts) | 95% CI | p (BH-adj) | Era 2018-20 | Era 2021-23 | 2024 holdout |
|---|---|---|---|---|---|---|
| Position: RB | **−20.2** | [−26.5, −15.6] | 0.001 | −25.8 | −15.5 | **+1.6** (flips) |
| Position: WR | **+15.6** | [+10.2, +20.9] | 0.001 | +13.7 | +17.2 | +0.8 (flat, doesn't hold) |
| Position: TE | **+23.1** | [+11.2, +33.6] | 0.001 | +25.1 | +21.5 | **+17.7** (holds) |
| Position: QB | −8.7 | [−21.9, +8.9] | 0.001* | **+8.0** | **−24.5** | −18.9 | 

*QB's family p-value is the omnibus test across all four positions, driven by RB/WR/TE, not QB
individually — QB's own CI crosses zero and its sign **flips between eras**, the opposite of a
robust finding. Treat QB as "no stable position-level effect found," not "underpriced" or
"overpriced."

**Diagnostic, not pre-registered (added because §1.5's caveat demanded it): position residual
conditional on round bucket**, train seasons only (2018–2023):

| Position | Rounds 1–3 | Rounds 4–8 | Round 9+ |
|---|---|---|---|
| QB | −15.9 (n=12) | −22.5 (n=55) | +7.0 (n=54) |
| **RB** | **−54.1 (n=104)** | −27.3 (n=110) | +27.6 (n=90) |
| WR | −18.3 (n=85) | +5.3 (n=136) | +54.8 (n=109) |
| TE | −18.9 (n=15) | −9.3 (n=35) | +68.3 (n=39) |

This is the finding that survives §1.5's regression-to-the-mean objection: **within the same round
bucket** (so the "early picks regress toward a skewed curve" mechanism is held roughly constant),
early-round RBs still underperform by roughly 3× the margin of any other position in the same
bucket (−54.1 vs. −15.9 to −18.9). That is not explainable by curve convexity alone — it is
specific to RB. This matches the widely-discussed "RB dead zone" pattern in fantasy commentary
(shorter careers, higher injury attrition, touch-share more exposed to a single coordinator's
scheme change) — **CLAUDE.md §11's instruction to treat "everyone knows X" as a hypothesis to
test, not received wisdom, is exactly why this is reported as a measured, era-stable, partially-
holdout-surviving pattern and not asserted from priors.**

**Honesty check the guardrails require:** the position-level (not round-conditional) RB and WR
results did **not** clearly replicate in the 2024 holdout — RB flipped from −20.2 to +1.6, WR
flattened from +15.6 to +0.8. Only TE held (+23.1 train → +17.7 holdout) and the round-bucket
pattern held directionally (round 1–3 stayed negative, round 9+ stayed strongly positive). **A
single holdout season has no meaningful confidence interval (n=1) — this is not strong
disconfirmation, but it is real disconfirmation of the raw position-level framing, and it is
reported because the guardrails require reporting a result that weakens a pattern, not just ones
that confirm it.** The round-conditional RB result is the one worth carrying forward; the
unconditional position-level framing is not.

**Confidence label: MODERATE for "early-round RB is overpriced relative to same-round peers,"
LOW for "RB/WR/TE are unconditionally mispriced by position."**

### Tier 2 — age × position, robust direction but noisy magnitude

| Bucket | Train mean | 95% CI | Era 2018-20 | Era 2021-23 |
|---|---|---|---|---|
| PASS_CATCH (WR/TE) ≤23 | **+34.6** | [+26.1, +43.8] | +39.4 | +30.6 |
| PASS_CATCH 24-27 | +12.6 | [+5.5, +19.5] | +9.5 | +16.2 |
| PASS_CATCH 28+ | +5.9 | [−2.1, +14.0] | +0.1 | +9.0 |
| RB 24-27 | **−27.2** | [−37.4, −18.8] | −35.2 | −22.0 |
| RB ≤23 | −13.7 | [−27.9, −1.3] | −16.8 | −9.1 |
| RB 28+ | −10.8 | [−27.9, +9.3] | −30.2 (n=10) | −3.6 (n=27) |
| QB (all bands) | noisy, small n, sign flips between eras | — | — | — |

Family p (BH-adj) = 0.001. Young pass-catchers (≤23) are the single strongest, most stable cell in
the whole analysis: positive in both eras, tight CI relative to its size, and directionally the
same mechanism that shows up in the round-9+ WR/TE surplus above (the market is systematically
slow to price a first- or second-year breakout). **Confidence label: MODERATE-HIGH** for "young
WR/TE outperform their ADP slot," **LOW** for QB age effects (n too small, sign unstable) and for
RB 28+ (n=37 train, CI crosses zero in one era).

### Tier 3 — no reliable pattern found (report plainly, per the dispatch's own instruction)

| Family | Train mean (extremes) | p (BH-adj) | Verdict |
|---|---|---|---|
| Prior-season games missed | 0 games: −7.3 · 4+ games: −1.2 | 0.48 | **Not significant. Sign order is not even monotonic**, and both extreme buckets flip sign between eras (era A: 0-games +1.1 / 4+-games +1.5; era B: 0-games −16.8 / 4+-games −3.0). No evidence the market over- or under-discounts games missed, in either direction. |
| Team change | same-team +12.0 / changed-team +30.6 (unadjusted values; era-split flips sign) | 0.73 | **Not significant.** Also see the coach-identity caveat below — this measures team change only, a narrower proxy than what was asked for. |
| Prior volume-vs-efficiency split | "high-volume/high-efficiency" −7.0, others noisy/small-n | 0.48 | **Not significant** as a 5-way split; the one directionally consistent cell across eras (high-vol/high-eff, players who were already both are drafted correctly and mildly *overpriced* by a small, stable margin) is the least interesting one. Small-n buckets (n=8-12) are too noisy to trust at all. |

These three are genuine, useful negative results, not analysis failures — per the guardrails
(`docs/statistical-guardrails.md` §5), a "the market is well-calibrated here" finding is reported,
not buried.

---

## 3. A gap this analysis could not close: coordinator identity

The dispatch specifically named "team change / new coordinator (`coach_id` is a first-class
dimension in this schema for exactly this reason)" as a candidate factor. **This database's
`play_callers` table (built by `src/ingest_play_callers.py`) has zero rows in this worktree's
`nfl.db`** — the ingestion code exists but has never been run against this environment's copy.
Family 5 above (`team_change`) is therefore a narrower proxy — literal team roster change only,
not coordinator/scheme change — and its null result should not be read as "coordinator change
doesn't matter." It's untested. Flagging this rather than substituting the weaker proxy silently,
per the standing rule on source swaps not being drop-in equivalents (CLAUDE.md preamble). Logged
in `docs/ideas-inbox.md` as follow-on work, not attempted here (out of this session's time budget
and not this dispatch's ask).

---

## 4. What this does and doesn't license

- **Does not, by itself, justify a ranking-model change.** No ADR was opened. The RB-early-round
  and young-WR/TE patterns are real, era-stable, partially-holdout-surviving measurements against
  a 12-team mock-ADP proxy — not yet validated against this league's own real 10-team market, and
  not yet run through a draft-simulation-based evaluation (guardrails §6's stated direction, not
  yet built). Handoff to `strategist` opened for exactly this next step (below).
- **Does license:** treating "buy WR/TE, especially young ones, later than the position group's
  raw ADP suggests, and be more skeptical of an early-round RB than the round alone implies" as a
  pre-registered hypothesis for the ranker's next factor-testing pass — with an explicit note that
  the *unconditional* position-level framing (as opposed to the round-conditional one) did not
  survive the 2024 holdout and should not be the form the hypothesis takes forward.

---

## 5. Reproducing this

```
python3 analysis/adp_vs_production.py
```

Requires a populated `data/nfl.db` including the `ffc_adp_snapshots` historical backfill rows
(`adp_source='ffc_half_ppr_12team'`, periods 2018-2024). If a fresh worktree's DB lacks those rows
(see §0), load them from the committed CSVs:

```python
import sqlite3, csv, glob
con = sqlite3.connect('data/nfl.db')
cur = con.cursor()
cols = [r[1] for r in cur.execute('PRAGMA table_info(ffc_adp_snapshots)').fetchall()]
for path in sorted(glob.glob('data/adp-snapshots-ffc/*period*.csv')):
    with open(path, newline='') as f:
        rows = list(csv.DictReader(f))
    src, period = rows[0]['adp_source'], rows[0]['period']
    if cur.execute('select count(*) from ffc_adp_snapshots where adp_source=? and period=?',
                    (src, period)).fetchone()[0]:
        continue
    placeholders = ','.join(['?'] * len(cols))
    for r in rows:
        cur.execute(f'INSERT INTO ffc_adp_snapshots ({",".join(cols)}) VALUES ({placeholders})',
                    [r.get(c) for c in cols])
con.commit()
```

Output: console summary + `data/qa/adp-vs-production-2026-07-30.json` (full per-family, per-era,
per-holdout tables).
