import { describe, expect, it } from 'vitest';
import {
  currentOverallPick,
  isSlotOnClock,
  nextPickForSlot,
  overallPickForRoundSlot,
  pickNumbersForSlot,
  pickWithinRound,
  roundOfPick,
  roundPickLabel,
  takenPlayerIds,
  teamSlotAtPick,
  toDraftLog,
  type DraftPickRecord,
  type DraftState,
} from '../data/draft';

/** RoundGrid.tsx's own forward formula (round, slot) -> pick, copied verbatim so
 *  teamSlotAtPick's inverse direction is checked against the one place in this
 *  app that already computes snake order, not just against itself. */
function forwardPick(round: number, slot: number, teams: number): number {
  const positionInRound = round % 2 === 1 ? slot : teams - slot + 1;
  return (round - 1) * teams + positionInRound;
}

describe('snake-order math', () => {
  it('teamSlotAtPick inverts RoundGrid\'s forward formula for every pick in a 10-team, 16-round league', () => {
    const teams = 10;
    for (let round = 1; round <= 16; round++) {
      for (let slot = 1; slot <= teams; slot++) {
        const pick = forwardPick(round, slot, teams);
        expect(teamSlotAtPick(pick, teams)).toBe(slot);
        expect(roundOfPick(pick, teams)).toBe(round);
      }
    }
  });

  it('reverses direction on even rounds (snake), not straight order', () => {
    const teams = 10;
    expect(teamSlotAtPick(1, teams)).toBe(1); // R1P1 -> slot 1
    expect(teamSlotAtPick(10, teams)).toBe(10); // R1P10 -> slot 10
    expect(teamSlotAtPick(11, teams)).toBe(10); // R2P1 -> slot 10 (reversed)
    expect(teamSlotAtPick(20, teams)).toBe(1); // R2P10 -> slot 1
  });

  it('works for a 12-team league too, not just the primary 10-team one', () => {
    expect(teamSlotAtPick(1, 12)).toBe(1);
    expect(teamSlotAtPick(12, 12)).toBe(12);
    expect(teamSlotAtPick(13, 12)).toBe(12);
    expect(teamSlotAtPick(24, 12)).toBe(1);
  });

  it('pickNumbersForSlot and nextPickForSlot agree with teamSlotAtPick', () => {
    const teams = 10;
    const slot = 3;
    const picks = pickNumbersForSlot(teams, slot, 16);
    expect(picks).toHaveLength(16);
    for (const p of picks) expect(teamSlotAtPick(p, teams)).toBe(slot);

    const noPicks: DraftPickRecord[] = [];
    expect(nextPickForSlot(noPicks, teams, slot, 16)).toBe(picks[0]);

    const somePicks: DraftPickRecord[] = Array.from({ length: 20 }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: i,
      playerName: `Player ${i}`,
      timestamp: 'x',
    }));
    expect(currentOverallPick(somePicks)).toBe(21);
    expect(nextPickForSlot(somePicks, teams, slot, 16)).toBe(picks.find((p) => p >= 21));
  });

  it('pickWithinRound and roundPickLabel (FR-087) agree with the forward formula for every pick in a 10-team, 16-round league', () => {
    const teams = 10;
    for (let round = 1; round <= 16; round++) {
      for (let slot = 1; slot <= teams; slot++) {
        const pick = forwardPick(round, slot, teams);
        // pickWithinRound is position-in-round, NOT the snake-reversed team slot --
        // deliberately not comparing against teamSlotAtPick, which is a different value.
        const positionInRound = round % 2 === 1 ? slot : teams - slot + 1;
        expect(pickWithinRound(pick, teams)).toBe(positionInRound);
        expect(roundPickLabel(pick, teams)).toBe(`R${round}.${String(positionInRound).padStart(2, '0')}`);
      }
    }
  });

  it('roundPickLabel zero-pads pick-within-round to two digits, e.g. pick 21 in a 10-team league', () => {
    // Round 3, position 1 -- single-digit position must still read "01", not "1".
    expect(roundPickLabel(21, 10)).toBe('R3.01');
    expect(roundPickLabel(1, 10)).toBe('R1.01');
    expect(roundPickLabel(10, 10)).toBe('R1.10');
  });

  it('isSlotOnClock matches teamSlotAtPick at the current pick', () => {
    const teams = 10;
    const picks: DraftPickRecord[] = Array.from({ length: 10 }, (_, i) => ({
      overallPick: i + 1,
      round: 1,
      teamSlot: i + 1,
      playerId: i,
      playerName: `Player ${i}`,
      timestamp: 'x',
    }));
    // 10 picks made -> pick 11 is on the clock -> round 2, slot 10 (reversed).
    expect(isSlotOnClock(picks, teams, 10)).toBe(true);
    expect(isSlotOnClock(picks, teams, 1)).toBe(false);
  });
});

