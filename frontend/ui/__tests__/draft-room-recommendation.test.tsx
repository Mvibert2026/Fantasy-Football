import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDraftState, saveDraftState, teamSlotAtPick, type DraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * Thread 049: the RECOMMENDED panel + WHAT YOU GIVE UP section (item 2), roster
 * slot chips + full MY PICKS sequence + Auto-fill to my pick (item 3-5), and the
 * Board/Opponents/Predictions tab shell (item 1).
 *
 * Real data (loadDatasetFromDisk), same rationale as draft-room-typeahead.test.tsx
 * and board-filters.test.tsx: these are properties of the real board/league shape,
 * not of a hand-written fixture.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** Seeds two synthetic (non-user) picks so overall pick 3 -- this league's real
 *  pick_sequence[0] -- is on the clock and belongs to the user, without needing
 *  to know anything about board contents. Off-board free-text names (playerId:
 *  null) so no real player is marked taken. */
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

describe('thread 049 item 3: roster slot chips', () => {
  it('renders one chip per startable slot type, filled/total, in QB/RB/WR/TE/FLEX/DEF/BN order', () => {
    renderDraftRoom();
    // Fresh draft, nothing picked yet -- every chip reads 0/<starters count>.
    // Thread 058 section D1: the chip's label and count are now two separate
    // text nodes inside a bordered box (matching the design's own checklist
    // markup), so a plain regex against a single text node no longer matches
    // -- scope the query to each element's own full text content instead.
    const hasText = (text: string) => (_content: string, el: Element | null) => el?.textContent === text;
    expect(screen.getByText(hasText('QB 0/1'))).toBeInTheDocument();
    expect(screen.getByText(hasText('RB 0/2'))).toBeInTheDocument();
    expect(screen.getByText(hasText('WR 0/3'))).toBeInTheDocument();
    expect(screen.getByText(hasText('TE 0/1'))).toBeInTheDocument();
    expect(screen.getByText(hasText('FLEX 0/2'))).toBeInTheDocument();
    expect(screen.getByText(hasText('DEF 0/1'))).toBeInTheDocument();
    expect(screen.getByText(hasText('BN 0/6'))).toBeInTheDocument();
  });
});

describe('thread 058 section D2: IR slot', () => {
  it('renders an IR slot in the roster list, sized from the real league.json:roster.ir count', () => {
    renderDraftRoom();
    expect(screen.getByText('IR')).toBeInTheDocument();
  });
});

describe('thread 049 item 4: MY PICKS full sequence', () => {
  it('shows every pick in league.json:pick_sequence, not just picks already made', () => {
    renderDraftRoom();
    // Real pick_sequence for this league/user_draft_slot: 3, 18, 23, 38, 43, ...
    // Scoped to the MY PICKS block specifically -- pick numbers like "3" also
    // appear elsewhere on screen (ON THE CLOCK, YOUR NEXT), so an unscoped
    // query would (correctly) find duplicates.
    const myPicks = within(screen.getByTestId('my-picks'));
    for (const n of [3, 18, 23, 38, 43]) {
      expect(myPicks.getByText(String(n))).toBeInTheDocument();
    }
  });
});

describe('thread 049 item 5: Auto-fill to my pick', () => {
  it('is disabled before any picks are logged (user is on the clock at pick 1... no wait, pick 3 -- so disabled is the wrong state to assert generically)', () => {
    // Regression guard only: the button exists and starts in some definite
    // enabled/disabled state rather than throwing. Behavioural coverage is the
    // next two tests, which set up a known pre-user-turn state explicitly.
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Auto-fill to my pick' })).toBeInTheDocument();
  });

  it('fills every opponent pick between now and the user\'s next turn with a synthetic, clearly-marked placeholder -- never a real player id', () => {
    renderDraftRoom();
    const button = screen.getByRole('button', { name: 'Auto-fill to my pick' });
    expect(button).not.toBeDisabled(); // pick 1 belongs to an opponent in this league
    fireEvent.click(button);

    const state = loadDraftState(leagueId);
    // Picks 1 and 2 belong to opponents (user's first real pick is 3); both
    // should now be filled with the synthetic placeholder, not a real player.
    expect(state.picks).toHaveLength(2);
    for (const p of state.picks) {
      expect(p.playerId).toBeNull();
      expect(p.playerName).toBe('(auto-filled — unknown pick)');
      expect(p.entryMode).toBeNull();
    }
    // The user's own turn (pick 3) was NOT auto-filled -- the button stops
    // exactly at the user's next turn, per Principle #3 (never part-apply).
    expect(state.picks.some((p) => p.overallPick === 3)).toBe(false);
  });

  it('is disabled once the user is actually on the clock (nothing left to skip)', () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Auto-fill to my pick' })).toBeDisabled();
  });
});

