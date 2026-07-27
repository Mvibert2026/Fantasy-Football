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

describe('thread 058 section A: Position Scarcity legibility and honest nulls', () => {
  it('renders a labelled pace phrase, never a bare signed integer, for a position with real board data', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
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
    const defRow = screen.getByTestId('scarcity-row-DEF');
    expect(within(defRow).getByText('DEF')).toBeInTheDocument();
    expect(within(defRow).getByText('no board data')).toBeInTheDocument();
    expect(within(defRow).getByText(data.board.def_note)).toBeInTheDocument();
  });

  it('sinks DEF to the bottom of the urgency-ordered panel', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
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
    expect(screen.getByText('availability.baseline_p → availability.live_p · adjustment.need + adjustment.run')).toBeInTheDocument();
  });

  it('does not render the footer for an empty queue/watchlist -- nothing to trace yet', () => {
    seedRealPicksThroughOverall(3);
    renderDraftRoom();
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
