# Are injury-prediction services accurate enough to be worth buying?

**Researcher, 2026-07-30.** Answers the founder's question, relayed as FR-097: *"how accurate are the
injury sites at predicting injuries, is that worthwhile?"*

Confidence tags per `docs/operating-model.md`: `[VERIFIED]` fetched from the source itself,
`[SNIPPET]` search excerpt only, `[SECONDARY]` third-party reporting, `[GAP]` could not establish.
**No number in this document fills a `[GAP]`.**

---

## Recommendation

**Buy nothing. Cost avoided: roughly $100–190/year** (see §4 for the measured figures and what did
not render).

Three independent reasons. Any one of them is sufficient on its own; the third is fatal regardless
of the other two.

1. **Unmeasurable.** No retail service publishes dated, per-player, archivable predictions. We
   could not check whether last season's forecasts were right, and after buying we still could not.
   Purchase would be an act of faith with no post-hoc audit path.
2. **Wrong target.** The one service with real numeric outputs *and* a documented validation
   (Draft Sharks, having acquired Sports Injury Predictor) validates on "misses at least two
   quarters of a game" — the **short**-absence category we already capture for free. Its
   games-missed model reports **MAE 1.610 games** `[VERIFIED]`, on an outcome where 64% of real
   events cost ≤2 games `[VERIFIED]`. Its discrimination on 9+ game absences is **never reported**
   `[GAP]`. It does not fill our gap; it duplicates what we already have.
3. **Unusable in the product.** `draftsharks.com`'s "Terms of Use" footer link is a dead `#`
   placeholder — **no terms document is reachable on the site** `[VERIFIED]`. `CLAUDE.md` §5
   requires checking terms *before* building against a source. We cannot. The app is publicly
   hosted (`docs/CURRENT-STATE.md`). Best case this is a personal-use backtest input that can never
   be displayed — the same fence as the Sleeper projections (thread 092).

**Do this instead, at zero cost:** the real gap is *current status*, not *forecast*. See §6.

---

## 1. The reframe, and why the founder's question as posed cannot be answered

"How accurate are they" is unanswerable for most of the market because most of the market does not
issue falsifiable claims. The productive questions, per service:

| Service | Publishes dated, specific, third-party-scoreable pre-season predictions? | Independently scored? | Reports a base rate alongside its accuracy? | Retail price |
|---|---|---|---|---|
| **Draft Sharks Injury Guide** (acquired Sports Injury Predictor) | Numeric outputs exist (in-season injury %, projected games missed with an 80% interval, durability 1–5) but paywalled, no visible as-of stamp, no archive of prior years' predictions found `[GAP]` | **No** `[GAP]` — searched, found none | **Yes** — the one service that does. Benchmarks stated explicitly, incl. "Historical Average (32% injury chance for all)" and a positional-average model `[VERIFIED]` | $16/mo displayed regular, entry tier `[VERIFIED]` |
| **PlayerProfiler Injury Finder / Fragility Rating** | Percentile *tiers*, not probabilities `[VERIFIED]` | No `[GAP]` | **No** — 2023 games-missed-by-tier stats given with no all-player denominator `[VERIFIED]` | `[GAP]` |
| **Footballguys Injury Index** | Retrospective; re-injury ratings as Low/Med/High/Very High `[VERIFIED]` | No `[GAP]` | No `[VERIFIED]` | PRO sub, price `[GAP]` |
| **Fantasy Points Injury Outlook** | Narrative medical analysis, no per-player probability `[VERIFIED]` | No `[GAP]` | Cites literature recurrence rates, but no denominator for its own calls `[VERIFIED]` | Sub, price `[GAP]` |
| **Ourlads Fantasy Injury Predictor** | `[GAP]` — the URL returned by search 404s on fetch | `[GAP]` | `[GAP]` | `[GAP]` |
| **Zone7 / Kitman Labs / Zelus** (team-side B2B) | Not retail. Requires GPS/wearable/medical inputs we cannot obtain `[VERIFIED]` for Zone7 | Vendor-run study, **explicitly "not intended nor designed to serve as peer reviewed scientific research"** `[VERIFIED]` | **No** — base rate not stated `[VERIFIED]` | Not sold to individuals `[GAP]` on price |

