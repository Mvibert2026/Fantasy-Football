# Bottom-up ranking — research pass 1

**Ranker, 2026-07-29.** Exploratory. Nothing here is confirmatory, nothing here is registered,
and no result in this document may be reported as an edge. Every number is a **hypothesis**.

**Look-ahead posture, stated once and true of every figure below:** season **2025 was never
read**, for features or for evaluation — not once, by any script in this pass. All model-style
predictors use only seasons strictly before the target. Statistics that deliberately read
target-season data exist only as **oracles** (upper bounds) or as **measurements of noise**, and
every one of those is named as such at the point of use. The player universe for target season N
is frozen from season N−1 before N is opened, so busts and zero-game seasons are counted as the
outcomes they were.

Code: `/tmp` scratchpad this session (not committed — regenerable from the recipes in §8).
Data: `data/nfl.db`, `player_weekly_stats` 1999-2024, scored through `src/scoring.py`'s real
league config (stacking bonuses included).

---

## 1. Conclusion first

**The edge is not in projection accuracy, and it is not in any of the situation channels. It is
in what the project already half-owns and has never measured properly: the structure of
positional value, and the fact that the shipped board measures that structure through a
corrupted lens.**

Three things, ranked by expected value.

**(1) The board's rank curve confounds two different quantities, and the fix currently on record
would make it worse.** `make_board.fit_rank_curves` regresses points on log *consensus* rank. That
single fit is the product of the positional value spread and the market's ordering skill that
year. Fitted on **realised** finish rank instead — which needs no consensus data and therefore has
26 seasons instead of 5 — the QB value curve has not collapsed at all; it is at an era **high**
(era-mean slope −72.9 in 2021-2024 vs −57 to −59 over 1999-2020), while the consensus-fitted slope
fell. The two series move in opposite directions. The R² gap is the tell: 0.91-0.98 on realised
rank against 0.15-0.41 on consensus rank — that 0.16-0.27 figure on the board's own screen is not
a property of football, it is the noise in consensus rank. **Recency-weighting the consensus curve,
the fix recorded in `ideas-inbox.md:229`, would make the board chase market noise faster.** Opened
as thread **085** to `strategist`, because ruling on this is not mine.

**(2) Tight-end is where the unpriced signal is, and three independent lines point at it.**
The variance ledger (§3) says TE has **0.336** of season-ppg variance that is stable player quality
and *not* priced by consensus — more than double RB or WR (0.151 each) and five times QB (0.063).
Consensus at TE is the only position where it fails to beat last season's points per game
(r² 0.303 vs 0.407) and where its within-position ordering is weakest (τ_b +0.31 vs +0.48-0.50
elsewhere). And independently, the prior prototype's single CI-clear VBD win over naive persistence
was TE (+0.073 [+0.034, +0.118], `experiments/bottomup/REPORT.md`). The league shape makes it cheap
to act on: 1 TE plus 2 flex in a 10-team league, TE10 replacement, small VBD spread, so being wrong
costs little and being right produces a flex-worthy asset.

**(3) Two named data gaps can be closed by deciding not to buy them.** The entire team-environment
channel — of which coach and coordinator tendency is a strict subset — is bounded at **≤ +0.055 τ_b**
by a perfect-foresight oracle, and a team fixed-effect on prediction residuals finds **no excess
variance over random grouping at any position**. Sourcing coaching staff history and Vegas implied
team totals should not be funded on the current evidence. The one gap that does bind is the depth of
**expert consensus history** (n=4 usable seasons), opened as thread **084** to `data-ops`.

**The single most valuable next experiment**, and the one I would run first:

> **Decompose the rank curve.** Fit the positional value-spread curve on realised finish rank over
> the deep sample, fit the consensus-rank → finish-rank mapping separately on the four usable
> consensus seasons, and compare the resulting board against today's single-regression board.

It is the highest-value experiment because it is the only one that touches a **live defect in a
shipped artefact**, it needs no new data, it is few-parameter and transparent, and it is testable
on 26 seasons rather than 4. It must be registered by `strategist` before it runs (thread 085) — I
will not run it unregistered.

**The runner-up, and it is close:** a TE-specific arm using `snap_counts` (2013-2025, already in the
database, **never used by the prototype**) as a route-participation proxy. See §7.

---

## 2. Premise check

I was asked to challenge the premise before acting. It holds, with one correction.

