import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { roundPickLabel, saveDraftState, teamSlotAtPick, type DraftPickRecord } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * docs/design/DRAFT-MIDDLE-PANE.md: the middle pane's fixed stack (RECOMMENDED-
 * when-on-clock, else POSITION SCARCITY + Queue/Watch + NEXT DECISION) becomes
 * one tab set -- Recommend / Scarcity / Queue / Insights -- with NEXT DECISION
 * as a persistent footer never behind a tab, plus FR-049's look-ahead toggle
 * and FR-051's next-pick reference point, both inside Recommend, and FR-045's
 * pace-suppression rule inside Scarcity.
 *
 * Real data (loadDatasetFromDisk), matching every other DraftRoom test file's
 * rationale: these are properties of the real board/league shape (this
 * league's real pick_sequence is 3, 18, 23, 38, ... -- teams=10, rounds=16).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** Two off-board filler picks so overall pick 3 -- this league's real
 *  pick_sequence[0] -- is on the clock and belongs to the user. */
function seedUpToUsersFirstPick() {
  const picks: DraftPickRecord[] = [];
  for (let n = 1; n < 3; n++) {
    picks.push({
      overallPick: n,
      round: 1,
      teamSlot: teamSlotAtPick(n, teams),
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    });
  }
  saveDraftState({ leagueId, mockId: 'test-mock', picks, queue: [] });
}

/** Three off-board filler picks, so the user's own pick-3 turn is already
 *  used up by a filler and the user is off the clock until pick 18. */
function seedThroughUsersFirstPick() {
  const picks: DraftPickRecord[] = [];
  for (let n = 1; n <= 3; n++) {
    picks.push({
      overallPick: n,
      round: 1,
      teamSlot: teamSlotAtPick(n, teams),
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    });
  }
  saveDraftState({ leagueId, mockId: 'test-mock', picks, queue: [] });
}

beforeEach(() => {
  localStorage.clear();
});

describe('the pane is one tab set: Recommend / Scarcity / Queue / Insights', () => {
  it('defaults to Recommend, and NEXT DECISION is visible regardless of which tab is active', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Recommend' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/NEXT DECISION/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Scarcity' }));
    expect(screen.getByTestId('position-scarcity')).toBeInTheDocument();
    expect(screen.getByText(/NEXT DECISION/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Queue' }));
    expect(screen.getByRole('button', { name: /^Queue \(/ })).toBeInTheDocument();
    expect(screen.getByText(/NEXT DECISION/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Insights' }));
    expect(screen.getByText('Not built yet.')).toBeInTheDocument();
    expect(screen.getByText(/FR-048/)).toBeInTheDocument();
    expect(screen.getByText(/NEXT DECISION/)).toBeInTheDocument();
  });

  it('the board list and roster rail stay mounted while switching pane tabs', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Insights' }));
    // The left board list (search box) and right roster rail (MY ROSTER) are
    // outside the tabbed middle pane -- confirm neither disappeared.
    expect(screen.getByPlaceholderText(/Mark pick/)).toBeInTheDocument();
    expect(screen.getByText('MY ROSTER')).toBeInTheDocument();
  });
});

describe('FR-049: look-ahead toggle inside Recommend', () => {
  it('on the clock, defaults to "this pick" content and offers a look-ahead toggle to the following turn', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByText("YOU'RE ON THE CLOCK — PICK 3")).toBeInTheDocument();
    const lookAheadButton = screen.getByRole('button', { name: /Look ahead → pick 18/ });
    expect(lookAheadButton).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'This pick' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(lookAheadButton);
    expect(screen.getByText(/LOOKING AHEAD — PICK 18 \(ROUND 2\)/)).toBeInTheDocument();
    expect(lookAheadButton).toHaveAttribute('aria-pressed', 'true');
    // Give-up / VBD-override reasoning is specific to "this pick"'s
    // followingUserPick-based survival math -- deliberately not shown in the
    // look-ahead branch (see recommendationDetailLookAhead's own comment).
    expect(screen.queryByText('WHAT YOU GIVE UP')).not.toBeInTheDocument();
    expect(screen.getByText(/computed on/)).toBeInTheDocument();
    expect(screen.getByText(/does not account for players taken between now and then/)).toBeInTheDocument();
  });

  it('off the clock, Recommend shows look-ahead content by default with no toggle', () => {
    seedThroughUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByText(/NOT ON THE CLOCK — LOOKING AHEAD TO PICK 18 \(ROUND 2\)/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'This pick' })).not.toBeInTheDocument();
    expect(screen.getByText('RECOMMENDED (unvalidated stopgap score, not a backtested model)')).toBeInTheDocument();
    expect(screen.getByText(/does not account for players taken between now and then/)).toBeInTheDocument();
  });
});

describe('FR-051: the next-pick reference point', () => {
  it('shows CONSIDERING / LIKELY THERE AT <pick> with real VBD figures while on the clock, "this pick"', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    // FR-087: round + pick-within-round now render alongside the raw pick
    // number here too -- same roundPickLabel helper the app itself uses, not
    // a separately hand-typed expectation.
    expect(
      screen.getByText(`LIKELY BEST AVAILABLE AT YOUR PICK 18 (${roundPickLabel(18, teams)})`),
    ).toBeInTheDocument();
    expect(screen.getByText('CONSIDERING')).toBeInTheDocument();
    expect(screen.getByText(`LIKELY THERE AT 18 (${roundPickLabel(18, teams)})`)).toBeInTheDocument();
    // Display-only, never fed into the recommendation -- the footer states so
    // explicitly per FR-051's own instruction.
    expect(screen.getByText(/Display only/)).toBeInTheDocument();
  });

  it('disappears once look-ahead is toggled on -- scoped to the base on-clock state only', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: /Look ahead → pick 18/ }));
    expect(
      screen.queryByText(`LIKELY BEST AVAILABLE AT YOUR PICK 18 (${roundPickLabel(18, teams)})`),
    ).not.toBeInTheDocument();
  });
});

describe('FR-045: pace suppression when auto-fill placeholders are present', () => {
  it('suppresses pace for every position once a placeholder pick exists, never a fabricated number', () => {
    // Off the clock (pick_sequence[0]=3, so logging 1 filler leaves the user
    // off the clock at pick 2 with picks 3..17 all opponents' -- auto-fill
    // has real picks to skip).
    saveDraftState({
      leagueId,
      mockId: 'test-mock',
      picks: [
        {
          overallPick: 1,
          round: 1,
          teamSlot: teamSlotAtPick(1, teams),
          playerId: null,
          playerName: 'Filler 1',
          timestamp: new Date().toISOString(),
          entryMode: 'typed',
        },
      ],
      queue: [],
    });
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Auto-fill to my pick' }));
    fireEvent.click(screen.getByRole('button', { name: 'Scarcity' }));

    const panel = screen.getByTestId('position-scarcity');
    const suppressed = within(panel).getAllByText(/auto-filled picks stand in for unknown opponents/);
    expect(suppressed.length).toBeGreaterThan(0);
    expect(within(panel).queryByText(/ahead of pace|behind of pace|behind pace/)).not.toBeInTheDocument();
  });
});

describe('Insights tab: honest not-built state (FR-048)', () => {
  it('names the missing findings.json artifact rather than approximating from unscoped research text', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Insights' }));
    expect(screen.getByText(/findings\.json/)).toBeInTheDocument();
    expect(screen.getByText(/does not exist in the export contract today/)).toBeInTheDocument();
  });
});
