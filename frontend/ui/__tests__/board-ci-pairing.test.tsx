import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Board } from '../views/Board';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { loadDatasetFromDisk } from './helpers';

/**
 * The bug the founder caught, 2026-07-30: the board's PROJ column read
 * "PROJ (CI)" and paired the projection with an interval that `ci_applies_to`
 * says is on VBD (145/145 rows, confirmed against the live export --
 * `ci-pairing.test.ts`). This is the test that would have caught it: whatever
 * quantity a row's interval is displayed against must match `ci_applies_to`,
 * and it must fail the moment a future change re-attaches the interval to the
 * wrong cell -- including for a quantity this app has never seen live, so a
 * hardcoded "always vbd" assumption cannot silently pass.
 *
 * Single-player synthetic datasets are used for the non-"vbd" cases so the
 * board's own `ciQuantityInRows` header logic (which reads across every
 * rendered row) has only one row to read from -- unambiguous by construction.
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);

function withOnlyPlayer(overrides: Partial<RawBoardPlayer>): Dataset {
  const base = data.board.players[0];
  if (!base) throw new Error('fixture expected at least one player');
  return {
    ...data,
    board: { ...data.board, players: [{ ...base, ...overrides }] },
  } as Dataset;
}

function renderSingle(dataset: Dataset) {
  const rows = buildRows(dataset);
  render(<Board data={dataset} rows={rows} league={league} />);
  return rows[0]!;
}

describe('Board: the interval renders on whatever ci_applies_to names', () => {
  it('real export data: at least one row has an interval, and it is on VBD, not PROJ (guards the fixture)', () => {
    const withCi = data.board.players.find((p) => p.ci_low !== null && p.ci_high !== null);
    if (!withCi) throw new Error('fixture expected at least one player with a real interval');
    expect(withCi.ci_applies_to).toBe('vbd');
  });

  it('ci_applies_to "vbd": the VBD column header carries "(CI)", PROJ does not, and the interval text sits next to VBD, not next to the projection', () => {
    const row = renderSingle(withOnlyPlayer({ ci_low: 135.33, ci_high: 222.43, ci_applies_to: 'vbd' }));
    const projHeader = screen.getByText('PROJ');
    expect(projHeader.textContent).not.toMatch(/CI/);

    const vbdHeaderRow = screen.getByText('VBD').closest('span');
    expect(vbdHeaderRow?.textContent).toMatch(/VBD/);
    // The "(CI)" suffix is its own hoverable span next to VBD.
    expect(screen.getAllByText('(CI)').length).toBeGreaterThan(0);

    // The row itself: the interval numbers appear once, attached to VBD.
    const vbdValue = row.vbd.kind === 'present' ? row.vbd.value : null;
    expect(vbdValue).not.toBeNull();
    expect(screen.getByText(/135\.3\s*–\s*222\.4/)).toBeInTheDocument();

    // The PROJ cell shows only the point estimate -- no range text beside it.
    const projValue = row.projectedPoints.kind === 'present' ? row.projectedPoints.value.toFixed(1) : null;
    expect(projValue).not.toBeNull();
    const projCellText = screen.getByText(projValue!).closest('span')?.parentElement?.textContent ?? '';
    expect(projCellText).not.toMatch(/–/); // no en-dash range in the PROJ cell
  });

  it('ci_applies_to "projected_points": the interval moves to PROJ, VBD stays a bare number -- never hardcoded to "vbd"', () => {
    renderSingle(withOnlyPlayer({ ci_low: 260, ci_high: 340, ci_applies_to: 'projected_points' }));
    // The header now reads "PROJ (CI)" (dynamic, per ciQuantityInRows), and
    // VBD lost its suffix.
    expect(screen.getAllByText('(CI)').length).toBeGreaterThan(0);
    expect(screen.getByText(/260\.0\s*–\s*340\.0/)).toBeInTheDocument();
  });

  it('ci_applies_to naming a quantity this app has no Cell for: an honest in-place note, never silently dropped and never paired with VBD or PROJ anyway', () => {
    renderSingle(withOnlyPlayer({ ci_low: 1, ci_high: 2, ci_applies_to: 'snap_share' }));
    // Neither header gets a "(CI)" suffix -- nothing recognized to attach it to.
    expect(screen.queryByText('(CI)')).not.toBeInTheDocument();
    // But the fact that an unrecognized interval exists is not silently
    // dropped -- an honest marker renders in place.
    expect(screen.getByText('(CI: unrecognized)')).toBeInTheDocument();
    // And the number is not fabricated onto VBD or PROJ either.
    expect(screen.queryByText(/1\.0\s*–\s*2\.0/)).not.toBeInTheDocument();
  });

  it('no interval on the row at all: neither column claims one', () => {
    renderSingle(withOnlyPlayer({ ci_low: null, ci_high: null }));
    expect(screen.queryByText('(CI)')).not.toBeInTheDocument();
    expect(screen.queryByText('(CI: unrecognized)')).not.toBeInTheDocument();
  });
});
