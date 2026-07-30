/**
 * The trace-affordance registry.
 *
 * Every field path this app puts on screen is listed here. That is the whole point of
 * the file: these names are **user-visible UI text**, not internal plumbing. They
 * appear in value tooltips, in the assistant's provenance lines, and in the
 * methodology view, and a user checking a number reads them directly.
 *
 * So renaming one is a product change, not a refactor. It changes what the user sees,
 * breaks any note they wrote down, and invalidates screenshots and hand-offs. The
 * process is:
 *
 *   1. Bump the export contract version.
 *   2. Tell Design before the change ships -- this is a UX decision, not a code diff.
 *   3. Update the entry here, moving the old name into `renamedFrom` so the change is
 *      legible rather than silent.
 *
 * `ui/__tests__/trace-fields.test.ts` fails if an export stops carrying a registered
 * field, or carries a field this registry does not know about. A rename therefore
 * shows up as a failing build with that instruction attached, instead of as a tooltip
 * that quietly changed wording between two draft sessions.
 */

export interface TraceField {
  /** Path as displayed, minus the per-player array index. */
  readonly path: string;
  /** What the user is told this field means, in the tooltip and the methodology view. */
  readonly label: string;
  /** Contract version this name was pinned at. */
  readonly since: string;
  /** Previous user-visible names, newest first. Empty unless the field has been renamed. */
  readonly renamedFrom?: readonly string[];
}

/** The contract version the registry below is pinned against. */
export const TRACE_CONTRACT = '1.18.0';

/**
 * Changes to the user-visible trace surface, newest first.
 *
 * A value change belongs here as well as a rename. A user who wrote down "RB28" from a
 * tooltip and comes back to find "RB30" has had the ground move under them just as much
 * as if the field had been renamed -- the label is identical, the meaning is not.
 */
