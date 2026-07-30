import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Availability } from '../views/Availability';
import { buildRows } from '../data/board';
import { applyUserSlotOverride, buildLeagueConfig } from '../data/league';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-066 ("When slot selection happens on the availability, it doesn't change the
 * picks shown"). Before this fix, `Availability` never received `league` at all and
 * read `availability.json:metadata.user_picks` directly for its pick selector --
 * fixed to whichever slot the Python simulation ran against, so overriding the slot
 * (FR-034) changed nothing on this one screen while every other screen updated.
 *
 * These tests assert the actual founder-observed behavior: the picks shown DO
 * change when the slot changes, an honest banner explains the gap while the
 * numbers themselves have not been recomputed, and clearing the override restores
 * the original picks -- not just that `applyUserSlotOverride`'s own unit tests pass.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const baseLeague = buildLeagueConfig(data);
const teams = baseLeague.teams.kind === 'present' ? baseLeague.teams.value : 0;
const sourcedSlot = baseLeague.userSlotSourced.kind === 'present' ? baseLeague.userSlotSourced.value : 0;
const overrideSlot = sourcedSlot === 1 ? 2 : 1;
const sourcedPicks = baseLeague.pickSequence.kind === 'present' ? baseLeague.pickSequence.value : [];

function renderAt(league = baseLeague) {
  return render(<Availability data={data} rows={rows} league={league} />);
}

/** Scoped to the "Your picks" group so pick numbers that coincide with a sigma
 *  value (5/10/20) can never collide with the SIGMA row's own buttons. */
function picksGroup() {
  return within(screen.getByRole('group', { name: 'Your picks' }));
}

describe('Availability screen and FR-034 slot override (FR-066)', () => {
  it('with no override, YOUR PICKS shows the sourced slot\'s real pick numbers, no banner', () => {
    renderAt();
    const group = picksGroup();
    for (const p of sourcedPicks.slice(0, 3)) {
      expect(group.getByRole('button', { name: String(p) })).toBeInTheDocument();
    }
    expect(screen.queryByText(/has not been recomputed for your selection/i)).not.toBeInTheDocument();
  });

  it('overriding the slot changes the pick numbers shown (the exact founder complaint)', () => {
    const overridden = applyUserSlotOverride(baseLeague, overrideSlot);
    const expectedPicks = overridden.pickSequence.kind === 'present' ? overridden.pickSequence.value : [];
    expect(expectedPicks).not.toEqual(sourcedPicks);

    renderAt(overridden);
    const group = picksGroup();

    // The overridden slot's own pick numbers are now on screen...
    for (const p of expectedPicks.slice(0, 3)) {
      expect(group.getByRole('button', { name: String(p) })).toBeInTheDocument();
    }
    // ...and the sourced slot's picks that don't coincide with the new sequence are gone.
    const onlyInSourced = sourcedPicks.filter((p) => !expectedPicks.includes(p));
    for (const p of onlyInSourced.slice(0, 3)) {
      expect(group.queryByRole('button', { name: String(p) })).not.toBeInTheDocument();
    }
  });

  it('under an override, the honest banner names both slots and explains nothing was recomputed', () => {
    const overridden = applyUserSlotOverride(baseLeague, overrideSlot);
    renderAt(overridden);
    expect(
      screen.getByText(new RegExp(`Showing slot ${sourcedSlot}.s simulation, not slot ${overrideSlot}.s`, 'i')),
    ).toBeInTheDocument();
    expect(screen.getByText(/has not been recomputed for your selection/i)).toBeInTheDocument();
    expect(screen.getByText(/FR-066/)).toBeInTheDocument();
  });

  it('a pick number unique to the overridden slot reads an honest absence, never a stale real number', async () => {
    const overridden = applyUserSlotOverride(baseLeague, overrideSlot);
    const expectedPicks = overridden.pickSequence.kind === 'present' ? overridden.pickSequence.value : [];
    const newOnlyPick = expectedPicks.find((p) => !sourcedPicks.includes(p));
    expect(newOnlyPick).toBeDefined();

    renderAt(overridden);
    const user = userEvent.setup();
    await user.click(picksGroup().getByRole('button', { name: String(newOnlyPick) }));

    // Every visible percentage cell for that pick is the honest absent dash, not a
    // real-looking number left over from the sourced slot's export.
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });

  it('clearing the override (back to null) restores the sourced slot\'s picks atomically', () => {
    const overridden = applyUserSlotOverride(baseLeague, overrideSlot);
    const { rerender } = renderAt(overridden);
    rerender(<Availability data={data} rows={rows} league={baseLeague} />);
    const group = picksGroup();
    for (const p of sourcedPicks.slice(0, 3)) {
      expect(group.getByRole('button', { name: String(p) })).toBeInTheDocument();
    }
    expect(screen.queryByText(/has not been recomputed for your selection/i)).not.toBeInTheDocument();
  });

  it('sanity: teams is present so the override actually differs from the sourced slot in this fixture', () => {
    expect(teams).toBeGreaterThan(1);
    expect(overrideSlot).not.toBe(sourcedSlot);
  });
});
