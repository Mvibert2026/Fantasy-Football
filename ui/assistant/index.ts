import type { BoardRow } from '../data/board';
import type { LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { assertTagged, type Claim } from './claim';
import { classify, type Lane } from './intent';
import { NO_CORPUS_MESSAGE, runNewsLane } from './news';
import { runReasoningLane } from './reasoning';
import { matchTemplate, TEMPLATES } from './templates';

/**
 * The single entry point. Classify, dispatch, and validate.
 *
 * Every answer leaving this function has passed `assertTagged`, so no claim can reach
 * the screen without saying what kind of claim it is and where it came from. That
 * check is here, once, rather than in each lane -- a lane cannot forget it.
 */

export interface Answer {
  question: string;
  lane: Lane;
  rationale: string;
  claims: readonly Claim[];
  /**
   * Present when the lane produced no claims. This is a normal outcome, not an error:
   * an empty news feed, an unmatched question, a disabled reasoning lane.
   */
  notice?: string;
  /** Shown alongside a notice when the user needs to know what the assistant *can* answer. */
  showTemplates?: boolean;
}

export interface AssistantContext {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
}

export async function ask(question: string, ctx: AssistantContext): Promise<Answer> {
  const { lane, rationale } = classify(question);
  const base = { question, lane, rationale };

  if (lane === 'export') {
    const matched = matchTemplate(question);
    if (!matched) {
      // classify() only routes here on a match, so this is unreachable in practice.
      return { ...base, claims: [], notice: unmatchedNotice(), showTemplates: true };
    }
    const claims = matched.template.run(matched.m, ctx);
    return { ...base, claims: assertTagged(claims) };
  }

  if (lane === 'news') {
    const result = runNewsLane(ctx.data, question);
    if (result.noCorpus) {
      return { ...base, claims: [], notice: NO_CORPUS_MESSAGE };
    }
    if (result.claims.length === 0) {
      return {
        ...base,
        claims: [],
        notice: 'No ingested feed item mentions a player named in that question.',
      };
    }
    return { ...base, claims: assertTagged(result.claims) };
  }

  const outcome = await runReasoningLane(ctx.data, ctx.rows, question);
  if (outcome.status === 'ok') {
    return { ...base, claims: assertTagged(outcome.claims) };
  }
  if (outcome.status === 'no_context') {
    return { ...base, claims: [], notice: `${outcome.detail}\n\n${unmatchedNotice()}`, showTemplates: true };
  }
  return { ...base, claims: [], notice: outcome.detail, showTemplates: true };
}

function unmatchedNotice(): string {
  return (
    'That question does not match any template the assistant can answer deterministically. ' +
    'It will not be guessed at, and it will not be answered from general football knowledge.'
  );
}

export { TEMPLATES };
export type { Lane };
