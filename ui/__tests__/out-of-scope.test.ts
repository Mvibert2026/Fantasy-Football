import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { loadDatasetFromDisk } from './helpers';

/**
 * Guards what this app deliberately does not surface.
 *
 * At contract 1.6.0 the backend removed the prior-year repeat assumption from the
 * availability model and dropped `te_scenarios` entirely (ADR-033/034) -- the
 * circularity this file used to guard against is gone, and the broad "availability
 * stays out" test that lived here has been retired along with it. The Availability
 * screen (`ui/data/availability.ts`, `ui/views/Availability.tsx`) reads
 * `availability.json` directly.
 *
 * What's left is narrower and still true regardless of that change:
 *
 *   - `board.json` carries its own embedded, per-player `.availability` field
 *     (top ~80 players only, a different and older shape than the dedicated
 *     availability.json). That field is not the real source and this app never
 *     reads it -- using it instead of availability.json would be a step backward,
 *     not a step into scope.
 *   - The round grid shows where the board sits at a given pick, which is
 *     arithmetic on rank, not a prediction of who will still be there. That
 *     distinction has nothing to do with availability circularity and remains
 *     true either way.
 */

describe('board.json embedded availability stays unused', () => {
  it('the board type carries a per-player availability field but rows never expose it', () => {
    // The field exists on the raw export and is typed, so it is visible to anyone
    // reading the code -- it is simply never lifted into a Cell and so can never render.
    const data = loadDatasetFromDisk();
    const rows = buildRows(data);
    const withAvailability = data.board.players.filter(
      (p) => p.availability && Object.keys(p.availability).length > 0,
    );
    expect(withAvailability.length).toBeGreaterThan(0); // the data really is there

    const rowKeys = Object.keys(rows[0] ?? {});
    expect(rowKeys).not.toContain('availability');
  });

  it('the round grid disclaims any availability prediction on screen', () => {
    // JSX wraps the sentence across lines, so normalise whitespace before matching.
    const grid = readFileSync('ui/views/RoundGrid.tsx', 'utf8').replace(/\s+/g, ' ');
    // It shows where the board sits at a pick -- arithmetic -- and says so in the UI,
    // not just in a comment, because the user is the one who could misread it.
    expect(grid).toMatch(/not a claim that the player will still be there/i);
  });
});
