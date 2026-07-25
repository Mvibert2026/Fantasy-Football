# Front-End Data Contract

**Version 1.0.0** · generated into `data/export/` · authored 2026-07-25

The UI reads these files and **never** touches `data/nfl.db`. Every artifact carries
`contract_version` and `generated_utc`. Breaking changes bump the major version and are
recorded in the changelog at the bottom.

## Regenerating

```bash
python src/export_contract.py     # board.json, availability.json, league.json
python src/export_static.py       # glossary.json, nulls.json, opponents.json
python src/export_strategies.py   # strategies.json  (runs simulations, slow)
```

`availability.json` reads `data/availability_2026.csv`, so run `src/run_availability.py`
first if the board has moved.

---

## Cross-cutting conventions

- All ranks are **1-indexed**; rank 1 is best.
- `delta_vs_consensus` is `consensus_rank - overall_rank`. **Positive means our board likes
  the player more than consensus does.**
- `null` means *not available*, never *zero*. Fields that could not be computed carry a
  sibling `*_note` or `data_status` explaining why. **No value in these files is invented to
  fill a gap.**
- Probabilities are floats in `[0, 1]`, not percentages.
- Pick numbers are overall draft picks (1-160), not round-and-slot.

---

## `board.json`

| Field | Type | Notes |
|---|---|---|
| `contract_version`, `generated_utc`, `season` | str | |
| `curve_fits` | obj | Per position: `r_squared`, `residual_sd`, `n_obs` for the projection fit |
| `curve_caveat` | str | **Surface this in the UI.** R² is 0.16–0.27 |
| `replacement_levels_used` | obj | `{QB:10, RB:28, WR:41, TE:11}` |
| `published_levels_compared_against` | obj | `{QB:12, RB:24, WR:36, TE:12}` |
| `players[]` | array | 378 records, sorted by `overall_rank` |

Per player:

| Field | Type | Notes |
|---|---|---|
| `overall_rank` | int | Our board position |
| `player`, `position`, `team` | str | |
| `positional_rank` | int | e.g. 12 |
| `positional_label` | str | e.g. `"WR12"` |
| `bye_week` | int\|null | Derived from the 2026 schedule |
| `projected_points` | float | **Weak.** See `curve_caveat` |
| `ci_low`, `ci_high` | float\|null | 95% interval |
| `ci_applies_to` | str | Currently `"vbd"` — the interval is on VBD, **not** on `projected_points` |
| `vbd` | float | Value over replacement |
| `consensus_rank` | int | FantasyPros ECR |
| `delta_vs_consensus` | int | Positive = we rank higher than consensus |
| `tier` | str\|null | `T1`–`T4`, or `T5+` |
| `structural_adjustment` | int | Rank movement from league-format corrections |
| `structural_breakdown.replacement_levels` | int | Movement attributable to RB28/WR41/TE11/QB10 vs published RB24/WR36/TE12/QB12 |
| `structural_breakdown.scoring_and_vbd_method` | int | The remainder: our scoring rules and the VBD method itself |
| `evaluative_adjustment` | **always null** | See below |
| `evaluative_adjustment_note` | str | Why it is null |
| `availability` | obj | `{pick: {sigma_5, sigma_10, sigma_20}}`, top ~80 players only; `{}` otherwise |

### The structural / evaluative split — read this

`structural_adjustment` is computed **exactly**, not estimated: the board is rebuilt under
published 12-team replacement levels and differenced against ours. The two components sum to
`delta_vs_consensus` by construction.

