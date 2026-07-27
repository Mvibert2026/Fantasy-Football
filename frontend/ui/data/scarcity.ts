import type { BoardRow } from './board';
import type { DraftPickRecord } from './draft';
import { takenPlayerIds } from './draft';
import type { Dataset } from './load';
import { playerAvailabilityAtPick } from './availability';
import { integer } from '../lib/format';

/**
 * Position scarcity, FRONTEND-SPEC.md §5.5. Everything here is arithmetic over
 * the board and the picks logged so far -- no simulation, no new data source.
 *
 * Thread 058 section A: DEF is now one of the positions this can be asked
 * about, and board.json carries zero DEF players (no DST data is ingested --
 * ADR-039, board.json:def_note). `dataAvailable` (= total > 0) is the gate: a
 * position with no board rows at all gets an honest "not computed" null on
 * every derived field below, never a fabricated 0 or ±0. Conflating "0 players
 * gone, exactly on pace" with "we have never tracked this position" is exactly
 * the substitution Principle #2 forbids, and it is a live risk here because the
 * arithmetic (`0 - 0 = 0`) produces a plausible-looking zero either way.
 */

export interface PositionScarcity {
  pos: string;
  total: number;
  remaining: number;
  gone: number;
  /** True only when the board carries at least one player at this position.
   *  False for DEF today -- every field below is an honest null in that case,
   *  not a computed zero. */
  dataAvailable: boolean;
  /** Consensus-implied count gone by `currentPick`. Null when there is no
   *  board data for the position at all. */
  expected: number | null;
  /** + = going faster than the market (consensus) expected. Null, not 0, when
   *  there is no board data for the position. */
  pace: number | null;
  tier1Remaining: number | null;
  tier2Remaining: number | null;
  /** Count of remaining players under 50% to reach nextUserPick, per the real
   *  Prep-mode marginal (sigma-10) -- absent players (outside the simulated
   *  pool) are not counted as "under 50%", since that isn't known either way.
   *  Null (not 0) when there is no board data, or no next user pick to probe. */
  under50ByNext: number | null;
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
    const dataAvailable = atPos.length > 0;
    const remaining = atPos.filter((r) => !taken.has(r.id));
    const gone = atPos.length - remaining.length;
    const expected = dataAvailable
      ? atPos.filter((r) => r.consensusRank.kind === 'present' && r.consensusRank.value < currentPick).length
      : null;
    const tier1Remaining = dataAvailable
      ? remaining.filter((r) => r.tierLabel.kind === 'present' && r.tierLabel.value === 'T1').length
      : null;
    const tier2Remaining = dataAvailable
      ? remaining.filter((r) => r.tierLabel.kind === 'present' && r.tierLabel.value === 'T2').length
      : null;
    const under50ByNext =
      !dataAvailable || nextUserPick === null
        ? null
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
      dataAvailable,
      expected,
      pace: dataAvailable && expected !== null ? gone - expected : null,
      tier1Remaining,
      tier2Remaining,
      under50ByNext,
      startablePool: (startersByPosition[pos] ?? 0) * teams,
    };
  });
}

/**
 * Depletion warning: the one derived urgency claim this product makes. Fires
 * when every remaining tier-1 player at a position sits under 50% to reach the
 * user's next pick. Both inputs are honest nulls, not just `nextUserPick`, so a
 * position with no board data can never trip this.
 */
export function depletionWarning(s: PositionScarcity, nextUserPick: number | null): string | null {
  if (nextUserPick === null) return null;
  if (s.tier1Remaining === null || s.under50ByNext === null) return null;
  if (s.tier1Remaining > 0 && s.under50ByNext >= s.tier1Remaining) {
    return `All ${s.tier1Remaining} remaining tier-1 ${s.pos} sit under 50% to reach pick ${nextUserPick}. If you want one, this is the turn.`;
  }
  return null;
}

/**
 * Thread 058 section A item 1: "a bare signed integer under a draft clock is a
 * guess." `pace` is `gone - expected`; positive means MORE players at this
 * position have been taken than the market expected by this pick (the
 * position is depleting faster than consensus), negative means fewer have.
 * Rendered as an explicit phrase rather than a bare `+2`/`-1` so the direction
 * of the claim never has to be inferred -- per the founder's own suggested
 * remedy ("label it, or render it as an explicit phrase").
 */
export function paceLabel(pace: number | null): string {
  if (pace === null) return 'pace not yet computed';
  if (pace === 0) return 'on pace';
  return pace > 0 ? `${integer(pace)} ahead of pace` : `${integer(Math.abs(pace))} behind pace`;
}

/**
 * Tier-depletion line, thread 058 section A item 2: "tier 1 gone · tier 2: 1
 * left" -- what actually determines whether the user must act, as opposed to
 * a raw remaining count. Null when the position has no board data at all
 * (DEF) -- the caller renders the position's single collapsed null line
 * instead of this.
 */
export function tierDepletionLine(s: PositionScarcity): string | null {
  if (!s.dataAvailable || s.tier1Remaining === null) return null;
  if (s.tier1Remaining === 0 && s.tier2Remaining === 0) return 'tiers 1–2 gone';
  if (s.tier1Remaining === 0) return `tier 1 gone · tier 2: ${s.tier2Remaining ?? '—'} left`;
  return `tier 1: ${s.tier1Remaining} left`;
}

/**
 * "N <50% by pick X" line, thread 058 section A item 3 -- the product's core
 * survival-odds number applied at the position level, shown per-position
 * whether or not it crosses the depletion-warning threshold. Distinct honest
 * states: no board data at all, vs. board data but no further pick of the
 * user's to probe against.
 */
export function under50Line(s: PositionScarcity, nextUserPick: number | null): string | null {
  if (!s.dataAvailable) return null;
  if (nextUserPick === null) return 'not yet — no further pick of yours this draft';
  if (s.under50ByNext === null) return '—';
  return `${s.under50ByNext} <50% by ${nextUserPick}`;
}

/**
 * Thread 058 section A item 5: order the panel by urgency rather than a fixed
 * QB/RB/WR/TE/DEF order, so the position that most needs a decision sits at
 * the top. FRONTEND-SPEC.md §5.5 does not define a formula for this (confirmed
 * by reading the section in full) -- this ordering is this session's own
 * reasonable choice, not a backtested or spec-mandated one, exactly the same
 * status as the existing recommendation score in recommendation.ts, and open
 * to being overridden.
 *
 * Rule: positions with no board data sink to the bottom (nothing to act on);
 * among the rest, fewer remaining tier-1 players is more urgent, ties broken
 * by more players about to drop under 50% survival, then by pace.
 */
export function orderByUrgency(list: PositionScarcity[]): PositionScarcity[] {
  return [...list].sort((a, b) => {
    if (a.dataAvailable !== b.dataAvailable) return a.dataAvailable ? -1 : 1;
    const aT1 = a.tier1Remaining ?? Infinity;
    const bT1 = b.tier1Remaining ?? Infinity;
    if (aT1 !== bT1) return aT1 - bT1;
    const aU = a.under50ByNext ?? -Infinity;
    const bU = b.under50ByNext ?? -Infinity;
    if (aU !== bU) return bU - aU;
    const aP = a.pace ?? 0;
    const bP = b.pace ?? 0;
    return bP - aP;
  });
}
