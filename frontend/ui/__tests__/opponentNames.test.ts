import { beforeEach, describe, expect, it } from 'vitest';
import { clearOpponentName, loadOpponentNames, saveOpponentName } from '../data/opponentNames';

/**
 * FR-036: typed opponent team names. Names only, local, per-league -- see the
 * module doc in ui/data/opponentNames.ts. These tests cover the storage layer;
 * ui/__tests__/opponents.test.tsx covers the rendered supplied-vs-derived distinction.
 */

beforeEach(() => {
  localStorage.clear();
});

describe('opponentNames storage', () => {
  it('returns an empty map when nothing has been typed for this league', () => {
    expect(loadOpponentNames('primary')).toEqual({});
  });

  it('round-trips a saved name for a slot', () => {
    saveOpponentName('primary', 4, 'The Testers');
    expect(loadOpponentNames('primary')).toEqual({ 4: 'The Testers' });
  });

  it('keeps names scoped per league -- the exact leak FR-036 rules out', () => {
    saveOpponentName('primary', 4, 'Primary Team');
    saveOpponentName('ethans_expert_league', 4, 'Ethan Team');
    expect(loadOpponentNames('primary')).toEqual({ 4: 'Primary Team' });
    expect(loadOpponentNames('ethans_expert_league')).toEqual({ 4: 'Ethan Team' });
  });

  it('supports multiple named slots in the same league', () => {
    saveOpponentName('primary', 1, 'Team One');
    saveOpponentName('primary', 5, 'Team Five');
    expect(loadOpponentNames('primary')).toEqual({ 1: 'Team One', 5: 'Team Five' });
  });

  it('trims whitespace around a typed name', () => {
    saveOpponentName('primary', 2, '  Padded Name  ');
    expect(loadOpponentNames('primary')).toEqual({ 2: 'Padded Name' });
  });

  it('treats saving an empty (or whitespace-only) name as clearing it, not storing a blank override', () => {
    saveOpponentName('primary', 3, 'Real Name');
    saveOpponentName('primary', 3, '   ');
    expect(loadOpponentNames('primary')).toEqual({});
  });

  it('clearOpponentName removes exactly the one slot, leaving siblings alone', () => {
    saveOpponentName('primary', 1, 'Team One');
    saveOpponentName('primary', 2, 'Team Two');
    clearOpponentName('primary', 1);
    expect(loadOpponentNames('primary')).toEqual({ 2: 'Team Two' });
  });

  it('clearing a slot that was never set is a no-op, not an error', () => {
    saveOpponentName('primary', 1, 'Team One');
    clearOpponentName('primary', 9);
    expect(loadOpponentNames('primary')).toEqual({ 1: 'Team One' });
  });

  it('ignores a corrupt stored value rather than crashing', () => {
    localStorage.setItem('prep.opponentNames.primary', 'not json');
    expect(loadOpponentNames('primary')).toEqual({});
  });

  it('drops a non-string or non-positive-integer-keyed entry from a hand-edited/corrupt blob', () => {
    localStorage.setItem(
      'prep.opponentNames.primary',
      JSON.stringify({ '1': 'Valid', '0': 'Invalid slot', abc: 'Not a number', '2': 42 }),
    );
    expect(loadOpponentNames('primary')).toEqual({ 1: 'Valid' });
  });
});