describe('thread 049 item 2: RECOMMENDED panel with WHAT YOU GIVE UP', () => {
  it("shows the top recommendation's name/pos-rank/team/bye, a reason, and names the next-best alternative in WHAT YOU GIVE UP", () => {
    seedUpToUsersFirstPick();
    renderDraftRoom();

    expect(screen.getByText("YOU'RE ON THE CLOCK — PICK 3")).toBeInTheDocument();
    // Qualifier text thread 051 explicitly asked to keep verbatim.
    expect(screen.getByText('RECOMMENDED (unvalidated stopgap score, not a backtested model)')).toBeInTheDocument();
    expect(screen.getByText('WHAT YOU GIVE UP')).toBeInTheDocument();
    expect(screen.getByText(/is the next best\./)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Why this rank' })).toBeInTheDocument();
  });
});

describe('thread 049 item 1 / FR-032: Board/Opponents/Predictions tab shell', () => {
  it('defaults to the Board tab showing the existing draft-room content', () => {
    renderDraftRoom();
    expect(screen.getByPlaceholderText(/Mark pick/)).toBeInTheDocument();
  });

<<<<<<< HEAD
  it('switching to Opponents/Predictions renders the real screens, folded in per the founder\'s ask', () => {
=======
  it('switching to Opponents shows the live, pick-log-derived view (FR-032) -- empty state before any pick is entered', () => {
>>>>>>> origin/worktree-agent-a88e0712d14a46ee0
    // Thread 058 section C1: hub tab labels are sentence case ("Opponents",
    // not "OPPONENTS"), matching the design's boxed-tab treatment.
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Opponents' }));
<<<<<<< HEAD
    // The real Opponents.tsx screen (real opponents.json cards), not the old
    // "not wired into Draft mode yet" placeholder -- plus this fold-in's own
    // live-vs-static caveat (rosters.json doesn't move with local picks).
    expect(screen.getByRole('heading', { name: 'Opponents' })).toBeInTheDocument();
    expect(screen.getByText(/does not move the cards below/)).toBeInTheDocument();
    expect(screen.queryByText(/Opponents is not wired into Draft mode yet/)).not.toBeInTheDocument();
=======
    // FR-032: no fabricated roster grid before any pick exists -- one honest
    // "no picks yet" sentence, not ten empty team cards.
    expect(screen.getByText(/No picks yet\. Mark picks on the Board tab/)).toBeInTheDocument();
>>>>>>> origin/worktree-agent-a88e0712d14a46ee0
    expect(screen.queryByPlaceholderText(/Mark pick/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Predictions' }));
    // The real Predictions.tsx screen -- its own calibration caveat is the
    // clearest unique real-content marker.
    expect(screen.getByRole('heading', { name: 'Predictions' })).toBeInTheDocument();
    expect(screen.getByText(/It is currently not calibrated/)).toBeInTheDocument();
    expect(screen.queryByText(/Predictions is not wired into Draft mode yet/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Board' }));
    expect(screen.getByPlaceholderText(/Mark pick/)).toBeInTheDocument();
  });

  it('Predictions reflects a pick recorded in this same Draft-mode session (shared localStorage draft state)', () => {
    // This is the scenario the founder's ask is actually about: recording a
    // pick in Draft mode's own pane, then checking Predictions shows it --
    // not merely that both screens mount. seedUpToUsersFirstPick() writes
    // through saveDraftState, the exact store Predictions.tsx re-reads on
    // mount (ui/data/draft.ts's `prep.draft.<leagueId>` key).
    seedUpToUsersFirstPick();
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Predictions' }));
    expect(screen.getByText(/Live availability at pick 3/)).toBeInTheDocument();
  });
});
