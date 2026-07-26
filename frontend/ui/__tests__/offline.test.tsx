import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { ask } from '../assistant';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * Fails if the app stops working when the proxy is stopped.
 *
 * The guarantee under test: the export-query lane is local computation over static
 * JSON and must never depend on the network. A draft is exactly when the network is
 * least reliable and the board matters most, so "works until the proxy dies" is not
 * good enough.
 *
 * The proxy is simulated as stopped by rejecting any fetch to /__reasoning while
 * letting static file reads through -- which is what actually happens when the dev
 * server's middleware is unavailable but the page is already loaded.
 */

const data = loadDatasetFromDisk();

/** Serves public/data from disk; rejects the reasoning endpoint as if the proxy were down. */
function installOfflineProxyFetch() {
  const files: Record<string, unknown> = {
    'data/_manifest.json': data.manifest,
    'data/board.json': data.board,
    'data/league.json': data.league,
    'data/glossary.json': data.glossary,
    'data/nulls.json': data.nulls,
    'data/strategies.json': data.strategies,
    'data/availability.json': data.availability,
    'data/opponents.json': data.opponents,
  };

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('__reasoning') || url.includes('__refresh')) {
        throw new TypeError('Failed to fetch');
      }

      const key = Object.keys(files).find((f) => url.includes(f));
      if (key) {
        return new Response(JSON.stringify(files[key]), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      }
      // feed.json legitimately does not exist.
      return new Response('not found', { status: 404 });
    }),
  );
}

describe('the app works with the proxy stopped', () => {
  beforeEach(installOfflineProxyFetch);
  afterEach(() => vi.unstubAllGlobals());

  it('renders the board from static files', async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Board' })).toBeInTheDocument());

    // A real player from the export, proving the table populated rather than erroring.
    const first = data.board.players[0]!.player;
    expect(await screen.findByText(first)).toBeInTheDocument();
  });

  it('answers an export-template query with MODEL claims and no network', async () => {
    const rows = buildRows(data);
    const league = buildLeagueConfig(data);

    const answer = await ask('what are the startable thresholds', { data, rows, league });

    expect(answer.lane).toBe('export');
    expect(answer.claims.length).toBeGreaterThan(0);
    expect(answer.claims.every((c) => c.tag === 'MODEL')).toBe(true);
    expect(answer.notice).toBeUndefined();

    // The thresholds came from league config, not from a hardcoded set.
    const text = answer.claims.map((c) => c.text).join(' ');
    for (const [pos, level] of Object.entries(data.league.replacement_levels)) {
      expect(text).toContain(`${pos}${level}`);
    }
  });

  it('answers best-available and compare queries with the proxy down', async () => {
    const rows = buildRows(data);
    const league = buildLeagueConfig(data);
    const ctx = { data, rows, league };

    const best = await ask('best available at pick 23', ctx);
    expect(best.lane).toBe('export');
    expect(best.claims.every((c) => c.tag === 'MODEL')).toBe(true);

    const a = data.board.players[0]!.player;
    const b = data.board.players[1]!.player;
    const compare = await ask(`compare ${a} and ${b}`, ctx);
    expect(compare.lane).toBe('export');
    expect(compare.claims.some((c) => c.text.includes(a))).toBe(true);
    expect(compare.claims.some((c) => c.text.includes(b))).toBe(true);
  });

  it('reports the reasoning lane unavailable instead of failing', async () => {
    const rows = buildRows(data);
    const league = buildLeagueConfig(data);

    // A question with retrievable context but no matching template, so it routes to
    // the reasoning lane -- which cannot reach the proxy.
    const player = data.board.players[0]!.player;
    const answer = await ask(`ramble about ${player} in general terms`, { data, rows, league });

    expect(answer.lane).toBe('reasoning');
    expect(answer.claims).toHaveLength(0);
    expect(answer.notice).toBeTruthy();
    expect(answer.notice).toMatch(/could not be reached/i);
    // The point of the message: everything else still works.
    expect(answer.notice).toMatch(/keeps working|never touch the network/i);
  });

  it('still lets the user switch views with the proxy down', async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Board' })).toBeInTheDocument());

    // Nav items are the sidebar's rows, not a horizontal tab bar -- see
    // ui/components/shell/Sidebar.tsx. "Strategy guide" (the view's own heading) is
    // lowercase-g where "Strategy Guide" (the nav label) is not; both are correct,
    // matching what's actually rendered in each place.
    await userEvent.click(screen.getByRole('button', { name: 'Strategy Guide' }));
    expect(await screen.findByRole('heading', { name: 'Strategy guide' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Methodology' }));
    expect(await screen.findByRole('heading', { name: 'Methodology' })).toBeInTheDocument();
  });
});
