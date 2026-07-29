import { beforeEach, describe, expect, it } from 'vitest';
import { clearSlotOverride, loadSlotOverride, randomSlot, saveSlotOverride } from '../data/draftSlot';

/**
 * FR-034: the draft-slot override store. Same shape/lifecycle contract as
 * ui/data/draft.ts's DraftState store -- per-league key, tolerant of a missing or
 * corrupt value, never invents a slot on its own.
 */

beforeEach(() => {
  localStorage.clear();
});

describe('draftSlot storage', () => {
  it('returns null (no override) when nothing has been stored for this league', () => {
    expect(loadSlotOverride('primary')).toBeNull();
  });

  it('round-trips a saved override', () => {
    saveSlotOverride('primary', 7);
    expect(loadSlotOverride('primary')).toBe(7);
  });

  it('keeps overrides scoped per league -- setting one league never leaks into another', () => {
    saveSlotOverride('primary', 3);
    saveSlotOverride('ethans_expert_league', 9);
    expect(loadSlotOverride('primary')).toBe(3);
    expect(loadSlotOverride('ethans_expert_league')).toBe(9);
  });

  it('clearing an override falls back to null (the caller then falls back to the sourced slot, not blank)', () => {
    saveSlotOverride('primary', 5);
    clearSlotOverride('primary');
    expect(loadSlotOverride('primary')).toBeNull();
  });

  it('clearing one league leaves a different league\'s override untouched', () => {
    saveSlotOverride('primary', 3);
    saveSlotOverride('ethans_expert_league', 9);
    clearSlotOverride('primary');
    expect(loadSlotOverride('primary')).toBeNull();
    expect(loadSlotOverride('ethans_expert_league')).toBe(9);
  });

  it('treats a corrupt stored value as no override, never a crash or a guessed number', () => {
    localStorage.setItem('prep.draftSlot.primary', 'not-a-number');
    expect(loadSlotOverride('primary')).toBeNull();
  });

  it('treats a stored 0 or negative slot as invalid -- slots are 1-indexed', () => {
    localStorage.setItem('prep.draftSlot.primary', '0');
    expect(loadSlotOverride('primary')).toBeNull();
    localStorage.setItem('prep.draftSlot.primary', '-2');
    expect(loadSlotOverride('primary')).toBeNull();
  });
});

describe('randomSlot', () => {
  it('always returns an integer in [1, teams]', () => {
    for (let i = 0; i < 200; i++) {
      const s = randomSlot(10);
      expect(Number.isInteger(s)).toBe(true);
      expect(s).toBeGreaterThanOrEqual(1);
      expect(s).toBeLessThanOrEqual(10);
    }
  });

  it('handles a 1-team edge case without ever returning anything but 1', () => {
    for (let i = 0; i < 20; i++) {
      expect(randomSlot(1)).toBe(1);
    }
  });
});
