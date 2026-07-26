import { DEFAULT_LEAGUE_ID, pathPrefixFor } from './league-registry';
import type {
  LeaguesManifest,
  Manifest,
  RawAvailability,
  RawBoard,
  RawFeed,
  RawGlossary,
  RawLeague,
  RawNulls,
  RawStrategies,
} from './types';

/**
 * Loads the export artifacts as static files from public/data/.
 *
 * There is no API. `scripts/sync-exports.mjs` copies data/export/*.json into public/
 * before the dev server starts, and the browser fetches them directly. Everything the
 * board views compute is computed here, in the client, from these files -- which is
 * what makes the app work at a draft table with no network.
 *
 * Multi-league loading: the default league stays at the unprefixed path exactly as
 * before. A non-default league is fetched from public/data/leagues/<id>/ instead,
 * and every artifact loaded that way must declare a matching `league_id` -- if any
 * artifact doesn't (missing, or belonging to a different league), loading refuses
 * outright rather than rendering. Wrong-league data that looks authoritative is
 * worse than an error.
 */

const BASE = 'data';

async function fetchJson<T>(name: string, pathPrefix: string): Promise<T> {
  const res = await fetch(`${BASE}/${pathPrefix}${name}.json`, { cache: 'no-store' });
  if (!res.ok) {
    throw new LoadError(
      `Could not read ${pathPrefix}${name}.json (HTTP ${res.status}). ` +
        `Run \`npm run dev\`, which regenerates public/data/ from data/export/ first.`,
    );
  }
  return (await res.json()) as T;
}

export class LoadError extends Error {}

export interface Dataset {
  manifest: Manifest;
  board: RawBoard;
  league: RawLeague;
  glossary: RawGlossary;
  nulls: RawNulls;
  strategies: RawStrategies;
  availability: RawAvailability;
  /**
   * Zero items today. There is no ingested news corpus in the repo, so the artifact
   * is absent and this is a synthesised empty feed rather than a fetch failure.
   */
  feed: RawFeed;
}

/**
 * The news feed has no producer yet. Rather than fail the whole load, resolve to an
 * explicitly empty feed -- the news lane then reports "no news data ingested yet",
 * which is the truth, instead of an error.
 */
async function fetchFeedOrEmpty(pathPrefix: string): Promise<RawFeed> {
  try {
    return await fetchJson<RawFeed>('feed', pathPrefix);
  } catch {
    return { contract_version: 'absent', generated_utc: 'never', items: [] };
  }
}

/** `{ artifactName: league_id }` for everything that must match, skipping the feed
 *  (which is legitimately absent for every league today, default or not). */
function leagueIdsOf(d: Omit<Dataset, 'manifest' | 'feed'>): Record<string, string | null | undefined> {
  return {
    board: d.board.league_id,
    league: d.league.league_id,
    glossary: d.glossary.league_id,
    nulls: d.nulls.league_id,
    strategies: d.strategies.league_id,
    availability: d.availability.league_id,
  };
}

function assertLeagueMatches(leagueId: string, data: Omit<Dataset, 'manifest' | 'feed'>): void {
  const mismatches = Object.entries(leagueIdsOf(data))
    .filter(([, got]) => got !== leagueId)
    .map(([artifact, got]) => `${artifact}.json declares league_id ${JSON.stringify(got ?? null)}`);

  if (mismatches.length > 0) {
    throw new LoadError(
      `Refusing to render league "${leagueId}": ${mismatches.join('; ')}, expected "${leagueId}" on every ` +
        `artifact. Wrong-league data that looks authoritative is worse than an error -- this is not rendered.`,
    );
  }
}

export async function loadDataset(leagueId: string = DEFAULT_LEAGUE_ID): Promise<Dataset> {
  const pathPrefix = pathPrefixFor(leagueId);

  // For a non-default league, confirm it's actually in the registry before
  // fetching six files that would otherwise fail one at a time with a less useful
  // "file not found" error apiece.
  let registryManifest: Manifest | null = null;
  if (leagueId !== DEFAULT_LEAGUE_ID) {
    const leagues = await fetchJson<LeaguesManifest>('_leagues', '');
    const entry = leagues.leagues.find((l) => l.id === leagueId);
    if (!entry) {
      throw new LoadError(
        `League "${leagueId}" is not in public/data/_leagues.json. It may not have been synced yet.`,
      );
    }
    registryManifest = { synced_utc: new Date().toISOString(), artifacts: entry.artifacts };
  }

  const [board, league, glossary, nulls, strategies, availability, feed] = await Promise.all([
    fetchJson<RawBoard>('board', pathPrefix),
    fetchJson<RawLeague>('league', pathPrefix),
    fetchJson<RawGlossary>('glossary', pathPrefix),
    fetchJson<RawNulls>('nulls', pathPrefix),
    fetchJson<RawStrategies>('strategies', pathPrefix),
    fetchJson<RawAvailability>('availability', pathPrefix),
    fetchFeedOrEmpty(pathPrefix),
  ]);

  const data = { board, league, glossary, nulls, strategies, availability };

  let manifest: Manifest;
  if (leagueId === DEFAULT_LEAGUE_ID) {
    manifest = await fetchJson<Manifest>('_manifest', '');
    // No league_id guard for the default league: the backend has not added the
    // field there, only to the convention for additional leagues, so absence is
    // expected rather than a mismatch.
  } else {
    manifest = registryManifest as Manifest;
    assertLeagueMatches(leagueId, data);
  }

  return { manifest, ...data, feed };
}

/** Looks up the run id the assistant cites alongside any value from this artifact. */
export function runIdOf(manifest: Manifest, artifact: string): string {
  return manifest.artifacts[artifact]?.run_id ?? `${artifact}@unknown`;
}
