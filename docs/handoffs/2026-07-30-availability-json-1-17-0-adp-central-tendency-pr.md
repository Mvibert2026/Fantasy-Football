---
ID: 2026-07-30-availability-json-1-17-0-adp-central-tendency-pr
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

No action required to unblock anything else in progress. This is the notification thread 104 and
this project's own rule ("contract schema change -> bump the version AND open a handoff thread to
frontend") both require. `CONTRACT_VERSION` moved **1.16.0 -> 1.17.0**, additive only, no removals.

### What changed in `availability.json`

`client_simulation_parameters` gains one new block, `adp_central_tendency`, and
`player_ranks`/`ranking_sources` (already shipped for thread 104) are unchanged in shape, only
`ranking_sources[0]` now also carries `as_of_date`.

**Important, read before building anything against this:** thread 119 (strategist) resolved
*while this was being built* and reformulated thread 104's original ask. Short version --
**`adp_central_tendency` is NOT yet usable for a real browser-side recompute.** It is exported
now, ahead of the model actually switching to it, so you are not blocked a second time once it
does. Two things are still missing on the backend/statistician side, named below.

```
client_simulation_parameters: {
  ranking_sources: [{ name, weight, as_of_date }],   // unchanged shape, as_of_date added
  player_ranks: { <player_name>: <float> },           // unchanged -- still what the SHIPPED
                                                        // model runs on today (fantasypros_ecr)
  adp_central_tendency: {
    status: "preparatory_switch_not_yet_shipped",
    status_note: "...",             // says plainly: do not use this to recompute today's numbers
    adp_source: "ffc_half_ppr_10team",
    as_of_date: "2026-07-30",
    sample_window: "July 25, 2026 to July 30, 2026",
    n_players_covered: 157,
    n_players_total: 378,
    axis_note: "...",               // adp_pick is NOT corrected for K/DEF or round-depth yet
    sigma_pending_note: "...",      // no sigma_pick key at all -- see below
    coverage_note: "...",
    by_player: {
      "<player_name>": { adp_pick: <float|null>, coverage_flag: <bool> },
      ...   // one entry for EVERY key by_player has, never a missing key
    }
  },
  ...unchanged fields (mechanical_need_targets, max_at_position, need_penalty_per_surplus,
     room_noise_drawn_once_per_draft, algorithm_note -- algorithm_note's text corrected, see below)
}
```

### The two gaps, plainly

1. **No `sigma_pick`.** Per-player dispersion is gated on M0 in
   `docs/ranking/availability-opponent-model-precommit.md` -- FFC's `times_drafted` and
   `total_drafts_in_sample` columns don't reconcile yet (documented there). Until that clears,
   there is no honest per-player uncertainty to ship, so none is. Do not treat a missing
   `sigma_pick` as an oversight.
2. **`adp_pick` is not axis-corrected.** FFC's pick numbers count kickers/defenses (Westwood has
   no kicker slot) and FFC's sampled drafts run deeper than this league's 16 rounds. `axis_note`
   says this explicitly. The fix is an isotonic calibration against `board.json`, assigned to
   strategist (M4 in the precommit doc), not done here.

**Coverage is honest, not fabricated:** 157 of 378 season-universe players resolve an FFC row
(skill positions only); 79 of the 80 players actually present in `by_player` are covered (one
gap: Marvin Harrison Jr. -- no FFC row). Every `by_player` key has a corresponding
`adp_central_tendency.by_player` entry with `coverage_flag` explicit either way; `adp_pick` is
non-null iff `coverage_flag` is true. Never a silently-empty field for keys it doesn't cover.

### Also corrected: `algorithm_note`

It previously claimed the user's own BPA pick runs off `board.json`'s unperturbed rank. That was
never true -- `ds.strategy_bpa` reads `data.consensus_rank`, the identical array the opponent
model's `ranking_sources` draws from. Flagged in thread 104 as "worth a look independent of the
export ask"; fixed here as part of the same pass since it's the same block. If any UI copy quotes
the old wording, it was wrong and should be updated.

## Why

Thread 104 asked for the rank the model runs on so a real browser-side recompute (already
prototyped, benched under 5s) could be built without approximating on the wrong source. That part
(`player_ranks`) shipped as originally asked. Mid-session, strategist's thread 119 reply argued the
recompute should target ADP + per-player dispersion instead (closed-form marginal, no Monte Carlo
port needed at all) and asked backend to reformulate the export ahead of that switch so you don't
have to redo client work twice. `adp_central_tendency` is that forward-looking export -- not yet
actionable for a real recompute (no sigma), but the shape and the source-identity plumbing are
locked in now.

## Done looks like

Nothing required from frontend right now. When M0/M2/M3 clear (statistician-owned,
`docs/ranking/availability-opponent-model-precommit.md`) and `sigma_pick` + the axis-corrected
`adp_pick` ship, a follow-up thread will say so explicitly and that is the point at which a real
closed-form or Monte-Carlo-port recompute becomes buildable. Until then, `player_ranks` is still
the field to build a faithful port of TODAY's shipped model against, if that work resumes before
the ADP switch lands.

---