/**
 * FR-135 (traditional draft board): `overallPickForRoundSlot` is the address
 * formula every cell in the board grid is keyed by, before any pick exists to
 * look up -- checked against the same independently-copied `forwardPick`
 * reference formula the snake-order suite above already uses, and against
 * `pickNumbersForSlot` (now defined in terms of it) so the refactor changed
 * no observable behaviour.
 */
describe('overallPickForRoundSlot (FR-135 board addressing)', () => {
  it('matches the independent forwardPick reference for every (round, slot) in a 10-team, 16-round league', () => {
    const teams = 10;
    for (let round = 1; round <= 16; round++) {
      for (let slot = 1; slot <= teams; slot++) {
        expect(overallPickForRoundSlot(round, slot, teams)).toBe(forwardPick(round, slot, teams));
      }
    }
  });

  it('round 2 runs backwards across the row -- the snake a board cell must number, not draw', () => {
    const teams = 10;
    // Sleeper's own verified convention (FINDINGS §2.3): round 2, leftmost
    // column (slot 1) carries the LAST pick of that round; rightmost column
    // (slot 10) carries the FIRST.
    expect(overallPickForRoundSlot(2, 1, teams)).toBe(20); // slot 1 -> pick 20 (2.10)
    expect(overallPickForRoundSlot(2, 10, teams)).toBe(11); // slot 10 -> pick 11 (2.1)
  });

  it('pickNumbersForSlot (unchanged public behaviour) still matches, one round at a time', () => {
    const teams = 10;
    const rounds = 16;
    for (let slot = 1; slot <= teams; slot++) {
      const list = pickNumbersForSlot(teams, slot, rounds);
      for (let round = 1; round <= rounds; round++) {
        expect(list[round - 1]).toBe(overallPickForRoundSlot(round, slot, teams));
      }
    }
  });
});

describe('taken-player tracking', () => {
  it('only counts picks that matched a real board player, not raw-text entries', () => {
    const picks: DraftPickRecord[] = [
      { overallPick: 1, round: 1, teamSlot: 1, playerId: 42, playerName: 'Real Player', timestamp: 'x' },
      { overallPick: 2, round: 1, teamSlot: 2, playerId: null, playerName: 'Some Kicker Nobody Ranked', timestamp: 'x' },
    ];
    expect(takenPlayerIds(picks)).toEqual(new Set([42]));
  });
});

describe('toDraftLog', () => {
  it('matches the backend mock-logging schema field-for-field, with no mfl_id', () => {
    const state: DraftState = {
      leagueId: 'default',
      mockId: 'mock-abc',
      queue: [],
      picks: [
        {
          overallPick: 1,
          round: 1,
          teamSlot: 1,
          playerId: 5,
          playerName: 'Bijan Robinson',
          timestamp: '2026-08-01T00:00:00.000Z',
          entryMode: 'shortcut',
        },
      ],
    };
    const log = toDraftLog(state);
    expect(log).toEqual([
      {
        mock_id: 'mock-abc',
        overall_pick: 1,
        round: 1,
        team_slot: 1,
        player_name_raw: 'Bijan Robinson',
        timestamp: '2026-08-01T00:00:00.000Z',
        entry_mode: 'shortcut',
      },
    ]);
    // Exactly these six fields -- no mfl_id, no playerId leaking through.
    expect(Object.keys(log[0]!).sort()).toEqual(
      ['entry_mode', 'mock_id', 'overall_pick', 'player_name_raw', 'round', 'team_slot', 'timestamp'].sort(),
    );
  });

  it('RETROFIT-5: a pick recorded before entry_mode existed exports as an explicit null, never a guessed mode', () => {
    const state: DraftState = {
      leagueId: 'default',
      mockId: 'mock-abc',
      queue: [],
      picks: [
        { overallPick: 1, round: 1, teamSlot: 1, playerId: 5, playerName: 'Bijan Robinson', timestamp: '2026-08-01T00:00:00.000Z' },
      ],
    };
    const log = toDraftLog(state);
    expect(log[0]!.entry_mode).toBeNull();
  });
});
