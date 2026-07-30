import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows, type BoardRow } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-075: `PlayerDetail.tsx` used to render "Not computed: archetype. No
 * backend field in this build" for every player, unconditionally -- a
 * wrong-not-absent claim (`docs/ranking/archetypes-proposal.md` SS0), since
 * `player_descriptions.json` carries a real per-player `archetype` field the
 * app already loads. These tests pin the four real on-screen states against
 * the actual committed export, not a hand-written fixture, so a future
 * regeneration of `player_descriptions.json` can't silently make this
 * degenerate back to one string for everyone.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);

if (!data.playerDescriptions) {
  throw new Error('Fixture assumption broken: primary export has no player_descriptions.json.');
}
const pdIds = new Set(data.playerDescriptions.players.map((p) => p.player_id));

const labelledRow = rows.find(
  (r) => r.raw.player_id_gsis && pdIds.has(r.raw.player_id_gsis) && ['RB', 'WR', 'TE'].includes(r.raw.position),
);
const unclassifiedRow = rows.find(
  (r) => r.raw.player_id_gsis && !pdIds.has(r.raw.player_id_gsis) && ['RB', 'WR', 'TE'].includes(r.raw.position),
);
const qbRow = rows.find((r) => r.raw.position === 'QB');

if (!labelledRow || !unclassifiedRow || !qbRow) {
  throw new Error('Fixture assumption broken: expected a labelled RB/WR/TE, an unclassified one, and a QB.');
}

function renderDetail(row: BoardRow, dataset: Dataset = data) {
  return render(
    <PlayerDetail
      row={row}
      rows={rows}
      data={dataset}
      league={league}
      picks={[]}
      watchlist={[]}
      onToggleWatch={() => {}}
      onClose={() => {}}
    />,
  );
}

describe('PlayerDetail archetype (FR-075)', () => {
  it('never renders the old blanket "not computed: archetype" false claim, for any player', () => {
    // Section 9 (bullet takeaways) is a genuinely separate, still-permanent
    // absence and legitimately keeps similar wording ("Not computed:
    // takeaways...") -- scope this to the archetype claim specifically so
    // that real, unrelated state doesn't make this assertion meaningless.
    for (const row of [labelledRow, unclassifiedRow, qbRow]) {
      const { unmount } = renderDetail(row);
      expect(document.body.textContent).not.toContain('Not computed: archetype');
      expect(document.body.textContent).not.toContain('permanently absent, no field in any export, ever');
      unmount();
    }
  });

  it('shows the real label, confidence and description for a classified RB/WR/TE', () => {
    const entry = data.playerDescriptions!.players.find((p) => p.player_id === labelledRow.raw.player_id_gsis)!;
    const { getByText, getAllByTitle } = renderDetail(labelledRow);
    // The chip strips the position prefix (see archetypeLabel) -- assert the
    // sourced field is reachable via the title attribute rather than
    // reconstructing the exact label text here. Rendered twice on purpose
    // (identity-strip chip + section 6), so both must carry it.
    const titled = getAllByTitle(new RegExp(`archetype = "${entry.archetype}"`));
    expect(titled.length).toBe(2);
    expect(getByText(new RegExp(`confidence: ${entry.confidence}`))).toBeTruthy();
    expect(getByText(entry.description)).toBeTruthy();
  });

  it('shows an honest UNCLASSIFIED state for a covered position with no matching row', () => {
    const { getAllByText } = renderDetail(unclassifiedRow);
    expect(getAllByText('UNCLASSIFIED').length).toBeGreaterThan(0);
  });

  it('shows a not-modelled state for QB, distinct from unclassified', () => {
    const { getAllByText } = renderDetail(qbRow);
    expect(getAllByText('ARCHETYPE N/A').length).toBeGreaterThan(0);
  });

  it('shows a not-available state when this league has no player_descriptions.json at all', () => {
    const noDescriptions: Dataset = { ...data, playerDescriptions: null };
    const { getAllByText } = renderDetail(labelledRow, noDescriptions);
    expect(getAllByText('ARCHETYPE —').length).toBeGreaterThan(0);
  });
});
