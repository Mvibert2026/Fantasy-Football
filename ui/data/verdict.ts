import type { BoardRow } from './board';
import { decimal, integer } from '../lib/format';
import type { LiveAvailabilityResult } from './liveAvailability';
import { freqText } from './liveAvailability';

/**
 * The verdict line, generated -- never hand-written -- per FRONTEND-SPEC.md §5.6.
 * Three clauses, fixed order, joined with " · " and closed with a period. No
 * adjectives, no ranking language, nothing that isn't arithmetic on a named
 * field: it has to work for all ~378 players with zero hand-written copy, and
 * every clause below traces to a real Cell.
 */

/** Clause 1 -- structure: position within tier, and how many remain in it. */
function structureClause(row: BoardRow, rows: BoardRow[]): string {
  if (row.tierLabel.kind !== 'present') return 'Tier not assigned for this player.';
  const tier = row.tierLabel.value;
  const tierPeers = rows.filter(
    (r) => r.raw.position === row.raw.position && r.tierLabel.kind === 'present' && r.tierLabel.value === tier,
  );
  const positionInTier = tierPeers.findIndex((r) => r.id === row.id) + 1;
  const n = tierPeers.length;
  const tierNum = tier.replace('T', '');

  if (n === 1) return `The only ${row.raw.position} left in tier ${tierNum}`;
  if (positionInTier === 1) return `Top of tier ${tierNum} at ${row.raw.position}, ${integer(n)} in the tier`;
  if (positionInTier === n) return `Last of ${integer(n)} in tier ${tierNum} at ${row.raw.position}`;
  return `${integer(positionInTier)} of ${integer(n)} in tier ${tierNum} at ${row.raw.position}`;
}

/** Clause 2 -- cost of waiting: live_p with frequency phrasing, or the baseline
 *  with an explicit "no live adjustment yet" caveat, or a stale notice. */
function costOfWaitingClause(avail: LiveAvailabilityResult | null, targetPick: number | null, stale: boolean): string {
  if (stale) return 'availability is stale for this league, so waiting is unpriced';
  if (!avail || targetPick === null) return 'no upcoming pick to price waiting against';
  if (avail.live !== null) {
    return `${integer(avail.live * 100)}% to reach your pick at ${integer(targetPick)} (${freqText(avail.live)})`;
  }
  if (avail.baseline.kind === 'present') {
    return `${integer(avail.baseline.value * 100)}% to reach your pick at ${integer(targetPick)} on the baseline, with no live adjustment yet`;
  }
  return 'no availability figure for this player, so waiting is unpriced';
}

/** Clause 3 -- value over the alternative: VBD gap to the next player at the position. */
function valueClause(row: BoardRow, rows: BoardRow[]): string {
  if (row.vbd.kind !== 'present') return 'no projection, so this is a rank-and-availability call only';
  const nextAtPosition = rows
    .filter(
      (r) =>
        r.raw.position === row.raw.position &&
        r.vbd.kind === 'present' &&
        r.overallRank.kind === 'present' &&
        row.overallRank.kind === 'present' &&
        r.overallRank.value > row.overallRank.value,
    )
    .sort((a, b) => (a.overallRank as { value: number }).value - (b.overallRank as { value: number }).value)[0];
  if (!nextAtPosition || nextAtPosition.vbd.kind !== 'present') {
    return `${decimal(row.vbd.value)} VBD points, the last ${row.raw.position} projected on this board`;
  }
  const gap = row.vbd.value - nextAtPosition.vbd.value;
  const nextName = nextAtPosition.name.kind === 'present' ? nextAtPosition.name.value : 'the next player';
  return `${decimal(gap)} VBD points clear of ${nextName}, the next ${row.raw.position} on the board`;
}

export function verdictLine(
  row: BoardRow,
  rows: BoardRow[],
  avail: LiveAvailabilityResult | null,
  targetPick: number | null,
  stale: boolean,
): string {
  const clauses = [
    structureClause(row, rows),
    costOfWaitingClause(avail, targetPick, stale),
    valueClause(row, rows),
  ];
  return `${clauses.join(' · ')}.`;
}
