/**
 * Shapes of the export artifacts, transcribed from docs/data-contract.md and verified
 * against the files in data/export/.
 *
 * These describe the artifacts as they actually are, which in two places differs from
 * the prose in the contract doc (the doc is at 1.1.0; the artifacts declare 1.0.0):
 *
 *   - `tier` is an int with a separate `tier_label` string; the doc describes a single
 *     string field.
 *   - `evaluative_adjustment` is 0 with a sibling `evaluative_adjustment_available:
 *     false`; the doc says the field is always null.
 *
 * Both are recorded in the contract-drift banner rather than smoothed over here.
 */

export type Position = 'QB' | 'RB' | 'WR' | 'TE';

export interface RawBoardPlayer {
  id: number;
  player_id_gsis: string | null;
  overall_rank: number;
  player: string;
  position: Position;
  positional_rank: number;
  positional_label: string;
  team: string;
  bye_week: number | null;
  /**
   * Contract 1.10.0 (ADR-050, thread 066). A PROXY derived from
   * `contracts.is_active`, not a real active/IR/practice-squad feed.
   * "no_active_contract_on_file" must never be worded as "retired" or
   * "confirmed inactive" -- a free agent between deals reads the same way.
   * Optional so a pre-1.10.0 export still parses.
   */
  roster_status?: 'active' | 'no_active_contract_on_file' | 'unknown_no_contract_data';
  projected_points: number;
  ci_low: number | null;
  ci_high: number | null;
  ci_applies_to: string;
  /**
   * False for 233 of 378 players. When false, `projection_note` instructs the UI not
   * to display `projected_points` at all -- the field is populated but contractually
   * suppressed. This is the sparse state.
   */
  projection_within_fitted_range: boolean;
  projection_note: string | null;
  vbd: number;
  consensus_rank: number;
  delta_vs_consensus: number;
  tier: number;
  tier_label: string;
  structural_adjustment: number;
  structural_breakdown: {
    replacement_levels: number;
    scoring_and_vbd_method: number;
  };
  evaluative_adjustment: number;
  evaluative_adjustment_available: boolean;
  evaluative_adjustment_note: string;
  availability: Record<string, unknown>;
  /**
   * Contract 1.12.0 (ADR-053, thread 073). Unconditional on every row in a
   * 1.12.0+ export (never conditionally present there); optional here only so a
   * pre-1.12.0 export still parses. Deterministic games-played deduction from a
   * hand-curated, dated list (`data/suspensions_2026.json`), NOT a probability
   * model. That list is currently empty, so every live row reads
   * `suspension_flag: false` -- expected, not a bug.
   * `projected_points_suspension_adjusted` is null when the flag is false OR
   * the appeal is still pending (`"not_adjusted_pending_appeal"`).
   */
  suspension_flag?: boolean;
  suspension_games?: number | null;
  projected_points_suspension_adjusted?: number | null;
  suspension_adjustment_note?: 'not_suspended' | 'games_adjusted' | 'not_adjusted_pending_appeal';
  /**
   * Contract 1.14.0 (thread 082). MyFantasyLeague public-aggregate ADP proxy,
   * NOT this league's own draft history -- see `RawBoard.adp_source_note` for
   * the full caveat (population, full-PPR-vs-this-league's-half-PPR capture).
   * MFL only has an opinion on roughly the top ~230 players in a 10-team pull,
   * so most rows carry a real, honest null here -- never render `0`/`0%` for
   * an absent value, that is a different claim. `adp_source` travels with
   * every non-null value and must never be blended with a differently-sourced
   * ADP number (e.g. a future `ffc_*` source). Optional so a pre-1.14.0
   * export still parses.
   */
  adp?: number | null;
  adp_min_pick?: number | null;
  adp_max_pick?: number | null;
  adp_selected_pct?: number | null;
  adp_source?: 'mfl_proxy' | string | null;
}

