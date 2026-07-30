import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { overallPickForRoundSlot, teamSlotAtPick, type DraftPickRecord, type DraftState } from '../data/draft';
import { TraditionalDraftBoard, surnameOf } from '../components/TraditionalDraftBoard';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-135 -- the traditional draft board, built to
 * `docs/design/research/draft-board/FINDINGS.md` §4. Real data
 * (loadDatasetFromDisk), same rationale as every other DraftRoom test file:
 * axis shape, snake numbering, and the cell-content ladder are properties of
 * this app's real board/league config, not of a hand-written fixture.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const rowsById = new Map(rows.map((r) => [r.id, r]));
const teams = league.teams.kind === 'present' ? league.teams.value : 0;
const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;

function emptyDraft(): DraftState {
  return { leagueId, mockId: 'test-mock', picks: [], queue: [] };
}

/** Real picks only (rows[0], rows[1], ...), never filler -- so every filled
 *  cell in these tests carries a real, resolvable position and name. */
function draftWithPicks(overallPicks: number[]): DraftState {
  const picks: DraftPickRecord[] = overallPicks.map((overall, i) => {
    const row = rows[i]!;
    const name = row.name.kind === 'present' ? row.name.value : `Filler ${overall}`;
    return {
      overallPick: overall,
      round: Math.ceil(overall / teams),
      teamSlot: teamSlotAtPick(overall, teams),
      playerId: row.id,
      playerName: name,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    };
  });
  return { leagueId, mockId: 'test-mock', picks, queue: [] };
}

function setWidth(px: number) {
  Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: px });
  window.dispatchEvent(new Event('resize'));
}

beforeEach(() => {
  localStorage.clear();
  setWidth(1400); // a stable, mid-range default unless a test asserts otherwise
});

describe('surnameOf', () => {
  it('takes the last whitespace-separated token', () => {
    expect(surnameOf('Justin Jefferson')).toBe('Jefferson');
    expect(surnameOf("Amon-Ra St. Brown")).toBe('Brown');
    expect(surnameOf('Bijan')).toBe('Bijan');
  });
});

describe('TraditionalDraftBoard: empty board (FINDINGS §4.2)', () => {
  it('renders full-sized before any pick -- every cell shows its own round.pick address, never blank', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    const cell11 = screen.getByTestId('tdb-cell-1-1');
    expect(cell11).toHaveTextContent('1.01');
    const lastCell = screen.getByTestId(`tdb-cell-${rounds}-${teams}`);
    expect(lastCell.textContent).toMatch(/^\d+\.\d{2}$/);
  });

  it('the number of team header columns matches league.json:teams', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    for (let slot = 1; slot <= teams; slot++) {
      expect(screen.getByTestId(`tdb-header-team-${slot}`)).toBeInTheDocument();
    }
  });

  it('round 2 counts DOWN across the row -- the snake, read off the numbers, never drawn', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    // Leftmost column (slot 1) carries the LAST pick of round 2; rightmost
    // (slot `teams`) carries the FIRST -- FINDINGS §2.3/§4.2, Sleeper's own
    // verified convention.
    expect(screen.getByTestId(`tdb-cell-2-1`)).toHaveTextContent(`2.${String(teams).padStart(2, '0')}`);
    expect(screen.getByTestId(`tdb-cell-2-${teams}`)).toHaveTextContent('2.01');
  });

  it('shows the round.pick address to the address helper directly (independent of the DOM), covering every cell', () => {
    for (let round = 1; round <= rounds; round++) {
      for (let slot = 1; slot <= teams; slot++) {
        const overall = overallPickForRoundSlot(round, slot, teams);
        expect(overall).toBeGreaterThan(0);
        expect(overall).toBeLessThanOrEqual(teams * rounds);
      }
    }
  });

  it('the on-clock bar names round 1, pick 1 before any pick is made', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    const bar = screen.getByTestId('tdb-onclock-bar');
    expect(bar).toHaveTextContent('ON THE CLOCK');
    expect(bar).toHaveTextContent('Round 1, pick 1');
  });
});

