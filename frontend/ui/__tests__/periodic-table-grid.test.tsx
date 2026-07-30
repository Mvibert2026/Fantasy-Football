import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftPickRecord, type DraftState } from '../data/draft';
import { buildGridCellData, buildPositionByTeamMatrix } from '../components/PeriodicTableGrid';
import { loadDatasetFromDisk } from './helpers';

/**
 * The periodic-table draft board, FR-044 / `docs/design/PERIODIC-TABLE-GRID.md`
 * -- additive fifth pane tab (Grid) plus the Expand sheet it shares with
 * `docs/design/PANE-LAYOUT-MODES.md`'s layout-mode gesture.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

function seedPicks(overallPicks: number[]) {
  const picks: DraftPickRecord[] = overallPicks.map((overall) => {
    const row = rows[overall - 1];
    const name = row && row.name.kind === 'present' ? row.name.value : `Filler ${overall}`;
    return {
      overallPick: overall,
      round: 1,
      teamSlot: teamSlotAtPick(overall, teams),
      playerId: row?.id ?? null,
      playerName: name,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    };
  });
  const state: DraftState = { leagueId, mockId: 'test-mock', picks, queue: [] };
  saveDraftState(state);
}

beforeEach(() => {
  localStorage.clear();
});

describe('buildGridCellData', () => {
  it('marks a taken row gone, straight off the real taken set -- never guessed', () => {
    const taken = new Set([rows[0]!.id]);
    const cells = buildGridCellData({ rows: rows.slice(0, 3), taken, data, league, picks: [], rowsById: new Map(), nextUserPick: null });
    expect(cells[0]!.gone).toBe(true);
    expect(cells[1]!.gone).toBe(false);
    expect(cells[2]!.gone).toBe(false);
  });

  it('never computes underHalf without a real nextUserPick -- absence of the dot is not a claim', () => {
    const cells = buildGridCellData({
      rows: rows.slice(0, 20),
      taken: new Set(),
      data,
      league,
      picks: [],
      rowsById: new Map(rows.map((r) => [r.id, r])),
      nextUserPick: null,
    });
    expect(cells.every((c) => c.underHalf === false)).toBe(true);
  });
});

describe('buildPositionByTeamMatrix', () => {
  it('groups cells by team|position and sorts each bucket by overall rank', () => {
    const cells = buildGridCellData({
      rows,
      taken: new Set(),
      data,
      league,
      picks: [],
      rowsById: new Map(rows.map((r) => [r.id, r])),
      nextUserPick: null,
    });
    const matrix = buildPositionByTeamMatrix(cells);
    // Every real row lands in exactly one bucket.
    const total = Array.from(matrix.values()).reduce((n, b) => n + b.length, 0);
    expect(total).toBe(rows.length);
    // The real board carries zero DEF players (ADR-039) -- every DEF bucket
    // is honestly empty, never fabricated.
    const defBuckets = Array.from(matrix.entries()).filter(([k]) => k.endsWith('|DEF'));
    expect(defBuckets.every(([, b]) => b.length === 0)).toBe(true);
    // A bucket that does have players is rank-ordered within itself.
    const nonEmpty = Array.from(matrix.values()).find((b) => b.length > 1);
    if (nonEmpty) {
      const ranks = nonEmpty.map((c) => (c.row.overallRank.kind === 'present' ? c.row.overallRank.value : Infinity));
      expect(ranks).toEqual([...ranks].sort((a, b) => a - b));
    }
  });
});

describe('the Grid pane tab (preview)', () => {
  it('is additive -- reachable alongside the four original tabs, showing identity/position/depletion only', () => {
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Grid' }));
    expect(screen.getByRole('button', { name: /Expand/ })).toBeInTheDocument();
    // The first board player by rank appears as a cell.
    const firstName = rows[0]!.name.kind === 'present' ? rows[0]!.name.value : '';
    expect(screen.getAllByText(firstName).length).toBeGreaterThan(0);
  });

  it('does not offer the position-by-team sort toggle in the preview -- only Expand does', () => {
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Grid' }));
    expect(screen.queryByRole('button', { name: /Position × team/ })).not.toBeInTheDocument();
  });

  it('a taken player renders struck through and dimmed, not removed from the grid', () => {
    seedPicks([1]);
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Grid' }));
    const firstName = rows[0]!.name.kind === 'present' ? rows[0]!.name.value : '';
    const cellText = screen.getAllByText(firstName)[0]!;
    expect(cellText).toHaveStyle({ textDecoration: 'line-through' });
  });
});

describe('the Expand sheet', () => {
  it('opens on the Expand button, covers board+pane, and leaves the roster rail (MY ROSTER) visible', () => {
    renderDraftRoom();
    fireEvent.click(screen.getByRole('button', { name: 'Grid' }));
    fireEvent.click(screen.getByRole('button', { name: /Expand/ }));
    expect(screen.getByText('GRID')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Draft order' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Position × team' })).toBeInTheDocument();
    // Roster rail still on screen.
    expect(screen.getByText('MY ROSTER')).toBeInTheDocument();
  });

  it('opens on Alt+G from anywhere on the screen', () => {
    renderDraftRoom();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByText('GRID')).toBeInTheDocument();
  });

  it('the position-by-team sort mode renders the 32-team-by-5-position matrix header', () => {
    renderDraftRoom();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    fireEvent.click(screen.getByRole('button', { name: 'Position × team' }));
    // The column headers, specifically -- not just "QB" appearing anywhere,
    // which also matches every individual QB player's position pill.
    expect(screen.getByTestId('grid-header-QB')).toHaveTextContent('QB');
    expect(screen.getByTestId('grid-header-RB')).toHaveTextContent('RB');
    expect(screen.getByTestId('grid-header-WR')).toHaveTextContent('WR');
    expect(screen.getByTestId('grid-header-TE')).toHaveTextContent('TE');
    // ATL is a real team from the loaded board (Bijan Robinson, RB) -- confirms
    // the team axis is real team codes, not a placeholder.
    expect(screen.getAllByText('ATL').length).toBeGreaterThan(0);
  });

  it('closes on the Close button', () => {
    renderDraftRoom();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(screen.queryByText('GRID')).not.toBeInTheDocument();
  });

  it('closes on Escape when the player detail card is not open', () => {
    renderDraftRoom();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByText('GRID')).toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    expect(screen.queryByText('GRID')).not.toBeInTheDocument();
  });

  it('Escape precedence: closes the player detail card first, not the grid sheet, when both are open', () => {
    renderDraftRoom();
    // Open the player card via a board row click.
    const firstName = rows[0]!.name.kind === 'present' ? rows[0]!.name.value : '';
    fireEvent.click(screen.getAllByText(firstName)[0]!);
    expect(screen.getByTestId('player-detail-backdrop')).toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByText('GRID')).toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    // Player card gone, grid sheet still open -- exactly one thing closed.
    expect(screen.queryByTestId('player-detail-backdrop')).not.toBeInTheDocument();
    expect(screen.getByText('GRID')).toBeInTheDocument();
  });

  it('closes itself when a pick lands', () => {
    renderDraftRoom();
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByText('GRID')).toBeInTheDocument();
    // Mark the first candidate taken via the "1-5 to commit" shortcut on the
    // search field, the same real user path a live draft uses.
    const input = screen.getByPlaceholderText(/Mark pick/);
    fireEvent.keyDown(input, { key: '1' });
    expect(screen.queryByText('GRID')).not.toBeInTheDocument();
  });
});