export interface RawBoard {
  contract_version: string;
  generated_utc: string;
  /** Absent on the default league today; required on every artifact under a
   *  data/export/<league_id>/ subdirectory. See ui/data/league-registry.ts. */
  league_id?: string | null;
  season: number;
  board_source: string;
  consensus_source: string;
  consensus_source_count: number;
  consensus_source_note: string;
  /**
   * Contract 1.11.0 (ADR-051, thread 069). The scoring format the consensus
   * source rows confirmed at export time (read from `rankings.scoring_format`,
   * not hardcoded) -- e.g. "half_ppr". Null when the source carries no
   * confirmed format or more than one; optional so a pre-1.11.0 export still
   * parses. Either empty state renders as "unconfirmed", never a guess.
   */
  scoring_format?: string | null;
  scoring_format_note?: string;
  /**
   * Contract 1.13.0 (thread 074). The `FreshnessResult` `src/freshness.py` computes on every
   * board build -- `src/export_contract.py`'s `build_board_json` already ran this check
   * (`enforce_freshness=True` by default, raising `StaleSnapshotError` rather than returning a
   * stale board), it just wasn't attached to the returned dict before this bump. Optional so a
   * pre-1.13.0 export still parses. `snapshot_as_of_date`/`snapshot_age_days` are null together
   * iff the source/season has no rows at all.
   */
  snapshot_as_of_date?: string | null;
  snapshot_age_days?: number | null;
  snapshot_max_age_days?: number;
  snapshot_stale?: boolean;
  snapshot_freshness_note?: string;
  /**
   * Contract 1.14.0 (thread 082). `adp_source` is always `"mfl_proxy"` today
   * (or null if the whole board somehow ships with no ADP data at all).
   * `adp_source_note` is written for display -- render it verbatim rather
   * than summarising, it carries the caveats (proxy population, full-PPR
   * capture vs. this half-PPR league) that make this NOT this league's ADP.
   * Optional so a pre-1.14.0 export still parses.
   */
  adp_source?: string | null;
  adp_as_of_date?: string | null;
  adp_match_rate_note?: string;
  adp_source_note?: string;
  consensus_state: string;
  attribution_is_additive: boolean;
  attribution_identity: string;
  curve_fits: Record<Position, { r_squared: number; residual_sd: number; n_obs: number }>;
  curve_caveat: string;
  replacement_levels_used: Record<Position, number>;
  published_levels_compared_against: Record<Position, number>;
  def_supported: boolean;
  def_note: string;
  players: RawBoardPlayer[];
}

export interface RawLeague {
  contract_version: string;
  league_id?: string | null;
  /** Added contract 1.7.0 (ADR-041). Absent on an older export. */
  league_name?: string;
  /** Real export field (confirmed against data/export/league.json), not yet
   *  typed here before thread 058 -- e.g. "sleeper" | "espn" | "yahoo" |
   *  "other". Optional so an older export without it doesn't fail to parse. */
  platform?: string;
  /** Real export field, e.g. "snake". Optional for the same reason as platform. */
  draft_type?: string;
  teams: number;
  rounds: number;
  user_draft_slot: number;
  pick_sequence: number[];
  roster: {
    starters: Record<string, number>;
    flex_eligible: string[];
    bench: number;
    ir: number;
    kicker: boolean;
  };
  scoring: Record<string, unknown>;
  replacement_levels: Record<string, number>;
  replacement_levels_note: string;
  /**
   * Positions that start in this league but carry no replacement level on purpose,
   * added at contract 1.5.0. DEF is the only member and the exclusion is permanent
   * (ADR-039) -- see `reasonForMissingLevel` in league.ts before touching it.
   */
  positions_without_replacement_levels?: string[];
  positions_without_replacement_levels_note?: string;
  flex_split_assumption: Record<string, number>;
  flex_split_note: string;
  playoff: { teams: number; weeks: number[]; reseeding: boolean };
  trade_deadline: string;
  faab_budget: number;
}

export interface RawGlossary {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  terms: Record<string, { short_definition: string; long_explanation: string }>;
}

export interface RawNulls {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  preamble: string;
  findings: Array<{
    id: string;
    claim_tested: string;
    method: string;
    result: string;
    plain_language_summary: string;
  }>;
}

export interface RawStrategySigma {
  sigma: number;
  mean_roster_points: number;
  p_top4: number;
  margin_vs_baseline: number | null;
  ci_low: number | null;
  ci_high: number | null;
  seasons_positive: number | null;
  sign_test_p: number | null;
  per_season_margin: Record<string, number> | null;
  simulation_se: number;
}

export interface RawStrategies {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  baseline: string;
  seasons: number[];
  simulations_per_cell: number;
  seed: number;
  sigma_values: number[];
  power_floor: {
    n_seasons: number;
    smallest_attainable_two_sided_p: number;
    plain_english: string;
  };
  lineup_assumption: string;
  strategies: Array<{
    name: string;
    is_baseline: boolean;
    by_sigma: RawStrategySigma[];
    verdict: string;
  }>;
}

/**
 * One opponent's profile. Every field beyond team_name/draft_slot/known_picks is
 * nullable because it genuinely is null for most opponents in this league: the
 * backend's own coverage_warning says so (7 of 9 have no behavioural data at
 * all). `data_status` names exactly what's known and how, per player -- this is
 * the field this screen leans on instead of inventing confidence where none exists.
 */
