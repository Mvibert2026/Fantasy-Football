/**
 * Copies data/export/*.json into public/data/ so the app can load them as static
 * files. No REST API: the browser fetches these directly.
 *
 * This script is the ONLY place export data is touched, and it is deliberately dumb.
 * It copies, it validates, and it records what it copied. It does not compute,
 * reshape, merge, or fill anything.
 *
 * It used to do one more thing: rewrite the bare `Infinity` token that league.json
 * shipped in `scoring.defense.points_allowed`, which made the file invalid JSON and
 * unloadable in a browser. Contract 1.4.0 fixed that at source -- the exporters now
 * write with `allow_nan=False` and a test parses every artifact with `parse_constant`
 * set to raise -- so the rewrite is gone. Patching a bug downstream is worth doing
 * exactly as long as the bug exists.
 *
 * What replaced it is a validation that fails loudly. If an invalid token ever comes
 * back, this throws at `npm run dev` with the file, the line and the token named,
 * rather than silently nulling a value and letting a wrong number reach a draft table.
 */

import { readdirSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = join(root, 'data', 'export');
const outDir = join(root, 'public', 'data');

/** Bare non-JSON numeric tokens, only where they sit in a JSON value position. */
const BAD_TOKEN = /(^|[\s:,[])(-?Infinity|NaN)(?=[\s,\]}]|$)/;

/** Locates an invalid token so the error can point at it precisely. */
function findBadToken(text) {
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const m = BAD_TOKEN.exec(lines[i]);
    if (m) return { line: i + 1, token: m[2] };
  }
  return null;
}

/**
 * Copies the exports and returns the manifest it wrote.
 *
 * Exported so the dev server's Refresh control can re-run exactly this, rather than
 * a second implementation that could drift from it. `quiet` suppresses the per-file
 * logging when it runs on request rather than at startup.
 */
export function syncExports({ quiet = false } = {}) {
  const log = quiet ? () => {} : (...args) => console.log(...args);

  if (!existsSync(srcDir)) {
    throw new Error(`[sync-exports] missing ${srcDir}`);
  }
  mkdirSync(outDir, { recursive: true });

  const files = readdirSync(srcDir).filter((f) => f.endsWith('.json'));
  const artifacts = {};

  for (const file of files) {
    const raw = readFileSync(join(srcDir, file), 'utf8');

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      const bad = findBadToken(raw);
      if (bad) {
        throw new Error(
          `[sync-exports] ${file} is not valid JSON: bare \`${bad.token}\` token at line ${bad.line}.\n` +
            `  JSON has no Infinity or NaN literal, so no browser can load this file.\n` +
            `  This was fixed upstream at contract 1.4.0 by writing with allow_nan=False; a\n` +
            `  reappearance means that regressed. Fix it in the exporter, not here.`,
        );
      }
      throw new Error(`[sync-exports] ${file} is not valid JSON: ${err.message}`);
    }

    writeFileSync(join(outDir, file), raw);

    const name = basename(file, '.json');
    const contractVersion = parsed?.contract_version ?? null;
    const generatedUtc = parsed?.generated_utc ?? null;

    artifacts[name] = {
      file: `data/${file}`,
      contract_version: contractVersion,
      generated_utc: generatedUtc,
      // The run id is what the assistant cites alongside every value it returns.
      // It identifies the export run a number came from, nothing more.
      run_id:
        contractVersion && generatedUtc
          ? `${name}@${contractVersion}+${generatedUtc}`
          : `${name}@unversioned`,
    };
    log(`[sync-exports] ${file} -> public/data/${file}`);
  }

  const manifest = { synced_utc: new Date().toISOString(), artifacts };
  writeFileSync(join(outDir, '_manifest.json'), JSON.stringify(manifest, null, 2));

  log(
    `[sync-exports] ${files.length} artifact(s) copied verbatim. ` +
      `Manifest: public/data/_manifest.json`,
  );

  return manifest;
}

/** Reads the manifest already in public/data/, or null on a cold start. */
export function readCurrentManifest() {
  const path = join(outDir, '_manifest.json');
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    return null;
  }
}

// Only run when invoked directly (npm predev / pretest), not when imported.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    syncExports();
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}
