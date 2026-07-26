import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { loadDatasetFromDisk } from './helpers';

/**
 * Guards what this app deliberately does not surface.
 *
 * Availability is the one that matters. Those figures are circular: their spread comes
 * from assuming two named managers repeat their 2025 TE picks, so a probability read
 * off them is conditional on an assumption the reader cannot see. ADR-033 records the
 * decision to demote them to display-only, but the export still ships `te_scenarios`
 * and per-player `availability` blocks, so the protection here is simply that nothing
 * renders them.
 *
 * That protection is one careless import away from disappearing, and the failure would
 * be silent -- a probability rendered as if it were marginal. Hence a test rather than
 * a comment.
 *
 * If availability is ever brought into scope, this test should fail loudly and be
 * replaced by whatever presents it as a named-assumption scenario rather than a fact.
 */

const APP_DIRS = ['ui/views', 'ui/components', 'ui/assistant', 'ui/data', 'ui/lib'];

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.tsx?$/.test(entry)) out.push(full);
  }
  return out;
}

/** Strips comments so a mention in prose does not read as a use. */
function code(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');
}

describe('out-of-scope data stays out', () => {
  const files = APP_DIRS.flatMap(walk);

  it('has app files to scan', () => {
    expect(files.length).toBeGreaterThan(0);
  });

  it('never dereferences per-player availability', () => {
    const offenders = files.filter((f) => /\.availability\b/.test(code(readFileSync(f, 'utf8'))));
    expect(
      offenders,
      `These files read player.availability: ${offenders.join(', ')}.\n` +
        `Availability figures are circular — their spread comes from assuming two managers ` +
        `repeat their 2025 TE picks (ADR-033). Rendering one as a probability presents a ` +
        `conditional forecast as a marginal fact. If availability is now in scope, present it ` +
        `as a named-assumption scenario and update this test deliberately.`,
    ).toEqual([]);
  });

  it('never reads the availability artifact or its scenario blocks', () => {
    // Property or index access, not a bare mention. The trace-field registry names
    // `availability` as a known-but-unrendered field and the changelog discusses the
    // artifact in prose -- both are documentation, and neither reads a value.
    const banned = /[.[]\s*['"]?(?:te_scenarios|by_tier|by_player|sigma_(?:5|10|20))\b/;
    const offenders = files.filter((f) => banned.test(code(readFileSync(f, 'utf8'))));
    expect(
      offenders,
      `These files reach into availability data: ${offenders.join(', ')}. ` +
        `te_scenarios in particular is a conditional forecast under a named assumption, not a ` +
        `marginal probability, and merging the two would let the UI present a scenario as a fact.`,
    ).toEqual([]);
  });

  it('does not load the availability artifact', () => {
    const loader = code(readFileSync('ui/data/load.ts', 'utf8'));
    expect(loader).not.toMatch(/fetchJson<[^>]*>\('availability'\)/);
  });

  it('the board type carries availability but the rows never expose it', () => {
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