export const TRACE_CHANGELOG: ReadonlyArray<{
  version: string;
  kind: 'rename' | 'value' | 'added' | 'removed';
  summary: string;
}> = [
  {
    version: '1.18.0',
    kind: 'added',
    summary:
      'Pin moves 1.17.0 -> 1.18.0 (2026-07-30 backend, FR-2026-07-30-four-selectable-ranking-' +
      'sources). The board gains `ranking_source_selection` and a new `ranking_sources.json` ' +
      'artifact: the founder asked for the app to run off any of four sources at a user toggle ' +
      '-- Consensus adjusted (what shipped before, and still the default when no selection is ' +
      'passed), Consensus, ADP, and Proprietary bottom-up. The fourth is CATALOGUED BUT NOT ' +
      'BUILT and raises rather than silently serving another source. Additive; an existing ' +
      'reader that ignores the new field sees byte-identical behaviour.',
  },
  {
    version: '1.17.0',
    kind: 'added',
    summary:
      'Pin moves 1.16.0 -> 1.17.0 (2026-07-30 backend, thread 104). `availability.json` gains ' +
      '`client_simulation_parameters.player_ranks` -- the per-player rank the availability model ' +
      'actually runs its opponent model and the user\'s own best-available pick against, keyed to ' +
      'match `by_player`. It unblocks the browser-side recompute, which could not be built on ' +
      '`board.json:consensus_rank`: those are different rankings from different sources, and 73 of ' +
      'the top 80 players sit in a different order. Also adds an `adp_central_tendency` block, ' +
      'explicitly marked `preparatory_switch_not_yet_shipped` -- the model has NOT moved to ADP; ' +
      'that decision is gated on the M0 data defect. Additive only, nothing renamed or removed.',
  },
  {
    version: '1.16.0',
    kind: 'rename',
    summary:
      'Pin moves 1.15.0 -> 1.16.0 (2026-07-30 backend session, FR-079/FR-083 league-scoring-aware ' +
      'history fix). `season_stats.json`\'s `fantasy_points_ppr` is renamed `fantasy_points` (removed, ' +
      'not additive) plus a new `fantasy_points_available` boolean -- both files now compute this via ' +
      'THIS project\'s own scoring engine (`scoring.score_offensive_game`) under the exporting league\'s ' +
      'own `cfg.scoring`, scored per game and summed, never nflreadpy\'s fixed full-PPR ' +
      '`fantasy_points_ppr` column. `weekly_finishes.json`\'s `finish` ranking basis moved with it -- ' +
      'positional finish is now ranked by this same re-scored figure. Both files\' envelopes gain ' +
      '`league_id`/`scoring_note`/`scoring_ruleset_note`. PlayerDetail.tsx\'s WEEKLY FINISHES and THREE ' +
      'SEASONS sections previously carried a caveat unconditionally claiming "standard PPR, not this ' +
      'league\'s own ruleset" -- true of the pre-1.16.0 export, false of this one, and removed; replaced ' +
      'with a note built from the fetched envelope\'s own `league_id`/`scoring_ruleset_note ` (see ' +
      '`historyScoringNote` in PlayerDetail.tsx), since the fetch itself is still unprefixed (always the ' +
      'primary league\'s file regardless of which league is loaded -- a separate, still-open gap, see ' +
      '`ui/data/types.ts`\'s `RawWeeklyFinishes` doc comment and `docs/CURRENT-STATE.md` open item 5) and ' +
      'so may not actually match the league on screen. "PPR PTS" column header shortened to "PTS" to ' +
      'match -- it is no longer a PPR-specific figure.',
  },
  {
    version: '1.15.0',
    kind: 'added',
    summary:
      'Pin moves 1.14.0 -> 1.15.0 (ADR-062, thread 093). league.json gains ' +
      '`scoring_ruleset_note`, stating plainly which scoring ruleset a league actually runs on -- ' +
      'Westwood\'s verified custom ruleset for the primary league, or the new ' +
      '`standard_scoring.STANDARD_LEAGUE` (FR-042: no stacking yardage bonuses, defense unverified) ' +
      'for every other league, which for the first time genuinely differs from Westwood\'s numbers ' +
      '(e.g. Bijan Robinson 303.16 pts on the primary board vs. 296.68 on espn_10_half — the same ' +
      'preset used to silently copy Westwood\'s ruleset before this fix). No board.json player-row ' +
      'field changed shape, so BOARD_TRACE_FIELDS is unaffected; `scoring_ruleset_note` is a ' +
      'league.json field and is registered where it is actually rendered instead -- the league ' +
      'selector\'s track badge (design/TWO-TRACK-EXPRESSION.md) and a new "Scoring ruleset" section ' +
      'in Methodology.',
  },
  {
    version: '1.14.0',
    kind: 'added',
    summary:
      'Thread 082 (FR-024, backend done, this bump wires it into the three screens founder asked ' +
      'for). Every player row gains five ADP fields -- `adp`, `adp_min_pick`, `adp_max_pick`, ' +
      '`adp_selected_pct`, `adp_source` -- and board.json gains four top-level fields: ' +
      '`adp_source`, `adp_as_of_date`, `adp_match_rate_note`, `adp_source_note`. This is a ' +
      'MyFantasyLeague public-aggregate ADP PROXY (`adp_source: "mfl_proxy"`), a different claim ' +
      'from `consensus_rank` (FantasyPros expert consensus) and NOT this league\'s own draft ' +
      'history -- captured at a matching 10-team size but full PPR against this half-PPR league, ' +
      'so receivers read a few picks earlier than this league would actually take them. Measured ' +
      'on the live export: 144 of 510 rows carry a real value, 366 are honest nulls (MFL only has ' +
      'an opinion on roughly the top ~230 players). Rendered on the Board table (new ADP column, ' +
      'labelled "ADP (MFL)"), the Draft Room board list (compact ADP figure beside the delta), and ' +
      'the Player Detail sheet (full block: value, min-max range, selected%, the verbatim ' +
      '`adp_source_note` caveat, and `adp_as_of_date`). Deliberately NOT added as a second delta ' +
      'column next to `delta_vs_consensus` -- two adjacent deltas measuring different things ' +
      '(market vs. expert consensus) would read as one signal at a glance; the raw ADP value sits ' +
      'beside CONS instead, so a reader compares three numbers (CONS, ADP, our rank) rather than ' +
      'two deltas whose difference is not itself computed anywhere.',
  },
  {
    version: '1.13.0',
    kind: 'added',
    summary:
      'Pin moves 1.12.0 -> 1.13.0 (thread 074, closes the T5 export gap). board.json top level ' +
      'gains five snapshot-freshness fields -- `snapshot_as_of_date`, `snapshot_age_days`, ' +
      '`snapshot_max_age_days`, `snapshot_stale`, `snapshot_freshness_note` -- carrying the ' +
      '`FreshnessResult` `src/freshness.py` already computed on every build but previously only ' +
      'printed to the build console. No player-row field changed shape; audited against the real ' +
      'data/export/board.json (contract_version 1.13.0) before this bump. RefreshData.tsx now ' +
      'reads these instead of asserting the freshness check "is not exported by backend", which ' +
      'became false the moment this landed -- registered below in BOARD_HEADER_TRACE_FIELDS since ' +
      'they are now rendered.',
  },
  {
    version: '1.12.0',
    kind: 'added',
    summary:
      'Pin moves 1.9.0 -> 1.12.0 in one step, covering three backend bumps, audited against the ' +
      'real data/export/board.json (contract_version 1.12.0, all five new player-row keys ' +
      'confirmed present on row 0). 1.10.0 (ADR-050, thread 066): player rows gained ' +
      '`roster_status` -- a proxy from contracts.is_active, labelled as such; ' +
      '"no_active_contract_on_file" is not a retirement claim. 1.11.0 (ADR-051, thread 069): two ' +
      'rendered header strings changed value -- `consensus_source` is now ' +
      '"fantasypros_csv_2026draft" (was "fantasypros_ecr") and `board_source` moved with it -- and ' +
      'the board gained top-level `scoring_format`/`scoring_format_note` ("half_ppr" on the live ' +
      'export), registered in BOARD_HEADER_TRACE_FIELDS below because this player-row registry is ' +
      'compared 1:1 against player keys by its test. 1.12.0 (ADR-053, thread 073): four ' +
      'unconditional suspension keys on every row (`suspension_flag`, `suspension_games`, ' +
      '`projected_points_suspension_adjusted`, `suspension_adjustment_note`) -- deterministic ' +
      'games deduction from a hand-curated dated list that is currently empty, so every live row ' +
      'reads suspension_flag: false today; the rendering and this registry entry are ahead of the ' +
      'first real datum on purpose.',
  },
  {
    version: '1.9.0',
    kind: 'added',
    summary:
      'Audited field-by-field against the real data/export/board.json on disk (thread 043) before ' +
      'bumping this pin, not just against the changelog claim. Confirmed: the 26 player-row keys ' +
      'board.json actually carries are byte-for-byte the same set this registry already had ' +
      'registered for 1.8.0 -- no addition, removal, or rename. `player_id_gsis` is present as ' +
      'before and still emits null for all 378 players (verified by direct count on this export), ' +
      'so it is not silently populated as part of this bump -- see thread 052, still open, tracking ' +
      'the join-key gap separately. The only real change at 1.9.0 is two new sibling files, ' +
      '`weekly_finishes.json` and `season_stats.json` (thread 017/039, `src/export_history.py`) -- ' +
      'both carry their own `export_version` and are not `CONTRACT_VERSION`-tagged themselves, the ' +
      'same pattern `player_descriptions.json` already uses, so neither belongs in this ' +
      'board.json-scoped registry. This bump is a version-pin update with no rename to react to, ' +
      'recorded here (rather than skipped) because the changelog is the audit trail that lets the ' +
      'next session trust "no shape change" without re-deriving it from source.',
  },
  {
    version: '1.8.0',
    kind: 'value',
    summary:
      'Not a board.json change -- board.json, league.json, glossary.json and opponents.json ' +
      'regenerated byte-identically apart from the version/timestamp stamp (verified field by ' +
      'field against the previous export before this bump). Two real things moved: (1) ' +
      'rosters.json is a new artifact (docs/handoffs/016) -- full per-team roster slots and ' +
      'mechanical needs, now wired into the Opponents cards (docs/frontend-audit-2026-07.md); it ' +
      'is optional per league (null on any pre-1.8.0 export) and not yet in this registry because ' +
      'it is rendered from its own typed shape (RawRoster), not the trace-tooltip path this file ' +
      'governs. (2) strategies.json\'s "balanced" strategy verdict changed materially on ' +
      're-simulation: was "No real difference from just taking the best player available" (+17 ' +
      'margin, mixed sign across seasons), now "Consistently better than best-available in all 4 ' +
      'seasons, by about 28 points" -- every by_sigma cell moved with it. This was caught because ' +
      'this bump is also the fix for a stale-data bug: `frontend/scripts/sync-exports.mjs` was ' +
      'reading a stale, committed copy of the exports under `frontend/data/export/` (contract ' +
      '1.7.0, ~18h old) instead of the shared repo-root `data/export/` a concurrent backend ' +
      'session actually writes to. That copy is removed from git as part of this fix; the app now ' +
      'reads the one real source of truth.',
  },
  {
    version: '1.7.0',
    kind: 'value',
    summary:
      'Multi-league export support (ADR-041). Every artifact now carries league_id, and a second, ' +
      'non-primary league (a Yahoo-format mock, for pipeline validation only) can now exist ' +
      'alongside the primary one -- see ui/data/league-registry.ts and the TopBar league switcher. ' +
      'Two rendered strings changed on the primary league: board.json.def_note dropped its ' +
      'parenthetical "(1 per team)" (the count is league-specific and now lives in ' +
      'league.json.roster.starters, not repeated in prose), and ' +
      'availability.json.metadata.sigma_plain_english changed "the other nine teams" to "the ' +
      'other opposing teams" since team count is no longer always nine. New fields not yet ' +
      'surfaced anywhere in this app -- league_name, platform, draft_type, unsupported_positions, ' +
      'unsupported_positions_note -- are additive and not yet in the registry below because ' +
      'nothing renders them; the per-player field set this registry actually governs is unchanged.',
  },
  {
    version: '1.6.0',
    kind: 'removed',
    summary:
      'Two separate backend updates landed close together. The commit that made the second ' +
      'change was titled "Contract v1.6.0" but initially shipped six artifacts still stamped ' +
      '"1.5.1" -- fixed in a follow-up commit that regenerated nothing and only corrected the ' +
      'stamp (content was byte-identical throughout). (1) league.json now carries generated_utc ' +
      '-- it was the only artifact without one, through five contract versions; provenance only, ' +
      'no displayed value changed. (2) The availability model dropped the prior-year repeat ' +
      'assumption entirely and te_scenarios was removed from availability.json (ADR-033/034). ' +
      'Availability figures were circular before this -- their spread came from assuming two ' +
      'named managers repeat their 2025 TE picks -- which is why this app did not surface them. ' +
      'That is no longer true; the Availability screen is queued to read from the export directly.',
  },
  {
    version: '1.5.0',
    kind: 'value',
    summary:
      'Two user-visible strings corrected upstream, both of which this app renders verbatim. ' +
      'league.json.flex_split_note said the flex split was "an explicit tunable assumption, not ' +
      'a measurement" — false since ADR-029 measured it over 26 seasons; it now carries the ' +
      'variance caveat instead. glossary.json\'s replacement-level definition still read ' +
      'RB28/WR41/TE11 in prose. In both cases the values we rendered were right and the help ' +
      'text beside them disagreed, which is the worse failure of the two. Also: nulls.json ' +
      'elite_te_early is now −96.1 ± 6 (was −92.9), resolving a disagreement with ' +
      'strategies.json; no conclusion moved. DEF settled as a permanent exclusion (ADR-039).',
  },
  {
    version: '1.4.0',
    kind: 'value',
    summary:
      'Bug fix upstream: league.json is valid JSON again (the open-ended DEF points-allowed ' +
      'tier now ends in null plus a note, instead of a bare Infinity token). No board value ' +
      'moved — board.json and availability.json regenerated byte-identically. Two stale ' +
      'strings were corrected: league.json.replacement_levels_note and glossary.json still ' +
      'read RB28/WR41/TE11 in prose while the values had been RB30/WR40/TE10 since 1.3.0. ' +
      'That prose is user-visible, so the correction is recorded here.',
  },
  {
    version: '1.3.0',
    kind: 'value',
    summary:
      'Startable thresholds changed from RB28/WR41/TE11 to RB30/WR40/TE10 (QB10 unchanged), ' +
      'per ADR-029, from measurement rather than convention. No field was renamed and no ' +
      'label changed — but the displayed values did, and every vbd, projected_points and ' +
      'overall_rank on the board moved with them. Any reference material quoting the old ' +
      'numbers is now wrong.',
  },
  { version: '1.0.0', kind: 'added', summary: 'Initial registry of user-visible trace fields.' },
];

