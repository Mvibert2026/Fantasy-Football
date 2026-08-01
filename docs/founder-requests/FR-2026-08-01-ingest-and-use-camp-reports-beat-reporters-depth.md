---
ID: FR-2026-08-01-ingest-and-use-camp-reports-beat-reporters-depth
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Ingest and use camp reports, beat reporters, depth charts, coach quotes 24/7; injuries and depth_charts already in DB and read by no model

Founder's own words, chat 2026-08-01, immediately after being shown that assuming every player
plays a full season makes the model worse at all four positions:

> "I think we need to be pulling and including camp reports beat reporters, depth charts, coaches
> quotes etc. information is valuable. Given our set up it should be an advantage for us. We can run
> and search automated and include it 24/7."

## Why it matters

**It targets the one measured deficit.** Fable located v2's entire gap to consensus in the
projected-games channel. What consensus knows that we do not is *who is going to play* -- and its
sources are precisely the ones the founder names.

**The 24/7 argument is sound and is a real structural advantage.** No human analyst reads every beat
writer every day. An always-on ingest is something this setup can do that a person cannot.

## Initial read

**The finding that changes the sequencing: we already hold most of this, in structured historical
form, and no model reads any of it.** Verified 2026-08-01 -- the only consumers of these tables are
`src/ingest_reference.py`, `src/identity.py`, `src/team_codes.py`, i.e. ingestion and ID mapping.

| Table | Rows | Seasons | Notable |
|---|---|---|---|
| `injuries` | 79,816 | 2009-2024 | `report_status`, `report_primary_injury`, **`practice_primary_injury`**, `practice_secondary_injury` |
| `depth_charts_weekly` | 865,329 | 2001-2024 | `depth_team`, `formation`, `club_code`, `week` |
| `rosters_weekly` | 888,786 | 2002-2025 | `status`, `depth_chart_position` |

`injuries` carries **practice participation** -- DNP / Limited / Full. That is the single most
predictive public signal for whether a player suits up, and it is *what beat reporters are reporting
on*. We have held the primary source for 15 seasons and never opened it. Depth charts, which the
founder named explicitly, are present back to 2001.

**Two-phase sequencing, and the reason is validation, not appetite.**

1. **Structured first (dispatched to `ranker`, 2026-08-01).** Injury history, practice participation,
   depth-chart position, roster-status transitions -> a pre-season player-availability model.
   **Backtestable across 2009-2024**, which matters more than usual right now: batch C1 showed the
   registered WIN rule awards a win to pure noise on 9.6% of cells, so adding an *unvalidatable*
   input to the highest-leverage channel would be the worst possible timing.
2. **Unstructured news second (not dispatched).** Camp reports, beat writers, coach quotes.
   **Structurally not backtestable** -- historical beat-writer text is not retrievable at trustworthy
   `as_of` dates. Same wall as per-analyst rankings (FR-2026-08-01-bar-is-parity...): usable for the
   2026 draft, never validatable against 2018-2024.

**Two requirements for the news layer when it is built, both non-negotiable:**

- **Timestamp at capture.** Capture date is the only honest `as_of`. A story's entire value is in
  *when we knew it*; a scraped archive that restates or re-dates produces exactly the outcome
  contamination strategist flagged on week-1 roster status (C1 in the G2a conditions thread).
- **Report it as a 2026-forward signal, never as validated.** The signal begins accruing the day it
  is switched on. Any later write-up that reports it alongside backtested factors without that
  caveat is misreporting it.

**Corollary worth acting on separately:** the news layer's value compounds with time running, so the
capture should start *early* even before the model consumes it -- the archive cannot be built
retroactively. That is an argument for standing up capture soon and modelling later, the opposite of
the usual order.

**Note on terms:** the founder ruled 2026-08-01 (`CLAUDE.md` §5) that terms review is his concern,
not an agent gate. That ruling applies here.
