import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { rankByRecommendation, recommendationScore, recommendationTerms } from '../data/recommendation';
import { roundOfPick, pickNumbersForSlot } from '../data/draft';
import { playerAvailabilityAtPick } from '../data/availability';
import { loadDatasetFromDisk } from './helpers';

/**
 * DIAGNOSTIC ONLY -- reproduces the founder's 2026-07-30 pick-18 screenshot
 * (FR-2026-07-30-recommendation-logic-is-inverted). Asserts what the code
 * DOES today, not what it should do. Delete once the strategist's rule lands.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

const TEAMS = 10;
const SLOT = 3; // pick 18 (round 2, snake) belongs to slot 3; its next pick is 23
const PICK = 18;

describe('repro: pick 18, Allen over McBride', () => {
  it('confirms the pick arithmetic matches the screenshot', () => {
    expect(roundOfPick(PICK, TEAMS)).toBe(2);
    const picks = pickNumbersForSlot(TEAMS, SLOT, 16);
    expect(picks).toContain(18);
    expect(picks.find((p) => p > 18)).toBe(23);
  });

  it('reproduces the preference and shows the arithmetic that drove it', () => {
    const allen = rows.find((r) => r.name.kind === 'present' && r.name.value === 'Josh Allen')!;
    const mcbride = rows.find((r) => r.name.kind === 'present' && r.name.value === 'Trey McBride')!;
    const round = roundOfPick(PICK, TEAMS);
    // Round 2 with one pick made: every starting slot except the round-1 pick's
    // is unfilled. Widest plausible need set -- helps McBride, not Allen.
    const unfilled = new Set(['QB', 'RB', 'WR', 'TE', 'DEF']);

    const allenScore = recommendationScore(allen, round, unfilled)!;
    const mcbrideScore = recommendationScore(mcbride, round, unfilled)!;

    // eslint-disable-next-line no-console
    console.log({
      allen: { vbd: allen.vbd, terms: recommendationTerms(allen, round, unfilled), score: allenScore },
      mcbride: { vbd: mcbride.vbd, terms: recommendationTerms(mcbride, round, unfilled), score: mcbrideScore },
    });

    expect(allenScore).toBeGreaterThan(mcbrideScore);

    // And Allen is #1 over the whole undrafted board, not merely over McBride.
    const ranked = rankByRecommendation(rows, round, unfilled);
    // eslint-disable-next-line no-console
    console.log(
      'top 6:',
      ranked.slice(0, 6).map((s) => [s.row.name.kind === 'present' ? s.row.name.value : '?', s.row.raw.position, s.score.toFixed(2)]),
    );
  });

  it('survival probability is absent from the score: perturbing it changes nothing', () => {
    const allen = rows.find((r) => r.name.kind === 'present' && r.name.value === 'Josh Allen')!;
    const round = roundOfPick(PICK, TEAMS);
    const unfilled = new Set(['QB', 'RB', 'WR', 'TE', 'DEF']);
    const before = recommendationScore(allen, round, unfilled);
    // Mutate the row's availability wholesale. If survival entered the score,
    // this would have to move it.
    // `availability` on the raw row is a Record, not a number -- casting a number into it
    // through `as typeof allen` type-checks in the editor and fails `tsc -b`, which is how
    // this landed with a green suite and a red production build. Go through `unknown`.
    const mutated = {
      ...allen,
      raw: { ...allen.raw, availability: 0.01 as unknown as typeof allen.raw.availability },
    } as typeof allen;
    const after = recommendationScore(mutated, round, unfilled);
    expect(after).toBe(before);
  });

  it('reports the availability numbers the screenshot showed', () => {
    for (const name of ['Josh Allen', 'Trey McBride']) {
      // eslint-disable-next-line no-console
      console.log(name, 'at 18:', playerAvailabilityAtPick(data, name, 18), 'at 23:', playerAvailabilityAtPick(data, name, 23));
    }
  });
});
