# Sleeper screen: can we predict late-ADP breakouts before they happen? (FR-094)

**Session:** backend, 2026-07-30. **Founder request (verbatim):** "I wonder if we can predict
'sleepers' Later round ADPs but who show some characteristics of a break out but not enough to
warrant score adjustments or early round picks." **Design constraint honored throughout:** this
line of work, if anything survives, produces a **flag beside the ranking**, never an adjustment
inside it — `CLAUDE.md` §4's ranking sources stay separate, never blended.

**This is a Sonnet/default-tier session, not a dispatched Opus/high-effort one.** Per
`docs/operating-model.md`, statistical-methodology work like this should arrive dispatched to
Opus at high effort; this dispatch did not specify that. Flagging this explicitly rather than
stopping to ask — the analysis below applies every guardrail in `docs/statistical-guardrails.md`
this session could identify, but a second, Opus-tier read is exactly the kind of check that
document says Statistician + Red-team should still run before any of this is trusted for a
product change (handoff opened to `strategist` below).

**Script:** `analysis/sleeper_screen.py` (self-contained, no network calls, ~10s runtime against
a populated `data/nfl.db`). **Raw output:** `data/qa/sleeper-screen-2026-07-30.json`.

**Why self-contained rather than importing the ADP-vs-production analysis's script:** that
script's commit lives on a sibling worktree branch not yet merged into this branch's history.
Importing across an unmerged sibling branch would make this script silently break the moment
that branch is rebased or squashed. The universe-loading, VBD, and season-clustered-resampling
logic is duplicated here (documented in the script's own module docstring), not re-invented from
scratch — see `docs/analysis/adp-vs-production-2026-07-30.md` for the shared methodology this
reuses conceptually.

---

## 0. Data source and its limits — same caveats as the sibling analysis

Same source, same caveats as `docs/analysis/adp-vs-production-2026-07-30.md`: FFC 12-team
half-PPR mock-draft ADP (`ffc_adp_snapshots`, `adp_source='ffc_half_ppr_12team'`), seasons
2018–2024. **Not** this league's real 10-team ADP (no verified 10-team historical source exists
anywhere in this project). Mock drafts, not real drafts. 2025 is not in this ADP source at all —
the project's locked holdout is untouched by construction. Train 2018–2023, holdout 2024, same
split as the sibling analysis so the two documents are directly comparable — one look at 2024,
reported below even where it weakens the finding.

**A real, separate finding from rebuilding `data/nfl.db` this session:** this worktree's DB
started as an empty 0-byte stub (the standing worktree gotcha, `docs/environment.md` §4).
Rebuilt via `scripts/rebuild_database.py`'s steps 1/2/3/5/6 plus a direct call into
`ingest_ffc_adp.import_all_snapshot_csvs` for the FFC ADP history (step 4, `ingest_rankings.py`,
403'd on `dynastyprocess/data` in this session specifically — a known, documented proxy
restriction per that script's own docstring, not something this session's analysis needs: no
`rankings` table is read anywhere in this script).

---

## 1. Method

### 1.1 Universe / survivorship
For season *N*, the population is every player in that season's FFC ADP snapshot with
`adp_overall_rank >= 109` (12-team round 10+) — decided before the season, no outcome
information used. A player who did nothing that season stays in with `actual_vbd` computed
against the position's replacement floor (never dropped — `CLAUDE.md` §6.2).

### 1.2 Cutoff justification
Round 10+ (rank ≥ 109) is one bucket further out than the round-9+ bucket already reported in
the sibling analysis, which found round-9+ **already carries a strong positive residual**
(WR +54.8, TE +68.3 VBD pts/season) — the market half-expects upside that late. A "sleeper" flag
is supposed to find value the market has *not* already partially priced in, so round 10+ is the
honest place to test it. This is a judgment call, stated as one — picked from a structure already
reported before this script ran, not tuned against this script's own outcome.

### 1.3 Hit definition
"Startable value" = `actual_vbd > 0` — positive value over this league's own measured
replacement level (ADR-029's RB30/WR40/TE10/QB10 baselines, `scoring.compute_vbd`/
`ReplacementLevels`, identical machinery to the sibling analysis).

