import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { Board } from '../views/Board';
import { loadDatasetFromDisk } from './helpers';

/**
 * Threads 069 and 073 (contract 1.11.0/1.12.0 display work).
 *
 * The suspension fields are unconditional on every 1.12.0 row but every live
 * value is the "not suspended" default today -- data/suspensions_2026.json is
 * verified-empty (ADR-053), not unpopulated by accident. So the real export can
 * only prove the badge and detail block correctly do NOT render; the states
 * that must render are exercised on a synthetic row derived from the real one.
 * Both directions are covered so neither can regress silently: fabricating a
 * flag on a clean row is as much a defect as dropping it on a suspended one.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

/** Real dataset with player 0's suspension fields overridden. */
function withSuspendedFirstPlayer(overrides: Partial<RawBoardPlayer>): Dataset {
  return {
    ...data,
    board: {
      ...data.board,
      players: data.board.players.map((p, i) => (i === 0 ? { ...p, ...overrides } : p)),
    },
  } as Dataset;
}

function renderDetail(dataset: Dataset) {
  const detailRows = buildRows(dataset);
  const first = detailRows[0];
  if (!first) throw new Error('Real board export has zero players -- fixture assumption broken.');
  return render(
    <PlayerDetail
      row={first}
      rows={detailRows}
      data={dataset}
      league={league}
      picks={[]}
      watchlist={[]}
      onToggleWatch={() => {}}
      onClose={vi.fn()}
    />,
  );
}

describe('board header scoring format (thread 069)', () => {
  it('shows the export-confirmed scoring format beside the consensus source', () => {
    // Guard the fixture: the live export must actually confirm a format for
    // this assertion to mean anything (it is "half_ppr" as of contract 1.11.0).
    expect(data.board.scoring_format).toBeTruthy();

    render(<Board data={data} rows={rows} league={league} />);

    const expected = `${data.board.consensus_source} · ${data.board.scoring_format!.replace(/_/g, ' ')}`;
    expect(screen.getByText(new RegExp(expected))).toBeInTheDocument();
  });

  it('says "scoring format unconfirmed" when the export carries null, never a guessed format', () => {
    const noFormat = { ...data, board: { ...data.board, scoring_format: null } } as Dataset;

    render(<Board data={noFormat} rows={rows} league={league} />);

    expect(screen.getByText(/scoring format unconfirmed/)).toBeInTheDocument();
    expect(screen.queryByText(/half ppr/)).not.toBeInTheDocument();
  });
});

describe('suspension display (thread 073)', () => {
  it('renders exactly as many SUSP badges as rows with suspension_flag true (zero on the live export today)', () => {
    const flagged = rows.filter((r) => r.raw.suspension_flag === true).length;

    render(<Board data={data} rows={rows} league={league} />);

    expect(screen.queryAllByText('SUSP')).toHaveLength(flagged);
  });

  it('badges a row whose export says a suspension is on file', () => {
    const dataset = withSuspendedFirstPlayer({
      suspension_flag: true,
      suspension_games: 6,
      projected_points_suspension_adjusted: 180.4,
      suspension_adjustment_note: 'games_adjusted',
    });

    render(<Board data={dataset} rows={buildRows(dataset)} league={league} />);

    expect(screen.getAllByText('SUSP')).toHaveLength(1);
  });

  it('detail sheet shows games and the adjusted projection for a games_adjusted row', () => {
    renderDetail(
      withSuspendedFirstPlayer({
        suspension_flag: true,
        suspension_games: 6,
        projected_points_suspension_adjusted: 180.4,
        suspension_adjustment_note: 'games_adjusted',
      }),
    );

    const note = screen.getByTestId('suspension-note');
    expect(note).toHaveTextContent('SUSPENSION ON FILE');
    expect(note).toHaveTextContent('Suspended 6 games');
    expect(note).toHaveTextContent('180.4');
    expect(note).toHaveTextContent('board.json:suspension_flag');
  });

  it('detail sheet explains a pending appeal instead of fabricating an adjusted number', () => {
    renderDetail(
      withSuspendedFirstPlayer({
        suspension_flag: true,
        suspension_games: null,
        projected_points_suspension_adjusted: null,
        suspension_adjustment_note: 'not_adjusted_pending_appeal',
      }),
    );

    const note = screen.getByTestId('suspension-note');
    expect(note).toHaveTextContent('Appeal pending');
    expect(note).toHaveTextContent('deliberately not adjusted');
  });

  it('detail sheet renders no suspension block for an unsuspended row', () => {
    // Guard: this only tests the negative branch if row 0 really is unsuspended
    // (true for every row on the live export while the curated list is empty).
    expect(data.board.players[0]?.suspension_flag).toBe(false);

    renderDetail(data);

    expect(screen.queryByTestId('suspension-note')).not.toBeInTheDocument();
  });
});
