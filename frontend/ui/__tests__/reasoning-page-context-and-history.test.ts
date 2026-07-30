import { afterEach, describe, expect, it, vi } from 'vitest';
import { buildRows } from '../data/board';
import type { ContextItem, ConversationTurn } from '../assistant/reasoning';
import { runReasoningLane } from '../assistant/reasoning';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-076 + FR-077 together: the reasoning lane must (a) always have the
 * page-context bundle available to it, even for a question that shares no
 * vocabulary with the static exports, and (b) carry conversation history to
 * the endpoint so a follow-up question can resolve a referent from the prior
 * turn. Root-cause note from the dispatch: "retrieval is a small set of regex
 * templates, not a model capability... confirm this before building" -- these
 * tests confirm the *fix* landed where the gap actually was (this lane), not
 * that the diagnosis was correct in isolation.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

const PAGE_ITEM: ContextItem = {
  id: 'page.recommendation',
  text: 'For the pick happening right now: the top recommendation is Test Player (RB).',
  confidence: 'high',
  source_path: 'live draft session (this browser): Draft Room > Recommend tab, top card',
};

function mockFetchOk() {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) =>
    new Response(JSON.stringify({ status: 'ok', text: 'An answer.', context_ids: ['page.recommendation'] }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => vi.unstubAllGlobals());

describe('runReasoningLane: page context', () => {
  it('answers from page context alone when lexical retrieval finds nothing but page context exists', async () => {
    const fetchMock = mockFetchOk();
    // A question that shares no vocabulary with any static export (confirmed by
    // the pre-existing retrieval test "a truly unrelated question returns
    // nothing"), but the real failure this whole feature exists to fix: a
    // question about the current pick, answerable only from page state.
    const outcome = await runReasoningLane(data, rows, 'what are my likely choices and trade-offs at my next pick', [
      PAGE_ITEM,
    ]);
    expect(outcome.status).toBe('ok');
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
    expect(body.context.some((c: ContextItem) => c.id === 'page.recommendation')).toBe(true);
  });

  it('still reports no_context when neither lexical retrieval nor page context has anything', async () => {
    const fetchMock = mockFetchOk();
    const outcome = await runReasoningLane(data, rows, 'zzz qqq xyzzy', []);
    expect(outcome.status).toBe('no_context');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('merges page context with real lexical retrieval rather than one replacing the other', async () => {
    const fetchMock = mockFetchOk();
    const player = data.board.players[0]!.player;
    await runReasoningLane(data, rows, `tell me about ${player}`, [PAGE_ITEM]);
    const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
    const ids: string[] = body.context.map((c: ContextItem) => c.id);
    expect(ids).toContain('page.recommendation');
    expect(ids.some((id) => id.startsWith('board.'))).toBe(true);
  });
});

describe('runReasoningLane: conversation history', () => {
  it('sends prior turns to the endpoint alongside the current question and context', async () => {
    const fetchMock = mockFetchOk();
    const history: ConversationTurn[] = [
      { question: 'who is the best RB available', answerText: 'Test Player is the top recommendation.' },
    ];
    await runReasoningLane(data, rows, 'what about him', [PAGE_ITEM], history);
    const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
    expect(body.history).toHaveLength(1);
    expect(body.history[0].question).toBe('who is the best RB available');
    expect(body.history[0].answerText).toContain('Test Player');
  });

  it('bounds history to the most recent turns and truncates a long prior answer', async () => {
    const fetchMock = mockFetchOk();
    const longHistory: ConversationTurn[] = Array.from({ length: 10 }, (_, i) => ({
      question: `question ${i}`,
      answerText: 'x'.repeat(1000),
    }));
    await runReasoningLane(data, rows, 'a follow-up', [PAGE_ITEM], longHistory);
    const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
    expect(body.history.length).toBeLessThan(10);
    expect(body.history.length).toBeGreaterThan(0);
    for (const turn of body.history) {
      expect(turn.answerText.length).toBeLessThanOrEqual(601); // MAX_HISTORY_ANSWER_CHARS + the ellipsis char
    }
    // The most recent turns survive, not the oldest.
    expect(body.history[body.history.length - 1].question).toBe('question 9');
  });

  it('sends an empty history array on the first question of a session', async () => {
    const fetchMock = mockFetchOk();
    await runReasoningLane(data, rows, 'a first question', [PAGE_ITEM]);
    const body = JSON.parse((fetchMock.mock.calls[0]![1] as RequestInit).body as string);
    expect(body.history).toEqual([]);
  });
});
