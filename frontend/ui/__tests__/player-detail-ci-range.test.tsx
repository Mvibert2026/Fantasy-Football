import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { loadDatasetFromDisk } from './helpers';

/**
 * The player card's PROJECTION section used to plot `row.interval` (a VBD
 * range) against `mid={row.projectedPoints.value}` unconditionally --
 * `frontend/e2e/artifacts/fr114-player-card-off.png` is the screenshot the
 * founder's question came from: 303.2 projected pts sat directly above a bar
 * whose bounds were 135.3-222.4, so the marker was clamped to the bar's far
 * right edge (`RangeBar`'s own `Math.min(100, ...)`) every time, since 303.2
 * never actually fell inside that range. `ProjectionRange` now reads
 * `ciTargetFor(row)` and plots the bar's `mid` against whichever cell the
 * interval is actually on -- VBD for every row that carries one live.
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);

function withOverride(overrides: Partial<RawBoardPlayer>): Dataset {
  return {
    ...data,
    board: {
      ...data.board,
      players: data.board.players.map((p, i) => (i === 0 ? { ...p, ...overrides } : p)),
    },
  } as Dataset;
}

function renderFirst(dataset: Dataset, wrapper: (el: ReactElement) => ReactElement = (el) => el) {
  const rows = buildRows(dataset);
  const first = rows[0];
  if (!first) throw new Error('Real board export has zero players -- fixture assumption broken.');
  return render(
    wrapper(
      <PlayerDetail
        row={first}
        rows={rows}
        data={dataset}
        league={league}
        picks={[]}
        watchlist={[]}
        onToggleWatch={() => {}}
        onClose={vi.fn()}
      />,
    ),
  );
}

describe('PlayerDetail PROJECTION section: the range bar plots what the interval is actually on', () => {
  it('ci_applies_to "vbd": captions the bar "VBD range" and the range text sits under that caption, not unlabelled under the projection', () => {
    renderFirst(withOverride({ ci_low: 135.33, ci_high: 222.43, ci_applies_to: 'vbd' }));
    expect(screen.getByText('VBD range')).toBeInTheDocument();
    expect(screen.getByText(/135\.3\s*–\s*222\.4/)).toBeInTheDocument();
  });

  it('ci_applies_to "projected_points": captions the bar "PROJ range" instead -- never hardcoded to "vbd"', () => {
    renderFirst(withOverride({ ci_low: 260, ci_high: 340, ci_applies_to: 'projected_points' }));
    expect(screen.getByText('PROJ range')).toBeInTheDocument();
    expect(screen.queryByText('VBD range')).not.toBeInTheDocument();
  });

  it('an unrecognized ci_applies_to renders an honest in-place note, no bar, no VBD/PROJ mislabel', () => {
    renderFirst(withOverride({ ci_low: 1, ci_high: 2, ci_applies_to: 'snap_share' }));
    expect(screen.queryByText('VBD range')).not.toBeInTheDocument();
    expect(screen.queryByText('PROJ range')).not.toBeInTheDocument();
    expect(screen.getByText(/does not display/i)).toBeInTheDocument();
    expect(screen.getByText(/snap_share/)).toBeInTheDocument();
  });

  it('no interval on the row at all: no bar, no caption, no crash', () => {
    renderFirst(withOverride({ ci_low: null, ci_high: null }));
    expect(screen.queryByText('VBD range')).not.toBeInTheDocument();
    expect(screen.queryByText('PROJ range')).not.toBeInTheDocument();
  });
});
