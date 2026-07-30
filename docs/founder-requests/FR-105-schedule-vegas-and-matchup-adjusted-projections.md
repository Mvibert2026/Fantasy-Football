---
ID: FR-105
STATUS: NEW
PRIORITY: MEDIUM-HIGH (playoff-weeks half) / LOW (matchup-type half)
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Schedule, Vegas, and matchup-adjusted projections

Founder's own words:

> "have we taken into account schedule, like vegas defenses they play and their stats the prior year
> against those types of defenses etc."

## Current state — none of it is done, and one entry is an assertion rather than a measurement

| Item | Registry | State |
|---|---|---|
| Vegas win totals & implied team totals | #11 | **NEW** — never started. The `odds` data source is still "TBD"; no odds data is ingested anywhere. |
| Season-long strength of schedule | #12 | **SPEC** — never run. Prior recorded as "**~Zero**". |
| Player performance vs. defense *type* | — | **Not in the registry at all.** |

**The #12 entry deserves scrutiny.** Its note reads: *"SOS is largely non-actionable for drafts —
defenses shift year over year and the worst units get the most offseason investment. Weight near
zero. Retained only so we can say we checked."*

That reasoning is plausible and it is **still received wisdom, not a measurement.** `CLAUDE.md` §11
requires "everyone knows X" to be treated as a hypothesis to test. The entry states a conclusion
("~Zero") in the effort/edge column of a test that has never been run.

## Initial read — the request splits into three, with very different value

Not the founder's own words — PM's read.

### 1. Playoff-weeks schedule — the one worth doing, and it is league-specific

**Season-long SOS is probably near-zero for the reason the registry gives: it averages out over 17
games.** But this league has a **4-team playoff in weeks 16–17 with no reseeding** (`CLAUDE.md` §7).
The founder's season is decided in **two specific games**, and two games do not average out.

Weeks 16–17 opponent quality is knowable at draft time — the schedule is published — and it is a much
narrower, more defensible use of schedule data than a season-long average. This is the version of the
founder's question that is both cheap and directly actionable, and nobody has looked at it.

Caveat that must survive into any result: to *use* a playoff-weeks edge you must first make the
playoff, and §7 already notes a slow start is unusually costly here. A player who is great in weeks
16–17 and poor in weeks 1–13 may never get to help.

### 2. Vegas implied team totals — plausible, but unblocked work first

Implied team totals are a genuinely different signal from SOS: they price the *offence's* expected
environment rather than the schedule's difficulty, and the market updates them continuously. But
**no odds source is selected or ingested**, and the registry's own note says to benchmark candidate
sources for accuracy before committing to one. That is real work, not a lookup.

Prior worth stating: the insights backfill recovered a finding that the
**coach/coordinator/team-environment channel is near-zero — "do not fund the sourcing."** Implied team
totals are a team-environment signal. That is adjacent evidence for a low prior, though not the same
measurement.

### 3. "Their stats the prior year against those types of defenses" — the speculative one

This is the founder's most granular idea and the least likely to work, for three compounding reasons:

- **Defense typology needs charting data we largely lack.** Coverage shell and scheme come from the
  FTN subset inside nflverse, which is **2022+ only** — three seasons, and CC-BY-SA with attribution
  required.
- **The samples are tiny.** A receiver faces a given defensive type perhaps three or four times a
  season. A player × defense-type cell is a handful of games, which is noise.
- **Defenses do not persist.** Personnel and coordinators change, so "this defense was weak against
  slot receivers last year" is a claim about a unit that no longer exists — the same non-stationarity
  problem as §6.4, at team level.

Not worthless, but it should be last, and only if the cheaper two show anything.

## Recommended sequencing

1. **Playoff-weeks (16–17) schedule quality** — cheap, league-specific, never examined.
2. **Season-long SOS** — run it properly so "~Zero" becomes a measurement rather than an assertion.
   Cheap, and it closes an entry that currently states a conclusion it did not earn.
3. **Vegas implied totals** — only after a source is evaluated and licensing checked.
4. **Player × defense-type** — only if 1–3 show something.
