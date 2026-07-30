---
ID: 114
FROM: ranker
TO: data-ops
STATUS: OPEN
OPENED: 2026-07-30
BLOCKS: test-registry #28 (vacated targets & carries)
---

**No `ID:` field on purpose — allocate it with `tools/handoffs.py sync`, do not hand-type one
(collisions: threads 043, 049, 053; ADR-048).**

## Ask

Ingest `nflreadpy.load_rosters_weekly()` into `nfl.db`. Minimum viable shape:

```
rosters_weekly(season, week, team, gsis_id, status, position, game_type)
```

- `status` ∈ {ACT, **RES** (injured reserve), INA, PUP, DEV, CUT, **RSN/SUS** (suspended), RET} —
  `status` is the whole point; do not drop it.
- Free, no login, goes back to at least 2002. Same nflverse licensing as everything else already
  ingested (CC-BY, attribution).
- Please also land **week 0 / preseason rows if the feed carries them**, and keep whatever
  as-of/date column exists. See "what would make this strictly better" below.

Done looks like: row count and season range reported, `status` value counts by season, and a
one-line check that Michael Thomas 2021 shows `RES` rows (the `injuries` table has zero for him).

## Why — two independent consumers, one ingestion

**This is the second time this table has been asked for.** It was already commissioned by `ranker`
for the availability gap in `docs/ranking/component-model-rb-qb-te-pass-1.md` §5.2: the `injuries`
table accounts for only **2.5–4.8% of absences of nine games or more**, because season-ending IR
removes a player from the weekly report, and the depth chart marks an IR player as *off-roster*,
which is the opposite of the truth. `rosters_weekly` is the only source found that marks IR and
suspension.

**The new, separate reason:** `nfl.db` contains **no pre-season roster or team-membership table at
all.** Verified this session:

| candidate | why it does not work |
|---|---|
| `depth_charts_weekly` | earliest rows are REG **week 1**; no PRE game_type in the table (game types present: REG, WC, DIV, CON, SB, SBBYE) |
| `depth_charts_snapshots` | a single snapshot, `dt = 2026-03-14`, no season history |
| `rosters` | **does not exist** |
| `contracts` | not a per-season roster |

So "which players left this team between season N−1 and season N" is **unanswerable from stored data
at a legal cutoff**. Registry #28 (vacated targets and carries, tagged HIGH edge, never run) had to
run on a Week-1 depth-chart PROXY, declared in advance in
`docs/ranking/factor-batch-1-precommit.md` §3.3.

**The proxy's known leak then showed up exactly where predicted.** Results in
`docs/ranking/factor-batch-1-results.md` §4: the vacancy feature is harmful, and the harm is
concentrated entirely in the **high-measured-vacancy** bucket (RB +0.77 carries MAE, WR +0.30) —
which is the bucket a Week-1 injury inflates, because an injured player drops off the chart and is
counted as departed. The experiment therefore **cannot separate "vacated opportunity is
uninformative" from "our proxy for it is contaminated."** #28 is recorded as **BLOCKED, not NULL.**

## What would make this strictly better than the proxy

The proxy is dated at REG week 1 — roughly a week *after* a real draft, so it is later than
`CLAUDE.md` §6.1's "preseason N" bound and it can encode a Week-1 injury. A roster feed with
**preseason or week-0 rows, or any as-of date before Week 1**, removes both problems at once and
makes #28 answerable at a legal cutoff. If the feed carries only REG weeks, say so plainly in your
reply — that is itself the finding, and it means #28 stays blocked rather than becoming answerable.

## What I will do with it

Re-run registry #28 with a real departure definition, and re-run the availability arms from
`component-model-rb-qb-te-pass-1.md` §5 with IR and suspension visible. Both are already coded; the
only missing input is this table. Neither is expected to be large — §5.1 found no availability arm
improved the ranking at any position — but #28 currently has **no measurement at all**, and a HIGH-
edge registry item sitting on a proxy-confounded result is worse than one sitting on a clean null.
