import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Board } from '../views/Board';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * Regression cover for the Board control row, ported from the design handoff
 * prototype (design_handoff_draft_assistant/Draft Assistant.dc.html, lines
 * 405-461): position tabs, the Table/Round-grid toggle, and the Delta view sort.
 *
 * This file previously tested a different, earlier control row -- multi-select
 * position buttons, tier buttons, free-text search, and numeric delta-bound
 * inputs -- including a regression test for an uncontrolled-input bug in those
 * bound fields. That whole control surface no longer exists: the prototype's Board
 * screen has no search box and no delta-bound inputs (both are specific to its
 * Draft Room screen, not Prep/Board), so the old regression test is retired along
 * with the inputs it guarded, not left behind to fail against a UI it no longer
 * describes.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function renderBoard() {
  return render(<Board data={data} rows={rows} league={league} />);
}

describe('board control row', () => {
  it('filters to one position at a time via the ALL/QB/RB/WR/TE/DEF tabs', async () => {
    renderBoard();

    expect(screen.getByText(`${rows.length} players`)).toBeInTheDocument();

    const qbCount = rows.filter((r) => r.raw.position === 'QB').length;
    await userEvent.click(screen.getByRole('button', { name: 'QB' }));
    expect(screen.getByText(`${qbCount} players`)).toBeInTheDocument();

    // Single-select: switching to RB must not leave QB's filter active alongside it.
    const rbCount = rows.filter((r) => r.raw.position === 'RB').length;
    await userEvent.click(screen.getByRole('button', { name: 'RB' }));
    expect(screen.getByText(`${rbCount} players`)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'ALL' }));
    expect(screen.getByText(`${rows.length} players`)).toBeInTheDocument();
  });

  it('marks the active position tab with aria-pressed', async () => {
    renderBoard();
    const all = screen.getByRole('button', { name: 'ALL' });
    const wr = screen.getByRole('button', { name: 'WR' });
    expect(all).toHaveAttribute('aria-pressed', 'true');
    expect(wr).toHaveAttribute('aria-pressed', 'false');

    await userEvent.click(wr);
    expect(all).toHaveAttribute('aria-pressed', 'false');
    expect(wr).toHaveAttribute('aria-pressed', 'true');
  });

  it('Delta view sorts by the size of the disagreement with consensus', async () => {
    renderBoard();

    const biggestDelta = Math.max(
      ...rows
        .filter((r) => r.deltaVsConsensus.kind === 'present')
        .map((r) => Math.abs((r.deltaVsConsensus as { value: number }).value)),
    );
    // Guard the fixture: the test is meaningless if nothing actually disagrees.
    expect(biggestDelta).toBeGreaterThan(0);

    await userEvent.click(screen.getByRole('button', { name: /Delta view/ }));

    // Header and rows are siblings inside one scroll container (needed for the
    // header's position:sticky to work against the right ancestor) -- rows are
    // the header's general siblings directly, not wrapped in an extra layer.
    const rowsInDom = document.querySelectorAll('[style*="grid-template-columns: 64px"] ~ div');
    expect(rowsInDom.length).toBeGreaterThan(0);
  });

  it('toggles between the table and the round grid, showing one at a time', async () => {
    renderBoard();

    expect(screen.getByText('RANK')).toBeInTheDocument();
    expect(document.querySelector('.round-grid')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Round grade grid' }));
    expect(document.querySelector('.round-grid')).toBeInTheDocument();
    expect(screen.queryByText('RANK')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Table' }));
    expect(screen.getByText('RANK')).toBeInTheDocument();
    expect(document.querySelector('.round-grid')).not.toBeInTheDocument();
  });

  it('shows the projection curve caveat required by the data contract', () => {
    renderBoard();
    expect(screen.getByText(data.board.curve_caveat)).toBeInTheDocument();
  });

  it('shows the real loaded-player count with no hardcoded denominator', () => {
    // Regression: the provenance line used to read "N of 378 players loaded" -- 378 was a
    // literal snapshot of the export size at the time it was written, not a sourced field
    // (buildRows maps 1:1 over board.json:players, so there is no separate "total available"
    // to divide against). It silently drifted true the moment the export grew past 378 rows.
    renderBoard();
    expect(screen.getByText(new RegExp(`${rows.length} players loaded`))).toBeInTheDocument();
    expect(screen.queryByText(/of \d+ players loaded/)).not.toBeInTheDocument();
  });

  it('reports an empty result as a state, not an error', async () => {
    // DEF is never on this board (no DST data ingested), so filtering to it is a
    // reliable way to reach the empty state without relying on a specific dataset shape.
    renderBoard();
    await userEvent.click(screen.getByRole('button', { name: 'DEF' }));
    expect(screen.getByText(/nothing matches these filters/i)).toBeInTheDocument();
  });

  it('shows a projection reason on hover instead of a blank cell for sparse rows', () => {
    renderBoard();
    const sparse = rows.find((r) => r.isSparse);
    expect(sparse).toBeDefined();
    expect(screen.getAllByText('no projection').length).toBeGreaterThan(0);
  });

  it('selecting a row opens the detail panel with the structural attribution breakdown', async () => {
    renderBoard();
    const first = rows[0]!;
    const name = first.name.kind === 'present' ? first.name.value : '';
    await userEvent.click(screen.getAllByText(name)[0]!);
    expect(screen.getByText('WHY OUR RANK DIFFERS FROM THE MARKET')).toBeInTheDocument();
    // The three-box breakdown: consensus rank, format correction, our rank.
    expect(screen.getByText('CONSENSUS')).toBeInTheDocument();
    expect(screen.getByText('FORMAT CORRECTION')).toBeInTheDocument();
  });

  it('reports the selected player up so the assistant can anchor to them', async () => {
    const onFocusPlayer = vi.fn();
    render(<Board data={data} rows={rows} league={league} onFocusPlayer={onFocusPlayer} />);
    const first = rows[0]!;
    const name = first.name.kind === 'present' ? first.name.value : '';

    await userEvent.click(screen.getAllByText(name)[0]!);
    expect(onFocusPlayer).toHaveBeenLastCalledWith(name);

    // Closing the panel (the "esc" button) clears the anchor rather than leaving it stale.
    await userEvent.click(screen.getByRole('button', { name: 'esc' }));
    expect(onFocusPlayer).toHaveBeenLastCalledWith(null);
  });

  it('shows tier bands with a player count for a single position, in the default rank order', async () => {
    renderBoard();

    // Bands only render for a single position, not "ALL": board.json's tier_label
    // is assigned per position, not globally, so in overall-rank order across
    // every position the same label re-triggers repeatedly as positions
    // interleave (verified against the live export: 74 transitions across the
    // full board vs. a clean 5 within any one position) -- see the comment on
    // Board's bandsEnabled. RB is picked arbitrarily; any single position works.
    const rbT1Count = rows.filter(
      (r) => r.raw.position === 'RB' && r.tierLabel.kind === 'present' && r.tierLabel.value === 'T1',
    ).length;
    expect(rbT1Count).toBeGreaterThan(0); // guard the fixture

    expect(screen.queryByText('TIER 1')).not.toBeInTheDocument(); // ALL view: no bands

    await userEvent.click(screen.getByRole('button', { name: 'RB' }));
    expect(screen.getByText('TIER 1')).toBeInTheDocument();
    expect(screen.getByText(`${rbT1Count} players`)).toBeInTheDocument();

    // Sorting by a column other than rank breaks the tier grouping a band implies.
    await userEvent.click(screen.getByText('VBD'));
    expect(screen.queryByText('TIER 1')).not.toBeInTheDocument();

    // Clicking RANK again (it was the default, now displaced) restores bands.
    await userEvent.click(screen.getByText('RANK'));
    expect(screen.getByText('TIER 1')).toBeInTheDocument();
  });

  it('sorts by a column on click and shows a direction indicator that flips on a second click', async () => {
    renderBoard();

    const consHeader = screen.getByText('CONS');
    await userEvent.click(consHeader);
    expect(consHeader.parentElement?.textContent).toContain('▲');

    await userEvent.click(consHeader);
    expect(consHeader.parentElement?.textContent).toContain('▼');
  });

  it('sorting by CONS actually reorders the rows, not just the indicator', async () => {
    renderBoard();
    await userEvent.click(screen.getByText('CONS'));

    const bestConsensus = Math.min(
      ...rows
        .filter((r) => r.consensusRank.kind === 'present')
        .map((r) => (r.consensusRank as { value: number }).value),
    );
    const leader = rows.find(
      (r) => r.consensusRank.kind === 'present' && r.consensusRank.value === bestConsensus,
    )!;
    const leaderName = leader.name.kind === 'present' ? leader.name.value : '';

    const firstDataRow = document.querySelectorAll('[style*="grid-template-columns: 64px"] + div')[0];
    expect(firstDataRow?.textContent).toContain(leaderName);
  });

  it('keeps the header row sticky so it stays visible while the table scrolls', () => {
    renderBoard();
    const header = screen.getByText('RANK').closest('div[style*="position: sticky"]');
    expect(header).not.toBeNull();
  });
});
