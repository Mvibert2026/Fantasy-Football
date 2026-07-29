import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { loadDatasetFromDisk } from './helpers';

/**
 * The founder asked twice for the "Refresh data" button to be removed -- it called
 * `/__refresh`, a dev-server-only endpoint that has never existed on the hosted
 * static build, so on the live site every click could only fail. See App.tsx's
 * `FreshnessNote` module doc for the full removal rationale.
 *
 * This locks in both halves of that fix: the button is gone, and the freshness
 * information it used to sit next to is still visible (a downgrade this project's
 * own standing rule explicitly warns against -- removing the control must not also
 * remove the fact it reported).
 */

const data = loadDatasetFromDisk();

function installFetch() {
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
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const key = Object.keys(files).find((f) => url.includes(f));
      if (key) {
        return new Response(JSON.stringify(files[key]), { status: 200, headers: { 'content-type': 'application/json' } });
      }
      return new Response('not found', { status: 404 });
    }),
  );
}

describe('Refresh data button removal', () => {
  it('renders no "Refresh data" button anywhere, but keeps the freshness note', async () => {
    installFetch();
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Board' })).toBeInTheDocument();

    expect(screen.queryByRole('button', { name: /refresh data/i })).not.toBeInTheDocument();

    const note = screen.getByTestId('freshness-note');
    expect(note.textContent).toContain('exported');
    expect(note.textContent).toMatch(/snapshot (fresh|STALE)|snapshot freshness not exported/);

    vi.unstubAllGlobals();
  }, 15000);
});