| Claim in the brief | Repo | Verdict |
|---|---|---|
| Consensus explains 0.16-0.27 of the variance | `docs/data-contract.md:95`, `:379` | Confirmed as recorded. **But it is the R² of the consensus-rank curve, not a property of the game** — see §4.2. Reproduced here at 0.15-0.41 across 16 position-seasons. |
| QB slope ran −67, −73, −59, −45, −4 | `docs/ideas-inbox.md:229` | Confirmed as recorded; my 2021-2024 refit gives −66.6, −72.6, −58.6, −45.0. **The interpretation is contested** (§4.2). |
| Nobody has checked other positions | grep of `docs/` | Confirmed. Now checked: TE behaves like QB, RB and WR do not. |
| Ceiling/variance pricing "never once quantified" | grep of `docs/`, `experiments/` | Confirmed for the *board reordering* question. **PR-002 already ran and returned NULL** on the adjacent question (does spike-week-ness persist), which changes what is left to ask — see §4.1. |
| Consensus history 2021-2025, one sealed | `rankings` table | Confirmed. 2021-2024 usable, n=4. |
| Vacated opportunity / rookie capital / QB eliminated | `experiments/bottomup/REPORT.md` | Confirmed. Not revisited. |

One repo defect found and fixed in passing: `tools/handoffs.py:31`'s `ROLES` list did not contain
`ranker`, although `.claude/agents/ranker.md` exists — so this role could not open a correctly
attributed thread. One-line addition, made this session.

---

## 3. How much of a season is reducible at all?

This is the question that bounds everything else, so it gets answered with a number.

### 3.1 The ladder — what perfect foresight of one channel is worth

Kendall τ_b against actual season points, universe frozen from the prior season, folds 2010-2024
(n=15), season-level bootstrap 95% CI. `O_avail` knows *exactly how many games the player will
play* but nothing new about his rate. `O_rate` knows *exactly what his per-game rate will be* but
assumes average availability. Both are impossible; both are upper bounds on a channel.

| Pos | B1 prior pts | B2 prior ppg | **O_avail** (real games) | **O_rate** (real ppg) |
|---|---|---|---|---|
| QB | +0.266 [+0.19,+0.35] | +0.247 | **+0.623 [+0.54,+0.69]** | **+0.725 [+0.69,+0.76]** |
| RB | +0.298 [+0.25,+0.34] | +0.318 | **+0.637 [+0.59,+0.68]** | **+0.775 [+0.74,+0.80]** |
| WR | +0.354 [+0.31,+0.40] | +0.352 | **+0.629 [+0.59,+0.66]** | **+0.765 [+0.74,+0.79]** |
| TE | +0.243 [+0.17,+0.33] | +0.215 | **+0.600 [+0.54,+0.66]** | **+0.728 [+0.66,+0.79]** |

On the same universe restricted to the four consensus seasons, with every rung recomputed on the
identical player set (n=4, **descriptive only**):

| Pos | B1 | B2 | **ECR consensus** | O_avail | O_rate |
|---|---|---|---|---|---|
| QB | +0.356 | +0.372 | **+0.492 [+0.42,+0.56]** | +0.724 | +0.701 |
| RB | +0.246 | +0.334 | **+0.481 [+0.42,+0.53]** | +0.590 | +0.801 |
| WR | +0.431 | +0.392 | **+0.496 [+0.40,+0.59]** | +0.632 | +0.748 |
| TE | +0.231 | +0.312 | **+0.309 [+0.20,+0.49]** | +0.623 | +0.695 |

Consensus is roughly two-thirds of the way from naive persistence to a *single-channel omniscient*
predictor. That is a strong market.

### 3.2 The ledger — where the variance actually lives

Decompose observed season points-per-game as `μ_i + s_it + e_it`: a stable player level, a real
season-specific shift, and week-to-week noise.

- **`e` (week-to-week noise)** from within-season split-half (odd vs even weeks, ≥10 games,
  Spearman-Brown corrected), 2010-2024. This reads target-season data **by construction** — it is a
  measurement of noise, not a predictor.
- **`μ` (stable)** from `corr(ppg_{t−1}, ppg_{t+1})` — adjacent seasons, never the middle one, so
  anything season-specific to `t` cannot inflate it.
- **`s`** is the remainder.

Shares of observed season-ppg variance (players with ≥6 games), alongside what is currently priced:

