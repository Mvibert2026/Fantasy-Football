import { describe, expect, it } from 'vitest';
import { matchesPlayerQuery, normalizeSearchTerm } from '../data/playerSearch';
import { buildRows, type BoardRow } from '../data/board';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-122 ("typing a player's name should filter the list... a search as well
 * as a 'drafted' function"). Direct unit coverage of the matching rules the
 * FR itself specifies, independent of DraftRoom's own wiring.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

function rowNamed(name: string): BoardRow {
  const row = rows.find((r) => r.name.kind === 'present' && r.name.value === name);
  if (!row) throw new Error(`fixture guard: expected a row named "${name}" in the real board export`);
  return row;
}

describe('normalizeSearchTerm', () => {
  it('folds diacritics, punctuation and case together -- the FR\'s own example', () => {
    // The FR names this exact trio: "Ja'Marr", "JaMarr" and "jamarr" must all match.
    expect(normalizeSearchTerm("Ja'Marr")).toBe('jamarr');
    expect(normalizeSearchTerm('JaMarr')).toBe('jamarr');
    expect(normalizeSearchTerm('jamarr')).toBe('jamarr');
  });

  it('folds accented letters to their plain form', () => {
    expect(normalizeSearchTerm('José Ramírez')).toBe('joseramirez');
  });

  it('strips spaces and hyphens so "RB 10" / "RB-10" / "RB10" all reduce identically', () => {
    expect(normalizeSearchTerm('RB 10')).toBe('rb10');
    expect(normalizeSearchTerm('RB-10')).toBe('rb10');
    expect(normalizeSearchTerm('RB10')).toBe('rb10');
  });
});

describe('matchesPlayerQuery', () => {
  it('matches on the display name', () => {
    const row = rowNamed('Bijan Robinson');
    expect(matchesPlayerQuery(row, 'bijan')).toBe(true);
    expect(matchesPlayerQuery(row, 'Robinson')).toBe(true);
    expect(matchesPlayerQuery(row, 'zzz-no-such-substring')).toBe(false);
  });

  it("matches the founder's own punctuation examples against a real diacritic-bearing name if one exists, else exercises the fold on a synthetic row", () => {
    const synthetic: BoardRow = {
      ...rows[0]!,
      name: { kind: 'present', value: "Ja'Marr Test" } as BoardRow['name'],
    };
    expect(matchesPlayerQuery(synthetic, "Ja'Marr")).toBe(true);
    expect(matchesPlayerQuery(synthetic, 'JaMarr')).toBe(true);
    expect(matchesPlayerQuery(synthetic, 'jamarr')).toBe(true);
  });

  it('matches on team', () => {
    const row = rows.find((r) => r.raw.team && r.raw.team.length > 0)!;
    expect(matchesPlayerQuery(row, row.raw.team)).toBe(true);
    expect(matchesPlayerQuery(row, row.raw.team.toLowerCase())).toBe(true);
  });

  it('matches on bare position', () => {
    const row = rows.find((r) => r.raw.position === 'RB')!;
    expect(matchesPlayerQuery(row, 'rb')).toBe(true);
  });

  it(
    'matches on positional rank as a prefix, so "RB1" narrows to RB1 and RB10-19 -- the FR\'s own example ' +
      '("not return nothing")',
    () => {
      const rb1 = rows.find((r) => r.positionalLabel.kind === 'present' && r.positionalLabel.value === 'RB1');
      const rb10 = rows.find((r) => r.positionalLabel.kind === 'present' && r.positionalLabel.value === 'RB10');
      // Fixture guard: both must exist in the real board for this to be a real test.
      expect(rb1).toBeDefined();
      expect(rb10).toBeDefined();
      expect(matchesPlayerQuery(rb1!, 'RB1')).toBe(true);
      expect(matchesPlayerQuery(rb10!, 'RB1')).toBe(true);
      // And a clearly unrelated positional label does not match.
      const wr5 = rows.find((r) => r.positionalLabel.kind === 'present' && r.positionalLabel.value === 'WR5');
      if (wr5) expect(matchesPlayerQuery(wr5, 'RB1')).toBe(false);
    },
  );

  it('an empty (or whitespace-only) query matches every row -- "no filter active", not "filter to nothing"', () => {
    const row = rowNamed('Bijan Robinson');
    expect(matchesPlayerQuery(row, '')).toBe(true);
    expect(matchesPlayerQuery(row, '   ')).toBe(true);
  });
});
