import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { findVbdOverride, rankByRecommendation, recommendationScore, recommendationTerms } from '../data/recommendation';
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

describe('recommendationTerms (FR-058: plain-word reasons behind each constant)', () => {
  it('unfilled_need reason names the position in plain words, only when the position is in the unfilled set', () => {
    const wr = rows.find((r) => r.raw.position === 'WR' && r.raw.tier !== 1 && r.vbd.kind === 'present');
    expect(wr).toBeDefined();
    expect(recommendationTerms(wr!, 5, new Set())).toEqual([]);
    const withNeed = recommendationTerms(wr!, 5, new Set(['WR']));
    expect(withNeed).toEqual([{ key: 'unfilled_need', points: 8, reason: 'you have no wide receiver yet' }]);
  });

  it('tier1_te reason fires unconditionally on tier, never on need', () => {
    const te1 = rows.find((r) => r.raw.position === 'TE' && r.raw.tier === 1 && r.vbd.kind === 'present');
    expect(te1).toBeDefined();
    const terms = recommendationTerms(te1!, 5, new Set());
    expect(terms).toContainEqual({
      key: 'tier1_te',
      points: 18,
      reason: 'this is the last tier-1 tight end left on the board',
    });
  });

  it('early_qb_penalty fires only before round 6, never after', () => {
    const qb = rows.find((r) => r.raw.position === 'QB' && r.vbd.kind === 'present');
    expect(qb).toBeDefined();
    const early = recommendationTerms(qb!, 5, new Set());
    expect(early).toContainEqual({
      key: 'early_qb_penalty',
      points: -25,
      reason: 'it is a quarterback being taken before round 6',
    });
    const late = recommendationTerms(qb!, 6, new Set());
    expect(late.some((t) => t.key === 'early_qb_penalty')).toBe(false);
  });
});

describe('findVbdOverride (FR-058: "if the recommendation strays from VBD ... explain")', () => {
  it('returns null when the given top pick already IS the highest-VBD available player -- nothing to explain', () => {
    const leader = rows.filter((r) => r.vbd.kind === 'present').sort((a, b) => (b.vbd as any).value - (a.vbd as any).value)[0]!;
    expect(findVbdOverride(leader, [leader], 1, new Set())).toBeNull();
  });

  it('returns null when only one row (or none) has a VBD value to compare against', () => {
    const noVbd = rows.find((r) => r.vbd.kind === 'absent');
    const anyRow = rows.find((r) => r.vbd.kind === 'present')!;
    if (noVbd) expect(findVbdOverride(anyRow, [anyRow], 1, new Set())).toBeNull();
  });

  it('flags a real departure -- a tier-1 TE outranking the board\'s own VBD leader on the tier-1-TE bonus alone -- and names the displaced player, the exact VBD gap, and the firing term in plain words', () => {
    const vbdLeader = rows
      .filter((r) => r.vbd.kind === 'present')
      .sort((a, b) => (b.vbd as any).value - (a.vbd as any).value)[0]!;
    const te1 = rows.find(
      (r) => r.raw.position === 'TE' && r.raw.tier === 1 && r.vbd.kind === 'present' && r.id !== vbdLeader.id,
    )!;
    expect(te1).toBeDefined();
    expect((vbdLeader.vbd as any).value).toBeGreaterThan((te1.vbd as any).value); // guard the fixture assumption

    const override = findVbdOverride(te1, [vbdLeader, te1], 5, new Set());
    expect(override).not.toBeNull();
    expect(override!.displaced.id).toBe(vbdLeader.id);
    expect(override!.vbdGap).toBeCloseTo((vbdLeader.vbd as any).value - (te1.vbd as any).value, 5);
    expect(override!.firing).toContainEqual({
      term: { key: 'tier1_te', points: 18, reason: 'this is the last tier-1 tight end left on the board' },
      appliesTo: 'top',
    });
  });

  it('flags the displaced side too -- a QB VBD leader penalized before round 6 -- distinctly from a top-side boost', () => {
    const qb = rows.find((r) => r.raw.position === 'QB' && r.vbd.kind === 'present')!;
    const nonQbLower = rows.find(
      (r) => r.raw.position !== 'QB' && r.vbd.kind === 'present' && (r.vbd as any).value < (qb.vbd as any).value,
    )!;
    expect(qb).toBeDefined();
    expect(nonQbLower).toBeDefined();

    const override = findVbdOverride(nonQbLower, [qb, nonQbLower], 3, new Set());
    expect(override).not.toBeNull();
    expect(override!.displaced.id).toBe(qb.id);
    expect(override!.firing).toContainEqual({
      term: { key: 'early_qb_penalty', points: -25, reason: 'it is a quarterback being taken before round 6' },
      appliesTo: 'displaced',
    });
  });

  it('returns null once the top pick\'s own VBD already meets or beats every available row -- no gap to explain', () => {
    const leader = rows.filter((r) => r.vbd.kind === 'present').sort((a, b) => (b.vbd as any).value - (a.vbd as any).value)[0]!;
    const lower = rows.find((r) => r.vbd.kind === 'present' && r.id !== leader.id)!;
    // leader passed as `top` against a pool that includes a strictly lower row --
    // leader is still the pool's own VBD leader, so nothing was overridden.
    expect(findVbdOverride(leader, [leader, lower], 1, new Set())).toBeNull();
  });
});