| Pos | week noise `e` | season-specific `s` | stable `μ` | consensus r² | prior-ppg r² | **stable, not priced** |
|---|---|---|---|---|---|---|
| QB | 0.257 | 0.331 | 0.411 [0.26,0.54] | 0.348 [0.19,0.52] | 0.234 | **0.063** |
| RB | 0.095 | 0.305 | 0.600 [0.56,0.64] | 0.449 [0.35,0.55] | 0.355 | **0.151** |
| WR | 0.125 | 0.201 | 0.674 [0.65,0.70] | 0.523 [0.46,0.58] | 0.379 | **0.151** |
| TE | 0.126 | 0.235 | 0.638 [0.59,0.68] | 0.303 [0.09,0.56] | 0.321 | **0.336** |

And season points are `games × ppg`, so availability multiplies on top. Log-variance shares among
players who played: **games ≈ 29%, rate ≈ 48-52%, covariance ≈ 19-24%** (RB/WR). 4-5% of the frozen
universe plays **zero** games; 17-24% plays fewer than ten.

### 3.3 The answer

**Most of it is not reducible, but the irreducible part is mostly availability, not scoring noise —
and that is a different conclusion with a different consequence.**

For a wide receiver, of the variance in observed season ppg: **12.5% is week-to-week noise nobody
can ever predict; 20.1% is real season-specific change; 52.3% is already priced by consensus; and
about 15.1% is stable player quality that consensus does not price.** That last number is the
bottom-up target on the rate channel, and it is small. Multiply through by the rate channel's share
of season-points variance and the headroom on the decision-relevant object is roughly **8-9% of
season-points variance at WR** — real, but not the two-thirds the framing implies.

Availability is the larger unexplained block and it is **near-unforecastable**: prior-two-season
games predicts target-season games at r = **+0.09 to +0.18** (QB +0.178, WR +0.127, TE +0.098,
RB +0.094). Perfect games foresight would be worth +0.11 to +0.31 τ over consensus. Nobody gets it.

**The consequence for the founder is the one worth stating plainly: his edge is not going to come
from being a better forecaster of a player's rate. Consensus has taken most of that. It comes from
(a) valuing the outcome *distribution* correctly for this specific league, and (b) getting the
structural/positional layer right — which is exactly where §4.2 finds a live defect.**

Two caveats that cut against my own numbers, stated because they should be: the split-half estimate
of `μ` includes information that only becomes visible *during* a season (a Week-3 role change is
"stable" within that season), so the pre-season-knowable share is **smaller** than 0.674 and the
headroom smaller than 0.151. And "stable minus consensus r²" assumes consensus prices only `μ`; if
it also prices part of `s`, the leftover is smaller again. Both errors point the same way: **I am
over-stating the headroom, not under-stating it.**

---

## 4. The four channels

### 4.1 Ceiling and variance priced for this league — **small, and now quantified**

Asked: how many players does it move, and by how much? Answered on 2009-2024, draft-relevant depth,
scoring each player-season twice — once with the real stacking bonuses, once with them removed.

| Pos | bonus pts/season | share of pts | top-12 | bottom-12 | τ_b with vs without | mean abs rank move | max | % moving ≥2 | % ≥3 |
|---|---|---|---|---|---|---|---|---|---|
| QB | 8.0 | 2.8% | 10.1 | 5.5 | 0.932 | **0.60** | 4 | 9.7% | 3.1% |
| RB | 2.9 | 1.7% | 6.2 | 0.9 | 0.981 | **0.40** | 5 | 5.7% | 1.1% |
| WR | 3.2 | 1.9% | 7.6 | 0.9 | 0.979 | **0.57** | 5 | 10.9% | 3.0% |
| TE | 1.2 | 0.9% | 1.7 | 0.5 | 0.979 | **0.19** | 2 | 2.5% | 0.0% |

**The bonuses move the within-position order by about half a rank on average, and that is the
realised upper bound, not the ex-ante one.** Ex ante it is smaller still, and the reason is already
in the repo: 31-71% of a player's bonus points are explained by his season yardage alone, and
**PR-002 tested whether the leftover shape residual persists year over year and returned NULL**
(WR receiving-100 r=+0.041 [−0.018,+0.099]; RB rushing-100 r=+0.063 [−0.001,+0.124]; nothing
survived BH across 36 tests). The part of the bonus that reorders is the part that does not repeat.

Where the bonuses *do* act is **across** positions, not within them — and that has never been noted:

| Pos | top-3 VBD with bonuses | without | **Δ** |
|---|---|---|---|
| WR | 153.8 | 144.3 | **+9.4** |
| RB | 183.5 | 176.1 | **+7.4** |
| QB | 89.8 | 84.1 | **+5.7** |
| TE | 73.8 | 71.1 | **+2.7** |

