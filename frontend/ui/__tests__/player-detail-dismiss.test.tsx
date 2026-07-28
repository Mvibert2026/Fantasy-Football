import { render, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows, type BoardRow } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * Thread 073 dismissible-surface audit, one enumerated surface: the player
 * detail side sheet. Click-outside via the transparent backdrop (§3.3)
 * already worked pre-audit; Escape did not, despite the close button being
 * labelled "esc" -- the key itself was never wired to anything. Both are
 * covered here separately so a regression in either direction fails on its
 * own, not folded into the other's assertion.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
if (!rows[0]) throw new Error('Real board export has zero players -- fixture assumption broken.');
const firstRow: BoardRow = rows[0];

function renderDetail(onClose: () => void) {
  return render(
    <PlayerDetail
      row={firstRow}
      rows={rows}
      data={data}
      league={league}
      picks={[]}
      watchlist={[]}
      onToggleWatch={() => {}}
      onClose={onClose}
    />,
  );
}

describe('PlayerDetail dismissal', () => {
  it('closes on Escape from anywhere on the page', () => {
    const onClose = vi.fn();
    renderDetail(onClose);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on a click on the transparent backdrop outside the sheet', () => {
    const onClose = vi.fn();
    const { getByTestId } = renderDetail(onClose);

    fireEvent.click(getByTestId('player-detail-backdrop'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close on a key other than Escape', () => {
    const onClose = vi.fn();
    renderDetail(onClose);

    fireEvent.keyDown(document, { key: 'Enter' });

    expect(onClose).not.toHaveBeenCalled();
  });
});
