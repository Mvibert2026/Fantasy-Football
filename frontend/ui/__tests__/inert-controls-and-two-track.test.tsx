import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Board } from '../views/Board';
import { Glossary } from '../views/Glossary';
import { StrategyGuide } from '../views/StrategyGuide';
import { TopBar } from '../components/shell/TopBar';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { fetchSelectableLeagues } from '../data/league-registry';
import type { SelectableLeague } from '../data/league-registry';
import { loadDatasetFromDisk } from './helpers';

/**
 * design/INERT-CONTROLS.md (FR-037) and design/TWO-TRACK-EXPRESSION.md
 * (FR-042, FR-027), 2026-07-29.
 *
 * INERT-CONTROLS: "A control that cannot act is not a control. Render the
 * fact instead of the dead affordance." Covers the six controls the founder
 * has been clicking and finding dead: Export CSV, Export PDF, League
 * settings, Compare, Ask, and per-term Ask the assistant in the glossary.
 * Every one of them must be gone -- not merely still disabled -- and the
 * fact that replaces each one must actually be on screen.
 *
 * League settings is no longer one of the six dead ones -- FR-069/FR-040
 * built a real panel this session (`ui/components/shell/SettingsPanel.tsx`).
 * Its own coverage below now pins the two states TopBar can render rather
 * than asserting the control stays dead, and full panel coverage lives in
 * `ui/__tests__/settings-panel.test.tsx`.
 *
 * TWO-TRACK: the league selector must say which of the two tracks a league
 * is on (Westwood, the one real primary league, vs. every other league,
 * generic) before the user switches to it, and StrategyGuide's old single
 * "Not available for this league" string must split by track rather than
 * conflating "generic, and will not be" with "not yet run."
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

describe('INERT-CONTROLS: Export CSV / Export PDF (Board.tsx)', () => {
  it('renders no Export CSV or Export PDF button, and states the fact in the provenance line', () => {
    render(<Board data={data} rows={rows} league={league} />);
    expect(screen.queryByRole('button', { name: /export csv/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /export pdf/i })).not.toBeInTheDocument();
    expect(screen.getByText(/export not built/)).toBeInTheDocument();
  });
});

describe('INERT-CONTROLS: Compare / Ask (PlayerDetail.tsx)', () => {
  it('opens the detail sheet with neither a Compare nor an Ask button', async () => {
    render(<Board data={data} rows={rows} league={league} />);
    const first = rows[0]!;
    const name = first.name.kind === 'present' ? first.name.value : '';
    await userEvent.click(screen.getAllByText(name)[0]!);

    expect(screen.getByText('WHY OUR RANK DIFFERS FROM THE MARKET')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^compare$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^ask$/i })).not.toBeInTheDocument();
    // The real, working actions in the same row must still be there -- this is
    // "the row shrinks," not "the row is gone."
    expect(screen.getByRole('button', { name: /watchlist/i })).toBeInTheDocument();
  });
});

describe('INERT-CONTROLS: Ask the assistant per glossary term (Glossary.tsx)', () => {
  it('renders no per-term Ask the assistant button anywhere in the glossary', () => {
    render(<Glossary data={data} />);
    expect(screen.queryByRole('button', { name: /ask the assistant/i })).not.toBeInTheDocument();
    expect(screen.queryAllByText(/ask the assistant/i)).toHaveLength(0);
  });
});

describe('League settings (TopBar.tsx) -- built FR-069/FR-040, previously inert', () => {
  /**
   * Was "INERT-CONTROLS: renders no League settings button -- only a plain
   * not-built statement." That premise no longer holds: FR-069/FR-040
   * (`docs/design/LEAGUE-SETTINGS-BOUNDARY.md`) built a real Settings panel
   * this session -- see `ui/__tests__/settings-panel.test.tsx` for its full
   * coverage. This block now pins the two states TopBar itself can be in,
   * rather than asserting the control is dead, which would be false.
   */
  function renderTopBar(leagues: SelectableLeague[], withSlotHandlers: boolean) {
    render(
      <TopBar
        mode="prep"
        onModeChange={() => {}}
        theme="dark"
        onToggleTheme={() => {}}
        league={league}
        leagues={leagues}
        leagueId="default"
        onSelectLeague={() => {}}
        onSelectSlot={withSlotHandlers ? () => {} : undefined}
        onClearSlot={withSlotHandlers ? () => {} : undefined}
      />,
    );
  }

  it('renders a real, clickable Settings button when slot-override handlers are wired (the live app)', () => {
    renderTopBar([{ id: 'default', label: 'Westwood' }], true);
    expect(screen.getByRole('button', { name: 'Settings' })).toBeInTheDocument();
    expect(screen.queryByText(/settings.*not built/i)).not.toBeInTheDocument();
  });

  it('renders an honest, still-not-a-dead-button fallback when they are not (e.g. the standalone build)', () => {
    renderTopBar([{ id: 'default', label: 'Westwood' }], false);
    expect(screen.queryByRole('button', { name: 'Settings' })).not.toBeInTheDocument();
    expect(screen.getByText(/settings.*not available in this build/i)).toBeInTheDocument();
  });
});