### 1.4 Features (pre-registered)
1. **AGE_YOUNG** — WR/TE, age ≤23 as of Sept 1 of season *N*. Re-tests the sibling analysis's
   MODERATE-HIGH-confidence finding (+34.6 VBD pts/season across the whole board) on a
   **narrower population** (round 10+ only) and a **different metric** (binary hit rate, not
   mean residual).
2. **EFFICIENT_LOW_VOLUME** — prior-season (*N*−1) efficiency percentile within position ≥0.75
   AND volume percentile ≤0.40, among players with qualifying volume. The "productive when used"
   case FR-094 names.
3. **RISING_SHARE** — within-season *N*−1 target-share **trend**: mean(weeks 10–18) −
   mean(weeks 1–9) ≥ +5 percentage points, WR/RB/TE only, ≥2 qualifying weeks in each half. Tests
   the guardrail's own example directly: a player finishing strong looks identical to a fading
   one in a season *mean*, so only the trend is tested, never the mean.

### 1.5 Not tested this pass
- **Depth-chart position change / vacated targets** — named by FR-094, not built this pass
  (time-boxed). Logged to `docs/ideas-inbox.md` as untested, explicitly not a null result.
- **Team change** — already tested against the *full* ADP board in the sibling analysis (Tier 3,
  no reliable pattern, era-split flips sign). Not re-run against this narrower round-10+
  population, to keep this pass's family count small. The prior null is cited, not re-derived.
- **Route participation — BLOCKED.** No route-run or route-participation column exists anywhere
  in this project's ingested tables (checked every player-level table's schema directly: no
  `routes`, `route_participation`, or equivalent field on `player_weekly_stats`, `ngs_receiving`,
  `snap_counts`, or `depth_charts_weekly`). FTN charting data — the documented potential source —
  is not ingested. Not proxied silently, per the standing rule that a source swap must be
  verified, not assumed.

### 1.6 Multiple comparisons
Three pre-registered features, one p-value each (season-clustered permutation test on the binary
hit indicator — shuffle the flag within each season, preserving that season's own hit-rate base
and flagged/unflagged group sizes). Benjamini–Hochberg correction across the three. A combined
OR-flag is reported separately, explicitly labeled **exploratory, not pre-registered** — no
significance test was run on it; it did not earn one.

