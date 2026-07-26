# Front-End Data Contract

**Version 1.7.0** · generated into `data/export/` · authored 2026-07-25

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

All three scripts accept `--league <league_id>` (default: the primary league). See
"Multi-league exports" below.

---

## Multi-league exports (ADR-041)

Every artifact now carries `league_id`. **The primary league's six artifacts stay at the
unprefixed `data/export/` path** — this never changes, so nothing about existing consumers
breaks. Any other league's six artifacts land at `data/export/<league_id>/`, same filenames,
same shape.

League configs themselves live at `data/leagues/<league_id>.json` (a `LeagueConfig`, see
`src/league_config.py`) and are tracked in git — they are source data, not generated output.

**Timing** (measured on the primary league and confirmed comparable on a 12-team mock):
`board.json` + `league.json` regenerate in ~7s; a full `availability.json` recompute
(`run_availability.py`, 3000 sims × 3 sigmas) takes ~45-60s; `strategies.json`
(`export_strategies.py`, 43,200 simulated drafts) takes ~13 minutes regardless of which league.
Board + availability can support a "recompute on settings change" UI flow with a loading state.
Strategies is a background/queued job — this does not change per league, since the cost is
simulation count, not league count.

**Findings that do NOT carry across leagues.** `nulls.json`'s findings (PR-002, Hero RB,
elite-TE, QB-early, board-vs-consensus) are computed under the PRIMARY league's exact scoring
rules and roster shape. They are NOT re-run for other leagues — `nulls.json` for a non-primary
league returns the same finding identities with `result: "NOT_YET_RUN_FOR_THIS_LEAGUE"` rather
than either omitting the file or presenting the primary league's numbers as if they applied.
The single exception is the alpha-detection closure (ADR-026), which is a function of how many
consensus seasons exist, not of any league's rules — but that finding is not currently
represented in `nulls.json` at all, so this is stated here for anyone reasoning about which
project-level claims travel across leagues and which do not.

**Known gap: no kicker or DST scoring engine exists.** A league that rosters K and/or DEF gets
`unsupported_positions` listing both — no replacement level, projection, VBD or board row for
either, for the same reason DEF has never had one (no scoring data ingested).

---

## Cross-cutting conventions

- All ranks are **1-indexed**; rank 1 is best.
- `delta_vs_consensus` is `consensus_rank - overall_rank`. **Positive means our board likes
  the player more than consensus does.**
- `null` means *not available*, never *zero*. Fields that could not be computed carry a
  sibling `*_note` or `data_status` explaining why. **No value in these files is invented to
  fill a gap.** The single documented exception is the open-ended DEF points-allowed tier in
  `league.json`, where a null ceiling means *no upper bound*; it carries an inline note saying so.
- **Every file is strict JSON (RFC 8259).** No `Infinity`, `-Infinity` or `NaN` tokens — those
  are valid Python literals but not valid JSON, and `JSON.parse` throws on them. Enforced at
  write time (`allow_nan=False`) and by a test that parses each artifact with `parse_constant`
  set to raise. See the 1.4.0 changelog entry.
- Probabilities are floats in `[0, 1]`, not percentages.
- Pick numbers are overall draft picks (1-160), not round-and-slot.

---

## `board.json`

| Field | Type | Notes |
|---|---|---|
| `contract_version`, `generated_utc`, `season` | str | |
| `curve_fits` | obj | Per position: `r_squared`, `residual_sd`, `n_obs` for the projection fit |
| `curve_caveat` | str | **Surface this in the UI.** R² is 0.16–0.27 |
| `replacement_levels_used` | obj | `{QB:10, RB:30, WR:40, TE:10}` (ADR-029, measured) |
| `replacement_levels_flex_split_measured` | bool | `false` means `flex_split` was borrowed from the primary league's ADR-029 measurement as a flagged placeholder, not measured for THIS league |
| `published_levels_compared_against` | obj | `{QB:12, RB:24, WR:36, TE:12}` |
| `unsupported_positions` | array | Starter positions with no scoring engine (always includes `DEF`; also `K` for a league that rosters one). Generalizes `def_supported`/`def_note`, which are unchanged for back-compat |
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
| `structural_breakdown.replacement_levels` | int | Movement attributable to RB30/WR40/TE10/QB10 vs published RB24/WR36/TE12/QB12 |
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
| `metadata` | sims run, sigma values, plain-English sigma explanation, user picks, reliability note, marginals note |
| `client_simulation_parameters` | Everything needed to re-run the opponent model client-side, conditioned on live draft state — see below |

**These are the most reliable numbers in the project** — they never pass through the projection
curve. Surface `metadata.reliability_note`.

