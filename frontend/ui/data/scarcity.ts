import type { BoardRow } from './board';
import type { DraftPickRecord } from './draft';
import { takenPlayerIds } from './draft';
import type { Dataset } from './load';
import { playerAvailabilityAtPick } from './availability';

/**
 * Position scarcity, FRONTEND-SPEC.md §5.5. Everything here is arithmetic over
 * the board and the picks logged so far -- no simulation, no new data source.
 */

export interface PositionScarcity {
  pos: string;
  total: number;
  remaining: number;
  gone: number;
  /** + = going faster than the market (consensus) expected. */
  pace: number;
  tier1Remaining: number;
  /** Count of remaining players under 50% to reach nextUserPick, per the real
   *  Prep-mode marginal (sigma-10) -- absent players (outside the simulated
   *  pool) are not counted as "under 50%", since that isn't known either way. */
  under50ByNext: number;
  startablePool: number;
}

export function positionScarcity(
  data: Dataset,
  rows: BoardRow[],
  picks: DraftPickRecord[],
  currentPick: number,
  nextUserPick: number | null,
  positions: readonly string[],
  startersByPosition: Record<string, number>,
  teams: number,
): PositionScarcity[] {
  const taken = takenPlayerIds(picks);

  return positions.map((pos) => {
    const atPos = rows.filter((r) => r.raw.position === pos);
    const remaining = atPos.filter((r) => !taken.has(r.id));
    const gone = atPos.length - remaining.length;
    const expected = atPos.filter(
      (r) => r.consensusRank.kind === 'present' && r.consensusRank.value < currentPick,
    ).length;
    const tier1Remaining = remaining.filter((r) => r.tierLabel.kind === 'present' && r.tierLabel.value === 'T1').length;
    const under50ByNext =
      nextUserPick === null
        ? 0
        : remaining.filter((r) => {
            if (r.name.kind !== 'present') return false;
            const cell = playerAvailabilityAtPick(data, r.name.value, nextUserPick);
            return cell.sigma10.kind === 'present' && cell.sigma10.value < 0.5;
          }).length;

    return {
      pos,
      total: atPos.length,
      remaining: remaining.length,
      gone,
      pace: gone - expected,
      tier1Remaining,
      under50ByNext,
      startablePool: (startersByPosition[pos] ?? 0) * teams,
    };
  });
}

/**
 * Depletion warning: the one derived urgency claim this product makes. Fires
 * when every remaining tier-1 player at a position sits under 50% to reach the
 * user's next pick.
 */
export function depletionWarning(s: PositionScarcity, nextUserPick: number | null): string | null {
  if (nextUserPick === null) return null;
  if (s.tier1Remaining > 0 && s.under50ByNext >= s.tier1Remaining) {
    return `All ${s.tier1Remaining} remaining tier-1 ${s.pos} sit under 50% to reach pick ${nextUserPick}. If you want one, this is the turn.`;
  }
  return null;
}
