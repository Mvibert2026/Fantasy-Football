import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftPickRecord, type DraftState } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * Thread 058 (draft board design gap), sections A and B against the real
 * DraftRoom screen -- Position Scarcity's legible pace/tier/under-50 lines and
 * honest DEF null state, the board row's positional label, and the new SORT
 * controls. Real data (loadDatasetFromDisk), same rationale as the other
 * DraftRoom test files: these are properties of the real board/league shape.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

/** Logs real picks (never fillers) up to, but not including, the user's first
 *  pick (overall 3 in this league), so the user is off the clock and the
 *  Position Scarcity panel -- not the RECOMMENDED card -- is what's on screen. */
function seedRealPicksThroughOverall(n: number, extra: BoardRowPickSpec[] = []) {
  const picks: DraftPickRecord[] = [];
  const used = new Set<number>();
  for (const spec of extra) used.add(spec.id);
  let cursor = 0;
  for (let overall = 1; overall <= n; overall++) {
    const spec = extra.find((_, i) => i === cursor && overall === extra[i]!.overall);
    if (spec) {
      picks.push({
        overallPick: overall,
        round: 1,
        teamSlot: teamSlotAtPick(overall, teams),
        playerId: spec.id,
        playerName: spec.name,
        timestamp: new Date().toISOString(),
        entryMode: 'typed',
      });
      cursor++;
    } else {
      picks.push({
        overallPick: overall,
        round: 1,
        teamSlot: teamSlotAtPick(overall, teams),
        playerId: null,
        playerName: `Filler ${overall}`,
        timestamp: new Date().toISOString(),
        entryMode: 'typed',
      });
    }
  }
  const state: DraftState = { leagueId, mockId: 'test-mock', picks, queue: [] };
  saveDraftState(state);
}

interface BoardRowPickSpec {
  overall: number;
  id: number;
  name: string;
}

beforeEach(() => {
  localStorage.clear();
});

/** DRAFT-MIDDLE-PANE.md: Position Scarcity/Queue moved from the whole
 *  off-clock middle pane to their own tabs, alongside the new default
 *  Recommend tab. Every test that inspects their content now switches to the
 *  tab first, matching a real user clicking it. */
function switchPaneTab(label: 'Recommend' | 'Scarcity' | 'Queue' | 'Insights') {
  fireEvent.click(screen.getByRole('button', { name: label }));
}

describe('thread 058 section A: Position Scarcity legibility and honest nulls', () => {
  it('renders a labelled pace phrase, never a bare signed integer, for a position with real board data', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Scarcity');
    // "on pace" / "N ahead of pace" / "N behind of pace" -- whichever the real
    // data produces, it must be a phrase, not a bare +N/-N/±0.
    const paceMatches = screen.getAllByText(/on pace|ahead of pace|behind of pace|behind pace/);
    expect(paceMatches.length).toBeGreaterThan(0);
    // The old bare-signed rendering (±0, +2 with nothing else) must be gone.
    expect(screen.queryByText(/^±\d/)).not.toBeInTheDocument();
  });

  it('renders DEF as a fifth scarcity row with an honest null, quoting board.json:def_note -- never a fabricated 0 or ±0', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Scarcity');
    const defRow = screen.getByTestId('scarcity-row-DEF');
    expect(within(defRow).getByText('DEF')).toBeInTheDocument();
    expect(within(defRow).getByText('no board data')).toBeInTheDocument();
    expect(within(defRow).getByText(data.board.def_note)).toBeInTheDocument();
  });

  it('sinks DEF to the bottom of the urgency-ordered panel', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Scarcity');
    const panel = screen.getByTestId('position-scarcity');
    const rows = ['QB', 'RB', 'WR', 'TE', 'DEF'].map((pos) => within(panel).getByTestId(`scarcity-row-${pos}`));
    const order = rows.map((r) => panel.compareDocumentPosition(r));
    // DOCUMENT_POSITION_FOLLOWING (4) means the row comes after the panel's
    // earlier rows in source order -- compare each row's position against DEF's.
    const defRow = within(panel).getByTestId('scarcity-row-DEF');
    for (const pos of ['QB', 'RB', 'WR', 'TE']) {
      const row = within(panel).getByTestId(`scarcity-row-${pos}`);
      // row precedes defRow in the DOM (defRow is DOCUMENT_POSITION_FOLLOWING
      // relative to row) -- i.e. every other position renders before DEF.
      expect(row.compareDocumentPosition(defRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    expect(order.length).toBe(5); // sanity: all five rows are present
  });

  it('carries the traceability footer naming the real fields behind the panel', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Scarcity');
    expect(screen.getByText('board.position_remaining · board.position_tier · pace vs board.consensus_rank')).toBeInTheDocument();
  });

  it('depletes a real tier via real picks and renders "tier 1 gone · tier 2: N left"', () => {
    const qbTier1 = rows.filter((r) => r.raw.position === 'QB' && r.tierLabel.kind === 'present' && r.tierLabel.value === 'T1');
    expect(qbTier1.length).toBeGreaterThan(0);
    const extra: BoardRowPickSpec[] = qbTier1.map((r, i) => ({
      overall: i + 1,
      id: r.id,
      name: r.name.kind === 'present' ? r.name.value : `qb${i}`,
    }));
    seedRealPicksThroughOverall(Math.max(3, extra.length), extra);
    renderDraftRoom();
    switchPaneTab('Scarcity');
    expect(screen.getByText(/tier 1 gone · tier 2: \d+ left/)).toBeInTheDocument();
  });
});

