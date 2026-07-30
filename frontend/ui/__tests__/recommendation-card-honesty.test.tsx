import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * Thread 2026-07-30-recommendation-card-states-a-rule-the-code-does- /
 * ADR-DRAFT-suggested-pick-opportunity-cost-rule.md D-2/D-3: two honesty
 * defects in the RECOMMENDED card's "WHAT YOU GIVE UP" text. Neither needs a
 * statistic -- both are the product asserting a causal claim, or an
 * editorial framing, that the code does not support.
 *
 * Same seeding pattern as draft-room-recommendation.test.tsx (real data, real
 * pick_sequence[0] = overall pick 3 for this league/user_draft_slot).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

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

describe('item 1: the false causal claim is gone', () => {
  it('never renders "That difference, not the point gap, is the reason for the order" -- the ordering cannot see availability at all', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.queryByText(/reason for the order/)).not.toBeInTheDocument();
    expect(screen.queryByText(/not the point gap/)).not.toBeInTheDocument();
  });

  it('replaces it with a true statement: the two survival percentages are not an input to the order', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    // The replacement sentence names what the order actually is (VBD plus
    // the stopgap constants), rather than inventing a new causal story.
    expect(screen.getByText(/Neither figure is an input to the order above/)).toBeInTheDocument();
    expect(screen.getByText(/value over replacement plus three unbacktested constants/)).toBeInTheDocument();
  });
});

describe('item 2: "only" is no longer hardcoded onto every survival percentage', () => {
  it('never renders "only NN%" in the give-up text -- the ordering does not read this number at all', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.queryByText(/only \d+% likely/)).not.toBeInTheDocument();
    expect(screen.queryByText(/only \d+% to survive/)).not.toBeInTheDocument();
  });

  it('reason/give-up text uses neutral "likely to still be there" wording instead', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByText(/likely to still be there at your pick at \d+/)).toBeInTheDocument();
  });
});