`evaluative_adjustment` is **always null, deliberately.** The board assigns every player at
the same positional consensus rank an identical projection (ADR-017), so it holds no
player-level opinion at all — there is nothing to attribute. Producing a split here would mean
inventing a number the board does not contain. A genuine evaluative component needs
component-level projections (test-registry #2), which no accessible source provides.

**UI implication:** do not build a "we disagree with the experts about this player" view. The
board does not currently support that claim. It supports "this player is worth more *in this
league's format*", which is a different and better-founded statement.

---

## `availability.json`

| Key | Shape |
|---|---|
| `by_player` | `{player: {pick: {sigma_5, sigma_10, sigma_20}}}` |
| `by_tier` | `{position: {tier: {pick: {sigma_5, sigma_10, sigma_20}}}}` — P(≥1 of that tier still on the board) |
| `te_scenarios[]` | `{tier, pick, probability_available, note}` — the 0% / 50% / 100% repeat cases, kept separate |
| `metadata` | sims run, sigma values, plain-English sigma explanation, user picks, reliability note |

`te_scenarios` is deliberately **not** merged into `by_tier`: it is a conditional forecast under
a named assumption about two specific managers, not a marginal probability, and merging them
would let the UI present a scenario as a fact.

**These are the most reliable numbers in the project** — they never pass through the projection
curve. Surface `metadata.reliability_note`.

---

## `strategies.json`

| Field | Notes |
|---|---|
| `baseline` | `"bpa_consensus"` |
| `power_floor` | `n_seasons`, `smallest_attainable_two_sided_p`, and a plain-English gloss |
| `lineup_assumption` | Perfect-hindsight caveat (Block 3 corrects this) |
| `strategies[].by_sigma[]` | `mean_roster_points`, `p_top4`, `margin_vs_baseline`, `ci_low/high`, `seasons_positive`, `sign_test_p`, `per_season_margin`, `simulation_se` |
| `strategies[].verdict` | Plain-language sentence, safe to display verbatim |

**Do not render `sign_test_p` against a 0.05 threshold.** The floor is 0.125 at n=4 — nothing
can clear 0.05. Render `power_floor.plain_english` next to any significance claim.

`simulation_se` and the season CI are **different uncertainties**: the first shrinks with more
simulated drafts, the second does not. Never combine them.

---

## `opponents.json`

**7 of 9 opponents have no data.** Only draft slots are known, and those are *derived* from
supplied pick numbers, not guessed.

| Field | Notes |
|---|---|
| `coverage_warning` | Top-level; surface it |
| `opponents[].team_name` | `null` for the 7 unknown |
| `opponents[].draft_slot_2026` | Always known (derived) |
| `opponents[].draft_slot_2025`, `positional_tendencies`, `first_pick_by_position`, `consensus_tracking_behaviour` | `null` throughout — not supplied |
| `opponents[].cited_2025_picks` | Empty. The contract asked for pick citations; none exist in this repo and none were invented |
| `opponents[].holds_picks_19_to_22` | `true` for Shit Leopards (slot 2) and Cucked Commish (slot 1) |
| `opponents[].data_status` | `PARTIAL` or `NOT SUPPLIED`, per profile |

**To populate these:** supply the 2025 draft board as (pick number, team, player). It is not
derivable from anything currently ingested, and the simulator consequently models all nine
opponents identically.

---

## `glossary.json`

`{terms: {term: {short_definition, long_explanation}}}`. Written for a smart non-statistician;
no jargon inside definitions. Covers VBD, replacement level, consensus rank, confidence
interval, tier, structural vs evaluative adjustment, availability probability, sigma, sign
test, power floor, holdout, projected points.

`short_definition` fits a tooltip; `long_explanation` fits a help panel.

---

## `nulls.json`

`{preamble, findings: [{id, claim_tested, method, result, plain_language_summary}]}`.

Five entries: PR-002 spike-week persistence, Hero RB, elite-TE-early, QB-early, and the
board-vs-consensus status (including an openly recorded correction to our own earlier error).

This is a **feature section**, not an appendix. Public guides do not publish their failures.

---

## `league.json`

Teams, rounds, user slot, full pick sequence, roster slots, complete scoring rules,
replacement levels (with the note that they are derived, not hardcoded), the `flex_split`
assumption flagged as an assumption, playoff structure, trade deadline, FAAB.

---

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-25 | Initial contract: board, availability, strategies, opponents, glossary, nulls, league |