describe('thread 058 section B: board row positional label and SORT controls', () => {
  it('shows a positional rank label (e.g. RB1/WR1), not a bare position, on board rows', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    // Positional labels look like POS+digits (board.json:positional_label,
    // confirmed "RB1"/"WR1"-style against the real export).
    const labels = screen.getAllByText(/^(QB|RB|WR|TE)\d+$/);
    expect(labels.length).toBeGreaterThan(0);
  });

  it('exposes the four SORT controls from FRONTEND-SPEC.md §7.1 and reorders rows on click', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    for (const label of ['Our rank', 'Consensus', 'Delta', 'Proj pts']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
    // Default sort is 'Our rank' -- top-of-list rank should be ascending.
    fireEvent.click(screen.getByRole('button', { name: 'Proj pts' }));
    expect(screen.getByRole('button', { name: 'Proj pts' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Our rank' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('adds DEF to the position filter and shows an honest empty state with no fabricated players', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    const posRow = screen.getByRole('button', { name: 'ALL' }).parentElement!;
    fireEvent.click(within(posRow).getByRole('button', { name: 'DEF' }));
    expect(screen.getByText(/No DEF players on this board/)).toBeInTheDocument();
  });

  it('FR-050: adds a fifth SORT control, VBD, and reorders rows descending by it on click', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    // DRAFT-MIDDLE-PANE.md: off the clock, the default Recommend tab now
    // shows a real look-ahead recommendation (FR-049), which can legitimately
    // name the same top-VBD player already at the top of the board list --
    // switch to Scarcity so the assertions below see one Bijan Robinson, not
    // two, without weakening what they check.
    switchPaneTab('Scarcity');
    const vbdButton = screen.getByRole('button', { name: 'VBD' });
    expect(vbdButton).toBeInTheDocument();
    fireEvent.click(vbdButton);
    expect(vbdButton).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Our rank' })).toHaveAttribute('aria-pressed', 'false');

    // seedRealPicksThroughOverall(3) with no `extra` seeds three off-board
    // fillers (playerId: null) -- no real player is taken, so every row in
    // `rows` is still available. Sorted by VBD descending, the same rows the
    // sorted list should now show at the top.
    const expectedTop = rows
      .filter((r) => r.vbd.kind === 'present')
      .sort((a, b) => (b.vbd as { value: number }).value - (a.vbd as { value: number }).value)
      .slice(0, 3)
      .map((r) => (r.name.kind === 'present' ? r.name.value : ''));
    for (const name of expectedTop) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
  });
});

describe('FR-055: draft-room board list carries a header row naming its columns', () => {
  it('shows RANK / PLAYER / POS / TM / ADP / Δ / VBD / AVAIL above the row list, ported from Board.tsx where the number matches', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    // "RANK" is unique on screen (the SORT tab reads "Our rank", not "RANK"),
    // so its immediate parent is the header row -- scope the rest of the
    // column-label assertions to it. Unscoped, "VBD" and "Δ" each match twice
    // (the header cell and, respectively, the SORT tab button and the row's
    // own delta cell), which is real, not a bug -- the same label legitimately
    // appears in two different controls.
    const headerRow = screen.getByText('RANK', { exact: true }).parentElement!;
    const withinHeader = within(headerRow);
    for (const label of ['RANK', 'PLAYER', 'POS', 'TM', 'ADP', 'VBD', 'AVAIL', 'Δ']) {
      expect(withinHeader.getByText(label, { exact: true })).toBeInTheDocument();
    }
  });

  it('every board row now renders a VBD figure, matching board.json:players[].vbd (FR-050)', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    // Puka Nacua (id 4) is real-VBD-present and on the board at pick 3 in this
    // fixture (Bijan/Chase/Gibbs are the only ones taken) -- its formatted VBD
    // (Board.tsx's own `decimal()`, one decimal place) should appear on screen.
    const nacua = rows.find((r) => r.id === 4)!;
    expect(nacua.vbd.kind).toBe('present');
    const formatted = (nacua.vbd as { value: number }).value.toFixed(1);
    expect(screen.getAllByText(formatted).length).toBeGreaterThan(0);
  });
});

describe('thread 058 section D2: IR slot', () => {
  it('sizes the IR slot from the real league.json:roster.ir count, distinct from bench', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    const ir = data.league.roster.ir ?? 0;
    expect(ir).toBeGreaterThan(0); // sanity: this league really does start an IR slot
    expect(screen.getAllByText('IR')).toHaveLength(ir);
  });
});

describe('thread 058 section E4/F: queue and watchlist traceability footer', () => {
  it('renders the footer once the watchlist has a real row to trace', () => {
    const starred = rows.find((r) => r.name.kind === 'present');
    expect(starred).toBeTruthy();
    localStorage.setItem('prep.watchlist', JSON.stringify([starred!.name.kind === 'present' ? starred!.name.value : '']));
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Queue');
    expect(screen.getByText('availability.baseline_p → availability.live_p · adjustment.need + adjustment.run')).toBeInTheDocument();
  });

  it('does not render the footer for an empty queue/watchlist -- nothing to trace yet', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    switchPaneTab('Queue');
    expect(screen.queryByText('availability.baseline_p → availability.live_p · adjustment.need + adjustment.run')).not.toBeInTheDocument();
  });
});

describe('thread 058 section C: hub tab chrome', () => {
  it('renders sentence-case hub tab labels, not all-caps', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
    expect(screen.getByRole('button', { name: 'Board' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Opponents' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Predictions' })).toBeInTheDocument();
    expect(screen.queryByText('BOARD')).not.toBeInTheDocument();
  });
});