describe('TWO-TRACK: the league selector carries the track', () => {
  it('reads the real primary league as primary track, with a real opponents-modelled count', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('data/_leagues.json')) {
          return new Response(
            JSON.stringify({
              leagues: [],
              primary: {
                id: 'default',
                label: 'Westwood',
                track: { isPrimary: true, scoringRulesetNote: "Westwood's verified custom ruleset...", opponentsModelledCount: 9 },
              },
            }),
            { status: 200, headers: { 'content-type': 'application/json' } },
          );
        }
        return new Response('not found', { status: 404 });
      }),
    );

    const leagues = await fetchSelectableLeagues();
    expect(leagues).toEqual([
      {
        id: 'default',
        label: 'Westwood',
        track: { isPrimary: true, scoringRulesetNote: "Westwood's verified custom ruleset...", opponentsModelledCount: 9 },
      },
    ]);

    render(
      <TopBar
        mode="prep"
        onModeChange={() => {}}
        theme="dark"
        onToggleTheme={() => {}}
        league={league}
        leagues={leagues}
        leagueId="default"
        onSelectLeague={() => {}}
      />,
    );
    // Visible text is a short label (the top bar is already tight -- see the
    // module doc on trackFullDescriptor); the full sentence design's mockup
    // shows lives in the title, not gone.
    const badge = screen.getByTestId('league-track');
    expect(badge.textContent).toBe('PRIMARY');
    expect(badge.title).toContain('primary track');
    expect(badge.title).toContain('9 opponents modelled');

    vi.unstubAllGlobals();
  });

  it('reads a generic-track league as such, with no opponents-modelled count claimed', () => {
    const leagues: SelectableLeague[] = [
      {
        id: 'default',
        label: 'Westwood',
        track: { isPrimary: true, scoringRulesetNote: null, opponentsModelledCount: 9 },
      },
      {
        id: 'espn_10_half',
        label: 'ESPN-default, 10 teams, half scoring',
        track: { isPrimary: false, scoringRulesetNote: 'STANDARD ruleset (FR-042)...', opponentsModelledCount: null },
      },
    ];
    render(
      <TopBar
        mode="prep"
        onModeChange={() => {}}
        theme="dark"
        onToggleTheme={() => {}}
        league={league}
        leagues={leagues}
        leagueId="espn_10_half"
        onSelectLeague={() => {}}
      />,
    );
    const badge = screen.getByTestId('league-track');
    expect(badge.textContent).toBe('GENERIC');
    expect(badge.title).toContain('generic track');
    expect(badge.title).toContain('opponents not modelled');
  });

  it('renders no track badge at all when the manifest predates the field (standalone build, older export)', () => {
    render(
      <TopBar
        mode="prep"
        onModeChange={() => {}}
        theme="dark"
        onToggleTheme={() => {}}
        league={league}
        leagues={[{ id: 'default', label: 'Default league' }]}
        leagueId="default"
        onSelectLeague={() => {}}
      />,
    );
    expect(screen.queryByTestId('league-track')).not.toBeInTheDocument();
  });
});

describe('TWO-TRACK: StrategyGuide splits the old single empty-state string by track', () => {
  it('names the generic track plainly for a non-primary league with no strategies.json', () => {
    const genericData = { ...data, strategies: null, league: { ...data.league, league_id: 'espn_10_half' } };
    render(<StrategyGuide data={genericData} />);
    expect(screen.getByText(/Generic track/)).toBeInTheDocument();
    expect(screen.queryByText(/^Not available for this league\.$/)).not.toBeInTheDocument();
  });

  it('does not claim "generic track" for the primary league even if strategies.json were somehow missing', () => {
    const primaryNullData = { ...data, strategies: null, league: { ...data.league, league_id: 'primary' } };
    render(<StrategyGuide data={primaryNullData} />);
    expect(screen.queryByText(/Generic track/)).not.toBeInTheDocument();
    expect(screen.getByText(/Not available\./)).toBeInTheDocument();
  });

  it('renders the real strategies when present, for the real primary league (unchanged behaviour)', () => {
    render(<StrategyGuide data={data} />);
    expect(screen.queryByText(/Generic track/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Not available/)).not.toBeInTheDocument();
    expect(screen.getByText('Strategy guide')).toBeInTheDocument();
  });
});
