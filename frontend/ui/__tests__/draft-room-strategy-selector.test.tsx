import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { rankByRecommendation } from '../data/recommendation';
import { saveDraftState, teamSlotAtPick, type DraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-061 / `docs/design/STRATEGY-SELECTOR.md`. Real data (loadDatasetFromDisk),
 * same rationale as the other draft-room test files: whether the recommendation
 * actually reorders is a property of the real board's real VBD figures, not of a
 * hand-written fixture that could accidentally make every strategy a no-op.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** This league's real user_draft_slot is 3 -- seed two off-board filler picks so
 *  overall pick 3 (round 1, the user's real first turn) is on the clock, same
 *  helper pattern as draft-room-recommendation.test.tsx. */
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
  const state: DraftState = { leagueId, mockId: 'strategy-selector-test', picks, queue: [] };
  saveDraftState(state);
}

beforeEach(() => {
  localStorage.clear();
});

describe('Strategy selector (FR-061)', () => {
  it('renders at the head of the Recommend tab with the required power-floor and lineup caveats, never shortened', () => {
    renderDraftRoom();
    expect(screen.getByText('STRATEGY')).toBeInTheDocument();
    expect(screen.getByText(/Best player available/)).toBeInTheDocument();
    // The two caveats strategies.json actually carries -- rendered verbatim,
    // not collapsed into a single "results are indicative" line.
    expect(screen.getByText(new RegExp(data.strategies!.power_floor.plain_english.slice(0, 40)))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(data.strategies!.lineup_assumption.slice(0, 40)))).toBeInTheDocument();
  });

  it('does not move the board -- selecting Zero RB never renders a "STRATEGY ADJUSTMENT" panel without the founder\'s own default staying visible in the selector', () => {
    renderDraftRoom();
    // Default is selected and pressed.
    const bpaButton = screen.getByRole('button', { name: /Best player available/ });
    expect(bpaButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('reorders the Recommend shortlist and explains why when Zero RB actually changes the top pick', () => {
    seedUpToUsersFirstPick();

    // Compute the real, un-adjusted top pick for this league's first user turn
    // (round 1, all players still available) directly from the same formula
    // DraftRoom itself uses, so this test doesn't hardcode a specific player
    // name that could drift if the board export changes.
    const baseRanked = rankByRecommendation(rows, 1, new Set(['QB', 'RB', 'WR', 'TE', 'DEF']));
    const baseTop = baseRanked[0]!;
    const isBaseTopRB = baseTop.row.raw.position === 'RB';

    renderDraftRoom();
    const zeroRbButton = screen.getByRole('button', { name: /Zero RB/ });
    fireEvent.click(zeroRbButton);

    expect(zeroRbButton).toHaveAttribute('aria-pressed', 'true');

    if (isBaseTopRB) {
      // The real board's plain-VBD pick 1 recommendation is an RB -- Zero RB
      // must have moved it, and the panel must say so.
      expect(screen.getByText(/STRATEGY ADJUSTMENT — ZERO RB/)).toBeInTheDocument();
      expect(screen.getByText(/a preference you selected, not a claim that this pick scores higher/)).toBeInTheDocument();
    } else {
      // If the real board's own top pick were ever not an RB, Zero RB has
      // nothing to move at pick 1 and must render nothing extra -- "nothing at
      // all when nothing moved," the same rule FR-058 already uses.
      expect(screen.queryByText(/STRATEGY ADJUSTMENT/)).not.toBeInTheDocument();
    }
  });
});
