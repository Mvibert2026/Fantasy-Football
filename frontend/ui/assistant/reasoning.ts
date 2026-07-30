import type { BoardRow } from '../data/board';
import type { Dataset } from '../data/load';
import { inferenceClaim, type Claim } from './claim';
import { buildCorpus, retrieve } from './retrieval';

/**
 * The reasoning lane: a language model over retrieved context, and nothing else.
 *
 * The model never sees the exports, the repo, or the docs. It sees a list of context
 * items assembled here -- scored by `./retrieval`'s lexical retriever over a corpus
 * built from every shipped export artifact -- and it is told it may reword them and
 * may not add to them. Numbers reach it only inside those items, so a number it
 * prints either came from an export or is a contract violation the provenance line
 * will expose.
 *
 * Unavailability is permanent, not a placeholder. No key, proxy stopped, and offline
 * are three flavours of the same answer: this lane is off, everything else still works.
 */

export interface ContextItem {
  id: string;
  text: string;
  confidence: 'high' | 'medium' | 'low';
  source_path: string;
}

export type ReasoningOutcome =
  | { status: 'ok'; claims: Claim[] }
  | { status: 'no_context'; detail: string }
  | { status: 'unavailable'; reason: string; detail: string };

const ENDPOINT = '/__reasoning';

/**
 * Scores `question` against a corpus built from every artifact this dataset
 * carries (board rows, glossary, strategies, league.json, nulls.json,
 * player_descriptions.json -- see `./retrieval`) and returns the top matches.
 *
 * Genuinely empty when nothing clears the relevance floor -- this is the
 * behaviour rule 3 depends on. A wider corpus must not become a guarantee that
 * *something* always comes back; it must become able to find the right thing
 * for a much wider range of real questions, which is a different property.
 */
export function retrieveContext(data: Dataset, rows: BoardRow[], question: string): ContextItem[] {
  const corpus = buildCorpus(data, rows);
  return retrieve(corpus, question);
}

export async function runReasoningLane(
  data: Dataset,
  rows: BoardRow[],
  question: string,
): Promise<ReasoningOutcome> {
  const context = retrieveContext(data, rows, question);

  if (context.length === 0) {
    // The expected, correct outcome for a question that shares no real vocabulary
    // with anything in the exports -- not an edge case to work around. See
    // ./retrieval's module doc: retrieval must be able to truthfully say "nothing
    // found" or rule 3 (no answering from general football knowledge) is hollow.
    return {
      status: 'no_context',
      detail:
        'Nothing in the exports matched that question, so there was no context to reason over. ' +
        'Rather than answer from general football knowledge, the assistant stops here.',
    };
  }

  let res: Response;
  try {
    res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ question, context }),
    });
  } catch {
    // Offline, or the dev server is not running. A permanent, expected state.
    return {
      status: 'unavailable',
      reason: 'offline',
      detail:
        'The reasoning lane could not be reached. Everything else on this page keeps working — ' +
        'the board, the guide, the glossary and every template query are computed locally from ' +
        'static files and never touch the network.',
    };
  }

  const body = (await res.json().catch(() => null)) as
    | { status: string; text?: string; detail?: string; reason?: string; context_ids?: string[] }
    | null;

  if (!body) {
    return {
      status: 'unavailable',
      reason: 'bad_response',
      detail: 'The reasoning lane returned something unreadable.',
    };
  }

  if (body.status === 'ok' && body.text) {
    // One claim per paragraph, each tagged INFERENCE and citing the context it drew on.
    const paragraphs = body.text.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean);
    const ids = body.context_ids ?? context.map((c) => c.id);
    return { status: 'ok', claims: paragraphs.map((p) => inferenceClaim(p, ids)) };
  }

  if (body.status === 'no_context') {
    return { status: 'no_context', detail: body.detail ?? 'No context to reason over.' };
  }

  return {
    status: 'unavailable',
    reason: body.reason ?? 'unknown',
    detail: body.detail ?? 'The reasoning lane is unavailable.',
  };
}
