import type { Plugin } from 'vite';

/**
 * Task 1 (data freshness on load): before this plugin, `public/data/*.json` was
 * only ever re-copied from `data/export/` in two ways -- restarting `npm run dev`
 * (predev script) or clicking the "Refresh data" button (server/refresh.ts's
 * `/__refresh` endpoint). A plain page reload fetched board.json with
 * `cache: 'no-store'` (ui/data/load.ts), so it always hit the network -- but the
 * network answer could still be an hours-old copy if the backend had regenerated
 * `data/export/` since the dev server last synced. Reload looked live and wasn't
 * necessarily current. This plugin closes that gap: every request under `/data/`
 * re-syncs first, so a reload always serves whatever is actually on disk in
 * `data/export/` right now, with no manual action.
 *
 * Coalesced, not throttled: concurrent requests (the app fires ~10 parallel
 * fetches on one load) share a single in-flight sync rather than each starting
 * their own, so a burst costs one directory copy, not ten. Once that sync
 * settles the next request starts a fresh one -- there is no time window where
 * a real change is skipped.
 *
 * Fails OPEN, deliberately asymmetric with the Refresh button: sync-exports.mjs
 * throws loudly on invalid JSON by design (see its own docstring), which is the
 * right behaviour for an explicit, user-initiated refresh the button reports on.
 * Here, on every ordinary page load, throwing would take the whole app down on
 * a transient mid-write read of a file the backend is still writing. Logging and
 * falling through to serve the last-good copy keeps normal loads working; the
 * Refresh button remains the loud, explicit path when someone wants to see (and
 * act on) that failure directly.
 */
export function autoSyncExports(): Plugin {
  let inFlight: Promise<void> | null = null;

  async function syncOnce(): Promise<void> {
    const { syncExports } = (await import('../scripts/sync-exports.mjs')) as typeof import(
      '../scripts/sync-exports.js'
    );
    syncExports({ quiet: true });
  }

  return {
    name: 'prep-auto-sync-exports',
    configureServer(server) {
      server.middlewares.use('/data', (_req, _res, next) => {
        if (!inFlight) {
          inFlight = syncOnce()
            .catch((err) => {
              console.error(
                '[auto-sync] failed, serving last-synced public/data/ unchanged:',
                err instanceof Error ? err.message : err,
              );
            })
            .finally(() => {
              inFlight = null;
            });
        }
        inFlight.then(() => next());
      });
    },
  };
}
