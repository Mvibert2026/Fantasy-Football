import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { ask } from '../assistant';
import { assertTagged, CLAIM_TAGS, UntaggedClaimError, type Claim } from '../assistant/claim';
import { TEMPLATES } from '../assistant/templates';
import { runNewsLane } from '../assistant/news';
import { loadDatasetFromDisk } from './helpers';

/**
 * Fails on any untagged claim from any lane.
 *
 * An untagged claim is the failure this whole design exists to prevent: a sentence
 * that reads as authoritative without saying whether it is arithmetic over the user's
 * own board, something a reporter published, or a model's prose. At a draft table
 * those warrant very different trust, and the tag is the only thing carrying that.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const ctx = { data, rows, league };

describe('every claim is tagged and sourced', () => {
  it.each(TEMPLATES.map((t) => [t.id, t] as const))(
    'template %s emits only tagged, sourced claims',
    (_id, template) => {
      const m = template.match(template.example);
      expect(m, `template example "${template.example}" must match its own pattern`).not.toBeNull();

      const claims = template.run(m!, ctx);
      expect(claims.length).toBeGreaterThan(0);

      for (const claim of claims) {
        expect(CLAIM_TAGS).toContain(claim.tag);
        expect(claim.text.trim()).not.toBe('');
        expect(claim.provenance.trim()).not.toBe('');
      }
      expect(() => assertTagged(claims)).not.toThrow();
    },
  );

  it('every template answer routed through ask() is tagged', async () => {
    for (const template of TEMPLATES) {
      const answer = await ask(template.example, ctx);
      for (const claim of answer.claims) {
        expect(CLAIM_TAGS).toContain(claim.tag);
        expect(claim.provenance.trim()).not.toBe('');
      }
    }
  });

  it('the news lane emits SOURCE claims and nothing else', () => {
    // No corpus today, so the lane returns no claims -- assert the shape it will have
    // when one arrives, using a synthetic feed rather than waiting for the backend.
    const withFeed = {
      ...data,
      feed: {
        contract_version: '1.0.0',
        generated_utc: new Date().toISOString(),
        items: [
          {
            headline: 'Player listed as limited in practice',
            source_name: 'Example Wire',
            url: 'https://example.invalid/story',
            published_at: new Date().toISOString(),
            player_ids: [data.board.players[0]!.id],
            retrieved_at: new Date().toISOString(),
          },
        ],
      },
    };
    const result = runNewsLane(withFeed, data.board.players[0]!.player.toLowerCase());
    expect(result.noCorpus).toBe(false);
    expect(result.claims.length).toBeGreaterThan(0);
    for (const claim of result.claims) {
      expect(claim.tag).toBe('SOURCE');
      expect(claim.provenance).toContain('https://example.invalid/story');
    }
  });

  it('shows the age of a SOURCE claim past the staleness window', () => {
    const old = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString();
    const withStaleFeed = {
      ...data,
      feed: {
        contract_version: '1.0.0',
        generated_utc: old,
        items: [
          {
            headline: 'Older report',
            source_name: 'Example Wire',
            url: 'https://example.invalid/old',
            published_at: old,
            player_ids: [data.board.players[0]!.id],
            retrieved_at: old,
          },
        ],
      },
    };
    const result = runNewsLane(withStaleFeed, data.board.players[0]!.player.toLowerCase());
    expect(result.claims[0]?.age).toMatch(/\d+d old/);
  });

  // Positive controls. Without these, a no-op assertTagged would let the suite pass.
  it.each([
    ['missing tag', { text: 'x', provenance: 'y' }],
    ['bogus tag', { tag: 'GUESS', text: 'x', provenance: 'y' }],
    ['no provenance', { tag: 'MODEL', text: 'x', provenance: '' }],
    ['no text', { tag: 'MODEL', text: '   ', provenance: 'y' }],
  ])('rejects a claim with %s', (_label, bad) => {
    expect(() => assertTagged([bad as unknown as Claim])).toThrow(UntaggedClaimError);
  });
});
