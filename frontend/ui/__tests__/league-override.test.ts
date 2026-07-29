import { describe, expect, it } from 'vitest';
import { pickNumbersForSlot } from '../data/draft';
import { applyUserSlotOverride, buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-034: applyUserSlotOverride is the single seam every downstream consumer
 * (DraftRoom, PlayerDetail, Predictions, RoundGrid) reads through -- see its own
 * doc comment in ui/data/league.ts for why pickSequence has to be recomputed here,
 * not left as the backend's own value for the sourced slot.
 */

const data = loadDatasetFromDisk();
const base = buildLeagueConfig(data);
const teams = base.teams.kind === 'present' ? base.teams.value : 0;
const rounds = base.rounds.kind === 'present' ? base.rounds.value : 0;
const sourcedSlot = base.userSlot.kind === 'present' ? base.userSlot.value : 0;

describe('applyUserSlotOverride', () => {
  it('is a no-op when override is null', () => {
    const result = applyUserSlotOverride(base, null);
    expect(result).toBe(base);
  });

  it('leaves userSlotOverridden false and userSlot unchanged for a null override', () => {
    const result = applyUserSlotOverride(base, null);
    expect(result.userSlotOverridden).toBe(false);
    expect(result.userSlot).toEqual(base.userSlot);
  });

  it('applies a valid override: userSlot becomes the override value, userSlotOverridden is true', () => {
    const target = sourcedSlot === 1 ? 2 : 1; // guaranteed different from sourced
    const result = applyUserSlotOverride(base, target);
    expect(result.userSlotOverridden).toBe(true);
    expect(result.userSlot.kind).toBe('present');
    if (result.userSlot.kind === 'present') expect(result.userSlot.value).toBe(target);
  });

  it('keeps userSlotSourced pointing at the real league.json value, untouched by the override', () => {
    const target = sourcedSlot === 1 ? 2 : 1;
    const result = applyUserSlotOverride(base, target);
    expect(result.userSlotSourced).toEqual(base.userSlotSourced);
    expect(result.userSlotSourced.kind).toBe('present');
    if (result.userSlotSourced.kind === 'present') expect(result.userSlotSourced.value).toBe(sourcedSlot);
  });

  it('an override equal to the sourced slot is treated as no override at all (userSlotOverridden stays false)', () => {
    const result = applyUserSlotOverride(base, sourcedSlot);
    expect(result.userSlotOverridden).toBe(false);
  });

  it('rejects an out-of-range override (below 1 or above teams) as a no-op, never clamping or guessing', () => {
    expect(applyUserSlotOverride(base, 0)).toBe(base);
    expect(applyUserSlotOverride(base, -1)).toBe(base);
    expect(applyUserSlotOverride(base, teams + 1)).toBe(base);
  });

  it('rejects a non-integer override as a no-op', () => {
    expect(applyUserSlotOverride(base, 2.5)).toBe(base);
  });

  it(
    'recomputes pickSequence for the overridden slot using the exact same snake formula as ' +
      'pickNumbersForSlot -- the field DraftRoom\'s MY PICKS panel and RoundGrid read directly',
    () => {
      const target = sourcedSlot === 1 ? 2 : 1;
      const result = applyUserSlotOverride(base, target);
      const expected = pickNumbersForSlot(teams, target, rounds);
      expect(result.pickSequence.kind).toBe('present');
      if (result.pickSequence.kind === 'present') {
        expect(result.pickSequence.value).toEqual(expected);
        // And, critically, this must differ from the sourced slot's own sequence --
        // otherwise RoundGrid would silently keep highlighting someone else's picks.
        expect(result.pickSequence.value).not.toEqual(base.pickSequence.kind === 'present' ? base.pickSequence.value : []);
      }
    },
  );

  it('marks the recomputed pickSequence as derived, not as league.json:pick_sequence -- it is not that field anymore', () => {
    const target = sourcedSlot === 1 ? 2 : 1;
    const result = applyUserSlotOverride(base, target);
    expect(result.pickSequence.kind).toBe('present');
    if (result.pickSequence.kind === 'present') {
      expect(result.pickSequence.path).not.toBe('league.json:pick_sequence');
    }
  });
});
