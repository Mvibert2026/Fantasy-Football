---
ID: 084
FROM: ranker
TO: data-ops
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask

Establish, and if feasible acquire, **pre-season expert consensus ranking history for seasons
before 2021**, in the same shape as the existing `rankings` rows where
`source='fantasypros_ecr' AND is_preseason_final=1`.

Concretely:

1. **Feasibility first, acquisition second.** Report whether pre-2021 pre-season ECR (or any
   comparable stated-expert-opinion consensus — not ADP) is retrievable at all, per season,
   from FantasyPros archives, the DynastyProcess mirror, the Wayback Machine, or any other
   source. A per-season yes/no table with the URL pattern tried is a complete answer even if
   every row is "no".
2. If retrievable, land it into `rankings` with the existing columns
   (`source`, `season`, `player_id`, `position`, `adp_rank`, `as_of_date`,
   `is_preseason_final`, `scoring_format`) under a **new `source` value** — do not merge into
   `fantasypros_ecr`, which currently means "the 2021-2025 mirror" and is depended on by
   `src/make_board.py::collect_observations` (`TRAINING_SOURCE`).
3. `as_of_date` must be a real pre-season date per season, not a backfilled constant. If the
   archive cannot supply a date, quarantine the row rather than inventing one — the whole
   value of this pull is that it is pre-draft information.
4. **Do not fetch anything for season 2025** beyond what is already on file. 2025 is the
   sealed holdout (`src/holdout.py`).

**What I will do with it:** every "does our model beat the market" question in this project is
currently limited to **n=4 usable seasons** (2021-2024; 2025 sealed). At n=4 nothing can reach
significance and `docs/reviews/*` correctly labels every consensus comparison DESCRIPTIVE.
PR-004/PR-005 both had to route around this. With ~12-15 seasons the market-relative question
becomes answerable at the same standard as the naive-baseline question already is.

## Why

Measured this session (`docs/ranking/bottom-up-research-pass-1.md`): consensus ECR sits at
tau_b +0.48 to +0.50 at QB/RB/WR and +0.31 at TE, versus +0.23 to +0.43 for prior-season
points. Consensus is the only baseline that matters and we can measure it on four seasons.
Every other data gap in this project (coaching history, Vegas odds, route participation) is
now **measured as thin or bounded near zero** — this one is not, and it is the only gap that
binds the project's headline claim.

Cost note: this is a research/scrape task with real licensing questions (D-020 says no
FantasyPros licence is needed while the product stays private/founder-only; D-021 loosened
FFC harvesting on the same basis). Check terms **before** building, per CLAUDE.md §5. If the
answer is "not retrievable" or "not permissible", that is a complete and useful answer — I
will design around n=4 permanently rather than keep hoping.

## Done looks like

Either (a) a per-season retrievability table committed under `docs/research/`, with a plain
verdict, or (b) that table **plus** rows in `rankings` under a new `source` value, a row count
per season, and the ingester committed. Reply on this thread with the season coverage actually
achieved, not the attempt.
