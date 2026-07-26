import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Dataset } from '../data/load';

/**
 * Loads the real exports from public/data/ for tests.
 *
 * Deliberately the real files, not fixtures. The properties under test -- that no view
 * invents a number, that no claim is untagged -- are properties of this data, and a
 * hand-written fixture would let a real export drift out from under them.
 */

const DATA_DIR = join(process.cwd(), 'public', 'data');

function read<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, `${name}.json`), 'utf8')) as T;
}

export function loadDatasetFromDisk(): Dataset {
  return {
    manifest: read('_manifest'),
    board: read('board'),
    league: read('league'),
    glossary: read('glossary'),
    nulls: read('nulls'),
    strategies: read('strategies'),
    feed: { contract_version: 'absent', generated_utc: 'never', items: [] },
  } as Dataset;
}
