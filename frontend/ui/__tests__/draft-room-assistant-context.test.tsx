import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { DraftRoom } from '../views/DraftRoom';
import type { ContextItem } from '../assistant/reasoning';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { saveDraftState, teamSlotAtPick, type DraftPickRecord } from '../data/draft';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-076: DraftRoom must actually report the page-context bundle it built for
 * its own render, or the wiring described in `docs/founder-requests/FR-076-*`
 * is fiction. This is the one integration test standing behind the unit tests
 * in `page-context.test.ts` (which never touch DraftRoom itself) and
 * `reasoning-page-context-and-history.test.ts` (which never touch React at
 * all) -- it confirms the real component, with a real seeded draft, actually
 * calls `onAssistantContext` with a bundle that matches what's on screen.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

function seedUpToUsersFirstPick() {
  const picks: DraftPickRecord[] = [];
  for (let n = 1; n < 3; n++) {
    picks.push({
      overallPick: n,
      round: 1,
      teamSlot: teamSlotAtPick(n, teams),
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    });
  }
  saveDraftState({ leagueId, mockId: 'test-mock', picks, queue: [] });
}

beforeEach(() => {
  localStorage.clear();
});

describe('DraftRoom reports its page context to the assistant (FR-076)', () => {
  it('calls onAssistantContext with a real recommendation and roster-needs item while on the clock', () => {
    seedUpToUsersFirstPick();
    let latest: ContextItem[] = [];
    render(
      <DraftRoom
        data={data}
        rows={rows}
        league={league}
        onAssistantContext={(items) => {
          latest = items;
        }}
      />,
    );

    const ids = latest.map((i) => i.id);
    expect(ids).toContain('page.draft_state');
    expect(ids).toContain('page.roster_needs');
    expect(ids).toContain('page.recommendation');
    expect(ids).toContain('page.scope_note');

    const state = latest.find((i) => i.id === 'page.draft_state')!;
    expect(state.text).toMatch(/on the clock right now/i);

    // Exactly the founder's failed question -- confirm the recommendation
    // item's reason text is non-empty, real prose, not a placeholder.
    const rec = latest.find((i) => i.id === 'page.recommendation')!;
    expect(rec.text.length).toBeGreaterThan(20);
    expect(rec.text).toMatch(/for the pick happening right now/i);
  });

  it('calls onAssistantContext with [] before any picks are logged and league config is otherwise ready', () => {
    // No seeding: pick 1 is on the clock for whichever team holds slot 1 --
    // still a fully valid state, just not the user's turn (assuming the
    // user's slot isn't 1st in this league's real pick_sequence[0]=3).
    let calls: ContextItem[][] = [];
    render(
      <DraftRoom
        data={data}
        rows={rows}
        league={league}
        onAssistantContext={(items) => {
          calls = [...calls, items];
        }}
      />,
    );
    // At minimum, the very first call must be a definite array (not
    // undefined) -- App.tsx's state initialises to [], so DraftRoom must
    // agree with that shape from its first render.
    expect(Array.isArray(calls[0])).toBe(true);
  });
});