export const BOARD_TRACE_FIELDS: readonly TraceField[] = [
  { path: 'overall_rank', label: 'Our board position', since: '1.0.0' },
  { path: 'player', label: 'Player name', since: '1.0.0' },
  { path: 'position', label: 'Position', since: '1.0.0' },
  { path: 'team', label: 'NFL team', since: '1.0.0' },
  { path: 'positional_rank', label: 'Rank within position', since: '1.0.0' },
  { path: 'positional_label', label: 'Position and positional rank', since: '1.0.0' },
  { path: 'bye_week', label: 'Bye week, from the 2026 schedule', since: '1.0.0' },
  { path: 'projected_points', label: 'Projected fantasy points', since: '1.0.0' },
  { path: 'ci_low', label: 'Interval, lower bound', since: '1.0.0' },
  { path: 'ci_high', label: 'Interval, upper bound', since: '1.0.0' },
  { path: 'ci_applies_to', label: 'What the interval is on', since: '1.0.0' },
  {
    path: 'projection_within_fitted_range',
    label: 'Whether the projection sits inside the fitted curve',
    since: '1.0.0',
  },
  { path: 'projection_note', label: 'Why the projection is not shown', since: '1.0.0' },
  { path: 'vbd', label: 'Value over replacement', since: '1.0.0' },
  { path: 'consensus_rank', label: 'FantasyPros expert consensus rank', since: '1.0.0' },
  {
    path: 'delta_vs_consensus',
    label: 'Consensus rank minus our rank; positive means we like the player more',
    since: '1.0.0',
  },
  { path: 'tier', label: 'Tier number', since: '1.0.0' },
  { path: 'tier_label', label: 'Tier', since: '1.0.0' },
  {
    path: 'structural_adjustment',
    label: 'Rank movement from this league’s format',
    since: '1.0.0',
  },
  {
    path: 'structural_breakdown',
    label: 'How the rank movement splits',
    since: '1.0.0',
  },
  {
    path: 'structural_breakdown.replacement_levels',
    label: 'Movement attributable to this league’s replacement levels',
    since: '1.0.0',
  },
  {
    path: 'structural_breakdown.scoring_and_vbd_method',
    label: 'Movement attributable to our scoring rules and VBD method',
    since: '1.0.0',
  },
  { path: 'evaluative_adjustment', label: 'Player-level opinion', since: '1.0.0' },
  {
    path: 'evaluative_adjustment_available',
    label: 'Whether any player-level opinion exists to attribute',
    since: '1.0.0',
  },
  {
    path: 'evaluative_adjustment_note',
    label: 'Why there is no player-level opinion',
    since: '1.0.0',
  },
  { path: 'id', label: 'Internal player id', since: '1.0.0' },
  { path: 'player_id_gsis', label: 'GSIS player id', since: '1.0.0' },
  { path: 'availability', label: 'Availability probabilities (out of scope in this app)', since: '1.0.0' },
  {
    path: 'roster_status',
    label: 'Contract-status proxy; "no active contract on file" is not a retirement or inactive claim',
    since: '1.10.0',
  },
  {
    path: 'suspension_flag',
    label: 'Whether a confirmed suspension is on file for this player',
    since: '1.12.0',
  },
  {
    path: 'suspension_games',
    label: 'Confirmed games suspended; null when not suspended',
    since: '1.12.0',
  },
  {
    path: 'projected_points_suspension_adjusted',
    label: 'Projection after deducting suspended games; null unless a confirmed, non-appealed suspension exists',
    since: '1.12.0',
  },
  {
    path: 'suspension_adjustment_note',
    label: 'Why the projection was or was not suspension-adjusted',
    since: '1.12.0',
  },
  {
    path: 'adp',
    label: 'Average draft position, MyFantasyLeague proxy -- not this league’s ADP',
    since: '1.14.0',
  },
  {
    path: 'adp_min_pick',
    label: 'Earliest pick this player was taken at in the MFL sample',
    since: '1.14.0',
  },
  {
    path: 'adp_max_pick',
    label: 'Latest pick this player was taken at in the MFL sample',
    since: '1.14.0',
  },
  {
    path: 'adp_selected_pct',
    label: 'Share of sampled MFL drafts that took this player at all',
    since: '1.14.0',
  },
  {
    path: 'adp_source',
    label: 'Which ADP source this value came from -- always travels with the value',
    since: '1.14.0',
  },
];