**The highest-value cell in that table is column 1, and it is almost uniformly "no."** For four of
six services the output is a tier or a paragraph. A tier cannot be scored. Their accuracy is
unmeasurable not just by us but by their own publishers, and that is most of a buy decision on its
own.

### Sample quality — this is an n of 1, not an n of 6

The six services collapse into three methodological units, and only one of them is even in scope:

- **Draft Sharks and Sports Injury Predictor are the same unit.** Draft Sharks acquired SIP and
  folded it in-house `[VERIFIED]`. Anyone comparing "SIP" against "Draft Sharks" is comparing a
  thing to itself.
- **Footballguys, Fantasy Points, PlayerProfiler are one unit for this question** — all three emit
  tiers or narrative, so all three answer column 1 identically for the same structural reason.
- **Zone7 / Kitman / Zelus are one unit** — B2B, wearable-fed, not purchasable by an individual.

So the effective sample for *"a retail numeric NFL injury model with a documented validation"* is
**exactly one**. That is the finding, and it should be read as a thin market rather than as
convergent evidence from six sources.

**Non-representativeness I could not fix:** English-language, US, one search engine, public pages
only. A model that is marketed only behind a paywall, on a podcast, or in a Discord would be
invisible to this survey `[GAP]`.

---

## 2. The one service with a real validation, examined properly

Draft Sharks' methodology page (`/injury-predictor/about`, **"Updated 9/28/20 by Jason Phelps"**)
`[VERIFIED]`. Verbatim:

> "ROC-AUC moves from a poor 0.626 to a borderline good 0.809"
> "log loss makes a significant improvement over the positional average model (from 0.646 to 0.542)"
> "R2 value jumps from a benchmark best of 0.026 to 0.401"
> "mean absolute error is 1.610; meaning, on average, our predictions are off by about a game and a half"

Setup `[VERIFIED]`: ~300 variables over ~3,500 player-seasons; trained on seasons before 2016;
tested on **385 player-seasons from 2016**. Benchmarks named: Historical Mode (0% for all),
Historical Average (32% for all), Historical **Positional** Average, and Career In-Season Injury
Rate. Inputs include prior-injury counts, time-since-last-injury, high-impact plays, snaps, ADP,
strength-to-weight. They state they used *"2016 preseason projections provided by DraftSharks.com
instead of a player's actual usage."*

**What is genuinely good here, and should be said plainly:** this is the only vendor in the survey
that (a) states its base rate, (b) benchmarks against a *positional* average rather than a global
one — the correct control, since position alone moves per-game injury rate by 2× (§5) — and (c)
uses preseason projections rather than realised usage, which is the right guard against the
look-ahead leak our own `CLAUDE.md` §6.1 exists to prevent. Credit where due.

**Why it still does not support a purchase:**

| Objection | Detail |
|---|---|
| **One holdout season** | 385 player-seasons, 2016 only. Under `CLAUDE.md` §6.3 that is a hypothesis, not a finding. Player-seasons are heavily autocorrelated — the same players recur — so 385 rows is far fewer than 385 independent observations. |
| **Ten years stale** | The page reporting it was last updated **2020-09-28**; the test season is **2016**. No statement anywhere that the model has been revalidated since `[VERIFIED]` — the absence is verified, not assumed. |
| **Vendor self-reported, never replicated** | I searched specifically for an independent scoring of SIP/Draft Sharks predictions and found none `[GAP]`. |
| **Not reproducible even by the buyer** | The KB page states no publication dates accompany the predictions themselves `[VERIFIED]`. Prior seasons' prediction sets are not archived publicly. A subscriber cannot audit last year's calls. |
| **Wrong target** | The classification target is *"the chance a player misses at least two quarters in a game"* `[VERIFIED]`. That is the short-absence event. |

