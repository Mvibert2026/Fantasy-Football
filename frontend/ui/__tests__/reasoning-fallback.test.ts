import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { retrieveContext } from '../assistant/reasoning';
import { loadDatasetFromDisk } from './helpers';

/**
 * The reasoning lane used to refuse outright whenever a question mentioned no
 * player name, no glossary term, and no nulls.json keyword -- "Which strategy
 * appears best?" returned nothing, even though strategies.json contains exactly
 * that data. This is the fix: when nothing narrow matches, hand over
 * strategies.json's comparisons and every nulls.json finding instead of stopping,
 * with the honesty guarantee carried in the tagging (every claim built from this
 * context is still tagged INFERENCE downstream) rather than in refusing to try.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
// The default league (what loadDatasetFromDisk reads) always carries strategies.json.
if (!data.strategies) throw new Error('fixture expected to carry strategies.json');
const strategies = data.strategies;

describe('reasoning lane context fallback', () => {
  it('used to refuse a strategy question with zero context; now retrieves strategies.json', () => {
    const items = retrieveContext(data, rows, 'Which strategy appears best?');
    expect(items.length).toBeGreaterThan(0);
    expect(items.some((i) => i.source_path.startsWith('strategies.json:'))).toBe(true);
    // Every real strategy shows up, not just one cherry-picked example.
    for (const strategy of strategies.strategies) {
      expect(items.some((i) => i.text.includes(strategy.name))).toBe(true);
    }
  });

  it('includes the power floor caveat so significance is never overstated', () => {
    const items = retrieveContext(data, rows, 'which strategy is best');
    const floor = items.find((i) => i.source_path === 'strategies.json:power_floor.plain_english');
    expect(floor).toBeDefined();
    expect(floor?.text).toBe(strategies.power_floor.plain_english);
    expect(floor?.confidence).toBe('high');
  });

  it('states plainly that strategies were not simulated in combination', () => {
    const items = retrieveContext(data, rows, 'which strategy is best');
    const caveat = items.find((i) => i.id === 'strategies.not_compositional');
    expect(caveat).toBeDefined();
    expect(caveat?.text).toMatch(/new simulation/i);
  });

  it('retrieves nulls.json findings for a positional-valuation question with no keyword hit', () => {
    // Checked against every nulls.json claim_tested string: no word here over 4
    // characters ("should", "focus", "receivers", "middle", "rounds") appears in
    // any of them, so the OLD narrow keyword matcher would have found nothing.
    const items = retrieveContext(data, rows, 'should I focus on wide receivers in the middle rounds');
    expect(items.some((i) => i.source_path.startsWith('nulls.json:'))).toBe(true);
    expect(items.length).toBeGreaterThanOrEqual(data.nulls.findings.length);
  });

  it('every context item carries a real, checkable source_path', () => {
    const items = retrieveContext(data, rows, 'which strategy is best');
    for (const item of items) {
      expect(item.source_path).toMatch(/^\w+\.json:/);
      expect(item.text.trim()).not.toBe('');
    }
  });

  it('a player-specific question still gets narrow, player-specific context, not the fallback dump', () => {
    const player = data.board.players[0]!;
    const items = retrieveContext(data, rows, `tell me about ${player.player}`);
    expect(items.some((i) => i.text.includes(player.player))).toBe(true);
    // Narrow context does not also carry strategies.json -- the fallback only
    // fires when nothing narrow matched at all.
    expect(items.some((i) => i.source_path.startsWith('strategies.json:'))).toBe(false);
  });

  it('a truly unrelated question still gets something rather than silently nothing', () => {
    // Even a question sharing no vocabulary with any export still reaches the
    // fallback dump, because the fallback no longer depends on keyword overlap.
    const items = retrieveContext(data, rows, 'zzz qqq xyzzy');
    expect(items.length).toBeGreaterThan(0);
  });
});
