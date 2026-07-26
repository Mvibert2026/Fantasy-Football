import { absent, present, type Cell } from './cell';
import type { Dataset } from './load';
import { runIdOf } from './load';
import type { RawAvailabilitySigma } from './types';

/**
 * Availability probabilities, read from availability.json.
 *
 * The model dropped the prior-year-repeat assumption entirely at contract 1.6.0
 * (ADR-033/034) -- these figures are no longer circular, which is what makes this
 * screen buildable now. Two things stay true regardless:
 *
 *   - There is no single `noise_band` scalar anywhere in this artifact. The
 *     backend confirmed the field has never existed in any version of this
 *     project. The real shape is a three-setting sigma sweep (5/10/20); every
 *     figure here is read at all three, never collapsed to one number.
 *   - `by_player`/`by_tier` are unconditional marginals -- averaged over every
 *     possible draft, not conditioned on picks actually made. That is
 *     `metadata.figures_are_unconditional_marginals` and `metadata.marginals_note`,
 *     both surfaced verbatim on screen rather than left in a tooltip. Conditioning
 *     on real picks would need Draft mode's live simulator
 *     (`client_simulation_parameters`), which is out of scope for this build.
 */

export interface SigmaCell {
  sigma5: Cell<number>;
  sigma10: Cell<number>;
  sigma20: Cell<number>;
}

export interface AvailabilityMeta {
  season: Cell<number>;
  simulationsPerSetting: Cell<number>;
  sigmaValues: number[];
  sigmaPlainEnglish: string;
  userDraftSlot: Cell<number>;
  userPicks: number[];
  reliabilityNote: string;
  marginalsNote: string;
  figuresAreUnconditionalMarginals: boolean;
  algorithmNote: string;
  roomNoiseNote: string;
  mechanicalNeedTargets: Record<string, number>;
  maxAtPosition: Record<string, number>;
  rankingSources: Array<{ name: string; weight: number }>;
}

export function buildAvailabilityMeta(data: Dataset): AvailabilityMeta {
  const runId = runIdOf(data.manifest, 'availability');
  const m = data.availability.metadata;
  const c = data.availability.client_simulation_parameters;
  return {
    season: present(m.season, 'availability.json:metadata.season', runId),
    simulationsPerSetting: present(
      m.simulations_per_setting,
      'availability.json:metadata.simulations_per_setting',
      runId,
    ),
    sigmaValues: m.sigma_values,
    sigmaPlainEnglish: m.sigma_plain_english,
    userDraftSlot: present(m.user_draft_slot, 'availability.json:metadata.user_draft_slot', runId),
    userPicks: m.user_picks,
    reliabilityNote: m.reliability_note,
    marginalsNote: m.marginals_note,
    figuresAreUnconditionalMarginals: m.figures_are_unconditional_marginals,
    algorithmNote: c.algorithm_note,
    roomNoiseNote: c.room_noise_note,
    mechanicalNeedTargets: c.mechanical_need_targets,
    maxAtPosition: c.max_at_position,
    rankingSources: c.ranking_sources,
  };
}

function sigmaCellFrom(
  entry: RawAvailabilitySigma | undefined,
  path: string,
  runId: string,
  reason: string,
): SigmaCell {
  if (!entry) {
    return {
      sigma5: absent(`${path}.sigma_5`, runId, reason),
      sigma10: absent(`${path}.sigma_10`, runId, reason),
      sigma20: absent(`${path}.sigma_20`, runId, reason),
    };
  }
  return {
    sigma5: present(entry.sigma_5, `${path}.sigma_5`, runId),
    sigma10: present(entry.sigma_10, `${path}.sigma_10`, runId),
    sigma20: present(entry.sigma_20, `${path}.sigma_20`, runId),
  };
}

/** How many of the top players availability.json actually simulated -- absence for
 *  anyone outside that pool is "not simulated", not "zero chance of survival". */
export function simulatedPlayerCount(data: Dataset): number {
  return Object.keys(data.availability.by_player).length;
}

export function playerAvailabilityAtPick(data: Dataset, playerName: string, pick: number): SigmaCell {
  const runId = runIdOf(data.manifest, 'availability');
  const path = `availability.json:by_player.${playerName}.${pick}`;
  const byPick = data.availability.by_player[playerName];
  if (!byPick) {
    return sigmaCellFrom(
      undefined,
      path,
      runId,
      `${playerName} is outside the ${simulatedPlayerCount(data)} players availability.json simulated.`,
    );
  }
  return sigmaCellFrom(byPick[String(pick)], path, runId, `No availability figure recorded for pick ${pick}.`);
}

export function tierPositions(data: Dataset): string[] {
  return Object.keys(data.availability.by_tier);
}

export function tiersForPosition(data: Dataset, position: string): string[] {
  return Object.keys(data.availability.by_tier[position] ?? {});
}

export function tierAvailabilityAtPick(data: Dataset, position: string, tier: string, pick: number): SigmaCell {
  const runId = runIdOf(data.manifest, 'availability');
  const path = `availability.json:by_tier.${position}.${tier}.${pick}`;
  const byPick = data.availability.by_tier[position]?.[tier];
  if (!byPick) {
    return sigmaCellFrom(undefined, path, runId, `No availability data simulated for ${position} ${tier}.`);
  }
  return sigmaCellFrom(byPick[String(pick)], path, runId, `No availability figure recorded for pick ${pick}.`);
}
