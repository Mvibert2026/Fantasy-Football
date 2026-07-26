import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RefreshData } from '../components/RefreshData';

/**
 * The Refresh control is the bridge between the two sessions, and it is the thing that
 * has to keep working once both go quiet. These cover the three outcomes that matter:
 * something changed, nothing changed, and the server is gone.
 *
 * The middle case is the one worth guarding. A no-op that renders nothing is
 * indistinguishable from a broken button, and a user would reasonably conclude the
 * feature is broken rather than that their data is current.
 */

function stubRefresh(body: unknown, ok = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      if (!ok) throw new TypeError('Failed to fetch');
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }),
  );
}

const NO_CHANGE = {
  updated: false,
  message: 'No update available. data/export/ has not been re-copied since the last refresh.',
  checkedAt: '2026-07-26T00:00:00.000Z',
  changes: [
    {
      artifact: 'board',
      before: { contract_version: '1.4.0', generated_utc: 'x' },
      after: { contract_version: '1.4.0', generated_utc: 'x' },
      change: 'unchanged' as const,
    },
  ],
  behindExpected: [],
  expected: '1.4.0',
};

const CHANGED = {
  updated: true,
  message: '1 artifact(s) changed.',
  checkedAt: '2026-07-26T00:00:00.000Z',
  changes: [
    {
      artifact: 'board',
      before: { contract_version: '1.3.0', generated_utc: 'old' },
      after: { contract_version: '1.4.0', generated_utc: 'new' },
      change: 'version' as const,
    },
  ],
  behindExpected: [],
  expected: '1.4.0',
};

describe('Refresh data control', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('says "no update available" instead of doing nothing visible', async () => {
    stubRefresh(NO_CHANGE);
    const onApplied = vi.fn();
    render(<RefreshData onApplied={onApplied} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));

    expect(await screen.findByText(/no update available/i)).toBeInTheDocument();
    // A no-op must not pretend to have reloaded anything.
    expect(onApplied).not.toHaveBeenCalled();
  });

  it('shows a before/after and applies the change when something moved', async () => {
    stubRefresh(CHANGED);
    const onApplied = vi.fn();
    render(<RefreshData onApplied={onApplied} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));

    expect(await screen.findByText(/1 artifact\(s\) changed/i)).toBeInTheDocument();
    expect(screen.getByText('1.3.0')).toBeInTheDocument();
    expect(screen.getByText('1.4.0')).toBeInTheDocument();
    expect(screen.getByText(/contract version changed/i)).toBeInTheDocument();
    expect(onApplied).toHaveBeenCalledTimes(1);
  });

  it('names artifacts still behind the expected contract', async () => {
    stubRefresh({
      ...NO_CHANGE,
      behindExpected: [{ artifact: 'strategies', version: '1.0.0' }],
    });
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));

    expect(await screen.findByText(/strategies \(1\.0\.0\)/)).toBeInTheDocument();
    expect(screen.getByText(/nothing is adjusted to compensate/i)).toBeInTheDocument();
  });

  it('explains itself when the dev server is not running', async () => {
    stubRefresh(null, false);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));

    const message = await screen.findByText(/could not be reached/i);
    expect(message).toBeInTheDocument();
    // The board on screen is still valid -- say so rather than implying data loss.
    expect(screen.getByText(/still valid/i)).toBeInTheDocument();
  });

  it('can be dismissed', async () => {
    stubRefresh(NO_CHANGE);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));
    expect(await screen.findByText(/no update available/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));
    expect(screen.queryByText(/no update available/i)).not.toBeInTheDocument();
  });
});