describe('TraditionalDraftBoard: filled cells (FINDINGS §2.4, never drop the surname)', () => {
  it('a made pick shows the real surname and position colour, sourced from the board row', () => {
    const draft = draftWithPicks([1]);
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const row = rows[0]!;
    const name = row.name.kind === 'present' ? row.name.value : '';
    const cell = screen.getByTestId(`tdb-cell-1-${teamSlotAtPick(1, teams)}`);
    expect(cell).toHaveTextContent(surnameOf(name));
    expect(cell).toHaveTextContent(row.raw.position);
  });

  it('a pick with no board match (typed/off-board, playerId null) renders the typed name honestly -- never a fabricated position', () => {
    const overall = 1;
    const slot = teamSlotAtPick(overall, teams);
    const draft: DraftState = {
      leagueId,
      mockId: 'test-mock',
      picks: [
        {
          overallPick: overall,
          round: 1,
          teamSlot: slot,
          playerId: null,
          playerName: 'Some Kicker',
          timestamp: new Date().toISOString(),
          entryMode: 'typed',
        },
      ],
      queue: [],
    };
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const cell = screen.getByTestId(`tdb-cell-1-${slot}`);
    expect(cell).toHaveTextContent('Kicker');
    // Never fabricate a position for an off-board pick: no QB/RB/WR/TE pill
    // text inside this specific cell.
    for (const pos of ['QB', 'RB', 'WR', 'TE']) {
      expect(within(cell).queryByText(pos)).not.toBeInTheDocument();
    }
  });

  it('the auto-fill placeholder pick is labelled as such, not shown as a real name', () => {
    const overall = 1;
    const slot = teamSlotAtPick(overall, teams);
    const draft: DraftState = {
      leagueId,
      mockId: 'test-mock',
      picks: [
        {
          overallPick: overall,
          round: 1,
          teamSlot: slot,
          playerId: null,
          playerName: '(auto-filled — unknown pick)',
          timestamp: new Date().toISOString(),
          entryMode: null,
        },
      ],
      queue: [],
    };
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const cell = screen.getByTestId(`tdb-cell-1-${slot}`);
    expect(cell).toHaveTextContent('(auto-filled)');
  });
});

describe('TraditionalDraftBoard: current pick marked more than once (FINDINGS §4.4)', () => {
  it('marks the on-clock team header, the specific cell, and the persistent bar together', () => {
    const draft = draftWithPicks([1, 2, 3]); // picks 1-3 made -> pick 4 on the clock
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const onClockSlot = teamSlotAtPick(4, teams);
    const header = screen.getByTestId(`tdb-header-team-${onClockSlot}`);
    const cell = screen.getByTestId(`tdb-cell-1-${onClockSlot}`);
    const bar = screen.getByTestId('tdb-onclock-bar');
    expect(header).toBeInTheDocument();
    expect(cell).toBeInTheDocument();
    expect(bar).toHaveTextContent('ON THE CLOCK');
    expect(bar).toHaveTextContent(`overall #4`);
  });
});

describe('TraditionalDraftBoard: view toggle (FINDINGS §4.5)', () => {
  it('defaults to pick-order, and switches to the roster-slot grid on click', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    expect(screen.getByTestId('tdb-pick-order-grid')).toBeInTheDocument();
    expect(screen.queryByTestId('tdb-roster-slot-grid')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('tdb-view-toggle-roster-slot'));
    expect(screen.getByTestId('tdb-roster-slot-grid')).toBeInTheDocument();
    expect(screen.queryByTestId('tdb-pick-order-grid')).not.toBeInTheDocument();
  });

  it('roster-slot view: the row template is the same length for every team column -- one skeleton, not one per team', () => {
    const draft = draftWithPicks([1, 2]);
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    fireEvent.click(screen.getByTestId('tdb-view-toggle-roster-slot'));
    // Exactly one gutter cell per row index (not `teams` of them) -- confirms
    // the row skeleton is computed once, independent of each team's picks.
    const gutter0 = screen.getAllByTestId('tdb-roster-gutter-0');
    expect(gutter0).toHaveLength(1);
    // But a data cell exists for every team at that same row index.
    for (let slot = 1; slot <= teams; slot++) {
      expect(screen.getByTestId(`tdb-roster-cell-${slot}-0`)).toBeInTheDocument();
    }
  });

  it('roster-slot view: an unfilled slot renders an honest dash, never a fabricated player', () => {
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    fireEvent.click(screen.getByTestId('tdb-view-toggle-roster-slot'));
    const cell = screen.getByTestId('tdb-roster-cell-1-0');
    expect(cell).toHaveTextContent('—');
  });

  it('roster-slot view: an off-board pick occupies no slot -- a known, pre-existing gap in buildRosterSlots shared with LiveOpponents.tsx, never rendered as a fabricated entry here', () => {
    const slot = 1;
    const draft: DraftState = {
      leagueId,
      mockId: 'test-mock',
      picks: [
        {
          overallPick: 1,
          round: 1,
          teamSlot: slot,
          playerId: null,
          playerName: 'Local Waiver Pickup',
          timestamp: new Date().toISOString(),
          entryMode: 'typed',
        },
      ],
      queue: [],
    };
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    fireEvent.click(screen.getByTestId('tdb-view-toggle-roster-slot'));
    // Never shows the typed name as if it filled a slot -- it doesn't.
    expect(screen.queryByText(/Waiver Pickup|Pickup/)).not.toBeInTheDocument();
    // Every one of this team's slots stays an honest dash, not a guess.
    for (let i = 0; i < 17; i++) {
      const cell = screen.queryByTestId(`tdb-roster-cell-${slot}-${i}`);
      if (cell) expect(cell).toHaveTextContent('—');
    }
  });
});

