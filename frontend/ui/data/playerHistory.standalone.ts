import type { PlayerHistoryState } from './playerHistory';

/**
 * Standalone-build replacement for ui/data/playerHistory.ts, aliased in
 * vite.standalone.config.ts (resolve.alias) so the live dev/CI app is
 * completely untouched by this file.
 *
 * weekly_finishes.json (8.9MB) and season_stats.json (2.3MB) are deliberately
 * not embedded in the standalone bundle -- see
 * scripts/build-standalone-data.mjs's doc comment. This always reports the
 * `error` state, which is a real, existing branch in PlayerDetail.tsx (sections
 * 7/8), not a new one: it renders "Could not load weekly_finishes.json: <msg>"
 * verbatim, so the message says plainly why, rather than the app pretending
 * the fetch is in flight (the real `loading` state) or hanging silently.
 */
const REASON =
  'not included in this static snapshot (kept out to keep the file small -- ' +
  'the live app at npm run dev has full season history)';

export function usePlayerHistory(_gsisId: string | null): PlayerHistoryState {
  return { status: 'error', message: REASON };
}

/** Only used by WeeklyFinishesHeatmap, which is unreachable behind the
 *  always-error state above -- kept for type/import compatibility with
 *  PlayerDetail.tsx, which imports both names from one module specifier. */
export function recentSeasonKeys(): string[] {
  return [];
}
