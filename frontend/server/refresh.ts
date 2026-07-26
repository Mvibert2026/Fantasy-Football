import type { Plugin, ViteDevServer } from 'vite';
import type { ServerResponse } from 'node:http';

/**
 * The Refresh control's endpoint.
 *
 * Two sessions are running against this repo -- one on the backend regenerating
 * exports, one here on the front end. Nothing tells this app when the other side has
 * shipped a new contract, and noticing a stale drift banner is a poor substitute for
 * asking. This endpoint is the bridge: it re-reads data/export/, re-copies into
 * public/data/, and reports precisely what moved.
 *
 * It has to live server-side because the browser cannot read data/export/ -- only
 * public/. It is dev-server middleware for the same reason the reasoning proxy is:
 * `npm run dev` stays the only command.
 */

export const REFRESH_ENDPOINT = '/__refresh';

export interface ArtifactChange {
  artifact: string;
  before: { contract_version: string | null; generated_utc: string | null } | null;
  after: { contract_version: string | null; generated_utc: string | null };
  /** 'added' | 'version' | 'regenerated' | 'unchanged' */
  change: 'added' | 'version' | 'regenerated' | 'unchanged';
}

export interface RefreshReport {
  updated: boolean;
  message: string;
  checkedAt: string;
  changes: ArtifactChange[];
  /** Artifacts whose contract version differs from what the UI expects. */
  behindExpected: Array<{ artifact: string; version: string | null }>;
  expected: string;
}

function json(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.end(JSON.stringify(body));
}

/**
 * @param expectedContract the version the UI is written against. Passed in rather than
 * imported so the server does not depend on a client module.
 */
export function refreshEndpoint(expectedContract: string): Plugin {
  return {
    name: 'prep-refresh',
    configureServer(server: ViteDevServer) {
      server.middlewares.use(REFRESH_ENDPOINT, async (req, res) => {
        if (req.method !== 'POST') {
          json(res, 405, { updated: false, message: 'method_not_allowed' });
          return;
        }

        try {
          const { syncExports, readCurrentManifest } = (await import(
            '../scripts/sync-exports.mjs'
          )) as typeof import('../scripts/sync-exports.js');

          // Snapshot before re-copying, so the comparison is against what the app is
          // actually holding rather than against the source twice.
          const before = readCurrentManifest();
          const after = syncExports({ quiet: true });

          const names = [
            ...new Set([
              ...Object.keys(before?.artifacts ?? {}),
              ...Object.keys(after.artifacts),
            ]),
          ].sort();

          const changes: ArtifactChange[] = names.map((name) => {
            const b = before?.artifacts?.[name];
            const a = after.artifacts[name];
            const beforeState = b
              ? { contract_version: b.contract_version, generated_utc: b.generated_utc }
              : null;
            const afterState = {
              contract_version: a?.contract_version ?? null,
              generated_utc: a?.generated_utc ?? null,
            };

            let change: ArtifactChange['change'] = 'unchanged';
            if (!beforeState) change = 'added';
            else if (beforeState.contract_version !== afterState.contract_version)
              change = 'version';
            else if (beforeState.generated_utc !== afterState.generated_utc)
              change = 'regenerated';

            return { artifact: name, before: beforeState, after: afterState, change };
          });

          const moved = changes.filter((c) => c.change !== 'unchanged');

          const behindExpected = changes
            .filter((c) => c.after.contract_version !== expectedContract)
            .map((c) => ({ artifact: c.artifact, version: c.after.contract_version }));

          const report: RefreshReport = {
            updated: moved.length > 0,
            // The explicit no-op answer. A silent nothing-happened is indistinguishable
            // from a broken button.
            message: moved.length
              ? `${moved.length} artifact(s) changed.`
              : 'No update available. data/export/ has not been re-copied since the last refresh.',
            checkedAt: new Date().toISOString(),
            changes,
            behindExpected,
            expected: expectedContract,
          };

          json(res, 200, report);
        } catch (err) {
          json(res, 500, {
            updated: false,
            message:
              err instanceof Error ? err.message : 'Refresh failed for an unknown reason.',
            checkedAt: new Date().toISOString(),
            changes: [],
            behindExpected: [],
            expected: expectedContract,
          });
        }
      });
    },
  };
}
