import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Ground truth is read directly from data/export/*.json -- never from the
 * app's own rendered output, and never re-derived from frontend source. This
 * is the whole point of a content-assertion harness: an independent read of
 * the same files the app is supposed to be showing.
 */
export function loadGroundTruth(repoRoot) {
  const exportDir = join(repoRoot, 'data', 'export');
  const board = JSON.parse(readFileSync(join(exportDir, 'board.json'), 'utf8'));
  const league = JSON.parse(readFileSync(join(exportDir, 'league.json'), 'utf8'));

  return {
    board,
    league,
    playerCount: Array.isArray(board.players) ? board.players.length : null,
  };
}