### The tail — the only thing we actually needed

Our stated gap (per dispatch, sourced to `ranker`; **unverifiable in this worktree** — see §7) is
that `nfl.db.injuries` captures 26–35% of short absences but only **2.5–4.8% of absences of nine
games or more**, because season-ending IR removes a player from the weekly report entirely.

Against that gap, `MAE = 1.610 games` is close to disqualifying on its face. `[VERIFIED]` from an
independent source: **64% of injuries that cost at least one game cost two or fewer**, and the mean
absence is 3.1 games (ProFootballLogic, 2015 season, 1,794 players). An error metric of 1.6 games
on a distribution whose mass sits at 0–2 games is dominated by the short-absence bulk. It tells you
almost nothing about whether the model separates "misses 2" from "misses 11".

**Does it discriminate in the tail? `[GAP]`.** No vendor reports it, no independent party has
measured it, and it is not derivable from the published figures. **I will not estimate it.** The
honest statement is: the single quantity that would justify buying this product has never been
published by anyone.

`R² = 0.401` on games missed looks strong and should be treated with suspicion rather than
enthusiasm: on a zero-inflated, right-skewed outcome, R² is largely earned by correctly predicting
the many zeros, and is compatible with no tail discrimination at all. That is a mechanism, stated as
a caution, not a measurement — I did not verify it against their data and could not.

---

## 3. Does the underlying scientific claim hold up?

**Association: yes, weakly and consistently reported.** Prior injury is a recognised risk factor
across sports `[SECONDARY]`.

**Discrimination — the thing that would make it purchasable: no, and this is well documented.**

| Source | Finding, verbatim where quoted |
|---|---|
| **Bullock GS, Mylott J, Hughes T, Nicholson KF, Riley RD, Collins GS.** *Just How Confident Can We Be in Predicting Sports Injuries?* Sports Med. 2022 Oct;52(10):2469–2482. doi:10.1007/s40279-022-01698-9 `[VERIFIED]` | "Thirty studies (204 models) were included"; "2% of models (7% of studies) were low risk of bias and 98% of models (93% of studies) were high or unclear risk of bias"; **"All studies developed a prediction model and no studies externally validated a prediction model"**; **"No models could be recommended for use in practice."** |
| **Leckey C, van Dyk N, Doherty C, et al.** *Machine learning approaches to injury risk prediction in sport: a scoping review with evidence synthesis.* Br J Sports Med. 2024;59(7):e108576. doi:10.1136/bjsports-2024-108576 `[VERIFIED]` | AUC "ranged between 0.57 and 0.95" across 27 reporting studies; one-third in the 0.50–0.69 "poor" band. "While several studies report strong predictive performance, their clinical utility can be limited, with wide prediction windows or broad definitions of injury." "Three studies reported model performance of AUC>0.9, yet the clinical relevance is questionable." 39% of studies had class imbalance. |
| **Van Eetvelde H, et al.** *Machine learning methods in sport injury prediction and prevention: a systematic review.* J Exp Orthop. 2021. doi:10.1186/s40634-021-00346-x `[VERIFIED]` | 11 studies. "Injury predictive performance ranged from poor (Accuracy = 52%, AUC = 0.52) to strong (AUC = 0.87, f1-score = 85%)." "the methodological study quality was moderate to very low." Notes dependency between training and test sets in several studies. |
| **Bahr R.** *Why screening tests to predict injury do not work—and probably never will…: a critical review.* Br J Sports Med. 2016;50(13):776–780 `[SECONDARY]` — abstract read via review aggregators, publisher page not rendered | No screening test for sports injuries has adequate test properties; substantial overlap between high- and low-risk players is to be expected; a statistically significant association is not sufficient for predictive accuracy. |

Two things to carry forward from that table.

- **"Externally validated: zero, out of 204 models."** Every published sports injury model is a
  development study. Draft Sharks' 2016 test is an internal holdout by the same team that built the
  model — methodologically the same class of evidence the Bullock review says cannot be recommended
  for use.
