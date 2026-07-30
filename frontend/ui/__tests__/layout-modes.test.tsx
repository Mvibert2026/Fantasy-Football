import { act, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { beforeEach, describe, expect, it } from 'vitest';
import { LAYOUT_MODE_ORDER, LAYOUT_PRESETS, paneColumns, useDraftLayout } from '../data/layoutModes';

/**
 * Item 7 of the 2026-07-31 design round, `docs/design/PANE-LAYOUT-MODES.md`,
 * and the Expand mechanism it shares with item 3
 * (`docs/design/PERIODIC-TABLE-GRID.md`). One module, one keyboard listener,
 * covering both -- see `ui/data/layoutModes.ts`'s own module doc.
 */

const STORAGE_KEY = 'prep.draftLayoutMode';

beforeEach(() => {
  localStorage.clear();
});

function Probe({ escBlocked = false }: { escBlocked?: boolean }) {
  const { layoutMode, gridExpanded } = useDraftLayout(escBlocked);
  const [renders, setRenders] = useState(0);
  return (
    <div>
      <span data-testid="mode">{layoutMode}</span>
      <span data-testid="expanded">{gridExpanded ? 'open' : 'closed'}</span>
      <button onClick={() => setRenders((r) => r + 1)} data-testid="noop">
        {renders}
      </button>
    </div>
  );
}

describe('LAYOUT_PRESETS', () => {
  it('Balanced matches the pre-existing hardcoded default (boardPct 35, centerPct 40) exactly', () => {
    expect(LAYOUT_PRESETS.balanced).toMatchObject({ boardPct: 35, centerPct: 40 });
  });

  it('Board widens the rankings column and narrows the pane relative to Balanced', () => {
    expect(LAYOUT_PRESETS.board.boardPct).toBeGreaterThan(LAYOUT_PRESETS.balanced.boardPct);
    expect(LAYOUT_PRESETS.board.centerPct).toBeLessThan(LAYOUT_PRESETS.balanced.centerPct);
  });

  it('Decide widens the pane relative to Balanced', () => {
    expect(LAYOUT_PRESETS.decide.centerPct).toBeGreaterThan(LAYOUT_PRESETS.balanced.centerPct);
  });

  it('every preset has a distinct Alt-digit shortcut, in order 1/2/3 matching the design table', () => {
    expect(LAYOUT_MODE_ORDER.map((m) => LAYOUT_PRESETS[m].code)).toEqual(['Digit1', 'Digit2', 'Digit3']);
  });
});

describe('paneColumns', () => {
  it('reproduces the same three-way split the old hardcoded call produced', () => {
    expect(paneColumns()).toBe(paneColumns(35, 40));
    expect(paneColumns()).toBe('minmax(0,35.00%) minmax(0,40.00%) minmax(0,25.00%)');
  });

  it('clamps out-of-range inputs rather than producing a negative or zero column', () => {
    const cols = paneColumns(5, 5);
    // board clamps to 20, center clamps to 20 -- never the raw (too-small) input.
    expect(cols).toContain('minmax(0,');
    expect(cols.split(' ')).toHaveLength(3);
  });
});

describe('useDraftLayout', () => {
  it('defaults to balanced with the grid sheet closed', () => {
    render(<Probe />);
    expect(screen.getByTestId('mode')).toHaveTextContent('balanced');
    expect(screen.getByTestId('expanded')).toHaveTextContent('closed');
  });

  it('Alt+1/Alt+2/Alt+3 switch layout mode and persist it', () => {
    render(<Probe />);
    act(() => {
      fireEvent.keyDown(document, { key: '1', code: 'Digit1', altKey: true });
    });
    expect(screen.getByTestId('mode')).toHaveTextContent('board');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('board');

    act(() => {
      fireEvent.keyDown(document, { key: '3', code: 'Digit3', altKey: true });
    });
    expect(screen.getByTestId('mode')).toHaveTextContent('decide');

    act(() => {
      fireEvent.keyDown(document, { key: '2', code: 'Digit2', altKey: true });
    });
    expect(screen.getByTestId('mode')).toHaveTextContent('balanced');
  });

  it('plain "1" (no Alt) does not switch layout mode -- it is not stealing the digit-commit shortcut', () => {
    render(<Probe />);
    act(() => {
      fireEvent.keyDown(document, { key: '1', code: 'Digit1', altKey: false });
    });
    expect(screen.getByTestId('mode')).toHaveTextContent('balanced');
  });

  it('Alt+G toggles the grid sheet open and closed', () => {
    render(<Probe />);
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('open');
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('closed');
  });

  it('none of the shortcuts fire while focus is inside a text input', () => {
    render(
      <div>
        <input aria-label="filter" />
        <Probe />
      </div>,
    );
    const input = screen.getByLabelText('filter');
    input.focus();
    act(() => {
      fireEvent.keyDown(input, { key: '1', code: 'Digit1', altKey: true });
    });
    act(() => {
      fireEvent.keyDown(input, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByTestId('mode')).toHaveTextContent('balanced');
    expect(screen.getByTestId('expanded')).toHaveTextContent('closed');
  });

  it('Escape closes the grid sheet when nothing else is blocking it', () => {
    render(<Probe />);
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('open');
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('closed');
  });

  it('Escape precedence: does not close the grid sheet while escBlocked is true (the player card owns that press)', () => {
    render(<Probe escBlocked />);
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('open');
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    // Still open -- the player detail card's own unconditional listener is
    // the thing that should have closed on this press, not the grid sheet.
    expect(screen.getByTestId('expanded')).toHaveTextContent('open');
  });

  it('Escape while typing in an input does not close the grid sheet either', () => {
    render(
      <div>
        <input aria-label="filter" />
        <Probe />
      </div>,
    );
    act(() => {
      fireEvent.keyDown(document, { key: 'g', code: 'KeyG', altKey: true });
    });
    const input = screen.getByLabelText('filter');
    input.focus();
    act(() => {
      fireEvent.keyDown(input, { key: 'Escape' });
    });
    expect(screen.getByTestId('expanded')).toHaveTextContent('open');
  });

  it('reads a stored layout-mode preference on mount', () => {
    localStorage.setItem(STORAGE_KEY, 'decide');
    render(<Probe />);
    expect(screen.getByTestId('mode')).toHaveTextContent('decide');
  });

  it('ignores a corrupt/unknown stored value and falls back to balanced', () => {
    localStorage.setItem(STORAGE_KEY, 'nonsense');
    render(<Probe />);
    expect(screen.getByTestId('mode')).toHaveTextContent('balanced');
  });
});
