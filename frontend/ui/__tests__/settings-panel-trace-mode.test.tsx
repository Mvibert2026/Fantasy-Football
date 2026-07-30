import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { TopBar } from '../components/shell/TopBar';
import { buildLeagueConfig } from '../data/league';
import { TraceModeProvider } from '../data/traceMode';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-121 / `docs/design/PROVENANCE-DISCLOSURE.md`. The founder's own ask: put
 * the control in the existing Settings panel. This exercises the real
 * `TraceModeProvider` (App.tsx/StandaloneApp.tsx wrap the whole shell in one;
 * `settings-panel.test.tsx`'s existing suite renders TopBar bare, which is
 * fine for the boundary-rule assertions it covers but can't exercise a real
 * toggle interaction since there's no provider above it to toggle).
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);
const STORAGE_KEY = 'prep.showDataSources';

function noop() {}

function renderTopBar() {
  return render(
    <TraceModeProvider>
      <TopBar
        mode="prep"
        onModeChange={noop}
        theme="dark"
        onToggleTheme={noop}
        league={league}
        leagues={[]}
        leagueId="primary"
        onSelectLeague={noop}
        onSelectSlot={noop}
        onClearSlot={noop}
      />
    </TraceModeProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe('Settings panel "show data sources" switch (FR-121)', () => {
  it('is labelled in the founder\'s own language -- never "provenance", "trace", or "field path"', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    expect(screen.getByText('Show data sources')).toBeInTheDocument();
    const dialog = screen.getByRole('dialog', { name: 'Settings' });
    expect(dialog.textContent).not.toMatch(/provenance/i);
    expect(dialog.textContent).not.toMatch(/\btrace\b/i);
    expect(dialog.textContent).not.toMatch(/field path/i);
  });

  it('is off by default, unchecked, no persistent indicator on screen', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
    expect(screen.queryByTestId('show-data-sources-indicator')).not.toBeInTheDocument();
  });

  it('checking it turns on the persistent indicator and persists the boolean to localStorage', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

    fireEvent.click(checkbox);

    expect(checkbox.checked).toBe(true);
    expect(screen.getByTestId('show-data-sources-indicator')).toBeInTheDocument();
    expect(localStorage.getItem(STORAGE_KEY)).toBe('1');
  });

  it('unchecking it removes the indicator and clears the stored preference', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

    fireEvent.click(checkbox);
    fireEvent.click(checkbox);

    expect(checkbox.checked).toBe(false);
    expect(screen.queryByTestId('show-data-sources-indicator')).not.toBeInTheDocument();
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('a stored "on" preference from a prior session renders the indicator immediately on mount', () => {
    localStorage.setItem(STORAGE_KEY, '1');
    renderTopBar();
    expect(screen.getByTestId('show-data-sources-indicator')).toBeInTheDocument();
  });

  it('Alt+T toggles the same indicator, without opening Settings', () => {
    renderTopBar();
    expect(screen.queryByTestId('show-data-sources-indicator')).not.toBeInTheDocument();
    fireEvent.keyDown(document, { key: 't', code: 'KeyT', altKey: true });
    expect(screen.getByTestId('show-data-sources-indicator')).toBeInTheDocument();
  });
});
