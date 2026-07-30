import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Assistant } from '../views/Assistant';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-077: "Chatbot ony allows for one question input at a time, it needs a
 * clear standing chat box, and and answer area, shrink the number of
 * suggested or relevant questions to 3 tops." Three properties under test:
 * the standing input survives asking a question (it was never literally
 * removed, but confirm it explicitly since this is the exact founder
 * complaint), starter buttons are capped to 3, and a follow-up question
 * actually carries the conversation so far to the reasoning lane -- the
 * dispatch's own instruction: "otherwise 'standing chat box' is cosmetic."
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function mockReasoningFetch(reply: (body: { question: string; history?: unknown[] }) => string) {
  const calls: Array<{ question: string; history: unknown[] }> = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const body = JSON.parse((init?.body as string) ?? '{}');
      calls.push({ question: body.question, history: body.history ?? [] });
      return new Response(
        JSON.stringify({ status: 'ok', text: reply(body), context_ids: (body.context ?? []).map((c: { id: string }) => c.id) }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      );
    }),
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe('Assistant conversation surface (FR-077)', () => {
  it('shows at most 3 suggested-question buttons, not the full template set', () => {
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);
    const buttons = screen.getAllByRole('button').filter((b) => b.hasAttribute('title'));
    expect(buttons.length).toBeLessThanOrEqual(3);
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('keeps the input present and usable after asking a question -- never a one-shot field', async () => {
    mockReasoningFetch(() => 'A short answer.');
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);

    const player = data.board.players[0]!.player;
    const input = screen.getByPlaceholderText('Ask about the board');
    await userEvent.type(input, `tell me about ${player}`);
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => expect(screen.getByText('A short answer.')).toBeInTheDocument());

    // The input is still there, still empty and ready for the next question --
    // this is the literal "standing chat box" claim.
    const inputAfter = screen.getByPlaceholderText('Ask a follow-up');
    expect(inputAfter).toBeInTheDocument();
    expect((inputAfter as HTMLInputElement).value).toBe('');
    expect(inputAfter).not.toBeDisabled();
  });

  it('shows both turns in the answer area at once -- a real conversation, not a single-answer swap', async () => {
    mockReasoningFetch(() => 'Answer text.');
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);

    const player = data.board.players[0]!.player;
    async function ask(text: string) {
      const input = screen.getByRole('textbox');
      await userEvent.clear(input);
      await userEvent.type(input, text);
      await userEvent.click(screen.getByRole('button', { name: /ask/i }));
      await waitFor(() => expect(screen.getAllByText('Answer text.').length).toBeGreaterThan(0));
    }

    await ask(`tell me about ${player}`);
    await ask(`what about ${player}'s upside`);

    expect(screen.getByText(`tell me about ${player}`)).toBeInTheDocument();
    expect(screen.getByText(`what about ${player}'s upside`)).toBeInTheDocument();
  });

  it('sends the prior turn as history on a follow-up question, and no history on the first', async () => {
    const calls = mockReasoningFetch((body) => `Reply to: ${body.question}`);
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);

    const player = data.board.players[0]!.player;
    const input = screen.getByRole('textbox');

    await userEvent.type(input, `tell me about ${player}`);
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.history).toEqual([]);

    await userEvent.type(screen.getByRole('textbox'), `what about ${player}'s upside`);
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.history).toHaveLength(1);
    expect((calls[1]!.history[0] as { question: string }).question).toBe(`tell me about ${player}`);
    expect((calls[1]!.history[0] as { answerText: string }).answerText).toContain(`Reply to: tell me about ${player}`);
  });

  it('passes page-context items through to the reasoning lane request', async () => {
    const calls: Array<{ context: Array<{ id: string }> }> = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
        const body = JSON.parse((init?.body as string) ?? '{}');
        calls.push(body);
        return new Response(JSON.stringify({ status: 'ok', text: 'ok', context_ids: [] }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      }),
    );
    const pageContext = [
      {
        id: 'page.draft_state',
        text: 'The current overall pick is 7 (round 1). The user is on the clock right now.',
        confidence: 'high' as const,
        source_path: 'live draft session (this browser): command bar pick clock',
      },
    ];
    render(<Assistant data={data} rows={rows} league={league} pageContext={pageContext} />);

    await userEvent.type(screen.getByRole('textbox'), 'what are my likely choices at my next pick');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.context.some((c) => c.id === 'page.draft_state')).toBe(true);
  });
});
