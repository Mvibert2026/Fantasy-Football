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

**Consequence for sequencing — SUPERSEDED by the founder's ruling below. Retained so the reasoning
is visible, but do not act on it.** PM argued that the two-phase order should govern *modelling*
only and should not gate *capture*, on two grounds: (1) the archive cannot be built retroactively, so
every uncaptured day is permanently missing; (2) the pipeline's justification does not rest on the
ranking result, since four other consumers need it regardless — so a NULL against v2 must not be read
as "not worth building."

### FOUNDER'S RULING, 2026-08-01 — exhaust the measurable first

> "We should do as much modeling without news as possible. It's harder to measure and a bit more
> discretionary. Once we've exhausted that we'll bring in the news."

**This governs. News work — capture and modelling both — is deferred until the measurable programme
is exhausted.** His reasoning is on the merits, not on cost: news is harder to measure and more
discretionary, and mixing a weakly-measurable input into a model whose grading rule has just been
shown to award wins to pure noise (batch C1) would make everything downstream harder to trust.

**"Exhausted" needs a definition or it becomes arguable later. Proposed, pending his correction:**

1. All ~95 `docs/factor-ledger.md` candidates dispositioned **against v2** — not against the old
   consensus-derived board. **6 of 95 as of 2026-08-01** (batch C1).
2. Threshold / breakpoint tests run as a class (batch C2, dispatched 2026-08-01).
3. The discovery pass complete and its candidates confirmed or dropped
   (`docs/ranking/discovery-pass-1.md`, dispatched 2026-08-01).
4. The structured availability model built and measured — injuries, practice participation, depth
   charts (dispatched to `ranker` 2026-08-01). **This is the news-adjacent signal in backtestable
   form and it is explicitly inside the measurable programme, not deferred with news.**
5. A valid inclusion decision rule in place (blocked on `strategist`; the registered one awards a WIN
   to pure noise on 9.6% of cells).

**The one fact that does not go away and should be re-raised when this comes back, not now:** the
archive is not retroactively buildable, so the cost of deferring capture is a permanently missing
window, not a delay. The founder has heard this argument and ruled; it is recorded here rather than
repeated at him.

**Still non-negotiable when built:** timestamp at capture (capture date is the only honest `as_of`),
and report any news-derived model signal as **2026-forward and unvalidated**, never alongside
backtested factors without that caveat.

**Not dispatched.** Scoping note only -- the founder has not asked for it to be built yet, and
`ranker` is on the structured availability model first.