- **Note the wide AUC range and read it as a warning, not a menu.** Leckey's 0.57–0.95 spread across
  studies with 39% class imbalance is the signature of small samples and optimistic internal
  validation, not of a solved problem. Draft Sharks' 0.809 sits comfortably inside that spread — it
  is unremarkable within a literature that concludes nothing is ready for use.

**Confounding with position, age and usage:** real and large. Per-game injury rate by position runs
from **2.5% (QB)** to **5.2% (RB)** `[VERIFIED]`, a 2× spread from position alone. Any "high risk"
list that is disproportionately running backs is partly just restating position. Draft Sharks is the
only vendor that controls for this (their positional-average benchmark, AUC 0.626). For every other
service, whether the tiers survive conditioning on position is **`[GAP]`**.

---

## 4. Cost

`[VERIFIED]` from `draftsharks.com/subscribe`, as displayed 2026-07-30:

| Tier | Displayed regular price | Discounted rate shown |
|---|---|---|
| Traditional Leagues, Unlimited | $16/month | $6/month billed semi-annually |
| Plus Keeper, Dynasty & Auction ("Most Popular") | $22/month | $8/month billed semi-annually |
| Plus Personalized Advice | $44/month | $16/month billed semi-annually |

The Injury Guide is **Insider-members-only** `[VERIFIED]`; it is not in a free tier.

**Annual totals `[GAP]`.** The page computes them client-side; the fetch returned unrendered
template placeholders (`{{formatCentsAsCurrency(proratedAmounts['X'] / 2)}}`). **I am not going to
multiply and present the result as a price.** Bounding it honestly at the displayed regular monthly
rate: the entry tier is **at most $192/year**, and the promotional semi-annual rate implies
materially less. That range — call it **$100–190/year** — is the cost this recommendation avoids.

Other services' prices: `[GAP]`, not pursued once the falsifiability column had already closed them
out.

---

## 5. Base rates — so no accuracy figure in this document floats free

`[VERIFIED]`, ProFootballLogic NFL Injury Rate Analysis, 2015 season, 1,794 players, per-week snap
and injury tracking, weeks 1–16:

| Quantity | Value |
|---|---|
| Players missing ≥1 game | **38%** (688 of 1,794) |
| Players available all 16 games | 45% |
| Mean games available | 14.2 of 16 |
| Per-game probability of an injury costing the next game | **4.1%** |
| Mean length of an absence, given ≥1 game missed | 3.1 games |
| Share of absences costing ≤2 games | **64%** |
| Injuries/game — RB / OL / QB | 5.2% / 3.4% / 2.5% |

Draft Sharks' own stated base rate for its target event is **32%** `[VERIFIED]`. These are different
definitions and different populations and should not be arithmetically compared, but both establish
the same thing: **roughly a third of players suffer the event every year anyway.**

That is the number that makes most vendor marketing unusable. PlayerProfiler's "approximately
50-percent of 80th–100th-percentile WRs missed at least two games" `[VERIFIED]` has **no denominator
attached** — without knowing what share of *all* WRs missed two games, 50% could be a strong signal
or could be noise. **Marked unusable**, per the standard this project holds itself to.

Zone7's "72.4%" is the same defect at team level: it is a **sensitivity** (of injuries that
occurred, how many were flagged), computed over 423 injuries across 11 professional soccer teams,
2019–2021, **with the base rate not stated and no false-positive rate reported** `[VERIFIED]`. A
flag-everyone policy scores 100% on that metric. **Marked unusable.**

**Our free baseline.** Per the dispatch, our own pipeline found prior-season games missed is *not
significant*, with non-monotonic sign order and both extreme buckets flipping sign between eras
(`docs/analysis/adp-vs-production-2026-07-30.md:199`). **I could not verify this — that file does
not exist in this worktree** (§7); it is carried as `[GAP]`, sourced to the dispatch. I also searched
for external corroboration that prior-season games missed predicts next-season games missed in the
NFL and found **no peer-reviewed study establishing it** `[GAP]` — which is consistent with, but does
not confirm, our null.

