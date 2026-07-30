---
ID: 108
FROM: researcher
TO: pm
STATUS: OPEN
BLOCKS: FR-097 (injury-prediction-service buy decision); raises priority of open item 8 (T6 roster-status ingest) and the Sleeper daily snapshot job
OPENED: 2026-07-30
---

## Recommendation: buy nothing. Cost avoided ~$100–190/year.

Full report: `docs/research/injury-prediction-services-2026-07-30.md`.

Three independent reasons, any one sufficient:

1. **Unmeasurable.** No retail injury service publishes dated, per-player, archivable pre-season
   predictions. Four of the six services surveyed emit tiers or narrative, which cannot be scored by
   anyone — including their own publishers. We could not audit last season's calls before buying, and
   could not audit next season's after.
2. **Wrong target.** The only service with numeric outputs *and* a documented validation (Draft
   Sharks, having acquired Sports Injury Predictor) validates on "misses at least two quarters of a
   game" — the **short**-absence event we already capture free. Its games-missed model reports
   **MAE 1.610 games** `[VERIFIED]` on an outcome where 64% of real absences cost ≤2 games
   `[VERIFIED]`. Its discrimination on 9+ game absences — the only thing we needed — is **never
   reported by anyone** `[GAP]`, and I did not estimate it.
3. **Unusable in the product.** `draftsharks.com`'s Terms of Use footer link is a dead `#`
   placeholder — **no terms document is reachable** `[VERIFIED]`. `CLAUDE.md` §5 requires checking
   terms before building against a source; we cannot. The app is publicly hosted. Best case this is a
   personal-use backtest input that could never be displayed — the thread-092 Sleeper fence again.

## The one honest counterweight, so this reads fairly

Draft Sharks is the only vendor that states its base rate (32%), benchmarks against a **positional**
average rather than a global one (the correct control — position alone moves per-game injury rate
2×, QB 2.5% to RB 5.2%), and uses preseason projections rather than realised usage (the right
look-ahead guard). Claimed lift: ROC-AUC **0.626 → 0.809** `[VERIFIED]`.

That figure is nonetheless: **one** holdout season (385 autocorrelated player-seasons, **2016**), on
a page last updated **2020-09-28**, vendor-self-reported, never independently replicated `[GAP]`, and
never revalidated publicly `[VERIFIED]` — the absence of revalidation is verified, not assumed. It
sits unremarkably inside the 0.57–0.95 AUC spread that Leckey et al. 2024 (BJSM) reports across a
literature it concludes is not ready for use. Bullock et al. 2022 (Sports Med, 204 models):
**98% high or unclear risk of bias; zero externally validated; "No models could be recommended for
use in practice."**

## Sample quality — this is an n of 1, not an n of 6

Six named services collapse to three units: Draft Sharks *is* SIP (acquisition); Footballguys /
Fantasy Points / PlayerProfiler are one unit for the falsifiability question (all tiers or prose);
Zone7 / Kitman / Zelus are one unit (B2B, wearable-fed, not retail). Effective n for "retail numeric
NFL injury model with a documented validation" = **1**. Read that as a thin market, not as six
sources agreeing.

## Two vendor figures explicitly marked unusable

- PlayerProfiler: "~50% of 80th–100th-percentile WRs missed at least two games" — **no denominator**.
- Zone7: "72.4%" is a **sensitivity** with base rate and false-positive rate both unstated; a
  flag-everyone policy scores 100% on it.

## What to do instead — no new work, just reprioritise

The gap is misdiagnosed as prediction. A player on IR in July is a **known fact**, not a forecast,
and he is precisely who the weekly-practice-report `injuries` table cannot see. Free and lawful to
fetch:

- **Sleeper `/v1/players/nfl`** — `status`, `injury_status`, `injury_start_date`,
  `practice_participation` `[VERIFIED]` from `docs.sleeper.com`, which explicitly invites a
  once-daily pull and instructs saving to our own servers. Redistribution still forbidden →
  personal-use fence, same as thread 092.
- **nflverse `load_rosters()`** status — already open item 8 (T6).

Both are already queued. This research adds no scope; it says spend the free effort, not the money,
and it raises the urgency because Sleeper has **zero history** — every un-snapshotted day is a
permanently lost row, and nflverse's own injury source died after 2024 with NFL.com `[BLOCKED]` by
ToS.

## Two things `pm` needs to action, which are not researcher calls

1. **`docs/founder-requests/FR-097-are-injury-prediction-services-accurate-enough-t.md` does not
   exist in this worktree.** Highest FR present is **FR-071**; `INDEX.md` says "56 requests since
   freeze". `docs/analysis/adp-vs-production-2026-07-30.md` (cited in the dispatch at line 199) does
   not exist either — `docs/analysis/` is absent. Nor is the `ranker` finding (26–35% short-absence
   capture, 2.5–4.8% for 9+ games) present in any doc here. Either this worktree is behind `main`, or
   FR-097 was never allocated. **I did not resolve it.** Every claim sourced to those files is tagged
   `[GAP]` in the report rather than reported as verified. If FR-097 genuinely does not exist, it
   needs allocating via `tools/founder_requests.py new` and this recommendation attaching to it.
2. **No thread ID or ADR number is allocated** — this session had no Bash tool, so
   `tools/handoffs.py new` could not be run. Filed as `NEW-`. Needs `tools/handoffs.py sync` to take
   an ID. Nothing is committed; the two files this session wrote need committing by whoever picks
   this up. Fourth researcher session on record to hit the no-Bash constraint.

## Trigger list — what would reopen this

1. A service publishes dated, downloadable per-player forecasts and leaves prior years up.
2. Anyone independently scores long-absence (≥9 games) discrimination against a stated base rate.
3. Draft Sharks revalidates on a post-2020 season with tail performance broken out.
4. A peer-reviewed, **externally validated** NFL injury model appears (current count across all
   sports: zero).
5. Multi-user launch — only bites if 1–4 already resolved favourably.
