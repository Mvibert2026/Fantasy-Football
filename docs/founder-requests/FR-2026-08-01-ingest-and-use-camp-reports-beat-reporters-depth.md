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

## Addendum, same day -- the news pipeline is shared infrastructure, not a ranking feature

Founder, on being told the news layer would be sequenced second:

> "Also why our news feed and player tagged news is important. We need the backbone for it for
> rankings anyway. Everything we need for rankings will drive lots of other features."

**This changes the scoping, and he is right.** PM had framed player-tagged news as an *input to the
ranking model*, to be justified by whether it improves rank correlation. That framing
under-values it and would get it built wrong -- narrowly, as a feature column, rather than as a
pipeline.

**The piece every consumer needs is the same piece: news reliably resolved to a `player_id`.** That
entity-resolution layer is the hard part and the reusable part. Once it exists:

| Consumer | What it uses |
|---|---|
| Ranking / availability model | Injury and status signal, dated at capture |
| Draft room | "News since you last looked" on the board and on the pick recommendation |
| In-season management (Phase 3) | Start/sit, waiver, and injury alerts -- the whole surface |
| The in-app assistant | "Why is this player ranked here" answered with current evidence |
| Deviation diagnostic (`FR-2026-08-01-respectability-check...`) | The *reason* attached to a large consensus disagreement |

**Consequence for sequencing.** The two-phase order in the Initial read stands for *modelling* --
structured injury/practice data is backtestable and news is not -- but it should **not** gate
*capture*. Two independent arguments:

1. **The archive cannot be built retroactively.** Value compounds with running time; every day not
   captured is permanently missing. Capture should start well before any model consumes it -- the
   reverse of the usual build order.
2. **Its justification does not rest on the ranking result.** If a news arm returns NULL against v2,
   the pipeline is still required by four other consumers. So a null must not be read as "the news
   pipeline was not worth building" -- a mistake this project is currently primed to make, having
   just spent a campaign reading nulls as verdicts.

**Still non-negotiable when built:** timestamp at capture (capture date is the only honest `as_of`),
and report any news-derived model signal as **2026-forward and unvalidated**, never alongside
backtested factors without that caveat.

**Not dispatched.** Scoping note only -- the founder has not asked for it to be built yet, and
`ranker` is on the structured availability model first.
