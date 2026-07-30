import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Board } from '../views/Board';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk, withTraceOn } from './helpers';

/**
 * FR-114 / `docs/design/PROVENANCE-DISCLOSURE.md` -- the board's own "why this
 * rank" expanded row used to print the structural-breakdown field path as
 * static, always-visible text: `board.json:players[0].structural_breakdown.
 * replacement_levels`, one of the exact examples named in the design spec.
 * The plain-English "Replacement levels: <value>" line is the reason and
 * stays visible either way; only the trailing `(path)` is gated.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function expandFirstRow() {
  const expandHandles = screen.getAllByTitle('Why this rank -- click to expand');
  fireEvent.click(expandHandles[0]!);
}

describe('Board expanded-row field paths (FR-114)', () => {
  it('does not show a board.json field path by default, once a row is expanded', () => {
    render(<Board data={data} rows={rows} league={league} />);
    expandFirstRow();
    // The plain-English reason still renders...
    expect(document.body.textContent).toMatch(/Replacement levels:|Scoring and VBD method:/);
    // ...but the field path citation does not.
    expect(document.body.textContent).not.toContain('board.json:players[');
  });

  it('shows the board.json field path once the switch is on', () => {
    render(withTraceOn(<Board data={data} rows={rows} league={league} />));
    expandFirstRow();
    expect(document.body.textContent).toContain('board.json:players[');
  });
});
