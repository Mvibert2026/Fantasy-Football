import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { stripInlineCitations, TraceModeProvider, useTraceMode } from '../data/traceMode';

/**
 * FR-121 (`docs/design/PROVENANCE-DISCLOSURE.md`) -- the global "show data
 * sources" switch. Founder's own words: *"I like the idea about traceablity, I
 * found a lot of things with those notes, I just want to be able to see a
 * version with and without them."* Never deletes anything; a visibility
 * condition, default off, persisted, toggled by the Settings checkbox
 * (`SettingsPanel.tsx`) or `Alt+T` (both drive this one module).
 */

const STORAGE_KEY = 'prep.showDataSources';

beforeEach(() => {
  localStorage.clear();
});

function Probe() {
  const { on, toggle } = useTraceMode();
  return (
    <button onClick={toggle} data-testid="probe">
      {on ? 'on' : 'off'}
    </button>
  );
}

describe('TraceModeProvider', () => {
  it('defaults to off with no stored preference', () => {
    render(
      <TraceModeProvider>
        <Probe />
      </TraceModeProvider>,
    );
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
  });

  it('toggle() flips state and persists it', () => {
    render(
      <TraceModeProvider>
        <Probe />
      </TraceModeProvider>,
    );
    fireEvent.click(screen.getByTestId('probe'));
    expect(screen.getByTestId('probe')).toHaveTextContent('on');
    expect(localStorage.getItem(STORAGE_KEY)).toBe('1');

    fireEvent.click(screen.getByTestId('probe'));
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('reads a stored "on" preference on mount', () => {
    localStorage.setItem(STORAGE_KEY, '1');
    render(
      <TraceModeProvider>
        <Probe />
      </TraceModeProvider>,
    );
    expect(screen.getByTestId('probe')).toHaveTextContent('on');
  });

  it('Alt+T toggles the switch', () => {
    render(
      <TraceModeProvider>
        <Probe />
      </TraceModeProvider>,
    );
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
    act(() => {
      fireEvent.keyDown(document, { key: 't', code: 'KeyT', altKey: true });
    });
    expect(screen.getByTestId('probe')).toHaveTextContent('on');
    act(() => {
      fireEvent.keyDown(document, { key: 't', code: 'KeyT', altKey: true });
    });
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
  });

  it('Alt+T does nothing while focus is inside a text input, so it never fights typing', () => {
    render(
      <TraceModeProvider>
        <input aria-label="question" />
        <Probe />
      </TraceModeProvider>,
    );
    const input = screen.getByLabelText('question');
    input.focus();
    act(() => {
      fireEvent.keyDown(input, { key: 't', code: 'KeyT', altKey: true });
    });
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
  });

  it('a component rendered without a provider gets the safe off default, not a crash', () => {
    // Most of this app's unit tests render a single view in isolation, not the
    // whole shell -- this is the property that keeps them all passing without
    // needing to know this switch exists.
    render(<Probe />);
    expect(screen.getByTestId('probe')).toHaveTextContent('off');
  });
});

describe('stripInlineCitations', () => {
  const text =
    'Between the two, that difference, not the point gap, is the reason for the order. ' +
    '[page.next_pick_reference] Reference point for the user\'s next pick before this answer was given.';

  it('leaves the text verbatim when trace mode is on', () => {
    expect(stripInlineCitations(text, true)).toBe(text);
  });

  it('strips a bracketed context-id token and collapses the resulting spacing when off', () => {
    const stripped = stripInlineCitations(text, false);
    expect(stripped).not.toContain('[page.next_pick_reference]');
    expect(stripped).not.toContain('  ');
    expect(stripped).toContain('is the reason for the order.');
    expect(stripped).toContain('Reference point for the user\'s next pick');
  });

  it('strips multiple tokens, e.g. the reasoning lane\'s six context-key dividers', () => {
    const many =
      '[page.draft_state] Some prose. [page.roster_needs] More prose. [page.recommendation] Even more.';
    const stripped = stripInlineCitations(many, false);
    expect(stripped).not.toMatch(/\[page\.\w+\]/);
    expect(stripped).toContain('Some prose.');
    expect(stripped).toContain('More prose.');
    expect(stripped).toContain('Even more.');
  });

  it('leaves ordinary text with no bracketed tokens untouched either way', () => {
    const plain = 'Bijan Robinson is the top-ranked RB on this board.';
    expect(stripInlineCitations(plain, false)).toBe(plain);
    expect(stripInlineCitations(plain, true)).toBe(plain);
  });
});
