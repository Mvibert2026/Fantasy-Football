import { spawn, execSync } from 'node:child_process';

/**
 * Starts the frontend's own `npm run dev` (vite) as a subprocess, pinned to a
 * port distinct from 5173 with --strictPort so it fails loudly instead of
 * silently sharing a port with another session's dev server, rather than
 * spawning a second, competing instance of the same default port.
 */
export function startDevServer({ cwd, port }) {
  const child = spawn('npm', ['run', 'dev', '--', '--port', String(port), '--strictPort'], {
    cwd,
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let log = '';
  child.stdout.on('data', (d) => { log += d.toString(); });
  child.stderr.on('data', (d) => { log += d.toString(); });

  return {
    child,
    getLog: () => log,
  };
}

export async function waitForServer(url, { timeoutMs = 30000, intervalMs = 500 } = {}) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status === 404) return true;
    } catch (err) {
      lastError = err;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Dev server did not respond at ${url} within ${timeoutMs}ms: ${lastError}`);
}

/**
 * `npm run dev` spawns vite as a child of a child (npm -> node -> vite on
 * Windows via npm.cmd) -- child.kill() only signals the immediate npm
 * process and leaves vite running. taskkill /T kills the whole tree.
 */
export function stopDevServer(child) {
  if (!child || child.killed || child.exitCode !== null) return;
  if (process.platform === 'win32') {
    try {
      execSync(`taskkill /pid ${child.pid} /T /F`, { stdio: 'ignore' });
    } catch {
      // Already gone -- fine.
    }
  } else {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      child.kill('SIGTERM');
    }
  }
}
