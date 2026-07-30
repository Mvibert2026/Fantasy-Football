import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * PERIODIC-TABLE-GRID.md, item 3 of the 2026-07-31 round: "A fifth tab.
 * Nothing removed ... The four existing tabs keep their content, their order
 * and their default." This is the founder's own binding constraint, stated
 * unprompted after praising the pane -- and per CLAUDE.md's own operating
 * rule, "a test is the only thing that keeps it true through the next
 * refactor." So this file exists solely to pin that shape, independent of any
 * test that happens to exercise one tab's content.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

beforeEach(() => {
  localStorage.clear();
});

describe('DraftRoom pane tabs: additive-only constraint', () => {
  it('renders exactly the four original tabs plus Grid, in that order', () => {
    renderDraftRoom();
    const tabBar = screen.getByRole('button', { name: 'Recommend' }).parentElement;
    if (!tabBar) throw new Error('pane tab bar not found');
    const labels = Array.from(tabBar.querySelectorAll('button')).map((b) => b.textContent);
    expect(labels).toEqual(['Recommend', 'Scarcity', 'Queue', 'Insights', 'Grid']);
  });

  it('still defaults to Recommend, unchanged', () => {
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Recommend' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Scarcity' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Queue' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Insights' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Grid' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('still renders the three hub tabs unchanged (Board / Opponents / Predictions)', () => {
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Board' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Opponents' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Predictions' })).toHaveAttribute('aria-pressed', 'false');
  });
});
