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
 * Player-, glossary-term-, and nulls-finding-specific context. Plain substring
 * matching on names and glossary terms -- the same reasoning as the news lane: no
 * scoring until there is something to tune it against.
 */
function retrieveNarrowContext(data: Dataset, rows: BoardRow[], q: string): ContextItem[] {
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

/**
 * The fallback that replaces outright refusal: when nothing above matched a name,
 * a glossary term, or a nulls keyword, hand over the two export files most likely
 * to answer a general strategy or positional-valuation question -- strategies.json
 * and every nulls.json finding -- rather than stopping at "nothing matched".
 *
 * This is not question-specific retrieval; it is "here is what this app measured,
 * pick out what's relevant." The model is still bound by the renderer contract: it
 * cannot state a number that is not in one of these items, and every claim is
 * tagged INFERENCE with its provenance regardless of how the context arrived.
 *
 * Two things are included specifically so the model can give the caveated answer
 * this fallback exists for, instead of either inventing one or refusing:
 *   - `power_floor.plain_english`, so a strategy comparison doesn't get narrated as
 *     statistically significant when the data cannot support that at n=4 seasons.
 *   - An explicit statement that each strategy was simulated only against the
 *     baseline, not against each other -- so a "which two strategies combine best"
 *     question gets told that plainly rather than answered from nothing.
 */
function retrieveFallbackContext(data: Dataset): ContextItem[] {
  const items: ContextItem[] = [];
  const s = data.strategies;

  // Null for a league strategies.json hasn't been run for yet (see Dataset.strategies)
  // -- nothing to summarize, but nulls.json findings below still apply.
  if (s) {
    for (const [i, strategy] of s.strategies.entries()) {
      // Sigma 10 is the export's own default reading ("about one round of slippage");
      // summarizing at one sigma keeps each strategy to one digestible context item
      // instead of three near-duplicates.
      const cell = strategy.by_sigma.find((c) => c.sigma === 10) ?? strategy.by_sigma[0];
      if (!cell) continue;
      const j = strategy.by_sigma.indexOf(cell);

      const margin =
        cell.margin_vs_baseline === null
          ? ''
          : ` Margin vs. the baseline: ${cell.margin_vs_baseline > 0 ? '+' : ''}${decimal(cell.margin_vs_baseline)} points.`;
      const seasons =
        cell.seasons_positive === null
          ? ''
          : ` Positive in ${integer(cell.seasons_positive)} of ${integer(s.power_floor.n_seasons)} simulated seasons.`;
      const signTest = cell.sign_test_p === null ? '' : ` Sign-test p = ${decimal(cell.sign_test_p)}.`;

      items.push({
        id: `strategies.${i}.summary`,
        text:
          `Strategy "${strategy.name}"${strategy.is_baseline ? ' (the baseline every other strategy is measured against)' : ''}: ` +
          `${strategy.verdict} At sigma ${integer(cell.sigma)}, mean roster points ${decimal(cell.mean_roster_points)}.` +
          `${margin}${seasons}${signTest}`,
        confidence: 'medium',
        source_path: `strategies.json:strategies[${i}].by_sigma[${j}]`,
      });
    }

    items.push({
      id: 'strategies.power_floor',
      text: s.power_floor.plain_english,
      confidence: 'high',
      source_path: 'strategies.json:power_floor.plain_english',
    });

    items.push({
      id: 'strategies.not_compositional',
      text:
        'Each strategy above was simulated independently against the baseline, one at a time. There is no ' +
        'simulation of combining two strategies into a single draft plan, and these numbers cannot be added ' +
        'or averaged together to produce one -- that would need a new simulation run, not arithmetic on the ' +
        'existing results.',
      confidence: 'high',
      source_path: 'strategies.json:strategies',
    });
  }

  for (const [i, finding] of data.nulls.findings.entries()) {
    items.push({
      id: `nulls.${finding.id}.fallback`,
      text: `We tested this and found nothing. ${finding.claim_tested}: ${finding.plain_language_summary}`,
      confidence: 'high',
      source_path: `nulls.json:findings[${i}].plain_language_summary`,
    });
  }

  return items;
}

export function retrieveContext(data: Dataset, rows: BoardRow[], question: string): ContextItem[] {
  const q = question.toLowerCase();
  const narrow = retrieveNarrowContext(data, rows, q);
  return narrow.length > 0 ? narrow : retrieveFallbackContext(data);
}

export async function runReasoningLane(
  data: Dataset,
  rows: BoardRow[],
  question: string,
): Promise<ReasoningOutcome> {
  const context = retrieveContext(data, rows, question);

  if (context.length === 0) {
    // Reachable only if strategies.json and nulls.json are both empty, which the
    // fallback assumes they never are for this project.
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
