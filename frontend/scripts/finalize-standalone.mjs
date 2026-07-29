/**
 * vite-plugin-singlefile writes dist-standalone/<entry-html-basename> (i.e.
 * index.standalone.html, matching build.rollupOptions.input's filename). This
 * renames that one file to the name the founder actually asked for --
 * frontend/dist-standalone/board.html -- and fails loudly if anything besides
 * that one HTML file landed in the output directory, since a second file
 * would mean the singlefile plugin did not actually inline everything.
 */
import { existsSync, readdirSync, renameSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const outDir = join(root, 'dist-standalone');
const from = join(outDir, 'index.standalone.html');
const to = join(outDir, 'board.html');

if (!existsSync(from)) {
  throw new Error(`[finalize-standalone] expected ${from} to exist after vite build -- it did not.`);
}
renameSync(from, to);

const remaining = readdirSync(outDir);
if (remaining.length !== 1 || remaining[0] !== 'board.html') {
  throw new Error(
    `[finalize-standalone] expected dist-standalone/ to contain exactly board.html after the ` +
      `singlefile build, found: ${remaining.join(', ')}. Something did not get inlined.`,
  );
}

const bytes = statSync(to).size;
console.log(`[finalize-standalone] dist-standalone/board.html (${(bytes / 1024 / 1024).toFixed(2)} MB)`);
