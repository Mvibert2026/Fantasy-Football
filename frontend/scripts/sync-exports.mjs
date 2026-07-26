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

/** Copies one directory of *.json exports into one output directory, validating
 *  each file the same way regardless of whether it's the default league or a
 *  per-league subdirectory. Returns the artifacts map for whichever manifest the
 *  caller is building. */
function copyJsonDir(fromDir, toDir, pathPrefix, log) {
  mkdirSync(toDir, { recursive: true });
  const files = readdirSync(fromDir).filter((f) => f.endsWith('.json'));
  const artifacts = {};

  for (const file of files) {
    const raw = readFileSync(join(fromDir, file), 'utf8');

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      const bad = findBadToken(raw);
      if (bad) {
        throw new Error(
          `[sync-exports] ${pathPrefix}${file} is not valid JSON: bare \`${bad.token}\` token at line ${bad.line}.\n` +
            `  JSON has no Infinity or NaN literal, so no browser can load this file.\n` +
            `  This was fixed upstream at contract 1.4.0 by writing with allow_nan=False; a\n` +
            `  reappearance means that regressed. Fix it in the exporter, not here.`,
        );
      }
      throw new Error(`[sync-exports] ${pathPrefix}${file} is not valid JSON: ${err.message}`);
    }

    writeFileSync(join(toDir, file), raw);

    const name = basename(file, '.json');
    const contractVersion = parsed?.contract_version ?? null;
    const generatedUtc = parsed?.generated_utc ?? null;
    const leagueId = parsed?.league_id ?? null;

    artifacts[name] = {
      file: `data/${pathPrefix}${file}`,
      contract_version: contractVersion,
      generated_utc: generatedUtc,
      league_id: leagueId,
      // The run id is what the assistant cites alongside every value it returns.
      // It identifies the export run a number came from, nothing more.
      run_id:
        contractVersion && generatedUtc
          ? `${name}@${contractVersion}+${generatedUtc}`
          : `${name}@unversioned`,
    };
    log(`[sync-exports] ${pathPrefix}${file} -> public/data/${pathPrefix}${file}`);
  }

  return artifacts;
}

/**
 * Copies the exports and returns the manifest it wrote.
 *
 * Exported so the dev server's Refresh control can re-run exactly this, rather than
 * a second implementation that could drift from it. `quiet` suppresses the per-file
 * logging when it runs on request rather than at startup.
 *
 * The default league's files stay exactly where they've always been --
 * data/export/*.json -> public/data/*.json -- per the backend's convention: the
 * current league keeps the unprefixed path, and additional leagues each get their
 * own data/export/<league_id>/ subdirectory with the same filenames, copied to
 * public/data/leagues/<league_id>/. Nothing here computes or invents a league_id;
 * it's read from each artifact's own `league_id` field, or recorded as absent if
 * the artifact doesn't carry one yet (true for every default-league artifact
 * today -- the backend hasn't added the field there, only to the convention for
 * additional leagues).
 */
export function syncExports({ quiet = false } = {}) {
  const log = quiet ? () => {} : (...args) => console.log(...args);

  if (!existsSync(srcDir)) {
    throw new Error(`[sync-exports] missing ${srcDir}`);
  }

  const artifacts = copyJsonDir(srcDir, outDir, '', log);
  const manifest = { synced_utc: new Date().toISOString(), artifacts };
  writeFileSync(join(outDir, '_manifest.json'), JSON.stringify(manifest, null, 2));

  const fileCount = Object.keys(artifacts).length;
  log(
    `[sync-exports] ${fileCount} artifact(s) copied verbatim. ` +
      `Manifest: public/data/_manifest.json`,
  );

  // Additional leagues: any subdirectory of data/export/ other than files.
  const leagueDirs = readdirSync(srcDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const leagues = leagueDirs.map((leagueId) => {
    const from = join(srcDir, leagueId);
    const to = join(outDir, 'leagues', leagueId);
    const leagueArtifacts = copyJsonDir(from, to, `leagues/${leagueId}/`, log);

    // league_name (added contract 1.7.0, ADR-041) makes a much better switcher
    // label than the raw id -- read it straight from the copy just written rather
    // than re-parsing the source, so there's exactly one place that trusts the
    // file's content. Falls back to the id itself on an older contract that
    // doesn't carry the field yet, same as the default league's label.
    let label = leagueId;
    try {
      const leagueJson = JSON.parse(readFileSync(join(to, 'league.json'), 'utf8'));
      if (typeof leagueJson.league_name === 'string' && leagueJson.league_name.trim()) {
        label = leagueJson.league_name;
      }
    } catch {
      // No league.json, or it doesn't parse -- copyJsonDir already threw loudly
      // for a genuine parse error, so reaching here just means "no name available".
    }

    return { id: leagueId, label, artifacts: leagueArtifacts };
  });

  writeFileSync(join(outDir, '_leagues.json'), JSON.stringify({ leagues }, null, 2));
  if (leagueDirs.length > 0) {
    log(`[sync-exports] ${leagueDirs.length} additional league(s) copied. Manifest: public/data/_leagues.json`);
  }

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
