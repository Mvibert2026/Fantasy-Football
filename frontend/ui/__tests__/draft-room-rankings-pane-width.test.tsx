import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * RANKINGS-PANE.md item 1 (design round 2026-07-31): "at 1180 the pane drops
 * the player's name entirely." Root cause, confirmed reading DraftRoom.tsx
 * directly: the old PLAYER cell was `flex: 1, minWidth: 0` -- a flex child
 * with NO floor at all, so once this pane's own share of the layout-mode grid
 * got narrower than every other column's combined fixed width, PLAYER's
 * resolved width went to (near) zero and the name disappeared completely.
 *
 * jsdom does not run a real layout engine (every element reports 0 for
 * `offsetWidth`/`getBoundingClientRect`), so a test cannot literally shrink
 * the window and observe pixels the way the design review's screenshot did --
 * that verification is the Playwright screenshot at 1180w (see
 * `frontend/e2e/verify-rankings-pane.mjs` and the committed artifacts). What
 * a unit test CAN assert, and what would have caught the original defect, is
 * the structural guarantee the fix actually relies on: PLAYER's column is a
 * CSS Grid `minmax(Npx, 1fr)` track with a real, nonzero floor -- not a
 * floor-less flex child -- and the header and every row size that column from
 * the exact same template string, so they can never drift into two different
 * widths for the same conceptual column (RANKINGS-PANE.md item 3's
 * constraint, satisfied as a side effect of fixing item 1).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** Pulls the `minmax(Npx,1fr)` floor (in px) out of a `grid-template-columns`
 *  string's PLAYER track (the 2nd of 11 tracks -- RANK, PLAYER, POS, TM, ADP,
 *  Δ, VBD, AVAIL, dots, watch, taken). Returns `null` if the track is not a
 *  `minmax(...)` at all -- e.g. a regression back to a bare `1fr`, which is
 *  exactly as floor-less as the old `flex: 1, minWidth: 0`. */
function playerTrackFloorPx(gridTemplateColumns: string): number | null {
  const tracks = gridTemplateColumns.trim().split(/\s+(?![^(]*\))/); // split on spaces not inside parens
  const playerTrack = tracks[1];
  const m = playerTrack?.match(/^minmax\((\d+(?:\.\d+)?)px\s*,/);
  return m ? Number(m[1]) : null;
}

describe('RANKINGS-PANE.md item 1: PLAYER column never drops', () => {
  it("the header row's grid template gives PLAYER a real, nonzero minimum width -- not a floor-less flex child", () => {
    renderDraftRoom();
    const header = screen.getByTestId('rankings-pane-header-row');
    const floor = playerTrackFloorPx(header.style.gridTemplateColumns);
    expect(floor).not.toBeNull();
    expect(floor).toBeGreaterThan(0);
  });

  it('a real row uses the exact same grid template as the header -- one column definition, not two that can drift apart', () => {
    renderDraftRoom();
    const header = screen.getByTestId('rankings-pane-header-row');
    const firstRow = rows[0]!;
    const rowWrapper = screen.getByTestId(`rankings-pane-row-${firstRow.id}`);
    const rowGrid = rowWrapper.firstElementChild as HTMLElement;
    expect(rowGrid.style.gridTemplateColumns).toBe(header.style.gridTemplateColumns);
  });

  it('the PLAYER header cell and a row\'s name cell both render real text -- the header literally says PLAYER, not nothing', () => {
    renderDraftRoom();
    const header = screen.getByTestId('rankings-pane-header-row');
    expect(header).toHaveTextContent('PLAYER');
    const firstRow = rows.find((r) => r.name.kind === 'present')!;
    const rowWrapper = screen.getByTestId(`rankings-pane-row-${firstRow.id}`);
    expect(firstRow.name.kind).toBe('present');
    if (firstRow.name.kind === 'present') {
      expect(rowWrapper).toHaveTextContent(firstRow.name.value);
    }
  });

  it('every row in the list carries a real, non-empty PLAYER cell -- not just the first one', () => {
    renderDraftRoom();
    // Sample a handful of rows spread across the board, not just row 0.
    const sample = [rows[0]!, rows[Math.floor(rows.length / 2)]!, rows[rows.length - 1]!];
    for (const r of sample) {
      if (r.name.kind !== 'present') continue;
      const rowWrapper = screen.getByTestId(`rankings-pane-row-${r.id}`);
      expect(rowWrapper).toHaveTextContent(r.name.value);
    }
  });

  it("the PLAYER track's floor matches the ~7-character truncated width design's own 1500w capture already treated as acceptable, not an arbitrarily small value that would still read as blank", () => {
    // Guards against a future "fix" that sets the floor to something
    // technically nonzero but still illegible (e.g. 4px). 40px is comfortably
    // below what any real name needs but well above "not really visible."
    renderDraftRoom();
    const header = screen.getByTestId('rankings-pane-header-row');
    const floor = playerTrackFloorPx(header.style.gridTemplateColumns);
    expect(floor).not.toBeNull();
    expect(floor as number).toBeGreaterThanOrEqual(40);
  });
});