### `te_scenarios` is REMOVED (ADR-033, ADR-034) — do not reintroduce it

Prior versions shipped a `te_scenarios[]` block: P(TE tier survives to pick 23) under three
hand-set probabilities that two *named* managers repeat a 2025 round-3 TE pick. It was found
circular — its entire spread (0.60 at 0% repeat down to 0.13 at 100%) came from assuming
specific people's behaviour, not from measuring anything. The switch that generated it
(`repeat_2025 / half_repeat / no_repeat`) has been deleted from the codebase, not just the
export. `by_tier["TE"]["T1"]` at pick 23 is now the answer to that question, computed under the
model below rather than assumed.

### `by_player` / `by_tier` are UNCONDITIONAL marginals — "Prep mode" only

They average over every possible draft, not the one actually happening. **Do not display them
as current once a real draft is underway** — `metadata.marginals_note` says so and must be
surfaced anywhere these numbers are read mid-draft. For a number conditioned on picks already
made, recompute using `client_simulation_parameters` (below) against the real board state
instead of reading these.

### `client_simulation_parameters` — what a client-side simulator needs

| Field | Notes |
|---|---|
| `ranking_sources[]` | `{name, weight}`. Today: one entry, `fantasypros_ecr`, weight 1.0. A second entry (MFL ADP, ADR-035) extends this list, not the algorithm |
| `mechanical_need_targets` | Per position, the count past which a team is no longer preferred toward that position. `STARTERS[pos] + FLEX_SLOTS` for flex-eligible positions — see `mechanical_need_targets_note` for why this is an upper bound, not a partition |
| `max_at_position` | Hard cap; a team at this count never takes another of that position |
| `need_penalty_per_surplus` | Additive rank penalty per player beyond `mechanical_need_targets`, applied before ranking |
| `room_noise_drawn_once_per_draft` | `true`. One noise draw per player, shared by the whole room for a single simulated draft — not per pick, not per team |
| `algorithm_note` | The full per-draft procedure in plain English, referencing `league.json` for roster/pick-order fields it does not duplicate |

Player pool, positions and consensus ranks come from `board.json`; roster structure, team count,
rounds and draft slot come from `league.json`. This block supplies only what belongs to the
**opponent model** itself, so nothing is duplicated across artifacts.

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

### `scoring.defense.points_allowed`

An ordered list of `[ceiling, bonus]` tiers, inclusive upper bound. **The final tier's ceiling
is `null`, meaning no upper bound** — not "unavailable". `points_allowed_note` states this
inline so the field is unambiguous without reading this document.

Before 1.4.0 this shipped as a bare `Infinity` token, which is invalid JSON; see the changelog.

### DEF is permanently excluded — settled decision (ADR-039)

`roster.starters.DEF` is `1`, but `replacement_levels` has no `DEF` key. That is deliberate, and
`positions_without_replacement_levels: ["DEF"]` now says so explicitly rather than leaving the
absence to be read as an oversight. `board.json.def_supported` stays `false`.

**Do not synthesize a DEF replacement level from these files.** No DST data is ingested, so any
DEF points value would be fabricated. Render `board.json.def_note` verbatim where a DEF number
would otherwise go.

Ingesting DST data is **not** planned. Note for anyone tempted to reopen this: the replacement
*rank* DEF10 is derivable from league structure alone (10 teams × 1 starter, the same arithmetic
as QB10). It is still withheld, because publishing a rank invites a downstream VBD and the
*points* half genuinely does not exist.

