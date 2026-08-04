# TO: data-ops
# FROM: ranker
# STATUS: OPEN
# SUBJECT: player_weekly_stats targets are ZERO for 2003-2008 - six seasons of receiver usage history turn on whether this is our ingest or upstream

## The measurement

`SUM(targets)` per REG season over `position IN ('QB','RB','WR','TE','FB')`:

| 1999 | 2000 | 2001 | 2002 | **2003** | **2004** | **2005** | **2006** | **2007** | **2008** | 2009 | 2010 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 16,087 | 15,715 | 15,731 | 16,814 | **3** | **5** | **0** | **67** | **14** | **17** | 16,776 | 17,013 |

Not sparse. **Zero.** Receptions, carries, attempts and all yardage columns are complete and
plausible across the same seasons, so this is one column (plus `receiving_air_yards`, which is
near-zero 1999-2008 and real from 2009 - that one is a genuine upstream start date, not a hole).

Corroborated independently inside our own DB: `league_season_metrics.wr_target_top45_share` is
**NULL for exactly 2003-2008** and populated for every other season 1999-2025. Two different
ingest paths agree on the same six seasons, which is what you would expect either from one shared
upstream gap or from one shared ingest bug.

## Why it matters now, and it is not a small thing

The founder pushed back on 2026-08-01 on the model's seven-season window, correctly: the core stat
lines run 1999-2025 with no gaps, so `first_feature_season` can be **2002** and `first_target`
**2004** - twenty-one target seasons against the current seven. Full measurement:
`docs/ranking/season-span-M4.md` §1, `experiments/bottomup/results/span_feasibility.csv`.

**This hole is the one thing that stops receivers coming along for the ride.** With `N_LAGS = 3`, a
target-derived feature (target share, catch rate, aDOT, WOPR) supports feature seasons
**{2002, 2003}** and **{2012 onward}** and nothing in between, because any 3-lag window from 2004
to 2011 straddles the gap. QB and RB are unaffected - their volume channels are attempts and
carries. So the span extension is currently a QB/RB extension only, and WR/TE stay at seven
seasons for the features that matter most to them.

**Six seasons is not a rounding error at S = 7.** Strategist's own note: at S = 7 an exact
season-level randomisation test cannot reach a BH threshold by any method; at S = 12 it can.

## The ask, in order

1. **Establish whether the gap is ours or upstream.** Pull `nflreadpy` / `nfl_data_py` weekly
   player stats for 2005 directly and check whether `targets` is populated at source. That single
   check decides everything downstream and should take minutes.
2. **If it is ours** - a column-mapping or schema change in that era's upstream files - backfill
   `player_weekly_stats.targets` for 2003-2008 and say what the fix was.
3. **If it is upstream** - say so plainly and close this. It then becomes a permanent, documented
   boundary rather than a suspected defect, and `docs/ranking/season-span-M4.md` §1.2 should be
   updated to record it as such. A documented boundary is a fine outcome; an undiagnosed one is not.
4. **Either way, check `receiving_air_yards` for 1999-2002 while you are in there.** It sums to
   7,500-10,800 per season there against ~140,000 from 2009 - about 5%. That looks like partial
   charting rather than full coverage, and anything built on pre-2009 air yards would be reading a
   biased sample. I have assumed it is unusable before 2009 and would like that confirmed or denied.

## What I did NOT do

I did not design around it, proxy it, or quietly restrict the span to hide it. The receiver curve in
`season-span-M4.md` §3 is reported with the confound named **in advance of the numbers**, so that a
decline at deep spans for WR/TE is read as a data defect and not as evidence that older seasons are
misleading. If this gets fixed, that measurement should be re-run.

Nothing here touches the sealed 2025 holdout.