**The uncomfortable framing this creates, stated plainly:** a paid product would have to clear a free
baseline that appears to be worth approximately nothing. That is a low bar and *still* nobody has
published evidence of clearing it on the long-absence tail.

---

## 6. What to buy instead: nothing, but do this

**The gap is misdiagnosed as a prediction problem.** A player who tore an ACL in December and is
rehabbing in July is not a forecast — he is a *known fact*, publicly reported, and he is exactly the
population our weekly-practice-report `injuries` table structurally cannot see, because IR removes
him from the report. The 2.5–4.8% long-absence capture rate is a **status-feed** hole, not a
modelling hole.

Free, documented, lawful to fetch:

| Source | What it closes | Terms |
|---|---|---|
| **Sleeper `/v1/players/nfl`** — fields `status`, `injury_status`, `injury_start_date`, `practice_participation` `[VERIFIED]` from `docs.sleeper.com` | Current IR / PUP / out status, the exact population nflverse injuries misses | Docs explicitly instruct *"save this information on your own servers"* and *"use this call sparingly… once per day at most"* `[VERIFIED]`. **Fetching: invited. Redistribution: forbidden** — already established in this project (thread 092). Personal-use fence applies, same as the Sleeper projections. |
| **nflverse `load_rosters()`** status | Already open item 8 (T6 roster-status ingest) | CC-BY |

Both are already on the open-items list. **This research does not add work; it says do the free work
already queued instead of spending money, and it raises its priority.**

Two honest caveats on the free path:

1. It gives **current status**, not forward risk. It will tell you Player X is on IR today. It will
   not tell you Player Y is likelier than average to end up there in November. Nothing purchasable
   does that credibly either — that is the whole finding.
2. Sleeper has **zero history**. Its value is entirely a function of when snapshotting starts
   (`docs/research/timeseries-data-audit-2026-07.md` §5 makes the same argument, unchanged). Every
   day without a snapshot is a permanently lost row. Same urgency as ADP.

Also relevant and already documented: nflverse's injury source **died after the 2024 season**
(*"At the moment, there is no 2025 data and there is no ETA"*, `[VERIFIED]` in the timeseries audit
§2.5), and NFL.com is `[BLOCKED]` by ToS for database compilation. So Sleeper is not a nice-to-have
alternative to buying — it is the only lawful forward injury feed we have identified at all.

---

## 7. What I could not do, and one contradiction to resolve

**No Bash tool in this session.** Could not run `tools/handoffs.py` (so no thread ID is allocated —
the handoff is filed as `NEW-`), could not run `tools/founder_requests.py`, could not commit, and
**could not query `nfl.db` to compute our own injury base rate for the fantasy-relevant population**,
which would have been the single most useful number in this document. This is the fourth researcher
session on record to hit this; noting it rather than routing around it.

**Two files named in the dispatch do not exist in this worktree** —
`docs/founder-requests/FR-097-are-injury-prediction-services-accurate-enough-t.md` (highest FR
present is **FR-071**; `docs/founder-requests/INDEX.md` says "56 requests since freeze") and
`docs/analysis/adp-vs-production-2026-07-30.md` (`docs/analysis/` does not exist here). The `ranker`
finding about 26–35% / 2.5–4.8% injury-table coverage is likewise not present in any doc in this
worktree.

I did **not** resolve this. I proceeded on the framing carried in the dispatch itself, which is
self-contained, and every claim sourced to those files is tagged `[GAP]` above rather than reported
as verified. **Escalated to `pm` in the handoff** — this is either a worktree behind `main`, or FR-097
was never actually created, and it is not a researcher call which.

