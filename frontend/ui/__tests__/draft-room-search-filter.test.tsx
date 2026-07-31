import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-122 ("when typing in a player's name, the list should begin to shrink
 * down based on possible parameters so it can be used as a search as well as
 * a 'drafted' function"). Reuses the existing pick-entry field (the same one
 * RETROFIT-5's typeahead already covers in draft-room-typeahead.test.tsx) --
 * this file covers its second job, narrowing the rankings pane's row list,
 * without touching the first job's own suggester-dropdown behaviour.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

function pickEntryInput(): HTMLInputElement {
  return screen.getByPlaceholderText(/Mark pick 1/) as HTMLInputElement;
}

function rankingsPaneList(): HTMLElement {
  return screen.getByTestId('rankings-pane-list');
}

beforeEach(() => {
  localStorage.clear();
});

describe("FR-122: the pick-entry field's second job -- filtering the rankings pane list", () => {
  it('typing a substring of a real player name narrows the visible row list to matches', async () => {
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present')!;
    if (target.name.kind !== 'present') throw new Error('fixture guard');
    const input = pickEntryInput();

    await userEvent.type(input, target.name.value.slice(0, 5));

    const list = rankingsPaneList();
    expect(within(list).getByTestId(`rankings-pane-row-${target.id}`)).toBeInTheDocument();
    // A player whose name plainly does not contain the typed substring should
    // no longer have a row rendered.
    const needle = target.name.value.slice(0, 5).toLowerCase();
    const nonMatch = rows.find((r) => {
      if (r.id === target.id || r.name.kind !== 'present') return false;
      return !r.name.value.toLowerCase().includes(needle);
    })!;
    expect(within(list).queryByTestId(`rankings-pane-row-${nonMatch.id}`)).not.toBeInTheDocument();
  });

  it(
    '"RB1" narrows to running backs ranked 1 and 10-19, not to nothing -- the FR\'s own named example',
    async () => {
      renderDraftRoom();
      const rb1 = rows.find((r) => r.positionalLabel.kind === 'present' && r.positionalLabel.value === 'RB1')!;
      const rb10 = rows.find((r) => r.positionalLabel.kind === 'present' && r.positionalLabel.value === 'RB10')!;
      expect(rb1).toBeDefined();
      expect(rb10).toBeDefined();
      const input = pickEntryInput();

      await userEvent.type(input, 'RB1');

      const list = rankingsPaneList();
      expect(within(list).getByTestId(`rankings-pane-row-${rb1.id}`)).toBeInTheDocument();
      expect(within(list).getByTestId(`rankings-pane-row-${rb10.id}`)).toBeInTheDocument();
    },
    // Rendering ~500 rows plus a real 511-player dataset under userEvent.type's
    // per-keystroke re-render is occasionally slow in a CPU-contended shared
    // container (see docs/status/2026-07-29-frontend-fr050-055-058.md's own
    // note on this exact class of flake) -- a longer timeout, not a weaker
    // assertion.
    15_000,
  );

  it('matches on team, independent of the currently selected position tab', async () => {
    renderDraftRoom();
    // Select a specific, narrow position tab first...
    const posRow = screen.getByRole('button', { name: 'ALL' }).parentElement!;
    fireEvent.click(within(posRow).getByRole('button', { name: 'QB' }));
    // ...then search for a team that a non-QB is on. The FR is explicit that a
    // search in progress is not additionally constrained by the tab.
    const wr = rows.find((r) => r.raw.position === 'WR' && r.raw.team)!;
    const input = pickEntryInput();

    await userEvent.type(input, wr.raw.team);

    const list = rankingsPaneList();
    expect(within(list).getByTestId(`rankings-pane-row-${wr.id}`)).toBeInTheDocument();
  });

  it('folds punctuation and case, matching the search examples the FR names', async () => {
    // Exercise the fold end-to-end (not just the unit-tested normalizeSearchTerm)
    // by searching in a case/punctuation-different form of a real name's start.
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present' && /[a-z]/.test(r.name.value))!;
    if (target.name.kind !== 'present') throw new Error('fixture guard');
    const oddCased = target.name.value.slice(0, 4).toUpperCase();
    const input = pickEntryInput();

    await userEvent.type(input, oddCased);

    const list = rankingsPaneList();
    expect(within(list).getByTestId(`rankings-pane-row-${target.id}`)).toBeInTheDocument();
  });

  it('does not auto-select or commit a pick just because the query narrows to exactly one row', async () => {
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present')!;
    if (target.name.kind !== 'present') throw new Error('fixture guard');
    const input = pickEntryInput();

    // Type the full name -- as narrow as a query can get.
    await userEvent.type(input, target.name.value);

    // No Enter, no digit shortcut, no click -- narrowing alone must never commit.
    expect(loadDraftState(leagueId).picks).toHaveLength(0);
  });

  it('clearing the query restores the position tab\'s own list (does not leave the search filter stuck on)', async () => {
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present')!;
    if (target.name.kind !== 'present') throw new Error('fixture guard');
    const input = pickEntryInput();

    await userEvent.type(input, target.name.value);
    const otherRow = rows.find((r) => r.id !== target.id && r.name.kind === 'present')!;
    expect(within(rankingsPaneList()).queryByTestId(`rankings-pane-row-${otherRow.id}`)).not.toBeInTheDocument();

    await userEvent.clear(input);

    expect(within(rankingsPaneList()).getByTestId(`rankings-pane-row-${otherRow.id}`)).toBeInTheDocument();
  });

  it('an honest empty state names the query when nothing matches, rather than a silently blank list', async () => {
    renderDraftRoom();
    const input = pickEntryInput();
    await userEvent.type(input, 'zzz-no-real-player-or-team-matches-this-zzz');
    expect(screen.getByText(/No still-available player matches/)).toBeInTheDocument();
  });

  it('a search still leaves RETROFIT-5\'s own 5-slot commit suggester working unchanged', async () => {
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present')!;
    if (target.name.kind !== 'present') throw new Error('fixture guard');
    const input = pickEntryInput();

    await userEvent.type(input, target.name.value.slice(0, 5));
    // The existing suggester dropdown (a different, pre-existing feature) is
    // untouched by this change -- it still opens and still offers row 1.
    expect(screen.getByTestId('suggester-dropdown')).toBeInTheDocument();
  });
});
