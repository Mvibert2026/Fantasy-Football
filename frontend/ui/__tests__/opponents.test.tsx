import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { pickNumbersForSlot } from '../data/draft';
import { loadOpponentNames } from '../data/opponentNames';
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

/** The card's outer container for one opponent, found by walking up from its
 *  header name node -- name span -> header row div -> card div. Shared by the
 *  ordering and next-pick tests below so each asserts against one real card
 *  rather than the whole grid's concatenated text. */
function cardFor(opp: (typeof data.opponents.opponents)[number]): HTMLElement {
  const label = opp.team_name ?? `Slot ${opp.draft_slot_2026} (no team name supplied)`;
  const nameNode = screen.getByText(label);
  const card = nameNode.parentElement?.parentElement;
  if (!card) throw new Error(`could not find card container for ${label}`);
  return card;
}

describe('Opponents', () => {
  it('renders the screen heading -- proving the tab exists and is reachable, not a routed-to blank pane', () => {
    render(<Opponents data={data} />);
    expect(screen.getByRole('heading', { name: 'Opponents' })).toBeInTheDocument();
  });

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
    // No rosters.json means the next-pick figure has no input to compute from --
    // the header must render nothing there, never a stale or fabricated number.
    expect(screen.queryAllByText(/^next$/).length).toBe(0);
  });

  /**
   * `next #N` (02-draft-opponents.md's card anatomy, thread 027) is pure
   * snake-order arithmetic -- rosters.json:picks_ingested plus
   * league.json:teams/rounds and the opponent's own draft_slot_2026, run
   * through the same pickNumbersForSlot helper DraftRoom/PlayerDetail use for
   * the user's own next pick. Computed here from the real export, not a
   * hand-picked literal, so this breaks the moment the arithmetic drifts from
   * what ui/data/draft.ts actually does, not from a stale fixture number.
   */
  it("shows each opponent's real next pick, computed from rosters.json:picks_ingested and league.json:teams/rounds", () => {
    expect(data.rosters).not.toBeNull();
    render(<Opponents data={data} />);

    const current = data.rosters!.picks_ingested + 1;
    for (const opp of data.opponents.opponents) {
      const expected = pickNumbersForSlot(data.league.teams, opp.draft_slot_2026, data.league.rounds).find(
        (p) => p >= current,
      );
      const card = cardFor(opp);
      if (expected === undefined) {
        expect(within(card).getByText('—')).toBeInTheDocument();
      } else {
        expect(within(card).getByText(`#${expected}`)).toBeInTheDocument();
      }
    }
  });

  it('renders "next —" (not a number, not a blank) when rosters.json says a team has no picks left in the league\'s round count', () => {
    expect(data.rosters).not.toBeNull();
    // Force the "fully drafted for this slot" state: one round total, and every
    // team's single pick already ingested -- picks_ingested equal to the team
    // count means round 1 is over and there is no round 2 to look for.
    const doneDrafting = {
      ...data,
      league: { ...data.league, rounds: 1 },
      rosters: { ...data.rosters!, picks_ingested: data.league.teams },
    };
    render(<Opponents data={doneDrafting} />);
    for (const opp of data.opponents.opponents) {
      expect(within(cardFor(opp)).getByText('—')).toBeInTheDocument();
    }
  });

  it("orders each card's roster rows QB, RB, WR, TE, FLEX, DEF -- FLEX before DEF, per the spec's slot order", () => {
    render(<Opponents data={data} />);
    const firstOpp = data.opponents.opponents[0]!;
    const card = cardFor(firstOpp);
    const labels = within(card)
      .getAllByText(/^(QB|RB|WR|TE|FLEX|DEF)$/)
      .map((el) => el.textContent);
    expect(labels).toEqual(['QB', 'RB', 'WR', 'TE', 'FLEX', 'DEF']);
  });

  describe('FR-036: manually-typed opponent team names', () => {
    const leagueId = data.league.league_id ?? 'default';

    beforeEach(() => {
      localStorage.clear();
    });

    it('typing a name for a slot with no sourced team_name replaces the "no team name supplied" placeholder', async () => {
      render(<Opponents data={data} />);
      const unnamed = data.opponents.opponents.find((o) => o.team_name === null);
      if (!unnamed) throw new Error('fixture guard: expected at least one unnamed opponent');
      const card = cardFor(unnamed);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      const input = within(card).getByRole('textbox', { name: /team name for slot/i });
      await userEvent.type(input, 'The Testers{Enter}');

      expect(within(card).getByText('The Testers')).toBeInTheDocument();
      expect(within(card).queryByText(/no team name supplied/i)).not.toBeInTheDocument();
      expect(within(card).getByText('typed')).toBeInTheDocument();
    });

    it('SUPPLIED-VALUES.md: marks the typed name with a dotted underline and a lowercase marker, never the --acc delta colour', async () => {
      render(<Opponents data={data} />);
      const unnamed = data.opponents.opponents.find((o) => o.team_name === null);
      if (!unnamed) throw new Error('fixture guard: expected at least one unnamed opponent');
      const card = cardFor(unnamed);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      await userEvent.type(within(card).getByRole('textbox', { name: /team name for slot/i }), 'The Testers{Enter}');

      const nameEl = within(card).getByText('The Testers');
      // Green already means "good, positive, better than baseline" (the
      // board's delta colour) -- a typed name is not that, so it must never
      // borrow the accent, on the name or on the marker beside it. Reading
      // `.style` directly rather than jest-dom's `toHaveStyle` (its CSS
      // parser did not match this shorthand reliably against a raw `var()`
      // value in this environment).
      expect(nameEl.style.color).not.toBe('var(--acc)');
      expect(nameEl.style.borderBottom).toBe('1px dotted var(--line2)');
      const marker = within(card).getByText('typed');
      expect(marker.style.color).not.toBe('var(--acc)');
      expect(marker.style.border).not.toContain('var(--acc)');
    });

    it('a typed name overrides a real sourced name, and marks itself TYPED -- never presented as the same kind of value', async () => {
      const named = data.opponents.opponents.find((o) => o.team_name !== null);
      if (!named) throw new Error('fixture guard: expected at least one named opponent');
      render(<Opponents data={data} />);
      const card = cardFor(named);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      const input = within(card).getByRole('textbox', { name: /team name for slot/i });
      await userEvent.clear(input);
      await userEvent.type(input, 'Renamed Locally{Enter}');

      expect(within(card).getByText('Renamed Locally')).toBeInTheDocument();
      expect(within(card).queryByText(named.team_name!)).not.toBeInTheDocument();
      expect(within(card).getByText('typed')).toBeInTheDocument();
    });

    it('persists the typed name to per-league storage, matching the shape of the draft-state store', async () => {
      const unnamed = data.opponents.opponents.find((o) => o.team_name === null);
      if (!unnamed) throw new Error('fixture guard: expected at least one unnamed opponent');
      render(<Opponents data={data} />);
      const card = cardFor(unnamed);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      const input = within(card).getByRole('textbox', { name: /team name for slot/i });
      await userEvent.type(input, 'Stored Name{Enter}');

      expect(loadOpponentNames(leagueId)[unnamed.draft_slot_2026]).toBe('Stored Name');
    });

    it('clearing a typed override falls back to the real sourced name, not blank', async () => {
      const named = data.opponents.opponents.find((o) => o.team_name !== null);
      if (!named) throw new Error('fixture guard: expected at least one named opponent');
      render(<Opponents data={data} />);
      const card = cardFor(named);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      const input1 = within(card).getByRole('textbox', { name: /team name for slot/i });
      await userEvent.clear(input1); // starts prefilled with the sourced name -- must replace, not append
      await userEvent.type(input1, 'Temp Override{Enter}');
      expect(within(card).getByText('Temp Override')).toBeInTheDocument();

      await userEvent.click(within(card).getByRole('button', { name: /clear typed team name/i }));

      expect(within(card).getByText(named.team_name!)).toBeInTheDocument();
      expect(within(card).queryByText('Temp Override')).not.toBeInTheDocument();
      expect(within(card).queryByText('typed')).not.toBeInTheDocument();
    });

    it('clearing a typed override for a slot with no sourced name falls back to the honest "no team name supplied" placeholder, not blank', async () => {
      const unnamed = data.opponents.opponents.find((o) => o.team_name === null);
      if (!unnamed) throw new Error('fixture guard: expected at least one unnamed opponent');
      render(<Opponents data={data} />);
      const card = cardFor(unnamed);

      await userEvent.click(within(card).getByRole('button', { name: /edit team name/i }));
      await userEvent.type(within(card).getByRole('textbox', { name: /team name for slot/i }), 'Temp Override{Enter}');
      await userEvent.click(within(card).getByRole('button', { name: /clear typed team name/i }));

      expect(within(card).getByText(/no team name supplied/i)).toBeInTheDocument();
    });

    it('does not carry a typed name over from a different league\'s storage', () => {
      // A name typed under a different league key must never surface here --
      // exactly the leak FR-036 explicitly rules out.
      localStorage.setItem(`prep.opponentNames.some-other-league`, JSON.stringify({ 1: 'Wrong League Name' }));
      render(<Opponents data={data} />);
      expect(screen.queryByText('Wrong League Name')).not.toBeInTheDocument();
    });
  });
});
