import { describe, expect, it } from 'vitest';
import { GLOSSARY_ALIASES, UNALIASED_HEADER_LABELS, glossaryShortDefinitionFor } from '../data/glossaryAliases';
import { loadDatasetFromDisk } from './helpers';

/**
 * Founder, 2026-07-30: "the chat bot should have been able to answer the
 * question like you did about CI -- even hovering over CI to tell me that
 * would have been ok." The glossary already has a correct "confidence
 * interval" entry; nothing connected it to the "CI" the UI actually renders.
 *
 * These tests are the guard against the next abbreviation reintroducing the
 * same gap silently: every alias must resolve to a real, live glossary term
 * (not a typo'd key that quietly returns undefined forever), and the
 * documented "no entry" list must actually have no entry -- if backend ever
 * adds one, this test should be the thing that notices.
 */

const data = loadDatasetFromDisk();

describe('GLOSSARY_ALIASES', () => {
  it("covers CI, PROJ, CONS and AVAIL -- the abbreviations the founder's own audit found unreachable", () => {
    for (const abbr of ['CI', 'PROJ', 'CONS', 'AVAIL']) {
      expect(GLOSSARY_ALIASES).toHaveProperty(abbr);
    }
  });

  it('every alias resolves to a term that actually exists in the live glossary export', () => {
    const liveTerms = new Set(Object.keys(data.glossary.terms));
    for (const [abbr, term] of Object.entries(GLOSSARY_ALIASES)) {
      expect(liveTerms.has(term), `alias "${abbr}" -> "${term}" has no matching glossary.json entry`).toBe(true);
    }
  });

  it('CI resolves to the real confidence-interval short definition', () => {
    expect(glossaryShortDefinitionFor(data, 'CI')).toBe(data.glossary.terms['confidence interval']!.short_definition);
  });

  it('the short definitions used as hovers stay short (~12 words), per PROVENANCE-DISCLOSURE.md', () => {
    for (const term of Object.values(GLOSSARY_ALIASES)) {
      const def = data.glossary.terms[term]?.short_definition;
      if (!def) continue;
      // Generous ceiling, not a strict word-count assertion -- catches an
      // accidental swap of long_explanation for short_definition, which is
      // the realistic regression here (both exist on every term).
      expect(def.length, `"${term}" short_definition looks too long for a hover: "${def}"`).toBeLessThan(150);
    }
  });

  it('MFL/POS/TM/BYE are deliberately unaliased -- checked, not omitted by accident', () => {
    const liveTerms = new Set(Object.keys(data.glossary.terms));
    for (const label of UNALIASED_HEADER_LABELS) {
      expect(GLOSSARY_ALIASES).not.toHaveProperty(label);
      // If backend ever adds a real term for one of these, this is the
      // signal to move it out of the unaliased list, not leave it stranded.
      expect(liveTerms.has(label), `"${label}" now has a live glossary entry -- move it into GLOSSARY_ALIASES`).toBe(
        false,
      );
    }
  });

  it('an abbreviation with no alias returns no hover text, never a fabricated one', () => {
    expect(glossaryShortDefinitionFor(data, 'MFL')).toBeUndefined();
    expect(glossaryShortDefinitionFor(data, 'NOT_A_REAL_ABBREVIATION')).toBeUndefined();
  });
});
