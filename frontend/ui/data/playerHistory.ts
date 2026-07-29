import { useEffect, useState } from 'react';
import type {
  RawSeasonStats,
  RawSeasonStatsPlayer,
  RawWeeklyFinishes,
  RawWeeklyFinishesPlayer,
} from './types';

/**
 * Lazy fetch + join layer for `weekly_finishes.json` / `season_stats.json`
 * (thread 017/039). These are unprefixed, not per-league, and not part of
 * `loadDataset`'s eager `Promise.all` -- together they're ~11.6MB, and the
 * only consumer is the player detail sheet's sections 7/8. Fetching them on
 * every page load (Board, Draft, Opponents, ...) whether or not a player
 * sheet is ever opened would be real, unjustified weight. Fetched once, on
 * first use, and cached module-wide so paging through several players'
 * sheets in one session doesn't refetch either file.
 *
 * The join key is `player_id_gsis` on a board row against `player_id` here --
 * both sides speak nflverse gsis ids as of thread 052/ADR-048. Before that
 * landed, `player_id_gsis` was always null and PlayerDetail rendered an
 * explicit "not yet joinable" reason instead of attempting this fetch at all.
 */

export interface PlayerHistory {
  weeklyFinishes: RawWeeklyFinishes;
  seasonStats: RawSeasonStats;
}

let cached: Promise<PlayerHistory> | null = null;

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`data/${path}`, { cache: 'no-store' });
  const contentType = res.headers.get('content-type') ?? '';
  if (!res.ok || !contentType.includes('json')) {
    throw new Error(
      `Could not read data/${path} (HTTP ${res.status}${!res.ok ? '' : ', non-JSON response'}).`,
    );
  }
  return (await res.json()) as T;
}

export function loadPlayerHistory(): Promise<PlayerHistory> {
  if (!cached) {
    cached = Promise.all([
      fetchJson<RawWeeklyFinishes>('weekly_finishes.json'),
      fetchJson<RawSeasonStats>('season_stats.json'),
    ]).then(([weeklyFinishes, seasonStats]) => ({ weeklyFinishes, seasonStats }));
  }
  return cached;
}

/** Undefined means this gsis id has zero rows in the file -- a real, per-player
 *  absence of history (thread 052: 7 of 378 board players, plausibly rookies),
 *  a DIFFERENT claim from the board-wide "not yet joinable" state that applied
 *  before the join key existed. Never conflate the two reasons in the UI. */
export function weeklyFinishesFor(
  h: RawWeeklyFinishes,
  gsisId: string,
): RawWeeklyFinishesPlayer | undefined {
  return h.players.find((p) => p.player_id === gsisId);
}

export function seasonStatsFor(
  h: RawSeasonStats,
  gsisId: string,
): RawSeasonStatsPlayer | undefined {
  return h.players.find((p) => p.player_id === gsisId);
}

/** Most recent N season keys a player's weekly_finishes record actually has,
 *  newest first. Seasons with zero weeks logged don't happen in the export,
 *  but this doesn't assume it either -- it reads what's there. */
export function recentSeasonKeys(player: RawWeeklyFinishesPlayer, n: number): string[] {
  return Object.keys(player.seasons)
    .sort((a, b) => Number(b) - Number(a))
    .slice(0, n);
}

/**
 * Four distinct states, deliberately not collapsed into fewer (Principle #2):
 *  - `loading`: fetch in flight. Different from "not computed" -- it resolves.
 *  - `no-key`: this board row itself carries no `player_id_gsis`. Shouldn't
 *    happen post-thread-052 (378/378 measured), but a row without the key is
 *    a different failure than a row whose key doesn't resolve, so it gets its
 *    own state rather than silently falling through to "no rows found".
 *  - `error`: the fetch itself failed (network, bad JSON, ...).
 *  - `ready`: fetch succeeded. `weeklyFinishes`/`seasonStats` are `undefined`
 *    when this specific gsis id has zero rows in that file -- thread 052
 *    measured 7 of 378 board players this way (plausibly rookies with no
 *    prior NFL snaps), a real per-player absence, not a join failure.
 */
export type PlayerHistoryState =
  | { status: 'loading' }
  | { status: 'no-key' }
  | { status: 'error'; message: string }
  | {
      status: 'ready';
      weeklyFinishes: RawWeeklyFinishesPlayer | undefined;
      seasonStats: RawSeasonStatsPlayer | undefined;
    };

/**
 * Set only by vite.standalone.config.ts's `define`, to `true` in that one
 * build and left `undefined` everywhere else (npm run dev, npm test, npm run
 * build all see it as falsy) -- so STANDALONE below is provably `false` for
 * the live app, unconditionally, not just falsy-by-default.
 */
declare const __STANDALONE__: boolean | undefined;
const STANDALONE = typeof __STANDALONE__ !== 'undefined' && __STANDALONE__ === true;

/** frontend/dist-standalone/board.html never embeds weekly_finishes.json /
 *  season_stats.json (8.9MB + 2.3MB -- see scripts/build-standalone-data.mjs's
 *  doc comment), so there is nothing `loadPlayerHistory()` could fetch even if
 *  it tried. Short-circuiting here means it never tries: no request is issued
 *  and none fails, which is a different, stronger claim than "the fetch
 *  failed gracefully" -- the standalone build has zero fetch() calls at
 *  runtime, full stop. Reuses the real `error` state PlayerDetail.tsx already
 *  renders (sections 7/8), so this is an existing UI branch, not a new one. */
const STANDALONE_REASON =
  'not included in this static snapshot (kept out to keep the file small -- ' +
  'the live app at npm run dev has full season history)';

export function usePlayerHistory(gsisId: string | null): PlayerHistoryState {
  const [state, setState] = useState<PlayerHistoryState>(
    STANDALONE
      ? { status: 'error', message: STANDALONE_REASON }
      : gsisId === null
        ? { status: 'no-key' }
        : { status: 'loading' },
  );

  useEffect(() => {
    if (STANDALONE) return;
    if (gsisId === null) {
      setState({ status: 'no-key' });
      return;
    }
    let cancelled = false;
    setState({ status: 'loading' });
    loadPlayerHistory()
      .then((h) => {
        if (cancelled) return;
        setState({
          status: 'ready',
          weeklyFinishes: weeklyFinishesFor(h.weeklyFinishes, gsisId),
          seasonStats: seasonStatsFor(h.seasonStats, gsisId),
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState({ status: 'error', message: err instanceof Error ? err.message : String(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [gsisId]);

  return state;
}
