import type { BoardRow } from './board';

/**
 * FR-122 ("when typing in a player's name, the list should begin to shrink
 * down... so it can be used as a search as well as 'drafted' function").
 *
 * Reuses the draft room's existing pick-entry text field (`query` state in
 * DraftRoom.tsx, already there for RETROFIT-5's digit-key commit flow) as the
 * founder's "one control, two jobs" -- this module is the second job. It does
 * not add a second input.
 *
 * Folds diacritics and punctuation aggressively, per the founder's own named
 * examples (`Ja'Marr` / `JaMarr` / `jamarr` must all match): this is *search*,
 * where a wrong match costs one keystroke of correction, not the mock-draft
 * ingestion's strict identity matching, where a wrong match corrupts a row in
 * `nfl.db`. The two must never share code, only the same instinct -- keeping
 * them in separate files (this one is frontend-only, ingestion's matching is
 * Python) is deliberate, not an oversight.
 */

/** Lowercase, strip diacritics (NFD + combining marks), strip everything that
 *  isn't a letter or digit -- so `Ja'Marr`, `JaMarr` and `jamarr` all reduce
 *  to `jamarr`, and `RB10` / `rb-10` / `RB 10` all reduce to `rb10`. */
export function normalizeSearchTerm(raw: string): string {
  return raw
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // combining diacritical marks
    .replace(/[^a-z0-9]/gi, '')
    .toLowerCase();
}

/**
 * Fields a query can match, per the FR: "Match on more than the display
 * name. Team, position, and positional rank (RB10) should all filter... at
 * 1180w the positional rank is the only identity a row has." Positional
 * label (`RB10`) covers position-plus-rank in one field, so `RB1` correctly
 * substring-matches `RB1`, `RB10`..`RB19` -- the FR's own example -- without
 * a separate numeric-range comparison.
 */
export function matchesPlayerQuery(row: BoardRow, rawQuery: string): boolean {
  const q = normalizeSearchTerm(rawQuery);
  if (!q) return true;
  const haystacks = [
    row.name.kind === 'present' ? row.name.value : '',
    row.raw.team ?? '',
    row.raw.position ?? '',
    row.positionalLabel.kind === 'present' ? row.positionalLabel.value : '',
  ];
  return haystacks.some((h) => h && normalizeSearchTerm(h).includes(q));
}
