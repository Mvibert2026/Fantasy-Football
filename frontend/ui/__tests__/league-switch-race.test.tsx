import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { loadDatasetFromDisk } from './helpers';

/**
 * Regression test for a real bug found while verifying FR-036 (manual opponent
 * names), not part of that request itself: App.tsx's league-load effect had no
 * guard against out-of-order async resolution. `loadDataset(leagueId)` has no
 * cancellation; if `leagueId` changes again before an in-flight fetch resolves,
 * that stale call could still resolve *after* the newer one and silently overwrite
 * `data` with the wrong league's dataset -- `leagueId` (state) and `data.league`
 * (what's rendered) would then disagree, with no error and no loading state to
 * signal it. A Principle #3 violation, and worse than the principle's usual case:
 * not "still holds the pre-edit value" but "holds an actively wrong value that
 * looks current."
 *
 * Reproduced here by making the FIRST league's fetch resolve *slower* than the
 * SECOND league's, after the user has already switched back to the first league a
 * second time -- deliberately not a fast-click race, matching how it was actually
 * found (switches with real waits between them; see e2e/debug-fr036b.mjs for the
 * live-browser repro this test formalises).
 */

const data = loadDatasetFromDisk();

function secondLeagueFiles(leagueId: string): Record<string, unknown> {
  return {
    board: { ...data.board, league_id: leagueId },
    league: { ...data.league, league_id: leagueId, league_name: 'Second League' },
    glossary: { ...data.glossary, league_id: leagueId },
    nulls: { ...data.nulls, league_id: leagueId },
    strategies: { ...data.strategies, league_id: leagueId },
    availability: { ...data.availability, league_id: leagueId },
    opponents: { ...data.opponents, league_id: leagueId },
  };
}

describe('League switching: out-of-order async resolution', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('never lets a stale in-flight load overwrite a newer selection', async () => {
    const secondId = 'second-league';
    const secondFiles = secondLeagueFiles(secondId);
    const secondArtifacts = Object.fromEntries(
      Object.keys(secondFiles).map((name) => [
        name,
        { file: `leagues/${secondId}/${name}.json`, contract_version: '1.6.0', generated_utc: 'x', league_id: secondId, run_id: `${name}@x` },
      ]),
    );

    const defaultFiles: Record<string, unknown> = {
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

    // Every request for the DEFAULT league's league.json is deliberately delayed,
    // and delayed *more* on the second visit -- the exact shape of the real repro
    // (default -> second -> default (slow) -> second (fast), and the slow default
    // response must never win).
    let defaultLeagueFetchCount = 0;

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('data/_leagues.json')) {
          return new Response(JSON.stringify({ leagues: [{ id: secondId, label: 'Second League', artifacts: secondArtifacts }] }), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          });
        }

        if (url.includes(`leagues/${secondId}/`)) {
          const key = Object.keys(secondFiles).find((f) => url.endsWith(`${f}.json`));
          if (key) {
            return new Response(JSON.stringify(secondFiles[key]), { status: 200, headers: { 'content-type': 'application/json' } });
          }
          return new Response('not found', { status: 404 });
        }

        if (url.endsWith('data/league.json')) {
          defaultLeagueFetchCount += 1;
          // Second visit to the default league is deliberately slow, so its
          // response can only arrive after the second league's fast response --
          // the fix must ignore it when it finally does.
          if (defaultLeagueFetchCount >= 2) {
            await new Promise((r) => setTimeout(r, 300));
          }
          return new Response(JSON.stringify(data.league), { status: 200, headers: { 'content-type': 'application/json' } });
        }

        const key = Object.keys(defaultFiles).find((f) => url.includes(f));
        if (key) {
          return new Response(JSON.stringify(defaultFiles[key]), { status: 200, headers: { 'content-type': 'application/json' } });
        }
        return new Response('not found', { status: 404 });
      }),
    );

    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Board' })).toBeInTheDocument();

    const select = await screen.findByLabelText('Select league');

    // default -> second (fast)
    await userEvent.selectOptions(select, secondId);
    expect(await screen.findByText('Second League', {}, { timeout: 3000 })).toBeInTheDocument();

    // second -> default (this fetch will be the slow one)
    await userEvent.selectOptions(select, 'default');

    // default -> second again (fast) -- by the time this resolves, the slow
    // "default" response from the previous step has not landed yet.
    await userEvent.selectOptions(select, secondId);

    // The slow default response, once it finally resolves, must be a no-op.
    await new Promise((r) => setTimeout(r, 500));

    // Final state must reflect the LAST selection (second league), never the
    // stale default data landing on top of it.
    expect(select).toHaveValue(secondId);
    expect(screen.getByText('Second League')).toBeInTheDocument();
  }, 20000);
});