A generic half-PPR board understates WR/RB elite value by ~7-9 points of VBD and TE by ~3. The
*differential* is ~6.8 points — 2-4% of the VBD magnitudes involved. **Real, directionally
consistent across sixteen seasons, and small.** It does not support the claim that this is the
project's structural edge; it does support carrying the bonuses in the scoring engine, which the
project already does.

### 4.2 Regime detection — **the QB story in the repo is probably the wrong story**

Full detail is in thread 085; the essentials:

`points ~ a + b·ln(rank)` fitted two ways, per position per season. Era means of the **realised
finish-rank** fit (1999-2024, no consensus needed):

| Pos | 1999-2007 | 2008-2015 | 2016-2020 | 2021-2024 | replacement pts, first → last era |
|---|---|---|---|---|---|
| QB | −57.7 | −59.0 | −56.8 | **−72.9** | 219 → 295 |
| RB | −87.7 | −67.5 | −72.9 | −68.5 | 127 → 147 |
| WR | −57.2 | −56.0 | −50.3 | **−60.0** | 129 → 139 |
| TE | −44.8 | −45.8 | −45.4 | −44.6 | 96 → 129 |

Side by side over the four overlapping seasons:

| Pos | consensus-fit slope 2021→2024 | R² | realised-fit slope 2021→2024 | R² | consensus ordering skill τ_b |
|---|---|---|---|---|---|
| QB | −66.6, −72.6, −58.6, **−45.0** | 0.31→0.18 | −72.8, −83.2, −60.1, **−75.6** | 0.91-0.96 | 0.484, 0.305, 0.263, 0.263 |
| TE | −42.7, −40.7, −26.4, **−25.4** | 0.31→0.17 | −45.9, −48.4, −38.9, −45.2 | 0.91-0.95 | 0.305, 0.263, 0.326, **0.200** |
| RB | −34.9, −51.7, −41.4, −47.1 | 0.15-0.34 | −65.5, −67.8, −60.5, −80.4 | 0.91-0.97 | 0.318, 0.402, 0.297, 0.453 |
| WR | −37.7, −49.8, −46.1, −35.4 | 0.18-0.41 | −65.3, −60.0, −62.1, −52.7 | 0.96-0.98 | 0.290, 0.408, 0.445, 0.298 |

**Answering the question I was actually asked — is it happening at other positions? Yes, at TE, and
only at TE.** QB and TE fitted slopes flattened while their realised value curves did not, and both
positions' consensus ordering skill declined. RB and WR show neither.

Honest counter-argument against my own reading: a fit on realised finish rank is an order-statistic
fit and is *mechanically* steeper than a fit on any imperfect ordering, so slope-ratio < 1 proves
nothing on its own (measured: 0.41-0.67, all sixteen below 1). The load-bearing evidence is
directional: **the QB realised value spread reached an era high while its consensus-fitted slope
fell.** Those cannot both be measuring positional value.

Corroborating, from a completely different angle (cross-positional calibration, consensus overall
pick vs realised VBD rank, top 100, n=4): QB was drafted **+16.9 picks too late in 2021**, then
+6.9, +0.5, **−1.1**. The mispricing that would justify a QB premium existed in 2021 and is gone by
2024. **The shipped board's flat pooling over 2021-2025 is carrying a dead 2021 signal.** ADR-057's
*conclusion* — the QB premium is stale — survives. Its *mechanism* probably does not.

### 4.3 Coach and coordinator tendency — **bounded near zero; do not fund the sourcing**

The data genuinely is not in the database (no `coaches` / `coaching_staff_seasons` table, confirmed
by table census). I was asked what it would buy. Two independent bounds, both cheap:

**Oracle bound.** Give a projection perfect foresight of the target season's team-level volume
(carries for RB, targets for WR/TE), keeping the player's own prior share and efficiency. Coaching
tendency is a strict subset of what that oracle sees.

| Pos | prior-year team volume | **oracle team volume** | Δ |
|---|---|---|---|
| RB | +0.298 [+0.25,+0.34] | +0.318 [+0.27,+0.36] | **+0.020** |
| WR | +0.356 [+0.31,+0.40] | +0.366 [+0.33,+0.41] | **+0.010** |
| TE | +0.243 [+0.17,+0.33] | +0.299 [+0.24,+0.37] | **+0.055** |