---

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-25 | Initial contract: board, availability, strategies, opponents, glossary, nulls, league |
| 1.1.0 | 2026-07-25 | Added the narration layer (Fact schema + renderer contract). Additive only; no existing field changed |
| 1.2.0 | 2026-07-25 | Design-handoff reconciliation: integer `id` and `tier`, `evaluative_adjustment` 0 + availability flag, `consensus_source_count`, `def_supported`, `projection_within_fitted_range` |
| 1.3.0 | 2026-07-25 | **VALUE CHANGE, no schema change.** Replacement levels RB28/WR41/TE11 -> RB30/WR40/TE10 from measurement (ADR-029). Every `vbd`, `projected_points` and `overall_rank` in board.json moved. Re-fetch the board. |
| 1.7.0 | 2026-07-25/26 | **Additive — multi-league (ADR-041).** All six per-league artifacts gain `league_id`. `board.json`/`league.json` gain `unsupported_positions`/`unsupported_positions_note` (generalizes `def_supported`/`def_note`, kept unchanged for back-compat), `replacement_levels_flex_split_measured`/`_note`. `league.json` gains `league_name`, `platform`, `draft_type`, `flex_split_measured`. **New export location convention:** the primary league stays at the unprefixed `data/export/` path (no change for existing consumers); every other league's six artifacts land at `data/export/<league_id>/`, same filenames, same shape. Minor prose genericization in `availability.json.metadata.sigma_plain_english` ("the other nine teams" → "the other opposing teams", no longer assumes 10 teams) and `league.json`'s DEF note. All primary-league VALUES verified unchanged — see ADR-041 |
| 1.6.0 | 2026-07-25 | **BREAKING (removal).** `availability.json.te_scenarios[]` removed — implements ADR-033/034. The prior-year-manager-repeat assumption it encoded has been deleted from the model, not just the export. Added `availability.json.client_simulation_parameters` (ranking-source mixture, mechanical need targets, room-noise spec) so a client can recompute availability conditioned on live draft state instead of reading the unconditional marginals. `metadata.figures_are_unconditional_marginals` + `metadata.marginals_note` added. TE T1 @ pick 23 moves from 0.598 (old unconditional baseline) to ~0.59 under the new model — inside the pre-declared sanity bracket, not a reversal |
| 1.5.1 | 2026-07-25 | **Additive, provenance only.** `league.json` gains `generated_utc` — it was the one artifact shipping without it, through five contract versions, so consumers keying a run id on it fell back to "unversioned". A test now asserts every artifact carries both `contract_version` and `generated_utc`, which is what this document's opening line has always claimed. No other field changed |
| 1.5.0 | 2026-07-25 | **Additive.** `league.json` gains `positions_without_replacement_levels: ["DEF"]` + note (ADR-037 — DEF permanently excluded, stated as a decision rather than an absence). `board.json.def_note` reworded to match. `league.json.flex_split_note` corrected: it called the split "an explicit tunable assumption, not a measurement", which ADR-029 made false. `nulls.json` PR-003 elite-TE result restated −92.9 → **−96.1 ± 6** (ADR-028 seed fix; no conclusion moved). No existing field removed or retyped |
| 1.4.0 | 2026-07-25 | **BUG FIX — `league.json` was not valid JSON.** `scoring.defense.points_allowed`'s open-ended tier shipped a bare `Infinity` token, so `JSON.parse`/`fetch().json()` threw and no browser could load the file. The ceiling is now `null` plus a `points_allowed_note`. All three exporters now write with `allow_nan=False`, and a test parses every artifact with `parse_constant` set to raise. **Consumers sanitising this token at copy time can drop the workaround.** Also: stale `RB28/WR41/TE11` prose corrected to `RB30/WR40/TE10` in `league.json.replacement_levels_note` and `glossary.json` (the *values* have been correct since 1.3.0; only these two strings were stale). `board.json` and `availability.json` regenerated byte-identically — no values moved. |

---

## Narration layer (added 2026-07-25, contract 1.1.0)

`src/narrate.py` sits between the exports and any AI-generated prose. **The renderer never
sees the exports.** It receives only `Fact` objects.

### `Fact`

| Field | Notes |
|---|---|
| `id` | Stable, e.g. `tier_survival_shift.RB.T1.18_to_23` |
| `kind` | `tier_survival_shift`, `tier_survival`, `replacement_level_crossing`, `reach_cost`, `opponent_need`, `registered_null` |
| `source_path` | `"artifact.json:dotted.path"` — **must resolve**, or extraction raises |
| `value` | Numeric, or `null` for narrative facts |
| `template` | Plain-language starting wording with `{}` placeholders |
| `params` | Values the template substitutes |
| `confidence` | `high` (availability — no projection curve), `medium` (structural arithmetic), `low` (projection/VBD, R² 0.16–0.27) |

### Renderer contract — binding

1. It may **reword** a Fact's `template`.
2. It may **not** introduce any claim, comparison between Facts, cause, prediction, or
   recommendation not already present in a Fact.
3. Every emitted sentence must be traceable to exactly one `Fact.id`.
4. It must call `validate_render_input()`, which raises `RenderContractError` on anything
   that is not a list of `Fact`s — including a bare Fact, a dict, or a string.
5. It must respect `confidence`. A `low`-confidence Fact may not be rendered in the same
   assertive register as a `high`-confidence one.

`render_reference()` is a pure-substitution reference implementation used to test the
traceability property. It is **not** the LLM renderer.

### Why it is built this way

A language model handed draft data will produce fluent causal prose whether or not the data
supports it — "he's falling because the room is worried about his workload" is exactly the
class of claim this project spends its effort not making. Facts are the airlock. If a claim
is not in a Fact, it cannot reach the page.

`nulls.json` feeds `registered_null` facts so the renderer can say "we tested this and found
no evidence" instead of improvising a rationale for a result we do not have.