/**
 * Top-level (non-player-row) board.json fields this app renders. Kept separate
 * because `BOARD_TRACE_FIELDS` is compared 1:1 against the *player-row* key set
 * by `ui/__tests__/trace-fields.test.ts` -- a top-level path in that list would
 * trip its "registry names a field the export dropped" check.
 */
export const BOARD_HEADER_TRACE_FIELDS: readonly TraceField[] = [
  {
    path: 'scoring_format',
    label: 'Scoring format the consensus source confirmed at export time; null when unconfirmed',
    since: '1.11.0',
  },
  {
    path: 'scoring_format_note',
    label: 'What a null scoring format means',
    since: '1.11.0',
  },
  {
    path: 'snapshot_as_of_date',
    label: 'The rankings snapshot date this board was built from',
    since: '1.13.0',
  },
  {
    path: 'snapshot_age_days',
    label: 'Days between build time and the rankings snapshot date',
    since: '1.13.0',
  },
  {
    path: 'snapshot_max_age_days',
    label: 'This league’s configured staleness threshold, in days',
    since: '1.13.0',
  },
  {
    path: 'snapshot_stale',
    label: 'Whether the rankings snapshot exceeded the staleness threshold at build time',
    since: '1.13.0',
  },
  {
    path: 'snapshot_freshness_note',
    label: 'What the snapshot-freshness check does and does not claim',
    since: '1.13.0',
  },
  {
    path: 'adp_source',
    label: 'The ADP source name shown at board level, e.g. "mfl_proxy"',
    since: '1.14.0',
  },
  {
    path: 'adp_as_of_date',
    label: 'Date the ADP snapshot was captured',
    since: '1.14.0',
  },
  {
    path: 'adp_match_rate_note',
    label: 'How many ADP rows resolved to a board player via the identity join',
    since: '1.14.0',
  },
  {
    path: 'adp_source_note',
    label: 'The full ADP proxy caveat -- population, format mismatch, sample size',
    since: '1.14.0',
  },
];

