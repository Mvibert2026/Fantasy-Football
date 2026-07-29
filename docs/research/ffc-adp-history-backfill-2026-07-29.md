# FFC historical ADP backfill — 2026-07-29 (data-ops, thread 055)

Executes the plan researcher validated the same day
(`docs/research/historical-adp-availability-2026-07-29.md`). No new probing of the date-gate
question — that document's per-season table is trusted as-is and reproduced below with one
correction (§2).

## 1. What was fetched

`tools/backfill_ffc_adp_history.py`, one-time, cache-first (`data/raw/ffc/`), ≥1s between
requests, 19 season-formats attempted, **19 fetched successfully, 0 dropped for an unparseable
date**.

| Format | Team size | Seasons | Rows stored | Rows quarantined | Match rate range |
|---|---|---|---|---|---|
| Half-PPR (priority, per ranker's ask) | 12 | 2018–2024 (7) | 1,072 | 122 | 85.8%–92.7% |
| Non-PPR | 12 | 2013–2024, minus exclusions (12) | 1,395 | 211 | 65.1%–92.2% |
| **Total** | | **19 season-formats** | **2,467** | **333** | |

Per-season detail (`period`, rows stored):

- Non-PPR: 2013→28, 2014→27, 2015→52, 2016→58, 2017→94, 2018→126, 2019→137, 2020→175, 2021→185,
  2022→174, 2023→173, 2024→166.
- Half-PPR: 2018→127, 2019→138, 2020→162, 2021→187, 2022→114, 2023→180, 2024→164.

**Team count is 12, not the primary league's 10.** The archive silently serves the 12-team page
for any other requested size (verified independently again this session; not re-litigated).
`adp_source` values are new and separate from the daily 10-team capture:
`ffc_non_ppr_12team`, `ffc_half_ppr_12team` — never blended with `ffc_*_10team` or `mfl_proxy`.

**`as_of_date` is the parsed window END date** (e.g. `2024-09-01`), not the day this script ran.
`sample_window` (FFC's verbatim "Data from N drafts between DATE1 and DATE2" sentence) is kept
unchanged, per the ranker's explicit ask on thread 055 — without it the rows cannot be proven
pre-Week-1 for the season they claim to represent.

Quarantine detail: `data/qa/ffc-adp-history-quarantine-2026-07-29.csv`, 333 rows. All three
reasons are the pre-existing, documented ones (`tools/ci_ffc_adp_snapshot.py`'s docstring) —
`no_name_match` (299, almost entirely team defenses — `ff_playerids` carries no DEF entities at
all), and two small `ambiguous_name_match:{2,3}_candidates` buckets (15 + 19). **No fuzzy
matching was used anywhere in this run.** An unresolved or ambiguous name is quarantined with a
reason, never guessed.

## 2. Two findings that change the researcher's plan, both confirmed by direct fetch (not WebFetch)

### 2a. 2010 non-PPR passes the date gate but is content-corrupted — excluded

The researcher's date-gate table marks 2010 non-PPR **PASS** (window Sep 6–8, kickoff Sep 9).
That gate is correct as far as it goes, but the page itself is garbled: 25 rows, dominated by
DEF/QB/PK, missing every real 2010 RB1 (no Adrian Peterson, no Chris Johnson, no Arian Foster).
Reproduced today with a direct `urllib` GET — not the WebFetch markdown-conversion artifact the
researcher flagged as a `[GAP]` guess. This closes that gap: **it was not WebFetch dropping
rows; FFC's own archived page for 2010 is degenerate.** Plausibly the same root cause as the
2007–2009 "window ends June 20, 2010" migration artifact next to it. **2010 is excluded from
this backfill despite passing the date gate** — a third disposition (content-invalid), not
folded into the date-gate PASS/FAIL binary. `NON_PPR_CONTENT_INVALID` in the script.

### 2b. Pre-2018 non-PPR boards are real but thin — kept, reported, not dropped

2013 (28 rows stored / 43 parsed before quarantine), 2014 (27/39), 2015 (52/69), 2016 (58/70) are
far shallower than 2018+ (126–185). Spot-checked the top 12 picks of each for sanity (real skill
players in roughly ascending ADP order, unlike 2010's garble) — legitimate, just capturing fewer
mocked players than FFC's site attracted from 2018 onward. **Kept.** An honestly thin board with
a verified pre-draft date is still real signal; dropping it would be exactly the kind of
plausible-looking substitution CLAUDE.md forbids in the other direction. 2017 (94 rows) is the
approximate hinge point.

## 3. Seasons never fetched, and why (no network request spent)

| Season | Format | Reason |
|---|---|---|
| 2007, 2008, 2009 | non-PPR | Window ends 2010-06-20 — accumulated aggregate, not a preseason sample |
| 2011 | non-PPR | Window (Sep 7–9) ends **after** Week 1 kickoff (Sep 8) |
| 2012 | non-PPR | Window ends the same calendar day as kickoff — marginal, excluded conservatively |
| 2010 | non-PPR | Content-invalid, see §2a (date gate itself passes) |
| 2015, 2016, 2017 | half-PPR | No archive exists — FFC serves the empty default shell (0 rows) for these format-years |
| 2025 | both | No archive exists in any format — confirmed again this session, consistent with the researcher's finding |

## 4. Look-ahead gate — how it was computed, not assumed

Per-season Week 1 kickoff was pulled live from `nflreadpy.load_schedules(seasons=[N])`, `min`
gameday of `game_type == "REG"` rows, for every season 2010–2024. Every value matched the
researcher's `[SECONDARY]`, search-derived table exactly (e.g. 2018 → 2018-09-06, 2021 →
2021-09-09). This closes that document's outstanding "not from a primary schedule source" caveat
— the schedules source used here is the same nflverse feed the rest of the project already
treats as canonical, fetched live (not from a local `schedules` table — `nfl.db` does not carry
one; `src/export_contract.py` and `src/ingest_league_metrics.py` already call
`nfl.load_schedules()` the same way at build time).

## 5. What this unblocks

The ranker's pass-2 proxy (ECR rank standing in for draft position, n=4 seasons, TE calibration
n=18) can be re-run against real ADP for **7 half-PPR seasons (2018–2024)** and **12 non-PPR
seasons (2013–2024 minus exclusions)**. `never-blend` still applies: any comparison must keep
`ffc_half_ppr_12team` and `ffc_non_ppr_12team` as separate arms, and both are still a 12-team
archive being used as a proxy for a 10-team league — a scaling/rescaling step, not a like-for-like
match, exactly as the ranker anticipated in their reply.

## 6. Mock-draft-bias caveat, restated (not new, carried from the researcher's finding)

FFC ADP is drawn from self-selected mock drafters, not real-money leagues. This backfill does not
change that. Every `ffc_*_12team` row inherits the same caveat already attached to the daily
10-team capture and should never be treated as ground truth for how Westwood specifically drafts.
