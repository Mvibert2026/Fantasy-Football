import { render, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows, type BoardRow } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { loadDatasetFromDisk, withTraceOn } from './helpers';

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

function renderDetailWithSourcesShown(row: BoardRow, dataset: Dataset = data) {
  return render(
    withTraceOn(
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
    ),
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
    const { getByText, getAllByTitle, queryAllByTitle } = renderDetail(labelledRow);
    // FR-114: the sourced field path itself is behind the "show data sources"
    // switch, default off -- this default-state render must NOT carry the
    // `player_descriptions.json:...` path, only the plain-English archetype
    // value. Confidence and description are meaning, not sourcing, and stay.
    expect(queryAllByTitle(/player_descriptions\.json:/).length).toBe(0);
    const titled = getAllByTitle(new RegExp(`Archetype: "${entry.archetype}"`));
    expect(titled.length).toBe(2);
    expect(getByText(new RegExp(`confidence: ${entry.confidence}`))).toBeTruthy();
    expect(getByText(entry.description)).toBeTruthy();
  });

  it('shows the field path once the switch is on, same two places', () => {
    const entry = data.playerDescriptions!.players.find((p) => p.player_id === labelledRow.raw.player_id_gsis)!;
    const { getAllByTitle } = renderDetailWithSourcesShown(labelledRow);
    // Rendered twice on purpose (identity-strip chip + section 6), so both
    // must carry it once the switch is on.
    const titled = getAllByTitle(new RegExp(`player_descriptions\\.json:players\\[\\]\\.archetype = "${entry.archetype}"`));
    expect(titled.length).toBe(2);
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

/**
 * Design round-1 item 2 (thread 121): the archetype chip's placement is
 * dual-built behind `ui/data/archetypePlacement.ts` until the founder rules
 * between FR-075's own placement request (identity strip, Arrangement A --
 * DEFAULT) and design's disclosed-section amendment (Arrangement B). These
 * tests pin both arrangements from the same build, and separately pin that
 * the three absence states render visibly differently from each other --
 * design's actual finding was that three identically-grey chips read as one
 * claim, not three -- not just with different text.
 */
describe('PlayerDetail archetype chip placement (thread 121 scaffolding)', () => {
  const noDescriptions: Dataset = { ...data, playerDescriptions: null };

  beforeEach(() => {
    localStorage.removeItem('prep.archetypePlacement');
    window.history.pushState(null, '', '/');
  });
  afterEach(() => {
    localStorage.removeItem('prep.archetypePlacement');
    window.history.pushState(null, '', '/');
  });

  function setPlacement(placement: 'identity-strip' | 'disclosed') {
    window.history.pushState(null, '', `/?archetypePlacement=${placement}`);
  }

  it('Arrangement A (default, untouched flag): shows the chip in the identity strip for a real label', () => {
    const { getByTestId } = renderDetail(labelledRow);
    const strip = getByTestId('player-detail-identity-strip');
    expect(within(strip).getAllByTitle(/Archetype: "/).length).toBe(1);
  });

  it.each([
    ['unclassified', () => unclassifiedRow, 'UNCLASSIFIED'],
    ['not-applicable (QB)', () => qbRow, 'ARCHETYPE N/A'],
    ['not-available (no export)', () => labelledRow, 'ARCHETYPE —'],
  ] as const)('Arrangement A (default): the %s absence state still renders in the identity strip', (kind, getRow, text) => {
    setPlacement('identity-strip');
    const row = getRow();
    const dataset = kind === 'not-available (no export)' ? noDescriptions : data;
    const { getByTestId } = renderDetail(row, dataset);
    const strip = getByTestId('player-detail-identity-strip');
    expect(within(strip).getAllByText(text).length).toBe(1);
  });

  it.each([
    ['unclassified', () => unclassifiedRow, 'UNCLASSIFIED'],
    ['not-applicable (QB)', () => qbRow, 'ARCHETYPE N/A'],
    ['not-available (no export)', () => labelledRow, 'ARCHETYPE —'],
  ] as const)('Arrangement B (disclosed): the %s absence state is REMOVED from the identity strip', (kind, getRow, text) => {
    setPlacement('disclosed');
    const row = getRow();
    const dataset = kind === 'not-available (no export)' ? noDescriptions : data;
    const { getByTestId, getAllByText } = renderDetail(row, dataset);
    const strip = getByTestId('player-detail-identity-strip');
    expect(within(strip).queryByText(text)).toBeNull();
    // But it is not gone -- it still renders once, in the disclosed ARCHETYPE section.
    expect(getAllByText(text).length).toBe(1);
  });

  it('Arrangement B (disclosed) still shows a real label in the identity strip -- the rule is "absence moves," not "chip moves"', () => {
    setPlacement('disclosed');
    const { getByTestId } = renderDetail(labelledRow);
    const strip = getByTestId('player-detail-identity-strip');
    expect(within(strip).getAllByTitle(/Archetype: "/).length).toBe(1);
  });

  it('the three absence states render with three different border treatments, not one shared "muted" look', () => {
    // 'disclosed' so each absence state renders exactly once (in the
    // disclosed section only) -- avoids the identity-strip's duplicate
    // rendering of the same chip, which would make a plain getByText ambiguous.
    setPlacement('disclosed');
    const { getByText: getByTextUnclassified, unmount: u1 } = renderDetail(unclassifiedRow);
    const unclassifiedStyle = getByTextUnclassified('UNCLASSIFIED').style.borderStyle;
    u1();

    const { getByText: getByTextNA, unmount: u2 } = renderDetail(qbRow);
    const naStyle = getByTextNA('ARCHETYPE N/A').style.borderStyle;
    u2();

    const { getByText: getByTextMissing, unmount: u3 } = renderDetail(labelledRow, noDescriptions);
    const missingStyle = getByTextMissing('ARCHETYPE —').style.borderStyle;
    u3();

    // Each of the three must differ from each other -- three-way pairwise distinct.
    expect(unclassifiedStyle).not.toBe(naStyle);
    expect(unclassifiedStyle).not.toBe(missingStyle);
    expect(naStyle).not.toBe(missingStyle);
    // And none of them borrows the real-label chip's solid-filled look.
    expect(unclassifiedStyle).toBe('dashed');
    expect(missingStyle).toBe('dotted');
  });

  it('a real label keeps its solid, filled chip regardless of placement', () => {
    setPlacement('disclosed');
    const { getAllByTitle } = renderDetail(labelledRow);
    const entry = data.playerDescriptions!.players.find((p) => p.player_id === labelledRow.raw.player_id_gsis)!;
    const chip = getAllByTitle(new RegExp(`Archetype: "${entry.archetype}"`))[0]!;
    expect(chip.style.borderStyle).toBe('solid');
  });
});
