import type { Dataset } from '../data/load';
import { ageOf } from '../lib/format';
import { sourceClaim, type Claim } from './claim';

/**
 * The news lane.
 *
 * There is no ingested corpus. `feed.items` is empty and will stay empty until the
 * backend ships one, so this lane's real job today is to say that clearly.
 *
 * Deliberately not built yet: ranking, relevance scoring, recency weighting, dedup,
 * any retrieval tuning at all. There is nothing to tune against, so anything written
 * now would be guesswork dressed as engineering. What exists is the contract, the
 * routing, the empty state, and the staleness rule -- the parts that are decidable
 * without a corpus.
 */

export interface NewsResult {
  claims: Claim[];
  /** True when the lane has no corpus at all, as opposed to a corpus with no matches. */
  noCorpus: boolean;
}

export function runNewsLane(data: Dataset, question: string, now = Date.now()): NewsResult {
  const items = data.feed.items;

  if (items.length === 0) {
    return { claims: [], noCorpus: true };
  }

  // Flat scan, no scoring. A player named in the question matches its items; that is
  // the entire retrieval strategy until there is a corpus to evaluate a better one against.
  const q = question.toLowerCase();
  const namesById = new Map(data.board.players.map((p) => [p.id, p.player.toLowerCase()]));
  const matched = items.filter((item) =>
    item.player_ids.some((id) => {
      const name = namesById.get(id);
      return name ? q.includes(name) || name.split(' ').some((part) => part.length > 3 && q.includes(part)) : false;
    }),
  );

  const claims = matched.map((item) => {
    // The staleness rule: past the window, the age is shown alongside the claim.
    // Body text is never stored or re-rendered -- headline, attribution, link only.
    const age = ageOf(item.published_at, now);
    return sourceClaim(item.headline, item.source_name, item.url, item.published_at, age ?? undefined);
  });

  return { claims, noCorpus: false };
}

export const NO_CORPUS_MESSAGE =
  'No news data ingested yet. The feed contract exists and this lane is wired to it, but nothing ' +
  'has produced feed items, so there is nothing to retrieve. Board queries are unaffected.';