**Other explicit gaps:** Draft Sharks' Terms of Use content (the link is a placeholder, so there may
be no document at all, or it may exist at an unlinked URL I did not find); whether the paywalled
injury-predictor tables carry an as-of date (the pages exceed the fetcher's length limit and
truncated on four attempts); Ourlads' product entirely; prices for PlayerProfiler / Footballguys /
Fantasy Points; and any tail-discrimination figure for any product, from anyone.

**`draftsharks.com/robots.txt` `[VERIFIED]`:** `User-agent: *` / `Disallow:` — crawling is fully
permitted. That does not help. Fetching is allowed; the terms governing what we could *do* with it
are unreachable, and it is the terms that decide the product question.

---

## 8. What would change this answer

A trigger list, so this does not get re-researched from scratch:

1. **Any service publishes a dated, downloadable, per-player pre-season forecast file** and leaves
   prior years' files up. Then it becomes scoreable and worth one season of free observation before
   any purchase.
2. **Any independent party scores a vendor's long-absence (≥9 games) discrimination against a
   stated base rate.** That is the exact missing measurement.
3. **Draft Sharks publishes a revalidation on a post-2020 season**, ideally with tail performance
   broken out. The current evidence is a 2016 test on a 2020 page.
4. **A peer-reviewed, externally validated NFL injury model appears.** Per Bullock 2022 the count of
   externally validated sports injury models is currently zero, across all sports.
5. **The project goes multi-user or the terms question changes.** Irrelevant while nothing is worth
   buying, but it is the gate that would still bite if #1–#4 all resolved favourably.

---

## Sources

- [Draft Sharks — About the Injury Guide](https://www.draftsharks.com/injury-predictor/about) `[VERIFIED]`
- [Draft Sharks — Injury Predictor KB](https://www.draftsharks.com/kb/injury-predictor) `[VERIFIED]`
- [Draft Sharks — Subscribe](https://www.draftsharks.com/subscribe) `[VERIFIED]`
- [Draft Sharks — robots.txt](https://www.draftsharks.com/robots.txt) `[VERIFIED]`
- [Draft Sharks — Privacy Policy](https://www.draftsharks.com/site/privacy-policy) `[VERIFIED]` (Terms of Use link is a `#` placeholder)
- [PlayerProfiler — Injury Finder](https://www.playerprofiler.com/article/nfl-injured-players-injury-finder/) `[VERIFIED]`
- [Footballguys — 2024 Injury Index](https://www.footballguys.com/article/2024-injury-index-fantasy-performance-re-injury-rate-by-position) `[VERIFIED]` (paywalled beyond QB preview)
- [Fantasy Points — 2025 Fantasy Football Injury Outlook](https://www.fantasypoints.com/nfl/articles/2025/fantasy-football-injury-outlook) `[VERIFIED]`
- [Zone7 — Validation Study](https://zone7.ai/case-studies/validation-study/validation-study-injury-risk-forecasting-with-zone7-ai/) `[VERIFIED]`
- [ProFootballLogic — NFL Injury Rate Analysis](https://www.profootballlogic.com/articles/nfl-injury-rate-analysis/) `[VERIFIED]`
- [Bullock et al. 2022, Sports Med — PubMed 35689749](https://pubmed.ncbi.nlm.nih.gov/35689749/) `[VERIFIED]`
- [Leckey et al. 2024, Br J Sports Med — PMC12013557](https://pmc.ncbi.nlm.nih.gov/articles/PMC12013557/) `[VERIFIED]`
- [Van Eetvelde et al. 2021, J Exp Orthop — PMC8046881](https://pmc.ncbi.nlm.nih.gov/articles/PMC8046881/) `[VERIFIED]`
- [Bahr 2016, Br J Sports Med — via Physio Network review](https://www.physio-network.com/research-reviews/other/golden-oldie-why-screening-tests-to-predict-injury-do-not-work-and-probably-never-will-a-critical-review/) `[SECONDARY]`
- [Sleeper API docs](https://docs.sleeper.com/) `[VERIFIED]`
- [Ourlads — Fantasy Injury Predictor](https://www.ourlads.com/fantasy/injury-predictor) `[GAP]` — 404 on fetch
