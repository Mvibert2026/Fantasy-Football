import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftPickRecord, type DraftState } from '../data/draft';
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

/** Real picks through overall pick `n` (never fillers past it), so the caller
 *  can put the user off the clock at a chosen point in the sequence. Mirrors
 *  draft-room-scarcity-and-sort.test.tsx's own helper. */
function seedRealPicksThroughOverall(n: number) {
  const picks: DraftPickRecord[] = [];
  for (let overall = 1; overall <= n; overall++) {
    picks.push({
      overallPick: overall,
      round: 1,
      teamSlot: teamSlotAtPick(overall, teams),
      playerId: null,
      playerName: `Filler ${overall}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
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

describe('item 3: board AVAIL retargets to the pick after the current one while on the clock', () => {
  it('while on the clock at pick 3, the header names pick 18 (followingUserPick), not pick 3 (the event already resolved)', () => {
    // This league/user_draft_slot's real pick_sequence: 3, 18, 23, ... --
    // asserted directly against league.json rather than hand-guessed, so a
    // future league-config change fails this test instead of silently
    // asserting the wrong pick number.
    const sequence = league.pickSequence.kind === 'present' ? league.pickSequence.value : [];
    expect(sequence.slice(0, 2)).toEqual([3, 18]);

    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByText("YOU'RE ON THE CLOCK — PICK 3")).toBeInTheDocument();

    // Before the fix this read "AVAIL" against `nextUserPick`, which equals
    // `currentPick` (3) while on the clock -- an event every visible row has
    // already survived. ADR-DRAFT-suggested-pick-opportunity-cost-rule.md
    // D-4: it must name the user's *following* turn instead.
    expect(screen.getByText('AVAIL @ 18')).toBeInTheDocument();
    expect(screen.queryByText('AVAIL @ 3')).not.toBeInTheDocument();
    expect(screen.queryByText('AVAIL', { exact: true })).not.toBeInTheDocument();
  });

  it('off the clock, the header still names the honest next pick (nextUserPick, unchanged branch)', () => {
    // Seeds picks 1-3 (including the user's real pick 3), so the user is off
    // the clock and their next real pick is 18 -- same number as the on-clock
    // case above, but reached via the untouched `nextUserPick` branch (ADR
    // §6: "Off the clock, `nextUserPick` is already correct — do not change
    // that branch."), not `followingUserPick`.
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    expect(screen.queryByText("YOU'RE ON THE CLOCK")).not.toBeInTheDocument();
    expect(screen.getByText('AVAIL @ 18')).toBeInTheDocument();
  });

  it('the header tooltip names the same pick number as the visible text, not a generic "your next pick"', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    const header = screen.getByText('AVAIL @ 18');
    expect(header).toHaveAttribute('title', expect.stringMatching(/pick 18/));
  });
});
