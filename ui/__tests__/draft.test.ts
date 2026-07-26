import { describe, expect, it } from 'vitest';
import {
  currentOverallPick,
  isSlotOnClock,
  nextPickForSlot,
  pickNumbersForSlot,
  roundOfPick,
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
      watchlist: [],
      picks: [
        { overallPick: 1, round: 1, teamSlot: 1, playerId: 5, playerName: 'Bijan Robinson', timestamp: '2026-08-01T00:00:00.000Z' },
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
      },
    ]);
    // Exactly these five fields -- no mfl_id, no playerId leaking through.
    expect(Object.keys(log[0]!).sort()).toEqual(
      ['mock_id', 'overall_pick', 'player_name_raw', 'round', 'team_slot', 'timestamp'].sort(),
    );
  });
});
