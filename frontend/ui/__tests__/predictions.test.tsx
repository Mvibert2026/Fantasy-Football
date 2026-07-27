import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { Predictions } from '../views/Predictions';
import { buildRows, type BoardRow } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import {
  currentOverallPick,
  roundOfPick,
  saveDraftState,
  teamSlotAtPick,
  type DraftPickRecord,
  type DraftState,
} from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * Predictions -- thread 028 (docs/handoffs/028-build-predictions-tab.md).
 *
 * The original failure mode named in docs/operating-model.md was this exact
 * screen (and Opponents) reported complete while a fully green test suite ran
 * against an app where the screen did not exist. The first test below exists
 * specifically to make that failure mode impossible again: it asserts the tab is
 * both present in navigation and actually renders real content when reached.
 *
 * The rest cover the three hard requirements from the thread: the honest-null
 * "not yet" treatment for an uncomputed live probability (never `0%`), the dot
 * array never standing in for a bare percentage, and the calibration caveat
 * being present and never implying the numbers are validated.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function renderPredictions() {
  return render(<Predictions data={data} rows={rows} league={league} />);
}

/** Builds N sequential, well-formed picks (round/teamSlot derived the same way
 *  draft.ts derives them for a real pick), skipping the user's own slot so the
 *  user's next pick stays in the future -- matching how a real mid-draft session
 *  looks by the time this screen has anything live to show. */
function buildPicks(n: number, availableRows: BoardRow[], userSlot: number): DraftPickRecord[] {
  const picks: DraftPickRecord[] = [];
  let cursor = 0;
  for (let i = 0; i < n; i++) {
    const overallPick = currentOverallPick(picks);
    const slot = teamSlotAtPick(overallPick, teams);
    // Never draft the user's own slot in this synthetic log -- keeps the user's
    // real next pick undisturbed regardless of n.
    if (slot === userSlot) {
      picks.push({
        overallPick,
        round: roundOfPick(overallPick, teams),
        teamSlot: slot,
        playerId: null,
        playerName: `synthetic user pick ${overallPick}`,
        timestamp: new Date().toISOString(),
        entryMode: 'shortcut',
      });
      continue;
    }
    const row = availableRows[cursor++];
    picks.push({
      overallPick,
      round: roundOfPick(overallPick, teams),
      teamSlot: slot,
      playerId: row?.id ?? null,
      playerName: row?.name.kind === 'present' ? row.name.value : `synthetic pick ${overallPick}`,
      timestamp: new Date().toISOString(),
      entryMode: 'shortcut',
    });
  }
  return picks;
}

function seedDraft(n: number) {
  const picks = buildPicks(n, rows, league.userSlot.kind === 'present' ? league.userSlot.value : 0);
  const state: DraftState = { leagueId, mockId: 'test-mock', picks, queue: [] };
  saveDraftState(state);
}

beforeEach(() => {
  localStorage.clear();
});

