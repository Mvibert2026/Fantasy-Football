import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { autoSyncExports } from './server/autoSync';
import { reasoningProxy } from './server/proxy';
import { refreshEndpoint } from './server/refresh';
import { EXPECTED_CONTRACT } from './ui/data/contract';

/**
 * The reasoning proxy runs as Vite dev-server middleware rather than as a separate
 * process, so `npm run dev` remains the only command needed to run the whole app.
 *
 * The key is read here, in Node, via loadEnv with an empty prefix. Vite only exposes
 * variables prefixed `VITE_` to client code, and nothing here is ever written into
 * `define`, so ANTHROPIC_API_KEY cannot reach the browser bundle.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      react(),
      reasoningProxy(env.ANTHROPIC_API_KEY),
      refreshEndpoint(EXPECTED_CONTRACT),
      autoSyncExports(),
    ],
    server: { port: 5173 },
    test: {
      environment: 'jsdom',
      // Scoped to ui/ so the Python suite under tests/ is never collected.
      include: ['ui/**/*.test.{ts,tsx}'],
      setupFiles: ['ui/test-setup.ts'],
      globals: true,
    },
  };
});
