import { describe, expect, it } from 'vitest';
import { buildRows, ciTargetFor } from '../data/board';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { loadDatasetFromDisk } from './helpers';

/**
 * Founder, 2026-07-30: "what is in the parenthesis here -- it's a range, but
 * the projection isn't in it?" Measured against the live export: of the 145
 * players carrying an interval, 145/145 have that interval inside their own
 * VBD, and 0/145 inside `projected_points`. `ci_applies_to` says "vbd" on
 * every one of them -- every UI consumer paired the interval with
 * `projected_points` anyway.
 *
 * `ciTargetFor` (`ui/data/board.ts`) is the one place that pairing decision
 * gets made now. These tests are the regression guard the fix was required to
 * ship with: they fail if any future change makes the resolved target
 * diverge from `ci_applies_to`, including for quantities this app doesn't
 * see in the live export today.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

/** Real dataset with player 0's CI fields overridden, same idiom
 *  `suspension-and-scoring-format.test.tsx` uses for suspension fields. */
function withCiOverride(overrides: Partial<RawBoardPlayer>): Dataset {
  return {
    ...data,
    board: {
      ...data.board,
      players: data.board.players.map((p, i) => (i === 0 ? { ...p, ...overrides } : p)),
    },
  } as Dataset;
}

describe('ciTargetFor', () => {
  it('measured against the live export: every row with an interval has ci_applies_to "vbd", and VBD (not projected_points) is what it actually brackets', () => {
    const withInterval = data.board.players.filter((p) => p.ci_low !== null && p.ci_high !== null);
    expect(withInterval.length).toBeGreaterThan(0); // guard the fixture
    for (const p of withInterval) {
      expect(p.ci_applies_to).toBe('vbd');
      expect(p.vbd).toBeGreaterThanOrEqual(p.ci_low!);
      expect(p.vbd).toBeLessThanOrEqual(p.ci_high!);
      // The regression this whole fix exists for: the projection is NOT
      // inside its own row's interval.
      const inProjection = p.projected_points >= p.ci_low! && p.projected_points <= p.ci_high!;
      expect(inProjection).toBe(false);
    }
  });

  it('resolves "vbd" to the VBD cell, carrying the real interval bounds', () => {
    const row = buildRows(withCiOverride({ ci_low: 10, ci_high: 20, ci_applies_to: 'vbd' }))[0]!;
    const target = ciTargetFor(row);
    expect(target.kind).toBe('known');
    if (target.kind !== 'known') throw new Error('unreachable');
    expect(target.quantity).toBe('vbd');
    expect(target.label).toBe('VBD');
    expect(target.cell).toBe(row.vbd);
  });

  it('resolves "projected_points" to the PROJ cell -- never assumed to always be "vbd"', () => {
    const row = buildRows(withCiOverride({ ci_low: 200, ci_high: 260, ci_applies_to: 'projected_points' }))[0]!;
    const target = ciTargetFor(row);
    expect(target.kind).toBe('known');
    if (target.kind !== 'known') throw new Error('unreachable');
    expect(target.quantity).toBe('projected_points');
    expect(target.label).toBe('PROJ');
    expect(target.cell).toBe(row.projectedPoints);
  });

  it('an unrecognized ci_applies_to value is an honest absence, not a silent fallback to VBD or PROJ', () => {
    const row = buildRows(withCiOverride({ ci_low: 5, ci_high: 9, ci_applies_to: 'snap_share' }))[0]!;
    const target = ciTargetFor(row);
    expect(target.kind).toBe('unrecognized');
    if (target.kind !== 'unrecognized') throw new Error('unreachable');
    expect(target.raw).toBe('snap_share');
  });

  it('no interval at all resolves to "none", not to a fabricated target', () => {
    const row = buildRows(withCiOverride({ ci_low: null, ci_high: null }))[0]!;
    expect(row.interval.kind).toBe('absent');
    expect(ciTargetFor(row)).toEqual({ kind: 'none' });
  });

  it('a live row (row 0 unmodified) resolves through ciTargetFor exactly as measured against the export', () => {
    const row = rows[0]!;
    const raw = data.board.players[0]!;
    const target = ciTargetFor(row);
    if (raw.ci_low === null || raw.ci_high === null) {
      expect(target.kind).toBe('none');
    } else {
      expect(target.kind).toBe('known');
      if (target.kind === 'known') expect(target.quantity).toBe(raw.ci_applies_to);
    }
  });
});
