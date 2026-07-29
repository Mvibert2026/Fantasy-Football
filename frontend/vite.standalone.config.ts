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
 * `define.__STANDALONE__` flips a compile-time flag `ui/data/playerHistory.ts`
 * checks (`declare const __STANDALONE__`) to skip its fetch entirely and go
 * straight to the same `error` state PlayerDetail.tsx's sections 7/8 already
 * render on a real failure -- undefined everywhere else (npm run dev, npm
 * test, npm run build all see it as falsy), so the live app's behavior is
 * unchanged. An earlier version of this file tried a `resolve.alias` swap
 * instead; that silently failed to match (Vite aliases match the raw import
 * specifier text, not the post-resolution absolute path, and the specifier
 * here is a relative `../data/playerHistory`) and shipped a real `fetch()`
 * that failed at runtime -- caught by verify-standalone.mjs, not assumed away.
 */
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  // Relative asset paths: this file is opened via `file://`, which has no
  // concept of a site root that a leading `/` could resolve against.
  base: './',
  // Vite copies the whole publicDir into outDir by default -- that's
  // frontend/public/data/*.json, the very fetched-at-runtime copies this
  // build exists to NOT depend on. Nothing in the standalone entry
  // references anything under public/, so there is nothing to copy.
  publicDir: false,
  define: {
    __STANDALONE__: true,
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
