import { fireEvent, render, screen } from '@testing-library/react';
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

  // Task 1 (data freshness on load): board.json:generated_utc is a real, named
  // field; the underlying ranking-snapshot staleness (src/freshness.py's T5
  // check) is a different claim that the backend does not export anywhere, so
  // it must read as an honest gap here, never a silently-omitted question.
  it('shows the real board.json:generated_utc timestamp and names the T5 staleness gap explicitly', () => {
    render(<RefreshData onApplied={vi.fn()} boardGeneratedUtc="2026-07-27T20:10:55.274740+00:00" />);

    const note = screen.getByTestId('freshness-note');
    expect(note).toHaveTextContent('2026-07-27T20:10:55.274740+00:00');
    expect(note).toHaveTextContent('snapshot freshness not exported by backend');
  });

  it('renders an honest dash, not a fabricated date, when the dataset has not loaded yet', () => {
    render(<RefreshData onApplied={vi.fn()} />);

    expect(screen.getByTestId('freshness-note')).toHaveTextContent('exported —');
  });

  // Founder ask, 2026-07-29: "we can remove that refresh data button" -- because
  // /__refresh is dev-server-only middleware (server/refresh.ts's configureServer
  // hook never attaches under `vite build`) and his daily use has moved to the
  // hosted static site, where the button could only ever fail. `refreshAvailable`
  // defaults to `import.meta.env.DEV` in real builds; here it's forced explicitly
  // so the test doesn't depend on how the bundler happens to inline that flag.
  it('hides the Refresh data button when the endpoint cannot exist (a production/static build), but keeps the freshness fact on screen', () => {
    render(
      <RefreshData
        onApplied={vi.fn()}
        boardGeneratedUtc="2026-07-27T20:10:55.274740+00:00"
        snapshotAgeDays={1}
        snapshotMaxAgeDays={14}
        snapshotStale={false}
        refreshAvailable={false}
      />,
    );

    expect(screen.queryByRole('button', { name: /refresh data/i })).not.toBeInTheDocument();
    // The header must not silently lose the freshness information just because
    // the (always-broken-there) button is gone.
    const note = screen.getByTestId('freshness-note');
    expect(note).toHaveTextContent('exported 2026-07-27T20:10:55.274740+00:00');
    expect(note).toHaveTextContent('snapshot fresh (1d old, max 14d)');
  });

  it('shows the Refresh data button when the endpoint can exist (dev server)', () => {
    render(<RefreshData onApplied={vi.fn()} refreshAvailable={true} />);
    expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument();
  });

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

  // Thread 073: this was the confirmed failing case -- the founder could not
  // clear this exact message, because the "Dismiss" button covered above was
  // the ONLY way to close it. Escape and click-outside are enumerated as
  // their own tests so either regressing independently fails on its own.
  it('closes on Escape', async () => {
    stubRefresh(NO_CHANGE);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));
    expect(await screen.findByText(/no update available/i)).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText(/no update available/i)).not.toBeInTheDocument();
  });

  it('closes on a click outside the popover', async () => {
    stubRefresh(NO_CHANGE);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));
    expect(await screen.findByText(/no update available/i)).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    expect(screen.queryByText(/no update available/i)).not.toBeInTheDocument();
  });

  it('does not close on a click inside the popover (e.g. the artifact table)', async () => {
    stubRefresh(CHANGED);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));
    expect(await screen.findByText(/1 artifact\(s\) changed/i)).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByText('board'));
    expect(screen.getByText(/1 artifact\(s\) changed/i)).toBeInTheDocument();
  });

  it('the unreachable-server error also closes on Escape (it previously had no dismiss control at all)', async () => {
    stubRefresh(null, false);
    render(<RefreshData onApplied={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: /refresh data/i }));
    expect(await screen.findByText(/could not be reached/i)).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText(/could not be reached/i)).not.toBeInTheDocument();
  });
});