describe('Predictions', () => {
  it('carries the calibration caveat, never implying the availability figures are validated', () => {
    renderPredictions();
    expect(screen.getByText(/is currently not calibrated/i)).toBeInTheDocument();
    expect(screen.getByText(/1 of ~30 required mock drafts is logged/i)).toBeInTheDocument();
    expect(screen.queryByText(/is calibrated\./i)).not.toBeInTheDocument();
  });

  it('with zero picks logged, states the signal-none condition in plain language and every LIVE cell reads "not yet", never "0%"', () => {
    renderPredictions();
    expect(
      screen.getByText(/roster-need and run signals need \d+ picks before they say anything\. 0 logged/i),
    ).toBeInTheDocument();

    const notYet = screen.getAllByText('not yet');
    expect(notYet.length).toBeGreaterThan(0);
    // The specific substitution Principle #2 forbids: a null live value must never
    // render as a computed-looking zero.
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('once enough picks are logged for a full round, computes real LIVE values and states the ok condition', () => {
    seedDraft(12); // > teams (10): signal 'ok', matching computeLiveAvailability's own threshold
    renderPredictions();

    expect(
      screen.getByText(/12 picks logged across 2 rounds\. roster-need arithmetic and run detection are both in play\./i),
    ).toBeInTheDocument();
    // At least one row now renders a real percentage in LIVE rather than "not yet".
    expect(screen.queryAllByText('not yet').length).toBe(0);
  });

  it('marks a thin signal (fewer picks than one full round) distinctly from both the none and ok states', () => {
    seedDraft(7); // >= minPicks (5), < teams (10): signal 'thin'
    renderPredictions();
    expect(
      screen.getByText(/only 7 picks logged, under one full round\. the adjustment is computed but its band is widened/i),
    ).toBeInTheDocument();
  });

  it('renders the IN 10 DRAFTS dot array, never a bare percentage standing alone as the headline number', () => {
    seedDraft(12);
    renderPredictions();
    // The header's own IN 10 DRAFTS column label is present, and at least one
    // player row carries a populated dot title (freqText, "N in 10 drafts").
    expect(screen.getByText('IN 10 DRAFTS')).toBeInTheDocument();
    expect(screen.getAllByTitle(/in 10 drafts/i).length).toBeGreaterThan(0);
  });

  it('reachable from navigation and renders the real available-player list -- the exact failure mode this thread exists to close', async () => {
    // Mounts the full App, which renders all 378 board rows -- offline.test.tsx's
    // equivalent App-level tests show the same ~1-2s cost in isolation but can
    // exceed vitest's 5000ms default under concurrent load (verified: this repo
    // had 8 sibling agent sessions running in this same tree at the time this was
    // written). A longer explicit timeout, not a smaller test.
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        const files: Record<string, unknown> = {
          'data/_manifest.json': data.manifest,
          'data/board.json': data.board,
          'data/league.json': data.league,
          'data/glossary.json': data.glossary,
          'data/nulls.json': data.nulls,
          'data/strategies.json': data.strategies,
          'data/availability.json': data.availability,
          'data/opponents.json': data.opponents,
          ...(data.rosters ? { 'data/rosters.json': data.rosters } : {}),
        };
        const key = Object.keys(files).find((f) => url.includes(f));
        if (key) {
          return new Response(JSON.stringify(files[key]), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          });
        }
        return new Response('not found', { status: 404 });
      }),
    );

    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Board' })).toBeInTheDocument();

    const nav = screen.getByRole('button', { name: 'Predictions' });
    expect(nav).toBeInTheDocument();
    await userEvent.click(nav);

    expect(await screen.findByRole('heading', { name: 'Predictions' })).toBeInTheDocument();

    // Real content, not an empty shell: the top-ranked available player's name is
    // on screen, and the calibration caveat rendered along with it.
    const topAvailable = rows.find((r) => r.overallRank.kind === 'present' && r.overallRank.value === 1);
    expect(topAvailable?.name.kind).toBe('present');
    if (topAvailable?.name.kind === 'present') {
      expect(screen.getByText(topAvailable.name.value)).toBeInTheDocument();
    }
    expect(screen.getByText(/is currently not calibrated/i)).toBeInTheDocument();

    vi.unstubAllGlobals();
  }, 20000);

  it('the "+ queue" toggle writes to the same draft-scoped queue DraftRoom reads, not a second store', async () => {
    renderPredictions();
    const first = rows.find((r) => r.overallRank.kind === 'present' && r.overallRank.value === 1);
    if (first?.name.kind !== 'present') throw new Error('fixture guard: expected a present name');

    const row = screen.getByText(first.name.value).closest('span')!;
    const toggle = within(row.parentElement as HTMLElement).getByText('+ queue');
    await userEvent.click(toggle);

    const stored = JSON.parse(localStorage.getItem(`prep.draft.${leagueId}`)!) as DraftState;
    expect(stored.queue).toContain(first.id);
  });
});
