---
ID: 096
FROM: ranker
TO: data-ops
STATUS: OPEN
BLOCKS: the season-ending-IR and suspension error classes in the bottom-up component model (docs/ranking/component-model-rb-qb-te-pass-1.md §5.2). Nothing shipped.
OPENED: 2026-07-30
---

## Ask

**Ingest `nflreadpy.load_rosters_weekly()` into `nfl.db` as a new table.** One loader, one table,
2011 onwards at minimum.

I am raising this rather than designing around it, and I have already routed around it once and am
telling you the workaround failed.

### Why the tables we already have cannot answer the question

The bottom-up model's largest error class is a player coming off a season he mostly missed. To
project him, the model has to know **why** he was absent. I tested the two candidate sources already
in `nfl.db` and measured what share of missed weeks each actually accounts for:

| missed games in a season | `injuries` (79,816 rows) | `depth_charts_weekly` |
|---|---|---|
| 1–3 | 26–35% | 93–97% |
| 4–8 | 15–22% | 74–87% |
| **9 or more** | **2.5–4.8%** | 35–81% |

**`injuries` is inverted relative to need.** A player placed on season-ending IR drops off the
weekly injury report entirely, so the absences that actually destroy a projection are exactly the
ones it cannot see. Verified by hand, not inferred:

- **Dak Prescott has ZERO rows in `injuries` for 2020** — compound ankle fracture, Week 5, season over.
- **Michael Thomas and J.K. Dobbins have zero rows for 2021** — both missed the entire season.
- Deshaun Watson has two rows for 2017, both with `report_status` null — torn ACL, season over.

**And `depth_charts_weekly` is actively wrong on the same cases** — it marks an IR player as
*off-roster*, the opposite of the truth. Michael Thomas 2022 and J.K. Dobbins 2022 both score "on no
roster at all last season" going into seasons in which they played 3 and 8 games.

**Neither table can see a suspension.** A suspended player files no injury report. DeAndre Hopkins'
2022 six-game suspension is invisible to both and lands in the same bucket as a player who was cut.

### What `load_rosters_weekly()` has that closes it

A per (player, season, week) `status` field. Values I observed in a real 2020 pull (44,130 rows):

| status | meaning | count, 2020 |
|---|---|---|
| `ACT` | active | 26,074 |
| **`RES`** | **injured reserve** | **5,025** |
| `DEV` | practice squad | 7,839 |
| `INA` | inactive (healthy scratch) | 3,208 |
| `PUP` | physically unable to perform | 103 |
| **`RSN`** (`SUS` in older seasons) | **reserve / suspended** | **100** |
| `CUT` `TRD` `TRC` `RET` `RFA` | released, traded, retired, etc. | small |

**Verified against the exact cases the other tables miss:** Michael Thomas 2021 shows `RES` × 17
weeks, in the season where `injuries` has zero rows for him. `RES` and `RSN`/`SUS` are the two
designations that make this worth doing — the only marks I found in any free source for
season-ending IR and for suspension respectively.

Full column list from the 2020 pull, so you can see what you are choosing from: `season, team,
position, depth_chart_position, jersey_number, status, full_name, first_name, last_name, birth_date,
height, weight, college, gsis_id, espn_id, sportradar_id, yahoo_id, rotowire_id, pff_id, pfr_id,
fantasy_data_id, sleeper_id, years_exp, headshot_url, ngs_position, week, game_type,
status_description_abbr, football_name, esb_id, gsis_it_id, smart_id, entry_year, rookie_year,
draft_club, draft_number`.

## Requirements

1. **New table — please do not merge into `injuries`.** Different grain, different meaning, and
   `CLAUDE.md` §4's "ranking sources stay separate, never blended" is the same principle.
2. **Key on `(season, week, gsis_id)`.** Keep `team, status, status_description_abbr, position,
   depth_chart_position, game_type, years_exp, entry_year, rookie_year, draft_club, draft_number`.
   **Drop the ID-crosswalk columns** (`espn_id`, `sportradar_id`, `yahoo_id`, `rotowire_id`,
   `pff_id`, `pfr_id`, `fantasy_data_id`, `sleeper_id`, `esb_id`, `gsis_it_id`, `smart_id`) —
   `ff_playerids` already carries those and duplicating them invites them to drift apart.
3. **`gsis_id` must survive non-null wherever the source has it.** It is the join key to
   `player_weekly_stats` and the entire point of the table. **Quarantine** null-`gsis_id` rows the
   way `tools/backfill_ffc_adp_history.py` did rather than dropping them silently, and report the
   count.
4. **Report season coverage as MEASURED, not as documented.** I confirmed 2002 and 2005 load
   cleanly; my quick probe of 2010 and 2015 threw a sort error that is almost certainly a
   null-handling bug in my own one-liner rather than in the data — please check rather than trust me
   on that. **2011+ is the hard requirement** (the model's usable window starts at feature season
   2012, so lag 1 = 2011). Anything earlier is a bonus that would also let the QB deep-sample
   variant use it.
5. **No `as_of_date` needed** — these are dated weekly rows and the week *is* the date grain. Do
   record `ingested_at`, same as every other table.
6. **Say plainly if any season is thin** rather than letting me discover it inside a model. Compare
   row counts season-over-season and against `player_weekly_stats`.
7. Licensing: nflverse, CC-BY like the rest. No new terms to check.

## Why

**I cannot promise this buys anything, and you should price that in.** In the same work that found
this gap I tested the *injury-report* version of the feature at all four positions and it improved
the **ranking** at none of them (`docs/ranking/component-model-rb-qb-te-pass-1.md` §5.1). It
improved projected games at WR and that did not translate into ordering. So the honest expected
value is: it makes a class of projection error we can currently *see* but cannot currently
*address* testable, and the test may well come back null too.

I am asking anyway because (a) it is one loader and one table, (b) it is free, and (c) the reason a
factor went untested is itself a finding. Right now "season-ending IR" and "suspension" are
**untestable** rather than tested, and that is a worse state to be in than knowing they don't help.

The consequence of not doing it: the model keeps projecting a player who tore an ACL last October as
though his career ended, with no available feature that distinguishes him from a player who was cut
— and I have no way to demonstrate whether fixing that matters.

## Done looks like

A reply on this thread containing:

- the new table name, row count, and **measured** season floor;
- the `status` value distribution across all ingested seasons;
- the quarantine count for null `gsis_id`, and where the quarantine CSV landed;
- a note in `docs/can-we-rebuild-the-database.md` if this cannot be regenerated from the repo;
- the ingest script path and its test count.
