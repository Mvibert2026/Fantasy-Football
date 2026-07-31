import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { assistantContextDocs } from '../assistant/retrieval';
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

/**
 * docs/handoffs/2026-07-31-wire-assistant-retrieval-to-docs-assistant-conte.md:
 * before `assistantContextDocs` existed, nothing in `frontend/` or `worker/`
 * referenced `docs/assistant-context.md` at all -- confirmed by grep, zero hits.
 * Librarian's curated intervals, effective n and stated scope never reached the
 * reasoning lane. These tests cover the two properties that matter: the file's
 * content is genuinely reachable through the same retrieval path as every other
 * artifact, and a chunk boundary never severs an interval from the sentence
 * stating what it applies to (or leaves a stray, unpaired markdown `**`).
 */
describe('assistant-context.md retrieval (FR/thread: wire assistant retrieval)', () => {
  it('null (not synced, or file absent) yields no documents -- not a crash, not an empty placeholder claim', () => {
    expect(assistantContextDocs(null)).toEqual([]);
  });

  it('a prose section is kept as one document, heading plus full body verbatim, not truncated', () => {
    const md = [
      '# Assistant Context',
      '',
      '## Why alpha detection is closed for 2026',
      '',
      'Market-consensus data only exists for 2021-2025, and one of those five seasons',
      'is held back as an honest test. No further work is planned until roughly 2028.',
    ].join('\n');
    const docs = assistantContextDocs(md);
    expect(docs).toHaveLength(1);
    expect(docs[0]!.text).toContain('Why alpha detection is closed for 2026');
    // The interval/scope detail must survive whole, in the same chunk as the
    // headline claim -- not split off into a separate document that could be
    // retrieved (or dropped) independently of the claim it qualifies.
    expect(docs[0]!.text).toContain('2021-2025');
    expect(docs[0]!.text).toContain('2028');
    expect(docs[0]!.source_path).toBe('docs/assistant-context.md#why-alpha-detection-is-closed-for-2026');
  });

  it('a bulleted section splits one document per bullet, each a self-contained settled decision', () => {
    const md = [
      '# Assistant Context',
      '',
      '## Registered nulls',
      '',
      '- **Spike-week ability is not a persistent player trait.** r is near zero across 26 seasons.',
      '- **Hero RB has no measurable edge.** Coin flip in either direction.',
    ].join('\n');
    const docs = assistantContextDocs(md);
    expect(docs).toHaveLength(2);
    expect(docs.map((d) => d.id)).toEqual(['assistant_context.registered-nulls.0', 'assistant_context.registered-nulls.1']);
    expect(docs[0]!.text).toContain('Spike-week ability is not a persistent player trait');
    expect(docs[0]!.text).toContain('26 seasons');
    expect(docs[1]!.text).toContain('Hero RB has no measurable edge');
    // Neither bullet's text should leak the other's content.
    expect(docs[0]!.text).not.toContain('Hero RB');
    expect(docs[1]!.text).not.toContain('Spike-week');
  });

  it('never leaves a stray, unpaired markdown bold marker in a chunk -- a chunk boundary can split a bold span', () => {
    const md = ['# Assistant Context', '', '## Some section', '', '- **Bold claim.** Rest of the sentence.'].join(
      '\n',
    );
    const docs = assistantContextDocs(md);
    expect(docs[0]!.text).not.toContain('**');
  });

  it('empty or absent sections produce no phantom documents', () => {
    const md = ['# Assistant Context', '', '## Empty section', '', '## Real section', '', 'Some real content.'].join(
      '\n',
    );
    const docs = assistantContextDocs(md);
    expect(docs).toHaveLength(1);
    expect(docs[0]!.text).toContain('Some real content');
  });

  it('end to end: a question the real assistant-context.md answers, and nothing else in the corpus does, retrieves it with the interval/scope intact', () => {
    if (!data.assistantContextMd) {
      throw new Error(
        'fixture expected public/data/assistant_context.md to exist -- run node scripts/sync-exports.mjs first',
      );
    }
    const items = retrieveContext(data, rows, 'is alpha detection happening for 2026');
    const hit = items.find((i) => i.id.startsWith('assistant_context.'));
    expect(hit).toBeDefined();
    expect(hit!.source_path).toMatch(/^docs\/assistant-context\.md#/);
    // The scope (which seasons, why the number is what it is) must ride along
    // with the verdict -- exactly what the dispatch's "does it survive intact"
    // question is checking, not just the word "closed".
    expect(hit!.text).toContain('2021');
    expect(hit!.text).toContain('2025');
    expect(hit!.text).not.toContain('**');
  });
});
