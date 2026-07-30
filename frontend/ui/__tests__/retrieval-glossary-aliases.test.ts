import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { retrieveContext } from '../assistant/reasoning';
import { loadDatasetFromDisk } from './helpers';

/**
 * Founder, 2026-07-30: "the chat bot should have been able to answer the
 * question like you did about CI." Before the alias map, "what is CI" scored
 * zero relevance -- `glossary.json`'s term is "confidence interval", never
 * abbreviated in the export, so a lexical hit on "CI" found nothing and the
 * reasoning lane correctly refused rather than inventing an answer. These
 * tests check the fix on the retrieval side: the abbreviation now resolves,
 * without the substring-matching hazard a 2-letter identifier creates
 * (`\bci\b` is a word-boundary match now, not `.includes('ci')`).
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

describe('retrieval: glossary abbreviations resolve through the alias map', () => {
  it('"what does CI mean" retrieves the real confidence-interval glossary entry, at high confidence', () => {
    const items = retrieveContext(data, rows, 'what does CI mean');
    const hit = items.find((i) => i.id === 'glossary.confidence interval');
    expect(hit).toBeDefined();
    expect(hit!.confidence).toBe('high');
    expect(hit!.text).toBe(
      `confidence interval: ${data.glossary.terms['confidence interval']!.short_definition} ${data.glossary.terms['confidence interval']!.long_explanation}`,
    );
  });

  it('"what is PROJ" retrieves the projected-points glossary entry', () => {
    const items = retrieveContext(data, rows, 'what is PROJ');
    expect(items.some((i) => i.id === 'glossary.projected points')).toBe(true);
  });

  it('"what does AVAIL mean" retrieves the availability-probability glossary entry', () => {
    const items = retrieveContext(data, rows, 'what does AVAIL mean');
    expect(items.some((i) => i.id === 'glossary.availability probability')).toBe(true);
  });

  it('does not exact-match "CI" as a bare substring of an ordinary word -- word-boundary only', () => {
    // "decision" contains the substring "ci"; a naive .includes() match would
    // have wrongly treated this as an exact hit on the confidence-interval
    // glossary doc for a question that never mentions CI.
    const items = retrieveContext(data, rows, 'what is the best decision at this point in the draft');
    const ciDoc = items.find((i) => i.id === 'glossary.confidence interval');
    // Either not retrieved at all, or retrieved on real lexical merit only
    // (never marked 'high' purely from the accidental substring).
    if (ciDoc) expect(ciDoc.confidence).not.toBe('high');
  });
});