These are *upper bounds carrying a known self-inclusion leak* (a player's own volume is part of his
team's), which makes them generous — and they are still tiny. Team volume itself is only weakly
persistent anyway (y/y r: targets 0.43, carries 0.39, attempts 0.40).

**Fixed-effect bound.** Take the residual after predicting season points from prior points, and ask
how much of it is a team-level common shock. Between-team share of residual variance, minus what
random grouping of the same size would produce by chance:

| Pos | raw between-team share | expected by chance | **excess** |
|---|---|---|---|
| QB | 0.960 | 0.975 | **−0.015** |
| RB | 0.606 | 0.648 | **−0.042** |
| WR | 0.500 | 0.503 | **−0.002** |
| TE | 0.896 | 0.923 | **−0.027** |

**No excess team-level structure at any position.** QB/TE are badly underpowered here (1-2 players
per team, so degrees of freedom eat the estimate); WR at 60 players over ~32 teams is the one to
trust, and it is 0.000.

What sourcing would require, so the decision is informed rather than speculative: a
`coaching_staff_seasons` table (`coach_id`, team, role, season) scraped from Pro Football Reference,
plus a licensing check before building, plus a `coach_id` join through the team crosswalk in
`experiments/bottomup/data.py`. **My recommendation is not to build it.** Two independent methods
put the ceiling on the entire team channel at a few hundredths of τ, and the project has already
eliminated the two situation channels that ranked highest on prior expectation (vacated opportunity,
rookie draft capital). The calibration prior says a third situation story is the *least* likely
thing to work, not the most.

The same argument disposes of **Vegas implied team totals** as a priority: they are a forecast of
team environment, and team environment is the thing just bounded near zero.

### 4.4 Projection accuracy — **no systematic consensus error found large enough to trade on**

First, a trap I walked into and then removed: bucketing consensus residuals by consensus tier shows
top-12 players "underperforming" and 25+ players "overperforming" at every position. That is pure
Galton regression to the mean between two rankings of the same set, not a market error. Every figure
below is **de-trended** — residual taken against the fitted finish-vs-consensus line first.

De-trended residual correlations, 2021-2024, n=4 seasons, **descriptive, uncorrected, ~16
comparisons**:

| Pos | prior games | age | prior TD rate | prior ppg |
|---|---|---|---|---|
| QB | −0.048 | +0.119 | +0.041 | +0.042 |
| RB | −0.131 | −0.047 | **−0.173** | −0.066 |
| WR | **+0.170** | −0.083 | +0.028 | −0.013 |
| TE | −0.097 | +0.039 | +0.111 | **+0.173** |

The two largest, as hypotheses only: **consensus over-rates running backs coming off a high
touchdown rate** (r=−0.173 — the classic TD-regression story, apparently not fully priced), and
**consensus over-rates wide receivers coming off a partial season** (r=+0.170; WRs who played 9-12
games last year ran −0.087 ± 0.045 against the trend). Both are r² ≈ 0.03. Both are the kind of
compelling situation story that this project's own scorecard says is wrong four times in five. I am
recording them at half weight, as the calibration prior requires, and I am not proposing either as
a factor yet.

The more useful pattern is the coarse one: **consensus beats last season's ppg on the rate channel
at RB (0.449 vs 0.338) and WR (0.523 vs 0.436), and does not beat it at QB (0.348 vs 0.360) or TE
(0.303 vs 0.407).** That is the same QB/TE-versus-RB/WR split that shows up in §4.2's slope analysis
and in §3.2's ledger, from three different directions. Something real separates those two pairs.

---

## 5. Hypotheses discarded, and why

| Discarded | Why |
|---|---|
| "Bonus/ceiling pricing is our structural edge" | Measured: half a positional rank of realised reordering, less ex ante, and PR-002 already showed the reorder-driving residual does not persist. Keep the bonuses in the scoring engine; stop calling this the edge. |
| Coaching / coordinator tendency as a factor family | Two independent bounds put the whole team channel at ≤ +0.055 τ and zero excess fixed-effect variance. Not worth the sourcing. |
| Vegas implied team totals as a priority input | Forecasts the channel just bounded near zero. |
| Recency-weighting the pooled consensus rank curve | Probably the wrong fix; §4.2. Deferred to strategist, thread 085. |
| A durability / availability projection model | Prior-games predicts games at r = 0.09-0.18. The prototype already found a games model *worse than the position mean*. Availability is a large variance block and a near-empty signal block. |
| Consensus-tier-based "market bias" corrections | Regression-to-the-mean artifact. Confirmed by de-trending. |
| Anything at QB | Six configurations already failed; my ledger says only 0.063 of QB rate variance is stable-and-unpriced, the smallest of any position. Consistent, and closed. |
| Machine learning | Nothing here shows a simple model leaving signal on the table. Not a finding. |
| The self-excluded team-environment oracle | My own specification was numerically unstable as a player's share approached 1 and produced negative τ. Discarded as a broken spec, **not** reported as a negative result. The leaky version in §4.3 is the honest upper bound. |

---

## 6. What I need that does not exist

| Need | Status | Thread |
|---|---|---|
| **Expert consensus history before 2021** | The one gap that binds. n=4 usable seasons caps every market-relative claim below significance, permanently, by design of the data — not by choice of method. | **084** → `data-ops` |
| Coaching staff history | Not in the DB. **No longer requested** — §4.3 bounds it near zero. Recorded so the decision is not silently re-litigated. | — |
| Vegas odds / implied team totals | Not in the DB. **Deprioritised** for the same reason. | — |
| Route participation | Not directly available. **Partially superseded**: `snap_counts` (2013-2025, 324,611 rows) is already in the database and is a defensible proxy that must be labelled as one. See §7. | — |

---

## 7. The unexploited data already on disk

`experiments/bottomup/data.py` reads `player_weekly_stats`, `draft_picks` and `ff_playerids`. That
is all. Sitting unused in the same database:

| Table | Coverage | Rows | Why it matters |
|---|---|---|---|
| `snap_counts` | 2013-2025 | 324,611 | `offense_pct` is the closest thing to route participation the project can get without new ingestion. Snap share is the standard role signal and the prototype's usage arm never saw it. **Label as a proxy.** |
| `ngs_receiving` | 2016-2025 | 14,731 | `avg_separation`, `avg_cushion`, `percent_share_of_intended_air_yards` — separation is the one receiver trait plausibly stable and not visible in box scores. |
| `ngs_rushing` | 2016-2025 | 6,059 | `efficiency`, `percent_attempts_gte_eight_defenders` — box-independent context for the RB TD-regression hypothesis in §4.4. |
| `depth_charts_weekly` | 2001-2024 | 865,329 | Ends 2024 (a known gap for the 2026 board) but is complete for every backtest fold. |
| `injuries` | 2009-2024 | 79,816 | `as_of_date`-enforced. The only lever on the availability block, which §3.3 shows is the largest unexplained one. |

**This is the cheapest real lead in the document**: twelve to thirteen seasons of role data, zero
acquisition cost, zero licensing question, and a plausible mechanism at exactly the position (TE)
where §3.2 says the unpriced stable signal is.

---

## 8. Reproducing this

Every figure comes from five scripts against a read-only handle on `data/nfl.db`, scored with
`src/scoring.py::score_offensive_game` so the points match the shipped harness exactly. The
recipes, so they can be rebuilt without the scratchpad:

1. **Loader** — `player_weekly_stats` REG rows 1999-2024 at QB/RB/WR/TE, scored per game, aggregated
   to player-seasons with bonus and bonus-free totals kept separately; modal position and team;
   per-week point vectors retained for split-half. Universe frozen from season N−1 at ADR-016 depths
   (QB 20 / RB 45 / WR 60 / TE 20).
2. **Oracle ladder + reliability** — §3.1, §3.2, §3.3.
3. **Rate ladder + consensus** — §3.2's consensus columns, §4.4's residuals (de-trended).
4. **Channels** — §4.1 bonus arithmetic, §4.2 realised curves, §4.3 volume oracle.
5. **Bounds** — §4.2's side-by-side fits, §4.3's fixed-effect ANOVA, §4.4's cross-positional
   calibration.

Bootstrap CIs resample **seasons**, not players, per `docs/statistical-guardrails.md` §7. Seed
20260729, 4000 draws.

**Checks applied:** look-ahead (structural — 2025 never loaded; predictors read only seasons < N);
survivorship (universe frozen pre-season, zero-game players scored 0 and retained); multiple
comparisons (**not corrected — this pass is exploratory and no result is claimed as significant**);
uncertainty (CI on every headline figure); baselines (B1 prior points, B2 prior ppg, B3 three-season
average, and consensus where it exists).

**What would falsify the main conclusion:** if the realised-finish-rank curve turns out to be a
mechanical artefact of order-statistic fitting rather than a real value structure, §4.2 collapses
and the ADR-057 recency fix is fine after all. That is precisely the question thread 085 asks
`strategist` to rule on, and it is the reason I did not act on it.
