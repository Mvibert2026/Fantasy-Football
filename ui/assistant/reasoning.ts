import type { BoardRow } from '../data/board';
import type { Dataset } from '../data/load';
import { decimal, integer, signed } from '../lib/format';
import { inferenceClaim, type Claim } from './claim';

/**
 * The reasoning lane: a language model over retrieved context, and nothing else.
 *
 * The model never sees the exports, the repo, or the docs. It sees a list of context
 * items assembled here from the same Cells the table renders, and it is told it may
 * reword them and may not add to them. Numbers reach it only inside those items, so
 * a number it prints either came from an export or is a contract violation the
 * provenance line will expose.
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

function nameOf(row: BoardRow): string {
  return row.name.kind === 'present' ? row.name.value : '';
}

/**
 * Assembles context from the exports. Plain substring matching on names and glossary
 * terms -- the same reasoning as the news lane: no scoring until there is something
 * to tune it against.
 */
export function retrieveContext(data: Dataset, rows: BoardRow[], question: string): ContextItem[] {
  const q = question.toLowerCase();
  const items: ContextItem[] = [];

  for (const row of rows) {
    const name = nameOf(row);
    if (!name) continue;
    const surname = name.split(' ').slice(-1)[0]?.toLowerCase() ?? '';
    const hit = q.includes(name.toLowerCase()) || (surname.length > 3 && q.includes(surname));
    if (!hit) continue;

    const i = row.raw.id - 1;
    const label = row.positionalLabel.kind === 'present' ? row.positionalLabel.value : '';
    const tier = row.tierLabel.kind === 'present' ? row.tierLabel.value : '';
    const rank = row.overallRank.kind === 'present' ? integer(row.overallRank.value) : 'unknown';
    const consensus = row.consensusRank.kind === 'present' ? integer(row.consensusRank.value) : 'unknown';
    const delta = row.deltaVsConsensus.kind === 'present' ? signed(row.deltaVsConsensus.value) : 'unknown';

    items.push({
      id: `board.${row.raw.id}.identity`,
      text: `${name} is ${label}, tier ${tier}, on our board at overall rank ${rank}. Consensus has him at ${consensus}, a difference of ${delta}.`,
      confidence: 'medium',
      source_path: `board.json:players[${i}].overall_rank`,
    });

    if (row.projectedPoints.kind === 'present') {
      items.push({
        id: `board.${row.raw.id}.projection`,
        text: `${name} projects ${decimal(row.projectedPoints.value)} points. The projection curve explains under a third of the variance in what a player actually scores, so this is a weak number.`,
        confidence: 'low',
        source_path: `board.json:players[${i}].projected_points`,
      });
    } else {
      items.push({
        id: `board.${row.raw.id}.projection_absent`,
        text: `${name} has no displayable projection. ${row.projectedPoints.reason}`,
        confidence: 'high',
        source_path: `board.json:players[${i}].projection_note`,
      });
    }

    items.push({
      id: `board.${row.raw.id}.attribution`,
      text: `${name}'s difference against consensus is entirely structural — it reflects this league's format. ${row.evaluativeNote}`,
      confidence: 'medium',
      source_path: `board.json:players[${i}].evaluative_adjustment_note`,
    });
  }

  for (const [term, def] of Object.entries(data.glossary.terms)) {
    if (q.includes(term.toLowerCase())) {
      items.push({
        id: `glossary.${term}`,
        text: `${term}: ${def.short_definition}`,
        confidence: 'high',
        source_path: `glossary.json:terms.${term}.short_definition`,
      });
    }
  }

  for (const [i, finding] of data.nulls.findings.entries()) {
    const words = finding.claim_tested.toLowerCase().split(/\W+/).filter((w) => w.length > 4);
    if (words.some((w) => q.includes(w))) {
      items.push({
        id: `nulls.${finding.id}`,
        text: `We tested this and found nothing. ${finding.claim_tested}: ${finding.plain_language_summary}`,
        confidence: 'high',
        source_path: `nulls.json:findings[${i}].plain_language_summary`,
      });
    }
  }

  return items;
}

export async function runReasoningLane(
  data: Dataset,
  rows: BoardRow[],
  question: string,
): Promise<ReasoningOutcome> {
  const context = retrieveContext(data, rows, question);

  if (context.length === 0) {
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
