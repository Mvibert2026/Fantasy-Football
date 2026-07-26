/** Types for the sync script, which the Refresh endpoint imports at runtime. */
export interface SyncedArtifact {
  file: string;
  contract_version: string | null;
  generated_utc: string | null;
  run_id: string;
}
export interface SyncedManifest {
  synced_utc: string;
  artifacts: Record<string, SyncedArtifact>;
}
export function syncExports(opts?: { quiet?: boolean }): SyncedManifest;
export function readCurrentManifest(): SyncedManifest | null;
