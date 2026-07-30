import type { BoardRow } from '../data/board';
import type { Dataset } from '../data/load';
import { inferenceClaim, type Claim } from './claim';
import { buildCorpus, retrieve } from './retrieval';

/**
 * The reasoning lane: a language model over retrieved context, and nothing else.
 *
 * The model never sees the exports, the repo, or the docs. It sees a list of context
 * items assembled here -- scored by `./retrieval`'s lexical retriever over a corpus
 * built from every shipped export artifact, plus (FR-076) whatever the current screen
 * is showing, via `./pageContext` -- and it is told it may reword them and may not add
 * to them. Numbers reach it only inside those items, so a number it prints either came
 * from an export/page state or is a contract violation the provenance line will expose.
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

/**
 * One prior question/answer pair, kept only so a follow-up question can lean on a
 * referent from the conversation ("what about him") -- never a second source of
 * facts. The reasoning lane's binding rules (docs/assistant-persona.md rules 1-4,
 * unchanged) still require every claim in the CURRENT answer to trace to the
 * CURRENT turn's retrieved context; history is conversational continuity only, and
 * is never treated as context to cite from on its own. See rule 9, added for this.
 */
export interface ConversationTurn {
  question: string;
  /** The assistant's prior answer, flattened to plain text (claims joined). */
  answerText: string;
}

export type ReasoningOutcome =
  | { status: 'ok'; claims: Claim[] }
  | { status: 'no_context'; detail: string }
  | { status: 'unavailable'; reason: string; detail: string };

const ENDPOINT = '/__reasoning';

/** History is bounded so a long-running dock session can never grow the request
 *  without limit: the last few turns are enough for a real follow-up referent, and
 *  each turn's answer is truncated so one long prior answer can't dominate the
 *  budget either. Same "keep the payload bounded" instruction FR-076 states for
 *  page context, applied to conversation history. */
const MAX_HISTORY_TURNS = 6;
const MAX_HISTORY_ANSWER_CHARS = 600;

function boundHistory(history: readonly ConversationTurn[]): ConversationTurn[] {
  return history.slice(-MAX_HISTORY_TURNS).map((t) => ({
    question: t.question,
    answerText:
      t.answerText.length > MAX_HISTORY_ANSWER_CHARS
        ? `${t.answerText.slice(0, MAX_HISTORY_ANSWER_CHARS)}…`
        : t.answerText,
  }));
}

/**
 * Scores `question` against a corpus built from every artifact this dataset
 * carries (board rows, glossary, strategies, league.json, nulls.json,
 * player_descriptions.json -- see `./retrieval`) and returns the top matches.
 *
 * Genuinely empty when nothing clears the relevance floor -- this is the
 * behaviour rule 3 depends on. A wider corpus must not become a guarantee that
 * *something* always comes back; it must become able to find the right thing
 * for a much wider range of real questions, which is a different property.
 *
 * Unchanged by FR-076: this function is still lexical retrieval over the static
 * exports only. Page context is a separate, always-included bundle merged in by
 * `runReasoningLane` below, not folded into this corpus -- keeping the two
 * concerns (what the exports say vs. what the screen shows right now) testable
 * independently, and keeping this function's existing test contract intact.
 */
export function retrieveContext(data: Dataset, rows: BoardRow[], question: string): ContextItem[] {
  const corpus = buildCorpus(data, rows);
  return retrieve(corpus, question);
}

/**
 * Merges the always-included page-context bundle with whatever lexical
 * retrieval found, page items first (so they survive the reasoning lane's own
 * bound if a caller ever caps the total) and de-duplicated by id -- a page item
 * and a lexical item can never collide in practice (disjoint id prefixes,
 * `page.*` vs `board.*`/`glossary.*`/etc.) but de-duping by id is one line and
 * removes the possibility outright rather than relying on that staying true.
 */
function mergeContext(pageContext: readonly ContextItem[], lexical: readonly ContextItem[]): ContextItem[] {
  const seen = new Set<string>();
  const merged: ContextItem[] = [];
  for (const item of [...pageContext, ...lexical]) {
    if (seen.has(item.id)) continue;
    seen.add(item.id);
    merged.push(item);
  }
  return merged;
}

export async function runReasoningLane(
  data: Dataset,
  rows: BoardRow[],
  question: string,
  pageContext: readonly ContextItem[] = [],
  history: readonly ConversationTurn[] = [],
): Promise<ReasoningOutcome> {
  const lexical = retrieveContext(data, rows, question);
  const context = mergeContext(pageContext, lexical);

  if (context.length === 0) {
    // The expected, correct outcome for a question that shares no real vocabulary
    // with anything in the exports AND no page context is available (e.g. Prep mode,
    // no active draft) -- not an edge case to work around. See ./retrieval's module
    // doc: retrieval must be able to truthfully say "nothing found" or rule 3 (no
    // answering from general football knowledge) is hollow.
    return {
      status: 'no_context',
      detail:
        'Nothing in the exports or on the current screen matched that question, so there was no ' +
        'context to reason over. Rather than answer from general football knowledge, the ' +
        'assistant stops here.',
    };
  }

  let res: Response;
  try {
    res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ question, context, history: boundHistory(history) }),
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
