import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Board } from '../views/Board';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * Regression cover for the board filters.
 *
 * The delta inputs were uncontrolled, so Reset cleared the filter but left the typed
 * text sitting in the box -- the table showed everything while the control still read
 * "10". At a draft table that is worse than a filter that does not work, because it
 * looks like it does.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function renderBoard() {
  return render(<Board data={data} rows={rows} league={league} />);
}

describe('board filters', () => {
  it('clears the delta inputs when Reset is pressed', async () => {
    renderBoard();

    const min = screen.getByLabelText('Minimum delta vs consensus') as HTMLInputElement;
    await userEvent.type(min, '10');
    expect(min.value).toBe('10');

    await userEvent.click(screen.getByRole('button', { name: 'Reset' }));
    expect(min.value).toBe('');
  });

  it('treats a non-numeric delta as no bound rather than filtering everything out', async () => {
    renderBoard();

    const min = screen.getByLabelText('Minimum delta vs consensus');
    await userEvent.type(min, 'abc');

    // Still showing the full board: a junk entry must not silently empty the table.
    expect(screen.getByText(new RegExp(`${rows.length} of ${rows.length} shown`))).toBeInTheDocument();
  });

  it('filters by position and restores on reset', async () => {
    renderBoard();

    const before = screen.getByText(new RegExp(`${rows.length} of ${rows.length} shown`));
    expect(before).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'QB' }));
    const qbCount = rows.filter((r) => r.raw.position === 'QB').length;
    expect(
      screen.getByText(new RegExp(`${qbCount} of ${rows.length} shown`)),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Reset' }));
    expect(
      screen.getByText(new RegExp(`${rows.length} of ${rows.length} shown`)),
    ).toBeInTheDocument();
  });

  it('reports an empty result as a state, not an error', async () => {
    renderBoard();

    // A bound no player can satisfy.
    const min = screen.getByLabelText('Minimum delta vs consensus');
    await userEvent.type(min, '99999');

    expect(screen.getByText(/nothing matches these filters/i)).toBeInTheDocument();
    expect(screen.getByText(/loosen a filter/i)).toBeInTheDocument();
  });

  it('shows the sparse count, which is most of the board', () => {
    renderBoard();
    const sparse = rows.filter((r) => r.isSparse).length;
    expect(
      screen.getByText(new RegExp(`${sparse} of ${rows.length} players carry no displayable projection`)),
    ).toBeInTheDocument();
  });
});
