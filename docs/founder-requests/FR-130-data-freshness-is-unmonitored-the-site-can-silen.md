---
ID: FR-130
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: data-ops, then backend
---

## Request

Founder's own words:

> "Yeah we will need to talk about data sources. I think you need to make sure you get most recent
> data available to the site for testing. That could be a silent killer."

Raised after learning the availability model runs on a ranking source four days older than the one
the board runs on.

## Why it matters

**He named a class of failure, and an audit found four instances of it in one pass.** Nothing on any
screen reports any of them. Measured 2026-07-30.

### 1 · Today's captured ADP is on disk and not in the database

A scheduled job committed `data/adp-snapshots/2026-07-30.csv` (236 rows) plus six FFC files this
morning. The database's latest `ffc_adp_snapshots` row is **2026-07-29**.

| | |
|---|---|
| Captured to disk | 2026-07-30 |
| Present in `nfl.db` | 2026-07-29 |

The capture half of the pipeline runs on a schedule. **The ingest half does not.** The gap widens by
one day, every day, and the only way to notice is to query the database by hand. This is the purest
form of what the founder called a silent killer: the automation looks like it is working, because the
part that is automated *is* working.

### 2 · Two live ranking sources, three days and 130 players apart, used by different subsystems

    fantasypros_csv_2026draft   n=538   as_of 2026-07-27   <- the board runs on this
    fantasypros_ecr             n=408   as_of 2026-07-24   <- availability runs on this

Both are current, neither is a stale leftover, and **73 of the 80 players in `availability.json` have
a different consensus rank between them** (measured during the FR-066 investigation). So the
availability model and the board disagree about what the market thinks, and no screen says so.

This is already blocking a shipped feature: browser-side availability recompute was prototyped, ran
in under 5 seconds, and **was not shipped** because the frontend has no honest source for the rank the
model actually uses. Thread 104 asks backend for that field and has sat open.

### 3 · Archetypes are computed from a four-day-old snapshot

`player_descriptions.json` was generated **2026-07-26**. Every other export regenerated **2026-07-30**.
So the archetype chip on the card describes a board that has since moved, and the 57.8%-unclassified
figure driving a live design decision (FR-123, and design's `PLAYER-PROFILE-AMENDMENT-ARCHETYPE.md`)
was measured on it.

### 4 · The board is sitting exactly on its own staleness limit

    snapshot_as_of_date:    2026-07-27
    snapshot_age_days:      3
    snapshot_max_age_days:  3
    snapshot_stale:         False

**Age equals the maximum.** One more day without a fresh rankings pull and `enforce_freshness` refuses
the build outright. That gate is good design and it is about to fire — as a hard stop rather than a
warning, because nothing escalates before the limit.

## Initial read

**The instances are worth fixing. The absence of monitoring is the actual request.** Each of these was
found by hand, today, because the founder happened to ask. That is not a process.

### Immediate — data-ops

1. **Ingest what is already on disk.** Today's ADP capture, and anything else the scheduled jobs wrote
   and nothing consumed. Then re-export.
2. **Pull fresh rankings** and rebuild, since the board is at its staleness limit.
3. **Regenerate `player_descriptions.json`** against the current board. Report whether the 57.8%
   unclassified figure moves — a live design decision rests on it, and if it shifts materially the
   amendment needs re-examining before item 2 is built.

### Standing — the part that stops it recurring

**A freshness check that fails loudly**, run as part of the export and surfaced in the app:

- Every dated source gets a maximum age and an owner. `board.json` already has this pattern
  (`snapshot_max_age_days` / `snapshot_stale` / `enforce_freshness`) and it works. **Extend it to
  every source rather than inventing a second mechanism** — rankings, ADP, player descriptions,
  availability.
- **Warn before the hard stop.** Age 3 of max 3 should have been visible before it became a refusal.
- **Capture without ingest is the failure mode to detect specifically.** A file on disk that is newer
  than the newest row in the table it feeds is a one-query check and would have caught instance 1
  the morning it happened.
- **Surface it in the app, not only in a log.** The top bar already renders an export timestamp and a
  `snapshot fresh (3d)` marker; that marker is telling the truth about the board and nothing about
  the other three sources.

### The one decision that needs a human

**Two live ranking sources is a choice nobody made.** Either the availability model should move to
`fantasypros_csv_2026draft` and match the board, or the split is deliberate and needs stating. It
cannot stay accidental — and it is currently producing a measurable disagreement inside the product's
most trusted output. Backend/strategist call, and it should be made before more work is built on
either source.