### 1.7 Uncertainty
Wilson score 95% intervals throughout (not normal-approximation, which misbehaves at small *n*
and rates near 0/1 — exactly this analysis's regime).

---

## 2. Step 1 — the base rate (report this even if step 2 finds nothing)

**Train seasons (2018–2023), round-10+ universe:**

| Position | n | hits | rate | Wilson 95% CI |
|---|---|---|---|---|
| QB | 46 | 7 | 15.2% | [7.6%, 28.2%] |
| RB | 70 | 15 | 21.4% | [13.4%, 32.4%] |
| WR | 82 | 23 | 28.0% | [19.5%, 38.6%] |
| TE | 34 | 11 | 32.4% | [19.1%, 49.2%] |
| **ALL** | **232** | **56** | **24.1%** | **[19.1%, 30.0%]** |

**Holdout (2024):**

| Position | n | hits | rate | Wilson 95% CI |
|---|---|---|---|---|
| QB | 9 | 1 | 11.1% | [2.0%, 43.5%] |
| RB | 16 | 5 | 31.2% | [14.2%, 55.6%] |
| WR | 17 | 5 | 29.4% | [13.3%, 53.1%] |
| TE | 7 | 1 | 14.3% | [2.6%, 51.3%] |
| **ALL** | **49** | **12** | **24.5%** | **[14.6%, 38.1%]** |

**This is the headline finding, on its own, independent of anything in step 2:** roughly **1 in 4**
players drafted beyond 12-team-round-9 in FFC mock drafts return positive value over this
league's own replacement level in a normal season — not the 3–6% a "sleeper" framing might
imply. The pooled overall rate is stable train→holdout (24.1% vs 24.5%, CIs overlap almost
entirely), which is reassuring for the base rate itself even though per-position holdout cells
are too small (n=7–17) to read individually with confidence. TE and WR run somewhat higher than
QB in train, consistent with the sibling analysis's position-level findings, but every
per-position CI here is wide enough to overlap its neighbors — do not over-read the position
ordering at this *n*.

**A caveat on universe size:** the round-10+ population is thin in the earlier and thinner FFC
board-years — 2022 in particular has only 9 qualifying rows train-side, because that season's
underlying 12-team board itself has only 114 total rows (vs. 180 in 2023), a data-availability
gap already documented in the sibling analysis, not a bug in this script. Season-level counts:
2018 n=21, 2019 n=28, 2020 n=45, 2021 n=65, 2022 n=9, 2023 n=64, 2024 n=49 (full breakdown in the
JSON output).

**This base rate does not, on its own, say the screen is actionable — that is step 2's
question.** A 24% base rate is high enough that a screen only adds value if it *meaningfully*
separates the 24% from the 76%, not merely if it points at players who might hit (a quarter of
this universe will, regardless of any feature).

---

## 3. Step 2 — does anything separate the hits from the misses?

**None of the three pre-registered features reach significance, even before correction.**

| Feature | Train flagged n | Flagged hit rate | Wilson 95% CI | Unflagged hit rate | p (raw) | p (BH-adj) |
|---|---|---|---|---|---|---|
| AGE_YOUNG | 47 | 31.9% | [20.4%, 46.2%] | 22.2% | 0.209 | 0.400 |
| EFFICIENT_LOW_VOLUME | 6 | 33.3% | [9.7%, 70.0%] | 23.9% | 0.643 | 0.643 |
| RISING_SHARE | 20 | 35.0% | [18.1%, 56.7%] | 23.1% | 0.266 | 0.400 |

**Holdout (2024), same frozen definitions, one look:**

| Feature | Holdout flagged n | Flagged hit rate | Wilson 95% CI | Holdout base rate |
|---|---|---|---|---|
| AGE_YOUNG | 8 | 37.5% | [13.7%, 69.4%] | 24.5% |
| EFFICIENT_LOW_VOLUME | 0 | — (no qualifying players) | — | 24.5% |
| RISING_SHARE | 6 | **0.0%** | [0%, 39.0%] | 24.5% |

**Reading this plainly, per the dispatch's own instruction:**

- **AGE_YOUNG** is directionally the strongest of the three (train lift ×1.32, and it's the only
  one that held its direction in holdout — 37.5% vs. 24.5% base), consistent with the sibling
  analysis's independently-evidenced age effect on the full board. But at *n*=47 flagged
  train-side and *n*=8 holdout-side, it does not clear significance even before multiple-
  comparisons correction (raw p=0.209), and the holdout CI is wide enough (13.7%–69.4%) to be
  fully consistent with no effect. **This is underpowered, not disproven** — the narrower round-10+
  universe (vs. the sibling analysis's whole board) cuts the flagged sample roughly in half.
- **EFFICIENT_LOW_VOLUME** flags almost nobody in this universe (*n*=6 train, *n*=0 holdout) —
  the "productive on low volume, still going undrafted past round 9" case is rare enough at these
  percentile thresholds (≥75th efficiency, ≤40th volume) that this feature cannot be evaluated
  meaningfully here. Not a negative finding; an unpowered one.
- **RISING_SHARE** looked the most promising train-side (lift ×1.45) and **completely inverted**
  in holdout (0 of 6 hit, vs. a 24.5% base rate that season). A single holdout season is too small
  to call this "disproven" either, but a feature whose train-side lift disappears entirely on its
  one permitted look is the textbook shape of an overfit false positive, and is reported as such
  rather than kept as a hopeful finding.

**Exploratory (not pre-registered): combined OR flag** (any of the three fires) — train lift
×1.40 (33.8% vs. 24.1% base), **holdout 23.1% vs. 24.5% base — flat, no lift at all.** Consistent
with the individual features: whatever train-side signal exists does not survive the one holdout
look.

---

## 4. Verdict

**No feature tested this pass reliably separates hits from misses in the round-10+ universe, at
this sample size.** Say this plainly, per the founder's own explicit instruction that a negative
result here is the most valuable output available: it stops the project building a flag that
would confidently mislead him on draft day.

- **AGE_YOUNG is the one candidate worth carrying forward as a hypothesis, not a finding** — it
  is the only feature whose direction held in holdout, and it is independently evidenced at
  MODERATE-HIGH confidence on the *full* ADP board in the sibling analysis. What this pass adds:
  the effect is much less certain when narrowed to round-10+ specifically, purely because of
  sample size (47 train / 8 holdout flagged players is not enough to resolve a signal this size).
  **The honest next step is more data, not a different feature** — either more historical seasons
  as they accrue, or accepting the wider round-9+ population despite §1.2's argument against it
  and re-testing there for power, with that trade-off stated explicitly if it's tried.
- **EFFICIENT_LOW_VOLUME and RISING_SHARE do not show usable signal in this pass.** RISING_SHARE
  in particular inverted on its one holdout look — treat it as disconfirmed for this specific
  cutoff/threshold combination, not merely "not yet proven."
- **No flag from this pass should ship.** Nothing here clears the bar CLAUDE.md §6.3 and
  `docs/statistical-guardrails.md` §3 require before a factor earns a place in anything
  user-facing, pre-registered or not. This is a screening pass that came back clean, which is a
  legitimate and useful result (`docs/statistical-guardrails.md` §5) — not a failure to re-run
  until it looks better.
- **What this pass does license:** treating "young WR/TE outperform ADP, and are the leading
  candidate late-round flag hypothesis" as a pre-registered question for the ranker's next
  factor-testing pass, once more seasons of FFC ADP history exist to power a round-10+-specific
  test — not before.

---

## 5. FR-096 (bust-candidate screen, the mirror request) — not attempted this pass

The founder extended this request mid-session to the reverse question: bust candidates among
early-ADP players, same use case (avoid a bad pick when two players sit at similar VBD), read
before finishing here as **FR-096**
(`docs/founder-requests/FR-096-bust-candidate-flag-the-mirror-of-the-sleeper-sc.md`). Per the
coordinator's explicit sequencing instruction — finish the sleeper screen first, hand off the bust
screen rather than half-doing both — **this session did not build the bust screen.** A NEW-
handoff scoping it is opened below, distinct from the methodology-review handoff for this
document, so it can be picked up as a fresh, correctly-scoped piece of work rather than an
afterthought bolted onto this report.

Worth stating up front, since it bears directly on how that future session should be scoped: the
asymmetry the coordinator's message describes is real and already partially answered by data in
hand. The sibling ADP-vs-production analysis's round-conditional finding — early-round RB
underperforms same-round peers at every other position by roughly 3× (−54.1 VBD pts vs. −15.9 to
−18.9, rounds 1–3, train seasons, era-stable) — is a **positional** bust signal already measured.
Whatever a player-level bust screen finds needs to be compared against "just knowing RB is risky
early" as an explicit baseline, exactly as the coordinator's message specifies, or it will not be
possible to tell whether a player-level feature adds anything over the position-level fact
already in hand.

---

## 6. Reproducing this

```
python3 analysis/sleeper_screen.py
```

Requires a populated `data/nfl.db` with `ffc_adp_snapshots` (`adp_source='ffc_half_ppr_12team'`,
periods 2018–2024), `player_weekly_stats`, `player_ids`, and `players_canonical`. If a fresh
worktree's DB is a stub (0 bytes — the standing `docs/environment.md` §4 gotcha), rebuild:

```
python3 src/ingest_weekly_stats.py --db data/nfl.db
python3 src/ingest_reference.py --db data/nfl.db
python3 src/ingest_league_metrics.py --db data/nfl.db
python3 src/ingest_fantasypros_csv.py --db data/nfl.db
```
then, in Python, run `identity.build_identity_tables(conn)` (no `--db` flag exists for that
module — see `scripts/rebuild_database.py`'s own docstring) and
`ingest_ffc_adp.import_all_snapshot_csvs(conn, Path('data/adp-snapshots-ffc'))` to restore the
committed FFC ADP history CSVs. `ingest_rankings.py` (step 4 of the full rebuild) is not required
for this script and may 403 in a Claude Code cloud session against `dynastyprocess/data` — a
known, documented proxy restriction, not a bug in this script.

Output: console summary + `data/qa/sleeper-screen-2026-07-30.json` (full per-feature, per-season,
per-position tables).
