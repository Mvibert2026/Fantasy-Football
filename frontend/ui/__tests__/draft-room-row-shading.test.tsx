import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * LIGHT-THEME-SHADING.md (2026-07-31, design item 5): shipped for Board.tsx
 * the same day, explicitly left undone on this screen -- `docs/CURRENT-STATE.md`
 * names DraftRoom.tsx as one of the "similar per-row hairlines" not yet given
 * the alternating-tint/raised-row treatment. This file checks the rankings
 * pane's rows now carry the exact same tokens Board.tsx's already-shipped
 * `BoardRowLine` uses (Board.tsx:591-598) -- not new, invented values.
 *
 * Values are read as the literal inline-style strings React renders, since
 * jsdom cannot resolve CSS custom properties into real colours -- the
 * property under test is "this row uses the SAME var(...) expression Board.tsx
 * uses," which a string comparison checks exactly and a computed-colour
 * check could not (jsdom would just report the var() text back unresolved
 * either way).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

function renderDraftRoom() {
  return render(<DraftRoom data={data} rows={rows} league={league} />);
}

describe('LIGHT-THEME-SHADING.md parity: the rankings pane rows match Board.tsx\'s already-shipped tables', () => {
  it('alternates row background between transparent and the light-only --row-alt token, with a fallback to transparent (unchanged in dark)', () => {
    renderDraftRoom();
    const sample = rows.slice(0, 6).filter((r) => r.name.kind === 'present');
    expect(sample.length).toBeGreaterThan(2);
    const backgrounds = sample.map((r) => screen.getByTestId(`rankings-pane-row-${r.id}`).style.background);
    // Every background is one of exactly the two tokens Board.tsx's BoardRowLine
    // uses for an unselected row -- never a third, invented value.
    for (const bg of backgrounds) {
      expect(['transparent', 'var(--row-alt, transparent)']).toContain(bg);
    }
    // And they actually alternate (not all the same value) -- same rowIndex %
    // 2 pattern Board.tsx uses.
    expect(new Set(backgrounds).size).toBeGreaterThan(1);
  });

  it('the row hairline falls back through --row-line to --line, the same fallback chain Board.tsx\'s BoardRowLine uses, not a bare --line', () => {
    renderDraftRoom();
    const first = rows.find((r) => r.name.kind === 'present')!;
    const row = screen.getByTestId(`rankings-pane-row-${first.id}`);
    expect(row.style.borderBottom).toBe('1px solid var(--row-line, var(--line))');
  });

  it('a row with its "why this rank" detail open becomes the raised row (--panel2), same as Board.tsx\'s selected-row treatment, and drops its hairline', () => {
    renderDraftRoom();
    const target = rows.find((r) => r.name.kind === 'present' && r.deltaVsConsensus.kind === 'present')!;
    const row = screen.getByTestId(`rankings-pane-row-${target.id}`);

    // The Δ cell (title "Why this rank -- click to expand") toggles the row's
    // own inline detail panel. Every row has one with this exact title, so
    // scope the query to this specific row.
    fireEvent.click(within(row).getByTitle('Why this rank -- click to expand'));

    expect(row.style.background).toBe('var(--panel2)');
    // jsdom's CSS engine does not retain `border-bottom: none` as a shorthand
    // value (verified directly: setting it leaves style.borderBottom === ''),
    // so the real assertion here is the negative one that matters --
    // the hairline var() is gone, not literally which string replaced it.
    expect(row.style.borderBottom).not.toContain('var(--row-line');
  });
});
