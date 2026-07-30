import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TopBar } from '../components/shell/TopBar';
import { applyUserSlotOverride, buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * docs/design/SUPPLIED-VALUES.md: the TopBar SLOT control's overridden value
 * used --acc green plus a "· sourced N" suffix. Green already means "good,
 * positive, better than baseline" on this board; a slot the founder picked
 * himself is not that. Now: no accent anywhere on this control, a dotted
 * underline on the value, and "set by you, league file says N" replacing
 * "· sourced N".
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);

function noop() {}

describe('SUPPLIED-VALUES.md: TopBar draft-slot control', () => {
  it('marks an overridden slot with a dotted underline and "set by you", never the --acc accent', () => {
    const sourced = league.userSlot.kind === 'present' ? league.userSlot.value : 1;
    const target = sourced === 1 ? 2 : 1;
    const overridden = applyUserSlotOverride(league, target);

    render(
      <TopBar
        mode="draft"
        onModeChange={noop}
        theme="dark"
        onToggleTheme={noop}
        league={overridden}
        leagues={[]}
        leagueId="primary"
        onSelectLeague={noop}
        onSelectSlot={noop}
        onClearSlot={noop}
      />,
    );

    const select = screen.getByRole('combobox', { name: 'Your draft slot' });
    expect(select.style.color).not.toBe('var(--acc)');
    expect(select.style.borderBottom).toBe('1px dotted var(--line2)');

    const slotLabel = screen.getByText('SLOT');
    expect(slotLabel.style.color).not.toBe('var(--acc)');

    const box = slotLabel.parentElement!;
    expect(box.style.border).not.toContain('var(--acc)');

    expect(screen.getByText(`· set by you, league file says ${sourced}`)).toBeInTheDocument();
    expect(screen.queryByText(`· sourced ${sourced}`)).not.toBeInTheDocument();

    const clearButton = screen.getByRole('button', { name: 'Clear draft slot override' });
    expect(clearButton.style.color).not.toBe('var(--acc)');
    expect(clearButton.style.border).not.toContain('var(--acc)');
  });

  it('renders no supplied-value marker at all when the slot is not overridden -- absence of the marker is itself information', () => {
    render(
      <TopBar
        mode="draft"
        onModeChange={noop}
        theme="dark"
        onToggleTheme={noop}
        league={league}
        leagues={[]}
        leagueId="primary"
        onSelectLeague={noop}
        onSelectSlot={noop}
        onClearSlot={noop}
      />,
    );
    expect(screen.queryByText(/set by you/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Clear draft slot override' })).not.toBeInTheDocument();
    const select = screen.getByRole('combobox', { name: 'Your draft slot' });
    expect(select.style.borderBottom).not.toBe('1px dotted var(--line2)');
  });
});
