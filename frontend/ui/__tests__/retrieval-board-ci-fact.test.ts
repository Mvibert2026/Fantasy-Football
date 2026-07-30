import { describe, expect, it } from 'vitest';
import { buildCorpus } from '../assistant/retrieval';
import { buildRows } from '../data/board';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { loadDatasetFromDisk } from './helpers';

/**
 * Founder, 2026-07-30: he asked the assistant why the range shown next to a
 * player's projection didn't contain the projection, and it had nothing to
 * say -- the board doc handed to the reasoning lane never mentioned the
 * interval at all, so it saw the same two numbers he did with no fact to
 * reconcile them. `boardDocs()` (`ui/assistant/retrieval.ts`) now states
 * `ci_applies_to` explicitly, per row, using `ciTargetFor` rather than
 * assuming "vbd" -- these tests check the fact actually lands in the
 * document text the reasoning lane receives, for all three cases: known
 * ("vbd"), known-but-different ("projected_points"), and unrecognized.
 */

const data = loadDatasetFromDisk();

function withOnlyPlayer(overrides: Partial<RawBoardPlayer>): Dataset {
  const base = data.board.players[0];
  if (!base) throw new Error('fixture expected at least one player');
  return {
    ...data,
    board: { ...data.board, players: [{ ...base, ...overrides }] },
  } as Dataset;
}

function identityDoc(dataset: Dataset) {
  const rows = buildRows(dataset);
  const corpus = buildCorpus(dataset, rows);
  const doc = corpus.find((d) => d.id === `board.${rows[0]!.raw.id}.identity`);
  if (!doc) throw new Error('expected an identity doc for the single fixture player');
  return doc;
}

describe('boardDocs: the retrieval corpus states ci_applies_to explicitly', () => {
  it('ci_applies_to "vbd": the doc says the interval applies to VBD, not to the projection', () => {
    const doc = identityDoc(withOnlyPlayer({ ci_low: 135.33, ci_high: 222.43, ci_applies_to: 'vbd' }));
    expect(doc.text).toMatch(/applies to VBD/);
    // decimal() rounds to one place -- check the rounded figures, not the raw input.
    expect(doc.text).toContain('135.3');
    expect(doc.text).toContain('222.4');
  });

  it('ci_applies_to "projected_points": the doc says PROJ, never hardcoded to VBD', () => {
    const doc = identityDoc(withOnlyPlayer({ ci_low: 260, ci_high: 340, ci_applies_to: 'projected_points' }));
    expect(doc.text).toMatch(/applies to PROJ/);
  });

  it('an unrecognized ci_applies_to is stated honestly as a quantity this app does not display, not silently omitted', () => {
    const doc = identityDoc(withOnlyPlayer({ ci_low: 1, ci_high: 2, ci_applies_to: 'snap_share' }));
    expect(doc.text).toMatch(/does not otherwise display/);
    expect(doc.text).toContain('snap_share');
  });

  it('no interval on the row: no interval sentence at all, not a fabricated one', () => {
    const doc = identityDoc(withOnlyPlayer({ ci_low: null, ci_high: null }));
    expect(doc.text).not.toMatch(/interval on file/);
  });
});
