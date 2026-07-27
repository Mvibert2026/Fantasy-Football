import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows, type BoardRow } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * RETROFIT-5 (docs/design-handoff/screens/01-draft-board.md): DraftRoom's pick
 * entry backported from the Mock Lab TypeAhead reference
 * (docs/design-reference/mock-lab/03-logging.dc.html's Component class --
 * there is no Mock Lab *application* code in this repo to port from, since Mock
 * Lab's own UI is unbuilt; the reference HTML mockup's `onKey`/`log`/`undo`
 * logic is the actual source ported here).
 *
 * Deliberately real data (loadDatasetFromDisk), not a fixture -- same
 * rationale as board-filters.test.tsx: the property under test ("the
 * candidates really are the top 5 by real board rank") is a property of the
 * real data, and a hand-written fixture could hide a wiring bug that only
 * shows up against the real shape.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** Same "top 5 by real board rank" computation DraftRoom.tsx uses for its
 *  default (no-query) shortlist, kept independent here rather than imported,
 *  so this test would actually fail if that logic drifted. */
function topFiveByRank(): BoardRow[] {
  return rows
    .map((r) => ({ row: r, rank: r.overallRank.kind === 'present' ? r.overallRank.value : null }))
    .filter((x): x is { row: BoardRow; rank: number } => x.rank !== null)
    .sort((a, b) => a.rank - b.rank)
    .slice(0, 5)
    .map((x) => x.row);
}

beforeEach(() => {
  localStorage.clear();
});

describe('RETROFIT-5: DraftRoom pick-entry TypeAhead', () => {
  it('shows the top 5 available-by-board-rank players as the default (no-query) shortlist', () => {
    renderDraftRoom();
    // Scoped to the 5 candidate rows specifically -- the full board pane behind
    // the dropdown also renders these same names, so an unscoped getByText
    // would (correctly) find duplicates and is not the right tool here.
    const shown = new Set(
      [1, 2, 3, 4, 5].map((i) => screen.getByTestId(`candidate-row-${i}`).textContent),
    );
    for (const row of topFiveByRank()) {
      expect(row.name.kind).toBe('present');
      if (row.name.kind === 'present') {
        const hit = [...shown].some((text) => text?.includes(row.name.kind === 'present' ? row.name.value : ''));
        expect(hit).toBe(true);
      }
    }
    // Exactly 5 numbered rows, not some other count.
    expect(screen.getByTestId('candidate-row-1')).toBeInTheDocument();
    expect(screen.getByTestId('candidate-row-5')).toBeInTheDocument();
    expect(screen.queryByTestId('candidate-row-6')).not.toBeInTheDocument();
  });

  it('digit "1" commits whichever candidate is displayed in row 1, auto-advances, clears the field, and logs entry_mode "shortcut"', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    const row1Name = screen.getByTestId('candidate-row-1').querySelector('span[style*="font-weight: 600"]')?.textContent;
    expect(row1Name).toBeTruthy();

    fireEvent.keyDown(input, { key: '1' });

    const state = loadDraftState(leagueId);
    expect(state.picks).toHaveLength(1);
    expect(state.picks[0]!.playerName).toBe(row1Name);
    expect(state.picks[0]!.entryMode).toBe('shortcut');
    expect(input.value).toBe(''); // auto-advance clears the field, no confirm step
    // Placeholder now reads pick 2 -- the pick clock actually advanced.
    expect(screen.getByPlaceholderText(/Mark pick 2/)).toBeInTheDocument();
  });

  it('Backspace on an empty field undoes the last pick', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;

    fireEvent.keyDown(input, { key: '1' }); // log pick 1 via shortcut
    expect(loadDraftState(leagueId).picks).toHaveLength(1);

    fireEvent.keyDown(input, { key: 'Backspace' }); // field is empty -> undo
    expect(loadDraftState(leagueId).picks).toHaveLength(0);
    expect(screen.getByPlaceholderText(/Mark pick 1/)).toBeInTheDocument(); // clock rolled back too
  });

  it('Backspace does NOT undo while the field still has text in it', async () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.keyDown(input, { key: '1' });
    expect(loadDraftState(leagueId).picks).toHaveLength(1);

    const input2 = screen.getByPlaceholderText(/Mark pick 2/) as HTMLInputElement;
    await userEvent.type(input2, 'z');
    fireEvent.keyDown(input2, { key: 'Backspace' }); // deletes text, must not also undo
    expect(loadDraftState(leagueId).picks).toHaveLength(1);
  });

  it('typing a name and pressing Enter logs entry_mode "typed", not "shortcut"', async () => {
    renderDraftRoom();
    const target = topFiveByRank()[0]!;
    if (target.name.kind !== 'present') throw new Error('fixture guard: expected a present name');
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;

    await userEvent.type(input, target.name.value);
    fireEvent.keyDown(input, { key: 'Enter' });

    const state = loadDraftState(leagueId);
    expect(state.picks).toHaveLength(1);
    expect(state.picks[0]!.playerName).toBe(target.name.value);
    expect(state.picks[0]!.entryMode).toBe('typed');
  });

  it('pasting a name and pressing Enter logs entry_mode "pasted", distinct from typing it', () => {
    renderDraftRoom();
    const target = topFiveByRank()[0]!;
    if (target.name.kind !== 'present') throw new Error('fixture guard: expected a present name');
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;

    // Simulate a paste: a native 'input' event carrying inputType
    // 'insertFromPaste', which is what onChange's entry_mode detection reads.
    // React tracks <input> value through the native property's own setter
    // (to detect changes React itself didn't cause), so the value must be set
    // via that setter -- not a plain assignment, which React-DOM's commit
    // phase then fights over and throws on.
    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    nativeSetter.call(input, target.name.value);
    fireEvent.input(input, { inputType: 'insertFromPaste' } as unknown as Event);
    fireEvent.keyDown(input, { key: 'Enter' });

    const state = loadDraftState(leagueId);
    expect(state.picks).toHaveLength(1);
    expect(state.picks[0]!.entryMode).toBe('pasted');
  });

  it('Escape clears the field without committing a pick', async () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    await userEvent.type(input, 'somebody');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input.value).toBe('');
    expect(loadDraftState(leagueId).picks).toHaveLength(0);
  });

  it('candidate order is actually randomised, not just capable of being -- rank order is not the only order seen across independent mounts', () => {
    const orders = new Set<string>();
    for (let attempt = 0; attempt < 20; attempt++) {
      localStorage.clear();
      const { unmount } = renderDraftRoom();
      const order = [1, 2, 3, 4, 5].map((i) => screen.getByTestId(`candidate-row-${i}`).textContent).join('|');
      orders.add(order);
      unmount();
    }
    // Rank order is one specific permutation out of 5! = 120; if the code
    // shuffled, 20 independent mounts landing on the exact same permutation
    // every time has probability on the order of (1/120)^19 -- not a
    // meaningfully flaky assertion. If this ever fails, the shuffle is gone,
    // not unlucky.
    expect(orders.size).toBeGreaterThan(1);
  });

  it('a pick logged before RETROFIT-5 (no entryMode in storage) round-trips as an explicit null, never a guessed mode', () => {
    localStorage.setItem(
      `prep.draft.${leagueId}`,
      JSON.stringify({
        leagueId,
        mockId: 'legacy-mock',
        queue: [],
        picks: [
          { overallPick: 1, round: 1, teamSlot: 1, playerId: rows[0]!.id, playerName: 'Legacy Pick', timestamp: 'x' },
        ],
      }),
    );
    const state = loadDraftState(leagueId);
    expect(state.picks[0]!.entryMode).toBeNull();
  });
});
