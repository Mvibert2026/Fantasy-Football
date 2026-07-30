import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { retrieveContext } from '../assistant/reasoning';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-048's "real bottleneck" finding: the reasoning lane used to retrieve context
 * two ways -- exact substring matching on player names/glossary terms/nulls
 * keywords, and, when that found nothing, an UNCONDITIONAL dump of every
 * strategies.json comparison and every nulls.json finding regardless of whether
 * any of it was actually relevant. The second path meant a question that shared
 * no real vocabulary with anything in the exports still got a full context
 * array -- indistinguishable, from the model's perspective, from a fixed prompt
 * with no retrieval at all, and a direct violation of rule 3 (refuse rather than
 * answer from general football knowledge when nothing genuinely matches).
 *
 * `ui/assistant/retrieval.ts` replaces both paths with one BM25-style lexical
 * scorer over a corpus built from every shipped artifact. These tests check the
 * two properties that matter: real questions that share real vocabulary with the
 * exports find it (much more of the time than the old narrow matcher could), and
 * a question that shares nothing gets nothing back -- not a consolation dump.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

describe('retrieval', () => {
  it('a truly unrelated question returns nothing -- rule 3, not a fallback dump', () => {
    // The old fallback would have handed back every strategy and every nulls
    // finding for this. Real lexical retrieval correctly finds no overlap.
    const items = retrieveContext(data, rows, 'zzz qqq xyzzy');
    expect(items).toEqual([]);
  });

  it('a player-specific question gets exact, high-confidence board context', () => {
    const player = data.board.players[0]!;
    const items = retrieveContext(data, rows, `tell me about ${player.player}`);
    expect(items.length).toBeGreaterThan(0);
    expect(items.every((i) => i.text.includes(player.player))).toBe(true);
    // Exact name match -> high confidence, not a hedge.
    expect(items.every((i) => i.confidence === 'high')).toBe(true);
    expect(items.some((i) => i.source_path.startsWith('board.json:players['))).toBe(true);
  });

  it('a strategy-comparison question retrieves real strategies.json content', () => {
    if (!data.strategies) throw new Error('fixture expected to carry strategies.json');
    const items = retrieveContext(data, rows, 'which draft strategy is best');
    expect(items.some((i) => i.source_path.startsWith('strategies.json:strategies['))).toBe(true);
  });

  it('attaches the power-floor and not-compositional caveats whenever a strategy result is shown', () => {
    // These two are short and share little vocabulary with most strategy
    // questions, so they would not clear the relevance floor on lexical merit
    // alone -- attachWhenKindPresent pairs them with any strategy hit instead,
    // because showing a strategy comparison without the significance caveat
    // would overstate what a 4-season backtest can support (CLAUDE.md 6.3).
    const items = retrieveContext(data, rows, 'is hero rb a good strategy');
    const floor = items.find((i) => i.source_path === 'strategies.json:power_floor.plain_english');
    const caveat = items.find((i) => i.id === 'strategies.not_compositional');
    expect(floor).toBeDefined();
    expect(floor?.text).toBe(data.strategies!.power_floor.plain_english);
    expect(floor?.confidence).toBe('high');
    expect(caveat).toBeDefined();
    expect(caveat?.text).toMatch(/new simulation/i);
  });

  it('does not attach the strategy caveats to a question with no strategy content at all', () => {
    const player = data.board.players[0]!;
    const items = retrieveContext(data, rows, `tell me about ${player.player}`);
    expect(items.some((i) => i.id === 'strategies.power_floor')).toBe(false);
  });

  it('retrieves league.json content for a league-configuration question', () => {
    const items = retrieveContext(data, rows, 'what is the trade deadline in this league');
    expect(items.some((i) => i.source_path.startsWith('league.json:'))).toBe(true);
  });

  it('retrieves player_descriptions.json content for a named player with an archetype description', () => {
    const described = data.playerDescriptions?.players[0];
    if (!described) return; // Primary league only; nothing to assert if absent.
    const items = retrieveContext(data, rows, `what is ${described.player_name} like as a player`);
    expect(items.some((i) => i.source_path.startsWith('player_descriptions.json:'))).toBe(true);
  });

  it('a real nulls.json finding is reachable by a differently-worded question, not just its own vocabulary', () => {
    // "when should I take a tight end" shares no words with PR-003-elite-te's
    // claim_tested field via the OLD narrow matcher (no player name, no glossary
    // term, no nulls keyword substring) -- but the finding's own plain-language
    // summary literally discusses reaching for a tight end early, so real lexical
    // scoring over the full text finds it where substring matching could not.
    const items = retrieveContext(data, rows, 'when should I take a tight end');
    expect(items.some((i) => i.id === 'nulls.PR-003-elite-te')).toBe(true);
  });

  it('never returns more than one confidence tier of overstatement: no non-exact match is high', () => {
    // Confidence must track match quality, not the shape of the data (FR-048).
    // A lexical, non-exact match is never 'high' unless it's an attached
    // companion (a deterministic pairing, not a loose keyword accident).
    const items = retrieveContext(data, rows, 'is our board better than consensus');
    for (const item of items) {
      if (item.confidence !== 'high') continue;
      const isAttachedCaveat = item.id === 'strategies.power_floor' || item.id === 'strategies.not_compositional';
      const isExactNameOrTerm = data.board.players.some((p) => item.text.includes(p.player)) || isAttachedCaveat;
      expect(isExactNameOrTerm).toBe(true);
    }
  });

  it('caps how many near-duplicate documents from one artifact can dominate a result set', () => {
    // player_descriptions.json templates its prose per archetype, so many bench
    // tight ends share near-identical wording. Without a per-kind cap, a broad
    // positional question returns a wall of interchangeable blurbs instead of a
    // mix of sources.
    const items = retrieveContext(data, rows, 'when should I take a tight end');
    const playerDescriptionHits = items.filter((i) => i.id.startsWith('player_descriptions.'));
    expect(playerDescriptionHits.length).toBeLessThanOrEqual(3);
  });

  it('every context item carries a real, checkable source_path and non-empty text', () => {
    for (const question of ['which draft strategy is best', 'what is the trade deadline in this league']) {
      const items = retrieveContext(data, rows, question);
      for (const item of items) {
        expect(item.source_path).toMatch(/^\w+\.json:/);
        expect(item.text.trim()).not.toBe('');
      }
    }
  });
});
