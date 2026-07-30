import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TopBar } from '../components/shell/TopBar';
import { buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-069 / FR-040 / `docs/design/LEAGUE-SETTINGS-BOUNDARY.md`. TopBar used to
 * render a static, unclickable "Settings — not built" string
 * (design/INERT-CONTROLS.md's rule for a dead affordance). Now a real button
 * opens a panel that enforces the spec's absolute rule: the screen must not
 * accept a setting it cannot apply.
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);

function noop() {}

function renderTopBar() {
  return render(
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
    />,
  );
}

describe('Settings panel (FR-069/FR-040)', () => {
  it('renders no dead "not built" text -- a real, clickable Settings control exists', () => {
    renderTopBar();
    expect(screen.queryByText(/Settings — not built/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Settings' })).toBeInTheDocument();
  });

  it('opens a panel naming the draft slot as the one applies-immediately field, and closes on Escape', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));

    expect(screen.getByRole('dialog', { name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByText(/DRAFT SLOT — applies immediately/)).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: 'Settings' })).not.toBeInTheDocument();
  });

  it('closes on a click on the transparent backdrop, same dismiss convention as PlayerDetail', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    fireEvent.click(screen.getByTestId('settings-backdrop'));
    expect(screen.queryByRole('dialog', { name: 'Settings' })).not.toBeInTheDocument();
  });

  it('renders SCORED UNDER as a read-only statement -- no input elements anywhere in the panel', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));

    expect(screen.getByText('SCORED UNDER')).toBeInTheDocument();
    const rulesetText = league.scoringRulesetNote.kind === 'present' ? league.scoringRulesetNote.value : null;
    if (rulesetText) {
      expect(screen.getByText(rulesetText)).toBeInTheDocument();
    }
    // The scoring section carries zero <input>/<select> elements -- the panel's
    // only interactive control is the draft-slot <select> from DraftSlotControl.
    const dialog = screen.getByRole('dialog', { name: 'Settings' });
    const selects = dialog.querySelectorAll('select');
    expect(selects.length).toBe(1);
    expect(selects[0]).toHaveAttribute('aria-label', 'Your draft slot');
  });

  it('states plainly that team count and roster shape are not editable here, even though the design spec calls them applies-immediately', () => {
    renderTopBar();
    fireEvent.click(screen.getByRole('button', { name: 'Settings' }));
    expect(screen.getByText(/Team count and roster shape are not editable here/)).toBeInTheDocument();
  });
});
