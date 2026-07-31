# 2026-07-30 — librarian — factor ledger + assistant-context projection

**Task:** `FR-2026-07-30-deliverable-a-ledger-of-every-factor-considered` (build the factor ledger),
extended mid-task by `FR-2026-07-30-assistant-access-to-factor-tests` (curate a projection into
`docs/assistant-context.md`).

## What was built

- **`docs/factor-ledger.md`** — 92 rows, every factor found stated as considered in a repo document
  this session. Not padded to the founder's suggested 100+. Disposition split: included 9,
  excluded 9, untested 49, blocked 17, rejected-with-evidence 8. Sourced from `test-registry.md`
  Tiers 0/1/2/5, `docs/research/analyst-factor-sweep-2026-07-30.md` (N1–N34 + 8 definition-only),
  `docs/ranking/factor-batch-1-results.md`, `experiments/bottomup/components/pos_features.py`,
  `docs/ranking/fr136-q1-bottom-up-assessment.md`, and `CLAUDE.md` §7. Both named scope traps
  (registry #13 — stability vs. target share itself; #28 — proxy artifact vs. a vacated-opportunity
  verdict) are stated explicitly at the top of the document and again at each affected row.
- **Four registry corrections applied to `docs/test-registry.md`**, all cited to the analyst sweep,
  none changing a result or edge rating: #18 xFP re-costed H → L (`load_ff_opportunity()` is
  prebuilt); #16/#17 re-tagged `nflverse:FTN` → `load_participation()` (FTN has no per-player
  columns; correct source gives 2016+, ten seasons not four — the wrong tag was suppressing both
  tests); #23 O-line re-tagged `external` → `derived`/`nflverse` (Adjusted Line Yards is a public
  PBP formula, `load_pfr_advstats()` ships free, no PFR scrape/403 risk).
- **`docs/assistant-context.md`**, "Factor test results" section replaced (11 entries, in place,
  current-state only). Each entry carries the number and its interval (never a verdict word alone),
  the effective n (season count, not cell count), and the exact scope of the question tested. Fixes
  the specific failure the coordinator flagged same-day: the assistant had called PR-003's −115.4
  QB-early point estimate a "worst case" (the interval is [−176.3, −54.4]) and described 4 seasons
  × 3 parameter settings as "12 scenarios" (effective n is 4). Both corrected in the new entry.

## Commits

- `d7709b1` — Tier 0/1 rows
- `7e3d67a` — Tier 2/5 rows
- `37503ab` — analyst-sweep rows + bonus-variance row + four registry corrections
- `0defb4d` — assistant-context.md curated projection

## Gaps flagged, not resolved

- **T1-25 (draft capital, rookies):** `fr136-q1-bottom-up-assessment.md` §3.3 calls draft capital
  "eliminated as an edge channel" per a "mandate," but the underlying quantified evidence for that
  elimination was not located in any file read this session. Logged in the ledger as `[GAP]` rather
  than asserted as verified — a `strategist`/`ranker` thread should locate or produce that evidence
  if the claim is going to keep being repeated.

No new handoff thread opened — the one gap above is a citation-tracing note, not a blocking
decision, and is visible in the ledger row itself (T1-25).
