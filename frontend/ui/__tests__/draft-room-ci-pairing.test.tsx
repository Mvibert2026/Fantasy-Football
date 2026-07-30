import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * The RECOMMENDED card used to derive a "points range" from the row's VBD
 * interval (an affine unit conversion, `pointsRangeFromVbdInterval`) and
 * caption it "honest range" directly under "projected pts" -- which read as
 * the projection's own interval even though the number itself was correct.
 * Retired 2026-07-30 per the founder's catch: the interval renders next to
 * whatever `ci_applies_to` actually names (`ciRangeFor`), which is VBD for
 * every row that carries one in the live export.
 *
 * Same idiom as draft-room-recommendation.test.tsx: real data, a synthetic
 * two-pick seed so the user is on the clock at their real first pick.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function seedUpToUsersFirstPick() {
  const picks = [];
  for (let n = 1; n < 3; n++) {
    picks.push({
      overallPick: n,
      round: 1,
      teamSlot: teamSlotAtPick(n, teams),
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed' as const,
    });
  }
  const state: DraftState = { leagueId, mockId: 'test-mock', picks, queue: [] };
  saveDraftState(state);
}

beforeEach(() => {
  localStorage.clear();
});

describe('DraftRoom RECOMMENDED card: the interval pairs with what ci_applies_to names', () => {
  it('the top recommendation carries a real interval in the live export (guards the fixture)', () => {
    const topByVbd = [...rows]
      .filter((r) => r.vbd.kind === 'present')
      .sort((a, b) => (b.vbd as { value: number }).value - (a.vbd as { value: number }).value)[0]!;
    expect(topByVbd.interval.kind).toBe('present');
    if (topByVbd.interval.kind === 'present') expect(topByVbd.interval.value.appliesTo).toBe('vbd');
  });

  it('renders the interval beside VBD, not beside "projected pts"', () => {
    seedUpToUsersFirstPick();
    render(<DraftRoom data={data} rows={rows} league={league} />);
    expect(screen.getByText("YOU'RE ON THE CLOCK — PICK 3")).toBeInTheDocument();

    const projLine = screen.getByText('projected pts').closest('div');
    expect(projLine?.textContent).not.toMatch(/–/); // no en-dash range on the projected-pts line

    const vbdLine = screen.getByText(/^VBD /).closest('div') ?? screen.getByText('VBD', { exact: false }).closest('div');
    expect(vbdLine?.textContent).toMatch(/–/); // the range lives here instead

    // The literal wording this bug produced must be gone.
    expect(screen.queryByText(/honest range/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Honest points range/i)).not.toBeInTheDocument();
  });
});
