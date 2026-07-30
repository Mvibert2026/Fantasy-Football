---
ID: FR-093
STATUS: SHIPPED
SOURCE: PM dispatch, data-ops session 2026-07-30
RAISED: 2026-07-30
---

## Request
Founder's words (relayed via PM dispatch, not verbatim chat capture): "Let's get the rest of teh
Historical ADP - FFC probaby has different formats and settings."

## Why it matters

`docs/analysis/adp-vs-production-2026-07-30.md` had to run entirely on FFC's 12-team mock-draft
archive because no 10-team historical ADP exists anywhere in the project, while the founder's
real leagues are 10-team. FFC's archive turns out to be 12-team-only for every historical season
(10/14-team URLs silently serve the 12-team page — verified in
`docs/research/historical-adp-availability-2026-07-29.md`), so 10-team history is not obtainable
from this source at all; what remained genuinely missing was the third FFC scoring format (PPR),
already backfilled for non-PPR and half-PPR in thread 055.

## Resolution (2026-07-30, data-ops)

Extended `tools/backfill_ffc_adp_history.py` with a `ppr` format key, reusing the season-level
look-ahead gate already built for non-PPR/half-PPR (kickoff dates are format-independent) plus an
independently re-verified content-validity check (PPR 2010 reproduces the same garbled-migration
artifact as non-PPR 2010: 26 rows, DEF/QB-heavy, missing every real RB1 — excluded on the same
basis; 2013 spot-checked sane).

**1,370 rows stored, 204 quarantined (mostly team-defense `no_name_match`, the same structural
ceiling documented in ADR-054), across 12 seasons (2013–2024), new `adp_source =
ffc_ppr_12team`.** Excluded, never fetched: 2007–2009 (window ends mid-2010, migration artifact),
2011 (window ends after kickoff), 2012 (window ends same day as kickoff), 2010 (content-invalid).

**Coverage now, all three FFC formats, all 12-team:**

| Format | Seasons | Rows |
|---|---|---|
| non-PPR | 2013–2024 (13, incl. 2010) | 1,395 |
| half-PPR | 2018–2024 | 1,072 |
| PPR | 2013–2024 | 1,370 |

**No 10-team or 14-team historical archive exists at any source found this session or the prior
one** — this is a structural FFC limitation, not a gap left unaddressed. The daily 10-team capture
(today forward only) is unaffected and continues under `ffc_*_10team`.

Quarantine detail: `data/qa/ffc-adp-history-quarantine-ppr-2026-07-30.csv` (204 rows). New tests:
`tests/test_backfill_ffc_adp_history.py` (12 passed, up from 10). Full writeup:
`docs/status/2026-07-30-data-ops-adp-and-coordinators.md`.
