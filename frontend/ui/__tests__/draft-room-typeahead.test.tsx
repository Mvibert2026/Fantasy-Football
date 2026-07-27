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
  it('does not show the suggester automatically on mount, even though candidates exist and the field autofocuses (thread 051 item 2)', () => {
    renderDraftRoom();
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    expect(screen.queryByTestId('candidate-row-1')).not.toBeInTheDocument();
  });

  it('opens the suggester on a real focus of the pick-entry field', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    fireEvent.focus(input);
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });

  it('opens the suggester when the user types, independent of focus', async () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    await userEvent.type(input, 'a');
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });

  it('dismisses the suggester on Escape', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.focus(input);
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('dismisses the suggester on a click outside it', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.focus(input);
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
    fireEvent.mouseDown(document.body);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('does not dismiss on a click inside the dropdown (e.g. hovering a candidate row)', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.focus(input);
    fireEvent.mouseDown(screen.getByTestId('candidate-row-1'));
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });

  it('shows the top 5 available-by-board-rank players as the default (no-query) shortlist, in real board-rank order -- not randomised (thread 051 item 3)', () => {
    renderDraftRoom();
    fireEvent.focus(screen.getByPlaceholderText(/Mark pick 1/));
    const shownOrder = [1, 2, 3, 4, 5].map((i) => screen.getByTestId(`candidate-row-${i}`).textContent);
    const expected = topFiveByRank();
    expect(expected).toHaveLength(5);
    shownOrder.forEach((text, i) => {
      const row = expected[i]!;
      expect(row.name.kind).toBe('present');
      if (row.name.kind === 'present') expect(text).toContain(row.name.value);
    });
    // Exactly 5 numbered rows, not some other count.
    expect(screen.getByTestId('candidate-row-1')).toBeInTheDocument();
    expect(screen.getByTestId('candidate-row-5')).toBeInTheDocument();
    expect(screen.queryByTestId('candidate-row-6')).not.toBeInTheDocument();
  });

  it('the default shortlist header no longer claims the order is randomised (thread 051 item 3)', () => {
    renderDraftRoom();
    fireEvent.focus(screen.getByPlaceholderText(/Mark pick 1/));
    expect(screen.getByText('TOP 5 BY BOARD RANK, STILL AVAILABLE')).toBeInTheDocument();
    expect(screen.queryByText(/ORDER RANDOMISED/)).not.toBeInTheDocument();
  });

  it('digit "1" commits whichever candidate is displayed in row 1, auto-advances, clears the field, and logs entry_mode "shortcut"', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.focus(input);
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

  it('candidate order is deterministic real board-rank order across independent mounts -- NOT randomised (thread 051 item 3, reversing this build\'s own earlier choice)', () => {
    const orders = new Set<string>();
    for (let attempt = 0; attempt < 8; attempt++) {
      localStorage.clear();
      const { unmount } = renderDraftRoom();
      fireEvent.focus(screen.getByPlaceholderText(/Mark pick 1/));
      const order = [1, 2, 3, 4, 5].map((i) => screen.getByTestId(`candidate-row-${i}`).textContent).join('|');
      orders.add(order);
      unmount();
    }
    // Every independent mount must land on the exact same order -- if this
    // ever fails, a shuffle crept back in.
    expect(orders.size).toBe(1);
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

/**
 * Thread 063 (regression of 051): the founder reported the suggester "seems to
 * trigger every pick." Root cause, confirmed by reading the code rather than
 * guessing: 051's fix only guarded the *mount/remount* programmatic focus()
 * call (setSearchInputRef's ref callback). It missed that `recordPick` --
 * invoked on every commit, from every commit site (digit shortcut, typed/
 * pasted Enter, clicking a candidate row, and the board row's own "mark
 * taken" X, which is how an opponent's pick gets logged) -- also called
 * `searchRef.current?.focus()` directly, unguarded, immediately after every
 * commit (kept deliberately, for fast keyboard re-entry). That refocus went
 * through the exact same onFocus handler as a real click, with no suppression
 * flag set for this call site, so the very next commit's own refocus looked
 * exactly like a genuine user focus and reopened the popover -- "opens every
 * pick" is a literal, not approximate, description of what the code did.
 *
 * The fix (frontend/ui/views/DraftRoom.tsx): a single shared helper,
 * `refocusSearchWithoutOpening`, used at both of this component's actual
 * programmatic-focus call sites (mount/remount, and post-commit refocus).
 * Same guard mechanism 051 introduced (`suppressNextFocusOpen`), completed to
 * cover the call site 051 missed -- not a second, competing guard.
 * `recordPick` now also explicitly closes the panel on commit
 * (`setSuggesterOpen(false)`), matching the stated rule "closes on ... commit"
 * for the case where the panel was already open going into that commit.
 *
 * One test per row of the reopen-trigger table in docs/handoffs/
 * 063-suggester-reopen-regression.md, in the table's own order, so a future
 * regression on any single trigger is pinned to exactly one failing test.
 */
describe('thread 063: suggester opens ONLY on explicit user intent (regression fix)', () => {
  it('row 1 -- click into the pick-entry field: opens', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    fireEvent.focus(input);
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });

  it('row 2 -- typing into the field: opens', async () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    await userEvent.type(input, 'a');
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });

  it('row 3 -- a pick is committed (yours or an opponent\'s): does not open, and closes if it was open -- this is the reported regression', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;

    // "Yours": commit via the digit shortcut while the panel is genuinely
    // open (the exact sequence the founder described -- focus it, then use
    // the 1-5 fast-entry path).
    fireEvent.focus(input);
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
    fireEvent.keyDown(input, { key: '1' });
    // Before the fix: this reopened via the post-commit refocus's onFocus.
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    expect(loadDraftState(leagueId).picks).toHaveLength(1);

    // "An opponent's": logging a pick via the board row's own "mark taken" X
    // is a *different* commit site than the search box entirely -- it must
    // not open the panel either, whether or not the panel is currently
    // showing.
    const markTaken = screen.getAllByTitle('Mark taken')[0]!;
    fireEvent.click(markTaken);
    expect(loadDraftState(leagueId).picks).toHaveLength(2);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('row 4 -- the board updates or recomputes: does not open', () => {
    const { rerender } = renderDraftRoom();
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    // Simulate a recompute publishing fresh row objects (new references, same
    // underlying data) without any user interaction.
    const recomputedRows = rows.map((r) => ({ ...r }));
    rerender(<DraftRoom data={data} rows={recomputedRows} league={league} />);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('row 5 -- component mount / page load / refresh: does not open, even though the field autofocuses', () => {
    renderDraftRoom();
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    expect(screen.queryByTestId('candidate-row-1')).not.toBeInTheDocument();
  });

  it('row 6 -- league switch: does not open', () => {
    const { rerender } = renderDraftRoom();
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
    const switchedData = {
      ...data,
      manifest: {
        ...data.manifest,
        artifacts: {
          ...data.manifest.artifacts,
          board: { ...data.manifest.artifacts.board!, league_id: 'a-different-league' },
        },
      },
    };
    rerender(<DraftRoom data={switchedData} rows={rows} league={league} />);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('row 7 -- returning to the Draft tab from another tab (unmount then remount): does not open', () => {
    const { unmount } = renderDraftRoom();
    unmount();
    renderDraftRoom();
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('row 8 -- undo: does not open', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    fireEvent.keyDown(input, { key: '1' }); // log a pick, unfocused-dropdown path
    expect(loadDraftState(leagueId).picks).toHaveLength(1);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();

    fireEvent.keyDown(screen.getByPlaceholderText(/Mark pick 2/), { key: 'Backspace' }); // undo
    expect(loadDraftState(leagueId).picks).toHaveLength(0);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();
  });

  it('row 9 -- programmatic focus from any source in this component does not open it, and is decoupled from focus itself actually moving', () => {
    renderDraftRoom();
    const input = screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
    // Mount's own autofocus already ran by this point -- confirm it really did
    // move DOM focus (the "auto-focus is fine" half of the rule) while leaving
    // the panel shut (the "but it must not open" half).
    expect(document.activeElement).toBe(input);
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument();

    // Now the post-commit path: blur first, via the real DOM method (not
    // fireEvent.blur, which only dispatches the event without actually
    // moving document.activeElement) so the refocus below is a genuine focus
    // transition -- jsdom, like real browsers, does not fire a focus event
    // from calling .focus() on an element that is already the active
    // element, so blurring first is what makes this an honest check of the
    // post-commit call site rather than an accidental no-op.
    input.blur();
    expect(document.activeElement).not.toBe(input);
    fireEvent.keyDown(input, { key: '1' });
    expect(document.activeElement).toBe(input); // fast-entry refocus still happened
    expect(screen.queryByTestId('suggester-dropdown')).not.toBeInTheDocument(); // but did not open it
  });
});
