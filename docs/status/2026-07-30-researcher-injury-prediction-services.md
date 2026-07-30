# 2026-07-30 — researcher — injury-prediction services: buy nothing

**Task:** answer the founder's question, relayed as FR-097 — *"how accurate are the injury sites at
predicting injuries, is that worthwhile?"* Deliverable framed as a buy decision with a cost.

**Verdict: buy nothing.** ~$100–190/year avoided. Three independent reasons in
`docs/research/injury-prediction-services-2026-07-30.md`; handoff staged unallocated at
`docs/handoffs/NEW-injury-prediction-services-buy-nothing.md`.

## What was actually established

- **Falsifiability is the decisive column, and five of six services fail it.** Four emit tiers or
  narrative; one 404'd. Only Draft Sharks (which acquired Sports Injury Predictor) emits per-player
  numbers, and those are paywalled with no as-of stamp and no public archive of prior seasons'
  predictions. Nobody outside the vendor can score any of them, before or after purchase.
- **The one documented validation targets the wrong event.** Draft Sharks classifies "misses at
  least two quarters of a game" — the short-absence category our own data already sees. ROC-AUC
  0.626 → 0.809 and R² 0.026 → 0.401, MAE 1.610 games, tested on **385 player-seasons from 2016**,
  reported on a page last updated **2020-09-28**, never revalidated, never independently replicated.
- **Tail performance on 9+ game absences — the only thing we needed — is `[GAP]` from every source.**
  Not estimated.
- **Effective sample is n=1, not n=6.** Draft Sharks *is* SIP; three editorial products are one
  methodological unit; three B2B platforms are another.
- **Peer-reviewed backdrop:** Bullock 2022 (Sports Med, 204 models) — 98% high/unclear risk of bias,
  **zero externally validated**, "No models could be recommended for use in practice." Leckey 2024
  (BJSM) — AUC 0.57–0.95, a third in the poor band, clinical utility questioned.
- **Base rates recovered so no accuracy figure floats free:** 38% of 1,794 NFL players missed ≥1 game
  (2015); 64% of absences cost ≤2 games; per-game injury rate 2.5% (QB) to 5.2% (RB). Two vendor
  figures (PlayerProfiler 50%, Zone7 72.4%) marked **unusable** for lacking denominators.
- **Licensing blocks it regardless:** `draftsharks.com`'s Terms of Use footer link is a dead `#`
  placeholder — no terms document reachable. `CLAUDE.md` §5 cannot be satisfied, and the app is
  public.

## What this argues for instead — no new scope

The gap is *current status*, not *forecast*. Sleeper `/v1/players/nfl` (`status`, `injury_status`,
`injury_start_date`, `practice_participation`; once-daily pull explicitly invited) plus open item 8's
`load_rosters()` ingest close the IR-invisibility hole for free. Both already queued; this raises
their priority. Sleeper has zero history — every un-snapshotted day is permanently lost.

## Constraints and unresolved items

- **No Bash tool.** No allocator access (handoff filed as `NEW-`, no ID hand-typed per ADR-048), no
  `tools/founder_requests.py`, no commit, and **no `nfl.db` query** — so our own fantasy-relevant
  injury base rate, the most useful number available, was not computed. Fourth researcher session on
  record to hit this.
- **`tools/status_log.py sync` could not be run**, so `docs/status/INDEX.md` is stale until someone
  with a shell regenerates it.
- **Escalated, not resolved:** `docs/founder-requests/FR-097-*.md` and
  `docs/analysis/adp-vs-production-2026-07-30.md` — both named in the dispatch — **do not exist in
  this worktree** (highest FR present is FR-071; `docs/analysis/` is absent). Either this worktree is
  behind `main` or FR-097 was never allocated. Claims sourced to those files are tagged `[GAP]`.
- `docs/CURRENT-STATE.md` not edited — this work closes an option rather than changing build state,
  and the reprioritisation is carried in the handoff to `pm`.
