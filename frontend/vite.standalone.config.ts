import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { viteSingleFile } from 'vite-plugin-singlefile';

/**
 * Standalone build: one self-contained HTML file, no dev server, no `fetch()`
 * at runtime, opens straight from `file://`. See docs/frontend-cloud-runbook.md
 * for the full recipe and ui/StandaloneApp.tsx's module doc for what is
 * deliberately absent versus the live app (Draft/Season modes, the multi-
 * league switcher, "Refresh data", the Assistant chat dock, and PlayerDetail's
 * season-history sections).
 *
 * Separate from vite.config.ts on purpose: the live app's config wires three
 * dev-server-only middlewares (reasoning proxy, refresh endpoint, auto-sync)
 * that have no meaning in a build with no server at the far end, and this
 * build's own entry point (index.standalone.html / ui/main.standalone.tsx)
 * needs a different `build.rollupOptions.input` than the default `index.html`.
 *
 * `resolve.alias` swaps in the standalone player-history stub (no fetch) for
 * PlayerDetail.tsx's history import, WITHOUT touching that shared component or
 * ui/data/playerHistory.ts -- the live app (npm run dev / npm test) is not
 * affected by anything in this file.
 */
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  // Relative asset paths: this file is opened via `file://`, which has no
  // concept of a site root that a leading `/` could resolve against.
  base: './',
  resolve: {
    alias: {
      [resolve(__dirname, 'ui/data/playerHistory.ts')]: resolve(
        __dirname,
        'ui/data/playerHistory.standalone.ts',
      ),
    },
  },
  build: {
    outDir: 'dist-standalone',
    emptyOutDir: true,
    // vite-plugin-singlefile requires all module graphs inlined into one
    // chunk; splitting defeats it, so it's turned off here specifically
    // rather than in the shared vite.config.ts.
    cssCodeSplit: false,
    rollupOptions: {
      input: resolve(__dirname, 'index.standalone.html'),
      output: { inlineDynamicImports: true },
    },
  },
});