export const LEAGUE_TRACE_FIELDS: readonly TraceField[] = [
  { path: 'teams', label: 'Teams in the league', since: '1.0.0' },
  { path: 'rounds', label: 'Draft rounds', since: '1.0.0' },
  { path: 'user_draft_slot', label: 'Your draft slot', since: '1.0.0' },
  { path: 'pick_sequence', label: 'Your picks, by overall pick number', since: '1.0.0' },
  { path: 'replacement_levels', label: 'Startable threshold per position', since: '1.0.0' },
  {
    path: 'positions_without_replacement_levels',
    label: 'Positions started in this league that deliberately have no threshold',
    since: '1.5.0',
  },
  { path: 'roster.starters', label: 'Starting lineup slots', since: '1.0.0' },
  { path: 'playoff.teams', label: 'Playoff teams', since: '1.0.0' },
];

const BOARD_BY_PATH = new Map(BOARD_TRACE_FIELDS.map((f) => [f.path, f]));

/** Strips the array index so `players[12].vbd` looks up as `vbd`. */
export function boardFieldOf(displayedPath: string): TraceField | undefined {
  const tail = displayedPath.replace(/^board\.json:players\[\d+\]\./, '');
  return BOARD_BY_PATH.get(tail);
}

/**
 * The tooltip a traced value shows: the field's user-facing meaning followed by the
 * path itself, because the path is the thing a user can go and check.
 *
 * `showPath` gates the path half only (`ui/data/traceMode.ts`'s global switch, default
 * off) -- the meaning half is a plain-English sentence, not developer-facing sourcing
 * text, so it stays in the tooltip either way. When the path is unknown to this
 * registry and the switch is off, there is nothing left to show (an empty tooltip
 * renders as no native title at all, which is correct -- an unregistered path is
 * exactly the case `ui/__tests__/trace-fields.test.ts` is meant to catch, not a case
 * to leak into the tooltip regardless of the switch).
 */
export function traceTooltip(displayedPath: string, showPath: boolean = true): string {
  const field = boardFieldOf(displayedPath);
  if (!field) return showPath ? displayedPath : '';
  return showPath ? `${field.label}\n${displayedPath}` : field.label;
}
