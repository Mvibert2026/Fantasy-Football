import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk, withTraceOn } from './helpers';

/**
 * `docs/design/PLAYER-PROFILE.md` §3 (reading level): the backend's own
 * `board.json:curve_caveat` is written in statistics vocabulary ("R-squared is
 * 0.16-0.27") -- accurate, but design's point is that a lower reading level
 * should read as a STRONGER warning, not a softer one. The formula moves to
 * trace mode (same FR-114 pattern as everywhere else on this card); the
 * plain-English replacement is the default. This pins both states so a future
 * edit can't silently drop either half.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

const PLAIN_ENGLISH =
  'Projections follow consensus rank, which explains well under half of what actually happens. ' +
  'Use them to separate tiers, not to split two players who are close.';

function renderFirst(wrapper?: (el: ReactElement) => ReactElement) {
  const first = rows[0];
  if (!first) throw new Error('Real board export has zero players -- fixture assumption broken.');
  const el = (
    <PlayerDetail
      row={first}
      rows={rows}
      data={data}
      league={league}
      picks={[]}
      watchlist={[]}
      onToggleWatch={() => {}}
      onClose={vi.fn()}
    />
  );
  return render(wrapper ? wrapper(el) : el);
}

describe('PlayerDetail projection caveat reading level (PLAYER-PROFILE.md §3)', () => {
  it('the real export field actually carries statistics vocabulary -- confirms this test is not vacuous', () => {
    expect(data.board.curve_caveat).toMatch(/R-squared/);
  });

  it('shows the plain-English rewrite by default, not the raw formula', () => {
    renderFirst();
    expect(screen.getByText(PLAIN_ENGLISH)).toBeTruthy();
    expect(document.body.textContent).not.toContain('R-squared');
    expect(document.body.textContent).not.toContain(data.board.curve_caveat);
  });

  it('shows the raw backend caveat verbatim once "show data sources" is on -- trace mode restores it, not deletes it', () => {
    renderFirst(withTraceOn);
    expect(screen.getByText(data.board.curve_caveat)).toBeTruthy();
    expect(document.body.textContent).not.toContain(PLAIN_ENGLISH);
  });
});
