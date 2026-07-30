import type { Dataset } from './load';

/**
 * Maps a displayed UI abbreviation to the `glossary.json` term key that
 * defines it.
 *
 * Founder, 2026-07-30, after the CI/VBD mislabelling was explained: "the chat
 * bot should have been able to answer the question like you did about CI --
 * even hovering over CI to tell me that would have been ok." Two failures
 * traced back to the same cause: `glossary.json` already carries a correct
 * "confidence interval" entry, but nothing connects it to the "CI" the UI
 * actually renders, so a lexical retrieval hit on "CI" found nothing
 * (`assistant/retrieval.ts`'s `glossaryDocs()` only indexes terms by their own
 * exact key) and no header offered a hover either.
 *
 * This is the one place that connection gets made. `retrieval.ts` reads it to
 * add each alias as an extra exact-match identifier alongside the term itself;
 * `Board.tsx`/`DraftRoom.tsx` read it to decide which column headers get a
 * glossary-sourced hover. A new column that reuses an existing glossary
 * concept needs one line here, not a hunt through both files.
 *
 * Measured against every abbreviation this app renders on a column header:
 * CI, PROJ, CONS and AVAIL have a real glossary entry and were previously
 * unreachable by either mechanism -- listed below. VBD, TIER and ADP already
 * matched retrieval (their glossary key equals their displayed label) but had
 * no header hover; listed here too so one map drives both.
 *
 * `UNALIASED_HEADER_LABELS` names the abbreviations that do NOT have a
 * glossary entry, checked deliberately rather than left to look like an
 * oversight -- do not invent a definition to fill this table.
 */
export const GLOSSARY_ALIASES: Record<string, string> = {
  CI: 'confidence interval',
  PROJ: 'projected points',
  CONS: 'consensus rank',
  AVAIL: 'availability probability',
  VBD: 'VBD',
  TIER: 'tier',
  ADP: 'ADP',
};

/**
 * Column-header abbreviations this app renders with no corresponding
 * glossary.json term, as of the 2026-07-30 audit prompted by the founder's
 * CI question. MFL is a source name (MyFantasyLeague), not a defined concept;
 * POS/TM/BYE are self-explanatory field labels, not jargon needing a gloss.
 * Kept as a real list, not a claim in a session report, so the gap is visible
 * in code and a later session can check it rather than re-deriving it.
 */
export const UNALIASED_HEADER_LABELS = ['MFL', 'POS', 'TM', 'BYE'] as const;

/**
 * The glossary's own short_definition for a displayed abbreviation, or
 * `undefined` when there is none -- callers must not fabricate a hover in
 * that case. Definitions are class-2 caveats under
 * `docs/design/PROVENANCE-DISCLOSURE.md`: ungated by trace mode, unlike the
 * field path a caller may append separately.
 */
export function glossaryShortDefinitionFor(data: Dataset, abbreviation: string): string | undefined {
  const term = GLOSSARY_ALIASES[abbreviation];
  if (!term) return undefined;
  return data.glossary.terms[term]?.short_definition;
}
