import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AssistantDock } from '../components/shell/AssistantDock';
import { Assistant } from '../views/Assistant';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * ASSISTANT-WINDOW.md item 4 -- the founder's two named complaints, each
 * asserted directly rather than inferred from a passing build:
 *
 *   "needs to have a constant window to be able to continue the conversation"
 *     -- a collapse must not destroy the conversation state `Assistant`
 *     holds. Real layout/paint (does it actually scroll on screen) is a
 *     screenshot's job, not jsdom's -- jsdom does not compute layout, so
 *     scrollHeight/clientHeight are always 0 here. What IS testable, and
 *     what actually was the bug: the container's inline sizing (a definite
 *     `top`+`bottom` box, not a `maxHeight: vh` one) and the fact that a
 *     long answer's full text reaches the DOM unclipped rather than being
 *     cut off after some fixed content budget.
 *
 *   "doesn't allow for scrolling"
 *     -- covered structurally below; see `frontend/e2e/artifacts/` for the
 *     actual rendered/visual proof (a screenshot scrolled to show both ends
 *     of a long answer).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

afterEach(() => vi.unstubAllGlobals());

function renderDock() {
  render(
    <AssistantDock where="Draft · pick 3">
      <Assistant data={data} rows={rows} league={league} pageContext={[]} />
    </AssistantDock>,
  );
}

describe('AssistantDock container sizing (ASSISTANT-WINDOW.md item 4)', () => {
  it('opens to a definite top+bottom box, not the old fixed-width/vh-fraction panel', async () => {
    renderDock();
    await userEvent.click(screen.getByText('Assistant'));

    // The panel is the nearest fixed-position ancestor of the standing input.
    const input = screen.getByPlaceholderText('Ask about the board');
    const panel = input.closest('div[style*="position: fixed"]') as HTMLElement;
    expect(panel).toBeTruthy();

    // Definite height from top+bottom, no maxHeight/vh fraction (the actual bug:
    // maxHeight gave flex children no definite box to size/overflow within).
    expect(panel.style.top).toBe('64px');
    expect(panel.style.bottom).toBe('18px');
    expect(panel.style.maxHeight).toBe('');

    // 520px, the spec's floor (docs/design/ASSISTANT-WINDOW.md: "520px
    // minimum, may grow to 720") -- not the old fixed 430px.
    expect(panel.style.width).toBe('520px');
  });
});

describe('AssistantDock conversation survives a collapse (the founder\'s actual ask)', () => {
  it('never unmounts the conversation: collapsing and reopening keeps prior turns intact', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ status: 'ok', text: 'A short answer.', context_ids: [] }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })),
    );

    renderDock();
    await userEvent.click(screen.getByText('Assistant'));

    const player = data.board.players[0]!.player;
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), `tell me about ${player}`);
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(screen.getByText('A short answer.')).toBeInTheDocument());

    // Collapse (the minimize control, not Escape/outside-click -- already
    // covered by assistant-dock-dismiss.test.tsx) -- the question text must
    // still be IN THE DOM (not unmounted), just not visible.
    await userEvent.click(screen.getByRole('button', { name: /collapse assistant/i }));
    const question = screen.getByText(`tell me about ${player}`);
    expect(question).not.toBeVisible();
    expect(screen.getByText('A short answer.')).not.toBeVisible();

    // Reopen -- the same turn is back, because it was never gone.
    await userEvent.click(screen.getByText('Assistant'));
    expect(screen.getByText(`tell me about ${player}`)).toBeVisible();
    expect(screen.getByText('A short answer.')).toBeVisible();

    // And the conversation is still live: a follow-up still carries history
    // (the same property assistant-conversation.test.tsx checks for a plain,
    // never-collapsed session) -- proving this is a real survived
    // conversation, not just leftover DOM text.
    await userEvent.type(screen.getByPlaceholderText('Ask a follow-up'), `what about ${player}'s upside`);
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(screen.getAllByText('A short answer.').length).toBe(2));
  });
});

describe('A long, multi-paragraph answer reaches the DOM in full (reachable via scroll)', () => {
  it('does not truncate a long answer -- both its opening and its closing lines are present', async () => {
    const paragraphs = Array.from({ length: 6 }, (_, i) => `Paragraph ${i + 1} of a long reasoning-lane answer, long enough that a fixed-height panel with no inner scroll would clip it before the end.`);
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(
        JSON.stringify({ status: 'ok', text: paragraphs.join('\n\n'), context_ids: ['page.draft_state'] }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      )),
    );

    render(<Assistant data={data} rows={rows} league={league} pageContext={[{
      id: 'page.draft_state',
      text: 'The current overall pick is 3.',
      confidence: 'high',
      source_path: 'live draft session (this browser): command bar pick clock',
    }]} />);

    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'walk me through your thinking here');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => expect(screen.getByText(/Paragraph 6 of/)).toBeInTheDocument());
    // The opening line is still reachable too -- not scrolled out of the DOM,
    // only (per the container test above) out of the currently visible frame.
    expect(screen.getByText(/Paragraph 1 of/)).toBeInTheDocument();
  });
});
