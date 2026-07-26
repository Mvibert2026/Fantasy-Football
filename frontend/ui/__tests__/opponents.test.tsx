import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Opponents } from '../views/Opponents';
import { loadDatasetFromDisk } from './helpers';

/**
 * Opponents used to be an explicit "not built" placeholder. Now it reads
 * opponents.json directly and must show the real 7-of-9-no-data coverage
 * honestly, not silently drop the caveat now that there's real content on screen.
 *
 * Real opponents.json has team_name: null for 7 of 9 records, and several
 * opponents share an identical data_status string verbatim -- both are real
 * properties of this data (how little is actually known), not test fixtures, so
 * these assertions count occurrences rather than assuming uniqueness.
 */

const data = loadDatasetFromDisk();

describe('Opponents', () => {
  it('renders the real coverage warning and one card per real opponent', () => {
    render(<Opponents data={data} />);
    expect(screen.getByText(data.opponents.coverage_warning)).toBeInTheDocument();

    const named = data.opponents.opponents.filter((o) => o.team_name !== null);
    for (const opp of named) {
      expect(screen.getByText(opp.team_name!)).toBeInTheDocument();
    }
    const unnamedCount = data.opponents.opponents.length - named.length;
    if (unnamedCount > 0) {
      expect(screen.getAllByText(/no team name supplied/i)).toHaveLength(unnamedCount);
    }
  });

  it('marks contextual fields NOT A MODEL INPUT exactly where any are present, never more or fewer', () => {
    render(<Opponents data={data} />);
    const withContext = data.opponents.opponents.filter(
      (o) => o.positional_tendencies || o.first_pick_by_position || o.consensus_tracking_behaviour,
    );
    // Real opponents.json today has none of the three populated for any
    // opponent -- this counts occurrences either way rather than assuming a
    // fixture shape the real export doesn't currently have.
    const labels = screen.queryAllByText(/NOT A MODEL INPUT/i);
    expect(labels.length).toBe(withContext.length);
  });

  it('shows the real data_status for every opponent, counting duplicates rather than assuming uniqueness', () => {
    render(<Opponents data={data} />);
    const counts = new Map<string, number>();
    for (const opp of data.opponents.opponents) {
      counts.set(opp.data_status, (counts.get(opp.data_status) ?? 0) + 1);
    }
    for (const [status, count] of counts) {
      expect(screen.getAllByText(status)).toHaveLength(count);
    }
  });

  /**
   * rosters.json (contract 1.8.0, docs/handoffs/016) wired in as part of the
   * 2026-07 frontend spec audit -- previously unreachable because sync-exports.mjs
   * read a stale shadow copy of data/export/ (docs/frontend-audit-2026-07.md).
   * `data.rosters` is real for this league today; the real export currently has
   * no 2026 draft logged, so every team's roster is empty and every starter slot
   * is a full need -- that's the honest state under test, not a fixture.
   */
  it('renders roster slots and STILL NEEDS chips from rosters.json when the artifact is present', () => {
    expect(data.rosters).not.toBeNull();
    render(<Opponents data={data} />);

    const rostersBySlot = new Map(data.rosters!.rosters.map((r) => [r.team_slot, r]));
    for (const opp of data.opponents.opponents) {
      const roster = rostersBySlot.get(opp.draft_slot_2026);
      if (!roster) continue;
      for (const [pos, n] of Object.entries(roster.needs)) {
        if (['QB', 'RB', 'WR', 'TE', 'DEF'].includes(pos) && n > 0) {
          expect(screen.getAllByText(`${pos} ×${n}`).length).toBeGreaterThan(0);
        }
      }
    }
  });

  it('states plainly that roster data is unavailable when a league has no rosters.json', () => {
    const withoutRosters = { ...data, rosters: null };
    render(<Opponents data={withoutRosters} />);
    expect(screen.getAllByText(/roster data not available for this league/i).length).toBe(
      data.opponents.opponents.length,
    );
  });
});
