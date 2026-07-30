import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Assistant } from '../views/Assistant';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk, withTraceOn } from './helpers';

/**
 * FR-121 / `docs/design/PROVENANCE-DISCLOSURE.md` item 1 -- the exact case the
 * founder named: the assistant panel printing a raw provenance line, including
 * (for the reasoning lane) a "model prose over context: page.draft_state,
 * page.roster_needs, ..." dump. `.claim` tag and text are meaning, not
 * sourcing, and stay visible either way; only the `.provenance` line is gated.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

afterEach(() => vi.unstubAllGlobals());

describe('Assistant provenance line (export lane, deterministic)', () => {
  it('hides the provenance line by default -- no glossary.json field path or claim tag text visible', async () => {
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'what is VBD');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(document.querySelector('.claim')).toBeTruthy());

    expect(document.querySelector('.provenance')).toBeNull();
    expect(document.body.textContent).not.toContain('glossary.json:terms');
  });

  it('shows the provenance line, verbatim, once the switch is on', async () => {
    render(withTraceOn(<Assistant data={data} rows={rows} league={league} pageContext={[]} />));
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'what is VBD');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(document.querySelector('.provenance')).toBeTruthy());

    expect(document.body.textContent).toContain('glossary.json:terms');
  });

  it('the claim tag and its text render in both states -- only sourcing is gated', async () => {
    render(<Assistant data={data} rows={rows} league={league} pageContext={[]} />);
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'what is VBD');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(document.querySelector('.claim')).toBeTruthy());
    expect(document.querySelector('.tag-MODEL')).toBeTruthy();
  });
});

describe('Assistant inline citation tokens (reasoning lane)', () => {
  function mockReasoningFetch(text: string) {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
        const body = JSON.parse((init?.body as string) ?? '{}');
        return new Response(
          JSON.stringify({ status: 'ok', text, context_ids: (body.context ?? []).map((c: { id: string }) => c.id) }),
          { status: 200, headers: { 'content-type': 'application/json' } },
        );
      }),
    );
  }

  const modelReply =
    'Between the two, that difference, not the point gap, is the reason for the order. ' +
    "[page.next_pick_reference] Reference point for the user's next pick before this answer was given.";

  // A non-empty page-context bundle (the always-included FR-076 case) guarantees
  // the reasoning lane's `retrieveContext(...).length === 0` short-circuit does
  // not fire regardless of what the free-text question happens to lexically
  // match against the static corpus -- the property under test here is what
  // happens to the model's OWN reply text, not retrieval matching.
  const pageContext = [
    {
      id: 'page.next_pick_reference',
      text: "Reference point for the user's next pick.",
      confidence: 'high' as const,
      source_path: 'live draft session (this browser): command bar pick clock',
    },
  ];

  it('strips inline [page.*] context-key dividers from the model prose by default', async () => {
    mockReasoningFetch(modelReply);
    render(<Assistant data={data} rows={rows} league={league} pageContext={pageContext} />);
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'walk me through your thinking here');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(document.querySelector('.claim')).toBeTruthy());

    expect(document.body.textContent).not.toContain('[page.next_pick_reference]');
    expect(document.body.textContent).toContain('is the reason for the order.');
  });

  it('leaves the model prose verbatim, brackets included, once the switch is on', async () => {
    mockReasoningFetch(modelReply);
    render(withTraceOn(<Assistant data={data} rows={rows} league={league} pageContext={pageContext} />));
    await userEvent.type(screen.getByPlaceholderText('Ask about the board'), 'walk me through your thinking here');
    await userEvent.click(screen.getByRole('button', { name: /ask/i }));
    await waitFor(() => expect(document.querySelector('.claim')).toBeTruthy());

    expect(document.body.textContent).toContain('[page.next_pick_reference]');
  });
});
