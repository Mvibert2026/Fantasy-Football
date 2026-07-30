import type { LeagueTrack, LeaguesManifest } from './types';

/**
 * Discovers which leagues are available to load, from public/data/_leagues.json.
 *
 * The default league (this app's real one) is always selectable and always lives
 * at the unprefixed path -- that never changes, per the backend's convention.
 * Anything beyond it comes entirely from what sync-exports.mjs actually found
 * under data/export/<league_id>/ on the last sync; there is no hardcoded second
 * league anywhere in this file. Today that list is empty -- the backend has not
 * shipped a second league yet -- so the switcher has exactly one option until it
 * does, which is the honest state to show rather than a placeholder.
 */

export const DEFAULT_LEAGUE_ID = 'default';

export interface SelectableLeague {
  id: string;
  /** league.json's own league_name where the export carries one (contract
   *  1.7.0+, ADR-041); the raw id otherwise -- never an invented display name. */
  label: string;
  /** design/TWO-TRACK-EXPRESSION.md: which track this league is on, read from
   *  _leagues.json at sync time so the switcher can show it before the league
   *  is loaded. Absent on a manifest written before this field existed. */
  track?: LeagueTrack;
}

export async function fetchSelectableLeagues(): Promise<SelectableLeague[]> {
  const base: SelectableLeague[] = [{ id: DEFAULT_LEAGUE_ID, label: 'Default league' }];

  let res: Response;
  try {
    res = await fetch('data/_leagues.json', { cache: 'no-store' });
  } catch {
    return base;
  }
  if (!res.ok) return base;

  const manifest = (await res.json().catch(() => null)) as LeaguesManifest | null;
  if (!manifest) return base;

  // The primary league's own switcher metadata (design/TWO-TRACK-EXPRESSION.md)
  // travels alongside the additional-league list rather than replacing `base`
  // outright -- an older manifest without `primary` keeps exactly the static
  // label this always showed, never a guessed track.
  const defaultEntry: SelectableLeague = manifest.primary
    ? { id: DEFAULT_LEAGUE_ID, label: manifest.primary.label, track: manifest.primary.track }
    : base[0]!;

  if (!manifest.leagues?.length) return [defaultEntry];

  return [
    defaultEntry,
    ...manifest.leagues.map((l) => ({ id: l.id, label: l.label ?? l.id, track: l.track })),
  ];
}

/** Path prefix under public/data/ for a given league's artifacts. */
export function pathPrefixFor(leagueId: string): string {
  return leagueId === DEFAULT_LEAGUE_ID ? '' : `leagues/${leagueId}/`;
}
