import { afterEach, describe, expect, it, vi } from 'vitest';
import { loadDataset, LoadError } from '../data/load';
import { DEFAULT_LEAGUE_ID, fetchSelectableLeagues } from '../data/league-registry';
import { loadDatasetFromDisk } from './helpers';

/**
 * No second league exists in this repo yet -- the backend has not shipped one --
 * so this is the only place multi-league loading and the wrong-league guard get
 * exercised at all. Everything here is synthetic fixtures over a mocked fetch,
 * proving the mechanism works before there is real data to point it at.
 */

const base = loadDatasetFromDisk();

function jsonResponse(body: unknown, ok = true) {
  return new Response(JSON.stringify(body), {
    status: ok ? 200 : 404,
    headers: { 'content-type': 'application/json' },
  });
}

/** A second league's artifact set, every file honestly carrying league_id. */
function secondLeagueFiles(leagueId: string): Record<string, { league_id?: string | null }> {
  return {
    board: { ...base.board, league_id: leagueId },
    league: { ...base.league, league_id: leagueId },
    glossary: { ...base.glossary, league_id: leagueId },
    nulls: { ...base.nulls, league_id: leagueId },
    strategies: { ...base.strategies, league_id: leagueId },
    availability: { ...base.availability, league_id: leagueId },
  };
}

function installFetch(files: Record<string, unknown>, leaguesManifest: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('data/_leagues.json')) return jsonResponse(leaguesManifest);
      if (url.includes('data/_manifest.json')) return jsonResponse(base.manifest);
      if (url.includes('feed.json')) return jsonResponse(null, false);
      const key = Object.keys(files).find((f) => url.endsWith(`${f}.json`));
      if (key) return jsonResponse(files[key]);
      return jsonResponse(null, false);
    }),
  );
}

describe('league registry', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('always offers the default league even when _leagues.json is empty', async () => {
    installFetch({}, { leagues: [] });
    const leagues = await fetchSelectableLeagues();
    expect(leagues).toEqual([{ id: DEFAULT_LEAGUE_ID, label: 'Default league' }]);
  });

  it('lists an additional league once sync-exports.mjs has written one', async () => {
    installFetch({}, { leagues: [{ id: 'dynasty', artifacts: {} }] });
    const leagues = await fetchSelectableLeagues();
    expect(leagues).toEqual([
      { id: DEFAULT_LEAGUE_ID, label: 'Default league' },
      { id: 'dynasty', label: 'dynasty' },
    ]);
  });
});

describe('loadDataset with a non-default league', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('loads successfully when every artifact carries the matching league_id', async () => {
    const files = secondLeagueFiles('dynasty');
    const artifacts = Object.fromEntries(
      Object.keys(files).map((name) => [
        name,
        { file: `leagues/dynasty/${name}.json`, contract_version: '1.6.0', generated_utc: 'x', league_id: 'dynasty', run_id: `${name}@x` },
      ]),
    );
    installFetch(files, { leagues: [{ id: 'dynasty', artifacts }] });

    const data = await loadDataset('dynasty');
    expect(data.board.league_id).toBe('dynasty');
    expect(data.league.league_id).toBe('dynasty');
  });

  it('refuses to render when one artifact belongs to a different league', async () => {
    const files = secondLeagueFiles('dynasty');
    // A wrong-league leak: strategies.json actually belongs to some other league.
    files.strategies = { ...files.strategies, league_id: 'someone-elses-league' };
    const artifacts = Object.fromEntries(
      Object.keys(files).map((name) => [
        name,
        { file: `leagues/dynasty/${name}.json`, contract_version: '1.6.0', generated_utc: 'x', league_id: 'dynasty', run_id: `${name}@x` },
      ]),
    );
    installFetch(files, { leagues: [{ id: 'dynasty', artifacts }] });

    await expect(loadDataset('dynasty')).rejects.toThrow(LoadError);
    await expect(loadDataset('dynasty')).rejects.toThrow(/someone-elses-league/);
  });

  it('refuses to render when an artifact carries no league_id at all', async () => {
    const files = secondLeagueFiles('dynasty');
    // A default-league file accidentally served under the dynasty path.
    files.league = base.league;
    const artifacts = Object.fromEntries(
      Object.keys(files).map((name) => [
        name,
        { file: `leagues/dynasty/${name}.json`, contract_version: '1.6.0', generated_utc: 'x', league_id: 'dynasty', run_id: `${name}@x` },
      ]),
    );
    installFetch(files, { leagues: [{ id: 'dynasty', artifacts }] });

    await expect(loadDataset('dynasty')).rejects.toThrow(LoadError);
  });

  it('refuses to render a league that is not in _leagues.json at all', async () => {
    installFetch({}, { leagues: [] });
    await expect(loadDataset('nonexistent')).rejects.toThrow(/not in public\/data\/_leagues\.json/);
  });
});

describe('loadDataset for the default league', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('does not require league_id on any artifact', async () => {
    // The real, unmodified default-league fixtures: none of them carry league_id.
    const files = {
      board: base.board,
      league: base.league,
      glossary: base.glossary,
      nulls: base.nulls,
      strategies: base.strategies,
      availability: base.availability,
    };
    installFetch(files, { leagues: [] });
    const data = await loadDataset(DEFAULT_LEAGUE_ID);
    expect(data.board.league_id ?? null).toBeNull();
  });
});
