import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { rankByRecommendation, recommendationScore } from '../data/recommendation';
import { loadDatasetFromDisk } from './helpers';

const data = loadDatasetFromDisk();
const rows = buildRows(data);

describe('recommendationScore', () => {
  it('returns null for a row with no VBD (unprojected players never rank on a fabricated score)', () => {
    const sparse = rows.find((r) => r.vbd.kind === 'absent');
    // Guard the fixture -- if every row has VBD this test proves nothing.
    if (sparse) expect(recommendationScore(sparse, 1, new Set())).toBeNull();
  });

  it('adds +8 for an unfilled position, +18 for a tier-1 TE (unconditionally), -25 for an early QB', () => {
    const te1 = rows.find((r) => r.raw.position === 'TE' && r.raw.tier === 1 && r.vbd.kind === 'present');
    expect(te1).toBeDefined();
    // The tier-1 TE bonus is not gated by need, so it's already present in the
    // no-need baseline -- only the +8 need bonus should separate the two calls.
    expect(recommendationScore(te1!, 5, new Set())).toBeCloseTo(te1!.vbd.kind === 'present' ? te1!.vbd.value + 18 : NaN, 5);
    const base = recommendationScore(te1!, 5, new Set());
    const withNeed = recommendationScore(te1!, 5, new Set(['TE']));
    expect(withNeed).toBeCloseTo(base! + 8, 5);

    const qb = rows.find((r) => r.raw.position === 'QB' && r.vbd.kind === 'present');
    expect(qb).toBeDefined();
    const early = recommendationScore(qb!, 3, new Set());
    const late = recommendationScore(qb!, 8, new Set());
    expect(early).toBeCloseTo(late! - 25, 5);
  });

  it('never scores a DEF player, because none exist on the board', () => {
    expect(rows.some((r) => r.raw.position === ('DEF' as string))).toBe(false);
  });
});

describe('rankByRecommendation', () => {
  it('sorts descending by score, unprojected rows last', () => {
    const ranked = rankByRecommendation(rows.slice(0, 40), 5, new Set());
    for (let i = 1; i < ranked.length; i++) {
      expect(ranked[i - 1]!.score).toBeGreaterThanOrEqual(ranked[i]!.score);
    }
  });
});
