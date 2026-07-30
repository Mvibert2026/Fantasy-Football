/**
 * Contract constants with no dependencies.
 *
 * Kept in its own module because vite.config.ts imports the expected version to wire
 * the Refresh endpoint, and importing it from a module that also pulls in the data
 * layer would drag browser code (fetch, the loader) into the Node config graph. A bare
 * constant file keeps that boundary clean.
 */

/**
 * The export contract version this app is written against.
 *
 * Thresholds, field names and value semantics are all read from the exports rather
 * than hardcoded, so a mismatch here is informational, not fatal: the app renders
 * whatever the export says and flags the divergence rather than adjusting for it.
 */
export const EXPECTED_CONTRACT = '1.16.0';