export interface RawOpponent {
  /** Null for slots with no supplied identity -- 7 of 9 in the real export.
   *  Render the slot number, never a blank or a fabricated name. */
  team_name: string | null;
  draft_slot_2026: number;
  draft_slot_2025: number | null;
  known_picks_2026: number[];
  positional_tendencies: string | null;
  first_pick_by_position: string | null;
  consensus_tracking_behaviour: string | null;
  notes: string;
  cited_2025_picks: number[];
  holds_picks_19_to_22: boolean;
  data_status: string;
}

export interface RawOpponents {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  user_draft_slot: number;
  coverage_warning: string;
  opponents: RawOpponent[];
}

/**
 * Full league rosters -- what each team HAS (drafted, by slot) and what it still
 * NEEDS (required minus filled, pure arithmetic). Added contract 1.8.0, answering
 * `docs/handoffs/016-league-rosters-endpoint.md`. Deliberately mechanical: it does
 * not model or guess what a team is likely to draft next -- see the artifact's own
 * `inference_scope_note`. For behavioural/tendency context, `opponents.json` is
 * the separate, much sparser artifact.
 *
 * Optional on `Dataset`: only the default league carries it today, and an older
 * league export (any of the pre-1.8.0 config-matrix directories) will not have
 * this file at all -- absence is a real state (`rosters: null`), not an error.
 */
export interface RawRosterSlotGroup {
  required: number;
  filled: number;
  players: string[];
}

export interface RawRosterFlexGroup extends RawRosterSlotGroup {
  eligible_positions: string[];
}

export interface RawRoster {
  team_slot: number;
  is_user: boolean;
  team_name: string | null;
  roster_slots: {
    starters: Record<string, RawRosterSlotGroup>;
    flex: RawRosterFlexGroup;
    bench: RawRosterSlotGroup;
    ir: RawRosterSlotGroup & { note?: string };
  };
  needs: Record<string, number>;
  players: string[];
}

export interface RawRosters {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  season: number;
  teams: number;
  draft_state: string;
  picks_ingested: number;
  unresolved_position_count: number;
  data_source_note: string;
  inference_scope_note: string;
  rosters: RawRoster[];
}

/**
 * The news feed contract. Nothing produces this yet -- there is no ingested corpus
 * anywhere in the repo, so the lane resolves to zero items and says so.
 *
 * There is deliberately no body-text field. News prose is licensed; storing or
 * re-rendering it is not something this app will do. A headline, an attribution and
 * a link out is the whole of what gets kept.
 */
export interface FeedItem {
  headline: string;
  source_name: string;
  url: string;
  /** ISO 8601. Drives the staleness rule -- see STALE_AFTER_MS. */
  published_at: string;
  /** Board player ids this item attaches to. */
  player_ids: number[];
  retrieved_at: string;
}

export interface RawFeed {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  items: FeedItem[];
}

export interface RawAvailabilitySigma {
  sigma_5: number;
  sigma_10: number;
  sigma_20: number;
}

/**
 * Availability probabilities: how likely a player (or the best player left in a
 * tier) is to survive to a given pick, simulated against this league's format.
 *
 * Both `by_player` and `by_tier` are keyed down to a pick number (one of the
 * user's own picks, as a string key), holding one RawAvailabilitySigma per pick --
 * a reading at each of the three sigma settings the model was run at, never a
 * single collapsed number. There is no `noise_band` field anywhere in this
 * artifact; the three-sigma sweep is the shape, not a placeholder for one.
 */
export interface RawAvailability {
  contract_version: string;
  generated_utc: string;
  league_id?: string | null;
  /** Player name -> pick number (string) -> sigma triple. Covers the top players
   *  simulated, not the full board -- absence means "not simulated", not zero. */
  by_player: Record<string, Record<string, RawAvailabilitySigma>>;
  /** Position -> tier label -> pick number (string) -> sigma triple. */
  by_tier: Record<string, Record<string, Record<string, RawAvailabilitySigma>>>;
  metadata: {
    season: number;
    simulations_per_setting: number;
    sigma_values: number[];
    sigma_plain_english: string;
    user_draft_slot: number;
    user_picks: number[];
    reliability_note: string;
    /** True: by_player/by_tier are averages over every possible draft, not
     *  conditioned on picks actually made. See `marginals_note`. */
    figures_are_unconditional_marginals: boolean;
    marginals_note: string;
  };
  /**
   * Parameters for a future client-side simulator that would recompute
   * availability conditioned on real picks made so far, instead of these
   * unconditional Prep-mode marginals. Not consumed by this build -- Draft mode
   * (which would condition on live picks) is explicitly out of scope for now.
   */
  client_simulation_parameters: {
    ranking_sources: Array<{ name: string; weight: number }>;
    mechanical_need_targets: Record<string, number>;
    mechanical_need_targets_note: string;
    max_at_position: Record<string, number>;
    need_penalty_per_surplus: number;
    room_noise_drawn_once_per_draft: boolean;
    room_noise_note: string;
    algorithm_note: string;
  };
}

