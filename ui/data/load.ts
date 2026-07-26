import type {
  Manifest,
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
 */

const BASE = 'data';

async function fetchJson<T>(name: string): Promise<T> {
  const res = await fetch(`${BASE}/${name}.json`, { cache: 'no-store' });
  if (!res.ok) {
    throw new LoadError(
      `Could not read ${name}.json (HTTP ${res.status}). ` +
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
async function fetchFeedOrEmpty(): Promise<RawFeed> {
  try {
    return await fetchJson<RawFeed>('feed');
  } catch {
    return { contract_version: 'absent', generated_utc: 'never', items: [] };
  }
}

export async function loadDataset(): Promise<Dataset> {
  const [manifest, board, league, glossary, nulls, strategies, feed] = await Promise.all([
    fetchJson<Manifest>('_manifest'),
    fetchJson<RawBoard>('board'),
    fetchJson<RawLeague>('league'),
    fetchJson<RawGlossary>('glossary'),
    fetchJson<RawNulls>('nulls'),
    fetchJson<RawStrategies>('strategies'),
    fetchFeedOrEmpty(),
  ]);

  return { manifest, board, league, glossary, nulls, strategies, feed };
}

/** Looks up the run id the assistant cites alongside any value from this artifact. */
export function runIdOf(manifest: Manifest, artifact: string): string {
  return manifest.artifacts[artifact]?.run_id ?? `${artifact}@unknown`;
}
