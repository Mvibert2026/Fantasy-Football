import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createElement, type ReactElement, type ReactNode } from 'react';
import type { Dataset } from '../data/load';
import { TraceModeContext } from '../data/traceMode';

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
  const rostersPath = join(DATA_DIR, 'rosters.json');
  const playerDescriptionsPath = join(DATA_DIR, 'player_descriptions.json');
  return {
    manifest: read('_manifest'),
    board: read('board'),
    league: read('league'),
    glossary: read('glossary'),
    nulls: read('nulls'),
    strategies: read('strategies'),
    availability: read('availability'),
    opponents: read('opponents'),
    // Optional, contract 1.8.0+ (see Dataset.rosters) -- not every synced export
    // set will have it.
    rosters: existsSync(rostersPath) ? read('rosters') : null,
    feed: { contract_version: 'absent', generated_utc: 'never', items: [] },
    // Primary league only (see Dataset.playerDescriptions).
    playerDescriptions: existsSync(playerDescriptionsPath) ? read('player_descriptions') : null,
  } as Dataset;
}

/**
 * FR-114 (the "show data sources" switch, `ui/data/traceMode.tsx`) -- wraps a
 * tree with the switch forced on, so a test can assert the ON state without a
 * real Settings-panel/`Alt+T` interaction. Tests that render a component
 * without this wrapper get the switch's real default (off), which is the
 * behaviour most tests should exercise; use this only for the tests that
 * specifically cover the ON state.
 */
export function withTraceOn(children: ReactNode): ReactElement {
  return createElement(
    TraceModeContext.Provider,
    { value: { on: true, setOn: () => {}, toggle: () => {} } },
    children,
  );
}