export interface ArtifactManifestEntry {
  file: string;
  contract_version: string | null;
  generated_utc: string | null;
  /** Null for the default league today -- the backend has not added `league_id`
   *  to any default-league artifact, only to the convention for additional
   *  leagues under data/export/<league_id>/. */
  league_id: string | null;
  /**
   * `name@contract_version+generated_utc`, or `name@unversioned` when the artifact
   * carries no timestamp. league.json has no `generated_utc`, so it takes the fallback.
   */
  run_id: string;
}

/** One additional league's artifact set, from public/data/_leagues.json. Empty
 *  today -- no backend league directory exists yet -- but the shape is real, not
 *  speculative: sync-exports.mjs writes it from whatever it actually finds under
 *  data/export/<id>/. */
export interface LeagueManifestEntry {
  id: string;
  /** league.json's own league_name where available (contract 1.7.0+), else the id. */
  label: string;
  artifacts: Record<string, ArtifactManifestEntry>;
}

export interface LeaguesManifest {
  leagues: LeagueManifestEntry[];
}

export interface Manifest {
  synced_utc: string;
  artifacts: Record<string, ArtifactManifestEntry>;
}

/**
 * `weekly_finishes.json` / `season_stats.json` (thread 017/039, `src/export_history.py`).
 * Outside `CONTRACT_VERSION` -- own `export_version`, unprefixed path only, same for
 * every league (see `ui/data/playerHistory.ts` for the fetch/join layer). Keyed by
 * nflverse `player_id` (a gsis id) -- joined to a board row via
 * `RawBoardPlayer.player_id_gsis`, populated as of thread 052/ADR-048.
 */
export interface RawWeeklyFinishWeek {
  week: number;
  /** `RANK()` over positional fantasy_points_ppr that week; ties share a rank. Null
   *  with `bye: false` means no recorded stat line -- not a confirmed inactive/roster
   *  lookup, just the absence of a row (see the artifact's own no_row_semantics_note). */
  finish: number | null;
  bye: boolean;
}

export interface RawWeeklyFinishSeason {
  target_data_unavailable: boolean;
  weeks: RawWeeklyFinishWeek[];
}

export interface RawWeeklyFinishesPlayer {
  player_id: string;
  seasons: Record<string, RawWeeklyFinishSeason>;
}

export interface RawWeeklyFinishes {
  export_version: string;
  generated_utc: string;
  note: string;
  no_row_semantics_note: string;
  players: RawWeeklyFinishesPlayer[];
}

export interface RawSeasonStatSeason {
  year: number;
  games: number;
  /** Null, with `target_data_unavailable: true`, for 2003-2008 -- charting-coverage
   *  gap upstream, never a fabricated 0. */
  targets: number | null;
  target_data_unavailable: boolean;
  receptions: number;
  receiving_yards: number;
  receiving_tds: number;
  rushing_yards: number;
  rushing_tds: number;
  fantasy_points_ppr: number;
}

export interface RawSeasonStatsPlayer {
  player_id: string;
  seasons: RawSeasonStatSeason[];
}

export interface RawSeasonStats {
  export_version: string;
  generated_utc: string;
  note: string;
  players: RawSeasonStatsPlayer[];
}

/**
 * `player_descriptions.json` (`src/player_descriptions.py`, ADR-044). AI-generated,
 * display-only prose -- "Never a Fact, never a model input" per the artifact's own
 * `note`. Own `export_version`, no `contract_version`/`league_id`: primary league
 * only today (see `docs/CURRENT-STATE.md` open item 5), not part of the per-league
 * six-artifact set. A player absent from `players` has an UNDETERMINED archetype;
 * render nothing for them rather than a placeholder.
 */
export interface RawPlayerDescription {
  player_id: string;
  player_name: string;
  season: number;
  position: Position;
  archetype: string;
  confidence: 'high' | 'medium' | 'low' | string;
  description: string;
  license_tag: string;
  generated_at: string;
  source_stats: {
    carry_share: number;
    target_share: number;
    offense_pct: number;
    adot: number;
    games_qualified: number;
  };
}

export interface RawPlayerDescriptions {
  export_version: string;
  license_tag: string;
  season: number;
  generated_utc: string;
  note: string;
  players: RawPlayerDescription[];
}
