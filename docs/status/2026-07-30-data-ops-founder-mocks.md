# 2026-07-30 — data-ops — founder mocks ingestion + scoring-format inference

Ingested two founder-pasted Yahoo mock drafts (10-team/slot4, 12-team/slot2, 15 rounds each) into
the existing `mock_drafts`/`mock_picks` pipeline (`src/ingest_mock_drafts.py`), no new schema or
parallel ingestion path. Converted TSV -> the same JSON shape `founder-mock-2026-07-29.json`
already uses. Snake order verified programmatically per round (round1 manager order -> slot map,
every even round asserted as the exact reverse) before trusting any `overall_pick`/`team_slot`.

**Rows:** 330 picks attempted, 291 resolved, 39 quarantined (team defenses, a kicker, and a
handful of genuinely ambiguous or unresolved player names — none guessed). Both mocks fail
`format_conforms()` (kicker present, 1 flex not 2, 12-team also fails on team count) — flagged
plainly, not resolved by assumption, matching the founder's "same as the first" claim being
inconsistent with what the files actually show.

**Scoring-format inference (Task 2):** Spearman rank correlation of realized pick order vs. FFC
ADP at matching team count, all three formats for 10-team (0.933 standard / 0.949 half-PPR / 0.954
PPR, current 2026-07-29 snapshots) and two for 12-team (0.559 standard / 0.571 half-PPR, but no
`ffc_ppr_12team` source exists and the freshest 12-team snapshot on file is 2024-09-01, not
current). Direction matches the founder's half-PPR-or-fuller guess but the 10-team gap between
half-PPR and PPR is too close to call without a formal separability test — outside this role's
remit, handed to `strategist` (`docs/handoffs/112-founder-mock-scoring-format-inference-needs-sepa.md`)
along with the stale-12-team-ADP question and a TE-early anomaly (Bowers/McBride both drafted
earlier than even full-PPR FFC ADP predicts).

**Admissibility (Task 4):** λ/opponent-noise — probably usable with a caveat about roster-shape
transfer. ADP proxy — no, a mock is not ADP, `is_mock=1`/`format_conforms=0` already mark this.
Positional-run behavior — yes, this is the real unblock: per-pick sequence data for
`live_availability.py`'s run-detection term now exists across 3 drafts / ~480 picks instead of 1
draft / 150 picks, though the roster-shape mismatch (Task 3) still caveats any run measured in a
kicker/1-flex draft against Westwood's no-kicker/2-flex shape.

Full writeup: `docs/analysis/founder-mocks-2026-07-30.md`.

## Evidence

- Rows ingested: 291 resolved / 330 attempted, 39 quarantined (reasons in analysis doc).
- Sources attempted: FFC ADP (`ffc_adp_snapshots`, already in DB, read-only this session) — no
  new scrape attempted, none needed.
- Tests: `tests/test_ingest_mock_drafts.py` 21 passed, plus
  `tests/test_mock_lab_store.py`/`tests/test_mock_validation_report.py` 61 passed total (no test
  file changed — existing suite already covers the ingestion path these mocks went through).
- Files: `data/mock-drafts/yahoo-10team-slot4-2026-07-30.{tsv,json}`,
  `data/mock-drafts/yahoo-12team-slot2-2026-07-30.{tsv,json}`,
  `docs/analysis/founder-mocks-2026-07-30.md`,
  `docs/handoffs/112-founder-mock-scoring-format-inference-needs-sepa.md`.
- `data/nfl.db` copied from the main checkout into this worktree per `docs/environment.md` §4
  (gitignored, not committed).
