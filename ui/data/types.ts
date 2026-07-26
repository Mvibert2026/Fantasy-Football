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
}

export interface RawBoard {
  contract_version: string;
  generated_utc: string;
  season: number;
  board_source: string;
  consensus_source: string;
  consensus_source_count: number;
  consensus_source_note: string;
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
  flex_split_assumption: Record<string, number>;
  flex_split_note: string;
  playoff: { teams: number; weeks: number[]; reseeding: boolean };
  trade_deadline: string;
  faab_budget: number;
}

export interface RawGlossary {
  contract_version: string;
  generated_utc: string;
  terms: Record<string, { short_definition: string; long_explanation: string }>;
}

export interface RawNulls {
  contract_version: string;
  generated_utc: string;
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
  items: FeedItem[];
}

export interface ArtifactManifestEntry {
  file: string;
  contract_version: string | null;
  generated_utc: string | null;
  /**
   * `name@contract_version+generated_utc`, or `name@unversioned` when the artifact
   * carries no timestamp. league.json has no `generated_utc`, so it takes the fallback.
   */
  run_id: string;
}

export interface Manifest {
  synced_utc: string;
  artifacts: Record<string, ArtifactManifestEntry>;
}
