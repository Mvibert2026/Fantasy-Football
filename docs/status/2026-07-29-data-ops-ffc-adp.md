# 2026-07-29 — data-ops — FFC ADP ingester (all three formats), wired into daily CI

## What this session did

1. **Verified the FFC-unblock authorisation independently**, rather than trusting the coordinator
   dispatch message alone: `docs/pm/MEMORY.md` §4 and
   `docs/founder-requests/FR-023-ffc-is-unblocked-founder-confirmed-no-restrictio.md` both confirm
   the founder contacted FFC directly and reported no restrictions. Re-fetched `robots.txt` myself
   and confirmed only `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`, `/adp/csv/`, `/draft/`,
   `/rate-my-team/results/`, `/rankings/custom/` are disallowed — the HTML ADP pages this ingester
   fetches are not on that list, and `/adp/csv/` is never touched.
2. **Built `src/ingest_ffc_adp.py`** — half-PPR 10-team initially, then extended to all three
   formats (non-PPR/half-PPR/PPR) mid-session at the founder's follow-up request. Each format is
   its own `adp_source` (`ffc_non_ppr_10team` / `ffc_half_ppr_10team` / `ffc_ppr_10team`), never
   blended with each other or with `mfl_proxy`.
3. **Found and fixed a same-day duplicate-row defect**: a second `store_adp()` call for the same
   day was appending rather than replacing. Added a `DELETE` scoped to
   `(adp_source, period, teams, format, as_of_date)` before insert, plus two regression tests.
4. **Rebuilt `data/nfl.db` locally** (`uv venv --python 3.12`, `scripts/rebuild_database.py`) to
   get `ff_playerids` for identity resolution — hit and resolved two environment issues along the
   way (a stale locked sqlite connection from an earlier failed run; the DB itself needed only
   `--only ff_playerids`, not a full rebuild, once the lock was cleared).
5. **Ran the real capture** for all three formats against the live site, once, and confirmed
   idempotency under repeated `--force` runs (no duplicate rows, no duplicate CSV lines).
6. **Wrote `tools/ci_ffc_adp_snapshot.py`** (mirrors `tools/ci_adp_snapshot.py`'s fail-loud
   posture) with an explicit, documented 80% name-resolution floor instead of MFL's 90% — FFC
   resolves by name against `ff_playerids`/`players_canonical`, which carries **zero** team-defense
   rows (verified by direct count), a structural ceiling below 100% rather than a join defect.
7. **Wired both MFL and all three FFC captures into `.github/workflows/adp-snapshot.yml`**,
   holding the existing bar: the run fails rather than commits an empty or degraded file, for any
   of the four snapshots.
8. **Mid-session false-alarm, documented for the record**: discovered two commits already on the
   branch with content matching my own uncommitted work almost exactly, and halted rather than
   resolving it myself (per CLAUDE.md's coordination discipline). The coordinator confirmed this
   was their own `git add -A` sweeping my in-progress files under their commit messages while I was
   still working — not a parallel agent. `git diff HEAD -- src/ingest_ffc_adp.py
   tests/test_ingest_ffc_adp.py` was empty, confirming byte-identical content; nothing was
   reconciled or discarded because there was nothing to reconcile.

## Evidence

**Rows captured (2026-07-29, live pull):**

| adp_source | stored | quarantined | match_rate | totalDrafts (sample) |
|---|---|---|---|---|
| `ffc_non_ppr_10team` | 171 | 17 | 91.0% | 628 |
| `ffc_half_ppr_10team` | 180 | 23 | 88.7% | 1,187 |
| `ffc_ppr_10team` | 213 | 29 | 88.0% | 3,673 |

**Quarantine reasons (union across formats, half-PPR shown as representative):** 19 of 23 are
`no_name_match` on team defenses ("Seattle Defense", "Denver Defense", ...) — `ff_playerids` has
zero DEF entries, confirmed by direct query. Remaining: `Marvin Harrison Jr.` (`ambiguous_name_match`
— normalize_name() strips the "Jr." suffix, colliding with the elder Marvin Harrison and a third WR
Harrison), `Kenny Gainwell`, `Eddy Piñeiro`, `Chig Okonkwo` (`no_name_match`, likely nickname/accent
mismatches against `ff_playerids`' canonical names — not investigated further, correctly quarantined
rather than fuzzy-matched).

**as_of_date:** `2026-07-29` for all three, `is_retrospective_aggregate=0` (genuine same-day
capture, not a backfill).

**Tests:** `tests/test_ingest_ffc_adp.py` — 18 new tests, all passing (parsing, identity
resolution + quarantine, never-blend across 3 formats, CSV export/import round-trip, same-day
overwrite-not-append, network-failure handling). `tests/test_holdout_audit.py` — added
`ingest_ffc_adp.py` to `CONNECT_ALLOWLIST` (ingestion module, same class as `ingest_mfl_adp.py`).
Full suite run this session: 655 passed, 8 skipped, 8 pre-existing failures unrelated to this work
(export_contract version/committed-artifact mismatches in files explicitly out of my boundary —
not investigated or touched, per task scope).

**Commit:** see `git log` for this session's commit hash (recorded at commit time below).

## Sources attempted and status

| Source | Status |
|---|---|
| FFC HTML ADP pages (`/adp/<format>/10-team/all/2026`) | **Captured**, 3 formats, daily via CI |
| FFC `/adp/csv/` | **Not touched** — robots-disallowed, never attempted |
| FFC historical seasons (`--period <year>`) | **Not pulled this session** — flagged in
  `docs/ideas-inbox.md`; would need `is_retrospective_aggregate=1` labelling per ADR-054, and a
  decision on whether a retrospective aggregate is worth capturing before it's built |

## Not done / explicitly out of scope this session

- Whether FFC ADP feeds `src/export_contract.py` / `src/make_board.py` / `src/availability.py` —
  not touched, per the task's explicit file boundary.
- FFC historical backfill.
- Model/ranking changes of any kind.