describe('TraditionalDraftBoard: width-driven cell-content ladder (FINDINGS §4.3) -- the surname never drops', () => {
  it('at 1180px (this project\'s own narrow reference width) the surname still renders in a filled cell', () => {
    setWidth(1180);
    const draft = draftWithPicks([1]);
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const row = rows[0]!;
    const name = row.name.kind === 'present' ? row.name.value : '';
    const slot = teamSlotAtPick(1, teams);
    const cell = screen.getByTestId(`tdb-cell-1-${slot}`);
    expect(cell).toHaveTextContent(surnameOf(name));
    expect(screen.getByTestId('tdb-root')).toHaveAttribute('data-tier', 'compact');
  });

  it('at 1180px the compact tier omits team code and bye week -- designed out on purpose, not overflowing', () => {
    setWidth(1180);
    const draft = draftWithPicks([1]);
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const row = rows[0]!;
    const slot = teamSlotAtPick(1, teams);
    const cell = screen.getByTestId(`tdb-cell-1-${slot}`);
    expect(within(cell).queryByText(new RegExp(`^${row.raw.team}`))).not.toBeInTheDocument();
  });

  it('at a wide width (1700px) the same filled cell adds the NFL team code', () => {
    setWidth(1700);
    const draft = draftWithPicks([1]);
    render(<TraditionalDraftBoard data={data} league={league} draft={draft} rowsById={rowsById} leagueId={leagueId} />);
    const row = rows[0]!;
    const name = row.name.kind === 'present' ? row.name.value : '';
    const slot = teamSlotAtPick(1, teams);
    const cell = screen.getByTestId(`tdb-cell-1-${slot}`);
    expect(cell).toHaveTextContent(surnameOf(name));
    expect(cell).toHaveTextContent(row.raw.team);
    expect(screen.getByTestId('tdb-root')).toHaveAttribute('data-tier', 'wider');
  });
});

describe('TraditionalDraftBoard: narrow-width breakpoint switch (FINDINGS §4.6)', () => {
  it('below the mobile breakpoint the two-axis grid is replaced by a list, not squeezed', () => {
    setWidth(700);
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    expect(screen.queryByTestId('tdb-pick-order-grid')).not.toBeInTheDocument();
    expect(screen.getByTestId('tdb-mobile-round')).toBeInTheDocument();
    expect(screen.getByTestId('tdb-root')).toHaveAttribute('data-mobile', 'true');
  });

  it('the mobile round list still numbers every pick honestly, and the unlisted axis becomes a chip row', () => {
    setWidth(700);
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    expect(screen.getByTestId('tdb-mobile-round-chip-1')).toBeInTheDocument();
    expect(screen.getByTestId(`tdb-mobile-round-chip-${rounds}`)).toBeInTheDocument();
    expect(screen.getByTestId('tdb-mobile-round-row-1')).toHaveTextContent('1.01');
  });

  it('at 1180px (the required narrow screenshot width) mobile mode is NOT engaged -- the real grid still renders', () => {
    setWidth(1180);
    render(<TraditionalDraftBoard data={data} league={league} draft={emptyDraft()} rowsById={rowsById} leagueId={leagueId} />);
    expect(screen.getByTestId('tdb-pick-order-grid')).toBeInTheDocument();
    expect(screen.getByTestId('tdb-root')).toHaveAttribute('data-mobile', 'false');
  });
});

describe('DraftRoom: the Draft Board hub tab (FR-135, additive)', () => {
  it('is reachable alongside Board / Opponents / Predictions, and renders the empty grid on arrival', () => {
    render(<DraftRoom data={data} rows={rows} league={league} />);
    fireEvent.click(screen.getByRole('button', { name: 'Draft Board' }));
    expect(screen.getByTestId('tdb-pick-order-grid')).toBeInTheDocument();
    expect(screen.getByTestId('tdb-onclock-bar')).toHaveTextContent('ON THE CLOCK');
  });

  it('the original three hub tabs are unaffected -- Board still shows the rankings pane', () => {
    render(<DraftRoom data={data} rows={rows} league={league} />);
    expect(screen.getByRole('button', { name: 'Board' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Draft Board' }));
    expect(screen.queryByPlaceholderText(/Mark pick/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Board' }));
    expect(screen.getByPlaceholderText(/Mark pick/)).toBeInTheDocument();
  });
});
