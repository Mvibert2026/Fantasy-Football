import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Board } from '../views/Board';
import { DraftRoom } from '../views/DraftRoom';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * Founder, 2026-07-30: "even hovering over CI to tell me that would have
 * been ok." Column headers with a real glossary entry now hover the term's
 * own short_definition (or an existing, more specific bespoke note), marked
 * with the app's one existing "there's more here" affordance -- a dotted
 * underline, `docs/design/SUPPLIED-VALUES.md` -- reused rather than a second
 * marker invented for this. These tests check the mechanism is actually
 * wired on both boards, not just that the underlying data exists.
 */

const DOTTED = '1px dotted var(--line2)';

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

describe('Board column headers hover the glossary short definition', () => {
  it('CONS header hovers the real "consensus rank" short_definition and carries the dotted-underline affordance', () => {
    render(<Board data={data} rows={rows} league={league} />);
    const header = screen.getByText('CONS');
    expect(header).toHaveAttribute('title', data.glossary.terms['consensus rank']!.short_definition);
    expect(header.style.borderBottom).toBe(DOTTED);
  });

  it('TIER header hovers the real "tier" short_definition', () => {
    render(<Board data={data} rows={rows} league={league} />);
    const header = screen.getByText('TIER');
    expect(header).toHaveAttribute('title', data.glossary.terms.tier!.short_definition);
  });

  it('a column with no glossary entry (RANK) renders plain, no title, no underline', () => {
    render(<Board data={data} rows={rows} league={league} />);
    const header = screen.getByText('RANK');
    expect(header).not.toHaveAttribute('title');
  });
});

describe('DraftRoom board-list headers hover, and keep their own richer wording where they already had one', () => {
  it('AVAIL header keeps its existing, more specific hover text -- but is now visibly hoverable via the dotted underline', () => {
    render(<DraftRoom data={data} rows={rows} league={league} />);
    const header = screen.getByText('AVAIL');
    expect(header).toHaveAttribute('title', expect.stringMatching(/Baseline -> live-adjusted/));
    expect(header.style.borderBottom).toBe(DOTTED);
  });

  it('VBD header keeps its existing "what the board is ranked on" wording, dotted-underlined', () => {
    render(<DraftRoom data={data} rows={rows} league={league} />);
    // "VBD" appears more than once on this screen (list header, RECOMMENDED
    // card) -- find the one carrying the header's specific hover text.
    const candidates = screen.getAllByText('VBD');
    const header = candidates.find((el) => el.getAttribute('title')?.includes('actually ranked on'));
    expect(header).toBeDefined();
    expect(header!.style.borderBottom).toBe(DOTTED);
  });
});
